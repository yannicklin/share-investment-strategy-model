"""Super Stars (Mode 3) view for the ASX AI Trading System."""

import streamlit as st
import pandas as pd
import plotly.express as px
from ui.components import render_trade_details


def render_super_stars(index_name, all_ticker_res):
    """Main panel for Mode 3: Finding the top 10 stocks in an index."""
    st.header(f"🌟 Hall of Fame: {index_name} Super Stars")
    st.info("Ranking all stocks in the index based on Consensus AI performance.")

    summary = []

    for ticker, res in all_ticker_res.items():
        if res and "error" not in res:
            # Ensure win_rate is present and valid
            win_rate = float(res.get("win_rate", 0.0))

            summary.append(
                {
                    "Ticker": ticker,
                    "Net ROI": float(res["roi"]),
                    "Win Rate": win_rate,
                    "Total Trades": int(res["total_trades"]),
                    "Final Portfolio": float(res["final_capital"]),
                }
            )

    if summary:
        # Sort by ROI and take top 10
        df_all = pd.DataFrame(summary).sort_values("Net ROI", ascending=False)
        df_top10 = df_all.head(10).reset_index(drop=True)

        # 1. Leaderboard Table
        st.subheader("🏆 Top 10 Profit Performers")
        st.dataframe(
            df_top10,
            column_config={
                "Ticker": st.column_config.TextColumn("Stock Symbol"),
                "Net ROI": st.column_config.NumberColumn("ROI", format="0.00%"),
                "Win Rate": st.column_config.NumberColumn("Win Rate", format="0.00%"),
                "Total Trades": st.column_config.NumberColumn("Trades", format="0"),
                "Final Portfolio": st.column_config.NumberColumn(
                    "Final Value", format="$0,0.00"
                ),
            },
            hide_index=True,
            use_container_width=True,
        )

        # 2. Comparative Chart
        fig = px.bar(
            df_top10,
            x="Ticker",
            y="Net ROI",
            color="Net ROI",
            title="Top 10 Stocks by Profitability",
            color_continuous_scale="RdYlGn",
            labels={"Net ROI": "Return on Investment"},
        )

        # Add labels to chart
        fig.update_traces(texttemplate="%{y:.2%}", textposition="outside")
        fig.update_layout(yaxis_tickformat=".2%")
        st.plotly_chart(fig, use_container_width=True)

        # 3. Drill-down for winners
        st.subheader("Detailed Look at Winners")
        # Creating a safe list of labels for tabs
        tab_labels = []
        for _, row in df_top10.iterrows():
            tab_labels.append(f"{row['Ticker']}")

        tabs = st.tabs(tab_labels)
        for i in range(len(tab_labels)):
            with tabs[i]:
                ticker_symbol = tab_labels[i]
                render_trade_details(all_ticker_res[ticker_symbol])

    else:
        st.warning(
            "No valid stock data could be processed for this index. Please ensure the models are trained."
        )
