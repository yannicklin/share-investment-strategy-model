"""
Super Stars worker function — lives in core/ so that ProcessPoolExecutor worker
processes only import lightweight ML/data dependencies, NOT streamlit.

Why this matters: ProcessPoolExecutor (spawn method on macOS) re-imports the
module that contains the worker function in each child process. If the function
lived in USA_AImodel.py / TWN_AImodel.py / ASX_AImodel.py, every worker would
import streamlit, which registers an atexit handler that prints "Stopping..." when
the worker process exits. Moving the function here eliminates that noise entirely.
"""

import logging
from copy import deepcopy

import pandas as pd

from core.backtest_engine import BacktestEngine
from core.config import Config
from core.model_builder import ModelBuilder

# Configure logging for worker processes
_worker_logger = logging.getLogger(__name__)


def run_super_star_worker(
    ticker: str,
    config: Config,
    data_cache: dict,
    market_data: pd.DataFrame | None,
    models: list[str],
    tie_breaker: str | None,
) -> tuple[str, dict]:
    """Run one Super Stars ticker analysis in an isolated worker process.

    The function is intentionally kept in core/ (no streamlit import) so that
    worker processes started by ProcessPoolExecutor never register Streamlit's
    atexit handler, which would print "Stopping..." on process exit.
    """
    try:
        _worker_logger.info(f"[WORKER] Starting analysis for {ticker}")
        
        worker_config = deepcopy(config)
        worker_config.target_stock_codes = [ticker]
        worker_config.model_types = list(models)

        worker_builder = ModelBuilder(worker_config)
        worker_builder.set_data_cache_snapshot(data_cache)
        worker_builder.set_cached_market_data(market_data)

        _worker_logger.info(f"[WORKER] Running backtest for {ticker}")
        worker_engine = BacktestEngine(worker_config, worker_builder)
        result = worker_engine.run_strategy_mode(
            ticker,
            worker_config.model_types,
            tie_breaker=tie_breaker,
            mode_prefix="ranking",
        )
        _worker_logger.info(f"[WORKER] Completed {ticker}, result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")

        # ── Cleanup ───────────────────────────────────────────────────────────────
        # Runs AFTER result is fully computed and stored in the local variable above.
        # result is a plain Python dict of numbers/strings — completely decoupled
        # from worker_builder and worker_engine at this point.
        # Deleting the ML objects here reduces atexit work so the process exits fast.
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

        _worker_logger.info(f"[WORKER] Finished cleanup for {ticker}")
        return ticker, result
    
    except Exception as e:
        _worker_logger.error(f"[WORKER] Error processing {ticker}: {e}", exc_info=True)
        return ticker, {"error": str(e)}
            pass

    if "prophet" in models:
        try:
            import gc

            gc.collect()  # releases cmdstanpy CmdStanModel objects and temp file refs
        except Exception:
            pass
    # ─────────────────────────────────────────────────────────────────────────

    return ticker, result
