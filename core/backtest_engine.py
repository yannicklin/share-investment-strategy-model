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
import logging
from typing import List, Dict, Any, Callable, Optional, Tuple, Union
from core.config import Config
from core.model_builder import ModelBuilder
from core.utils import (
    format_date_with_weekday,
    get_twn_trading_days,
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
        - STT: 0.3% (sell side only)
        - Minimum Brokerage: NT$20
        """
        # 1. Brokerage Fee
        broker_rate = 0.001425

        if self.config.cost_profile == "fubon_twn":
            broker_rate = 0.001425 * 0.4
        elif self.config.cost_profile == "first_twn":
            broker_rate = 0.001425 * 0.6

        brokerage = max(20.0, trade_value * broker_rate)

        # 2. Securities Transaction Tax (Sell-side only)
        stt = trade_value * 0.003 if is_sell else 0.0
        return brokerage + stt

    def get_hurdle_rate(self, current_capital: float) -> float:
        """Calculates the minimum return % required to break even in Taiwan."""
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

        # 6. KD (Taiwan Specific)
        low_9 = df["Low"].rolling(9).min()
        high_9 = df["High"].rolling(9).max()
        h_l_diff = high_9 - low_9
        h_l_diff = h_l_diff.replace(0, np.nan)
        rsv = ((df["Close"] - low_9) / (h_l_diff + 1e-9)) * 100
        rsv = rsv.fillna(50)
        df["K"] = rsv.ewm(com=2).mean()
        df["D"] = df["K"].ewm(com=2).mean()

        # 7. FinMind Institutional Data (Taiwan Only)
        if ticker.endswith(".TW"):
            self.model_builder._ensure_finmind_data(ticker)
            fm_data = self.model_builder._finmind_data
            if fm_data is not None and not fm_data.empty:
                finmind_subset = fm_data.shift(1).reindex(df.index).ffill()
                df = df.join(finmind_subset)

        # 8. Market Context Integration
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
        self.trading_days = get_twn_trading_days(official_start, official_end)

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
                f"Dataframe empty for {ticker} after applying market calendar filter."
            )
            return None, None, {"error": f"No valid trading days for {ticker}"}

        # Synchronized Features List
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
            "K",
            "D",
            "Daily_Return",
        ]

        # Add dynamic FinMind features (Taiwan institutional data)
        fm_data = self.model_builder._finmind_data
        if fm_data is not None and not fm_data.empty:
            for col in fm_data.columns:
                if col in df.columns:
                    features.append(col)

        # Add dynamic market features
        if m_data is not None:
            for col in m_data.columns:
                if col in df.columns:
                    features.append(col)

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

            # Safety check: avoid division by zero or negative prices
            if current_price <= 0 or prev_close <= 0:
                continue

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

            # Execution Logic with ±10% Price Limits (Taiwan Specific)
            limit_up = prev_close * 1.10
            limit_down = prev_close * 0.90

            if position == 0 and is_bullish:
                exec_price = min(current_price, limit_up)
                fees = self.calculate_fees(capital, is_sell=False)
                if capital <= fees:
                    continue
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
                position, buy_price, buy_date, buy_fees = (
                    new_position,
                    exec_price,
                    date,
                    fees,
                )
                capital = 0

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

                    # T+2 Settlement for Taiwan
                    settlement_date = None
                    if self.trading_days is not None:
                        settlement_date = calculate_trading_days_ahead(
                            date, 2, self.trading_days
                        )

                    if settlement_date is None:
                        settlement_date = date + pd.DateOffset(days=2)

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
                        notes=f"{reason} triggered. Funds available {settlement_date.strftime('%Y-%m-%d') if hasattr(settlement_date, 'strftime') else settlement_date}. {'(Floor @ -10%)' if sell_price == limit_down else ''}",
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
        init_cap = float(self.config.init_capital)
        roi = (final_cap - init_cap) / init_cap if init_cap > 0 else 0.0

        return {
            "roi": roi,
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
            result["ledger_path"] = self.ledger.save_to_file(
                filename=f"{ticker}_algorithm_{model_type}_{self.config.hold_period_value}{self.config.hold_period_unit}.csv"
            )
        return result

    def run_strategy_mode(
        self,
        ticker: str,
        models: List[str],
        tie_breaker: Optional[str] = None,
        mode_prefix: str = "consensus",
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
        if "error" not in result:
            result["ledger_path"] = self.ledger.save_to_file(
                filename=f"{ticker}_{mode_prefix}_{self.config.hold_period_value}{self.config.hold_period_unit}.csv"
            )
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
            seq_len = self.model_builder.sequence_length
            X_scaled = self.model_builder.scaler.transform(X_all_f32).astype(np.float32)
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
            prophet_df["ds"] = prophet_df["ds"].dt.tz_localize(None)
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
