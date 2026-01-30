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
    st.header(f"📊 Models Comparison: {ticker}")

    summary = []
    for m_name, res in ticker_res.items():
        if "error" not in res:
            summary.append(
                {
                    "Algorithm": m_name.upper(),
                    "Net ROI": float(res["roi"]),
                    "Win Rate": float(res.get("win_rate", 0)),
                    "Total Trades": res["total_trades"],
                    "Final Capital": float(res["final_capital"]),
                }
            )

    if summary:
        df = pd.DataFrame(summary).sort_values("Net ROI", ascending=False)

        col_table, col_chart = st.columns([1, 1])
        with col_table:
            st.subheader("Leaderboard")
            st.dataframe(
                df,
                column_config={
                    "Net ROI": st.column_config.NumberColumn(format="0.00%"),
                    "Win Rate": st.column_config.NumberColumn(format="0.00%"),
                    "Final Capital": st.column_config.NumberColumn(format="$0,0.00"),
                },
                hide_index=True,
                use_container_width=True,
            )

        with col_chart:
            fig = px.bar(
                df,
                x="Algorithm",
                y="Net ROI",
                color="Net ROI",
                title="Algorithm ROI Performance",
                color_continuous_scale="RdYlGn",
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Individual Model Analysis")
        tabs = st.tabs([m["Algorithm"] for m in summary])
        for i, m_info in enumerate(summary):
            with tabs[i]:
                render_trade_details(ticker_res[m_info["Algorithm"].lower()])
