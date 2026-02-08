"""
Trading AI System - Central Configuration

Purpose: Defines global constants, broker profiles, and tax logic for the USA market.
Supports "Foreign Investor" profile with W-8BEN settings.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import os
from dataclasses import dataclass
from typing import Dict

# ==============================================================================
# 1. MARKET & DATA SETTINGS
# ==============================================================================
MARKET_COUNTRY = "USA"
CURRENCY_SYMBOL = "$"
TIMEZONE = "US/Eastern"

# Default Ticker Universe (S&P 500 & Nasdaq 100 Leaders)
DEFAULT_TICKERS = [
    "SPY",
    "QQQ",
    "IWM",  # Indexes
    "AAPL",
    "MSFT",
    "NVDA",
    "GOOGL",
    "AMZN",
    "META",
    "TSLA",  # Mag 7
    "AMD",
    "AVGO",
    "COST",
    "PEP",
    "JPM",
    "V",
    "LLY",  # Other Blue Chips
]

# Date Range for Training
START_DATE = "2015-01-01"
END_DATE = "2025-01-01"

# ==============================================================================
# 2. FINANCIAL SETTINGS
# ==============================================================================
INITIAL_CAPITAL = 10000.00  # USD


@dataclass
class BrokerProfile:
    name: str
    brokerage_fixed: float  # Flat fee per trade
    brokerage_rate: float  # Percentage of trade value (0.01 = 1%)
    min_commission: float  # Minimum fee
    fx_rate: float  # FX Spread (0.0070 = 70bps). Not used in USD simulation loop but stored for reference.


# Broker Definitions
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

DEFAULT_BROKER = "Saxo / Global Prime (Classic)"


# ==============================================================================
# 3. TAXATION (FOREIGN INVESTOR / W-8BEN)
# ==============================================================================
@dataclass
class TaxProfile:
    w8ben_filed: bool
    dividend_tax_rate: float
    short_term_cgt_rate: float
    long_term_cgt_rate: float
    description: str


def get_tax_profile(w8ben_filed: bool = True) -> TaxProfile:
    """
    Returns the tax friction profile based on W-8BEN status.
    Note: For AU residents, US CGT is $0 (Treaty).
    """
    if w8ben_filed:
        return TaxProfile(
            w8ben_filed=True,
            dividend_tax_rate=0.15,  # 15% Withholding
            short_term_cgt_rate=0.00,  # 0% US CGT (Treaty)
            long_term_cgt_rate=0.00,  # 0% US CGT (Treaty)
            description="Foreign Investor (W-8BEN Filed)",
        )
    else:
        return TaxProfile(
            w8ben_filed=False,
            dividend_tax_rate=0.30,  # 30% Withholding
            short_term_cgt_rate=0.30,  # Potential Backup Withholding
            long_term_cgt_rate=0.30,
            description="Foreign Investor (No W-8BEN)",
        )


# ==============================================================================
# 4. RISK MANAGEMENT
# ==============================================================================
# Default Stop Loss / Take Profit (Can be overridden by AI)
DEFAULT_STOP_LOSS = 0.05  # 5%
DEFAULT_TAKE_PROFIT = 0.15  # 15%

# Hurdle Rate Components
RISK_FREE_RATE = 0.04  # 4% (Approx 10Y Treasury)
RISK_BUFFER = 0.02  # 2% Extra margin required

# ==============================================================================
# 5. PATHS
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(DATA_DIR, "models")
LEDGERS_DIR = os.path.join(DATA_DIR, "ledgers")

# Ensure directories exist
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(LEDGERS_DIR, exist_ok=True)
