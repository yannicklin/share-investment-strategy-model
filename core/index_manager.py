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
import requests  # Needed for web scraping with User-Agent
import io  # Required for pd.read_html StringIO
import re  # Required for regular expressions in ticker cleaning
from typing import List, Dict

CACHE_FILE = "data/models/usa_index_cache.json"

# User-Agent to mimic a browser and avoid 403 Forbidden errors
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

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
        html_content = requests.get(url_sp500, headers=HEADERS, timeout=10).text
        tables = pd.read_html(io.StringIO(html_content))
        df = tables[0]
        sp500_tickers = df["Symbol"].tolist()
        # Wikipedia uses dots for classes (BRK.B), but yfinance uses dashes (BRK-B)
        sp500_tickers = sorted(
            list(set([t.replace(".", "-") for t in sp500_tickers]))
        )  # Ensure unique and sorted
        new_data["S&P 500"] = sp500_tickers
        updated_counts["S&P 500"] = f"Updated {len(sp500_tickers)} tickers"
    except Exception as e:
        updated_counts["S&P 500"] = f"Failed: {str(e)}"
        new_data["S&P 500"] = DEFAULT_INDEX_DATA["S&P 500"]

    # 2. Scrape Nasdaq 100
    try:
        url_nasdaq100 = "https://en.wikipedia.org/wiki/Nasdaq-100"
        html_content = requests.get(url_nasdaq100, headers=HEADERS, timeout=10).text
        tables = pd.read_html(io.StringIO(html_content))
        # Nasdaq 100 table is usually the 4th one
        df = tables[4]
        df_columns_list = df.columns.tolist()
        if "Ticker" in df_columns_list:
            nasdaq_tickers = df["Ticker"].tolist()
        elif "Symbol" in df_columns_list:
            nasdaq_tickers = df["Symbol"].tolist()
        else:
            nasdaq_tickers = DEFAULT_INDEX_DATA["Nasdaq 100"]

        nasdaq_tickers = sorted(list(set(nasdaq_tickers)))  # Ensure unique and sorted
        new_data["Nasdaq 100"] = nasdaq_tickers
        updated_counts["Nasdaq 100"] = f"Updated {len(nasdaq_tickers)} tickers"
    except Exception as e:
        updated_counts["Nasdaq 100"] = f"Failed: {str(e)}"
        new_data["Nasdaq 100"] = DEFAULT_INDEX_DATA["Nasdaq 100"]

    # 3. Scrape Dow Jones 30
    try:
        url_dow = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
        html_content = requests.get(url_dow, headers=HEADERS, timeout=10).text
        tables = pd.read_html(io.StringIO(html_content))
        # Based on previous debug output, table 2 contains the Dow Jones constituents
        df = tables[2]
        dow_tickers = df["Symbol"].astype(str).tolist()
        # Clean up any non-ticker entries (e.g., table headers that got included)
        dow_tickers = [t for t in dow_tickers if re.match(r"^[A-Z]{1,5}$", t)]
        dow_tickers = sorted(list(set(dow_tickers)))  # Ensure unique and sorted
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
