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
        "Target Tickers (semicolon separated)", ";".join(config.target_stock_codes)
    )
    config.target_stock_codes = [t.strip() for t in ticker_input.split(";")]

    config.backtest_years = st.sidebar.slider(
        "Backtest Years", 1, 10, config.backtest_years
    )
    config.init_capital = st.sidebar.number_input(
        "Initial Capital", value=config.init_capital
    )
    config.stop_loss_threshold = st.sidebar.slider(
        "Stop-Loss Threshold", 0.01, 0.50, config.stop_loss_threshold
    )
    config.stop_profit_threshold = st.sidebar.slider(
        "Take-Profit Threshold", 0.01, 1.0, config.stop_profit_threshold
    )

    col_unit, col_val = st.sidebar.columns([2, 1])
    unit_options = ["day", "month", "quarter", "year"]
    unit_index = (
        unit_options.index(config.hold_period_unit)
        if config.hold_period_unit in unit_options
        else 1
    )
    config.hold_period_unit = col_unit.selectbox(
        "Min Hold Unit", unit_options, index=unit_index
    )
    config.hold_period_value = col_val.number_input(
        "Val", value=config.hold_period_value, min_value=1
    )

    config.model_types = st.sidebar.multiselect(
        "AI Algorithms to Compare",
        [
            "random_forest",
            "xgboost",
            "catboost",
            "prophet",
            "lstm",
        ],
        default=config.model_types,
    )

    scaler_options = ["standard", "robust"]
    scaler_index = (
        scaler_options.index(config.scaler_type)
        if config.scaler_type in scaler_options
        else 0
    )
    config.scaler_type = st.sidebar.radio(
        "Feature Stabilizer (Scaler)",
        scaler_options,
        index=scaler_index,
        help="StandardScaler: Good for normal data. RobustScaler: Better if the stock has frequent huge price/volume spikes.",
    )

    with st.sidebar.expander("Costs & Taxes"):
        profile_options = ["default", "cmc_markets"]
        profile_index = (
            profile_options.index(config.cost_profile)
            if config.cost_profile in profile_options
            else 0
        )
        config.cost_profile = st.selectbox(
            "Cost Profile (Broker)",
            profile_options,
            index=profile_index,
            help="Default: 0.12% brokerage + clearing/settlement. CMC: $11 or 0.10% flat.",
        )

        if config.cost_profile == "default":
            config.brokerage_rate = (
                st.number_input(
                    "Brokerage (%)", value=config.brokerage_rate * 100, step=0.01
                )
                / 100
            )
            config.clearing_rate = (
                st.number_input(
                    "Clearing (%)",
                    value=config.clearing_rate * 100,
                    step=0.0001,
                    format="%.5f",
                )
                / 100
            )
            config.settlement_fee = st.number_input(
                "Settlement ($)", value=config.settlement_fee
            )
        else:
            st.info("CMC Markets: Min $11 or 0.10%. No separate clearing/settlement.")

        st.markdown("---")
        config.annual_income = st.number_input(
            "Annual Income (excl. Investment)",
            value=config.annual_income,
            step=5000.0,
            help="Used to calculate marginal ATO tax brackets (2024-25 rates).",
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
            "catboost",
            "prophet",
            "lstm",
        ],
        default=["random_forest"],
    )

    config.scaler_type = st.sidebar.radio(
        "Feature Stabilizer (Scaler)",
        ["standard", "robust"],
        index=0,
        help="StandardScaler: Good for normal data. RobustScaler: Better if the stock has frequent huge price/volume spikes.",
    )

    with st.sidebar.expander("Costs & Taxes"):
        config.cost_profile = st.selectbox(
            "Cost Profile (Broker)",
            ["default", "cmc_markets"],
            help="Default: 0.12% brokerage + clearing/settlement. CMC: $11 or 0.10% flat.",
        )

        if config.cost_profile == "default":
            config.brokerage_rate = (
                st.number_input("Brokerage (%)", value=0.12, step=0.01) / 100
            )
            config.clearing_rate = (
                st.number_input(
                    "Clearing (%)", value=0.00225, step=0.0001, format="%.5f"
                )
                / 100
            )
            config.settlement_fee = st.number_input("Settlement ($)", value=1.5)
        else:
            st.info("CMC Markets: Min $11 or 0.10%. No separate clearing/settlement.")

        st.markdown("---")
        config.annual_income = st.number_input(
            "Annual Income (excl. Investment)",
            value=90000.0,
            step=5000.0,
            help="Used to calculate marginal ATO tax brackets (2024-25 rates).",
        )

    config.rebuild_model = st.sidebar.checkbox("Rebuild AI Model", value=True)

    if st.sidebar.button("💡 Generate Live Suggestions"):
        # Automatically clear old backtest results when generating new suggestions
        if "results" in st.session_state:
            del st.session_state["results"]

        suggestions = []
        for ticker in config.target_stock_codes:
            consensus_votes = 0
            total_expected_return = 0.0

            # Always fetch the 30-day sequence to be safe for LSTM
            # (Standard models will automatically take the last day [-1] via the new predict logic)
            builder = ModelBuilder(config)
            latest_features = builder.get_latest_features(ticker)

            if latest_features is not None:
                # Latest price is index 3 ('Close') of the LAST row
                current_price = float(latest_features[-1, 3])
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
        # Automatically clear old suggestions when running a new backtest
        if "suggestions" in st.session_state:
            del st.session_state["suggestions"]

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
            - **Net ROI (Return on Investment):** The final percentage gain or loss on your initial capital after all brokerage fees, clearing fees, settlement fees, and ATO taxes.
            - **Gross ROI:** The theoretical percentage gain or loss *before* any fees or taxes are deducted. This represents the "raw skill" of the AI model.
            - **Win Rate:** The percentage of closed trades that were profitable (Gross Profit > 0). 
              *Calculation: (Profitable Trades / Total Trades) * 100*
            - **Profit % (Trade Level):** The net percentage change (after fees and taxes) between the buy and sell points.

            **Costs & Taxes:**
            - **Fees:** Total transaction costs (Brokerage + Clearing + Settlement) for both entry and exit. Includes CMC Markets profiles.
            - **Tax (ATO):** Marginal Capital Gains Tax calculated using 2024-25 Individual Income Tax Brackets. 
              *Note: Includes 50% discount for holdings >= 12 months. Calculated based on your provided annual income.*
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
                if "error" not in res and all(
                    k in res
                    for k in ["roi", "win_rate", "total_trades", "final_capital"]
                ):
                    summary_data.append(
                        {
                            "Algorithm": m_type,
                            "Net ROI": f"{res['roi']:.2%}",
                            "Gross ROI": f"{res.get('gross_roi', 0):.2%}",
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
                        [
                            "Algorithm",
                            "Net ROI",
                            "Gross ROI",
                            "Win Rate",
                            "Trades",
                            "Final Capital",
                        ]
                    ]
                )

                # 2. Capital Growth Over Time (Lines connecting Trade Points)
                st.subheader(f"Capital Growth Comparison - {ticker}")

                combined_equity = []

                for m_type, res in model_res.items():
                    if "error" not in res:
                        # Start with initial capital
                        start_date = None
                        if "equity_history" in res and res["equity_history"]:
                            start_date = res["equity_history"][0]["date"]

                        points = []
                        if start_date:
                            points.append(
                                {
                                    "date": pd.to_datetime(start_date).date(),
                                    "capital": round(config.init_capital, 2),
                                    "Algorithm": m_type,
                                }
                            )

                        if res.get("trades"):
                            for t in res["trades"]:
                                points.append(
                                    {
                                        "date": pd.to_datetime(t["sell_date"]).date(),
                                        "capital": round(
                                            t.get(
                                                "cumulative_capital",
                                                config.init_capital,
                                            ),
                                            2,
                                        ),
                                        "Algorithm": m_type,
                                    }
                                )

                        # Add final capital point at the end of backtest if not already there
                        if "equity_history" in res and res["equity_history"]:
                            end_date = res["equity_history"][-1]["date"]
                            points.append(
                                {
                                    "date": pd.to_datetime(end_date).date(),
                                    "capital": round(res["final_capital"], 2),
                                    "Algorithm": m_type,
                                }
                            )

                        if points:
                            combined_equity.append(pd.DataFrame(points))

                if combined_equity:
                    equity_df = pd.concat(combined_equity)

                    # Create the line chart connecting trade points
                    fig_growth = px.line(
                        equity_df,
                        x="date",
                        y="capital",
                        color="Algorithm",
                        markers=True,
                        title=f"Portfolio Value Over Time (Realized Trades - {ticker})",
                        labels={"capital": "Total Capital (AUD)", "date": "Date"},
                    )
                    st.plotly_chart(fig_growth, width="stretch")

                # Detail View with Tabs
                st.subheader("Detailed Performance")
                tabs = st.tabs([m.upper() for m in model_res.keys()])
                for i, (m_type, res) in enumerate(model_res.items()):
                    with tabs[i]:
                        if "error" in res:
                            st.error(res["error"])
                            continue

                        avg_profit = 0.0
                        if res.get("trades"):
                            avg_profit = sum(
                                t["profit_pct"] for t in res["trades"]
                            ) / len(res["trades"])

                        col1, col2, col3, col4, col5 = st.columns(5)
                        col1.metric(
                            "Net ROI",
                            f"{res['roi']:.2%}",
                            help="Final return after all fees and taxes.",
                        )
                        col2.metric(
                            "Gross ROI",
                            f"{res.get('gross_roi', 0):.2%}",
                            help="Theoretical return before fees and taxes.",
                        )
                        col3.metric(
                            "Win Rate",
                            f"{res['win_rate']:.2%}",
                            help="Percentage of profitable trades.",
                        )
                        col4.metric(
                            "Avg Profit/Trade",
                            f"{avg_profit:.2%}",
                            help="Average net profit percentage per closed position.",
                        )
                        col5.metric(
                            "Trades",
                            res["total_trades"],
                            help="Number of completed transactions.",
                        )

                        if res["trades"]:
                            trades_df = pd.DataFrame(res["trades"])

                            # Convert dates to date-only for display
                            for col in ["buy_date", "sell_date"]:
                                if col in trades_df.columns:
                                    trades_df[col] = pd.to_datetime(
                                        trades_df[col]
                                    ).dt.date

                            st.write("#### Transaction Log")
                            # Format financial columns
                            format_cols = {
                                "buy_price": "{:.2f}",
                                "sell_price": "{:.2f}",
                                "fees": "{:.2f}",
                                "tax": "{:.2f}",
                                "profit_loss": "{:.2f}",
                                "profit_pct": "{:.2%}",
                                "cumulative_capital": "{:.2f}",
                            }
                            st.dataframe(trades_df.style.format(format_cols))

            else:
                st.warning(f"No valid results for {ticker}")


if __name__ == "__main__":
    run_ui()
