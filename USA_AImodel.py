"""
USA AI Trading System - Main Application Entry Point

Purpose: Streamlit dashboard for multi-model AI trading strategy analysis
with realistic backtesting and performance metrics.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
import pandas as pd
import os
import logging
import gc

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
from ui.strategy_view import render_strategy_view
from ui.stars_view import render_super_stars
from ui.components import render_glossary


def main():
    """Main execution flow for the dashboard."""
    try:
        st.set_page_config(
            page_title="USA Stock AI Strategy Lab", page_icon="🇺🇸", layout="wide"
        )
        render_app()
    except Exception as e:
        st.error(f"⚠️ A critical error occurred: {e}")
        st.exception(e)


def render_app():
    st.title("📈 USA AI Trading Strategy Dashboard")

    # Load shared configuration
    config = load_config()

    # Render Sidebar and get parameters
    sidebar_params = render_sidebar(config)
    if sidebar_params is None:
        st.error("Sidebar failed to render.")
        return

    mode = sidebar_params["mode"]
    run_analysis = sidebar_params["run_analysis"]
    tie_breaker = sidebar_params["tie_breaker"]
    index_choice = sidebar_params["index_choice"]

    # --- 1. ACTION: RUN BACKTEST ANALYSIS ---
    if run_analysis:
        if "results" in st.session_state:
            del st.session_state["results"]

        all_results = {}
        st.session_state["active_builder"] = ModelBuilder(config)
        builder = st.session_state["active_builder"]
        engine = BacktestEngine(config, builder)

        tickers = config.target_stock_codes

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
                            builder.load_or_build(ticker)

                        if mode == "Models Comparison":
                            for m_type in config.model_types:
                                ticker_results[m_type] = engine.run_model_mode(
                                    ticker, m_type
                                )

                        elif mode == "Time-Span Comparison":
                            # In USA branch, this is Consensus Mode
                            ticker_results = engine.run_strategy_mode(
                                ticker, config.model_types, tie_breaker=tie_breaker
                            )

                        else:
                            # Super Stars Mode
                            res = engine.run_strategy_mode(
                                ticker, config.model_types, tie_breaker=tie_breaker
                            )
                            if "error" not in res:
                                res["company_name"] = builder.get_company_name(ticker)
                            ticker_results = res

                    except Exception as e:
                        st.error(f"Error analyzing {ticker}: {e}")
                        ticker_results = {"error": str(e)}

                    status.update(
                        label=f"✅ {ticker} Complete", state="complete", expanded=False
                    )

                all_results[ticker] = ticker_results

                # Memory cleanup
                gc.collect()
                try:
                    import tensorflow as tf

                    tf.keras.backend.clear_session()
                except ImportError:
                    pass

        st.session_state["results"] = all_results
        st.session_state["active_mode"] = mode
        st.session_state["active_index"] = index_choice
        prog_placeholder.empty()
        st.session_state["trigger_rerun"] = True

    if st.session_state.get("trigger_rerun"):
        st.session_state["trigger_rerun"] = False
        st.rerun()

    # --- 2. RENDERING ---
    if "results" in st.session_state:
        results = st.session_state["results"]
        render_glossary()
        active_mode = st.session_state["active_mode"]

        if active_mode == "Find Super Stars":
            render_super_stars(
                st.session_state.get("active_index", "USA Index"), results
            )
        elif active_mode == "Time-Span Comparison":
            # This is Consensus Strategy View in USA
            for ticker, ticker_res in results.items():
                render_strategy_view(ticker, ticker_res)
                st.markdown("---")
        else:
            # Models Comparison
            for ticker, ticker_res in results.items():
                render_algorithm_comparison(ticker, ticker_res)
                st.markdown("---")
    else:
        st.info(
            "👈 Use the sidebar to configure your USA trading strategy and click 'Run Analysis'."
        )
        st.subheader("🇺🇸 USA Market Notes")
        col1, col2 = st.columns(2)
        with col1:
            st.write("- **T+1 Settlement**: Capital available next business day.")
            st.write(
                "- **Tax (W-8BEN)**: 15% Dividend Withholding, $0 Capital Gains (Treaty)."
            )
            st.write("- **Market Regime**: AI uses **^VIX** & **^TNX** as signals.")
        with col2:
            st.write(
                "- **Brokerage**: Low cost ($1-$3) but high FX friction (~70bps) for AU investors."
            )
            st.write("- **Market Hours**: 9:30 AM - 4:00 PM ET.")
            st.write("- **Currency**: All figures in USD.")


if __name__ == "__main__":
    main()
