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
        st.set_page_config(
            page_title="Australian Stock AI Strategy Lab", page_icon="🇦🇺", layout="wide"
        )
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

    mode, test_periods, period_map, run_analysis, tie_breaker, index_choice = (
        sidebar_res
    )

    # --- 1. ACTION: RUN BACKTEST ANALYSIS ---
    if run_analysis:
        # ... (analysis logic stays the same) ...
        # [Collapsed for brevity in this edit plan]
        pass

    # --- 3. RENDERING: DASHBOARD VIEWS ---
    if "results" in st.session_state:
        # ... (rendering logic stays the same) ...
        pass
    else:
        st.info(
            "👈 Use the sidebar to configure your Australian trading strategy and click 'Run Analysis'."
        )

        st.subheader("🇦🇺 Australia Market Notes")
        col1, col2 = st.columns(2)
        with col1:
            st.write(
                "- **T+2 Settlement**: Capital from a sale is locked for 2 trading days."
            )
            st.write(
                "- **ATO Tax**: Capital gains subject to individual income tax (50% discount if held > 12 months)."
            )
        with col2:
            st.write(
                "- **Brokerage**: Default assumes standard online rates (e.g. $6-$11 min)."
            )
            st.write("- **Market Hours**: 10:00 AM - 4:00 PM AEST.")
            st.write("- **Currency**: All figures in AUD (Australian Dollar).")


if __name__ == "__main__":
    main()
