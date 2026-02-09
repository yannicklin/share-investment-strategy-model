"""
USA AI Trading System - Backtesting Engine

Purpose: Simulates trading strategies on historical US market data with realistic
constraints (fees, SEC/FINRA, T+1 settlement, W-8BEN tax).

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Callable, Optional, Tuple

from core.config import Config, BROKERS, get_tax_profile
from core.model_builder import ModelBuilder
from core.utils import (
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

    def _prepare_data(
        self, ticker: str
    ) -> Tuple[Optional[pd.DataFrame], Optional[List[str]], Optional[Dict[str, str]]]:
        """Prepare and filter dataframe for backtesting."""
        raw_data = self.model_builder.fetch_data(ticker, self.config.backtest_years)
        if raw_data.empty:
            return None, None, {"error": f"No data for {ticker}"}

        df = raw_data.copy()

        # Indicators (Synchronized with ModelBuilder)
        df["MA5"] = df["Close"].rolling(window=5).mean()
        df["MA20"] = df["Close"].rolling(window=20).mean()
        df["MA50"] = df["Close"].rolling(window=50).mean()

        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        df["RSI"] = 100 - (100 / (1 + rs))

        exp1 = df["Close"].ewm(span=12, adjust=False).mean()
        exp2 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = exp1 - exp2
        df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()

        df["BB_Middle"] = df["Close"].rolling(window=20).mean()
        df["BB_Std"] = df["Close"].rolling(window=20).std()
        df["BB_Upper"] = df["BB_Middle"] + (2 * df["BB_Std"])
        df["BB_Lower"] = df["BB_Middle"] - (2 * df["BB_Std"])
        df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / (df["BB_Middle"] + 1e-9)

        high_low = df["High"] - df["Low"]
        high_close = np.abs(df["High"] - df["Close"].shift())
        low_close = np.abs(df["Low"] - df["Close"].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["ATR"] = tr.rolling(window=14).mean()

        # Market Context
        self.model_builder._ensure_market_data()
        m_data = self.model_builder._market_data
        if m_data is not None and not m_data.empty:
            market_subset = m_data.shift(1).reindex(df.index).ffill()
            df = df.join(market_subset)

        df["Daily_Return"] = df["Close"].pct_change(fill_method=None)

        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.ffill(inplace=True)
        df.fillna(0, inplace=True)

        # Determine official start/end dates
        official_start = pd.Timestamp.now().normalize() - pd.DateOffset(
            years=self.config.backtest_years
        )

        # Normalize index for robust comparison
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()

        official_end = pd.Timestamp(df.index[-1])
        self.trading_days = get_usa_trading_days(official_start, official_end)

        # Filter to valid trading days
        df = df[df.index.isin(self.trading_days)]

        if df.empty:
            return (
                None,
                None,
                {
                    "error": f"No valid trading days for {ticker} after calendar filtering"
                },
            )

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

        if m_data is not None:
            for col in m_data.columns:
                col_str = str(col)
                if col_str in df.columns and col_str not in features:
                    features.append(col_str)

        return df, features, None

    def _core_run(
        self,
        ticker: str,
        signal_func: Callable[[int, pd.DataFrame, List[str], float], bool],
        df: pd.DataFrame,
        features: List[str],
    ) -> Dict[str, Any]:
        """Shared engine logic for backtesting."""
        capital = float(self.config.init_capital)
        position, buy_price, buy_date, buy_fees = 0.0, 0.0, None, 0.0
        trades = []
        settlement_queue = []

        for i in range(len(df) - 1):
            date_ts = pd.Timestamp(df.index[i])
            current_price = float(df.iloc[i]["Close"])

            # Process Settlement
            new_settlement_queue = []
            for avail_date, amount in settlement_queue:
                if date_ts >= pd.Timestamp(avail_date):
                    capital += float(amount)
                else:
                    new_settlement_queue.append((avail_date, amount))
            settlement_queue = new_settlement_queue

            if position == 0:
                validation = validate_buy_capacity(capital, {ticker: current_price})
                if not validation["can_trade"]:
                    continue

            is_bullish = bool(
                signal_func(
                    i,
                    df,
                    features,
                    capital if position == 0 else (position * current_price),
                )
            )

            if position == 0 and is_bullish:
                fees = self.calculate_fees(capital, is_sell=False)
                new_position = (capital - fees) / current_price

                self.ledger.add_entry(
                    date=date_ts,
                    ticker=ticker,
                    action="BUY",
                    quantity=new_position,
                    price=current_price,
                    commission=fees,
                    cash_before=capital,
                    cash_after=0.0,
                    positions_before={},
                    positions_after={ticker: new_position},
                    notes="Initial purchase",
                )

                position, buy_price, buy_date, buy_fees, capital = (
                    new_position,
                    current_price,
                    date_ts,
                    fees,
                    0.0,
                )

            elif position > 0:
                min_hold_passed = False
                if buy_date is not None and self.trading_days is not None:
                    if self.config.hold_period_unit.lower() == "day":
                        target_date = calculate_trading_days_ahead(
                            pd.Timestamp(buy_date),
                            self.config.hold_period_value,
                            self.trading_days,
                        )
                        if target_date is not None:
                            min_hold_passed = date_ts >= target_date
                    else:
                        unit_map = {"week": "weeks", "month": "months", "year": "years"}
                        unit = unit_map.get(
                            self.config.hold_period_unit.lower(), "months"
                        )
                        offset = {unit: self.config.hold_period_value}
                        min_hold_passed = date_ts >= (
                            pd.Timestamp(buy_date) + pd.DateOffset(**offset)
                        )

                low_p, high_p = float(df.iloc[i]["Low"]), float(df.iloc[i]["High"])
                sl_p = buy_price * (1.0 - self.config.stop_loss_threshold)
                tp_p = buy_price * (1.0 + self.config.stop_profit_threshold)

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

                    # T+1 Settlement for USA
                    settlement_date = None
                    if self.trading_days is not None:
                        settlement_date = calculate_trading_days_ahead(
                            date_ts, 1, self.trading_days
                        )

                    if settlement_date is None:
                        settlement_date = date_ts + pd.DateOffset(days=1)

                    settlement_queue.append((settlement_date, new_capital))

                    self.ledger.add_entry(
                        date=date_ts,
                        ticker=ticker,
                        action="SELL",
                        quantity=position,
                        price=sell_price,
                        commission=total_costs,
                        tax=tax,
                        cash_before=0.0,
                        cash_after=new_capital,
                        positions_before={ticker: position},
                        positions_after={},
                        notes=f"{reason} triggered. Available {settlement_date.strftime('%Y-%m-%d')}",
                    )

                    trades.append(
                        {
                            "buy_date": buy_date,
                            "sell_date": date_ts,
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
                    position = 0.0

        # Final Portfolio Value
        final_cap = capital
        if position > 0:
            final_cap += position * float(df.iloc[-1]["Close"])
        for _, amount in settlement_queue:
            final_cap += amount

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
        }

    def run_model_mode(self, ticker: str, model_type: str) -> Dict[str, Any]:
        """Mode 1: Evaluate a single specific model."""
        self.ledger.clear()
        self.config.model_type = model_type
        self.model_builder.load_or_build(ticker)

        df_tuple = self._prepare_data(ticker)
        df, features, error = df_tuple
        if error or df is None or features is None:
            return error if error else {"error": "Failed to prepare data"}

        all_preds = self._get_bulk_predictions(df, features, model_type)

        def signal(
            i: int,
            df_inner: pd.DataFrame,
            features_inner: List[str],
            current_cap: float,
        ) -> bool:
            hurdle = self.get_hurdle_rate(current_cap)
            current_price = float(df_inner.iloc[i]["Close"])
            pred = all_preds[i]
            pred_return = (pred - current_price) / current_price
            return bool(pred_return > hurdle)

        result = self._core_run(ticker, signal, df, features)
        if "error" not in result:
            ledger_filename = f"{ticker}_{model_type}_{self.config.hold_period_value}{self.config.hold_period_unit}.csv"
            result["ledger_path"] = self.ledger.save_to_file(filename=ledger_filename)
        return result

    def run_strategy_mode(
        self, ticker: str, models: List[str], tie_breaker: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mode 2: Evaluate strategy sensitivity using multi-model consensus."""
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

        def signal(
            i: int,
            df_inner: pd.DataFrame,
            features_inner: List[str],
            current_cap: float,
        ) -> bool:
            votes = 0
            current_price = float(df_inner.iloc[i]["Close"])
            hurdle = self.get_hurdle_rate(current_cap)
            tb_model = tie_breaker if tie_breaker else models[0]
            tie_breaker_bullish = False

            for m_type in models:
                pred = committee_preds[m_type][i]
                pred_return = (pred - current_price) / current_price
                is_m_bullish = bool(pred_return > hurdle)
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
            result["ledger_path"] = self.ledger.save_to_file(filename=ledger_filename)
        return result

    def _get_bulk_predictions(
        self, df: pd.DataFrame, features: List[str], model_type: str
    ) -> np.ndarray:
        """Standardized bulk prediction helper."""
        X_all = df[features].values.astype(np.float32)

        if (
            model_type == "lstm"
            and self.model_builder.model is not None
            and self.model_builder.scaler is not None
        ):
            seq_len = self.model_builder.sequence_length
            X_scaled = self.model_builder.scaler.transform(X_all).astype(np.float32)

            valid_indices = np.arange(seq_len, len(df))
            X_seq = np.array(
                [X_scaled[i - seq_len : i] for i in valid_indices], dtype=np.float32
            )

            if len(X_seq) == 0:
                return np.zeros(len(df), dtype=np.float32)

            raw_preds = self.model_builder.model.predict(
                X_seq, batch_size=64, verbose=0
            ).flatten()

            if self.model_builder.target_scaler is not None:
                raw_preds = self.model_builder.target_scaler.inverse_transform(
                    raw_preds.reshape(-1, 1)
                ).flatten()

            all_preds = np.zeros(len(df), dtype=np.float32)
            all_preds[seq_len:] = raw_preds
            return all_preds

        elif model_type == "prophet" and self.model_builder.model is not None:
            prophet_df = pd.DataFrame({"ds": df.index}).copy()
            prophet_df["ds"] = pd.to_datetime(prophet_df["ds"]).dt.tz_localize(None)
            prophet_df["ds"] = prophet_df["ds"] + pd.DateOffset(days=1)
            forecast = self.model_builder.model.predict(prophet_df)
            return forecast["yhat"].values.astype(np.float32)

        elif (
            self.model_builder.model is not None
            and self.model_builder.scaler is not None
        ):
            X_scaled = self.model_builder.scaler.transform(X_all).astype(np.float32)
            return self.model_builder.model.predict(X_scaled).astype(np.float32)

        return np.zeros(len(df), dtype=np.float32)
