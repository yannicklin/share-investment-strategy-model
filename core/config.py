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

    rebuild_model: bool = False
    target_stock_codes: List[str] = field(
        default_factory=lambda: [
            "2330.TW",  # TSMC (台積電)
            "2317.TW",  # Hon Hai (鴻海)
            "2454.TW",  # MediaTek (聯發科)
            "2308.TW",  # Delta (台達電)
            "2303.TW",  # UMC (聯電)
            "2881.TW",  # Fubon Financial (富邦金)
            "2882.TW",  # Cathay Financial (國泰金)
            "2412.TW",  # Chunghwa Telecom (中華電)
            "2382.TW",  # Quanta (廣達)
            "3711.TW",  # ASE Technology (日月光)
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
    model_type: str = "random_forest"
    model_types: List[str] = field(
        default_factory=lambda: ["random_forest", "catboost"]
    )
    data_source: str = "yfinance"

    # Cost & Tax Profiles
    cost_profile: str = "default"  # "default", "fubon_twn", or "first_twn"
    annual_income: float = 960000.0  # Annual income in TWD (Default for TW branch)
    hurdle_risk_buffer: float = 0.005  # 0.5% extra buffer


def load_config() -> Config:
    """Loads configuration settings."""
    return Config()
