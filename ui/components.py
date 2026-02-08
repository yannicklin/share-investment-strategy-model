"""
USA AI Trading System - Shared UI Components

Purpose: Reusable Streamlit components for equity curves, trade logs,
and glossary displays.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core.utils import format_date_with_weekday


def render_trade_details(ticker, res):
    """Shared helper to render equity curves, stats, and logs."""
    if "error" in res:
        st.error(res["error"])
        return

    if res.get("trades"):
        # 1. Equity Curve
        trade_points = [
            {
                "date": pd.to_datetime(t["sell_date"]),
                "capital": round(float(t["cumulative_capital"]), 2),
            }
            for t in res["trades"]
        ]
        df_equity = pd.DataFrame(trade_points).sort_values("date")

        # Price overlay
        price_df = pd.DataFrame()
        if "active_builder" in st.session_state:
            builder = st.session_state["active_builder"]
            price_df = builder.fetch_data(ticker, builder.config.backtest_years)

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(
                x=df_equity["date"],
                y=df_equity["capital"],
                name="Realized Capital",
                line=dict(color="#00CC96", width=3),
            ),
            secondary_y=False,
        )

        if not price_df.empty:
            start_date = df_equity["date"].min()
            price_df = price_df[price_df.index >= start_date]
            fig.add_trace(
                go.Scatter(
                    x=price_df.index,
                    y=price_df["Close"],
                    name=f"{ticker} Price Trend",
                    line=dict(color="rgba(173, 216, 230, 0.6)", width=2, dash="dot"),
                ),
                secondary_y=True,
            )

        fig.update_layout(
            title=f"Realized Capital vs {ticker} Price Path",
            hovermode="x unified",
            template="plotly_dark",
        )
        fig.update_yaxes(title_text="Portfolio Value (USD)", secondary_y=False)
        fig.update_yaxes(
            title_text=f"{ticker} Price (USD)", secondary_y=True, showgrid=False
        )
        st.plotly_chart(fig, width="stretch")

        # 2. Statistics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Final Capital", f"${res['final_capital']:,.2f}")
        c2.metric("Total ROI", f"{res['roi']:.2%}")
        c3.metric("Win Rate", f"{res.get('win_rate', 0):.2%}")
        c4.metric("Trades", res["total_trades"])

        # 3. Log
        st.write("#### Detailed Transaction Log")
        log_df = pd.DataFrame(res["trades"])
        for d_col in ["buy_date", "sell_date"]:
            if d_col in log_df.columns:
                log_df[d_col] = pd.to_datetime(log_df[d_col]).apply(
                    lambda x: format_date_with_weekday(x)
                )

        trades_display = log_df.copy()
        for col in ["buy_price", "sell_price", "fees", "tax", "cumulative_capital"]:
            if col in trades_display.columns:
                trades_display[col] = log_df[col].apply(lambda x: f"${x:,.2f}")
        if "profit_pct" in trades_display.columns:
            trades_display["profit_pct"] = log_df["profit_pct"].apply(
                lambda x: f"{x * 100:.2f}%"
            )

        st.dataframe(trades_display, hide_index=True, width="stretch")
    else:
        st.warning("No trades executed during this period.")


def render_glossary():
    """Renders the metrics glossary."""
    with st.expander("ℹ️ Understanding the Metrics & Signals"):
        st.markdown("""
        **Metrics:**
        - **Net ROI:** Final return after all fees and W-8BEN tax adjustments.
        - **Win Rate:** Percentage of trades with Gross Profit > 0.
        - **Avg Profit/Trade:** Average net percentage gain per closed position.

        **Tax & Fees:**
        - **W-8BEN:** Treaty-aware tax logic (0% CGT for many non-US residents).
        - **SEC/FINRA:** Regulatory fees applied to sell orders.
        """)
