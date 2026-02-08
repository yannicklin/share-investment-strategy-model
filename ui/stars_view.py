"""
Trading AI System - Super Stars View (USA Edition)

Purpose: Renders the "Find Super Stars" dashboard.
Scans the market (S&P 500, Nasdaq 100) to find Top 10 stocks.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
import pandas as pd
from core.model_builder import ModelBuilder
from core.backtest_engine import BacktestEngine
from core.config import BROKERS, get_tax_profile


def render_stars_view(config):
    """
    Renders the Super Stars Scanner.
    Iterates through index constituents and ranks by ROI.
    """
    st.header(f"🌟 Find Super Stars: {config['index']}")

    st.warning(
        """
        **Note:** Scanning an entire index takes time. 
        For this demo, we will scan the Top 10 holdings of the selected index.
        """
    )

    # Define "Top 10" Proxies for scanning
    # Real implementation would fetch full constituent list.
    index_tickers = {
        "S&P 500": [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "NVDA",
            "META",
            "BRK-B",
            "TSLA",
            "LLY",
            "V",
        ],
        "Nasdaq 100": [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "NVDA",
            "META",
            "TSLA",
            "AVGO",
            "COST",
            "PEP",
        ],
        "Dow Jones 30": [
            "UNH",
            "GS",
            "HD",
            "MSFT",
            "CAT",
            "MCD",
            "V",
            "CRM",
            "BA",
            "HON",
        ],
    }

    tickers_to_scan = index_tickers.get(config["index"], [])

    if st.button("Start Scanner"):
        leaderboard = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, ticker in enumerate(tickers_to_scan):
            status_text.text(f"Scanning {ticker} ({i + 1}/{len(tickers_to_scan)})...")

            # 1. Quick Analysis (Single Model for Speed)
            # Use Random Forest as the "Scout"
            factory = ModelBuilder(
                ticker, "2020-01-01", "2025-01-01"
            )  # Shorter timeframe for speed
            data = factory.fetch_data()

            if data.empty:
                continue

            data = factory.preprocess_data()

            # Train Scout Model
            factory.train_model("Random Forest")

            # Backtest
            if factory.model:
                # Test on last year
                test_data = data.iloc[-252:].copy()  # approx 1 trading year
                X_test = test_data[factory.features]
                X_test_scaled = factory.scaler.transform(X_test)
                signals = factory.model.predict(X_test_scaled)

                engine = BacktestEngine(test_data, initial_capital=config["capital"])
                engine.broker = BROKERS[config["broker"]]
                engine.tax_profile = get_tax_profile(config["w8ben"])

                engine.run_strategy(pd.Series(signals, index=test_data.index))
                perf = engine.get_performance_summary()

                leaderboard.append(
                    {
                        "Ticker": ticker,
                        "Net Profit": perf["Net Profit ($)"],
                        "ROI": perf["ROI (%)"],
                        "Trades": perf["Total Trades"],
                    }
                )

            progress_bar.progress((i + 1) / len(tickers_to_scan))

        status_text.text("Scan Complete!")

        # 2. Display Leaderboard
        if leaderboard:
            df = pd.DataFrame(leaderboard)
            df = df.sort_values(by="ROI", ascending=False).reset_index(drop=True)

            st.subheader("🏆 Top Performers (Last 12 Months)")
            st.dataframe(df.style.highlight_max(axis=0, subset=["ROI", "Net Profit"]))

            # Winner Spotlight
            winner = df.iloc[0]
            st.success(
                f"The Super Star is **{winner['Ticker']}** with {winner['ROI']}% ROI!"
            )
        else:
            st.error("No results found.")
