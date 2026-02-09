"""
USA AI Trading System - Transaction Ledger

Purpose: High-performance memory-resident ledger for tracking buy/sell
executions with automated CSV persistence.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
import os
import time
from typing import List, Dict, Any, Optional


class TransactionLedger:
    """
    Manages a session-based transaction history with minimal memory footprint.

    Lifecycle:
        - Created fresh at start of each backtest run
        - Automatically cleared when user re-runs (no archiving)
        - Saved to data/ledgers/backtest_{timestamp}.csv on completion
    """

    def __init__(self):
        self.entries: List[Dict[str, Any]] = []
        self.summary = {
            "total_trades": 0,
            "total_costs": 0.0,
            "total_tax": 0.0,
            "portfolio_cash": 0.0,
            "portfolio_positions": {},
        }

    def update_summary(self, cash: float, positions: Dict[str, float]):
        """
        Update minimal portfolio tracking (~1 KB).

        Args:
            cash: Current cash balance
            positions: {ticker: units} mapping
        """
        self.summary["portfolio_cash"] = cash
        self.summary["portfolio_positions"] = positions

    def add_entry(
        self,
        date: pd.Timestamp,
        ticker: str,
        action: str,
        quantity: float,
        price: float,
        commission: float = 0.0,
        tax: float = 0.0,
        cash_before: float = 0.0,
        cash_after: float = 0.0,
        positions_before: Optional[Dict] = None,
        positions_after: Optional[Dict] = None,
        strategy: str = "N/A",
        model_votes: str = "N/A",
        confidence: float = 0.0,
        notes: str = "",
    ):
        """
        Add single transaction entry to ledger.

        Args:
            date: Transaction date (pd.Timestamp)
            ticker: Stock symbol (e.g., "AAPL")
            action: BUY, SELL, HOLD
            quantity: Number of units transacted
            price: Price per unit
            commission: Transaction fee
            tax: Government tax or regulatory fees
            cash_before: Portfolio cash before transaction
            cash_after: Portfolio cash after transaction
            positions_before: All positions before trade
            positions_after: All positions after trade
            strategy: Strategy name
            model_votes: Individual model predictions
            confidence: Signal confidence score (0-1)
            notes: Optional metadata
        """
        entry = {
            "timestamp": pd.Timestamp.now(),
            "trade_date": date,
            "ticker": ticker,
            "action": action,
            "quantity": round(quantity, 4),
            "price": round(price, 2),
            "total_value": round(quantity * price, 2),
            "commission": round(commission, 2),
            "tax": round(tax, 2),
            "cash_before": round(cash_before, 2),
            "cash_after": round(cash_after, 2),
            "positions_before": str(positions_before or {}),
            "positions_after": str(positions_after or {}),
            "strategy": strategy,
            "votes": model_votes,
            "confidence": round(confidence, 2),
            "notes": notes,
        }
        self.entries.append(entry)

        # Update summary metrics
        if action == "SELL":
            self.summary["total_trades"] += 1
        self.summary["total_costs"] += commission
        self.summary["total_tax"] += tax

    def clear(self):
        """Clear ledger entries."""
        self.entries = []
        self.summary = {
            "total_trades": 0,
            "total_costs": 0.0,
            "total_tax": 0.0,
            "portfolio_cash": 0.0,
            "portfolio_positions": {},
        }

    def save_to_file(
        self, filename: Optional[str] = None, output_dir: str = "data/ledgers/"
    ) -> str:
        """Batch write ledger to CSV file and clear from memory."""
        os.makedirs(output_dir, exist_ok=True)

        if not filename:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"backtest_usa_{timestamp}.csv"

        file_path = os.path.join(output_dir, filename)

        try:
            if not self.entries:
                df = pd.DataFrame(
                    columns=[
                        "timestamp",
                        "trade_date",
                        "ticker",
                        "action",
                        "quantity",
                        "price",
                        "total_value",
                        "commission",
                        "tax",
                        "cash_before",
                        "cash_after",
                        "positions_before",
                        "positions_after",
                        "strategy",
                        "votes",
                        "confidence",
                        "notes",
                    ]
                )
            else:
                df = pd.DataFrame(self.entries)

            df.to_csv(file_path, index=False)
            self.entries = []
            return os.path.abspath(file_path)
        except Exception as e:
            print(f"Error saving ledger: {e}")
            return ""

    def get_last_entry(self) -> Optional[Dict[str, Any]]:
        """Get most recent transaction entry."""
        return self.entries[-1] if self.entries else None

    def get_summary(self) -> Dict[str, Any]:
        """Get ledger summary metrics."""
        return self.summary
