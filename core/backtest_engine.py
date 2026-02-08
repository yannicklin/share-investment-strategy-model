"""
Taiwan Stock AI Trading System - Backtesting Engine

Purpose: Simulates trading strategies on historical Taiwan market data with realistic
constraints (fees, STT, price gaps, T+2 settlement, ±10% limits).

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
        - Brokerage: 0.1425% (standard online discount applied per profile)
        - STT: 0.3% (sell side only, grouped with fees per user preference)
        - Minimum Brokerage: NT$20
        """
        # 1. Brokerage Fee
        # Default is standard rate (0.1425%) with no discount
        broker_rate = 0.001425

        if self.config.cost_profile == "fubon_twn":
            broker_rate = 0.001425 * 0.4  # ~1.8-2.8折, using conservative 0.057%
        elif self.config.cost_profile == "first_twn":
            broker_rate = 0.001425 * 0.6  # ~2.8-3.8折, using conservative 0.0855%

        brokerage = max(20.0, trade_value * broker_rate)

        # 2. Securities Transaction Tax (Sell-side only)
        stt = trade_value * 0.003 if is_sell else 0.0
        return brokerage + stt

    def calculate_income_tax(self, income: float) -> float:
        """
        Taiwan Individual Income Tax (2024 Brackets).

        Note: Domestic stock capital gains are technically 0%, but we implement
        the logic for hurdle-aware income context as requested.
        """
        if income <= 560000:
            return income * 0.05
        if income <= 1260000:
            return income * 0.12 - 39200
        if income <= 2520000:
            return income * 0.20 - 140000
        if income <= 4720000:
            return income * 0.30 - 392000
        return income * 0.40 - 864000

    def get_marginal_tax_rate(self, income: float) -> float:
        """Determines the marginal tax rate based on 2024 Taiwan brackets."""
        if income <= 560000:
            return 0.05
        if income <= 1260000:
            return 0.12
        if income <= 2520000:
            return 0.20
        if income <= 4720000:
            return 0.30
        return 0.40

    def get_hurdle_rate(self, current_capital: float) -> float:
        """Calculates the minimum return % required to break even in Taiwan."""
        if current_capital <= 0:
            return 0.0

        # 1. Transactional Friction (Grouped Brokerage + STT)
        entry_fee = self.calculate_fees(current_capital, is_sell=False)
        exit_fee = self.calculate_fees(current_capital, is_sell=True)
        fees_pct = (entry_fee + exit_fee) / current_capital

        # 2. Risk Buffer (No Income Tax gross-up for Taiwan domestic stocks)
        # As per current regulation, CGT is 0%, so we do not apply the tax multiplier.
        # This keeps the hurdle rate focused on fees + pure risk buffer.
        return fees_pct + self.config.hurdle_risk_buffer

    def _get_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        if data is None or data.empty:
            return pd.DataFrame()
        df = data.copy()

        # Standard indicators
        df["MA5"] = df["Close"].rolling(5).mean()
        df["MA20"] = df["Close"].rolling(20).mean()
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df["RSI"] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        df["MACD"] = (
            df["Close"].ewm(span=12, adjust=False).mean()
            - df["Close"].ewm(span=26, adjust=False).mean()
        )
        df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["Daily_Return"] = df["Close"].pct_change(fill_method=None)

        # KD
        low_9 = df["Low"].rolling(9).min()
        high_9 = df["High"].rolling(9).max()
        rsv = (df["Close"] - low_9) / (high_9 - low_9 + 1e-9) * 100
        df["K"] = rsv.ewm(com=2).mean()
        df["D"] = df["K"].ewm(com=2).mean()

        # Fill missing new features if not present
        for col in [
            "Foreign_Net",
            "Trust_Net",
            "Dealer_Net",
            "Margin_Balance",
            "Short_Balance",
            "Revenue_YoY",
            "USD_TWD",
            "SOX_Index",
            "NASDAQ_Index",
        ]:
            if col not in df.columns:
                df[col] = 0.0

        # CLEANUP: Handle Inf values created by division (e.g. RSI gain/loss)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.ffill(inplace=True)
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
        self.trading_days = get_asx_trading_days(official_start, official_end)
        df = df[df.index.isin(self.trading_days)]

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
            "Foreign_Net",
            "Trust_Net",
            "Dealer_Net",
            "Margin_Balance",
            "Short_Balance",
            "Revenue_YoY",
            "USD_TWD",
            "SOX_Index",
            "NASDAQ_Index",
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
        settlement_queue = []

        for i in range(len(df) - 1):
            date = pd.Timestamp(df.index[i])
            current_price = float(df.iloc[i]["Close"])
            prev_close = float(df.iloc[i - 1]["Close"]) if i > 0 else current_price

            # Process Settlement Queue: T+2
            new_settlement_queue = []
            for avail_date, amount in settlement_queue:
                if date >= avail_date:
                    capital += amount
                else:
                    new_settlement_queue.append((avail_date, amount))
            settlement_queue = new_settlement_queue

            if position == 0:
                if not validate_buy_capacity(capital, {ticker: current_price})[
                    "can_trade"
                ]:
                    continue

            is_bullish = signal_func(
                i,
                df,
                features,
                capital if position == 0 else (position * current_price),
            )

            # Execution Logic with ±10% Price Limits
            limit_up = prev_close * 1.10
            limit_down = prev_close * 0.90

            if position == 0 and is_bullish:
                exec_price = min(current_price, limit_up)
                fees = self.calculate_fees(capital, is_sell=False)
                new_position = (capital - fees) / exec_price

                self.ledger.add_entry(
                    date=date,
                    ticker=ticker,
                    action="BUY",
                    quantity=new_position,
                    price=exec_price,
                    commission=fees,
                    tax=0.0,
                    cash_before=capital,
                    cash_after=0.0,
                    positions_before={},
                    positions_after={ticker: new_position},
                    notes=f"Initial purchase. {'(Cap @ 10%)' if current_price > limit_up else ''}",
                )
                position, buy_price, buy_date, buy_fees, capital = (
                    new_position,
                    exec_price,
                    date,
                    fees,
                    0,
                )

            elif position > 0:
                min_hold_passed = False
                if buy_date is not None and self.trading_days is not None:
                    if self.config.hold_period_unit.lower() == "day":
                        target_date = calculate_trading_days_ahead(
                            buy_date, self.config.hold_period_value, self.trading_days
                        )
                        min_hold_passed = date >= target_date if target_date else False
                    else:
                        unit = {
                            "week": "weeks",
                            "month": "months",
                            "year": "years",
                        }.get(self.config.hold_period_unit.lower(), "months")
                        min_hold_passed = date >= (
                            buy_date
                            + pd.DateOffset(**{unit: self.config.hold_period_value})
                        )

                low_p, high_p = float(df.iloc[i]["Low"]), float(df.iloc[i]["High"])
                sl_p, tp_p = (
                    buy_price * (1 - self.config.stop_loss_threshold),
                    buy_price * (1 + self.config.stop_profit_threshold),
                )

                reason, sell_price = None, 0.0
                if low_p <= sl_p:
                    reason, sell_price = (
                        "stop-loss",
                        max(limit_down, min(sl_p, float(df.iloc[i]["Open"]))),
                    )
                elif min_hold_passed:
                    if high_p >= tp_p:
                        reason, sell_price = (
                            "take-profit",
                            min(limit_up, max(tp_p, float(df.iloc[i]["Open"]))),
                        )
                    elif not is_bullish:
                        reason, sell_price = (
                            "model-exit",
                            max(limit_down, min(current_price, limit_up)),
                        )

                if reason and buy_date is not None:
                    val = position * sell_price
                    total_friction = self.calculate_fees(val, is_sell=True)
                    new_capital = val - total_friction

                    settlement_date = (
                        calculate_trading_days_ahead(date, 2, self.trading_days)
                        if self.trading_days is not None
                        else (date + pd.DateOffset(days=2))
                    )
                    if settlement_date is None:
                        settlement_date = date + pd.DateOffset(days=1)
                    settlement_queue.append((settlement_date, new_capital))

                    self.ledger.add_entry(
                        date=date,
                        ticker=ticker,
                        action="SELL",
                        quantity=position,
                        price=sell_price,
                        commission=total_friction,
                        tax=0.0,
                        cash_before=0.0,
                        cash_after=new_capital,
                        positions_before={ticker: position},
                        positions_after={},
                        notes=f"{reason} triggered. Funds available {settlement_date.strftime('%Y-%m-%d')}. {'(Floor @ -10%)' if sell_price == limit_down else ''}",
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
                            "fees": buy_fees + total_friction,
                            "tax": 0.0,
                        }
                    )
                    position = 0

        final_cap = capital + (
            position * float(df.iloc[-1]["Close"]) if position > 0 else 0
        )
        for _, amount in settlement_queue:
            final_cap += amount
        return {
            "roi": (final_cap - self.config.init_capital) / self.config.init_capital,
            "final_capital": final_cap,
            "win_rate": sum(1 for t in trades if t["profit_pct"] > 0) / len(trades)
            if trades
            else 0.0,
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
            return error or {"error": "Failed to prepare data"}
        all_preds = self._get_bulk_predictions(df, features, model_type)

        def signal(i, df_inner, features_inner, current_cap):
            hurdle = self.get_hurdle_rate(current_cap)
            current_price = float(df_inner.iloc[i]["Close"])
            if current_price <= 1e-9:
                return False
            return (all_preds[i] - current_price) / current_price > hurdle

        result = self._core_run(ticker, signal, df, features)
        if "error" not in result:
            result["ledger_path"] = self.ledger.save_to_file(
                filename=f"{ticker}_{model_type}_{self.config.hold_period_value}{self.config.hold_period_unit}.csv"
            )
        return result

    def run_strategy_mode(
        self, ticker: str, models: List[str], tie_breaker: Optional[str] = None
    ) -> Dict[str, Any]:
        self.ledger.clear()
        df_tuple = self._prepare_data(ticker)
        df, features, error = df_tuple
        if error or df is None or features is None:
            return error or {"error": "Failed to prepare data"}
        committee_preds = {}
        for m_type in models:
            self.config.model_type = m_type
            self.model_builder.load_or_build(ticker)
            # Force 1D array to prevent indexing errors on scalar returns
            preds = self._get_bulk_predictions(df, features, m_type)
            committee_preds[m_type] = np.atleast_1d(preds)

        def signal(i, df_inner, features_inner, current_cap):
            # Ensure index is integer
            idx = int(i)
            votes, hurdle = 0, self.get_hurdle_rate(current_cap)
            current_price = float(df_inner.iloc[idx]["Close"])
            tb_model = tie_breaker or models[0]
            tb_bullish = False

            for m in models:
                # Safe access with bounds checking
                preds_arr = committee_preds[m]
                if idx >= len(preds_arr):
                    continue

                pred_price = float(preds_arr[idx])

                # Safety check for zero price
                if current_price <= 1e-9:
                    bullish = False
                else:
                    bullish = (pred_price - current_price) / current_price > hurdle

                if bullish:
                    votes += 1
                if m == tb_model:
                    tb_bullish = bullish

            return votes > (len(models) / 2) or (
                votes == len(models) / 2 and tb_bullish
            )

        result = self._core_run(ticker, signal, df, features)
        if "error" not in result:
            result["ledger_path"] = self.ledger.save_to_file(
                filename=f"{ticker}_consensus_{self.config.hold_period_value}{self.config.hold_period_unit}.csv"
            )
        return result

    def _get_bulk_predictions(
        self, df: pd.DataFrame, features: List[str], model_type: str
    ) -> np.ndarray:
        # Validate Input Shape
        if df.empty or len(features) == 0:
            return np.zeros(len(df), dtype=np.float32)

        X_all = df[features].values.astype(np.float32)

        # Guard against single-feature mismatch
        if X_all.ndim == 1:
            X_all = X_all.reshape(-1, 1)

        # Ensure model is ready
        if self.model_builder.model is None:
            return np.zeros(len(df), dtype=np.float32)

        if model_type == "lstm" and self.model_builder.scaler:
            seq_len = 30
            X_scaled = self.model_builder.scaler.transform(X_all).astype(np.float32)
            valid_indices = np.arange(seq_len, len(df))
            if len(valid_indices) == 0:
                return np.zeros(len(df), dtype=np.float32)

            X_seq = np.array([X_scaled[i - seq_len : i] for i in valid_indices])
            raw_preds = self.model_builder.model.predict(
                X_seq, batch_size=64, verbose=0
            ).flatten()
            all_preds = np.full(len(df), raw_preds[0], dtype=np.float32)
            all_preds[seq_len:] = raw_preds
            return all_preds

        elif model_type == "prophet":
            p_df = pd.DataFrame({"ds": df.index}).copy()
            p_df["ds"] = p_df["ds"].dt.tz_localize(None) + pd.DateOffset(days=1)
            return self.model_builder.model.predict(p_df)["yhat"].values.astype(
                np.float32
            )

        elif self.model_builder.scaler:
            return self.model_builder.model.predict(
                self.model_builder.scaler.transform(X_all)
            ).astype(np.float32)

        return np.zeros(len(df), dtype=np.float32)
