"""
Taiwan Stock AI Trading System - Main Application Entry Point

Purpose: Streamlit dashboard for multi-model AI trading strategy analysis
with realistic backtesting and performance metrics for Taiwan market.

Author: Yannick
Copyright (c) 2026 Yannick
"""

# 1. Core Network/Data Libraries (MUST be before TensorFlow)
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy

try:
    from curl_cffi import requests as cf_requests
except ImportError:
    pass

import logging
import os

import pandas as pd
import streamlit as st

# Set logging level to WARNING to reduce terminal noise
logging.basicConfig(level=logging.WARNING)

# 2. Suppress TensorFlow noise and load
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
try:
    import tensorflow as tf

    # TensorFlow 2.x logging suppression (modern API)
    tf.get_logger().setLevel("ERROR")
    # Suppress autograph retracing warnings
    tf.autograph.set_verbosity(0)
except (ImportError, AttributeError):
    pass
from core.backtest_engine import BacktestEngine
from core.config import Config, load_config
from core.model_builder import ModelBuilder
from ui.algo_view import render_algorithm_comparison
from ui.components import render_glossary
from ui.sidebar import render_sidebar
from ui.stars_view import render_super_stars
from ui.strategy_view import render_strategy_sensitivity


def main():
    """Main execution flow for the dashboard."""
    try:
        # st.set_page_config must be the very first Streamlit command
        st.set_page_config(
            page_title="Taiwan Stock AI Strategy Lab", page_icon="🇹🇼", layout="wide"
        )
        render_app()
    except Exception as e:
        st.error(f"⚠️ A critical error occurred: {e}")
        st.exception(e)


def categorize_error(error_msg: str) -> str:
    """Categorize error messages into simple issue types."""
    error_lower = error_msg.lower()

    if (
        "no data" in error_lower
        or "empty" in error_lower
        or "insufficient data" in error_lower
    ):
        return "📊 Data Missing"
    elif "rate limit" in error_lower or "too many requests" in error_lower:
        return "⏱️ Rate Limited"
    elif "division by zero" in error_lower or "divide" in error_lower:
        return "🔢 Math Error"
    elif (
        "import" in error_lower
        or "module" in error_lower
        or "not installed" in error_lower
    ):
        return "📦 Library Missing"
    elif "feature mismatch" in error_lower or "dimension" in error_lower:
        return "⚙️ Config Changed"
    elif "memory" in error_lower or "cuda" in error_lower:
        return "💾 Resource Issue"
    elif "timeout" in error_lower or "connection" in error_lower:
        return "🌐 Network Error"
    else:
        return "⚠️ Technical Error"


def _run_super_star_worker(
    ticker: str,
    config: Config,
    data_cache: dict,
    market_data: pd.DataFrame | None,
    models: list[str],
    tie_breaker: str | None,
) -> tuple[str, dict]:
    """Run one Super Stars ticker analysis in an isolated worker state."""
    worker_config = deepcopy(config)
    worker_config.target_stock_codes = [ticker]
    worker_config.model_types = list(models)

    worker_builder = ModelBuilder(worker_config)
    worker_builder.set_data_cache_snapshot(data_cache)
    worker_builder.set_cached_market_data(market_data)

    worker_engine = BacktestEngine(worker_config, worker_builder)
    result = worker_engine.run_strategy_mode(
        ticker,
        worker_config.model_types,
        tie_breaker=tie_breaker,
        mode_prefix="ranking",
    )
    return ticker, result


