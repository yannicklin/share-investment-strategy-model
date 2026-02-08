"""
ASX AI Trading System - Main Application Entry Point

Purpose: Streamlit dashboard for multi-model AI trading strategy analysis
with realistic backtesting and performance metrics.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
import pandas as pd
import os
import logging

# Suppress TensorFlow noise early
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
try:
    import tensorflow as tf

    tf.get_logger().setLevel("ERROR")
    tf.autograph.set_verbosity(0)
except ImportError:
    pass
from core.config import load_config
from core.model_builder import ModelBuilder
from core.backtest_engine import BacktestEngine
from ui.sidebar import render_sidebar
from ui.algo_view import render_algorithm_comparison
from ui.strategy_view import render_strategy_sensitivity
from ui.stars_view import render_super_stars
from ui.components import render_glossary


def main():
    """Main execution flow for the dashboard."""
    try:
        # st.set_page_config must be the very first Streamlit command
        st.set_page_config(
            page_title="Australian Stock AI Strategy Lab", page_icon="🇦🇺", layout="wide"
        )
        render_app()
    except Exception as e:
        st.error(f"⚠️ A critical error occurred: {e}")
        st.exception(e)


def render_app():
    st.title("📈 ASX AI Trading Strategy Dashboard")

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
        with st.spinner(f"Pre-fetching historical data for {len(tickers)} tickers..."):
            builder.prefetch_data_batch(tickers, config.backtest_years)

        prog_placeholder = st.empty()

        for idx, ticker in enumerate(tickers):
            ticker_results = {}
            with prog_placeholder.container():
                st.write(f"### 🔍 Analyzing {ticker} ({idx + 1}/{len(tickers)})")
                st.progress((idx) / len(tickers))

                with st.status(f"Processing {ticker}...", expanded=True) as status:
                    try:
                        st.write("Preparing AI Models...")
                        for m_type in config.model_types:
                            config.model_type = m_type
                            try:
                                if builder.load_or_build(ticker) == "trained":
                                    st.write(f"✅ Trained {m_type}")
                            except Exception as e:
                                st.error(f"Model Error ({m_type}): {e}")
                                ticker_results[f"{m_type}_error"] = str(e)

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
                                config.hold_period_unit, config.hold_period_value = (
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
                                    ticker, config.model_types, tie_breaker=tie_breaker
                                )
                                if "error" in res:
                                    st.error(f"Ranking Error: {res['error']}")
                                # Include company name for Super Stars mode
                                res["company_name"] = builder.get_company_name(ticker)
                                ticker_results = res
                            except Exception as e:
                                st.error(f"Ranking Exception: {e}")
                                ticker_results = {"error": str(e)}
                    except Exception as ticker_e:
                        st.error(f"Critical Ticker Error ({ticker}): {ticker_e}")
                        ticker_results = {"error": str(ticker_e)}

                    status.update(
                        label=f"✅ {ticker} Complete", state="complete", expanded=False
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
            # Check if any model in the results has actual trade data (indicated by roi presence)
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
                    st.session_state.get("active_index", "ASX Index"),
                    results,
                    models=config.model_types,
                    tie_breaker=tie_breaker,
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
            "👈 Use the sidebar to configure your Australian trading strategy and click 'Run Analysis'."
        )

        st.subheader("🇦🇺 Australia Market Notes")
        col1, col2 = st.columns(2)
        with col1:
            st.write(
                "- **T+2 Settlement**: Capital from a sale is locked for 2 trading days."
            )
            st.write(
                "- **ATO Tax**: Capital gains subject to individual income tax (50% discount if held > 12 months)."
            )
        with col2:
            st.write(
                "- **Brokerage**: Default assumes standard online rates (e.g. $6-$11 min)."
            )
            st.write("- **Market Hours**: 10:00 AM - 4:00 PM AEST.")
            st.write("- **Currency**: All figures in AUD (Australian Dollar).")


if __name__ == "__main__":
    main()
