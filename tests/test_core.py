"""Tests for the AI trading system components."""

import pytest
import pandas as pd
import numpy as np
from config import Config
from buildmodel import ModelBuilder, XGB_AVAILABLE
from backtest import BacktestEngine


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
    # Need more data points for MACD (26) and RSI (14)
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
    from config import load_config

    config = load_config()
    assert isinstance(config, Config)
    assert "BHP.AX" in config.target_stock_codes
    assert config.hold_period_unit == "month"


def test_model_builder_prepare_features(mock_config, mock_data):
    builder = ModelBuilder(mock_config)
    X, y = builder.prepare_features(mock_data)
    # Features: Open, High, Low, Close, Volume, MA5, MA20, RSI, MACD, Signal_Line, Daily_Return
    assert X.shape[1] == 11

    assert len(X) == len(y)
    assert len(X) < 150


def test_backtest_engine_run_logic(mock_config, mock_data):
    # Mocking fetch_data to return our mock_data instead of calling yfinance
    builder = ModelBuilder(mock_config)
    builder.fetch_data = lambda ticker, years: mock_data

    # Train model on mock data
    builder.train("TEST.AX")

    engine = BacktestEngine(mock_config, builder)
    results = engine.run("TEST.AX")

    assert "roi" in results
    assert "win_rate" in results
    assert "trades" in results