def render_app():
    st.title("📈 Taiwan Stock AI Trading Strategy Dashboard")

    # Load shared configuration
    config = load_config()

    # Render Sidebar and get parameters
    sidebar_res = render_sidebar(config)
    if sidebar_res is None:
        st.error("Sidebar failed to render. Please check the logs.")
        return

    mode, test_periods, period_map, run_analysis, tie_breaker, index_choice = (
        sidebar_res
    )

    # --- 1. ACTION: RUN BACKTEST ANALYSIS ---
    if run_analysis:
        # Clear previous results
        if "results" in st.session_state:
            del st.session_state["results"]

        all_results = {}
        # Keep builder in session state for cache persistence across UI refreshes
        st.session_state["active_builder"] = ModelBuilder(config)
        builder = st.session_state["active_builder"]
        engine = BacktestEngine(config, builder)

        tickers = config.target_stock_codes

        # Batch pre-fetch all ticker data at once
        with st.spinner(
            f"Pre-fetching historical data for {len(tickers)} Taiwan stocks..."
        ):
            builder.prefetch_data_batch(tickers, config.backtest_years)
            builder.ensure_market_data()

        # Simple failure tracking for Super Stars mode
        ticker_failures = {}  # {ticker: {"issue": "...", "models": [...]}}

        prog_placeholder = st.empty()

        if mode == "Find Super Stars" and len(tickers) > 1:
            shared_data_cache = builder.get_data_cache_snapshot()
            shared_market_data = builder._market_data
            max_workers = min(config.super_stars_workers, len(tickers))
            completed = 0

            st.info(
                f"🚀 Running {max_workers} parallel workers for Super Stars analysis..."
            )
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                future_map = {
                    executor.submit(
                        _run_super_star_worker,
                        ticker,
                        config,
                        shared_data_cache,
                        shared_market_data,
                        list(config.model_types),
                        tie_breaker,
                    ): ticker
                    for ticker in tickers
                }

                for future in as_completed(future_map):
                    ticker = future_map[future]
                    completed += 1
                    try:
                        ticker_name, ticker_results = future.result()
                    except Exception as e:
                        ticker_name = ticker
                        ticker_results = {"error": str(e)}

                    all_results[ticker_name] = ticker_results

                    if isinstance(ticker_results, dict) and "error" in ticker_results:
                        ticker_failures[ticker_name] = [
                            {
                                "issue": categorize_error(ticker_results["error"]),
                                "details": ticker_results["error"],
                                "models": list(config.model_types),
                            }
                        ]

                    with prog_placeholder.container():
                        st.write(
                            f"### 🔍 Analyzing Super Stars ({completed}/{len(tickers)})"
                        )
                        st.progress(completed / len(tickers))
        else:
            for idx, ticker in enumerate(tickers):
                ticker_results = {}
                with prog_placeholder.container():
                    st.write(f"### 🔍 Analyzing {ticker} ({idx + 1}/{len(tickers)})")
                    st.progress((idx) / len(tickers))

                    with st.status(
                        f"Processing {ticker}...",
                        expanded=(mode != "Find Super Stars"),
                    ) as status:
                        try:
                            st.write("Preparing AI Models...")
                            for m_type in config.model_types:
                                config.model_type = m_type
                                try:
                                    result = builder.load_or_build(ticker)
                                    status_emoji = (
                                        "🆕" if "train" in result else "💾"
                                    )  # New trained vs Cached
                                    st.write(
                                        f"{status_emoji} **{m_type.upper()}**: {result.replace('_', ' ').title()}"
                                    )
                                except Exception as e:
                                    error_msg = str(e)
                                    st.error(f"❌ Model Error ({m_type}): {error_msg}")
                                    ticker_results[f"{m_type}_error"] = error_msg

                                    # Track failure for Super Stars summary
                                    if mode == "Find Super Stars":
                                        if ticker not in ticker_failures:
                                            ticker_failures[ticker] = []

                                        # Check if this error type already exists for this ticker
                                        issue_type = categorize_error(error_msg)
                                        existing = next(
                                            (
                                                item
                                                for item in ticker_failures[ticker]
                                                if item["issue"] == issue_type
                                            ),
                                            None,
                                        )

                                        if existing:
                                            # Same error type, just add model to list
                                            existing["models"].append(m_type)
                                        else:
                                            # New error type for this ticker
                                            ticker_failures[ticker].append(
                                                {
                                                    "issue": issue_type,
                                                    "details": error_msg,
                                                    "models": [m_type],
                                                }
                                            )

                            if mode == "Models Comparison":
                                for m_type in config.model_types:
                                    st.write(f"Backtesting {m_type}...")
                                    try:
                                        res = engine.run_model_mode(ticker, m_type)
                                        if "error" in res:
                                            st.error(
                                                f"Backtest Error ({m_type}): {res['error']}"
                                            )
                                        ticker_results[m_type] = res
                                    except Exception as e:
                                        st.error(f"Backtest Exception ({m_type}): {e}")
                                        ticker_results[m_type] = {"error": str(e)}
                            elif mode == "Time-Span Comparison":
                                for p_name in test_periods:
                                    st.write(f"Evaluating {p_name} strategy...")
                                    unit, val = period_map[p_name]
                                    (
                                        config.hold_period_unit,
                                        config.hold_period_value,
                                    ) = (
                                        unit,
                                        val,
                                    )
                                    try:
                                        res = engine.run_strategy_mode(
                                            ticker,
                                            config.model_types,
                                            tie_breaker=tie_breaker,
                                        )
                                        if "error" in res:
                                            st.error(
                                                f"Strategy Error ({p_name}): {res['error']}"
                                            )
                                        ticker_results[p_name] = res
                                    except Exception as e:
                                        st.error(f"Strategy Exception ({p_name}): {e}")
                                        ticker_results[p_name] = {"error": str(e)}
                            else:
                                st.write("Ranking stock...")
                                p_name = test_periods[0]
                                unit, val = period_map[p_name]
                                config.hold_period_unit, config.hold_period_value = (
                                    unit,
                                    val,
                                )
                                try:
                                    res = engine.run_strategy_mode(
                                        ticker,
                                        config.model_types,
                                        tie_breaker=tie_breaker,
                                        mode_prefix="ranking",
                                    )
                                    if "error" in res:
                                        st.error(f"Ranking Error: {res['error']}")
                                    # Include metadata for Super Stars UI
                                    res["company_name"] = builder.get_company_name(
                                        ticker
                                    )
                                    res["chinese_name"] = builder.get_chinese_name(
                                        ticker
                                    )
                                    ticker_results = res
                                except Exception as e:
                                    st.error(f"Ranking Exception: {e}")
                                    ticker_results = {"error": str(e)}

                            # Add metadata to ticker_results for all modes
                            if (
                                isinstance(ticker_results, dict)
                                and "error" not in ticker_results
                            ):
                                ticker_results["_metadata"] = {
                                    "chinese_name": builder.get_chinese_name(ticker),
                                    "company_name": builder.get_company_name(ticker),
                                }

                        except Exception as ticker_e:
                            st.error(f"Critical Ticker Error ({ticker}): {ticker_e}")
                            ticker_results = {"error": str(ticker_e)}

                        status.update(
                            label=f"✅ {ticker} Complete",
                            state="complete",
                            expanded=False,
                        )

                all_results[ticker] = ticker_results

                # Force memory cleanup
                import gc

                gc.collect()
                try:
                    import tensorflow as tf

                    tf.keras.backend.clear_session()
                except ImportError:
                    pass

        # Show simple failure report for Super Stars mode
        if mode == "Find Super Stars" and ticker_failures:
            total_issues = sum(len(errors) for errors in ticker_failures.values())
            st.warning(
                f"⚠️ {len(ticker_failures)} tickers had issues ({total_issues} unique error types)"
            )

            with st.expander("📋 Problem Tickers Report", expanded=True):
                # Create clean table (one row per ticker+error type combination)
                report_data = []
                for ticker, error_list in ticker_failures.items():
                    for error_info in error_list:
                        report_data.append(
                            {
                                "Ticker": ticker,
                                "Issue Type": error_info["issue"],
                                "Failed Models": ", ".join(
                                    [m.upper() for m in error_info["models"]]
                                ),
                                "Details": error_info["details"][:100] + "..."
                                if len(error_info["details"]) > 100
                                else error_info["details"],
                            }
                        )

                df = pd.DataFrame(report_data)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                        "Issue Type": st.column_config.TextColumn(
                            "Issue Type", width="medium"
                        ),
                        "Failed Models": st.column_config.TextColumn(
                            "Failed Models", width="medium"
                        ),
                        "Details": st.column_config.TextColumn(
                            "Error Details", width="large"
                        ),
                    },
                )

        st.session_state["results"] = all_results
        st.session_state["active_mode"] = mode
        st.session_state["active_index"] = (
            index_choice if mode == "Find Super Stars" else "Custom List"
        )
        prog_placeholder.empty()
        st.session_state["trigger_rerun"] = True

    if st.session_state.get("trigger_rerun"):
        st.session_state["trigger_rerun"] = False
        st.rerun()

    # --- 3. RENDERING: DASHBOARD VIEWS ---
    if "results" in st.session_state:
        results = st.session_state["results"]
        # Use existing builder to leverage cache, or a dummy if none active
        builder = st.session_state.get("active_builder")

        # Validation logic: identify tickers with valid non-error results
        valid_tickers = []
        for ticker, r in results.items():
            if not isinstance(r, dict):
                continue
            is_valid = False
            if any(isinstance(m_res, dict) and "roi" in m_res for m_res in r.values()):
                is_valid = True
            elif "roi" in r:
                is_valid = True

            if is_valid:
                valid_tickers.append(ticker)

        if not results:
            st.warning("Analysis completed but no tickers were processed.")
        elif not valid_tickers:
            st.error("❌ Analysis failed to generate any valid trade results.")
            with st.expander("🔍 View Technical Error Report", expanded=True):
                if builder:
                    st.subheader("📊 Data Consistency Check")
                    for ticker in results.keys():
                        # Try to get from cache first to avoid slow network calls
                        data = builder.fetch_data(ticker, config.backtest_years)
                        if data.empty:
                            st.error(f"- {ticker}: No data available.")
                        else:
                            st.success(f"- {ticker}: {len(data)} rows cached.")
                            st.write(f"  - Columns: {list(data.columns)}")

                st.subheader("📝 Execution Logs")
                for ticker, res in results.items():
                    st.markdown(f"**{ticker}:**")
                    if isinstance(res, dict):
                        found_err = False
                        for key, val in res.items():
                            if isinstance(val, dict) and "error" in val:
                                st.error(f"- {key}: {val['error']}")
                                found_err = True
                            elif key == "error":
                                st.error(f"- Global: {val}")
                                found_err = True
                        if not found_err:
                            st.write(
                                "- No trades were triggered by the AI models (Hurdle rate too high?)."
                            )
                    else:
                        st.write(f"- Unexpected result type: {type(res)}")
        else:
            render_glossary()
            active_mode = st.session_state["active_mode"]
            if active_mode == "Find Super Stars":
                render_super_stars(
                    st.session_state.get("active_index", "Taiwan Index"),
                    results,
                    models=config.model_types,
                    tie_breaker=tie_breaker,
                    builder=builder,
                )
            else:
                for ticker in valid_tickers:
                    ticker_res = results[ticker]
                    if active_mode == "Models Comparison":
                        render_algorithm_comparison(ticker, ticker_res)
                    else:
                        render_strategy_sensitivity(
                            ticker,
                            ticker_res,
                            models=config.model_types,
                            tie_breaker=tie_breaker,
                        )
                    st.markdown("---")
    else:
        st.info(
            "👈 Use the sidebar to configure your Taiwan trading strategy and click 'Run Analysis'."
        )

        st.subheader("🇹🇼 Taiwan Market Notes")
        st.info(
            "ℹ️ **FinMind Essential**: Yahoo Finance provides *Price* data, but only FinMind provides **Chips (Foreign/Trust/Margin)** & **Monthly Revenue**.\n"
            "This unique alpha is why Taiwan models require specialized data sources."
        )
        col1, col2 = st.columns(2)
        with col1:
            st.write("- **T+2 Settlement**: Strict cash clearing enforcement.")
            st.write(
                "- **0% Capital Gains Tax**: Currently tax-free for domestic stocks."
            )
            st.write(
                "- **DataSource (FinMind)**: Enhanced with Foreign/Trust, Margin, & Revenue features."
            )
        with col2:
            st.write("- **High Friction (STT)**: 0.3% tax on every sell order.")
            st.write("- **Circuit Breakers**: Daily price limit of ±10%.")
            st.write(
                "- **Global Correlation**: Includes NASDAQ/SOX/USD impacts via Yahoo Finance."
            )


if __name__ == "__main__":
    main()
