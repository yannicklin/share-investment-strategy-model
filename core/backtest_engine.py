"""Backtesting engine for evaluating AI trading strategies."""

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
        self, ticker: str, signal_func: Callable[[int, pd.DataFrame, List[str]], bool]
    ) -> Dict[str, Any]:
        """The shared engine logic for both modes."""
        raw_data = self.model_builder.fetch_data(ticker, self.config.backtest_years)
        if raw_data.empty:
            return {"error": f"No data for {ticker}"}

        df = self._get_indicators(raw_data)
        if df.empty:
            return {"error": f"Insufficient data after indicators for {ticker}"}

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
        trades, equity_history = [], []

        for i in range(len(df) - 1):
            date, current_price = df.index[i], float(df.iloc[i]["Close"])
            equity_history.append(
                {
                    "date": date,
                    "capital": float(
                        position * current_price if position > 0 else capital
                    ),
                }
            )

            is_bullish = signal_func(i, df, features)

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
            "equity_history": equity_history,
        }

    def run_model_mode(self, ticker: str, model_type: str) -> Dict[str, Any]:
        """Mode 1: Evaluate a single specific model."""
        self.config.model_type = model_type
        self.model_builder.load_or_build(ticker)  # Load once

        def signal(i, df, features):
            current_price = float(df.iloc[i]["Close"])
            if model_type == "lstm":
                if i < 30:
                    return False
                X = df.iloc[i - 29 : i + 1][features].values
                return self.model_builder.predict(X, date=df.index[i]) > current_price
            return (
                self.model_builder.predict(
                    df.iloc[i][features].values, date=df.index[i]
                )
                > current_price
            )

        return self._core_run(ticker, signal)

    def run_strategy_mode(
        self, ticker: str, models: List[str], tie_breaker: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mode 2: Evaluate strategy sensitivity using multi-model consensus."""
        # Pre-load all models and scalers into memory
        model_instances = {}
        for m_type in models:
            self.config.model_type = m_type
            self.model_builder.load_or_build(ticker)
            model_instances[m_type] = (
                self.model_builder.model,
                self.model_builder.scaler,
            )

        def signal(i, df, features):
            votes = 0
            current_price = float(df.iloc[i]["Close"])
            tie_breaker_bullish = False
            tb_model = tie_breaker if tie_breaker else models[0]

            for m_type in models:
                # Restore model state for prediction
                self.model_builder.model, self.model_builder.scaler = model_instances[
                    m_type
                ]
                self.config.model_type = m_type

                if m_type == "lstm":
                    if i < 30:
                        is_m_bullish = False
                    else:
                        pred = self.model_builder.predict(
                            df.iloc[i - 29 : i + 1][features].values, date=df.index[i]
                        )
                        is_m_bullish = pred > current_price
                else:
                    pred = self.model_builder.predict(
                        df.iloc[i][features].values, date=df.index[i]
                    )
                    is_m_bullish = pred > current_price

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
