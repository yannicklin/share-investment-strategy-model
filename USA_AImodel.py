"""
USA AI Trading System - Main Application Entry Point

Purpose: Streamlit dashboard for multi-model AI trading strategy analysis
with realistic backtesting and performance metrics for US stocks.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
import pandas as pd
import time
import os
import gc

# 1. Core Logic & Config
from core.config import load_config
from core.model_builder import ModelBuilder
from core.backtest_engine import BacktestEngine
from core.index_manager import load_index_constituents

# 2. UI Components
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
            page_title="USA Stock AI Strategy Lab",
            page_icon="🇺🇸",
            layout="wide",
            initial_sidebar_state="expanded",
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
    sidebar_res = render_sidebar(config)
    if sidebar_res is None:
        st.error("Sidebar failed to render. Please check the logs.")
        return

    mode, test_periods, period_map, run_analysis, tie_breaker, index_choice = (
        sidebar_res
    )

    # Initialize Backend Engines
    builder = ModelBuilder(config)
    engine = BacktestEngine(config, builder)

    # --- 1. ACTION: RUN BACKTEST ANALYSIS ---
    if run_analysis:
        # Clear previous results
        if "results" in st.session_state:
            del st.session_state["results"]

        tickers = config.target_stock_codes
        results = {}

        # Keep builder in session state for cache persistence across UI refreshes
        st.session_state["active_builder"] = builder
        st.session_state["active_mode"] = mode

        prog_placeholder = st.empty()
        with prog_placeholder.container():
            st.write(f"### 🔍 Analyzing {len(tickers)} Stocks...")
            # Batch pre-fetch all ticker data at once
            with st.spinner(
                f"Pre-fetching historical data for {len(tickers)} tickers..."
            ):
                builder.prefetch_data_batch(tickers, config.backtest_years)

            main_bar = st.progress(0)

            for idx, ticker in enumerate(tickers):
                main_bar.progress((idx + 1) / len(tickers))
                st.write(f"Processing **{ticker}** ({idx + 1}/{len(tickers)})...")

                try:
                    ticker_results = {}
                    if mode == "Models Comparison":
                        # Comparison mode: Single period, multiple models independently
                        for m_type in config.model_types:
                            st.write(f"Building {m_type}...")
                            config.model_type = m_type
                            try:
                                if builder.load_or_build(ticker) == "trained":
                                    st.write(f"✅ Trained {m_type}")
                            except Exception as e:
                                st.error(f"Model Error ({m_type}): {e}")
                                ticker_results[f"{m_type}_error"] = str(e)
                                continue

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
                        # Strategy sensitivity mode: Multiple periods, one consensus committee
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

                    elif mode == "Find Super Stars":
                        # Index scanning mode: One period, one consensus committee
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
                            res["company"] = builder.get_company_name(ticker)
                            ticker_results = res
                        except Exception as e:
                            st.error(f"Ranking Exception: {e}")
                            ticker_results = {"error": str(e)}

                    results[ticker] = ticker_results
                except Exception as ticker_e:
                    st.error(f"Critical Ticker Error ({ticker}): {ticker_e}")
                    results[ticker] = {"error": str(ticker_e)}

            st.success("✅ Analysis Complete!")
            time.sleep(1)

            # Force memory cleanup
            gc.collect()

        st.session_state["results"] = results
        st.session_state["active_index"] = (
            index_choice if mode == "Find Super Stars" else "Custom List"
        )
        prog_placeholder.empty()

    # --- 2. RENDERING: DASHBOARD VIEWS ---
    results = st.session_state.get("results")
    if results:
        # Use existing builder to leverage cache, or a dummy if none active
        active_builder = st.session_state.get("active_builder")

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
        elif (
            not valid_tickers
            and st.session_state.get("active_mode") != "Find Super Stars"
        ):
            st.error("❌ Analysis failed to generate any valid trade results.")
            with st.expander("🔍 View Technical Error Report", expanded=True):
                if active_builder:
                    st.subheader("📊 Data Consistency Check")
                    for ticker in results.keys():
                        data = active_builder.fetch_data(ticker, config.backtest_years)
                        if data.empty:
                            st.error(f"- {ticker}: No data available.")
                        else:
                            st.success(f"- {ticker}: {len(data)} rows cached.")

        render_glossary()
        active_mode = st.session_state["active_mode"]

        if active_mode == "Find Super Stars":
            render_super_stars(
                st.session_state.get("active_index", "USA Index"),
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
            "👈 Use the sidebar to configure your USA trading strategy and click 'Run Analysis'."
        )

        st.subheader("🇺🇸 USA Market Notes")
        col1, col2 = st.columns(2)
        with col1:
            st.write("- **T+1 Settlement**: Capital available next business day.")
            st.info(
                "- **Tax (W-8BEN)**: 15% Dividend Withholding, $0 Capital Gains (Treaty)."
            )
            st.write("- **Market Regime**: AI uses **^VIX** & **^TNX** as signals.")
        with col2:
            st.info(
                "- **Brokerage**: Default assumes standard USD rates (e.g. $3 min for Stake, $1 min for IBKR Pro Fixed)."
            )
            st.write("- **Market Hours**: 9:30 AM - 4:00 PM ET.")
            st.write("- **Currency**: All figures in USD.")


if __name__ == "__main__":
    main()
