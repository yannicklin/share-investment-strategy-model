"""
ASX Signal Generation Service

Market-specific implementation for Australian Securities Exchange.
Inherits from BaseSignalService to reduce duplication.
"""

from datetime import datetime, date
from app.bot.shared.models import Signal, ConfigProfile, JobLog, db
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
        
        # Validate trading day
        if not self._is_trading_day():
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
        """Process one ASX trading profile"""
        signals_count = 0
        
        for ticker in profile.stocks:
            try:
                # Add ASX suffix (.AX)
                full_ticker = ticker if ticker.endswith(self.ticker_suffix) else ticker + self.ticker_suffix
                
                # Fetch data from Yahoo Finance
                data = yf.download(full_ticker, period='2y', progress=False)
                
                if data.empty:
                    logger.warning(f"{self.market}: No data for {full_ticker}")
                    continue
                
                # Call UNIVERSAL core model (market-agnostic)
                model_builder = ModelBuilder()
                predictions = model_builder.predict(data)
                
                # Create ASX signal (ISOLATED)
                signal = Signal(
                    market=self.market,
                    ticker=ticker,  # Store without suffix
                    signal=predictions['consensus'],
                    confidence=predictions['confidence'],
                    job_type='daily-signal'
                )
                
                db.session.add(signal)
                signals_count += 1
                
            except Exception as e:
                logger.error(f"{self.market}: Failed to process {ticker}: {str(e)}")
        
        db.session.commit()
        return signals_count
    
    def _is_trading_day(self):
        """
        ASX-specific trading day validation
        
        Returns False if:
        - Weekend (Saturday/Sunday)
        - Public holiday (ASX closed)
        """
        today = date.today()
        
        # Weekend check
        if today.weekday() >= 5:  # 5=Saturday, 6=Sunday
            return False
        
        # Public holiday check
        if today.strftime('%Y-%m-%d') in PUBLIC_HOLIDAYS:
            return False
        
        return True
