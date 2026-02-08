"""
USA AI Trading System - Central Configuration

Purpose: Defines global constants, broker profiles, and tax logic for the USA market.
Supports "Foreign Investor" profile with W-8BEN settings.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class BrokerProfile:
    name: str
    brokerage_fixed: float  # Flat fee per trade
    brokerage_rate: float  # Percentage of trade value
    min_commission: float  # Minimum fee
    fx_rate: float  # FX Spread (reference)


@dataclass
class TaxProfile:
    w8ben_filed: bool
    dividend_tax_rate: float
    short_term_cgt_rate: float
    long_term_cgt_rate: float
    description: str


# Global Constants
BROKERS: Dict[str, BrokerProfile] = {
    "Saxo / Global Prime (Classic)": BrokerProfile(
        name="Classic Standard",
        brokerage_fixed=5.00,
        brokerage_rate=0.0008,
        min_commission=5.00,
        fx_rate=0.0050,
    ),
    "Stake (Retail)": BrokerProfile(
        name="Stake",
        brokerage_fixed=3.00,
        brokerage_rate=0.00,
        min_commission=3.00,
        fx_rate=0.0070,
    ),
    "Interactive Brokers (Pro)": BrokerProfile(
        name="IBKR Pro",
        brokerage_fixed=0.00,
        brokerage_rate=0.00005,
        min_commission=1.00,
        fx_rate=0.00002,
    ),
}


def get_tax_profile(w8ben_filed: bool = True) -> TaxProfile:
    """Returns the tax friction profile based on W-8BEN status."""
    if w8ben_filed:
        return TaxProfile(
            w8ben_filed=True,
            dividend_tax_rate=0.15,
            short_term_cgt_rate=0.00,
            long_term_cgt_rate=0.00,
            description="Foreign Investor (W-8BEN Filed)",
        )
    else:
        return TaxProfile(
            w8ben_filed=False,
            dividend_tax_rate=0.30,
            short_term_cgt_rate=0.30,
            long_term_cgt_rate=0.30,
            description="Foreign Investor (No W-8BEN)",
        )


class Config:
    """Central configuration class aligned with ASX/TWN API."""

    def __init__(self):
        self.market_country = "USA"
        self.currency_symbol = "$"
        self.timezone = "US/Eastern"

        # Paths
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(self.base_dir, "data")
        self.model_path = os.path.join(self.data_path, "models")
        self.ledger_path = os.path.join(self.data_path, "ledgers")

        # Ensure directories
        os.makedirs(self.model_path, exist_ok=True)
        os.makedirs(self.ledger_path, exist_ok=True)

        # Backtest Settings
        self.init_capital = 10000.00
        self.backtest_years = 5  # Default to 5 years
        self.hold_period_unit = "month"
        self.hold_period_value = 1
        self.stop_loss_threshold = 0.05
        self.stop_profit_threshold = 0.15
        self.hurdle_risk_buffer = 0.02
        self.risk_free_rate = 0.04
        self.annual_income = 0  # Not used in USA CGT logic (0% for W-8BEN)

        # Model Settings
        self.model_type = "random_forest"
        self.model_types = ["random_forest", "gradient_boosting", "lstm", "prophet"]
        self.scaler_type = "standard"
        self.rebuild_model = False

        # Market Universe
        self.target_stock_codes = [
            "SPY",
            "QQQ",
            "AAPL",
            "MSFT",
            "NVDA",
            "GOOGL",
            "AMZN",
            "META",
            "TSLA",
        ]
        self.cost_profile = "Saxo / Global Prime (Classic)"
        self.w8ben = True


def load_config() -> Config:
    """Helper to return a fresh config instance."""
    return Config()
