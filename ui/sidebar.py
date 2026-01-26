"""Sidebar components for the ASX AI Trading System."""

import streamlit as st
from core.config import Config


def render_sidebar(config: Config):
    """Renders all sidebar inputs and returns the selected analysis mode."""

    st.sidebar.header("Analysis Mode")

    # Shortening labels to ensure they fit on one horizontal line in the sidebar
    modes = ["Models", "Time-Span"]

    analysis_mode_short = st.sidebar.segmented_control(
        "Workflow Selection",
        options=modes,
        default="Models",
        label_visibility="collapsed",
        help="Toggle between benchmarking AI models and analyzing holding periods.",
    )

    # Map back to full names for logic consistency
    mode_map = {"Models": "Models Comparison", "Time-Span": "Time-Span Comparison"}
    analysis_mode = mode_map.get(analysis_mode_short, "Models Comparison")

    # --- 1. SHARED CONFIGURATION ---
    st.sidebar.header("Global Settings")

    ticker_input = st.sidebar.text_input(
        "Target Tickers (semicolon separated)", ";".join(config.target_stock_codes)
    )
    config.target_stock_codes = [t.strip() for t in ticker_input.split(";")]

    config.backtest_years = st.sidebar.slider(
        "Backtest Years", 1, 10, config.backtest_years
    )
    config.init_capital = st.sidebar.number_input(
        "Initial Capital", value=float(config.init_capital), format="%.2f", step=100.0
    )

    # Risk Thresholds
    config.stop_loss_threshold = st.sidebar.slider(
        "Stop-Loss Threshold", 0.01, 0.50, config.stop_loss_threshold
    )
    config.stop_profit_threshold = st.sidebar.slider(
        "Take-Profit Threshold", 0.01, 1.0, config.stop_profit_threshold
    )

    # --- 2. MODE-SPECIFIC CONFIGURATION ---
    st.sidebar.header(f"{analysis_mode} Settings")

    test_periods = []
    period_map = {}
    tie_breaker = None

    if analysis_mode == "Models Comparison":
        # Strategy fields only relevant when comparing models
        col_unit, col_val = st.sidebar.columns([2, 1])
        unit_options = ["day", "month", "quarter", "year"]
        unit_index = (
            unit_options.index(config.hold_period_unit)
            if config.hold_period_unit in unit_options
            else 1
        )
        config.hold_period_unit = col_unit.selectbox(
            "Strategy Hold Unit", unit_options, index=unit_index
        )
        config.hold_period_value = col_val.number_input(
            "Val", value=config.hold_period_value, min_value=1
        )

        config.model_types = st.sidebar.multiselect(
            "AI Algorithms to Benchmark",
            ["random_forest", "xgboost", "catboost", "prophet", "lstm"],
            default=config.model_types,
        )
    else:
        # Time-Span Comparison Fields
        config.model_types = st.sidebar.multiselect(
            "Select AI Committee",
            ["random_forest", "xgboost", "catboost", "prophet", "lstm"],
            default=["random_forest", "catboost"],
        )

        # Tie-breaker only for consensus mode with even numbers
        if len(config.model_types) > 0 and len(config.model_types) % 2 == 0:
            tie_breaker = st.sidebar.selectbox(
                "⚖️ Consensus Tie-Breaker",
                config.model_types,
                help="If the AI committee is split 50/50, this model makes the final decision.",
            )

        test_periods = st.sidebar.multiselect(
            "Time-Spans to Evaluate",
            ["1 day", "1 week", "2 weeks", "1 month", "3 months", "6 months", "1 year"],
            default=["1 day", "1 month", "1 year"],
        )
        period_map = {
            "1 day": ("day", 1),
            "1 week": ("day", 7),
            "2 weeks": ("day", 14),
            "1 month": ("month", 1),
            "3 months": ("month", 3),
            "6 months": ("month", 6),
            "1 year": ("year", 1),
        }

    # Data Preprocessing & Accounting (Always at bottom)
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

    config.rebuild_model = st.sidebar.checkbox(
        "Force Rebuild AI Models", value=config.rebuild_model
    )

    st.sidebar.markdown("---")
    gen_suggestions = st.sidebar.button("💡 Generate Live Suggestions")

    return analysis_mode, test_periods, period_map, gen_suggestions, tie_breaker
