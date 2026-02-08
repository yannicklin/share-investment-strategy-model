"""
Trading AI System - Sidebar (USA Edition)

Purpose: Configuration panel for selecting analysis mode, broker profile,
and tax settings (W-8BEN).

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
from core.config import BROKERS, DEFAULT_BROKER, DEFAULT_TICKERS, START_DATE, END_DATE


def render_sidebar():
    """Renders the sidebar and returns the configuration dictionary."""
    st.sidebar.header("🇺🇸 USA Market Strategy")

    # Mode Selection
    mode = st.sidebar.radio(
        "Analysis Mode",
        ["Models Comparison", "Time-Span Comparison", "Find Super Stars"],
        index=0,
    )

    st.sidebar.markdown("---")

    # Financial Configuration
    st.sidebar.subheader("Financial Profile")

    # Broker Selection
    broker_name = st.sidebar.selectbox(
        "Broker Profile",
        options=list(BROKERS.keys()),
        index=list(BROKERS.keys()).index(DEFAULT_BROKER),
    )

    # W-8BEN Status (Foreign Investor)
    st.sidebar.caption("Tax Residency Settings")
    w8ben_filed = st.sidebar.checkbox(
        "W-8BEN Filed?",
        value=True,
        help="If checked: 15% Dividend Tax, $0 Capital Gains Tax (Treaty). If unchecked: 30% Tax.",
    )

    initial_capital = st.sidebar.number_input(
        "Initial Capital (USD)", value=10000.0, step=1000.0, format="%.2f"
    )

    st.sidebar.markdown("---")

    # Ticker Selection
    st.sidebar.subheader("Asset Selection")

    index_choice = None
    if mode == "Find Super Stars":
        # Index Selection
        index_choice = st.sidebar.selectbox(
            "Market Index", ["S&P 500", "Nasdaq 100", "Dow Jones 30"]
        )
        selected_ticker = None  # Logic handled in view
    else:
        # Single Ticker Selection
        selected_ticker = st.sidebar.selectbox(
            "Select Ticker", options=DEFAULT_TICKERS, index=0
        )
        # Custom Ticker
        custom_ticker = st.sidebar.text_input("Or Enter Custom Symbol (e.g., PLTR)")
        if custom_ticker:
            selected_ticker = custom_ticker.upper()

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Data Range: {START_DATE} to {END_DATE}")
    st.sidebar.caption("© 2026 Yannick | USA Market Model")

    return {
        "mode": mode,
        "broker": broker_name,
        "w8ben": w8ben_filed,
        "capital": initial_capital,
        "ticker": selected_ticker,
        "index": index_choice if mode == "Find Super Stars" else None,
    }
