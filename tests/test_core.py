"""Tests for the AI trading system components."""

import pytest
import pandas as pd
import numpy as np
from config import Config
from buildmodel import ModelBuilder
from backtest import BacktestEngine


@pytest.fixture
def mock_config():
    return Config(
        target_stock_codes=["TEST.AX"],
        backtest_years=1,
        init_capital=10000.0,
        rebuild_model=True,
    )


@pytest.fixture
def mock_data():
    dates = pd.date_range(start="2023-01-01", periods=100)
    data = pd.DataFrame(
        {
            "Open": np.linspace(10, 20, 100),
            "High": np.linspace(11, 21, 100),
            "Low": np.linspace(9, 19, 100),
            "Close": np.linspace(10.5, 20.5, 100),
            "Adj Close": np.linspace(10.5, 20.5, 100),
            "Volume": np.random.randint(1000, 5000, 100),
        },
        index=dates,
    )
    return data


def test_config_load():
    from config import load_config

    config = load_config()
    assert isinstance(config, Config)
    assert "BHP.AX" in config.target_stock_codes


def test_model_builder_prepare_features(mock_config, mock_data):
    builder = ModelBuilder(mock_config)
    X, y = builder.prepare_features(mock_data)
    assert (
        X.shape[1] == 8
    )  # Open, High, Low, Adj Close, Volume, MA5, MA20, Daily_Return
    assert len(X) == len(y)
    assert len(X) < 100  # Due to MA20 window


def test_backtest_engine_init(mock_config):
    builder = ModelBuilder(mock_config)
    engine = BacktestEngine(mock_config, builder)
    assert engine.config == mock_config
    assert engine.model_builder == builder
