"""
ASX AI Trading System - Algorithm Comparison View

Purpose: Streamlit view for comparing AI model performance metrics
and visualizations.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from ui.components import render_trade_details


def render_algorithm_comparison(ticker, ticker_res):
    """Main panel for Model Mode: Comparing AI IQ."""
    # Check if ETF
    etf_label = ""
    if "active_builder" in st.session_state:
        if st.session_state["active_builder"].is_etf(ticker):
            etf_label = " 🏷️ (ETF)"

    # Fetch long name
    company_name = ""
    if "active_builder" in st.session_state:
        company_name = (
            f"({st.session_state['active_builder'].get_company_name(ticker)})"
        )

    st.header(f"📊 Models Comparison: {ticker}{company_name}{etf_label}")

    summary = []
    for m_name, res in ticker_res.items():
        # Skip error entries for the summary leaderboard
        if isinstance(res, dict) and "error" not in res:
            display_name = m_name
            summary.append(
                {
                    "Algorithm": display_name,
                    "Model": m_name,  # Hidden unique key
                    "Net ROI": float(res["roi"]),
                    "Win Rate": float(res.get("win_rate", 0)),
                    "Total Trades": res["total_trades"],
                    "Final Capital": float(res["final_capital"]),
                }
            )

    if summary:
        df = pd.DataFrame(summary).sort_values("Net ROI", ascending=False)

        # Format the display values
        df_display = df.copy()
        df_display["Net ROI"] = df["Net ROI"].apply(lambda x: f"{x * 100:.2f}%")
        df_display["Win Rate"] = df["Win Rate"].apply(lambda x: f"{x * 100:.2f}%")
        df_display["Final Capital"] = df["Final Capital"].apply(lambda x: f"${x:,.2f}")

        col_table, col_chart = st.columns([1, 1])
        with col_table:
            st.subheader("Leaderboard")
            st.dataframe(
                df_display.drop(columns=["Model"]),
                hide_index=True,
                width="stretch",
            )

        with col_chart:
            # Use Model as X to ensure uniqueness in chart if names overlap
            fig = px.bar(
                df,
                x="Model",
                y="Net ROI",
                color="Net ROI",
                title="Algorithm ROI Performance",
                color_continuous_scale="RdYlGn",
                labels={"Model": "Algorithm Type"},
            )
            # Update X-axis labels to use the display names
            fig.update_layout(
                xaxis=dict(
                    tickmode="array", tickvals=df["Model"], ticktext=df["Algorithm"]
                )
            )
            st.plotly_chart(fig, width="stretch")

        st.subheader("Individual Model Analysis")
        # Use only the internal model name for tabs as requested
        tabs = st.tabs([m["Model"] for m in summary])
        for i, m_info in enumerate(summary):
            with tabs[i]:
                render_trade_details(ticker, ticker_res[m_info["Model"]])
    else:
        st.warning(f"⚠️ No valid trades or model results for {ticker}.")
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
