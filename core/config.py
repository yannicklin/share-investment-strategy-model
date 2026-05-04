"""
Taiwan Stock AI Trading System - Configuration Management

Purpose: Configuration dataclass for Taiwan market (TWSE/TPEx).
Supports market-specific fee structures for Fubon (富邦) and First (第一) Securities.

Author: Yannick
Copyright (c) 2026 Yannick
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    """System configuration parameters."""

    target_stock_codes: List[str] = field(
        default_factory=lambda: [
            "2330.TW",  # TSMC (台積電)
            "2317.TW",  # Hon Hai (鴻海)
            "2454.TW",  # MediaTek (聯發科)
            "2308.TW",  # Delta (台達電)
            "2303.TW",  # UMC (聯電)
            "2882.TW",  # Cathay Financial (國泰金)
            "2412.TW",  # Chunghwa Telecom (中華電)
            "2382.TW",  # Quanta (廣達)
            "3711.TW",  # ASE Technology (日月光)
            "006208.TW",  # 富邦台50 EFT
        ]
    )
    backtest_years: int = 5
    stop_loss_threshold: float = 0.10  # Taiwan daily limit is 10%
    stop_profit_threshold: float = 0.30
    model_path: str = "data/models/"
    init_capital: float = 100000.0  # Initial capital in TWD (NT$100,000)
    hold_period_unit: str = "month"
    hold_period_value: int = 1

    # Taiwan Industry Averages / Standards
    brokerage_rate: float = 0.001425  # 0.1425% (Standard)
    stt_rate: float = 0.003  # 0.3% STT (Sell-side only)

    scaler_type: str = "robust"
    weighting_type: str = "normal"  # "normal" or "recency"
    # Recency weighting multiplier: half_life = backtest_years * multiplier
    # Controls decay aggressiveness in exponential weighting for recent data emphasis:
    #   0.5x = Fast decay (extreme recent bias, ~25% CPU overhead)
    #   1.0x = Moderate recency (balanced, ~50% CPU overhead) - DEFAULT
    #   1.5x = Gentle recency (less extreme, ~75% CPU overhead)
    #   2.0x = Softer recency (~100% CPU overhead)
    #   3.0x = Slowest decay (minimal recent bias, ~150% CPU overhead)
    recency_half_life_multiplier: float = 1.0
    model_type: str = "random_forest"
    # Available: ["random_forest", "ngboost", "catboost", "prophet", "lstm"]
    model_types: List[str] = field(
        default_factory=lambda: ["random_forest", "catboost"]
    )

    # Market & Macro Data Sources
    market_indices: dict = field(
        default_factory=lambda: {
            "TAIEX": "^TWII",
            "SP500": "^GSPC",
            "SOX": "^SOX",
            "NASDAQ": "^IXIC",
        }
    )
    macro_indicators: dict = field(
        default_factory=lambda: {
            "TWD_USD": "TWD=X",
            "Gold": "GC=F",
            "VIX": "^VIX",
        }
    )
    cost_profile: str = "default"  # "default", "fubon_twn", or "first_twn"
    annual_income: float = 960000.0  # Annual income in TWD (Default for TW branch)
    hurdle_risk_buffer: float = (
        0.005  # 0.5% default, adjustable in 0.1% increments via UI
    )
    super_stars_workers: int = 4  # Parallel worker count for Find Super Stars mode


def load_config() -> Config:
    """Loads configuration settings."""
    return Config()
