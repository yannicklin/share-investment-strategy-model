"""
Taiwan Stock AI Trading System - Sidebar Component

Purpose: Streamlit sidebar for mode selection, ticker input, and
backtest parameters.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import os

import streamlit as st

from core.config import Config
from core.index_manager import load_index_constituents, update_index_data
from core.model_builder import ModelBuilder


def clean_all_models(model_path: str) -> bool:
    """
    Remove all model files and ledger data.

    Args:
        model_path: Path to model directory

    Returns:
        True if successful, False otherwise
    """
    try:
        # Clean model files
        if os.path.exists(model_path):
            for filename in os.listdir(model_path):
                if filename.endswith((".joblib", ".h5", ".keras", ".json", ".pkl")):
                    file_path = os.path.join(model_path, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)

        # Clean ledger data
        ledger_path = "data/ledgers"
        if os.path.exists(ledger_path):
            for filename in os.listdir(ledger_path):
                if filename.endswith(".csv"):
                    file_path = os.path.join(ledger_path, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)

        return True
    except Exception as e:
        st.error(f"Error cleaning models and ledgers: {e!s}")
        return False


def render_sidebar(config: Config):
    """Renders all sidebar inputs and returns the selected analysis mode."""

    # Initialize session state
    if "show_model_cleanup_confirm" not in st.session_state:
        st.session_state.show_model_cleanup_confirm = False

    # Inject custom CSS for a friendlier Dark Mode sidebar
    st.markdown(
        """
        <style>
            /* Sidebar background and borders */
            [data-testid="stSidebar"] {
                border-right: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            /* Sidebar Headers */
            [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
                color: #27ae60 !important;
                font-weight: 700 !important;
                letter-spacing: -0.5px !important;
            }

            /* Buttons in Sidebar */
            [data-testid="stSidebar"] button {
                border-radius: 8px !important;
                font-weight: 600 !important;
                transition: all 0.3s ease !important;
            }
            
            [data-testid="stSidebar"] button:hover {
                border-color: #27ae60 !important;
                color: #27ae60 !important;
                box-shadow: 0 0 10px rgba(39, 174, 96, 0.2) !important;
            }

            /* Horizontal dividers */
            [data-testid="stSidebar"] hr {
                margin: 1rem 0 !important;
                border-color: rgba(255, 255, 255, 0.1) !important;
            }

            /* Better padding for sidebar content */
            [data-testid="stSidebarContent"] {
                padding-top: 1.5rem !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

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
        # Safety check: ensure index_data is a valid dict
        if not isinstance(index_data, dict):
            st.sidebar.error("❌ Failed to load index data. Using defaults.")
            index_data = {}

        index_choice = st.sidebar.selectbox(
            "Select Index to Scan",
            list(index_data.keys()) if index_data else [],
            help="台股50: Blue Chips. 台股中型100: Growth & Value. MSCI: Global Standard.",
        )

        if st.sidebar.button(
            "🔄 Update Index Constituents",
            help="Sync latest index constituents from TWSE (Taiwan Stock Exchange)",
        ):
            with st.spinner("Fetching latest market data from TWSE..."):
                results = update_index_data()
                if results:
                    st.sidebar.success("Updated!")
                    for idx, msg in results.items():
                        st.sidebar.caption(f"{idx}: {msg}")
                    # Reload data immediately after update
                    index_data = load_index_constituents()
                    if not isinstance(index_data, dict):
                        st.sidebar.error("Failed to reload index data. Using cache.")
                        index_data = {}
                else:
                    st.sidebar.error("Failed to fetch index data. Using cached data.")

        # Safely get target stock codes
        if index_data and index_choice:
            config.target_stock_codes = index_data.get(index_choice, [])
        else:
            config.target_stock_codes = []

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
        "2 days": ("day", 2),
        "1 week": ("day", 7),
        "2 weeks": ("day", 14),
        "1 month": ("month", 1),
        "3 months": ("month", 3),
        "6 months": ("month", 6),
        "1 year": ("year", 1),
    }
    tie_breaker = None

    if analysis_mode == "Models Comparison":
        col_unit, col_val = st.sidebar.columns([2, 1])
        unit_options = ["day", "week", "month", "year"]
        config.hold_period_unit = col_unit.selectbox(
            "Holding Period", unit_options, index=2
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
            [
                "1 day",
                "2 days",
                "1 week",
                "2 weeks",
                "1 month",
                "3 months",
                "6 months",
                "1 year",
            ],
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
            "Strategy Time-Span",
            [
                "1 day",
                "2 days",
                "1 week",
                "2 weeks",
                "1 month",
                "3 months",
                "6 months",
                "1 year",
            ],
            index=4,  # Default to "1 month"
        )
        test_periods = [star_period]

    # --- 3. PREPROCESSING & ACCOUNTING ---
    st.sidebar.markdown("---")
    config.weighting_type = st.sidebar.radio(
        "Sample Weighting",
        ["normal", "recency"],
        index=0 if config.weighting_type == "normal" else 1,
        help="Normal: Uniform weights. Recency: Exponential decay favoring recent data (half-life = backtest_years × multiplier set in config).",
    )

    with st.sidebar.expander("Costs & Taxes"):
        profile_options = ["default", "fubon_twn", "first_twn"]
        profile_names = {
            "default": "無折扣 (Default)",
            "fubon_twn": "富邦證券 (Fubon)",
            "first_twn": "第一金證券 (First)",
        }
        config.cost_profile = st.selectbox(
            "Broker Profile",
            profile_options,
            format_func=lambda x: str(profile_names.get(x, x)),
            index=profile_options.index(config.cost_profile)
            if config.cost_profile in profile_options
            else 0,
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

    # --- 4. MODEL MANAGEMENT ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🧹 Model & Ledger Management")

    # Clean models and ledgers button
    if st.sidebar.button(
        "🗑️ Clean out all models & ledgers",
        key="clean_models_btn",
        help="Remove all trained model files and transaction ledgers (force retraining on next run)",
        use_container_width=True,
    ):
        st.session_state.show_model_cleanup_confirm = True

    # Show confirmation dialog if user clicked clean button
    if st.session_state.get("show_model_cleanup_confirm", False):
        st.sidebar.warning("⚠️ This will delete all model files and ledger data!")

        confirm_clicked = st.sidebar.button(
            "✅ Confirm Delete", key="confirm_cleanup", use_container_width=True
        )
        cancel_clicked = st.sidebar.button(
            "❌ Cancel", key="cancel_cleanup", use_container_width=True
        )

        if confirm_clicked:
            if clean_all_models(config.model_path):
                st.session_state.show_model_cleanup_confirm = False
                st.sidebar.success("✅ Models & ledgers cleaned!")
                st.rerun()

        if cancel_clicked:
            st.session_state.show_model_cleanup_confirm = False
            st.rerun()

    st.sidebar.markdown("---")
    run_analysis = st.sidebar.button("🚀 Run Analysis", use_container_width=True)

    return (
        analysis_mode,
        test_periods,
        period_map,
        run_analysis,
        tie_breaker,
        index_choice,
    )
