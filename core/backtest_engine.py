"""
Taiwan Stock AI Trading System - Backtesting Engine

Purpose: Simulates trading strategies on historical Taiwan market data with realistic
constraints (fees, STT, price gaps, T+2 settlement).

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
import numpy as np
import os
import joblib
from typing import List, Dict, Any, Callable, Optional, Tuple, Union
from core.config import Config
from core.model_builder import ModelBuilder
from core.utils import (
    format_date_with_weekday,
    get_asx_trading_days,
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

    def calculate_fees(self, trade_value: float, is_sell: bool = False) -> float:
        """
        Taiwan Fee Structure:
        - Brokerage: 0.1425% (buy & sell)
        - STT: 0.3% (sell side only)
        - Minimum Brokerage: NT$20
        """
        # 1. Brokerage Fee
        broker_rate = self.config.brokerage_rate
        if self.config.cost_profile == "fubon_twn":
            broker_rate = 0.0006  # Example discounted rate (60% off) for Fubon
        elif self.config.cost_profile == "first_twn":
            broker_rate = 0.001425  # Standard for First Securities

        brokerage = max(20.0, trade_value * broker_rate)

        # 2. Securities Transaction Tax (Sell-side only)
        stt = 0.0
        if is_sell:
            stt = trade_value * 0.003

        return brokerage + stt

    def calculate_ato_tax(self, income: float) -> float:
        """Taiwan has NO capital gains tax for individuals."""
        return 0.0

    def get_marginal_tax_rate(self, income: float) -> float:
        """Taiwan has NO capital gains tax for individuals."""
        return 0.0

    def get_hurdle_rate(self, current_capital: float) -> float:
        """Calculates the minimum return % required to break even in Taiwan."""
        if current_capital <= 0:
            return 0.0

        # 1. Transactional Friction (Fees)
        # Round-trip: Buy (0.1425%) + Sell (0.1425% + 0.3% STT) = ~0.585%
        entry_fee = self.calculate_fees(current_capital, is_sell=False)
        exit_fee = self.calculate_fees(current_capital, is_sell=True)
        fees_pct = (entry_fee + exit_fee) / current_capital

        return fees_pct + self.config.hurdle_risk_buffer

    def _get_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        if data is None or data.empty:
            return pd.DataFrame()

        df = data.copy()
        standard_cols = ["Close", "Open", "High", "Low", "Volume"]

        for col in ["Close", "Open", "High", "Low"]:
            if col not in df.columns:
                found = False
                for c in df.columns:
                    if col.lower() in str(c).lower():
                        df.rename(columns={c: col}, inplace=True)
                        found = True
                        break
                if not found:
                    raise KeyError(f"CRITICAL: Column '{col}' not found.")

        for col in standard_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["Close", "Open", "High", "Low"])

        # Technical Indicators
        df["MACD"] = df["Close"].ewm(span=12).mean() - df["Close"].ewm(span=26).mean()
        df["Signal_Line"] = df["MACD"].ewm(span=9).mean()

        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df["RSI"] = 100 - (100 / (1 + (gain / loss)))

        # KD (Stochastic Oscillator) - Extremely popular in Taiwan
        low_9 = df["Low"].rolling(window=9).min()
        high_9 = df["High"].rolling(window=9).max()
        rsv = (df["Close"] - low_9) / (high_9 - low_9) * 100
        df["K"] = rsv.ewm(com=2).mean()
        df["D"] = df["K"].ewm(com=2).mean()

        df["MA5"], df["MA20"] = (
            df["Close"].rolling(5).mean(),
            df["Close"].rolling(20).mean(),
        )
        df["Daily_Return"] = df["Close"].pct_change(fill_method=None)
        return df.dropna()

    def _prepare_data(
        self, ticker: str
    ) -> Tuple[Optional[pd.DataFrame], Optional[List[str]], Optional[Dict[str, str]]]:
        raw_data = self.model_builder.fetch_data(ticker, self.config.backtest_years)
        if raw_data.empty:
            return None, None, {"error": f"No data for {ticker}"}

        df = self._get_indicators(raw_data)
        if df.empty:
            return None, None, {"error": f"Insufficient data for {ticker}"}

        official_start = pd.Timestamp.now() - pd.DateOffset(
            years=self.config.backtest_years
        )
        official_end = pd.Timestamp(df.index[-1])

        # Using ASX calendar as proxy (need to update utils.py for TWN)
        self.trading_days = get_asx_trading_days(official_start, official_end)

        df = df[df.index.isin(self.trading_days)]
        if df.empty:
            return None, None, {"error": f"No valid trading days for {ticker}"}

        features = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "MA5",
            "MA20",
            "RSI",
            "MACD",
            "Signal_Line",
            "K",
            "D",
            "Daily_Return",
        ]

        return df, features, None

    def _core_run(
        self,
        ticker: str,
        signal_func: Callable[[int, pd.DataFrame, List[str], float], bool],
        df: pd.DataFrame,
        features: List[str],
    ) -> Dict[str, Any]:
        capital = self.config.init_capital
        position, buy_price, buy_date, buy_fees = 0.0, 0.0, None, 0.0
        trades = []
        settlement_queue = []  # List of (available_date, amount)

        for i in range(len(df) - 1):
            date = pd.Timestamp(df.index[i])
            current_price = float(df.iloc[i]["Close"])

            # Process Settlement Queue: T+2
            new_settlement_queue = []
            for avail_date, amount in settlement_queue:
                if date >= avail_date:
                    capital += amount
                else:
                    new_settlement_queue.append((avail_date, amount))
            settlement_queue = new_settlement_queue

            # Portfolio validation
            if position == 0:
                validation = validate_buy_capacity(capital, {ticker: current_price})
                if not validation["can_trade"]:
                    continue

            is_bullish = signal_func(
                i,
                df,
                features,
                capital if position == 0 else (position * current_price),
            )

            if position == 0 and is_bullish:
                fees = self.calculate_fees(capital, is_sell=False)
                new_position = (capital - fees) / current_price

                positions_before = {}
                positions_after = {ticker: new_position}

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
                # Holding Period Logic
                min_hold_passed = False
                if buy_date is not None and self.trading_days is not None:
                    if self.config.hold_period_unit.lower() == "day":
                        target_date = calculate_trading_days_ahead(
                            buy_date, self.config.hold_period_value, self.trading_days
                        )
                        if target_date is not None:
                            min_hold_passed = date >= target_date
                    else:
                        unit_map = {"week": "weeks", "month": "months", "year": "years"}
                        unit = unit_map.get(
                            self.config.hold_period_unit.lower(), "months"
                        )
                        offset = {unit: self.config.hold_period_value}
                        min_hold_passed = date >= (buy_date + pd.DateOffset(**offset))

                low_p, high_p = float(df.iloc[i]["Low"]), float(df.iloc[i]["High"])
                sl_p, tp_p = (
                    buy_price * (1 - self.config.stop_loss_threshold),
                    buy_price * (1 + self.config.stop_profit_threshold),
                )

                reason, sell_price = None, 0.0
                if low_p <= sl_p:
                    reason, sell_price = (
                        "stop-loss",
                        min(sl_p, float(df.iloc[i]["Open"])),
                    )
                elif min_hold_passed:
                    if high_p >= tp_p:
                        reason, sell_price = (
                            "take-profit",
                            max(tp_p, float(df.iloc[i]["Open"])),
                        )
                    elif not is_bullish:
                        reason, sell_price = "model-exit", current_price

                if reason and buy_date is not None:
                    val = position * sell_price
                    s_fees = self.calculate_fees(val, is_sell=True)
                    tax = 0.0
                    new_capital = val - s_fees - tax

                    # T+2 Settlement Delay
                    settlement_date = None
                    if self.trading_days is not None:
                        settlement_date = calculate_trading_days_ahead(
                            date, 2, self.trading_days
                        )
                        if settlement_date is None:
                            settlement_date = date + pd.DateOffset(days=1)
                        settlement_queue.append((settlement_date, new_capital))
                    else:
                        settlement_queue.append(
                            (date + pd.DateOffset(days=2), new_capital)
                        )

                    positions_before = {ticker: position}
                    positions_after = {}

                    self.ledger.add_entry(
                        date=date,
                        ticker=ticker,
                        action="SELL",
                        quantity=position,
                        price=sell_price,
                        commission=s_fees,
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
                            "fees": buy_fees + s_fees,
                            "tax": tax,
                        }
                    )
                    position = 0

        final_cap = capital + (
            position * float(df.iloc[-1]["Close"]) if position > 0 else 0
        )
        for _, amount in settlement_queue:
            final_cap += amount

        win_rate = (
            sum(1 for t in trades if t["profit_pct"] > 0) / len(trades)
            if trades
            else 0.0
        )

        return {
            "roi": (final_cap - self.config.init_capital) / self.config.init_capital,
            "final_capital": final_cap,
            "win_rate": win_rate,
            "total_trades": len(trades),
            "trades": trades,
        }

    def run_model_mode(self, ticker: str, model_type: str) -> Dict[str, Any]:
        self.ledger.clear()
        self.config.model_type = model_type
        self.model_builder.load_or_build(ticker)
        df_tuple = self._prepare_data(ticker)
        df, features, error = df_tuple
        if error or df is None or features is None:
            return error if error else {"error": "Failed to prepare data"}
        all_preds = self._get_bulk_predictions(df, features, model_type)

        def signal(i, df_inner, features_inner, current_cap):
            current_price = float(df_inner.iloc[i]["Close"])
            hurdle = self.get_hurdle_rate(current_cap)
            pred = all_preds[i]
            pred_return = (pred - current_price) / current_price
            return pred_return > hurdle

        result = self._core_run(ticker, signal, df, features)
        if "error" not in result:
            ledger_filename = f"{ticker}_{model_type}_{self.config.hold_period_value}{self.config.hold_period_unit}.csv"
            ledger_path = self.ledger.save_to_file(filename=ledger_filename)
            result["ledger_path"] = ledger_path
        return result

    def run_strategy_mode(
        self, ticker: str, models: List[str], tie_breaker: Optional[str] = None
    ) -> Dict[str, Any]:
        self.ledger.clear()
        df_tuple = self._prepare_data(ticker)
        df, features, error = df_tuple
        if error or df is None or features is None:
            return error if error else {"error": "Failed to prepare data"}
        committee_preds = {}
        for m_type in models:
            self.config.model_type = m_type
            self.model_builder.load_or_build(ticker)
            committee_preds[m_type] = self._get_bulk_predictions(df, features, m_type)

        def signal(i, df_inner, features_inner, current_cap):
            votes = 0
            current_price = float(df_inner.iloc[i]["Close"])
            hurdle = self.get_hurdle_rate(current_cap)
            tb_model = tie_breaker if tie_breaker else models[0]
            tie_breaker_bullish = False
            for m_type in models:
                pred = committee_preds[m_type][i]
                is_m_bullish = (pred - current_price) / current_price > hurdle
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
        if "error" not in result:
            ledger_filename = f"{ticker}_consensus_{self.config.hold_period_value}{self.config.hold_period_unit}.csv"
            ledger_path = self.ledger.save_to_file(filename=ledger_filename)
            result["ledger_path"] = ledger_path
        return result

    def _get_bulk_predictions(
        self, df: pd.DataFrame, features: List[str], model_type: str
    ) -> np.ndarray:
        X_all = df[features].values.astype(np.float32)
        if (
            model_type == "lstm"
            and self.model_builder.model is not None
            and self.model_builder.scaler is not None
        ):
            seq_len = 30
            X_scaled = self.model_builder.scaler.transform(X_all).astype(np.float32)
            valid_indices = np.arange(seq_len, len(df))
            X_seq = np.array([X_scaled[i - seq_len : i] for i in valid_indices])
            raw_preds = self.model_builder.model.predict(
                X_seq, batch_size=64, verbose=0
            ).flatten()
            all_preds = np.zeros(len(df), dtype=np.float32)
            all_preds[seq_len:] = raw_preds
            return all_preds
        elif model_type == "prophet" and self.model_builder.model is not None:
            prophet_df = pd.DataFrame({"ds": df.index}).copy()
            prophet_df["ds"] = prophet_df["ds"].dt.tz_localize(None) + pd.DateOffset(
                days=1
            )
            forecast = self.model_builder.model.predict(prophet_df)
            return forecast["yhat"].values.astype(np.float32)
        elif (
            self.model_builder.model is not None
            and self.model_builder.scaler is not None
        ):
            X_scaled = self.model_builder.scaler.transform(X_all).astype(np.float32)
            return self.model_builder.model.predict(X_scaled).astype(np.float32)
        return np.zeros(len(df), dtype=np.float32)
