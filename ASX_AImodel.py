"""
ASX AI Trading System - Main Application Entry Point

Purpose: Streamlit dashboard for multi-model AI trading strategy analysis
with realistic backtesting and performance metrics.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
import pandas as pd
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
        st.set_page_config(page_title="ASX AI Trading System", layout="wide")
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

    mode, test_periods, period_map, gen_suggestions, tie_breaker, index_choice = (
        sidebar_res
    )

    # --- 1. ACTION: LIVE SUGGESTIONS ---
    if gen_suggestions:
        # Clear previous results to avoid UI clutter
        if "results" in st.session_state:
            del st.session_state["results"]

        suggestions_list = []
        builder = ModelBuilder(config)

        # Limit live scan to first 10 for performance if in index mode
        tickers_to_scan = (
            config.target_stock_codes[:10]
            if mode == "Find Super Stars"
            else config.target_stock_codes
        )

        with st.spinner("Pre-fetching market data for suggestions..."):
            builder.prefetch_data_batch(tickers_to_scan, 1)

        prog_placeholder = st.empty()
        progress_bar = prog_placeholder.progress(0)

        for i, ticker in enumerate(tickers_to_scan):
            with st.spinner(f"Analyzing {ticker} for today..."):
                # Fetch data once for all models of this ticker
                data_1y = builder.fetch_data(ticker, 1)
                if data_1y.empty:
                    continue
                X, y = builder.prepare_features(data_1y)
                if len(X) < builder.sequence_length:
                    continue
                latest_features = X[-builder.sequence_length :]

                votes, total_return, tie_breaker_bullish = 0, 0.0, False
                tb_model = tie_breaker if tie_breaker else config.model_types[0]
                current_price = float(latest_features[-1, 3])

                for m_type in config.model_types:
                    config.model_type = m_type
                    builder.load_or_build(ticker)
                    pred = builder.predict(latest_features, date=pd.Timestamp.now())
                    is_m_bullish = pred > current_price
                    if is_m_bullish:
                        votes += 1
                    if m_type == tb_model:
                        tie_breaker_bullish = is_m_bullish
                    total_return += (pred - current_price) / current_price

                avg_return = total_return / len(config.model_types)
                is_bullish = votes > (len(config.model_types) / 2) or (
                    votes == len(config.model_types) / 2 and tie_breaker_bullish
                )

                suggestions_list.append(
                    {
                        "Ticker": ticker,
                        "Price": current_price,
                        "Expected Return": avg_return,
                        "Consensus": f"{votes}/{len(config.model_types)} Models",
                        "Signal": "🟢 BUY" if is_bullish else "🟡 WAIT/HOLD",
                    }
                )
            progress_bar.progress((i + 1) / len(tickers_to_scan))

        st.session_state["suggestions"] = suggestions_list
        prog_placeholder.empty()
        # Use a state-based trigger instead of immediate rerun to avoid recursion loops
        st.session_state["trigger_rerun"] = True

    # --- 2. ACTION: RUN BACKTEST ANALYSIS ---
    if st.sidebar.button("🚀 Run Analysis"):
        # Clear previous suggestions
        if "suggestions" in st.session_state:
            del st.session_state["suggestions"]
        if "results" in st.session_state:
            del st.session_state["results"]

        all_results = {}
        builder = ModelBuilder(config)
        engine = BacktestEngine(config, builder)

        tickers = config.target_stock_codes

        # Batch pre-fetch all ticker data at once (5 years) to avoid loop overhead
        with st.spinner(f"Pre-fetching historical data for {len(tickers)} tickers..."):
            builder.prefetch_data_batch(tickers, config.backtest_years)

        prog_placeholder = st.empty()

        for idx, ticker in enumerate(tickers):
            ticker_results = {}
            with prog_placeholder.container():
                st.write(f"### 🔍 Analyzing {ticker} ({idx + 1}/{len(tickers)})")
                progress_bar = st.progress((idx) / len(tickers))

                with st.spinner(f"Preparing AI Models for {ticker}..."):
                    original_rebuild = config.rebuild_model
                    for m_type in config.model_types:
                        config.model_type = m_type
                        try:
                            builder.load_or_build(ticker)
                        except Exception as e:
                            st.warning(
                                f"Could not load/build {m_type} for {ticker}: {e}"
                            )
                    config.rebuild_model = False

                if mode == "Models Comparison":
                    for m_type in config.model_types:
                        with st.spinner(f"Backtesting {m_type}..."):
                            try:
                                ticker_results[m_type] = engine.run_model_mode(
                                    ticker, m_type
                                )
                            except Exception as e:
                                ticker_results[m_type] = {"error": str(e)}
                elif mode == "Time-Span Comparison":
                    for p_name in test_periods:
                        with st.spinner(f"Evaluating {p_name} strategy..."):
                            unit, val = period_map[p_name]
                            config.hold_period_unit, config.hold_period_value = (
                                unit,
                                val,
                            )
                            try:
                                ticker_results[p_name] = engine.run_strategy_mode(
                                    ticker, config.model_types, tie_breaker=tie_breaker
                                )
                            except Exception as e:
                                ticker_results[p_name] = {"error": str(e)}
                else:
                    # Find Super Stars (Mode 3)
                    with st.spinner(f"Ranking {ticker}..."):
                        p_name = test_periods[0]
                        unit, val = period_map[p_name]
                        config.hold_period_unit, config.hold_period_value = unit, val
                        try:
                            ticker_results = engine.run_strategy_mode(
                                ticker, config.model_types, tie_breaker=tie_breaker
                            )
                        except Exception as e:
                            ticker_results = {"error": str(e)}

                all_results[ticker] = ticker_results
                config.rebuild_model = original_rebuild

                # Force Python to release memory after each ticker
                import gc

                gc.collect()

        st.session_state["results"] = all_results
        st.session_state["active_mode"] = mode
        st.session_state["active_index"] = (
            index_choice if mode == "Find Super Stars" else "Custom List"
        )
        prog_placeholder.empty()
        st.session_state["trigger_rerun"] = True

    # Check for rerun trigger
    if st.session_state.get("trigger_rerun"):
        st.session_state["trigger_rerun"] = False
        st.rerun()

    # --- 3. RENDERING: DASHBOARD VIEWS ---

    # Render Suggestions Table if present
    if "suggestions" in st.session_state:
        st.header("🚀 AI Daily Recommendations")
        suggest_df = pd.DataFrame(st.session_state["suggestions"])
        if not suggest_df.empty:
            st.dataframe(
                suggest_df,
                column_config={
                    "Price": st.column_config.NumberColumn(
                        "Current Price", format="$0,0.00"
                    ),
                    "Expected Return": st.column_config.NumberColumn(
                        "Exp. Return", format="0.00%"
                    ),
                    "Ticker": st.column_config.TextColumn("Symbol"),
                },
                hide_index=True,
                use_container_width=True,
            )
            st.info(
                "Signals are based on the latest available market close and your trained models."
            )
        else:
            st.warning("No suggestions generated. Check your data connection.")

    # Render Backtest Results if present
    if "results" in st.session_state:
        render_glossary()
        results = st.session_state["results"]
        active_mode = st.session_state["active_mode"]

        if active_mode == "Find Super Stars":
            render_super_stars(
                st.session_state.get("active_index", "ASX Index"), results
            )
        else:
            for ticker, ticker_res in results.items():
                if active_mode == "Models Comparison":
                    render_algorithm_comparison(ticker, ticker_res)
                else:
                    render_strategy_sensitivity(ticker, ticker_res)
                st.markdown("---")

    # If nothing is active, show the welcome message
    if "results" not in st.session_state and "suggestions" not in st.session_state:
        st.info(
            "Welcome! Configure the sidebar and click 'Run Analysis' or 'Generate Suggestions' to start."
        )


if __name__ == "__main__":
    main()
