"""
Trading AI System - Main Application Entry Point (USA Edition)

Purpose: Dashboard for multi-model AI trading strategy analysis
with realistic backtesting and performance metrics.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
import pandas as pd
import logging
import os
import gc

# Suppress TensorFlow noise early
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
try:
    import tensorflow as tf

    tf.get_logger().setLevel("ERROR")
    tf.autograph.set_verbosity(0)
except ImportError:
    pass

# Set page config FIRST
st.set_page_config(
    page_title="USA Stock AI Strategy Lab",
    page_icon="🇺🇸",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.sidebar import render_sidebar
from core.model_builder import ModelBuilder
from core.backtest_engine import BacktestEngine
from core.config import BROKERS, get_tax_profile

# View Modules
from ui.strategy_view import render_strategy_view
from ui.stars_view import render_stars_view

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main application loop."""

    # 1. Render Sidebar & Get Config
    config = render_sidebar()

    # Header with Flag and Title (Unified Style)
    st.title("📈 USA Stock AI Trading Strategy Dashboard")

    # 2. Main Content Area
    if "results" not in st.session_state:
        render_initial_screen()

    if config["mode"] == "Models Comparison":
        render_models_comparison(config)
    elif config["mode"] == "Time-Span Comparison":
        render_strategy_view(config)
    elif config["mode"] == "Find Super Stars":
        render_stars_view(config)


def render_initial_screen():
    st.info(
        "👈 Use the sidebar to configure your USA trading strategy and click 'Run Analysis'."
    )

    st.subheader("🇺🇸 USA Market Notes")
    col1, col2 = st.columns(2)
    with col1:
        st.write("- **T+1 Settlement**: Capital available next business day (Fast).")
        st.write(
            "- **Tax (W-8BEN)**: 15% Dividend Withholding, $0 Capital Gains (Treaty)."
        )
        st.write(
            "- **Market Regime**: AI uses **^VIX** (Fear) & **^TNX** (Yields) as signals."
        )
    with col2:
        st.write(
            "- **Brokerage**: Low cost ($1-$3) but high FX friction (~70bps) for AU investors."
        )
        st.write("- **Market Hours**: 9:30 AM - 4:00 PM ET.")
        st.write("- **Currency**: All figures in USD.")
    st.markdown("---")


def render_models_comparison(config):
    """View 1: Compare individual models on a single ticker."""

    if "analysis_complete" not in st.session_state:
        render_initial_screen()

    st.header(f"Model Leaderboard: {config['ticker']}")

    if st.button("Run Analysis"):
        st.session_state["analysis_complete"] = True
        with st.spinner(f"Fetching data for {config['ticker']}..."):
            # 1. Build Model Factory
            factory = ModelBuilder(config["ticker"], "2015-01-01", "2025-01-01")
            data = factory.fetch_data()

            if data.empty:
                st.error(f"Could not fetch data for {config['ticker']}.")
                return

            # Preprocess
            data = factory.preprocess_data()

            # 2. Train & Backtest Each Algorithm
            results = []

            progress_bar = st.progress(0)
            algorithms = factory.SUPPORTED_ALGORITHMS

            for i, algo in enumerate(algorithms):
                st.text(f"Training {algo}...")
                train_metrics = factory.train_model(algo)

                if train_metrics.get("status") == "error":
                    continue

                # Generate Signals using Test Set (Out-of-Sample)
                split_idx = int(len(data) * 0.8)
                test_data = data.iloc[split_idx:].copy()

                X_test = test_data[factory.features]
                X_test_scaled = factory.scaler.transform(X_test)
                signals = factory.model.predict(X_test_scaled)

                # Run Backtest Engine
                engine = BacktestEngine(test_data, initial_capital=config["capital"])
                # Override broker/tax from config
                engine.broker = BROKERS[config["broker"]]
                engine.tax_profile = get_tax_profile(config["w8ben"])

                engine.run_strategy(pd.Series(signals, index=test_data.index))
                perf = engine.get_performance_summary()

                results.append(
                    {
                        "Algorithm": algo,
                        "Accuracy": f"{train_metrics['accuracy']:.2%}",
                        "Precision": f"{train_metrics['precision']:.2%}",
                        "Net Profit": f"${perf['Net Profit ($)']:,.2f}",
                        "ROI": f"{perf['ROI (%)']}%",
                        "Trades": perf["Total Trades"],
                    }
                )

                progress_bar.progress((i + 1) / len(algorithms))

                # Memory cleanup
                gc.collect()
                try:
                    import tensorflow as tf

                    tf.keras.backend.clear_session()
                except ImportError:
                    pass

            # 3. Display Results
            st.success("Analysis Complete!")
            df_results = pd.DataFrame(results)
            st.table(df_results)

            # Performance Visualization
            if not df_results.empty and "engine" in locals():
                st.subheader("Performance Visualization")
                df_history = pd.DataFrame(engine.history)
                if not df_history.empty:
                    # Plot realized equity curve from SELL actions
                    equity_curve = df_history[
                        df_history["Action"].isin(["SELL"])
                    ].set_index("Date")["Total"]

                    if not equity_curve.empty:
                        st.line_chart(equity_curve)
                        st.caption(
                            f"Realized Equity Curve ({results[-1]['Algorithm']})"
                        )
                    else:
                        st.info("No closed trades to plot.")


if __name__ == "__main__":
    main()
