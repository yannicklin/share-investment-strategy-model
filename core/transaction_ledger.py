"""
ASX AI Trading System - Transaction Ledger

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
    
    Lifecycle:
        - Created fresh at start of each backtest run
        - Automatically cleared when user re-runs (no archiving)
        - Saved to data/ledgers/backtest_{timestamp}.csv on completion
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
        """
        Update minimal portfolio tracking (~1 KB).
        
        Args:
            cash: Current cash balance
            positions: {ticker: units} mapping
        """
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
        """
        Add single transaction entry to ledger.
        
        Note: Only stores entry in memory buffer, not full ledger.
        Call save_to_file() to persist to disk.
        
        Args:
            date: Transaction date (pd.Timestamp)
            ticker: Stock symbol (e.g., "ABB.AX")
            action: BUY, SELL, HOLD
            quantity: Number of units transacted
            price: Price per unit
            commission: Transaction fee
            cash_before: Portfolio cash before transaction
            cash_after: Portfolio cash after transaction
            positions_before: All positions before trade
            positions_after: All positions after trade
            strategy: Strategy name (e.g., "consensus-30d")
            model_votes: Individual model predictions (for consensus)
            confidence: Signal confidence score (0-1)
            notes: Optional metadata
        """
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
            "positions_before": str(positions_before),  # Serialize as string
            "positions_after": str(positions_after),
            "strategy": strategy,
            "model_votes": str(model_votes) if model_votes else "",
            "confidence": confidence,
            "notes": notes,
        }
        
        self.entries.append(entry)
        
        # Update summary metrics (minimal memory)
        self.summary_metrics["total_trades"] += 1
        self.summary_metrics["total_fees"] += commission
    
    def clear(self):
        """
        Clear ledger entries (no archiving).
        
        Note: Called automatically when user re-runs backtest.
        """
        self.entries = []
        self.summary_metrics = {
            "total_trades": 0,
            "total_fees": 0.0,
            "total_tax": 0.0,
        }
    
    def save_to_file(
        self, filename: Optional[str] = None, output_dir: str = "data/ledgers"
    ) -> str:
        """
        Batch write ledger to CSV file and clear from memory.
        
        Args:
            filename: Optional custom filename (defaults to backtest_{timestamp}.csv)
            output_dir: Directory to save ledger files (default: data/ledgers/)
        
        Returns:
            Absolute path to saved file
        
        Notes:
            - Creates output_dir if doesn't exist
            - Uses batch write for better performance than streaming I/O
            - Clears entries from memory after successful write
        """
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            filename = f"backtest_{timestamp}.csv"
        
        filepath = os.path.join(output_dir, filename)
        
        # Batch write to CSV
        if self.entries:
            df = pd.DataFrame(self.entries)
            df.to_csv(filepath, index=False)
        else:
            # Empty ledger - write header only
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
        
        # Clear entries from memory after write
        self.clear()
        
        return filepath
    
    def get_last_entry(self) -> Optional[Dict[str, Any]]:
        """Get most recent transaction entry (for testing/debugging)."""
        return self.entries[-1] if self.entries else None
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get ledger summary metrics.
        
        Returns:
            {
                "total_trades": int,
                "total_fees": float,
                "total_tax": float,
                "portfolio_cash": float,
                "portfolio_positions": dict
            }
        """
        return {
            **self.summary_metrics,
            "portfolio_cash": self.portfolio_state["cash"],
            "portfolio_positions": self.portfolio_state["positions"].copy(),
        }
