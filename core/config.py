"""
AI Trading Bot System - Configuration Management (Multi-Market Architecture)

Purpose: Configuration dataclass for system parameters including tickers,
capital, thresholds, and backtesting settings. Supports multiple markets
(ASX, USA, TWN) with market-specific configurations.

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
            "ABB.AX",
            "SIG.AX",
            "IOZ.AX",
            "INR.AX",
            "IMU.AX",
            "MQG.AX",
            "PLS.AX",
            "XRO.AX",
            "TCL.AX",
            "SHL.AX",
        ]
    )
    backtest_years: int = 5
    stop_loss_threshold: float = 0.15
    stop_profit_threshold: float = 0.30
    model_path: str = "models/"
    init_capital: float = 3000.0
    hold_period_unit: str = "month"
    hold_period_value: int = 1
    brokerage_rate: float = 0.0012  # 0.12%
    clearing_rate: float = 0.0000225  # 0.00225%
    settlement_fee: float = 1.5  # $1.5 fixed
    tax_rate: float = 0.25  # 25% tax
    scaler_type: str = "robust"  # "standard" or "robust"
    model_type: str = "random_forest"
    # Available: ["random_forest", "gradient_boosting", "catboost", "prophet", "lstm"]
    model_types: List[str] = field(default_factory=lambda: ["random_forest", "catboost"])
    data_source: str = "yfinance"

    # Cost & Tax Profiles
    cost_profile: str = "default"  # "default", "cmc_markets", or "tiger_au"
    annual_income: float = 90000.0  # Annual income for tax bracket calculation
    hurdle_risk_buffer: float = 0.005  # 0.5% extra buffer to account for slippage/volatility


def load_config() -> Config:
    """Loads configuration settings."""
    return Config()
