"""
ASX AI Trading System - Unit Tests

Purpose: Test suite for core module validation including model builder
and backtesting engine.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pytest
import pandas as pd
import numpy as np
from core.config import Config
from core.model_builder import ModelBuilder, XGB_AVAILABLE
from core.backtest_engine import BacktestEngine


@pytest.fixture
def mock_config():
    model_types = ["random_forest"]
    if XGB_AVAILABLE:
        model_types.append("xgboost")

    return Config(
        target_stock_codes=["TEST.AX"],
        backtest_years=1,
        init_capital=10000.0,
        rebuild_model=True,
        hold_period_unit="month",
        hold_period_value=1,
        model_types=model_types,
    )


@pytest.fixture
def mock_data():
    dates = pd.date_range(start="2023-01-01", periods=150)
    data = pd.DataFrame(
        {
            "Open": np.linspace(10, 20, 150),
            "High": np.linspace(11, 21, 150),
            "Low": np.linspace(9, 19, 150),
            "Close": np.linspace(10.5, 20.5, 150),
            "Volume": np.random.randint(1000, 5000, 150),
        },
        index=dates,
    )
    return data


def test_config_load():
    from core.config import load_config

    config = load_config()
    assert isinstance(config, Config)
    assert config.hold_period_unit == "month"


def test_model_builder_prepare_features(mock_config, mock_data):
    builder = ModelBuilder(mock_config)
    X, y = builder.prepare_features(mock_data)
    assert X.shape[1] == 11
    assert len(X) == len(y)


def test_backtest_engine_run_logic(mock_config, mock_data):
    builder = ModelBuilder(mock_config)
    builder.fetch_data = lambda ticker, years: mock_data
    builder.train("TEST.AX")

    engine = BacktestEngine(mock_config, builder)
    # Using run_model_mode for Mode 1 testing
    results = engine.run_model_mode("TEST.AX", "random_forest")

    assert "roi" in results
    assert "trades" in results
    assert "final_capital" in results
