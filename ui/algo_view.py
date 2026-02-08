"""
USA AI Trading System - Algorithm Comparison View

Purpose: Streamlit view for comparing different AI models on a single stock.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from ui.components import render_trade_details


def render_algorithm_comparison(ticker, ticker_res):
    """Main panel for Mode 1: Comparing AI Algorithms."""
    # Check if ETF
    etf_label = ""
    if "active_builder" in st.session_state:
        if st.session_state["active_builder"].is_etf(ticker):
            etf_label = " 🏷️ (ETF)"

    st.header(f"🤖 Algorithm Benchmark: {ticker}{etf_label}")

    summary = []
    for m_name, res in ticker_res.items():
        # Skip error entries for the summary leaderboard
        if res and isinstance(res, dict) and "roi" in res:
            display_name = str(m_name).replace("_", " ").title()
            summary.append(
                {
                    "Algorithm": display_name,
                    "Model": m_name,  # Hidden unique key
                    "Net ROI": float(res["roi"]),
                    "Win Rate": float(res.get("win_rate", 0)),
                    "Total Trades": int(res["total_trades"]),
                    "Final Portfolio": float(res["final_capital"]),
                }
            )

    if summary:
        df = pd.DataFrame(summary).sort_values("Net ROI", ascending=False)

        # Format the display values
        df_display = df.copy()
        df_display["Net ROI"] = df["Net ROI"].apply(lambda x: f"{x * 100:.2f}%")
        df_display["Win Rate"] = df["Win Rate"].apply(lambda x: f"{x * 100:.2f}%")
        df_display["Final Portfolio"] = df["Final Portfolio"].apply(
            lambda x: f"${x:,.2f}"
        )

        # 1. Leaderboard Table
        st.subheader("🏆 Strategy Leaderboard")
        st.dataframe(
            df_display.drop(columns=["Model"]),
            hide_index=True,
            width="stretch",
        )

        # 2. Comparative Chart
        # Use Model as X to ensure uniqueness in chart if names overlap
        fig = px.bar(
            df,
            x="Model",
            y="Net ROI",
            color="Net ROI",
            title="Algorithm ROI Comparison",
            color_continuous_scale="Viridis",
            labels={"Net ROI": "Net Return on Investment", "Model": "AI Algorithm"},
        )
        # Update X-axis labels to use the display names
        fig.update_layout(
            xaxis=dict(
                tickmode="array", tickvals=df["Model"], ticktext=df["Algorithm"]
            ),
            template="plotly_dark",
        )
        st.plotly_chart(fig, width="stretch")

        # 3. Detailed Tabs
        st.subheader("Model-Specific Deep Dive")
        tab_titles = [m["Algorithm"] for m in summary]
        tabs = st.tabs(tab_titles)
        for i, m_info in enumerate(summary):
            with tabs[i]:
                render_trade_details(ticker, ticker_res[m_info["Model"]])
    else:
        st.warning(
            f"No successful trades generated for {ticker} by any selected model."
        )

        with st.expander("🔍 Why am I seeing this?"):
            st.write("Common reasons:")
            st.write(
                "1. **Data Availability**: The stock might not have enough historical data for the requested backtest period."
            )
            st.write(
                "2. **AI Strategy**: The AI models might not have found any 'BUY' opportunities that passed the hurdle rate filter."
            )
            st.write(
                "3. **Errors**: There might have been an issue fetching data or building the models."
            )

            if ticker_res:
                st.write("---")
                st.write("**Technical Details:**")
                for m, r in ticker_res.items():
                    if isinstance(r, dict) and "error" in r:
                        st.error(f"{m}: {r['error']}")
