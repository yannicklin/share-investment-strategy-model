"""ASX AI Trading System - Main Application Entry Point."""

import streamlit as st
import pandas as pd
from core.config import load_config
from core.model_builder import ModelBuilder
from core.backtest_engine import BacktestEngine
from ui.sidebar import render_sidebar
from ui.algo_view import render_algorithm_comparison
from ui.strategy_view import render_strategy_sensitivity
from ui.components import render_glossary


def main():
    """Main execution flow for the dashboard."""
    st.set_page_config(page_title="ASX AI Trading System", layout="wide")
    st.title("📈 ASX AI Trading Strategy Dashboard")

    # Load shared configuration
    config = load_config()

    # Render Sidebar and get mode-specific params
    mode, test_periods, period_map, gen_suggestions, tie_breaker = render_sidebar(
        config
    )

    # 1. LIVE SUGGESTIONS ENGINE (Today's Prediction)
    if gen_suggestions:
        if "results" in st.session_state:
            del st.session_state["results"]

        suggestions = []
        builder = ModelBuilder(config)

        for ticker in config.target_stock_codes:
            with st.spinner(f"Analyzing {ticker} for today..."):
                votes = 0
                total_return = 0.0
                tie_breaker_bullish = False

                # Tie breaker setup
                tb_model = tie_breaker if tie_breaker else config.model_types[0]

                latest_features = builder.get_latest_features(ticker)
                if latest_features is not None:
                    current_price = float(latest_features[-1, 3])

                    for idx, m_type in enumerate(config.model_types):
                        config.model_type = m_type
                        builder.load_or_build(ticker)
                        pred = builder.predict(latest_features, date=pd.Timestamp.now())

                        is_m_bullish = pred > current_price
                        if is_m_bullish:
                            votes += 1
                        if m_type == tb_model:
                            tie_breaker_bullish = is_m_bullish

                        total_return += (pred - current_price) / current_price

                    avg_return = total_return / len(config.model_types)

                    # Tie-breaker logic for live suggestions
                    is_bullish = False
                    if votes > (len(config.model_types) / 2):
                        is_bullish = True
                    elif votes == (len(config.model_types) / 2):
                        is_bullish = tie_breaker_bullish

                    suggestions.append(
                        {
                            "Ticker": ticker,
                            "Current Price": f"${current_price:,.2f}",
                            "Expected Return": f"{avg_return:.2%}",
                            "Consensus": f"{votes}/{len(config.model_types)} Models",
                            "Signal": "🟢 BUY" if is_bullish else "🟡 WAIT/HOLD",
                        }
                    )
        st.session_state["suggestions"] = suggestions

    # Display suggestions if they exist
    if "suggestions" in st.session_state:
        st.header("🚀 AI Daily Recommendations")
        suggest_df = pd.DataFrame(st.session_state["suggestions"])
        st.dataframe(
            suggest_df,
            column_config={
                "Current Price": st.column_config.TextColumn("Current Price"),
                "Expected Return": st.column_config.TextColumn("Expected Return"),
            },
            hide_index=True,
            use_container_width=True,
        )
        st.info(
            "Signals are based on the latest available market close and your trained models."
        )

    # 2. BACKTEST ANALYSIS ENGINE
    if st.sidebar.button("🚀 Run Analysis"):
        if "suggestions" in st.session_state:
            del st.session_state["suggestions"]
        if "results" in st.session_state:
            del st.session_state["results"]

        all_results = {}
        builder = ModelBuilder(config)
        engine = BacktestEngine(config, builder)

        for ticker in config.target_stock_codes:
            ticker_results = {}

            with st.spinner(f"Preparing models for {ticker}..."):
                original_rebuild = config.rebuild_model
                for m_type in config.model_types:
                    config.model_type = m_type
                    builder.load_or_build(ticker)
                config.rebuild_model = False

            if mode == "Models Comparison":
                for m_type in config.model_types:
                    with st.spinner(f"Testing {ticker} with {m_type}..."):
                        ticker_results[m_type] = engine.run_model_mode(ticker, m_type)
            else:
                # Mode 2: Time-Span Comparison
                for p_name in test_periods:
                    with st.spinner(f"Testing {ticker} with {p_name} hold..."):
                        unit, val = period_map[p_name]
                        config.hold_period_unit, config.hold_period_value = unit, val
                        ticker_results[p_name] = engine.run_strategy_mode(
                            ticker, config.model_types, tie_breaker=tie_breaker
                        )

            all_results[ticker] = ticker_results
            config.rebuild_model = original_rebuild

        st.session_state["results"] = all_results
        st.session_state["active_mode"] = mode

    # Render Main Dashboard
    if "results" in st.session_state:
        render_glossary()
        results = st.session_state["results"]
        active_mode = st.session_state["active_mode"]

        for ticker, ticker_res in results.items():
            if active_mode == "Models Comparison":
                render_algorithm_comparison(ticker, ticker_res)
            else:
                render_strategy_sensitivity(ticker, ticker_res)
            st.markdown("---")
    elif "suggestions" not in st.session_state:
        st.info("Configure the sidebar and click 'Run Analysis' to see results.")


if __name__ == "__main__":
    main()
