"""
USA AI Trading System - Algorithm Comparison View

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
    etf_label = ""
    if "active_builder" in st.session_state:
        if st.session_state["active_builder"].is_etf(ticker):
            etf_label = " 🏷️ (ETF)"

    st.header(f"📊 Models Comparison: {ticker}{etf_label}")

    summary = []
    for m_name, res in ticker_res.items():
        if isinstance(res, dict) and "error" not in res:
            summary.append(
                {
                    "Algorithm": m_name,
                    "Model": m_name,
                    "Net ROI": float(res["roi"]),
                    "Win Rate": float(res.get("win_rate", 0)),
                    "Total Trades": res["total_trades"],
                    "Final Capital": float(res["final_capital"]),
                }
            )

    if summary:
        df = pd.DataFrame(summary).sort_values("Net ROI", ascending=False)
        df_display = df.copy()
        df_display["Net ROI"] = df["Net ROI"].apply(lambda x: f"{x * 100:.2f}%")
        df_display["Win Rate"] = df["Win Rate"].apply(lambda x: f"{x * 100:.2f}%")
        df_display["Final Capital"] = df["Final Capital"].apply(lambda x: f"${x:,.2f}")

        col_table, col_chart = st.columns([1, 1])
        with col_table:
            st.subheader("Leaderboard")
            st.dataframe(
                df_display.drop(columns=["Model"]), hide_index=True, width="stretch"
            )

        with col_chart:
            fig = px.bar(
                df,
                x="Model",
                y="Net ROI",
                color="Net ROI",
                title="Algorithm ROI Performance",
                color_continuous_scale="RdYlGn",
                labels={"Model": "Algorithm Type"},
            )
            st.plotly_chart(fig, width="stretch")

        st.subheader("Individual Model Analysis")
        tabs = st.tabs([m["Model"] for m in summary])
        for i, m_info in enumerate(summary):
            with tabs[i]:
                render_trade_details(ticker, ticker_res[m_info["Model"]])
    else:
        st.warning(f"⚠️ No valid trades or model results for {ticker}.")
