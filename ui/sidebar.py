"""
USA AI Trading System - Sidebar Configuration

Purpose: Renders the Streamlit sidebar for user input parameters.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
import os
from core.config import BROKERS, load_config
from core.model_builder import ModelBuilder
from core.index_manager import load_index_constituents, update_index_data


def render_sidebar(config):
    """Renders all sidebar controls and returns user parameters."""
    st.sidebar.title("⚙️ USA Strategy Lab")

    # 1. Mode Selection
    mode = st.sidebar.radio(
        "Analysis Mode",
        ["Models Comparison", "Time-Span Comparison", "Find Super Stars"],
    )

    # 2. Market Data Selection
    st.sidebar.subheader("Market Universe")
    if mode == "Find Super Stars":
        indices = load_index_constituents()
        index_choice = st.sidebar.selectbox(
            "Select Index to Scan", list(indices.keys())
        )
        config.target_stock_codes = indices[index_choice]
        if st.sidebar.button("Update Constituents"):
            update_index_data()
            st.sidebar.success("Cache refreshed.")
    else:
        index_choice = "Custom List"
        ticker_input = (
            st.sidebar.text_input("Stock Ticker (e.g., AAPL, NVDA)", "NVDA")
            .upper()
            .strip()
        )
        config.target_stock_codes = [ticker_input]

    # 3. Strategy Parameters
    st.sidebar.subheader("Backtest Settings")
    config.init_capital = st.sidebar.number_input(
        "Initial Capital ($)", min_value=1000, value=10000, step=1000
    )
    config.backtest_years = st.sidebar.slider("Historical Lookback (Years)", 1, 10, 5)

    test_periods = ["Short (14d)", "Medium (30d)", "Long (90d)"]
    period_map = {
        "Short (14d)": ("day", 14),
        "Medium (30d)": ("day", 30),
        "Long (90d)": ("day", 90),
    }

    if mode == "Time-Span Comparison":
        test_periods = st.sidebar.multiselect(
            "Holding Periods to Compare", test_periods, default=test_periods
        )
    else:
        selected_p = st.sidebar.selectbox(
            "Standard Holding Period", test_periods, index=1
        )
        test_periods = [selected_p]
        config.hold_period_unit, config.hold_period_value = period_map[selected_p]

    # 4. Friction & Risk
    with st.sidebar.expander("Friction & Tax Settings"):
        config.cost_profile = st.selectbox("Broker Profile", list(BROKERS.keys()))
        config.w8ben = st.checkbox("W-8BEN Filed (0% CGT)", value=True)
        config.stop_loss_threshold = st.slider("Stop Loss (%)", 1, 20, 5) / 100
        config.stop_profit_threshold = st.slider("Take Profit (%)", 5, 50, 15) / 100
        config.hurdle_risk_buffer = st.slider("Risk Buffer (%)", 0.0, 5.0, 2.0) / 100

    # 5. AI Model Selection
    st.sidebar.subheader("AI Models")
    available_models = ModelBuilder.get_available_models()
    config.model_types = st.sidebar.multiselect(
        "Models to Include",
        available_models,
        default=["random_forest", "gradient_boosting", "lstm"],
    )

    tie_breaker = None
    if mode != "Models Comparison":
        tie_breaker = st.sidebar.selectbox("Consensus Tie-Breaker", config.model_types)

    config.rebuild_model = st.sidebar.checkbox("Force Rebuild AI Models", value=False)

    run_analysis = st.sidebar.button("🚀 Run Analysis", type="primary")

    return mode, test_periods, period_map, run_analysis, tie_breaker, index_choice
