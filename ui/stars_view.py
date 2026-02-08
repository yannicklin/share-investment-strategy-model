"""
USA AI Trading System - Super Stars View

Purpose: Renders the "Find Super Stars" dashboard.
Ranks stocks within an index by AI-driven ROI.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
import pandas as pd
import plotly.express as px


def render_super_stars(index_name, all_ticker_res, models=None, tie_breaker=None):
    """Main panel for Super Stars Mode: Index Leaderboard."""
    st.header(f"🌟 Find Super Stars: {index_name}")

    leaderboard = []
    for ticker, res in all_ticker_res.items():
        if isinstance(res, dict) and "roi" in res:
            leaderboard.append(
                {
                    "Ticker": ticker,
                    "Company": res.get("company_name", ticker),
                    "Net ROI": float(res["roi"]),
                    "Win Rate": float(res.get("win_rate", 0)),
                    "Total Trades": res["total_trades"],
                    "Final Capital": float(res["final_capital"]),
                }
            )

    if leaderboard:
        df = (
            pd.DataFrame(leaderboard)
            .sort_values("Net ROI", ascending=False)
            .reset_index(drop=True)
        )

        winner = df.iloc[0]
        st.success(
            f"🏆 **Winner:** {winner['Company']} ({winner['Ticker']}) with **{winner['Net ROI'] * 100:.2f}% ROI**"
        )

        df_display = df.copy()
        df_display["Net ROI"] = df["Net ROI"].apply(lambda x: f"{x * 100:.2f}%")
        df_display["Win Rate"] = df["Win Rate"].apply(lambda x: f"{x * 100:.2f}%")
        df_display["Final Capital"] = df["Final Capital"].apply(lambda x: f"${x:,.2f}")

        st.subheader("Leaderboard")
        st.dataframe(df_display, hide_index=True, use_container_width=True)

        fig = px.bar(
            df.head(10),
            x="Ticker",
            y="Net ROI",
            color="Net ROI",
            title="Top 10 Performance",
            color_continuous_scale="RdYlGn",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No successful results found to rank.")
