"""
USA AI Trading System - Configuration Management

Purpose: Configuration dataclass for system parameters including tickers,
capital, thresholds, and backtesting settings for the US market.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict


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


# Global Constants for USA - Using conservative (worst-case) rates
BROKERS: Dict[str, BrokerProfile] = {
    "Saxo / Global Prime (Classic)": BrokerProfile(
        name="Classic Standard",
        brokerage_fixed=5.00,
        brokerage_rate=0.0008,
        min_commission=5.00,
        fx_rate=0.0050,
    ),
    "Stake (Standard)": BrokerProfile(
        name="Stake",
        brokerage_fixed=0.00,
        brokerage_rate=0.0001,  # 0.01% for trades > $30k
        min_commission=3.00,  # Flat $3 for trades <= $30k
        fx_rate=0.00,
    ),
    "Interactive Brokers (Pro Fixed)": BrokerProfile(
        name="IBKR Pro Fixed",
        brokerage_fixed=0.00,
        brokerage_rate=0.005,  # Estimated per-share commission as rate (~50bps)
        min_commission=1.00,
        fx_rate=0.00002,
    ),
}


def get_tax_profile(w8ben_filed: bool = True) -> TaxProfile:
    """Returns the tax profile based on W-8BEN status."""
    if w8ben_filed:
        return TaxProfile(
            w8ben_filed=True,
            dividend_tax_rate=0.15,
            short_term_cgt_rate=0.00,  # Treaty benefit
            long_term_cgt_rate=0.00,
            description="Foreign Investor (W-8BEN Filed - 0% CGT, 15% Div)",
        )
    else:
        return TaxProfile(
            w8ben_filed=False,
            dividend_tax_rate=0.30,
            short_term_cgt_rate=0.30,  # Backup withholding
            long_term_cgt_rate=0.30,
            description="Foreign Investor (No W-8BEN - 30% CGT, 30% Div)",
        )


@dataclass
class Config:
    """Central configuration class aligned with ASX/TWN API."""

    rebuild_model: bool = False
    target_stock_codes: List[str] = field(
        default_factory=lambda: [
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
    )
    backtest_years: int = 5
    stop_loss_threshold: float = 0.05
    stop_profit_threshold: float = 0.15
    model_path: str = "data/models/"
    ledger_path: str = "data/ledgers/"
    init_capital: float = 3000.00
    hold_period_unit: str = "month"
    hold_period_value: int = 1
    hurdle_risk_buffer: float = 0.02
    risk_free_rate: float = 0.04
    annual_income: float = 0.0  # Not used in USA CGT logic (0% for W-8BEN)

    # Model Settings
    model_type: str = "random_forest"
    model_types: List[str] = field(
        default_factory=lambda: [
            "random_forest",
            "catboost",
        ]
    )
    scaler_type: str = "robust"

    # Market & Cost Settings
    cost_profile: str = "Saxo / Global Prime (Classic)"

    w8ben: bool = True
    market_country: str = "USA"
    currency_symbol: str = "$"
    timezone: str = "US/Eastern"

    # Market & Macro Data Sources
    market_indices: dict = field(
        default_factory=lambda: {
            "SP500": "^GSPC",
            "Nasdaq100": "^NDX",
            "VIX": "^VIX",
            "Yield10Y": "^TNX",
        }
    )
    macro_indicators: dict = field(
        default_factory=lambda: {
            "Gold": "GC=F",
            "Oil": "CL=F",
            "USD/JPY": "JPY=X",
        }
    )

    def __post_init__(self):
        # Ensure directories exist
        os.makedirs(self.model_path, exist_ok=True)
        os.makedirs(self.ledger_path, exist_ok=True)


def load_config() -> Config:
    """Helper to return a fresh config instance."""
    return Config()
