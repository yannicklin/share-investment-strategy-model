"""Streamlit UI for the AI-Based Stock Investment System."""

import streamlit as st
import pandas as pd
import plotly.express as px
from config import load_config
from buildmodel import ModelBuilder
from backtest import BacktestEngine


def run_ui():
    """Renders the Streamlit dashboard."""
    st.set_page_config(page_title="ASX AI Trading System", layout="wide")
    st.title("📈 ASX AI Trading Strategy Dashboard")

    # Sidebar - Configuration
    st.sidebar.header("Configuration")
    config = load_config()

    ticker_input = st.sidebar.text_input(
        "Target Tickers (semicolon separated)", "BHP.AX;CBA.AX"
    )
    config.target_stock_codes = [t.strip() for t in ticker_input.split(";")]

    config.backtest_years = st.sidebar.slider("Backtest Years", 1, 10, 5)
    config.init_capital = st.sidebar.number_input("Initial Capital", value=100000.0)
    config.stop_loss_threshold = st.sidebar.slider(
        "Stop-Loss Threshold", 0.01, 0.50, 0.10
    )
    config.stop_profit_threshold = st.sidebar.slider(
        "Take-Profit Threshold", 0.01, 1.0, 0.20
    )

    col_unit, col_val = st.sidebar.columns([2, 1])
    config.hold_period_unit = col_unit.selectbox(
        "Min Hold Unit", ["day", "month", "quarter", "year"], index=1
    )
    config.hold_period_value = col_val.number_input("Val", value=1, min_value=1)

    config.model_types = st.sidebar.multiselect(
        "AI Algorithms to Compare",
        [
            "random_forest",
            "xgboost",
            "lightgbm",
            "catboost",
            "elastic_net",
            "svr",
            "prophet",
        ],
        default=["random_forest"],
    )

    with st.sidebar.expander("Costs & Taxes"):
        config.brokerage_rate = (
            st.number_input("Brokerage (%)", value=0.12, step=0.01) / 100
        )
        config.clearing_rate = (
            st.number_input("Clearing (%)", value=0.00225, step=0.0001, format="%.5f")
            / 100
        )
        config.settlement_fee = st.number_input("Settlement ($)", value=1.5)
        config.tax_rate = st.number_input("Tax Rate (%)", value=25.0) / 100

    config.rebuild_model = st.sidebar.checkbox("Rebuild AI Model", value=True)

    if st.sidebar.button("🗑️ Clear Cache"):
        for key in ["results", "suggestions"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    if st.sidebar.button("💡 Generate Live Suggestions"):
        suggestions = []
        for ticker in config.target_stock_codes:
            consensus_votes = 0
            total_expected_return = 0.0

            # Use all selected models to reach consensus
            builder = ModelBuilder(config)
            latest_features = builder.get_latest_features(ticker)

            if latest_features is not None:
                current_price = latest_features[3]  # Index of 'Close'
                for m_type in config.model_types:
                    config.model_type = m_type
                    builder.load_or_build(ticker)
                    predicted_price = builder.predict(
                        latest_features, date=pd.Timestamp.now()
                    )
                    expected_return = (predicted_price - current_price) / current_price

                    if expected_return > 0:
                        consensus_votes += 1
                    total_expected_return += expected_return

                avg_return = total_expected_return / len(config.model_types)
                suggestions.append(
                    {
                        "Ticker": ticker,
                        "Current Price": f"${current_price:.2f}",
                        "Expected Return": f"{avg_return:.2%}",
                        "Consensus": f"{consensus_votes}/{len(config.model_types)} Models",
                        "Signal": "🟢 BUY"
                        if consensus_votes > len(config.model_types) / 2
                        else "🟡 WAIT/HOLD",
                    }
                )
        st.session_state["suggestions"] = suggestions

    if "suggestions" in st.session_state:
        st.header("🚀 AI Daily Recommendations")
        suggest_df = pd.DataFrame(st.session_state["suggestions"])
        st.table(suggest_df)
        st.info(
            "Signals are based on the latest available market close and your trained models."
        )

    if st.sidebar.button("🚀 Run Comparison Backtest"):
        all_results = {}
        for ticker in config.target_stock_codes:
            ticker_results = {}
            for model_type in config.model_types:
                with st.spinner(f"Processing {ticker} with {model_type}..."):
                    config.model_type = model_type  # Temporarily set for the builder
                    builder = ModelBuilder(config)
                    engine = BacktestEngine(config, builder)
                    builder.load_or_build(ticker)
                    res = engine.run(ticker)
                    ticker_results[model_type] = res
            all_results[ticker] = ticker_results
        st.session_state["results"] = all_results

    if "results" in st.session_state:
        results = st.session_state["results"]

        # Glossary / Help Section
        with st.expander("ℹ️ Understanding the Metrics & Signals"):
            st.markdown("""
            **Metrics:**
            - **ROI (Return on Investment):** The total percentage gain or loss on your initial capital after all fees and taxes.
            - **Win Rate:** The percentage of closed trades that were profitable. 
              *Calculation: (Profitable Trades / Total Trades) * 100*
            - **Profit % (Trade Level):** The net percentage change (after fees and taxes) between the buy and sell points.

            **Costs & Taxes:**
            - **Fees:** Total transaction costs (Brokerage + Clearing + Settlement) for both entry and exit.
            - **Tax (ATO):** Capital Gains Tax calculated on net profit. 
              *Note: Includes 50% discount for holdings >= 12 months.*
            - **stop-loss:** Automated safety exit because the stock price dropped below your risk threshold.
            - **take-profit:** Exit because the stock reached your desired profit target.
            - **model-exit:** The AI predicted a downward price trend for the next day, signaling it's time to sell.
            - **max-hold:** Exit triggered because the minimum holding period (month/quarter/year) was reached.
            """)

        for ticker, model_res in results.items():
            st.header(f"📊 Analysis: {ticker}")

            # Comparison Summary View
            summary_data = []
            for m_type, res in model_res.items():
                if "error" not in res:
                    summary_data.append(
                        {
                            "Algorithm": m_type,
                            "ROI": f"{res['roi']:.2%}",
                            "ROI_val": res["roi"],
                            "Win Rate": f"{res['win_rate']:.2%}",
                            "Trades": res["total_trades"],
                            "Final Capital": f"${res['final_capital']:,.2f}",
                        }
                    )

            if summary_data:
                # 1. Comparison Metrics Table
                summary_df = pd.DataFrame(summary_data)
                st.table(
                    summary_df[
                        ["Algorithm", "ROI", "Win Rate", "Trades", "Final Capital"]
                    ]
                )

                # 2. Capital Growth Over Time (Multi-Line Chart with Trade Dots)
                st.subheader(f"Capital Growth Comparison - {ticker}")

                # Combine equity history from all models
                combined_equity = []
                combined_trades = []

                for m_type, res in model_res.items():
                    if "error" not in res and "equity_history" in res:
                        # Add equity line data
                        hist_df = pd.DataFrame(res["equity_history"])
                        hist_df["Algorithm"] = m_type
                        combined_equity.append(hist_df)

                        # Add trade dot data
                        if res.get("trades"):
                            t_df = pd.DataFrame(res["trades"])
                            trade_dots = []
                            for _, t in t_df.iterrows():
                                # Safe access to equity_history
                                history = res.get("equity_history", [])
                                capital_at_date = next(
                                    (
                                        e["capital"]
                                        for e in reversed(history)
                                        if e["date"] <= t["sell_date"]
                                    ),
                                    config.init_capital,
                                )
                                trade_dots.append(
                                    {
                                        "date": t["sell_date"],
                                        "capital": capital_at_date,
                                        "Algorithm": m_type,
                                    }
                                )
                            if trade_dots:
                                combined_trades.append(pd.DataFrame(trade_dots))

                if combined_equity:
                    equity_df = pd.concat(combined_equity)

                    # Create the line chart
                    fig_growth = px.line(
                        equity_df,
                        x="date",
                        y="capital",
                        color="Algorithm",
                        title=f"Net Portfolio Value Over Time ({ticker})",
                        labels={"capital": "Total Capital (AUD)", "date": "Date"},
                    )

                    # Add trade dots if they exist
                    if combined_trades:
                        trades_dots_df = pd.concat(combined_trades)
                        fig_growth.add_scatter(
                            x=trades_dots_df["date"],
                            y=trades_dots_df["capital"],
                            mode="markers",
                            marker=dict(size=8, symbol="circle"),
                            name="Trades",
                            showlegend=True,
                            hoverinfo="skip",  # Lines already show the data
                        )

                    st.plotly_chart(fig_growth, use_container_width=True)

                # 3. ROI Comparison Bar Chart
                fig_roi = px.bar(
                    summary_df,
                    x="Algorithm",
                    y="ROI_val",
                    title=f"Final ROI Comparison - {ticker}",
                    labels={"ROI_val": "Return on Investment"},
                )
                st.plotly_chart(fig_roi)

                # Detail View with Tabs
                st.subheader("Detailed Performance")
                tabs = st.tabs([m.upper() for m in model_res.keys()])
                for i, (m_type, res) in enumerate(model_res.items()):
                    with tabs[i]:
                        if "error" in res:
                            st.error(res["error"])
                            continue

                        col1, col2, col3 = st.columns(3)
                        col1.metric(
                            "ROI",
                            f"{res['roi']:.2%}",
                            help="Total return on initial capital.",
                        )
                        col2.metric(
                            "Win Rate",
                            f"{res['win_rate']:.2%}",
                            help="Percentage of profitable trades.",
                        )
                        col3.metric(
                            "Trades",
                            res["total_trades"],
                            help="Number of completed transactions.",
                        )

                        if res["trades"]:
                            trades_df = pd.DataFrame(res["trades"])
                            st.write("#### Transaction Log")
                            # Format financial columns
                            format_cols = {
                                "fees": "{:.2f}",
                                "tax": "{:.2f}",
                                "profit_loss": "{:.2f}",
                                "profit_pct": "{:.2%}",
                            }
                            st.dataframe(trades_df.style.format(format_cols))

                            fig_detail = px.line(
                                trades_df,
                                x="sell_date",
                                y="profit_pct",
                                title=f"Profit % Trend - {m_type}",
                            )
                            st.plotly_chart(fig_detail)
            else:
                st.warning(f"No valid results for {ticker}")


if __name__ == "__main__":
    run_ui()
