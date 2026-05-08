"""
Taiwan Stock AI Trading System - Super Stars Worker

Purpose: Run one Super Stars analysis in a lightweight worker module that
avoids importing Streamlit and can reuse main-process cache snapshots.

Author: Yannick
Copyright (c) 2026 Yannick
"""

from copy import deepcopy
from typing import Optional

import pandas as pd

from core.backtest_engine import BacktestEngine
from core.config import Config
from core.model_builder import ModelBuilder


def run_super_star_worker(
    ticker: str,
    config: Config,
    data_cache: dict,
    finmind_cache: Optional[dict],
    market_data: pd.DataFrame | None,
    models: list[str],
    tie_breaker: str | None,
) -> tuple[str, dict]:
    """Run one Super Stars ticker analysis in an isolated worker process."""
    worker_config = deepcopy(config)
    worker_config.target_stock_codes = [ticker]
    worker_config.model_types = list(models)

    worker_builder = ModelBuilder(worker_config)
    worker_builder.set_data_cache_snapshot(data_cache)
    if finmind_cache is not None:
        worker_builder.set_finmind_cache_snapshot(finmind_cache)
    worker_builder.set_cached_market_data(market_data)

    worker_engine = BacktestEngine(worker_config, worker_builder)
    result = worker_engine.run_strategy_mode(
        ticker,
        worker_config.model_types,
        tie_breaker=tie_breaker,
        mode_prefix="ranking",
    )

    worker_builder.model = None
    del worker_engine
    del worker_builder

    if "lstm" in models:
        try:
            import tensorflow as tf

            tf.keras.backend.clear_session()
        except Exception:
            pass

    if "prophet" in models:
        try:
            import gc

            gc.collect()
        except Exception:
            pass

    return ticker, result