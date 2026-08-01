"""
Taiwan Stock AI Trading System - Super Stars View

Purpose: Streamlit view for ranking and displaying top-performing stocks
within Taiwan Stock indices.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from ui.components import render_trade_details


def _categorize_error(message: str) -> str:
    """Categorize error messages for cleaner display."""
    message = (message or "").lower()
    if "no data" in message or "empty" in message:
        return "No Data"
    if "insufficient" in message or "not enough" in message:
        return "Thin Data"
    if "model" in message or "train" in message:
        return "Model Error"
    if "keyerror" in message or "column" in message:
        return "Feature Error"
    return "Processing Error"


def render_super_stars(
    index_name,
    all_ticker_res,
    models=None,
    tie_breaker=None,
    builder=None,
):
    """Main panel for Mode 3: Finding the top 10 stocks in an index."""
    st.header(f"🌟 Hall of Fame: {index_name} Super Stars")

    # Dynamic Decision Engine Description
    if models and len(models) > 1:
        m_count = len(models)
        if m_count % 2 == 0:
            # Even number of models requires a tie-breaker
            tb_name = tie_breaker if tie_breaker else models[0]
            st.info(
                f"Ranking stocks based on Consensus ({m_count} models) with Tie-Breaker: {tb_name}"
            )
        else:
            # Odd number of models has a natural majority
            st.info(
                f"Ranking stocks based on Consensus (Majority Vote of {m_count} models)"
            )
    elif models and len(models) == 1:
        st.info(f"Ranking stocks based on Single Model ({models[0]})")
    else:
        st.info("Ranking all stocks in the index based on Consensus AI performance.")

    summary = []
    errors = []

    for ticker, res in all_ticker_res.items():
        if res and "error" not in res:
            # Extract metadata (prefer _metadata structure, fall back to top-level)
            metadata = res.get("_metadata", {})
            chinese_name = metadata.get("chinese_name", "") or res.get(
                "chinese_name", ""
            )
            company_name = metadata.get("company_name", "") or res.get(
                "company_name", ticker
            )

            # Ensure win_rate is present and valid
            win_rate = float(res.get("win_rate", 0.0))
            yfinance_url = f"https://finance.yahoo.com/quote/{ticker}"

            summary.append(
                {
                    "Ticker": ticker,
                    "Name": f"{chinese_name} ({company_name})"
                    if chinese_name
                    else company_name,
                    "Net ROI": float(res["roi"]),
                    "Win Rate": win_rate,
                    "Total Trades": int(res["total_trades"]),
                    "Final Portfolio": float(res["final_capital"]),
                    "Link": yfinance_url,
                }
            )
        elif res and "error" in res:
            errors.append(
                {
                    "Ticker": ticker,
                    "Issue": _categorize_error(res["error"]),
                    "Error": res["error"],
                }
            )

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

        if builder is not None:
            for row_idx, ticker in enumerate(df_top10["Ticker"]):
                try:
                    # Fetch Traditional Chinese name from FinMind for Taiwan stocks
                    chinese_name = (
                        builder.get_chinese_name(ticker)
                        if ticker.endswith(".TW")
                        else ""
                    )
                    company_name = builder.get_company_name(ticker)
                    # Display Chinese name primarily, English as fallback
                    display_name = chinese_name if chinese_name else company_name
                    df_display.at[row_idx, "Name"] = display_name
                except Exception:
                    pass

        # 1. Leaderboard Table
        st.subheader("🏆 Top 10 Profit Performers")
        st.dataframe(
            df_display,
            column_config={
                "Link": st.column_config.LinkColumn(
                    "Yahoo Finance",
                    help="View ticker details on Yahoo Finance",
                    validate=r"^https://finance\.yahoo\.com/quote/.*",
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
            hover_data=["Name"],
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
        # Build tab labels with stock IDs and store metadata
        tab_labels = []
        ticker_metadata = {}

        for ticker in df_top10["Ticker"]:
            ticker_str = str(ticker)
            # Extract stock ID (remove market suffix like .TW, .AX, etc.)
            stock_id = ticker_str.split(".")[0] if "." in ticker_str else ticker_str
            tab_labels.append(stock_id)

            # Store metadata for each ticker
            res = all_ticker_res[ticker_str]
            metadata = res.get("_metadata", {})
            chinese_name = metadata.get("chinese_name", "") or res.get(
                "chinese_name", ""
            )
            company_name = metadata.get("company_name", "") or res.get(
                "company_name", ""
            )

            ticker_metadata[stock_id] = {
                "ticker": ticker_str,
                "chinese_name": chinese_name,
                "company_name": company_name,
            }

        tabs = st.tabs(tab_labels)
        for i, stock_id in enumerate(tab_labels):
            with tabs[i]:
                ticker_symbol = ticker_metadata[stock_id]["ticker"]
                chinese_name = ticker_metadata[stock_id]["chinese_name"]
                company_name = ticker_metadata[stock_id]["company_name"]

                # Display Chinese name as heading if available
                if chinese_name:
                    st.subheader(f"{chinese_name}")
                elif company_name:
                    st.subheader(f"{company_name}")

                res = all_ticker_res[ticker_symbol]
                render_trade_details(ticker_symbol, res)

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
