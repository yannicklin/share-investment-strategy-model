"""
USA AI Trading System - Transaction Ledger

Purpose: Memory-optimized transaction logging for backtest audit trail.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


class TransactionLedger:
    """
    Memory-optimized transaction ledger for backtest audit trail.

    Design:
        - Stores only minimal state during backtest (~2 KB active memory)
        - Batch writes to disk on completion
        - Machine-parseable CSV format (optimized for AI/script analysis)
    """

    def __init__(self):
        """Initialize empty ledger with minimal memory footprint."""
        self.entries: List[Dict[str, Any]] = []
        self.portfolio_state = {
            "cash": 0.0,
            "positions": {},
        }
        self.summary_metrics = {
            "total_trades": 0,
            "total_fees": 0.0,
            "total_tax": 0.0,
        }

    def update_portfolio_state(self, cash: float, positions: Dict[str, float]):
        """Update minimal portfolio tracking (~1 KB)."""
        self.portfolio_state["cash"] = cash
        self.portfolio_state["positions"] = positions.copy()

    def add_entry(
        self,
        date: pd.Timestamp,
        ticker: str,
        action: str,
        quantity: float,
        price: float,
        commission: float,
        cash_before: float,
        cash_after: float,
        positions_before: Dict[str, float],
        positions_after: Dict[str, float],
        strategy: str = "",
        model_votes: Optional[Dict[str, str]] = None,
        confidence: float = 0.0,
        notes: str = "",
    ):
        """Add single transaction entry to ledger buffer."""
        from core.utils import format_date_with_weekday

        entry = {
            "date": format_date_with_weekday(date),
            "ticker": ticker,
            "action": action,
            "quantity": quantity,
            "price": price,
            "total_value": quantity * price,
            "commission": commission,
            "cash_before": cash_before,
            "cash_after": cash_after,
            "positions_before": str(positions_before),
            "positions_after": str(positions_after),
            "strategy": strategy,
            "model_votes": str(model_votes) if model_votes else "",
            "confidence": confidence,
            "notes": notes,
        }

        self.entries.append(entry)
        self.summary_metrics["total_trades"] += 1
        self.summary_metrics["total_fees"] += commission

    def clear(self):
        """Clear ledger entries."""
        self.entries = []
        self.summary_metrics = {
            "total_trades": 0,
            "total_fees": 0.0,
            "total_tax": 0.0,
        }

    def save_to_file(
        self, filename: Optional[str] = None, output_dir: str = "data/ledgers"
    ) -> str:
        """Batch write ledger to CSV file and clear from memory."""
        os.makedirs(output_dir, exist_ok=True)

        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            filename = f"backtest_usa_{timestamp}.csv"

        filepath = os.path.join(output_dir, filename)

        if self.entries:
            df = pd.DataFrame(self.entries)
            df.to_csv(filepath, index=False)
        else:
            pd.DataFrame(
                columns=[
                    "date",
                    "ticker",
                    "action",
                    "quantity",
                    "price",
                    "total_value",
                    "commission",
                    "cash_before",
                    "cash_after",
                    "positions_before",
                    "positions_after",
                    "strategy",
                    "model_votes",
                    "confidence",
                    "notes",
                ]
            ).to_csv(filepath, index=False)

        self.clear()
        return filepath

    def get_summary(self) -> Dict[str, Any]:
        """Get ledger summary metrics."""
        return {
            **self.summary_metrics,
            "portfolio_cash": self.portfolio_state["cash"],
            "portfolio_positions": self.portfolio_state["positions"].copy(),
        }
