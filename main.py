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

# Set page config FIRST
st.set_page_config(
    page_title="US Market AI Strategy",
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

    # Header with Flag and Title
    st.title("🇺🇸 US Market AI Strategy")
    st.markdown(
        """
        **Market Context**: The US Stock Market (NYSE/NASDAQ) is the largest and most liquid in the world. 
        It is characterized by high institutional participation, strong trends in Tech/Growth sectors, 
        and high sensitivity to **Macro Regimes** (Federal Reserve Policy, VIX).
        
        *This model integrates specific US friction layers including SEC fees, W-8BEN tax treaties, and T+1 Settlement.*
        """
    )
    st.markdown("---")

    st.header(f"Analysis Mode: {config['mode']}")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.caption(
            f"Broker: {config['broker']} | Capital: ${config['capital']:,.2f} | W-8BEN: {'✅ Filed' if config['w8ben'] else '❌ Not Filed'}"
        )
    with col2:
        st.caption("🧠 Market Regime: **Active** (^VIX + ^TNX)")

    # 2. Main Content Area
    if config["mode"] == "Models Comparison":
        render_models_comparison(config)
    elif config["mode"] == "Time-Span Comparison":
        render_strategy_view(config)
    elif config["mode"] == "Find Super Stars":
        render_stars_view(config)


def render_models_comparison(config):
    """View 1: Compare individual models on a single ticker."""
    st.header(f"Model Leaderboard: {config['ticker']}")

    if st.button("Run Analysis"):
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
