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
        commission = max(
            broker.min_commission,
            broker.brokerage_fixed + (trade_value * broker.brokerage_rate),
        )

        # 2. Regulatory Fees (Sell-side only)
        reg_fees = 0.0
        if is_sell:
            # SEC Fee: approx 0.0000278 * Value
            sec_fee = trade_value * 0.0000278
            # FINRA TAF: approx 0.000166 per share (capped at $8.30)
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

    def _prepare_data(
        self, ticker: str
    ) -> Tuple[Optional[pd.DataFrame], Optional[List[str]], Optional[Dict[str, str]]]:
        raw_data = self.model_builder.fetch_data(ticker, self.config.backtest_years)
        if raw_data.empty:
            return None, None, {"error": f"No data for {ticker}"}

        df = raw_data.copy()
        df["Returns"] = df["Close"].pct_change()
        df["MA50"] = df["Close"].rolling(50).mean()
        df["MA200"] = df["Close"].rolling(200).mean()

        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df["RSI"] = 100 - (100 / (1 + (gain / (loss + 1e-9))))

        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.ffill(inplace=True)
        df.fillna(0, inplace=True)

        official_start = pd.Timestamp.now() - pd.DateOffset(
            years=self.config.backtest_years
        )
        official_end = pd.Timestamp(df.index[-1])
        self.trading_days = get_usa_trading_days(official_start, official_end)
        df = df[df.index.isin(self.trading_days)]

        if df.empty:
            return None, None, {"error": f"No valid trading days for {ticker}"}

        features = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "Returns",
            "MA50",
            "MA200",
            "RSI",
        ]
        if "MKT_VIX" in df.columns:
            features.append("MKT_VIX")
        if "MKT_Yield10Y" in df.columns:
            features.append("MKT_Yield10Y")

        return df, features, None

    def _core_run(
        self, ticker: str, signal_func: Callable, df: pd.DataFrame, features: List[str]
    ) -> Dict[str, Any]:
        capital = self.config.init_capital
        position, buy_price, buy_date, buy_fees = 0.0, 0.0, None, 0.0
        trades = []
        settlement_queue = []  # T+1 for USA

        for i in range(len(df) - 1):
            date = pd.Timestamp(df.index[i])
            current_price = float(df.iloc[i]["Close"])

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

            if position == 0 and is_bullish:
                fees = self.calculate_fees(capital, is_sell=False)
                new_position = (capital - fees) / current_price
                self.ledger.add_entry(
                    date=date,
                    ticker=ticker,
                    action="BUY",
                    quantity=new_position,
                    price=current_price,
                    commission=fees,
                    cash_before=capital,
                    cash_after=0.0,
                    positions_before={},
                    positions_after={ticker: new_position},
                )
                position, buy_price, buy_date, buy_fees, capital = (
                    new_position,
                    current_price,
                    date,
                    fees,
                    0,
                )

            elif position > 0:
                min_hold_passed = False
                if buy_date:
                    unit = {
                        "day": "days",
                        "week": "weeks",
                        "month": "months",
                        "year": "years",
                    }.get(self.config.hold_period_unit.lower(), "months")
                    min_hold_passed = date >= (
                        buy_date
                        + pd.DateOffset(**{unit: self.config.hold_period_value})
                    )

                sl_p, tp_p = (
                    buy_price * (1 - self.config.stop_loss_threshold),
                    buy_price * (1 + self.config.stop_profit_threshold),
                )
                reason, sell_price = None, 0.0
                low_p, high_p = float(df.iloc[i]["Low"]), float(df.iloc[i]["High"])

                if low_p <= sl_p:
                    reason, sell_price = "stop-loss", sl_p
                elif min_hold_passed:
                    if high_p >= tp_p:
                        reason, sell_price = "take-profit", tp_p
                    elif not is_bullish:
                        reason, sell_price = "model-exit", current_price

                if reason:
                    val = position * sell_price
                    total_friction = self.calculate_fees(
                        val, shares=position, is_sell=True
                    )
                    tax = 0.0
                    if not self.config.w8ben:
                        tax_profile = get_tax_profile(False)
                        profit = (
                            val - (position * buy_price) - (buy_fees + total_friction)
                        )
                        if profit > 0:
                            tax = profit * tax_profile.short_term_cgt_rate

                    new_capital = val - total_friction - tax
                    settlement_date = calculate_trading_days_ahead(
                        date, 1, self.trading_days
                    ) or (date + pd.DateOffset(days=1))
                    settlement_queue.append((settlement_date, new_capital))

                    self.ledger.add_entry(
                        date=date,
                        ticker=ticker,
                        action="SELL",
                        quantity=position,
                        price=sell_price,
                        commission=total_friction,
                        cash_before=0.0,
                        cash_after=new_capital,
                        positions_before={ticker: position},
                        positions_after={},
                        notes=f"{reason} triggered",
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
                            "tax": tax,
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
        df, features, error = self._prepare_data(ticker)
        if error:
            return error

        X_all = df[features].values
        if model_type == "lstm":
            all_preds = []
            seq_len = self.model_builder.sequence_length
            X_scaled = self.model_builder.scaler.transform(X_all)
            for i in range(len(df)):
                if i < seq_len:
                    all_preds.append(float(df.iloc[i]["Close"]))
                else:
                    X_seq = X_scaled[i - seq_len : i].reshape(1, seq_len, -1)
                    all_preds.append(
                        float(self.model_builder.model.predict(X_seq, verbose=0)[0][0])
                    )
        else:
            all_preds = self.model_builder.model.predict(
                self.model_builder.scaler.transform(X_all)
            )

        def signal(i, df_inner, features_inner, current_cap):
            hurdle = self.get_hurdle_rate(current_cap)
            current_price = float(df_inner.iloc[i]["Close"])
            return (all_preds[i] - current_price) / current_price > hurdle

        result = self._core_run(ticker, signal, df, features)
        if "error" not in result:
            result["ledger_path"] = self.ledger.save_to_file(
                filename=f"{ticker}_{model_type}.csv"
            )
        return result

    def run_strategy_mode(
        self, ticker: str, models: List[str], tie_breaker: Optional[str] = None
    ) -> Dict[str, Any]:
        self.ledger.clear()
        df, features, error = self._prepare_data(ticker)
        if error:
            return error

        committee_preds = {}
        for m_type in models:
            self.config.model_type = m_type
            self.model_builder.load_or_build(ticker)
            committee_preds[m_type] = self.model_builder.model.predict(
                self.model_builder.scaler.transform(df[features].values)
            )

        def signal(i, df_inner, features_inner, current_cap):
            votes, hurdle = 0, self.get_hurdle_rate(current_cap)
            current_price = float(df_inner.iloc[i]["Close"])
            tb_model = tie_breaker or models[0]
            tb_bullish = False
            for m in models:
                bullish = (
                    committee_preds[m][i] - current_price
                ) / current_price > hurdle
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
                filename=f"{ticker}_consensus.csv"
            )
        return result
