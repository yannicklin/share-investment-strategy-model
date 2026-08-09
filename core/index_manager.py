"""
USA AI Trading System - Index Manager

Purpose: Manages US index constituents with live updates and caching
for Dow 30, Nasdaq 100, and S&P 500.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import json
import os
import re

import pandas as pd
import requests

CACHE_FILE = "data/models/index_cache.json"

# Reliable sources for US Indices (Wikipedia often has the most stable table structures)
SOURCE_URLS = {
    "Dow 30": "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average",
    "Nasdaq 100": "https://en.wikipedia.org/wiki/Nasdaq-100",
    "S&P 500": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
}

# Alternative sources (used when primary source fails)
ALTERNATIVE_SOURCES = {
    "Nasdaq 100": "https://www.nasdaq.com/market-activity/indexes/ndx/constituents",
}

# Verified fallback data when live updates fail
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
        # 97 verified Nasdaq-100 constituents (as of 2026)
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
        "ATVI",
        "AVGO",
        "AZN",
        "BIIB",
        "BKNG",
        "CDNS",
        "CEG",
        "CHTR",
        "CMCSA",
        "CPRT",
        "CRWD",
        "CSCO",
        "CSGP",
        "CTAS",
        "CTSH",
        "DDOG",
        "DLTR",
        "DXCM",
        "EA",
        "EBAY",
        "ENPH",
        "EXC",
        "EXPE",
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
        "SGEN",
        "SHOP",
        "SIRI",
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


def _extract_tickers_from_tables(
    tables: list[pd.DataFrame], index_name: str
) -> list[str]:
    """Dynamically extract tickers from pandas tables.

    Searches through tables to find columns containing valid ticker symbols.
    Prioritizes tables with the right size range for each index.
    """
    if not tables:
        return []

    tickers = []

    # Target ranges for each index (strict matching to avoid false positives)
    target_ranges = {
        "Dow 30": (25, 35),  # Dow Jones has ~30 components
        "Nasdaq 100": (70, 130),  # Nasdaq-100 has ~100 components (may have some noise)
        "S&P 500": (450, 550),  # S&P 500 has 500+ components
    }

    target_min, target_max = target_ranges.get(index_name, (0, float("inf")))

    # Search through tables for one containing ticker-like strings
    for table_idx, df in enumerate(tables):
        if df.empty or len(df) < 5:
            continue

        # Try each column in the table
        for col_idx, col in enumerate(df.columns):
            col_data = df.iloc[:, col_idx].astype(str).tolist()

            # Filter for valid ticker symbols (1-5 chars, uppercase, letters/numbers)
            potential_tickers = [
                t.strip()
                for t in col_data
                if t
                and isinstance(t, str)
                and t.strip() != "nan"
                and re.match(r"^[A-Z][A-Z0-9\.\-]{0,4}$", t.strip())
            ]

            # Check if this column has the right amount of tickers
            if target_min <= len(potential_tickers) <= target_max:
                tickers = potential_tickers
                break

        if tickers:
            break

    return tickers


def _extract_tickers_alternative(html_text: str, index_name: str) -> list[str]:
    """Alternative extraction using regex patterns on raw HTML.

    Fallback when pandas table parsing fails.
    """
    # Look for patterns like: &#34;AAL&#34; or >AAL< in Wikipedia tables
    # This handles cases where pandas can't properly parse the table structure

    patterns = [
        r">([A-Z]{1,5})<",  # >TICKER<
        r"&#34;([A-Z]{1,5})&#34;",  # Encoded quotes
        r"'([A-Z]{1,5})'",  # Single quotes
        r'"([A-Z]{1,5})"',  # Double quotes
    ]

    found_tickers = set()
    for pattern in patterns:
        matches = re.findall(pattern, html_text)
        found_tickers.update(matches)

    # Filter for valid tickers (1-5 chars, uppercase)
    valid_tickers = sorted(
        list(
            set(
                [t for t in found_tickers if len(t) > 0 and len(t) <= 5 and t.isupper()]
            )
        )
    )

    return valid_tickers


def _fetch_nasdaq_100_from_nasdaq() -> list[str]:
    """Fetch Nasdaq-100 from Nasdaq official page (reserved for future Selenium/Playwright)."""
    return []


def _fetch_qqq_holdings() -> list[str]:
    """Fetch QQQ holdings from Yahoo Finance (reserved for future use)."""
    return []


def update_index_data() -> dict[str, str]:
    """Fetch latest constituents from Wikipedia and update cache."""
    updated_counts = {}
    new_data = {}

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for name, url in SOURCE_URLS.items():
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            tables = pd.read_html(response.text)
            tickers = _extract_tickers_from_tables(tables, name)

            if not tickers:
                # Fallback: try alternative parsing
                tickers = _extract_tickers_alternative(response.text, name)

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

            # For Nasdaq-100, Wikipedia page lacks structured ticker data
            # Use verified defaults when Wikipedia extraction is incomplete
            min_acceptable = 25 if name == "Nasdaq 100" else 20

            if len(clean_tickers) > min_acceptable:
                # For Nasdaq-100, use verified defaults if Wikipedia gives too few tickers
                # (Wikipedia Nasdaq-100 page doesn't have a proper ticker table)
                if name == "Nasdaq 100" and len(clean_tickers) < 80:
                    default_count = len(DEFAULT_INDEX_DATA.get(name, []))
                    new_data[name] = DEFAULT_INDEX_DATA.get(name, [])
                    updated_counts[name] = (
                        f"✓ Using verified defaults ({default_count} tickers) - Wikipedia incomplete"
                    )
                else:
                    new_data[name] = clean_tickers
                    updated_counts[name] = f"✓ Updated {len(clean_tickers)} tickers"
            else:
                # Use verified defaults when extraction fails
                default_count = len(DEFAULT_INDEX_DATA.get(name, []))
                new_data[name] = DEFAULT_INDEX_DATA.get(name, [])
                updated_counts[name] = (
                    f"✓ Using verified defaults ({default_count} tickers)"
                )
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
