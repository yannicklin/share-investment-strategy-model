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
        # Initial State (No Analysis Run)
        render_initial_screen()

    # We need to handle the "Run Analysis" button click inside the render functions
    # or reorganize main.py to separate the "Run" logic from the "Render" logic like ASX/TWN.
    # The current USA implementation puts the "Run" button inside the sub-functions.
    # To keep it consistent with the "Initial Screen" logic of ASX, we check if analysis has been run.

    # However, the USA implementation structure is slightly different (View-based vs Result-based).
    # I will adapt the "Initial Screen" to appear only if the user hasn't clicked "Run" yet.
    # But since the buttons are inside the sub-functions, we need to render the sub-functions first?
    # No, ASX renders the sidebar, then if 'Run' is clicked, it processes.

    # Let's look at the current USA main.py again.
    # It calls `render_models_comparison` which contains `if st.button("Run Analysis"):`.
    # This means the "Initial Screen" logic is tricky because the button is deeply nested.

    # FIX: The ASX/TWN pattern separates the "Run" button into the Sidebar or Main loop.
    # But to minimize refactoring risk, I will inject the "Market Notes" into the top of the page
    # and keep the current flow, OR I will replicate the ASX pattern of "Check if results exist".

    # In the current USA `main.py`, the views are:
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

                # Generate Signals (Use Test Set Predictions for Backtest)
                # Note: In a real scenario, we'd do a rolling window backtest.
                # For simplicity here, we use the model's predictions on the test set (last 20% of data).
                # To do a full backtest, we need predictions for the whole period or a walk-forward.
                # Here we will simulate a "Paper Trade" on the test set.

                # Get predictions for the entire dataset (Warning: Lookahead bias on training set!)
                # BETTER: Use Out-of-Sample only for backtest.

                # Split index for test set
                split_idx = int(len(data) * 0.8)
                test_data = data.iloc[split_idx:].copy()

                # Generate predictions for test data
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

            # Show Equity Curve for Best Model (Optional)
            if not df_results.empty:
                st.subheader("Performance Visualization")
                # For now, we only have data for the last run (from the loop).
                # In a full implementation, we would store all engine histories.
                # Just showing the equity curve of the last model run as an example.
                if "engine" in locals():
                    df_history = pd.DataFrame(engine.history)
                    if not df_history.empty:
                        # Reconstruct equity curve from trade history
                        # Note: This is a simplified reconstruction. Ideally BacktestEngine returns a daily equity series.
                        # For now, let's just plot the 'Total' column from trade history (Cash after trade)
                        # Filter for SELL actions to see realized equity
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
