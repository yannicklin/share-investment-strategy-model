"""
USA AI Trading System - Index Manager

Purpose: Manages US index constituents with live updates and caching
for Dow 30, Nasdaq 100, and S&P 500.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
import json
import os
import re
import requests
from typing import List, Dict

CACHE_FILE = "data/models/index_cache_usa.json"

# Reliable sources for US Indices (Wikipedia often has the most stable table structures)
SOURCE_URLS = {
    "Dow 30": "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average",
    "Nasdaq 100": "https://en.wikipedia.org/wiki/Nasdaq-100",
    "S&P 500": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
}

DEFAULT_INDEX_DATA = {
    "Dow 30": [
        "AAPL",
        "AMZN",
        "AXP",
        "BA",
        "CAT",
        "CRM",
        "CSCO",
        "CVX",
        "DIS",
        "GS",
        "HD",
        "HON",
        "IBM",
        "INTC",
        "JNJ",
        "JPM",
        "KO",
        "MCD",
        "MMM",
        "MRK",
        "MSFT",
        "NKE",
        "PG",
        "TRV",
        "UNH",
        "V",
        "VZ",
        "WBA",
        "WMT",
        "DIS",
    ],
    "Nasdaq 100": [
        "AAPL",
        "ABNB",
        "ADBE",
        "ADI",
        "ADP",
        "ADSK",
        "AEP",
        "ALGN",
        "AMAT",
        "AMD",
        "AMGN",
        "AMZN",
        "ANSS",
        "ASML",
        "AVGO",
        "AZN",
        "BKR",
        "BKNG",
        "BIIB",
        "CDNS",
        "CEG",
        "CHTR",
        "CPRT",
        "CSGP",
        "CSCO",
        "CSX",
        "CTAS",
        "CTSH",
        "DDOG",
        "DLTR",
        "DXCM",
        "EA",
        "EBAY",
        "ENPH",
        "EXC",
        "FAST",
        "FANG",
        "FTNT",
        "GILD",
        "GOOG",
        "GOOGL",
        "HON",
        "IDXX",
        "ILMN",
        "INTC",
        "INTU",
        "ISRG",
        "JD",
        "KDP",
        "KLA",
        "LCID",
        "LRCX",
        "LULU",
        "MAR",
        "MCHP",
        "MDLZ",
        "MELI",
        "META",
        "MNST",
        "MRNA",
        "MRVL",
        "MSFT",
        "MU",
        "NFLX",
        "NVDA",
        "NXPI",
        "ORLY",
        "PANW",
        "PAYX",
        "PCAR",
        "PDD",
        "PEP",
        "PYPL",
        "QCOM",
        "REGN",
        "ROST",
        "SBUX",
        "SIRI",
        "SGEN",
        "SNPS",
        "SPLK",
        "SWKS",
        "TMUS",
        "TSLA",
        "TXN",
        "VRSK",
        "VRSN",
        "VRTX",
        "WBA",
        "WBD",
        "WDAY",
        "XEL",
        "ZM",
        "ZS",
    ],
    "S&P 500": [
        "AAPL",
        "MSFT",
        "AMZN",
        "NVDA",
        "GOOGL",
        "META",
        "GOOG",
        "BRK.B",
        "TSLA",
        "UNH",
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


from io import StringIO


def update_index_data() -> Dict[str, str]:
    """Fetches latest constituents from Wikipedia tables and updates cache."""
    updated_counts = {}
    new_data = {}

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for name, url in SOURCE_URLS.items():
        try:
            # Use requests with headers to avoid 403 Forbidden from Wikipedia
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                raise ConnectionError(f"HTTP {response.status_code}")

            tables = pd.read_html(StringIO(response.text))

            tickers = []
            # Robustly find the table with symbols
            for df in tables:
                cols = [str(c).lower() for c in df.columns]
                # Look for standard symbol columns
                symbol_col = None
                for i, col in enumerate(cols):
                    if col in ["symbol", "ticker", "ticker symbol"]:
                        symbol_col = i
                        break

                if symbol_col is not None:
                    # Dow 30/Nasdaq/S&P usually have symbols in these columns
                    raw_list = df.iloc[:, symbol_col].dropna().astype(str).tolist()
                    # Filter out header-like strings or junk
                    tickers = [
                        t.strip().upper().replace(".", "-")
                        for t in raw_list
                        if 1 <= len(t.strip()) <= 6
                        and any(c.isalpha() for c in t)  # Must contain letters
                    ]

                    # Verification: Dow 30 (~30), Nasdaq (~100), S&P (~500)
                    min_expected = {"Dow 30": 25, "Nasdaq 100": 95, "S&P 500": 490}
                    if len(tickers) >= min_expected.get(name, 5):
                        break  # Found the right table
                    else:
                        tickers = []  # Keep looking

            if tickers:
                new_data[name] = sorted(list(set(tickers)))
                updated_counts[name] = f"Updated {len(tickers)} tickers"
            else:
                updated_counts[name] = "Failed: No valid table found"
                new_data[name] = DEFAULT_INDEX_DATA.get(name, [])

        except Exception as e:
            updated_counts[name] = f"Failed: {str(e)}"
            new_data[name] = DEFAULT_INDEX_DATA.get(name, [])

    # Save to cache if any sync was successful
    if any("Updated" in v for v in updated_counts.values()):
        os.makedirs("data/models", exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(new_data, f)

    return updated_counts
