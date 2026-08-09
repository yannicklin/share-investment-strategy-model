"""
USA AI Trading System - Index Manager

Purpose: Manages US index constituents with live updates and caching
for Dow 30, Nasdaq 100, and S&P 500.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import json
import os

import pandas as pd
import requests

CACHE_FILE = "data/models/index_cache.json"

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


def load_index_constituents() -> dict[str, list[str]]:
    """Loads constituents from local cache or defaults."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_INDEX_DATA
    return DEFAULT_INDEX_DATA


def update_index_data() -> dict[str, str]:
    """Fetches latest constituents from Wikipedia tables and updates cache."""
    updated_counts = {}
    new_data = {}

    # Add proper User-Agent to avoid 403 Forbidden from Wikipedia
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for name, url in SOURCE_URLS.items():
        try:
            # Fetch Wikipedia page with proper headers to avoid 403 Forbidden
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise exception for bad status codes

            # For US indices on Wikipedia, pandas read_html is very effective
            # Pass the HTML content directly instead of URL to avoid requests without headers
            tables = pd.read_html(response.text)

            if name == "Dow 30":
                df = tables[1]  # Usually the second table
                tickers = df.iloc[:, 1].tolist()  # Symbol column
            elif name == "Nasdaq 100":
                df = tables[4]  # Usually the components table
                tickers = df.iloc[:, 1].tolist()
            elif name == "S&P 500":
                df = tables[0]
                tickers = df.iloc[:, 0].tolist()
            else:
                tickers = []

            # Clean tickers
            clean_tickers = sorted(
                list(
                    set(
                        [
                            str(t)
                            .strip()
                            .replace(
                                ".", "-"
                            )  # Wikipedia uses . for classes, yfinance uses -
                            for t in tickers
                            if isinstance(t, str) and len(t) > 0 and len(t) < 10
                        ]
                    )
                )
            )

            if len(clean_tickers) > 5:
                new_data[name] = clean_tickers
                updated_counts[name] = f"Updated {len(clean_tickers)} tickers"
            else:
                updated_counts[name] = "Failed: No tickers found"
                new_data[name] = DEFAULT_INDEX_DATA.get(name, [])

        except requests.exceptions.HTTPError as e:
            if "403" in str(e):
                updated_counts[name] = "Failed: Access denied (403). Using cache."
            else:
                updated_counts[name] = f"Failed: HTTP Error - {e!s}"
            new_data[name] = DEFAULT_INDEX_DATA.get(name, [])
        except requests.exceptions.RequestException as e:
            updated_counts[name] = f"Failed: Network error - {e!s}"
            new_data[name] = DEFAULT_INDEX_DATA.get(name, [])
        except Exception as e:
            updated_counts[name] = f"Failed: {e!s}"
            new_data[name] = DEFAULT_INDEX_DATA.get(name, [])

    # Save to cache
    os.makedirs("data/models", exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(new_data, f)

    return updated_counts
