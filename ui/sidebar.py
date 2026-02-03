"""
ASX AI Trading System - Sidebar Component

Purpose: Streamlit sidebar for mode selection, ticker input, and
backtest parameters.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
import yfinance as yf
from core.config import Config
from core.index_manager import load_index_constituents, update_index_data
from core.model_builder import ModelBuilder


def render_sidebar(config: Config):
    """Renders all sidebar inputs and returns the selected analysis mode."""

    st.sidebar.header("Analysis Mode")

    # Selection mode
    analysis_mode_short = st.sidebar.segmented_control(
        "Workflow Selection",
        options=["Models", "Time-Span", "Super Stars"],
        default="Models",
        label_visibility="collapsed",
        help="Models: Compare AI algorithms. Time-Span: Find best period. Super Stars: Find top 10 stocks.",
    )

    # Get available models based on installed libraries
    available_models = ModelBuilder.get_available_models()

    # Map back to full names
    mode_map = {
        "Models": "Models Comparison",
        "Time-Span": "Time-Span Comparison",
        "Super Stars": "Find Super Stars",
    }
    short_val = str(analysis_mode_short) if analysis_mode_short else "Models"
    analysis_mode = mode_map.get(short_val, "Models Comparison")
    index_choice = None

    # --- 1. SHARED GLOBAL SETTINGS ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Strategy Parameters")

    if analysis_mode != "Find Super Stars":
        ticker_input = st.sidebar.text_input(
            "Target Tickers (semicolon separated)", ";".join(config.target_stock_codes)
        )
        # Filter out empty tickers and normalize format
        config.target_stock_codes = [
            t.strip().upper()
            for t in ticker_input.split(";")
            if t.strip() and len(t.strip()) > 0
        ]
    else:
        # Super Star Index Choice
        st.sidebar.subheader("Index Selection")
        index_data = load_index_constituents()
        index_choice = st.sidebar.selectbox(
            "Select Index to Scan",
            list(index_data.keys()),
            help="ASX 50: Blue Chips. ASX 200: Benchmark index.",
        )

        if st.sidebar.button("🔄 Update Index Constituents"):
            with st.spinner("Fetching latest market data..."):
                results = update_index_data()
                st.sidebar.success("Updated!")
                for idx, msg in results.items():
                    st.sidebar.caption(f"{idx}: {msg}")
                # Reload data immediately after update
                index_data = load_index_constituents()

        config.target_stock_codes = index_data.get(index_choice, [])

    config.backtest_years = st.sidebar.slider(
        "Backtest Years", 1, 10, config.backtest_years
    )
    config.init_capital = st.sidebar.number_input(
        "Initial Capital", value=float(config.init_capital), format="%.2f", step=100.0
    )

    # Display as percentage but store as decimal
    sl_val = st.sidebar.slider(
        "Stop-Loss Threshold",
        1.0,
        50.0,
        float(config.stop_loss_threshold * 100),
        step=0.5,
        format="%.1f%%",
    )
    config.stop_loss_threshold = sl_val / 100.0

    tp_val = st.sidebar.slider(
        "Take-Profit Threshold",
        1.0,
        100.0,
        float(config.stop_profit_threshold * 100),
        step=1.0,
        format="%.0f%%",
    )
    config.stop_profit_threshold = tp_val / 100.0

    # --- 2. MODE-SPECIFIC CONFIGURATION ---
    st.sidebar.header(f"{analysis_mode} Settings")

    test_periods = []
    period_map = {
        "1 day": ("day", 1),
        "1 week": ("day", 7),
        "2 weeks": ("day", 14),
        "1 month": ("month", 1),
        "3 months": ("month", 3),
        "1 quarter": ("month", 3),
        "6 months": ("month", 6),
        "1 year": ("year", 1),
    }
    tie_breaker = None

    if analysis_mode == "Models Comparison":
        col_unit, col_val = st.sidebar.columns([2, 1])
        unit_options = ["day", "month", "quarter", "year"]
        config.hold_period_unit = col_unit.selectbox(
            "Strategy Hold Unit", unit_options, index=1
        )
        config.hold_period_value = col_val.number_input("Val", value=1, min_value=1)
        config.model_types = st.sidebar.multiselect(
            "AI Algorithms to Benchmark",
            available_models,
            default=[m for m in config.model_types if m in available_models],
        )

    elif analysis_mode == "Time-Span Comparison":
        config.model_types = st.sidebar.multiselect(
            "Select AI Committee",
            available_models,
            default=[m for m in config.model_types if m in available_models],
        )
        if len(config.model_types) > 0 and len(config.model_types) % 2 == 0:
            tie_breaker = st.sidebar.selectbox(
                "⚖️ Consensus Tie-Breaker", config.model_types
            )
        test_periods = st.sidebar.multiselect(
            "Time-Spans to Evaluate",
            ["1 day", "1 week", "1 month", "3 months", "1 year"],
            default=["1 day", "1 month", "1 year"],
        )

    else:
        # Find Super Stars (Mode 3)
        config.model_types = st.sidebar.multiselect(
            "Select AI Committee",
            available_models,
            default=[m for m in config.model_types if m in available_models],
        )
        if len(config.model_types) > 0 and len(config.model_types) % 2 == 0:
            tie_breaker = st.sidebar.selectbox(
                "⚖️ Consensus Tie-Breaker", config.model_types
            )
        star_period = st.sidebar.selectbox(
            "Strategy Time-Span", ["1 month", "1 quarter", "1 year"], index=0
        )
        test_periods = [star_period]

    # --- 3. PREPROCESSING & ACCOUNTING ---
    st.sidebar.markdown("---")
    config.scaler_type = st.sidebar.radio(
        "Feature Scaler",
        ["standard", "robust"],
        index=0 if config.scaler_type == "standard" else 1,
    )

    with st.sidebar.expander("Costs & Taxes"):
        config.cost_profile = st.selectbox(
            "Broker Profile",
            ["default", "cmc_markets"],
            index=0 if config.cost_profile == "default" else 1,
        )
        config.annual_income = st.number_input(
            "Annual Income (for Tax)",
            value=float(config.annual_income),
            format="%.2f",
            step=5000.0,
        )
        # Display as percentage (0-5%) but store as decimal (0-0.05)
        buffer_val = st.slider(
            "Hurdle Risk Buffer",
            0.0,
            5.0,
            float(config.hurdle_risk_buffer * 100),
            step=0.1,
            format="%.1f%%",
            help="Extra profit margin required after fees and tax to trigger a BUY.",
        )
        config.hurdle_risk_buffer = buffer_val / 100.0

    config.rebuild_model = st.sidebar.checkbox(
        "Force Rebuild AI Models", value=config.rebuild_model
    )

    st.sidebar.markdown("---")
    run_analysis = st.sidebar.button("🚀 Run Analysis", width="stretch")

    return (
        analysis_mode,
        test_periods,
        period_map,
        run_analysis,
        tie_breaker,
        index_choice,
    )
