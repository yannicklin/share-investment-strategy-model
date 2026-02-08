"""
Trading AI System - Backtest Engine (USA Edition)

Purpose: Core simulation engine for backtesting trading strategies on US market data.
Implements "Consensus Voting" logic and tax-aware friction (W-8BEN support).

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Any
from core.config import (
    BROKERS,
    DEFAULT_BROKER,
    get_tax_profile,
    INITIAL_CAPITAL,
    DEFAULT_STOP_LOSS,
    DEFAULT_TAKE_PROFIT,
)

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BacktestEngine:
    def __init__(self, data: pd.DataFrame, initial_capital: float = INITIAL_CAPITAL):
        self.data = data.copy()
        self.capital = initial_capital
        self.positions = 0
        self.entry_price = 0.0
        self.stop_loss = DEFAULT_STOP_LOSS
        self.take_profit = DEFAULT_TAKE_PROFIT
        self.history = []  # Log of trades

        # Load Defaults
        self.broker = BROKERS[DEFAULT_BROKER]
        self.tax_profile = get_tax_profile(w8ben_filed=True)  # Default: W-8BEN Filed

    def run_strategy(self, signals: pd.Series) -> pd.DataFrame:
        """
        Executes the trading strategy based on the provided signals series.
        Signal 1 = BUY, 0 = SELL/HOLD.
        """
        logger.info("Starting Backtest...")

        if signals.empty or self.data.empty:
            logger.warning("No data or signals to backtest.")
            return pd.DataFrame()

        # Align signals with data
        df = self.data.copy()
        df["Signal"] = signals
        df["Holdings"] = 0.0
        df["Cash"] = self.capital
        df["Total"] = self.capital

        for i in range(1, len(df)):
            price = df["Close"].iloc[i]
            prev_price = df["Close"].iloc[i - 1]
            signal = df["Signal"].iloc[i]

            # Position Management Logic
            if self.positions > 0:
                # Check Exit Conditions (Stop Loss / Take Profit)
                pnl_pct = (price - self.entry_price) / self.entry_price

                exit_signal = False
                exit_reason = ""

                if pnl_pct <= -self.stop_loss:
                    exit_signal = True
                    exit_reason = "Stop Loss"
                elif pnl_pct >= self.take_profit:
                    exit_signal = True
                    exit_reason = "Take Profit"
                elif signal == 0:  # Model says SELL
                    exit_signal = True
                    exit_reason = "Model Signal"

                if exit_signal:
                    self._sell(price, df.index[i], reason=exit_reason)

            elif self.positions == 0 and signal == 1:
                # Buy Signal
                self._buy(price, df.index[i])

            # Update Daily Portfolio Value
            current_value = self.capital + (self.positions * price)
            df.at[df.index[i], "Total"] = current_value
            df.at[df.index[i], "Cash"] = self.capital
            df.at[df.index[i], "Holdings"] = self.positions * price

        return df

    def _buy(self, price: float, date, shares: int = 0):
        """Executes a BUY order."""
        # Calculate max shares we can buy
        # Account for brokerage fee buffer
        cost_basis = price
        if self.broker.brokerage_rate > 0:
            cost_basis += price * self.broker.brokerage_rate

        # Determine quantity
        if shares == 0:
            shares = int((self.capital - self.broker.brokerage_fixed) / cost_basis)

        if shares > 0:
            cost = shares * price
            commission = max(
                self.broker.min_commission,
                self.broker.brokerage_fixed + (cost * self.broker.brokerage_rate),
            )

            total_cost = cost + commission

            if total_cost <= self.capital:
                self.capital -= total_cost
                self.positions += shares
                self.entry_price = price

                self.history.append(
                    {
                        "Date": date,
                        "Action": "BUY",
                        "Price": price,
                        "Shares": shares,
                        "Commission": commission,
                        "Total": -total_cost,
                        "Reason": "Entry",
                    }
                )

    def _sell(self, price: float, date, reason: str = "Exit"):
        """Executes a SELL order."""
        if self.positions > 0:
            proceeds = self.positions * price
            commission = max(
                self.broker.min_commission,
                self.broker.brokerage_fixed + (proceeds * self.broker.brokerage_rate),
            )

            # Tax Calculation (US Source)
            gross_profit = proceeds - (self.positions * self.entry_price)

            # Capital Gains Tax (US) - $0 if W-8BEN filed (Treaty), else 30% backup?
            # Config says 0% for W-8BEN filed.
            cgt = 0.0
            if gross_profit > 0:
                # Check Tax Profile
                if self.tax_profile.w8ben_filed:
                    cgt = 0.0  # Treaty Benefit
                else:
                    cgt = (
                        gross_profit * self.tax_profile.short_term_cgt_rate
                    )  # Backup Withholding 30%

            # Regulatory Fees (SEC/FINRA) - approx 0.0000278 * Value
            reg_fees = proceeds * 0.0000278

            net_proceeds = proceeds - commission - cgt - reg_fees

            self.capital += net_proceeds

            self.history.append(
                {
                    "Date": date,
                    "Action": "SELL",
                    "Price": price,
                    "Shares": self.positions,
                    "Commission": commission,
                    "Tax": cgt,
                    "RegFees": reg_fees,
                    "Total": net_proceeds,
                    "Reason": reason,
                }
            )

            self.positions = 0
            self.entry_price = 0.0

    def get_performance_summary(self) -> Dict[str, Any]:
        """Calculates performance metrics."""
        if not self.history:
            return {"ROI": 0.0, "Total Trades": 0}

        df_hist = pd.DataFrame(self.history)
        # Calculate final equity (Cash + Holdings Value)
        # Ideally, we should mark-to-market any open positions at the end.
        final_equity = self.capital
        if self.positions > 0 and not self.data.empty:
            last_price = self.data["Close"].iloc[-1]
            final_equity += self.positions * last_price

        roi = ((final_equity - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100

        # Estimate trades (BUY + SELL = 2 actions per trade approx)
        num_trades = len(df_hist[df_hist["Action"] == "SELL"])

        return {
            "Net Profit ($)": round(final_equity - INITIAL_CAPITAL, 2),
            "ROI (%)": round(roi, 2),
            "Total Trades": num_trades,
            "Broker": self.broker.name,
            "Tax Profile": self.tax_profile.description,
        }
