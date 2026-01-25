"""Configuration management for the AI-Based Stock Investment System."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    """System configuration parameters."""

    rebuild_model: bool = True
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
    stop_loss_threshold: float = 0.10
    stop_profit_threshold: float = 0.20
    model_path: str = "models/"
    init_capital: float = 3000.0
    hold_period_unit: str = "month"
    hold_period_value: int = 1
    brokerage_rate: float = 0.0012  # 0.12%
    clearing_rate: float = 0.0000225  # 0.00225%
    settlement_fee: float = 1.5  # $1.5 fixed
    tax_rate: float = 0.25  # 25% tax
    scaler_type: str = "standard"  # "standard" or "robust"
    model_type: str = "random_forest"
    # Available: ["random_forest", "xgboost", "catboost", "prophet", "lstm"]
    model_types: List[str] = field(
        default_factory=lambda: ["random_forest", "catboost"]
    )
    data_source: str = "yfinance"

    # Cost & Tax Profiles
    cost_profile: str = "default"  # "default" or "cmc_markets"
    annual_income: float = 90000.0  # Annual income for tax bracket calculation


def load_config() -> Config:
    """Loads configuration settings.

    In a real-world scenario, this might read from a JSON or YAML file.
    For now, it returns default values.

    Returns:
        Config: Initialized configuration object.
    """
    return Config()
