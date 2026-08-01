"""
Taiwan Stock AI Trading System - Backtesting Engine

Purpose: Simulates trading strategies on historical Taiwan market data with realistic
constraints (fees, STT, price gaps, T+2 settlement, ±10% limits).

Author: Yannick
Copyright (c) 2026 Yannick
"""

import logging
from collections.abc import Callable
from typing import Any, Optional

import numpy as np
import pandas as pd

from core.config import Config
from core.model_builder import FINMIND_FEATURE_COLUMNS, ModelBuilder
from core.transaction_ledger import TransactionLedger
from core.trend_detector import detect_trend
from core.utils import (
    calculate_trading_days_ahead,
    get_twn_trading_days,
    validate_buy_capacity,
)


class BacktestEngine:
    """Simulates trading strategy on historical data with support for multiple modes."""

    def __init__(self, config: Config, model_builder: ModelBuilder):
        self.config = config
        self.model_builder = model_builder
        self.ledger = TransactionLedger()
        self.trading_days: pd.DatetimeIndex | None = None
        self.logger = logging.getLogger(__name__)

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
    ) -> tuple[pd.DataFrame | None, list[str] | None, dict[str, str] | None]:
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
            fm_data = self.model_builder.get_finmind_data_for_ticker(ticker)
            finmind_subset = fm_data.shift(1).reindex(df.index).ffill().fillna(0)
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

        # Add fixed FinMind features (Taiwan institutional data)
        if ticker.endswith(".TW"):
            for col in FINMIND_FEATURE_COLUMNS:
                if col in df.columns:
                    features.append(col)

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
        buy_date: pd.Timestamp | None,
        current_date: pd.Timestamp,
    ) -> tuple[str | None, float]:
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
        signal_func: Callable[[int, pd.DataFrame, list[str], float], bool],
        df: pd.DataFrame,
        features: list[str],
        exit_signal_func: Callable[[int, pd.DataFrame, list[str], float], bool]
        | None = None,
    ) -> dict[str, Any]:
        capital = self.config.init_capital
        position, buy_price, buy_date, buy_fees = 0.0, 0.0, None, 0.0
        trades = []
        settlement_queue = []

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
                    execution_stats["buy_capacity_checks"] += 1
                    execution_stats["buy_capacity_blocks"] += 1
                    continue
                execution_stats["buy_capacity_checks"] += 1

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
                execution_stats["buy_signals"] += 1
                exec_price = min(current_price, limit_up)
                fees = self.calculate_fees(capital, is_sell=False)
                if capital <= fees:
                    execution_stats["buy_fee_blocks"] += 1
                    continue
                execution_stats["buy_executions"] += 1
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
                # Check for pre-consensus exits (stop-loss, take-profit)
                exit_reason, exit_price = self._get_pre_consensus_exit(
                    i, df, buy_price, buy_date, date
                )

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

                # Use pre-consensus exit if available
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
                    if min_hold_passed:
                        # Use horizon-1 exit model if provided; fall back to BUY signal
                        _exit_fn = (
                            exit_signal_func
                            if exit_signal_func is not None
                            else signal_func
                        )
                        if not _exit_fn(i, df, features, position * current_price):
                            reason, sell_price = (
                                "model-exit",
                                max(limit_down, min(current_price, limit_up)),
                            )
                            execution_stats["sell_model_exit"] += 1

                # Apply Taiwan's ±10% price limits to the sell price
                if reason and sell_price > 0:
                    sell_price = max(limit_down, min(sell_price, limit_up))

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
            "execution_summary": execution_stats,
        }

    def run_model_mode(self, ticker: str, model_type: str) -> dict[str, Any]:
        self.logger.info(
            f"[{ticker}] ========== Starting {model_type.upper()} Model Run =========="
        )
        self.ledger.clear()
        self.config.model_type = model_type
        horizon_days = self._resolve_prediction_horizon_days()
        self.logger.debug(f"[{ticker}] Horizon days: {horizon_days}")

        self.model_builder.load_or_build(ticker, target_horizon_days=horizon_days)
        df_tuple = self._prepare_data(ticker)
        df, features, error = df_tuple
        if error or df is None or features is None:
            self.logger.error(f"[{ticker}] Data preparation failed: {error}")
            return error if error else {"error": "Failed to prepare data"}

        self.logger.debug(
            f"[{ticker}] Data prepared: {len(df)} rows, {len(features)} features"
        )

        # Bulk predictions for BUY signal (horizon=N)
        self.logger.debug(f"[{ticker}] Generating BUY predictions for {model_type}...")
        all_buy_preds = self._get_bulk_predictions(ticker, df, features, model_type)
        self.logger.debug(
            f"[{ticker}] BUY predictions shape: {all_buy_preds.shape}, non-zero: {np.count_nonzero(all_buy_preds)}"
        )

        # Load exit model (horizon=1) if buy_horizon > 1
        all_exit_preds = None
        if horizon_days > 1:
            exit_builder = ModelBuilder(self.config)
            exit_builder.load_exit_model(ticker, buy_horizon_days=horizon_days)
            all_exit_preds = self._get_bulk_predictions(
                ticker, df, features, model_type, builder=exit_builder
            )

        def signal_buy(i, df_inner, features_inner, current_cap):
            current_price = float(df_inner.iloc[i]["Close"])
            hurdle = self.get_hurdle_rate(current_cap)
            pred = all_buy_preds[i]
            pred_return = (pred - current_price) / current_price
            
            # Log first 5 bars for diagnosis
            if i < 5:
                self.logger.debug(
                    f"[{ticker}] [BUY] Bar {i}: price={current_price:.2f}, pred={pred:.2f}, "
                    f"pred_return={pred_return:.4f} ({pred_return*100:.2f}%), hurdle={hurdle:.4f} ({hurdle*100:.2f}%), "
                    f"signal={pred_return > hurdle}, capital={current_cap:.2f}"
                )
            
            return pred_return > hurdle

        def signal_exit(i, df_inner, features_inner, current_cap):
            if all_exit_preds is None or i >= len(all_exit_preds):
                return True  # No exit model → default to bullish (don't exit)
            current_price = float(df_inner.iloc[i]["Close"])
            hurdle = self.get_hurdle_rate(current_cap)
            pred = all_exit_preds[i]
            pred_return = (pred - current_price) / current_price
            return (
                pred_return > hurdle
            )  # True = exit confirmed, False = stay in position

        result = self._core_run(
            ticker, signal_buy, df, features, exit_signal_func=signal_exit
        )
        if "error" not in result:
            trade_count = len(self.ledger.entries) if self.ledger.entries else 0
            roi = result.get("roi", 0.0)
            self.logger.info(
                f"[{ticker}] {model_type.upper()} Results: Trades={trade_count}, ROI={roi:.2f}%"
            )
            result["ledger_path"] = self.ledger.save_to_file(
                filename=f"{ticker}_algorithm_{model_type}_h{horizon_days}d_{self.config.hold_period_value}{self.config.hold_period_unit}.csv"
            )
        else:
            self.logger.error(
                f"[{ticker}] {model_type.upper()} failed: {result.get('error', 'unknown error')}"
            )
        return result

    def run_strategy_mode(
        self,
        ticker: str,
        models: list[str],
        tie_breaker: str | None = None,
        mode_prefix: str = "consensus",
    ) -> dict[str, Any]:
        self.ledger.clear()
        horizon_days = self._resolve_prediction_horizon_days()
        df_tuple = self._prepare_data(ticker)
        df, features, error = df_tuple
        if error or df is None or features is None:
            return error if error else {"error": "Failed to prepare data"}

        # Load BUY models (horizon=N)
        committee_buy_preds = {}
        for m_type in models:
            self.config.model_type = m_type
            load_status = self.model_builder.load_or_build(ticker, target_horizon_days=horizon_days)
            self.logger.info(
                f"[{ticker}] Loaded BUY {m_type} model (horizon={horizon_days}d): status={load_status}, "
                f"model exists={self.model_builder.model is not None}"
            )
            committee_buy_preds[m_type] = self._get_bulk_predictions(
                ticker, df, features, m_type
            )

        # Load EXIT models (horizon=1) if buy_horizon > 1
        committee_exit_preds = {}
        if horizon_days > 1:
            for m_type in models:
                self.config.model_type = m_type
                exit_builder = ModelBuilder(self.config)
                exit_builder.load_exit_model(ticker, buy_horizon_days=horizon_days)
                committee_exit_preds[m_type] = self._get_bulk_predictions(
                    ticker, df, features, m_type, builder=exit_builder
                )

        def signal_buy(i, df_inner, features_inner, current_cap):
            votes = 0
            current_price = float(df_inner.iloc[i]["Close"])
            hurdle = self.get_hurdle_rate(current_cap)
            tie_breaker_bullish = False
            tb_model = tie_breaker if tie_breaker else models[0]
            
            # For logging first 5 bars
            model_votes_debug = {}

            for m_type in models:
                pred = committee_buy_preds[m_type][i]
                pred_return = (pred - current_price) / current_price
                is_m_bullish = pred_return > hurdle
                model_votes_debug[m_type] = {
                    "pred": pred,
                    "pred_return": pred_return,
                    "is_bullish": is_m_bullish
                }

                if is_m_bullish:
                    votes += 1
                if m_type == tb_model:
                    tie_breaker_bullish = is_m_bullish
            
            # Log first 5 bars for diagnosis
            if i < 5:
                self.logger.debug(
                    f"[{ticker}] [CONSENSUS BUY] Bar {i}: price={current_price:.2f}, hurdle={hurdle:.4f} ({hurdle*100:.2f}%), "
                    f"votes={votes}/{len(models)}, details={model_votes_debug}"
                )

            if votes > (len(models) / 2):
                return True
            if votes == (len(models) / 2):
                return tie_breaker_bullish
            return False

        # WP-7.6: Phase 7 trend analysis for dynamic sell friction
        trend_data_for_consensus = {}
        for idx in range(len(df)):
            df_window = df.iloc[
                max(0, idx - 60) : idx + 1
            ]  # 60 days lookback for indicators
            if len(df_window) >= 50:
                trend_result = detect_trend(df_window, ticker)
                trend_data_for_consensus[idx] = trend_result.get("trend", "RANGEBOUND")
            else:
                trend_data_for_consensus[idx] = "RANGEBOUND"

        def signal_exit(i, df_inner, features_inner, current_cap):
            if not committee_exit_preds or i >= len(df_inner):
                return True  # No exit models → default to bullish (don't exit)

            votes = 0
            current_price = float(df_inner.iloc[i]["Close"])
            hurdle = self.get_hurdle_rate(current_cap)
            tie_breaker_bullish = False
            tb_model = tie_breaker if tie_breaker else models[0]

            # WP-7.6: Get dynamic sell_friction based on trend
            trend = trend_data_for_consensus.get(i, "RANGEBOUND")
            TREND_MULTIPLIERS = {
                "UPTREND": 5.0,  # Higher threshold: let winners run
                "DOWNTREND": 2.0,  # Lower threshold: quick exits
                "RANGEBOUND": 3.0,  # Neutral
            }
            sell_friction = TREND_MULTIPLIERS.get(trend, 3.0)

            for m_type in models:
                if m_type not in committee_exit_preds or i >= len(
                    committee_exit_preds[m_type]
                ):
                    continue
                pred = committee_exit_preds[m_type][i]
                pred_return = (pred - current_price) / current_price
                # WP-7.6: Apply dynamic friction multiplier
                is_m_bullish = pred_return > (hurdle * sell_friction)

                if is_m_bullish:
                    votes += 1
                if m_type == tb_model:
                    tie_breaker_bullish = is_m_bullish

            if votes > (len(models) / 2):
                return True  # Exit confirmed
            if votes == (len(models) / 2):
                return tie_breaker_bullish
            return False  # Stay in position

        result = self._core_run(
            ticker, signal_buy, df, features, exit_signal_func=signal_exit
        )
        if "error" not in result:
            result["ledger_path"] = self.ledger.save_to_file(
                filename=f"{ticker}_{mode_prefix}_h{horizon_days}d_{self.config.hold_period_value}{self.config.hold_period_unit}.csv"
            )
        return result

    def _get_bulk_predictions(
        self,
        ticker: str,
        df: pd.DataFrame,
        features: list[str],
        model_type: str,
        builder: Optional["ModelBuilder"] = None,
    ) -> np.ndarray:
        """Helper to get predictions for all rows in one go with memory safety."""
        _builder = builder if builder is not None else self.model_builder

        # Ensure data is clean and use float64 to prevent overflow/inf during cast
        X_all = (
            df[features]
            .replace([np.inf, -np.inf], np.nan)
            .fillna(0)
            .values.astype(np.float64)
        )

        if (
            model_type == "lstm"
            and _builder.model is not None
            and _builder.price_scaler is not None
        ):
            # LSTM uses multi-scaler architecture (price, volume, technical)
            # Apply the same multi-scaler transform used during training
            X_all_f32 = X_all.astype(np.float32)
            X_scaled = _builder._apply_multi_scalers_transform(X_all_f32).astype(
                np.float32
            )
            seq_len = _builder.sequence_length
            valid_indices = np.arange(seq_len, len(df))
            X_seq = np.array(
                [X_scaled[i - seq_len : i] for i in valid_indices], dtype=np.float32
            )

            if len(X_seq) == 0:
                self.logger.warning(f"[{ticker}] [LSTM] No valid sequences generated")
                return np.zeros(len(df), dtype=np.float32)

            raw_preds = _builder.model.predict(
                X_seq, batch_size=64, verbose=0
            ).flatten()

            if _builder.target_scaler is not None:
                raw_preds = _builder.target_scaler.inverse_transform(
                    raw_preds.reshape(-1, 1)
                ).flatten()

            all_preds = np.zeros(len(df), dtype=np.float32)
            all_preds[seq_len:] = raw_preds
            return all_preds

        elif model_type == "lstm" and (
            _builder.model is None or _builder.price_scaler is None
        ):
            self.logger.error(
                f"[{ticker}] [LSTM] Model or price_scaler is None! model={_builder.model is not None}, price_scaler={_builder.price_scaler is not None}"
            )
            return np.zeros(len(df), dtype=np.float32)

        elif model_type == "prophet" and _builder.model is not None:
            prophet_df = pd.DataFrame({"ds": df.index}).copy()
            prophet_df["ds"] = prophet_df["ds"].dt.tz_localize(None)
            prophet_df["ds"] = prophet_df["ds"] + pd.DateOffset(
                days=_builder.target_horizon_days
            )
            forecast = _builder.model.predict(prophet_df)
            preds = forecast["yhat"].values.astype(np.float32)
            return preds

        # Tree models (random_forest, catboost, ngboost) use raw data without scaling
        elif (
            model_type in ("random_forest", "catboost", "ngboost")
            and _builder.model is not None
        ):
            preds = _builder.model.predict(X_all).astype(np.float32)
            return preds

        elif _builder.model is not None and _builder.scaler is not None:
            X_scaled = _builder.scaler.transform(X_all).astype(np.float32)
            preds = _builder.model.predict(X_scaled).astype(np.float32)
            return preds

        elif _builder.model is not None:
            # Fallback for any other model type without scaler
            preds = _builder.model.predict(X_all).astype(np.float32)
            return preds

        else:
            self.logger.error(
                f"[{ticker}] [{model_type.upper()}] Model is None or insufficient configuration"
            )
            return np.zeros(len(df), dtype=np.float32)
