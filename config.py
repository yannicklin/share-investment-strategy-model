"""Configuration management for the AI-Based Stock Investment System."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    """System configuration parameters."""

    rebuild_model: bool = True
    target_stock_codes: List[str] = field(default_factory=lambda: ["BHP.AX", "CBA.AX"])
    backtest_years: int = 5
    stop_loss_threshold: float = 0.10
    stop_profit_threshold: float = 0.20
    model_path: str = "models/"
    init_capital: float = 100000.0
    hold_period_unit: str = "month"
    hold_period_value: int = 1
    brokerage_rate: float = 0.0012  # 0.12%
    clearing_rate: float = 0.0000225  # 0.00225%
    settlement_fee: float = 1.5  # $1.5 fixed
    tax_rate: float = 0.25  # 25% tax
    model_type: str = "random_forest"
    model_types: List[str] = field(default_factory=lambda: ["random_forest"])
    data_source: str = "yfinance"


def load_config() -> Config:
    """Loads configuration settings.

    In a real-world scenario, this might read from a JSON or YAML file.
    For now, it returns default values.

    Returns:
        Config: Initialized configuration object.
    """
    return Config()
