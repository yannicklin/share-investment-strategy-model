"""Sidebar components for the ASX AI Trading System."""

import streamlit as st
from core.config import Config


def render_sidebar(config: Config):
    """Renders all sidebar inputs and returns the selected analysis mode."""

    st.sidebar.header("Analysis Mode")
    is_strategy_mode = st.sidebar.toggle(
        "Strategy Sensitivity (Time-Span)",
        value=False,
        help="OFF: Compare AI models. ON: Find the best holding period using consensus.",
    )
    analysis_mode = (
        "Strategy Sensitivity" if is_strategy_mode else "Algorithm Comparison"
    )

    st.sidebar.header("Configuration")

    # Tickers
    ticker_input = st.sidebar.text_input(
        "Target Tickers (semicolon separated)", ";".join(config.target_stock_codes)
    )
    config.target_stock_codes = [t.strip() for t in ticker_input.split(";")]

    # Capital & History
    config.backtest_years = st.sidebar.slider(
        "Backtest Years", 1, 10, config.backtest_years
    )
    config.init_capital = st.sidebar.number_input(
        "Initial Capital", value=config.init_capital
    )

    # Risk Thresholds
    config.stop_loss_threshold = st.sidebar.slider(
        "Stop-Loss Threshold", 0.01, 0.50, config.stop_loss_threshold
    )
    config.stop_profit_threshold = st.sidebar.slider(
        "Take-Profit Threshold", 0.01, 1.0, config.stop_profit_threshold
    )

    # Mode-Specific Parameters
    test_periods = []
    period_map = {}
    tie_breaker = None

    if analysis_mode == "Algorithm Comparison":
        col_unit, col_val = st.sidebar.columns([2, 1])
        unit_options = ["day", "month", "quarter", "year"]
        unit_index = (
            unit_options.index(config.hold_period_unit)
            if config.hold_period_unit in unit_options
            else 1
        )
        config.hold_period_unit = col_unit.selectbox(
            "Fixed Min Hold Unit", unit_options, index=unit_index
        )
        config.hold_period_value = col_val.number_input(
            "Val", value=config.hold_period_value, min_value=1
        )

        config.model_types = st.sidebar.multiselect(
            "AI Algorithms to Compare",
            ["random_forest", "xgboost", "catboost", "prophet", "lstm"],
            default=config.model_types,
        )
    else:
        # Strategy Mode
        config.model_types = st.sidebar.multiselect(
            "Consensus Models (Committee)",
            ["random_forest", "xgboost", "catboost", "prophet", "lstm"],
            default=["random_forest", "catboost"],
        )

        if len(config.model_types) > 0 and len(config.model_types) % 2 == 0:
            tie_breaker = st.sidebar.selectbox(
                "⚖️ Tie-Breaker Model",
                config.model_types,
                help="If models are split 50/50, this model makes the final decision.",
            )

        test_periods = st.sidebar.multiselect(
            "Evaluate Holding Spans",
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

    # Data Preprocessing
    config.scaler_type = st.sidebar.radio(
        "Feature Scaler",
        ["standard", "robust"],
        index=0 if config.scaler_type == "standard" else 1,
    )

    # Costs & Taxes
    with st.sidebar.expander("Costs & Taxes"):
        config.cost_profile = st.selectbox(
            "Profile",
            ["default", "cmc_markets"],
            index=0 if config.cost_profile == "default" else 1,
        )
        config.annual_income = st.number_input(
            "Annual Income", value=config.annual_income, step=5000.0
        )

    config.rebuild_model = st.sidebar.checkbox(
        "Rebuild AI Model", value=config.rebuild_model
    )

    st.sidebar.markdown("---")
    gen_suggestions = st.sidebar.button("💡 Generate Live Suggestions")

    return analysis_mode, test_periods, period_map, gen_suggestions, tie_breaker
