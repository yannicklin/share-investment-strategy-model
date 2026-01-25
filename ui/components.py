"""Shared UI components for the ASX AI Trading System."""

import streamlit as st
import pandas as pd
import plotly.express as px


def render_trade_details(res):
    """Shared helper to render equity curves, stats, and logs."""
    if "error" in res:
        st.error(res["error"])
        return

    if res.get("trades"):
        # 1. Equity Curve
        trade_points = [
            {
                "date": pd.to_datetime(t["sell_date"]).date(),
                "capital": t["cumulative_capital"],
            }
            for t in res["trades"]
        ]
        df_equity = pd.DataFrame(trade_points)
        fig_curve = px.line(
            df_equity,
            x="date",
            y="capital",
            markers=True,
            title="Realized Capital Path",
            labels={"capital": "Portfolio Value (AUD)", "date": "Exit Date"},
        )
        st.plotly_chart(fig_curve, use_container_width=True)

        # 2. Statistics
        c1, c2, c3 = st.columns(3)
        c1.metric("Final Capital", f"${res['final_capital']:,.2f}")
        c2.metric("Total ROI", f"{res['roi']:.2%}")
        c3.metric("Trades", res["total_trades"])

        # 3. Log
        st.write("#### Detailed Transaction Log")
        log_df = pd.DataFrame(res["trades"])
        # Format dates
        for d_col in ["buy_date", "sell_date"]:
            if d_col in log_df.columns:
                log_df[d_col] = pd.to_datetime(log_df[d_col]).dt.date

        st.dataframe(
            log_df,
            column_config={
                "buy_price": st.column_config.NumberColumn("Buy", format="$%.2f"),
                "sell_price": st.column_config.NumberColumn("Sell", format="$%.2f"),
                "fees": st.column_config.NumberColumn("Fees", format="$%.2f"),
                "tax": st.column_config.NumberColumn("Tax", format="$%.2f"),
                "profit_pct": st.column_config.NumberColumn("P/L %", format="%.2%"),
                "cumulative_capital": st.column_config.NumberColumn(
                    "Portfolio", format="$%.2f"
                ),
                "duration": "Days",
                "reason": "Exit Reason",
            },
            hide_index=True,
            use_container_width=True,
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
