"""
USA AI Trading System - Strategy View

Purpose: Renders the "Consensus Strategy" dashboard.
Implements ROI evaluation using multi-model voting.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import streamlit as st
import pandas as pd
from ui.components import render_trade_details


def render_strategy_view(ticker, res):
    """Main panel for Consensus Mode: Evaluating the committee."""
    st.header(f"🏛️ Consensus Strategy: {ticker}")

    if "error" in res:
        st.error(res["error"])
        return

    st.info(
        """
        **The Strategy:**
        1. Train a committee of distinct AI models (Random Forest, GBDT, LSTM, Prophet).
        2. Each model casts a vote (BUY/SELL) based on predicted ROI vs Hurdle Rate.
        3. A trade is executed ONLY if there is a **Majority Consensus**.
        4. Tied votes are resolved by the **Tie-Breaker** model selected in the sidebar.
        """
    )

    # Re-use the trade details component as it's consistent across views now
    render_trade_details(ticker, res)
