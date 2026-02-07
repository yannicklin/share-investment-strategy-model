"""
Taiwan Stock AI Trading System - Core Entry Point

Purpose: Orchestrates the AI training, backtesting, and visualization
for Taiwan market stocks.

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

# Page Configuration
st.set_page_config(
    page_title="Taiwan Stock AI Strategy Lab",
    page_icon="🇹🇼",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    # 1. Initialize Configuration
    config = load_config()

    # 2. Render Sidebar & Get User Inputs
    sidebar_res = render_sidebar(config)
    if sidebar_res is None:
        st.error("Sidebar failed to render.")
        return

    (
        analysis_mode,
        test_periods,
        period_map,
        run_analysis,
        tie_breaker,
        index_choice,
    ) = sidebar_res

    st.title("📈 Taiwan Stock AI Trading Strategy Dashboard")

    # 4. Main Execution Logic
    if run_analysis:
        # Clear previous results
        if "results" in st.session_state:
            del st.session_state["results"]

        all_results = {}
        st.session_state["active_builder"] = ModelBuilder(config)
        builder = st.session_state["active_builder"]
        engine = BacktestEngine(config, builder)

        tickers = config.target_stock_codes

        with st.spinner(
            f"Pre-fetching historical data for {len(tickers)} Taiwan stocks..."
        ):
            builder.prefetch_data_batch(tickers, config.backtest_years)

        prog_placeholder = st.empty()

        for idx, ticker in enumerate(tickers):
            ticker_results = {}
            with prog_placeholder.container():
                st.write(f"### 🔍 Analyzing {ticker} ({idx + 1}/{len(tickers)})")
                st.progress((idx) / len(tickers))

                with st.status(f"Processing {ticker}...", expanded=True) as status:
                    try:
                        # Model Preparation
                        for m_type in config.model_types:
                            config.model_type = m_type
                            try:
                                builder.load_or_build(ticker)
                            except Exception as e:
                                st.error(f"Model Error ({m_type}): {e}")

                        if analysis_mode == "Models Comparison":
                            for m_type in config.model_types:
                                ticker_results[m_type] = engine.run_model_mode(
                                    ticker, m_type
                                )
                        elif analysis_mode == "Time-Span Comparison":
                            for p_name in test_periods:
                                unit, val = period_map[p_name]
                                config.hold_period_unit, config.hold_period_value = (
                                    unit,
                                    val,
                                )
                                ticker_results[p_name] = engine.run_strategy_mode(
                                    ticker, config.model_types, tie_breaker=tie_breaker
                                )
                        else:
                            # Super Stars Mode
                            p_name = test_periods[0]
                            unit, val = period_map[p_name]
                            config.hold_period_unit, config.hold_period_value = (
                                unit,
                                val,
                            )
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

        st.session_state["results"] = all_results
        st.session_state["active_mode"] = analysis_mode
        st.session_state["trigger_rerun"] = True
        prog_placeholder.empty()

    if st.session_state.get("trigger_rerun"):
        st.session_state["trigger_rerun"] = False
        st.rerun()

    # --- RENDERING ---
    if "results" in st.session_state:
        results = st.session_state["results"]
        render_glossary()
        active_mode = st.session_state["active_mode"]

        if active_mode == "Find Super Stars":
            render_super_stars(
                "Taiwan Index",
                results,
                models=config.model_types,
                tie_breaker=tie_breaker,
            )
        else:
            for ticker, ticker_res in results.items():
                if "error" in ticker_res:
                    st.error(f"Error for {ticker}: {ticker_res['error']}")
                    continue
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

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🇹🇼 Taiwan Market Rules")
            st.write("- **T+2 Settlement**: Strict cash clearing enforcement.")
            st.write("- **No Capital Gains Tax**: 0% CGT for individuals.")
            st.write("- **High Friction (STT)**: 0.3% tax on every sell order.")
            st.write("- **Circuit Breakers**: Daily price limit of ±10%.")

        with col2:
            st.subheader("🏢 Supported Brokers")
            st.write("- **Fubon Securities (富邦)**: Python SDK support.")
            st.write("- **First Securities (第一)**: High reliability.")
            st.write("- **Standard Online**: 0.1425% default rate.")


if __name__ == "__main__":
    main()
