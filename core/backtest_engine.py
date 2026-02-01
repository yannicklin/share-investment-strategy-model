"""
ASX AI Trading System - Backtesting Engine

Purpose: Simulates trading strategies on historical data with realistic
constraints (fees, taxes, price gaps, T+1 settlement).

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
import numpy as np
import os
import joblib
from typing import List, Dict, Any, Callable, Optional
from core.config import Config
from core.model_builder import ModelBuilder


class BacktestEngine:
    """Simulates trading strategy on historical data with support for multiple modes."""

    def __init__(self, config: Config, model_builder: ModelBuilder):
        self.config = config
        self.model_builder = model_builder

    def calculate_fees(self, trade_value: float) -> float:
        if self.config.cost_profile == "cmc_markets":
            return max(11.0, trade_value * 0.0010)
        return (
            (trade_value * self.config.brokerage_rate)
            + (trade_value * self.config.clearing_rate)
            + self.config.settlement_fee
        )

    def calculate_ato_tax(self, income: float) -> float:
        if income <= 18200:
            return 0
        if income <= 45000:
            return (income - 18200) * 0.16
        if income <= 135000:
            return 4288 + (income - 45000) * 0.30
        if income <= 190000:
            return 31288 + (income - 135000) * 0.37
        return 51638 + (income - 190000) * 0.45

    def get_marginal_tax_rate(self, income: float) -> float:
        """Determines the marginal tax rate based on 2024-25 ATO brackets."""
        if income <= 18200:
            return 0.0
        if income <= 45000:
            return 0.16
        if income <= 135000:
            return 0.30
        if income <= 190000:
            return 0.37
        return 0.45

    def get_hurdle_rate(self, current_capital: float) -> float:
        """Calculates the minimum return % required to break even after fees, tax, and buffer."""
        if current_capital <= 0:
            return 0.0

        # 1. Transactional Friction (Fees)
        entry_fee = self.calculate_fees(current_capital)
        exit_fee = self.calculate_fees(current_capital)
        fees_pct = (entry_fee + exit_fee) / current_capital

        # 2. Tax Friction
        # We need a profit that remains above the buffer AFTER tax.
        # Since tax only applies to the GAIN, we 'gross up' the risk buffer.
        marginal_rate = self.get_marginal_tax_rate(self.config.annual_income)

        # If tax rate is 100% (impossible), avoid division by zero
        tax_multiplier = 1.0 / (1.0 - marginal_rate) if marginal_rate < 1.0 else 1.0

        # Tax-adjusted buffer ensures the target 'risk buffer' is net of tax
        adjusted_buffer = self.config.hurdle_risk_buffer * tax_multiplier

        return fees_pct + adjusted_buffer

    def _get_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df["MACD"] = df["Close"].ewm(span=12).mean() - df["Close"].ewm(span=26).mean()
        df["Signal_Line"] = df["MACD"].ewm(span=9).mean()
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df["RSI"] = 100 - (100 / (1 + (gain / loss)))
        df["MA5"], df["MA20"] = (
            df["Close"].rolling(5).mean(),
            df["Close"].rolling(20).mean(),
        )
        df["Daily_Return"] = df["Close"].pct_change()
        return df.dropna()

    def _core_run(
        self,
        ticker: str,
        signal_func: Callable[[int, pd.DataFrame, List[str], float], bool],
    ) -> Dict[str, Any]:
        """The shared engine logic for both modes."""
        raw_data = self.model_builder.fetch_data(ticker, self.config.backtest_years)
        if raw_data.empty:
            return {"error": f"No data for {ticker}"}

        df = self._get_indicators(raw_data)
        if df.empty:
            return {"error": f"Insufficient data for {ticker}"}

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
            "Daily_Return",
        ]

        capital = self.config.init_capital
        position, buy_price, buy_date, buy_fees = 0.0, 0.0, None, 0.0
        trades = []

        for i in range(len(df) - 1):
            date, current_price = df.index[i], float(df.iloc[i]["Close"])

            is_bullish = signal_func(
                i,
                df,
                features,
                capital if position == 0 else (position * current_price),
            )

            if position == 0 and is_bullish:
                fees = self.calculate_fees(capital)
                position = (capital - fees) / current_price
                buy_price, buy_date, buy_fees = current_price, date, fees
                capital = 0
            elif position > 0:
                unit_map = {
                    "day": "days",
                    "month": "months",
                    "quarter": "weeks",
                    "year": "years",
                }
                offset = (
                    {"weeks": 13 * self.config.hold_period_value}
                    if self.config.hold_period_unit == "quarter"
                    else {
                        unit_map[
                            self.config.hold_period_unit
                        ]: self.config.hold_period_value
                    }
                )

                # Check if enough time passed
                min_hold_passed = False
                if buy_date is not None:
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
                    s_fees = self.calculate_fees(val)
                    g_profit = val - (position * buy_price) - (buy_fees + s_fees)
                    tax = 0.0
                    if g_profit > 0:
                        disc = 0.5 if (date - buy_date).days >= 365 else 1.0
                        tax = self.calculate_ato_tax(
                            self.config.annual_income + g_profit * disc
                        ) - self.calculate_ato_tax(self.config.annual_income)
                    capital = val - s_fees - tax
                    trades.append(
                        {
                            "buy_date": buy_date,
                            "sell_date": date,
                            "profit_pct": (capital - (position * buy_price + buy_fees))
                            / (position * buy_price + buy_fees),
                            "cumulative_capital": capital,
                            "reason": reason,
                            "buy_price": buy_price,
                            "sell_price": sell_price,
                            "fees": buy_fees + s_fees,
                            "tax": tax,
                        }
                    )
                    position = 0

        final_cap = position * float(df.iloc[-1]["Close"]) if position > 0 else capital

        # Calculate Win Rate
        win_rate = 0.0
        if trades:
            wins = sum(1 for t in trades if t["profit_pct"] > 0)
            win_rate = wins / len(trades)

        return {
            "roi": (final_cap - self.config.init_capital) / self.config.init_capital,
            "final_capital": final_cap,
            "win_rate": win_rate,
            "total_trades": len(trades),
            "trades": trades,
        }

    def run_model_mode(self, ticker: str, model_type: str) -> Dict[str, Any]:
        """Mode 1: Evaluate a single specific model."""
        self.config.model_type = model_type
        self.model_builder.load_or_build(ticker)  # Load once

        raw_data = self.model_builder.fetch_data(ticker, self.config.backtest_years)
        if raw_data.empty:
            return {"error": f"No data for {ticker}"}
        df = self._get_indicators(raw_data)
        if df.empty:
            return {"error": f"Insufficient data for {ticker}"}

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
            "Daily_Return",
        ]

        # Bulk pre-calculate predictions
        print(f"Pre-calculating bulk predictions for {model_type}...")
        all_preds = self._get_bulk_predictions(df, features, model_type)

        def signal(i, df_inner, features_inner, current_cap):
            current_price = float(df_inner.iloc[i]["Close"])
            hurdle = self.get_hurdle_rate(current_cap)
            pred = all_preds[i]
            pred_return = (pred - current_price) / current_price
            return pred_return > hurdle

        return self._core_run(ticker, signal)

    def run_strategy_mode(
        self, ticker: str, models: List[str], tie_breaker: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mode 2: Evaluate strategy sensitivity using multi-model consensus."""
        raw_data = self.model_builder.fetch_data(ticker, self.config.backtest_years)
        if raw_data.empty:
            return {"error": f"No data for {ticker}"}
        df = self._get_indicators(raw_data)
        if df.empty:
            return {"error": f"Insufficient data for {ticker}"}

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
            "Daily_Return",
        ]

        # Bulk pre-calculate predictions for all models in the committee
        committee_preds = {}
        for m_type in models:
            self.config.model_type = m_type
            self.model_builder.load_or_build(ticker)
            print(f"Pre-calculating bulk predictions for {m_type}...")
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

        return self._core_run(ticker, signal)

    def _get_bulk_predictions(
        self, df: pd.DataFrame, features: List[str], model_type: str
    ) -> np.ndarray:
        """Helper to get predictions for all rows in one go with memory safety."""
        X_all = df[features].values.astype(np.float32)

        if (
            model_type == "lstm"
            and self.model_builder.model is not None
            and self.model_builder.scaler is not None
        ):
            # LSTM needs sequences - pre-allocate to save memory
            seq_len = 30
            X_scaled = self.model_builder.scaler.transform(X_all).astype(np.float32)
            X_seq = np.zeros((len(df), seq_len, len(features)), dtype=np.float32)

            for i in range(len(df)):
                if i >= seq_len:
                    X_seq[i] = X_scaled[i - seq_len + 1 : i + 1]

            # Batch predict
            batch_preds = self.model_builder.model.predict(
                X_seq, batch_size=256, verbose=0
            )
            return batch_preds.flatten()

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
