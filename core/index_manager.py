"""
USA AI Trading System - Index Manager

Purpose: Manages USA index constituents (S&P 500, Nasdaq 100, Dow Jones)
with live updates and caching using Wikipedia as a reliable source.

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
    """Updates constituent data by scraping Wikipedia."""
    updated_counts = {}
    new_data = {}

    # 1. Scrape S&P 500
    try:
        url_sp500 = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url_sp500)
        df = tables[0]
        sp500_tickers = df["Symbol"].tolist()
        # Wikipedia uses dots for classes (BRK.B), but yfinance uses dashes (BRK-B)
        sp500_tickers = [t.replace(".", "-") for t in sp500_tickers]
        new_data["S&P 500"] = sp500_tickers
        updated_counts["S&P 500"] = f"Updated {len(sp500_tickers)} tickers"
    except Exception as e:
        updated_counts["S&P 500"] = f"Failed: {str(e)}"
        new_data["S&P 500"] = DEFAULT_INDEX_DATA["S&P 500"]

    # 2. Scrape Nasdaq 100
    try:
        url_nasdaq100 = "https://en.wikipedia.org/wiki/Nasdaq-100"
        tables = pd.read_html(url_nasdaq100)
        # Nasdaq 100 table is usually the 4th one
        df = tables[4]
        if "Ticker" in df.columns:
            nasdaq_tickers = df["Ticker"].tolist()
        elif "Symbol" in df.columns:
            nasdaq_tickers = df["Symbol"].tolist()
        else:
            nasdaq_tickers = DEFAULT_INDEX_DATA["Nasdaq 100"]

        new_data["Nasdaq 100"] = nasdaq_tickers
        updated_counts["Nasdaq 100"] = f"Updated {len(nasdaq_tickers)} tickers"
    except Exception as e:
        updated_counts["Nasdaq 100"] = f"Failed: {str(e)}"
        new_data["Nasdaq 100"] = DEFAULT_INDEX_DATA["Nasdaq 100"]

    # 3. Scrape Dow Jones 30
    try:
        url_dow = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
        tables = pd.read_html(url_dow)
        df = tables[1]
        dow_tickers = df["Symbol"].tolist()
        new_data["Dow Jones 30"] = dow_tickers
        updated_counts["Dow Jones 30"] = f"Updated {len(dow_tickers)} tickers"
    except Exception as e:
        updated_counts["Dow Jones 30"] = f"Failed: {str(e)}"
        new_data["Dow Jones 30"] = DEFAULT_INDEX_DATA["Dow Jones 30"]

    # Save to cache
    os.makedirs("data/models", exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(new_data, f)

    return updated_counts
