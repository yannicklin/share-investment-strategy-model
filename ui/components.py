"""
ASX AI Trading System - Shared UI Components

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


def render_trade_details(ticker, res):
    """Shared helper to render equity curves, stats, and logs."""
    if "error" in res:
        st.error(res["error"])
        return

    if res.get("trades"):
        # 1. Equity Curve with Share Price overlay
        trade_points = [
            {
                "date": pd.to_datetime(t["sell_date"]),
                "capital": round(float(t["cumulative_capital"]), 2),
            }
            for t in res["trades"]
        ]
        df_equity = pd.DataFrame(trade_points).sort_values("date")

        # Fetch historical price data for overlay
        price_df = pd.DataFrame()
        if "active_builder" in st.session_state:
            builder = st.session_state["active_builder"]
            # We use the same years as configured in backtest
            price_df = builder.fetch_data(ticker, builder.config.backtest_years)

        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add Capital Path (Primary Y-Axis)
        fig.add_trace(
            go.Scatter(
                x=df_equity["date"],
                y=df_equity["capital"],
                name="Realized Capital",
                line=dict(color="#00CC96", width=3),
                marker=dict(size=8),
                mode="lines+markers",
            ),
            secondary_y=False,
        )

        # Add Share Price (Secondary Y-Axis)
        if not price_df.empty:
            # Filter price data to match the backtest range for cleaner look
            if not df_equity.empty:
                start_date = df_equity["date"].min()
                end_date = df_equity["date"].max()
                price_df = price_df[
                    (price_df.index >= start_date) & (price_df.index <= end_date)
                ]

            fig.add_trace(
                go.Scatter(
                    x=price_df.index,
                    y=price_df["Close"],
                    name=f"{ticker} Price",
                    line=dict(color="rgba(100, 100, 100, 0.3)", width=1, dash="dot"),
                    mode="lines",
                ),
                secondary_y=True,
            )

        # Update layout
        fig.update_layout(
            title=f"Realized Capital vs {ticker} Price Path",
            xaxis_title="Date",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            hovermode="x unified",
            template="plotly_dark",
        )

        fig.update_yaxes(
            title_text="Portfolio Value (AUD)",
            secondary_y=False,
            gridcolor="rgba(255,255,255,0.1)",
        )
        fig.update_yaxes(
            title_text=f"{ticker} Price (AUD)", secondary_y=True, showgrid=False
        )

        st.plotly_chart(fig, use_container_width=True)

        # 2. Statistics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Final Capital", f"${res['final_capital']:,.2f}")
        c2.metric("Total ROI", f"{res['roi']:.2%}")
        c3.metric("Win Rate", f"{res.get('win_rate', 0):.2%}")
        c4.metric("Trades", res["total_trades"])

        # 3. Log
        st.write("#### Detailed Transaction Log")
        log_df = pd.DataFrame(res["trades"])

        # Round and format values in the dataframe for consistency
        if "profit_pct" in log_df.columns:
            log_df["profit_pct"] = log_df["profit_pct"].astype(float)
        if "cumulative_capital" in log_df.columns:
            log_df["cumulative_capital"] = log_df["cumulative_capital"].astype(float)

        # Format dates
        for d_col in ["buy_date", "sell_date"]:
            if d_col in log_df.columns:
                log_df[d_col] = pd.to_datetime(log_df[d_col]).dt.date

        # Format display values
        trades_display = log_df.copy()
        if "buy_price" in trades_display.columns:
            trades_display["buy_price"] = log_df["buy_price"].apply(
                lambda x: f"${x:,.2f}"
            )
        if "sell_price" in trades_display.columns:
            trades_display["sell_price"] = log_df["sell_price"].apply(
                lambda x: f"${x:,.2f}"
            )
        if "fees" in trades_display.columns:
            trades_display["fees"] = log_df["fees"].apply(lambda x: f"${x:,.2f}")
        if "tax" in trades_display.columns:
            trades_display["tax"] = log_df["tax"].apply(lambda x: f"${x:,.2f}")
        if "profit_pct" in trades_display.columns:
            trades_display["profit_pct"] = log_df["profit_pct"].apply(
                lambda x: f"{x * 100:.2f}%"
            )
        if "cumulative_capital" in trades_display.columns:
            trades_display["cumulative_capital"] = log_df["cumulative_capital"].apply(
                lambda x: f"${x:,.2f}"
            )

        st.dataframe(
            trades_display,
            hide_index=True,
            width="stretch",
        )

    else:
        st.warning("No trades executed during this period.")


def render_glossary():
    """Renders the metrics glossary."""
    with st.expander("ℹ️ Understanding the Metrics & Signals"):
        st.markdown("""
        **Metrics:**
        - **Net ROI:** Final return after all fees and ATO taxes.
        - **Win Rate:** Percentage of trades with Gross Profit > 0.
        - **Avg Profit/Trade:** Average net percentage gain per closed position.

        **Tax & Fees:**
        - **ATO Tax:** Marginal CGT based on your annual income (includes 12-month 50% discount).
        - **CMC Profile:** Greater of $11 or 0.10% flat brokerage.
        """)
