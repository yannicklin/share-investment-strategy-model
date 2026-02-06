"""
ASX Signal Generation Service

Market-specific implementation for Australian Securities Exchange.
Now includes:
- Trading day validation using pandas_market_calendars
- Resource availability checks (cash/stock holdings)
- Transaction ledger integration
"""

from datetime import datetime, date
from app.bot.shared.models import Signal, ConfigProfile, JobLog, db
from app.bot.services.trading_day_utils import is_trading_day
from app.bot.services.portfolio_service import PortfolioService
from core.model_builder import ModelBuilder
from .config import (
    MARKET_CODE, TICKER_SUFFIX, PUBLIC_HOLIDAYS,
    TRADING_HOURS_START, TRADING_HOURS_END
)
import yfinance as yf
import logging

logger = logging.getLogger(__name__)


class ASXSignalService:
    """
    ASX-specific signal generation service
    
    Ensures complete isolation from USA/TWN markets:
    - Only queries ASX profiles (via .for_market('ASX'))
    - Only creates ASX signals
    - ASX-specific trading day validation
    """
    
    def __init__(self):
        self.market = MARKET_CODE
        self.ticker_suffix = TICKER_SUFFIX
        self.portfolio = PortfolioService(MARKET_CODE)
    
    def generate_daily_signals(self):
        """
        Main entry point for ASX daily signal generation
        
        Returns:
            dict: {
                'already_calculated': bool,
                'already_sent': bool,
                'signals_generated': int,
                'errors': list
            }
        """
        logger.info(f"Starting {self.market} daily signal generation")
        
        # Check idempotency - already calculated today?
        today_signal = Signal.for_market(self.market).filter_by(
            date=date.today()
        ).first()
        
        if today_signal and today_signal.sent_at:
            logger.info(f"{self.market}: Signal already calculated and sent")
            return {
                'already_calculated': True,
                'already_sent': True,
                'signals_generated': 0
            }
         using pandas_market_calendars
        if not is_trading_day(self.market):
            logger.info(f"{self.market}: Not a trading day (weekend/holiday)
            logger.info(f"{self.market}: Not a trading day, skipping")
            return {
                'already_calculated': False,
                'already_sent': False,
                'signals_generated': 0,
                'message': 'Market closed'
            }
        
        # Get ASX profiles (ISOLATED - only ASX)
        profiles = ConfigProfile.for_market(self.market).all()
        
        if not profiles:
            logger.warning(f"{self.market}: No profiles configured")
            return {
                'already_calculated': False,
                'already_sent': False,
                'signals_generated': 0,
                'message': 'No profiles'
            }
        
        # Generate signals for each profile
        signals_generated = 0
        errors = []
        
        for profile in profiles:
            try:
                signals_generated += self._process_profile(profile)
            except Exception as e:
                logger.error(f"{self.market}: Profile {profile.name} failed: {str(e)}")
                errors.append(f"{profile.name}: {str(e)}")
        
        # Log job execution
        job_log = JobLog(
            market=self.market,
            job_type='daily-signal',
            status='success' if not errors else 'partial-failure',
            error_message='; '.join(errors) if errors else None
        )
        db.session.add(job_log)
        db.session.commit()
        
        return {
            'already_calculated': False,
            'already_sent': False,
            'signals_generated': signals_generated,
            'errors': errors
        }
    
    def _process_profile(self, profile):
        """Process one ASX trading profile with resource availability checks"""
        signals_count = 0
        
        for ticker in profile.stocks:
            try:
                # Add ASX suffix (.AX)
                full_ticker = ticker if ticker.endswith(self.ticker_suffix) else ticker + self.ticker_suffix
                
                # Generate signal using AI consensus
                result = self._generate_signal_for_ticker(full_ticker, profile)
                
                if result is None:
                    logger.warning(f"{self.market}: Skipped {full_ticker} (no data or no signal)")
                    continue
                
                # ✅ NEW: Validate resource availability before signal
                signal_type = result['signal']
                notes = ""
                
                if signal_type == 'BUY':
                    # Check if we have cash to buy
                    # Fetch current price for validation
                    price = self._get_current_price(full_ticker)
                    if price is None:
                        logger.warning(f"{self.market}: Cannot get price for {ticker}, skipping BUY signal")
                        continue
                    
                    can_buy, reason = self.portfolio.can_buy(ticker, price, quantity=1)
                    if not can_buy:
                        logger.warning(f"{self.market}: Cannot BUY {ticker}: {reason}")
                        notes = f"Resource check failed: {reason}"
                
                elif signal_type == 'SELL':
                    # Check if we have stock to sell
                    can_sell, reason = self.portfolio.can_sell(ticker, quantity=1)
                    if not can_sell:
                        logger.warning(f"{self.market}: Cannot SELL {ticker}: {reason}")
                        notes = f"Resource check failed: {reason}"
                
                # Create ASX signal (ISOLATED)
                signal = Signal(
                    market=self.market,
                    ticker=ticker,  # Store without suffix
                    signal=result['signal'],
                    confidence=result['confidence'],
                    job_type='daily-signal',
                    trigger_type='scheduled',
                    notes=notes if notes else None
                )
                
                db.session.add(signal)
                signals_count += 1
                
            except Exception as e:
                logger.error(f"{self.market}: Failed to process {ticker}: {str(e)}")
        
        db.session.commit()
        return signals_count
    
    def _generate_signal_for_ticker(self, full_ticker, profile):
        """
        Generate trading signal for a single ticker using multi-model consensus
        
        Args:
            full_ticker: Ticker with suffix (e.g., 'BHP.AX')
            profile: ConfigProfile with strategy parameters
            
        Returns:
            dict: {'signal': 'BUY'|'SELL'|'HOLD', 'confidence': float} or None if no data
        """
        try:
            # Fetch historical data (2 years for proper indicator calculation)
            data = yf.download(full_ticker, period='2y', progress=False, auto_adjust=True)
            
            if data.empty or len(data) < 100:
                logger.warning(f"{self.market}: Insufficient data for {full_ticker}")
                return None
            
            # Use Close price for predictions
            prices = data['Close'].values
            
            # Calculate technical indicators
            from core.model_builder import ModelBuilder
            from core.config import Config
            
            # Train/load models for this ticker
            # For bot: use lightweight models (RF + CatBoost) for speed
            models_to_use = ['random_forest', 'catboost']
            predictions = []
            
            for model_type in models_to_use:
                try:
                    # Create config for this model
                    model_config = Config()
                    model_config.model_type = model_type
                    
                    # Initialize builder with config
                    builder = ModelBuilder(config=model_config)
                    
                    # Prepare features using ModelBuilder's own method
                    # This requires implementing a simple feature engineering method
                    X, y = self._prepare_simple_features(data)
                    
                    if len(X) < 30:
                        continue
                    
                    # Train on historical data
                    builder.train(X[:-1], y[:-1])
                    
                    # Predict next day
                    prediction = builder.predict(X[-1:])
                    
                    # Convert prediction to signal
                    current_price = prices[-1]
                    predicted_return = (prediction - current_price) / current_price
                    
                    # Apply hurdle rate from profile
                    hurdle_rate = profile.hurdle_rate if hasattr(profile, 'hurdle_rate') else 0.05
                    
                    if predicted_return > hurdle_rate:
                        signal = 'BUY'
                    elif predicted_return < -hurdle_rate:
                        signal = 'SELL'
                    else:
                        signal = 'HOLD'
                    
                    predictions.append(signal)
                    
                except Exception as e:
                    logger.warning(f"{self.market}: Model {model_type} failed for {full_ticker}: {str(e)}")
                    continue
            
            if not predictions:
                logger.warning(f"{self.market}: No valid predictions for {full_ticker}")
                return None
            
            # Consensus: Majority vote
            buy_count = predictions.count('BUY')
            sell_count = predictions.count('SELL')
            hold_count = predictions.count('HOLD')
            
            total = len(predictions)
            
            if buy_count > sell_count and buy_count > hold_count:
                consensus = 'BUY'
                confidence = buy_count / total
            elif sell_count > buy_count and sell_count > hold_count:
                consensus = 'SELL'
                confidence = sell_count / total
            else:
                consensus = 'HOLD'
                confidence = hold_count / total
            
            return {
                'signal': consensus,
                'confidence': round(confidence, 2)
            }
            
        except Exception as e:
            logger.error(f"{self.market}: Signal generation failed for {full_ticker}: {str(e)}")
            return None
    
    def _get_current_price(self, full_ticker):
        """
        Fetch current price for a ticker.
        
        Args:
            full_ticker: Ticker with suffix (e.g., 'BHP.AX')
        
        Returns:
            Current price or None if unavailable
        """
        try:
            ticker_obj = yf.Ticker(full_ticker)
            info = ticker_obj.info
            
            # Try different price fields
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if price is None:
                # Fallback: get latest close from history
                hist = ticker_obj.history(period='1d')
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
            
            return price
        except Exception as e:
            logger.error(f"{self.market}: Failed to get price for {full_ticker}: {str(e)}")
            return None
    
    def _prepare_simple_features(self, data):
        """
        Prepare features for model training using simple technical indicators
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            tuple: (X, y) features and target arrays
        """
        df = data.copy()
        
        # Calculate returns
        df['Return'] = df['Close'].pct_change()
        
        # Simple moving averages
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        
        # RSI (simplified)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Drop NaN rows
        df = df.dropna()
        
        if len(df) < 30:
            raise ValueError("Insufficient data after feature engineering")
        
        # Features: returns, SMAs, RSI
        feature_cols = ['Return', 'SMA_5', 'SMA_20', 'RSI']
        X = df[feature_cols].values
        
        # Target: next day's close price
        y = df['Close'].shift(-1).ffill().values
        
        # Remove last row (no future target)
        X = X[:-1]
        y = y[:-1]
        
        return X, y
