"""
USA AI Trading System - Strategy View

Purpose: Renders the "Time-Span Comparison" dashboard.
Implements ROI comparison across different holding periods.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from ui.components import render_trade_details


def render_strategy_sensitivity(ticker, ticker_res, models=None, tie_breaker=None):
    """Main panel for Strategy Mode: Comparing time horizons."""
    st.header(f"⏳ Strategy Sensitivity: {ticker}")

    summary = []
    for p_name, res in ticker_res.items():
        if isinstance(res, dict) and "error" not in res:
            summary.append(
                {
                    "Period": p_name,
                    "Net ROI": float(res["roi"]),
                    "Win Rate": float(res.get("win_rate", 0)),
                    "Total Trades": res["total_trades"],
                    "Final Capital": float(res["final_capital"]),
                }
            )

    if summary:
        df = pd.DataFrame(summary)
        df_display = df.copy()
        df_display["Net ROI"] = df["Net ROI"].apply(lambda x: f"{x * 100:.2f}%")
        df_display["Win Rate"] = df["Win Rate"].apply(lambda x: f"{x * 100:.2f}%")
        df_display["Final Capital"] = df["Final Capital"].apply(lambda x: f"${x:,.2f}")

        col_t, col_c = st.columns([1, 1])
        with col_t:
            st.subheader("Leaderboard")
            st.dataframe(df_display, hide_index=True, width="stretch")

        with col_c:
            fig = px.line(
                df, x="Period", y="Net ROI", markers=True, title="ROI by Holding Period"
            )
            st.plotly_chart(fig, width="stretch")

        st.subheader("Period Details")
        tabs = st.tabs([s["Period"] for s in summary])
        for i, s_info in enumerate(summary):
            with tabs[i]:
                render_trade_details(ticker, ticker_res[s_info["Period"]])
    else:
        st.warning("No valid results to display.")
