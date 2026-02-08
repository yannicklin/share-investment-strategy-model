"""
USA AI Trading System - Index Manager

Purpose: Manages USA index constituents (S&P 500, Nasdaq 100, Dow Jones)
with live updates and caching.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
import json
import os
from typing import List, Dict

CACHE_FILE = "data/models/usa_index_cache.json"

DEFAULT_INDEX_DATA = {
    "S&P 500": [
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "NVDA",
        "META",
        "BRK-B",
        "TSLA",
        "LLY",
        "V",
        "JPM",
        "UNH",
        "MA",
        "XOM",
        "AVGO",
        "PG",
        "HD",
        "COST",
        "JNJ",
        "ORCL",
    ],
    "Nasdaq 100": [
        "AAPL",
        "MSFT",
        "AMZN",
        "NVDA",
        "META",
        "GOOGL",
        "GOOG",
        "AVGO",
        "TSLA",
        "COST",
        "PEP",
        "ADBE",
        "LIN",
        "AMD",
        "NFLX",
        "TMUS",
        "CSCO",
        "INTU",
        "QCOM",
        "AMAT",
    ],
    "Dow Jones 30": [
        "UNH",
        "GS",
        "HD",
        "MSFT",
        "CAT",
        "MCD",
        "V",
        "CRM",
        "BA",
        "HON",
        "AMGN",
        "AXP",
        "JPM",
        "IBM",
        "AAPL",
        "TRV",
        "WMT",
        "NKE",
        "PG",
        "DIS",
    ],
}


def load_index_constituents() -> Dict[str, List[str]]:
    """Loads constituents from local cache or defaults."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_INDEX_DATA
    return DEFAULT_INDEX_DATA


def update_index_data() -> Dict[str, str]:
    """Updates constituent data. For US markets, we currently use robust defaults."""
    # Placeholder for potential Wikipedia or yfinance based scraper
    os.makedirs("data/models", exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(DEFAULT_INDEX_DATA, f)

    return {k: f"Using default {len(v)} tickers" for k, v in DEFAULT_INDEX_DATA.items()}
