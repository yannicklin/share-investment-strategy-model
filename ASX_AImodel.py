"""ASX AI Trading System - Main Application Entry Point."""

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
    st.set_page_config(page_title="ASX AI Trading System", layout="wide")
    st.title("📈 ASX AI Trading Strategy Dashboard")

    # Load shared configuration
    config = load_config()

    # Render Sidebar and get parameters
    mode, test_periods, period_map, gen_suggestions, tie_breaker, index_choice = (
        render_sidebar(config)
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

        prog_placeholder = st.empty()
        progress_bar = prog_placeholder.progress(0)

        for i, ticker in enumerate(tickers_to_scan):
            with st.spinner(f"Analyzing {ticker} for today..."):
                votes, total_return, tie_breaker_bullish = 0, 0.0, False
                tb_model = tie_breaker if tie_breaker else config.model_types[0]
                latest_features = builder.get_latest_features(ticker)

                if latest_features is not None:
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
        st.rerun()

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
        prog_placeholder = st.empty()
        progress_bar = prog_placeholder.progress(0)

        for idx, ticker in enumerate(tickers):
            ticker_results = {}
            with st.spinner(f"Processing {ticker}... ({idx + 1}/{len(tickers)})"):
                # Pre-train/load
                original_rebuild = config.rebuild_model
                for m_type in config.model_types:
                    config.model_type = m_type
                    builder.load_or_build(ticker)
                config.rebuild_model = False

                if mode == "Models Comparison":
                    for m_type in config.model_types:
                        ticker_results[m_type] = engine.run_model_mode(ticker, m_type)
                elif mode == "Time-Span Comparison":
                    for p_name in test_periods:
                        unit, val = period_map[p_name]
                        config.hold_period_unit, config.hold_period_value = unit, val
                        ticker_results[p_name] = engine.run_strategy_mode(
                            ticker, config.model_types, tie_breaker=tie_breaker
                        )
                else:
                    # Find Super Stars (Mode 3)
                    p_name = test_periods[0]
                    unit, val = period_map[p_name]
                    config.hold_period_unit, config.hold_period_value = unit, val
                    ticker_results = engine.run_strategy_mode(
                        ticker, config.model_types, tie_breaker=tie_breaker
                    )

                all_results[ticker] = ticker_results
                config.rebuild_model = original_rebuild
            progress_bar.progress((idx + 1) / len(tickers))

        st.session_state["results"] = all_results
        st.session_state["active_mode"] = mode
        st.session_state["active_index"] = (
            index_choice if mode == "Find Super Stars" else "Custom List"
        )
        prog_placeholder.empty()
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
