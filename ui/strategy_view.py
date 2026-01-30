"""
ASX AI Trading System - Strategy Sensitivity View

Purpose: Streamlit view for comparing trading strategies across different
holding periods using consensus AI predictions.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from ui.components import render_trade_details


def render_strategy_sensitivity(ticker, ticker_res):
    """Main panel for Strategy Mode: Comparing Holding Times."""
    st.header(f"⏳ Time-Span Comparison: {ticker}")
    st.info("Decision Engine: Consensus (Majority Vote) of selected AI models.")

    summary = []
    errors = []

    for p_name, res in ticker_res.items():
        if res and "error" not in res:
            summary.append(
                {
                    "Hold Period": p_name,
                    "Net ROI": float(res["roi"]),
                    "Win Rate": float(res.get("win_rate", 0)),
                    "Total Trades": res["total_trades"],
                    "Final Portfolio": float(res["final_capital"]),
                }
            )
        elif res and "error" in res:
            errors.append(f"{p_name}: {res['error']}")

    if errors:
        for err in errors:
            st.warning(err)

    if summary:
        df = pd.DataFrame(summary)

        # 1. ROI Comparison Chart
        fig = px.bar(
            df,
            x="Hold Period",
            y="Net ROI",
            color="Net ROI",
            title="ROI Performance by Holding Period",
            color_continuous_scale="Viridis",
            labels={"Net ROI": "Net Return on Investment"},
        )
        st.plotly_chart(fig, use_container_width=True)

        # 2. Metrics Table
        st.subheader("Efficiency Metrics")
        st.dataframe(
            df,
            column_config={
                "Net ROI": st.column_config.NumberColumn("ROI", format=".2%"),
                "Win Rate": st.column_config.NumberColumn("Win Rate", format=".2%"),
                "Final Portfolio": st.column_config.NumberColumn(
                    "Final Value", format="$,.2f"
                ),
                "Total Trades": "Trades",
            },
            hide_index=True,
            use_container_width=True,
        )

        # 3. Detailed Tabs
        st.subheader("Period-Specific Deep Dive")
        tab_titles = [p["Hold Period"] for p in summary]
        tabs = st.tabs(tab_titles)
        for i, p_info in enumerate(summary):
            with tabs[i]:
                render_trade_details(ticker_res[p_info["Hold Period"]])
    else:
        if not errors:
            st.error(
                f"No summary data could be generated for {ticker}. Check your model selections."
            )
