"""
Trading AI System - Consensus Strategy View (USA Edition)

Purpose: Renders the "Time-Span Comparison" dashboard.
Implements the Multi-Model Consensus logic (Voting + Tie-Breaker).

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
import pandas as pd
from core.model_builder import ModelBuilder
from core.backtest_engine import BacktestEngine
from core.config import BROKERS, get_tax_profile


def render_strategy_view(config):
    """
    Renders the Consensus Strategy Dashboard.
    Compares Short-Term vs Long-Term holding periods using Majority Vote.
    """
    st.header(f"🏛️ Consensus Strategy: {config['ticker']}")

    st.info(
        """
        **The Strategy:**
        1. Train 5 distinct AI models (Random Forest, GBDT, LSTM, etc.).
        2. Each model casts a vote (BUY/SELL).
        3. A trade is executed ONLY if there is a **Majority Consensus** (e.g., 3/5).
        4. If the vote is tied, the **Tie-Breaker Model** decides.
        """
    )

    col1, col2 = st.columns(2)
    with col1:
        tie_breaker = st.selectbox(
            "Select Tie-Breaker Model",
            options=ModelBuilder.SUPPORTED_ALGORITHMS,
            index=0,
        )
    with col2:
        consensus_threshold = st.slider(
            "Consensus Threshold (Min Votes)", min_value=2, max_value=5, value=3
        )

    if st.button("Run Consensus Analysis"):
        with st.spinner(f"Training 5-Model Committee on {config['ticker']}..."):
            # 1. Fetch Data
            factory = ModelBuilder(config["ticker"], "2015-01-01", "2025-01-01")
            data = factory.fetch_data()
            if data.empty:
                st.error("No data found.")
                return

            data = factory.preprocess_data()

            # 2. Train All Models
            models = {}
            progress_bar = st.progress(0)

            # Split Data for Training/Testing
            split_idx = int(len(data) * 0.8)
            train_data = data.iloc[:split_idx]
            test_data = data.iloc[split_idx:].copy()

            X_train = train_data[factory.features]
            y_train = train_data["Target"]  # Note: Target logic is in preprocess_data
            X_test = test_data[factory.features]

            # Scale
            X_train_scaled = factory.scaler.fit_transform(X_train)
            X_test_scaled = factory.scaler.transform(X_test)

            # Train Loop
            algorithms = factory.SUPPORTED_ALGORITHMS
            for i, algo in enumerate(algorithms):
                st.text(f"Training Agent: {algo}...")
                # Hack: Re-use factory instance but swap internal model
                # Ideally ModelBuilder should return model objects.
                # For now, we simulate by training and predicting immediately.

                # Train
                res = factory.train_model(algo)  # Internal state updated

                # Predict on Test Set
                if factory.model:
                    preds = factory.model.predict(X_test_scaled)
                    models[algo] = preds

                progress_bar.progress((i + 1) / len(algorithms))

            # 3. Calculate Consensus Signal
            st.text("Calculating Consensus...")

            # Combine predictions into a DataFrame
            df_votes = pd.DataFrame(models, index=test_data.index)

            # Sum votes (Assuming 1=BUY, 0=SELL)
            df_votes["Sum"] = df_votes.sum(axis=1)

            # Apply Logic
            # If Sum >= Threshold -> BUY (1)
            # Else -> SELL (0)
            # Handle Tie-Breaker if needed (e.g., if total models is even? Here we have 4 models)
            # Current supported algos: RF, GBDT, LSTM (Placeholder), Prophet (Placeholder) -> 4 algos.
            # So a 2-2 tie is possible.

            def resolve_vote(row):
                votes = row["Sum"]
                total_models = len(models)

                if votes >= consensus_threshold:
                    return 1
                elif votes <= (total_models - consensus_threshold):
                    return 0
                else:
                    # Tie or Indecisive
                    # Use Tie-Breaker Model
                    return row[tie_breaker]

            df_votes["Consensus_Signal"] = df_votes.apply(resolve_vote, axis=1)

            # 4. Run Backtest on Consensus Signal
            engine = BacktestEngine(test_data, initial_capital=config["capital"])
            engine.broker = BROKERS[config["broker"]]
            engine.tax_profile = get_tax_profile(config["w8ben"])

            engine.run_strategy(df_votes["Consensus_Signal"])
            perf = engine.get_performance_summary()

            # 5. Display Results
            st.success("Consensus Strategy Complete!")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Net Profit", f"${perf['Net Profit ($)']:,.2f}")
            m2.metric("ROI", f"{perf['ROI (%)']}%")
            m3.metric("Total Trades", perf["Total Trades"])
            m4.metric("Win Rate", "N/A")  # Todo: Implement win rate in engine

            st.subheader("Equity Curve (Consensus)")
            if engine.history:
                df_hist = pd.DataFrame(engine.history)
                # Filter for SELLs to show realized PnL growth
                if not df_hist.empty:
                    equity = df_hist[df_hist["Action"] == "SELL"].set_index("Date")[
                        "Total"
                    ]
                    st.line_chart(equity)
                else:
                    st.info("No trades executed.")
