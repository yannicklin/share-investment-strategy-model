"""
USA AI Trading System - Backtesting Engine

Purpose: Simulates trading strategies on historical US market data with realistic
constraints (fees, SEC/FINRA, T+1 settlement, W-8BEN tax).

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
import numpy as np
import os
import joblib
import logging
from typing import List, Dict, Any, Callable, Optional, Tuple, Union
from core.config import Config, BROKERS, get_tax_profile
from core.model_builder import ModelBuilder
from core.utils import (
    format_date_with_weekday,
    get_usa_trading_days,
    calculate_trading_days_ahead,
    validate_buy_capacity,
)
from core.transaction_ledger import TransactionLedger


class BacktestEngine:
    """Simulates trading strategy on historical data with support for multiple modes."""

    def __init__(self, config: Config, model_builder: ModelBuilder):
        self.config = config
        self.model_builder = model_builder
        self.ledger = TransactionLedger()
        self.trading_days: Optional[pd.DatetimeIndex] = None

    def calculate_fees(
        self, trade_value: float, shares: float = 0, is_sell: bool = False
    ) -> float:
        """USA Fee Structure including SEC/FINRA for sells."""
        broker = BROKERS[self.config.cost_profile]

        # 1. Brokerage Fee
        if "IBKR" in broker.name:
            commission = max(broker.min_commission, shares * 0.005)
            commission = min(commission, trade_value * 0.01)
        else:
            commission = max(
                broker.min_commission,
                broker.brokerage_fixed + (trade_value * broker.brokerage_rate),
            )

        # 2. Regulatory Fees (Sell-side only)
        reg_fees = 0.0
        if is_sell:
            sec_fee = trade_value * 0.0000278
            finra_fee = min(8.30, shares * 0.000166)
            reg_fees = sec_fee + finra_fee

        return commission + reg_fees

    def get_hurdle_rate(self, current_capital: float) -> float:
        """Calculates minimum return % required to break even."""
        if current_capital <= 0:
            return 0.0

        entry_fee = self.calculate_fees(current_capital, is_sell=False)
        exit_fee = self.calculate_fees(current_capital, is_sell=True)
        fees_pct = (entry_fee + exit_fee) / current_capital

        return fees_pct + self.config.hurdle_risk_buffer

    def _get_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        if data is None or data.empty:
            return pd.DataFrame()

        # IMPORTANT: The data from ModelBuilder.fetch_data is already normalized.
        # However, we perform a safety check to ensure standard columns are available.
        df = data.copy()

        standard_cols = ["Close", "Open", "High", "Low", "Volume"]

        # Verify mandatory columns
        for col in ["Close", "Open", "High", "Low"]:
            if col not in df.columns:
                # If a core column is missing, it means normalization failed.
                # We try one last desperate search.
                found = False
                for c in df.columns:
                    if col.lower() in str(c).lower():
                        df.rename(columns={c: col}, inplace=True)
                        found = True
                        break
                if not found:
                    raise KeyError(
                        f"CRITICAL: Column '{col}' not found. Available: {list(df.columns)}"
                    )

        # Ensure numeric
        for col in standard_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["Close", "Open", "High", "Low"])

        # MACD
        df["MACD"] = df["Close"].ewm(span=12).mean() - df["Close"].ewm(span=26).mean()

        df["Signal_Line"] = df["MACD"].ewm(span=9).mean()
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-9)
        df["RSI"] = 100 - (100 / (1 + rs))
        df["MA5"], df["MA20"] = (
            df["Close"].rolling(5).mean(),
            df["Close"].rolling(20).mean(),
        )
        df["Daily_Return"] = df["Close"].pct_change(fill_method=None)
        return df.dropna()

    def _resolve_prediction_horizon_days(self) -> int:
        """Map the configured holding period to a BUY prediction horizon in days."""
        unit = self.config.hold_period_unit.lower()
        value = max(1, int(self.config.hold_period_value))

        if unit == "day":
            return value
        if unit == "week":
            return value * 7
        if unit == "month":
            return value * 30
        if unit == "year":
            return value * 365
        return value

    def _prepare_data(
        self, ticker: str
    ) -> Tuple[Optional[pd.DataFrame], Optional[List[str]], Optional[Dict[str, str]]]:
        """Prepare and filter dataframe for backtesting.

        Returns:
            (df, features, error_dict) - If error, df will be None
        """
        raw_data = self.model_builder.fetch_data(ticker, self.config.backtest_years)
        if raw_data.empty:
            return None, None, {"error": f"No data for {ticker}"}

        # Use the unified feature preparation from model_builder
        # We need the full dataframe with indicators for the core loop
        # So we'll recreate the feature list logic here to match exactly
        df = raw_data.copy()

        # 1. Basic Moving Averages
        df["MA5"] = df["Close"].rolling(window=5).mean()
        df["MA20"] = df["Close"].rolling(window=20).mean()
        df["MA50"] = df["Close"].rolling(window=50).mean()

        # 2. RSI
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        df["RSI"] = 100 - (100 / (1 + rs))

        # 3. MACD
        exp1 = df["Close"].ewm(span=12, adjust=False).mean()
        exp2 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = exp1 - exp2
        df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()

        # 4. Bollinger Bands
        df["BB_Middle"] = df["Close"].rolling(window=20).mean()
        df["BB_Std"] = df["Close"].rolling(window=20).std()
        df["BB_Upper"] = df["BB_Middle"] + (2 * df["BB_Std"])
        df["BB_Lower"] = df["BB_Middle"] - (2 * df["BB_Std"])
        df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / (df["BB_Middle"] + 1e-9)

        # 5. ATR
        high_low = df["High"] - df["Low"]
        high_close = np.abs(df["High"] - df["Close"].shift())
        low_close = np.abs(df["Low"] - df["Close"].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["ATR"] = tr.rolling(window=14).mean()

        # 6. Market Context Integration
        self.model_builder._ensure_market_data()
        m_data = self.model_builder._market_data
        if m_data is not None and not m_data.empty:
            market_subset = m_data.shift(1).reindex(df.index).ffill()
            df = df.join(market_subset)

        df["Daily_Return"] = df["Close"].pct_change(fill_method=None)

        # Clean up
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.ffill(inplace=True)
        df.fillna(0, inplace=True)

        # Determine the official start/end dates for trading
        official_start = pd.Timestamp.now().normalize() - pd.DateOffset(
            years=self.config.backtest_years
        )
        official_end = pd.Timestamp(df.index[-1])
        self.trading_days = get_usa_trading_days(official_start, official_end)

        # Normalize both to UTC-naive midnight for robust comparison
        df.index = pd.DatetimeIndex(df.index).tz_localize(None).normalize()
        trading_days_normalized = (
            pd.DatetimeIndex(self.trading_days).tz_localize(None).normalize()
            if self.trading_days is not None
            else pd.DatetimeIndex([])
        )

        # Filter dataframe to only include valid trading days
        df = df[df.index.isin(trading_days_normalized)]
        if df.empty:
            logging.warning(
                f"Dataframe empty for {ticker} after applying market calendar filter. Index: {raw_data.index[:1]} to {raw_data.index[-1:]}. Calendar: {self.trading_days[:1]} to {self.trading_days[-1:]}"
            )
            return None, None, {"error": f"No valid trading days for {ticker}"}

        # Synchronized Features List (MUST MATCH model_builder.py)
        features = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "MA5",
            "MA20",
            "MA50",
            "RSI",
            "MACD",
            "Signal_Line",
            "BB_Upper",
            "BB_Lower",
            "BB_Width",
            "ATR",
            "Daily_Return",
        ]

        # Add dynamic market features
        if m_data is not None:
            for col in m_data.columns:
                if col in df.columns:
                    features.append(col)

        return df, features, None

    def _get_pre_consensus_exit(
        self,
        i: int,
        df: pd.DataFrame,
        buy_price: float,
        buy_date: Optional[pd.Timestamp],
        current_date: pd.Timestamp,
    ) -> Tuple[Optional[str], float]:
        """Return an early risk exit before consensus voting, if one applies."""
        if buy_date is None:
            return None, 0.0

        low_p, high_p = float(df.iloc[i]["Low"]), float(df.iloc[i]["High"])
        sl_p, tp_p = (
            buy_price * (1 - self.config.stop_loss_threshold),
            buy_price * (1 + self.config.stop_profit_threshold),
        )

        if low_p <= sl_p:
            return "stop-loss", min(sl_p, float(df.iloc[i]["Open"]))

        if buy_date is not None and self.trading_days is not None:
            if self.config.hold_period_unit.lower() == "day":
                target_date = calculate_trading_days_ahead(
                    buy_date, self.config.hold_period_value, self.trading_days
                )
                min_hold_passed = (
                    target_date is not None and current_date >= target_date
                )
            else:
                unit_map = {
                    "week": "weeks",
                    "month": "months",
                    "year": "years",
                }
                unit = unit_map.get(self.config.hold_period_unit.lower(), "months")
                min_hold_passed = current_date >= (
                    buy_date + pd.DateOffset(**{unit: self.config.hold_period_value})
                )

            if min_hold_passed and high_p >= tp_p:
                return "take-profit", max(tp_p, float(df.iloc[i]["Open"]))

        return None, 0.0

    def _core_run(
        self,
        ticker: str,
        signal_func: Callable[[int, pd.DataFrame, List[str], float], bool],
        df: pd.DataFrame,
        features: List[str],
    ) -> Dict[str, Any]:
        """The shared engine logic for both modes.

        Args:
            ticker: Stock symbol
            signal_func: Function(i, df, features, capital) -> bool
            df: Pre-filtered dataframe (trading days only)
            features: Feature columns list
        """

        capital = self.config.init_capital
        position, buy_price, buy_date, buy_fees = 0.0, 0.0, None, 0.0
        trades = []
        settlement_queue = []  # List of (available_date, amount)
        
        # Execution diagnostics tracking
        execution_stats = {
            "buy_capacity_checks": 0,
            "buy_capacity_blocks": 0,
            "buy_fee_blocks": 0,
            "buy_signals": 0,
            "buy_executions": 0,
            "sell_stop_loss": 0,
            "sell_take_profit": 0,
            "sell_model_exit": 0,
        }

        for i in range(len(df) - 1):
            date = pd.Timestamp(df.index[i])
            current_price = float(df.iloc[i]["Close"])

            # Safety check: avoid division by zero or negative prices
            if current_price <= 0:
                continue
            new_settlement_queue = []
            for avail_date, amount in settlement_queue:
                if date >= avail_date:
                    capital += amount
                else:
                    new_settlement_queue.append((avail_date, amount))
            settlement_queue = new_settlement_queue

            # Portfolio validation before signal generation (for BUY signals only)
            if position == 0:
                # Signal engine needs to know current available capital
                validation = validate_buy_capacity(capital, {ticker: current_price})
                execution_stats["buy_capacity_checks"] += 1
                if not validation["can_trade"]:
                    # Skip signal generation if insufficient cash
                    execution_stats["buy_capacity_blocks"] += 1
                    continue

            is_bullish = signal_func(
                i,
                df,
                features,
                capital if position == 0 else (position * current_price),
            )

            if position == 0 and is_bullish:
                execution_stats["buy_signals"] += 1
                fees = self.calculate_fees(capital)
                if capital <= fees:
                    execution_stats["buy_fee_blocks"] += 1
                    continue
                execution_stats["buy_executions"] += 1
                new_position = (capital - fees) / current_price
                positions_before = {}
                positions_after = {ticker: new_position}

                # Add BUY entry to ledger
                self.ledger.add_entry(
                    date=date,
                    ticker=ticker,
                    action="BUY",
                    quantity=new_position,
                    price=current_price,
                    commission=fees,
                    cash_before=capital,
                    cash_after=0.0,
                    positions_before=positions_before,
                    positions_after=positions_after,
                    notes="Initial purchase",
                )

                position = new_position
                buy_price, buy_date, buy_fees = current_price, date, fees
                capital = 0

            elif position > 0:
                # Check for pre-consensus exits (stop-loss, take-profit)
                exit_reason, exit_price = self._get_pre_consensus_exit(
                    i, df, buy_price, buy_date, date
                )
                
                reason, sell_price = None, 0.0
                if exit_reason:
                    # Pre-consensus exit triggered (before model vote)
                    reason, sell_price = exit_reason, exit_price
                    if reason == "stop-loss":
                        execution_stats["sell_stop_loss"] += 1
                    elif reason == "take-profit":
                        execution_stats["sell_take_profit"] += 1
                else:
                    # No pre-consensus exit; check model-driven exit
                    if buy_date is not None and self.trading_days is not None:
                        if self.config.hold_period_unit.lower() == "day":
                            # "Day" unit = TRADING DAYS (excludes weekends + holidays)
                            target_date = calculate_trading_days_ahead(
                                buy_date, self.config.hold_period_value, self.trading_days
                            )
                            min_hold_passed = (
                                target_date is not None and date >= target_date
                            )
                        else:
                            # Other units (Week/Month/Year) = CALENDAR DAYS
                            unit_map = {
                                "week": "weeks",
                                "month": "months",
                                "year": "years",
                            }
                            unit = unit_map.get(
                                self.config.hold_period_unit.lower(), "months"
                            )
                            offset = {unit: self.config.hold_period_value}
                            min_hold_passed = date >= (
                                buy_date + pd.DateOffset(**offset)
                            )
                    else:
                        min_hold_passed = False
                    
                    if min_hold_passed and not is_bullish:
                        reason, sell_price = "model-exit", current_price
                        execution_stats["sell_model_exit"] += 1

                if reason and buy_date is not None:
                    val = position * sell_price
                    total_costs = self.calculate_fees(
                        val, shares=position, is_sell=True
                    )
                    tax = 0.0
                    if not self.config.w8ben:
                        tax_profile = get_tax_profile(False)
                        profit = val - (position * buy_price) - (buy_fees + total_costs)
                        if profit > 0:
                            tax = profit * tax_profile.short_term_cgt_rate

                    new_capital = val - total_costs - tax

                    # STRICT REALISM: T+1 Settlement Delay for USA
                    settlement_date = None
                    if self.trading_days is not None:
                        settlement_date = calculate_trading_days_ahead(
                            date, 1, self.trading_days
                        )
                        if settlement_date is None:
                            settlement_date = date + pd.DateOffset(days=1)
                        settlement_queue.append((settlement_date, new_capital))
                    else:
                        settlement_date = date + pd.DateOffset(days=1)
                        settlement_queue.append((settlement_date, new_capital))

                    positions_before = {ticker: position}
                    positions_after = {}

                    # Add SELL entry to ledger
                    self.ledger.add_entry(
                        date=date,
                        ticker=ticker,
                        action="SELL",
                        quantity=position,
                        price=sell_price,
                        commission=total_costs,
                        tax=tax,
                        cash_before=0.0,
                        cash_after=new_capital,
                        positions_before=positions_before,
                        positions_after=positions_after,
                        notes=f"{reason} triggered. Funds available {settlement_date.strftime('%Y-%m-%d') if hasattr(settlement_date, 'strftime') else settlement_date}",
                    )

                    trades.append(
                        {
                            "buy_date": buy_date,
                            "sell_date": date,
                            "profit_pct": (
                                new_capital - (position * buy_price + buy_fees)
                            )
                            / (position * buy_price + buy_fees),
                            "cumulative_capital": new_capital,
                            "reason": reason,
                            "buy_price": buy_price,
                            "sell_price": sell_price,
                            "fees": buy_fees + total_costs,
                            "tax": tax,
                        }
                    )
                    # capital = new_capital (REMOVED - now handled by settlement queue)
                    position = 0

        # Final Portfolio Value: Position + Cash + Pending Settlement
        final_cap = capital
        if position > 0:
            final_cap += position * float(df.iloc[-1]["Close"])

        # Add any pending cash in the settlement queue
        for _, amount in settlement_queue:
            final_cap += amount

        # Calculate Win Rate
        win_rate = 0.0
        if trades:
            wins = sum(1 for t in trades if t["profit_pct"] > 0)
            win_rate = wins / len(trades)

        init_cap = float(self.config.init_capital)
        roi = (final_cap - init_cap) / init_cap if init_cap > 0 else 0.0

        return {
            "roi": roi,
            "final_capital": final_cap,
            "win_rate": win_rate,
            "total_trades": len(trades),
            "trades": trades,
            "execution_summary": execution_stats,
        }

    def run_model_mode(self, ticker: str, model_type: str) -> Dict[str, Any]:
        """Mode 1: Evaluate a single specific model."""
        # Clear ledger from previous run (no archiving)
        self.ledger.clear()
        horizon_days = self._resolve_prediction_horizon_days()

        self.config.model_type = model_type
        self.model_builder.load_or_build(ticker, target_horizon_days=horizon_days)  # Load once

        # Prepare filtered data (trading days only)
        df_tuple = self._prepare_data(ticker)
        df, features, error = df_tuple
        if error or df is None or features is None:
            return error if error else {"error": "Failed to prepare data"}

        # Bulk pre-calculate predictions on FILTERED data
        all_preds = self._get_bulk_predictions(df, features, model_type)

        def signal(i, df_inner, features_inner, current_cap):
            current_price = float(df_inner.iloc[i]["Close"])
            hurdle = self.get_hurdle_rate(current_cap)
            pred = all_preds[i]
            pred_return = (pred - current_price) / current_price
            return pred_return > hurdle

        result = self._core_run(ticker, signal, df, features)

        # Save ledger to file and clear from memory
        if "error" not in result:
            ledger_filename = f"{ticker}_algorithm_{model_type}_h{horizon_days}d_{self.config.hold_period_value}{self.config.hold_period_unit}.csv"
            ledger_path = self.ledger.save_to_file(filename=ledger_filename)
            result["ledger_path"] = ledger_path

        return result

    def run_strategy_mode(
        self,
        ticker: str,
        models: List[str],
        tie_breaker: Optional[str] = None,
        mode_prefix: str = "consensus",
    ) -> Dict[str, Any]:
        """Mode 2/3: Evaluate strategy sensitivity using multi-model consensus."""
        # Clear ledger from previous run (no archiving)
        self.ledger.clear()
        horizon_days = self._resolve_prediction_horizon_days()

        # Prepare filtered data (trading days only)
        df_tuple = self._prepare_data(ticker)
        df, features, error = df_tuple
        if error or df is None or features is None:
            return error if error else {"error": "Failed to prepare data"}

        # Bulk pre-calculate predictions for all models in the committee on FILTERED data
        committee_preds = {}
        for m_type in models:
            self.config.model_type = m_type
            self.model_builder.load_or_build(ticker, target_horizon_days=horizon_days)
            committee_preds[m_type] = self._get_bulk_predictions(df, features, m_type)

        def signal(i, df_inner, features_inner, current_cap):
            votes = 0
            current_price = float(df_inner.iloc[i]["Close"])
            hurdle = self.get_hurdle_rate(current_cap)
            tie_breaker_bullish = False
            tb_model = tie_breaker if tie_breaker else models[0]

            for m_type in models:
                pred = committee_preds[m_type][i]
                pred_return = (pred - current_price) / current_price
                is_m_bullish = pred_return > hurdle

                if is_m_bullish:
                    votes += 1
                if m_type == tb_model:
                    tie_breaker_bullish = is_m_bullish

            if votes > (len(models) / 2):
                return True
            if votes == (len(models) / 2):
                return tie_breaker_bullish
            return False

        result = self._core_run(ticker, signal, df, features)

        # Save ledger to file and clear from memory
        if "error" not in result:
            ledger_filename = f"{ticker}_{mode_prefix}_h{horizon_days}d_{self.config.hold_period_value}{self.config.hold_period_unit}.csv"
            ledger_path = self.ledger.save_to_file(filename=ledger_filename)
            result["ledger_path"] = ledger_path

        return result

    def _get_bulk_predictions(
        self, df: pd.DataFrame, features: List[str], model_type: str
    ) -> np.ndarray:
        """Helper to get predictions for all rows in one go with memory safety."""
        # Ensure data is clean and use float64 to prevent overflow/inf during cast
        X_all = (
            df[features]
            .replace([np.inf, -np.inf], np.nan)
            .fillna(0)
            .values.astype(np.float64)
        )

        if (
            model_type == "lstm"
            and self.model_builder.model is not None
            and self.model_builder.scaler is not None
        ):
            # LSTM still needs float32 for most backends
            X_all_f32 = X_all.astype(np.float32)
            # Use sequence_length from model_builder for consistency
            seq_len = self.model_builder.sequence_length
            X_scaled = self.model_builder.scaler.transform(X_all_f32).astype(np.float32)

            # Create sequences: at time i, use [i-seq_len:i] to predict i+1
            # This matches training where [i:i+seq_len] predicts target[i+seq_len]=Close[i+seq_len+1]
            valid_indices = np.arange(seq_len, len(df))
            X_seq = np.array(
                [X_scaled[i - seq_len : i] for i in valid_indices], dtype=np.float32
            )

            if len(X_seq) == 0:
                logging.warning(
                    f"Not enough data for LSTM sequences (need >{seq_len} days)"
                )
                return np.zeros(len(df), dtype=np.float32)

            # Batch predict with a smaller batch size to avoid GPU memory overflow on M3
            raw_preds = self.model_builder.model.predict(
                X_seq, batch_size=64, verbose=0
            ).flatten()

            # Inverse transform LSTM predictions if target was scaled
            if self.model_builder.target_scaler is not None:
                raw_preds = self.model_builder.target_scaler.inverse_transform(
                    raw_preds.reshape(-1, 1)
                ).flatten()

            # Pad the beginning with zeros (no predictions for first seq_len days)
            all_preds = np.zeros(len(df), dtype=np.float32)
            all_preds[seq_len:] = raw_preds
            return all_preds

        elif model_type == "prophet" and self.model_builder.model is not None:
            # Prophet bulk predict
            prophet_df = pd.DataFrame({"ds": df.index}).copy()
            prophet_df["ds"] = prophet_df["ds"].dt.tz_localize(None)
            prophet_df["ds"] = prophet_df["ds"] + pd.DateOffset(days=1)

            forecast = self.model_builder.model.predict(prophet_df)
            return forecast["yhat"].values.astype(np.float32)

        elif (
            self.model_builder.model is not None
            and self.model_builder.scaler is not None
        ):
            # Standard SKLearn-like models
            X_scaled = self.model_builder.scaler.transform(X_all).astype(np.float32)
            return self.model_builder.model.predict(X_scaled).astype(np.float32)

        return np.zeros(len(df), dtype=np.float32)
