"""
ASX AI Trading System - Super Stars View

Purpose: Streamlit view for ranking and displaying top-performing stocks
within ASX indices.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from ui.components import render_trade_details


def render_super_stars(index_name, all_ticker_res, models=None, tie_breaker=None):
    """Main panel for Mode 3: Finding the top 10 stocks in an index."""
    st.header(f"🌟 Hall of Fame: {index_name} Super Stars")

    # Dynamic Decision Engine Description
    if models and len(models) > 1:
        m_count = len(models)
        if m_count % 2 == 0:
            # Even number of models requires a tie-breaker
            tb_name = tie_breaker.upper() if tie_breaker else models[0].upper()
            st.info(
                f"Ranking stocks based on Consensus ({m_count} models) with Tie-Breaker: {tb_name}"
            )
        else:
            # Odd number of models has a natural majority
            st.info(
                f"Ranking stocks based on Consensus (Majority Vote of {m_count} models)"
            )
    elif models and len(models) == 1:
        st.info(f"Ranking stocks based on Single Model ({models[0].upper()})")
    else:
        st.info("Ranking all stocks in the index based on Consensus AI performance.")

    summary = []
    errors = []

    for ticker, res in all_ticker_res.items():
        if res and "error" not in res:
            # Ensure win_rate is present and valid
            win_rate = float(res.get("win_rate", 0.0))
            company_name = res.get("company_name", ticker)
            yfinance_url = f"https://finance.yahoo.com/quote/{ticker}"

            summary.append(
                {
                    "Ticker": ticker,
                    "Company": company_name,
                    "Net ROI": float(res["roi"]),
                    "Win Rate": win_rate,
                    "Total Trades": int(res["total_trades"]),
                    "Final Portfolio": float(res["final_capital"]),
                    "Link": yfinance_url,
                }
            )
        elif res and "error" in res:
            errors.append({"Ticker": ticker, "Error": res["error"]})

    if summary:
        # Sort by ROI and take top 10
        df_all = pd.DataFrame(summary).sort_values("Net ROI", ascending=False)
        df_top10 = df_all.head(10).reset_index(drop=True)

        # Format the display values
        df_display = df_top10.copy()
        df_display["Net ROI"] = df_top10["Net ROI"].apply(lambda x: f"{x * 100:.2f}%")
        df_display["Win Rate"] = df_top10["Win Rate"].apply(lambda x: f"{x * 100:.2f}%")
        df_display["Final Portfolio"] = df_top10["Final Portfolio"].apply(
            lambda x: f"${x:,.2f}"
        )

        # 1. Leaderboard Table
        st.subheader("🏆 Top 10 Profit Performers")
        st.dataframe(
            df_display,
            column_config={
                "Link": st.column_config.LinkColumn(
                    "Yahoo Finance",
                    help="View ticker details on Yahoo Finance",
                    validate="^https://finance\.yahoo\.com/quote/.*",
                    display_text="View Page",
                ),
            },
            hide_index=True,
            width="stretch",
        )

        # 2. Comparative Chart
        fig = px.bar(
            df_top10,
            x="Ticker",
            y="Net ROI",
            hover_data=["Company"],
            color="Net ROI",
            title="Top 10 Stocks by Profitability",
            color_continuous_scale="RdYlGn",
            labels={"Net ROI": "Return on Investment"},
        )

        # Add labels to chart
        fig.update_traces(texttemplate="%{y:.2%}", textposition="outside")
        fig.update_layout(yaxis_tickformat=".2%")
        st.plotly_chart(fig, width="stretch")

        # 3. Drill-down for winners
        st.subheader("Detailed Look at Winners")
        # Creating a safe list of labels for tabs
        tab_labels = [row["Ticker"] for _, row in df_top10.iterrows()]

        tabs = st.tabs(tab_labels)
        for i in range(len(tab_labels)):
            with tabs[i]:
                ticker_symbol = tab_labels[i]
                render_trade_details(ticker_symbol, all_ticker_res[ticker_symbol])

    # Show errors in an expander at the bottom
    if errors:
        st.markdown("---")
        with st.expander(f"⚠️ View Processing Issues ({len(errors)} stocks failed)"):
            err_df = pd.DataFrame(errors)
            st.table(err_df)

    if not summary and not errors:
        st.warning(
            "No valid stock data could be processed for this index. Please ensure the models are trained."
        )
