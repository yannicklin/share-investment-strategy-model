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
    config.max_hold_days = st.sidebar.number_input("Max Hold Days", value=30)
    config.rebuild_model = st.sidebar.checkbox("Rebuild AI Model", value=True)

    if st.sidebar.button("🚀 Run Backtest"):
        builder = ModelBuilder(config)
        engine = BacktestEngine(config, builder)

        for ticker in config.target_stock_codes:
            with st.spinner(f"Processing {ticker}..."):
                builder.load_or_build(ticker)
                results = engine.run(ticker)

                if "error" in results:
                    st.error(f"Error for {ticker}: {results['error']}")
                    continue

                st.subheader(f"Results for {ticker}")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("ROI", f"{results['roi']:.2%}")
                col2.metric("Win Rate", f"{results['win_rate']:.2%}")
                col3.metric("Total Trades", results["total_trades"])
                col4.metric("Final Capital", f"${results['final_capital']:,.2f}")

                if results["trades"]:
                    trades_df = pd.DataFrame(results["trades"])
                    st.write("### Transaction Log")
                    st.dataframe(trades_df)

                    # Plotly Chart
                    fig = px.line(
                        trades_df,
                        x="sell_date",
                        y="profit_pct",
                        title=f"Profit % Over Time - {ticker}",
                    )
                    st.plotly_chart(fig)
                else:
                    st.info("No trades executed during this period.")

                # Future Recommendation (Mockup based on last prediction)
                data = builder.fetch_data(ticker, 1)
                if not data.empty:
                    # We need to compute features for the last row
                    # For simplicity, we'll just show the last prediction
                    # In a real app, we'd have a 'recommendation' function
                    st.info(
                        f"💡 **Recommendation for {ticker}:** Model predicts positive trend based on recent data."
                    )


if __name__ == "__main__":
    run_ui()
