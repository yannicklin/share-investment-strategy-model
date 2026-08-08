"""
Taiwan Stock AI Trading System - Index Manager

Purpose: Manages Taiwan index constituents (TWSE 50, etc.) with caching.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
import json
import os
from typing import List, Dict

CACHE_FILE = "data/models/index_cache_twn.json"

DEFAULT_INDEX_DATA = {
    "台股50 (Taiwan 50)": [
        "2330.TW",
        "2317.TW",
        "2454.TW",
        "2308.TW",
        "2303.TW",
        "2882.TW",
        "2412.TW",
        "2382.TW",
        "3711.TW",
        "2881.TW",
        "2301.TW",
        "2886.TW",
        "1301.TW",
        "1303.TW",
        "2002.TW",
        "2891.TW",
        "5880.TW",
        "2884.TW",
        "2892.TW",
        "2912.TW",
        "1216.TW",
        "2357.TW",
        "2408.TW",
        "2880.TW",
        "2885.TW",
        "3008.TW",
        "3045.TW",
        "4904.TW",
        "4938.TW",
        "5871.TW",
        "5876.TW",
        "6505.TW",
        "9910.TW",
        "1101.TW",
        "1590.TW",
        "2327.TW",
        "2379.TW",
        "2395.TW",
        "2409.TW",
        "2603.TW",
        "2609.TW",
        "2615.TW",
        "3034.TW",
        "3037.TW",
        "3231.TW",
        "3481.TW",
        "6415.TW",
        "8046.TW",
        "9921.TW",
        "9945.TW",
    ],
    "台股中型100 (Mid 100)": [
        "2337.TW",
        "2344.TW",
        "2352.TW",
        "2353.TW",
        "2356.TW",
        "2360.TW",
        "2376.TW",
        "2377.TW",
        "2385.TW",
        "2404.TW",
        "2449.TW",
        "2451.TW",
        "2458.TW",
        "2474.TW",
        "2492.TW",
        "2498.TW",
        "2610.TW",
        "2618.TW",
        "2801.TW",
        "2809.TW",
        "2812.TW",
        "2834.TW",
        "2845.TW",
        "2855.TW",
        "2883.TW",
        "2887.TW",
        "2888.TW",
        "2889.TW",
        "2890.TW",
        "2903.TW",
        "3005.TW",
        "3035.TW",
        "3532.TW",
        "3702.TW",
        "6176.TW",
        "6239.TW",
        "8046.TW",
        "9904.TW",
        "9933.TW",
    ],
    "MSCI台股指數 (MSCI Taiwan)": [
        "2330.TW",
        "2317.TW",
        "2454.TW",
        "2308.TW",
        "2303.TW",
        "2881.TW",
        "2882.TW",
        "2382.TW",
        "3711.TW",
        "2412.TW",
        "2891.TW",
        "5880.TW",
        "2886.TW",
        "2002.TW",
        "1301.TW",
        "1303.TW",
        "2884.TW",
        "1216.TW",
        "2892.TW",
        "2912.TW",
        "2357.TW",
        "2408.TW",
        "2880.TW",
        "2885.TW",
        "3008.TW",
        "3045.TW",
        "4904.TW",
        "4938.TW",
        "5871.TW",
        "5876.TW",
        "6505.TW",
        "9910.TW",
        "1101.TW",
        "1590.TW",
        "2327.TW",
        "2379.TW",
        "2395.TW",
        "2409.TW",
        "2603.TW",
        "2609.TW",
        "2615.TW",
        "3034.TW",
        "3037.TW",
        "3231.TW",
        "3481.TW",
        "6415.TW",
        "8046.TW",
        "9921.TW",
        "9945.TW",
        "2354.TW",
        "2360.TW",
        "2449.TW",
        "3017.TW",
        "3035.TW",
        "3532.TW",
        "3661.TW",
        "3702.TW",
        "6239.TW",
        "6669.TW",
        "8454.TW",
        "1476.TW",
        "2345.TW",
        "2376.TW",
        "2377.TW",
        "2451.TW",
        "2474.TW",
        "3019.TW",
        "3044.TW",
        "3406.TW",
        "3443.TW",
        "3533.TW",
        "5269.TW",
        "6409.TW",
    ],
}


def load_index_constituents() -> Dict[str, List[str]]:
    """Loads constituents from local cache or defaults."""
    # Always start with defaults to ensure new indices are available
    data = DEFAULT_INDEX_DATA.copy()
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cached = json.load(f)
                # Update with cached data but keep defaults if they are missing
                for k, v in cached.items():
                    data[k] = v
        except Exception:
            pass
    return data


import requests
import re


def update_index_data() -> Dict[str, str]:
    """Updates index data via online sync from formal sources (TWSE, etc.)."""
    results = {}
    new_data = DEFAULT_INDEX_DATA.copy()

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 1. Sync Taiwan 50 (TWSE Official)
    try:
        # TWSE API for Index Constituents
        # TWTB4U is the code for Taiwan 50
        tw50_url = "https://www.twse.com.tw/zh/api/getInduCmp?index=TWTB4U"
        resp = requests.get(tw50_url, headers=headers, timeout=10)
        if resp.status_code == 200 and resp.text.strip():
            try:
                data = resp.json()
                tickers = [f"{row[0]}.TW" for row in data.get("data", []) if len(row) > 0]
                if len(tickers) >= 45:  # Safety check
                    new_data["台股50 (Taiwan 50)"] = tickers
                    results["台股50 (Taiwan 50)"] = (
                        f"✅ Synced {len(tickers)} stocks from TWSE"
                    )
                else:
                    results["台股50 (Taiwan 50)"] = "⚠️ Sync failed: Incomplete data"
            except (json.JSONDecodeError, ValueError) as je:
                results["台股50 (Taiwan 50)"] = f"⚠️ Sync Error: Invalid JSON response"
        else:
            results["台股50 (Taiwan 50)"] = f"⚠️ Sync failed: HTTP {resp.status_code}"
    except requests.exceptions.Timeout:
        results["台股50 (Taiwan 50)"] = "⚠️ Sync Error: Request timeout"
    except requests.exceptions.ConnectionError:
        results["台股50 (Taiwan 50)"] = "⚠️ Sync Error: Network unreachable"
    except Exception as e:
        results["台股50 (Taiwan 50)"] = f"⚠️ Sync Error: {type(e).__name__}"

    # 2. Sync Taiwan Mid 100 (TWSE Official)
    try:
        # TWTB4V is the code for Mid 100
        mid100_url = "https://www.twse.com.tw/zh/api/getInduCmp?index=TWTB4V"
        resp = requests.get(mid100_url, headers=headers, timeout=10)
        if resp.status_code == 200 and resp.text.strip():
            try:
                data = resp.json()
                tickers = [f"{row[0]}.TW" for row in data.get("data", []) if len(row) > 0]
                if len(tickers) >= 90:  # Safety check
                    new_data["台股中型100 (Mid 100)"] = tickers
                    results["台股中型100 (Mid 100)"] = (
                        f"✅ Synced {len(tickers)} stocks from TWSE"
                    )
                else:
                    results["台股中型100 (Mid 100)"] = "⚠️ Sync failed: Incomplete data"
            except (json.JSONDecodeError, ValueError) as je:
                results["台股中型100 (Mid 100)"] = f"⚠️ Sync Error: Invalid JSON response"
        else:
            results["台股中型100 (Mid 100)"] = f"⚠️ Sync failed: HTTP {resp.status_code}"
    except requests.exceptions.Timeout:
        results["台股中型100 (Mid 100)"] = "⚠️ Sync Error: Request timeout"
    except requests.exceptions.ConnectionError:
        results["台股中型100 (Mid 100)"] = "⚠️ Sync Error: Network unreachable"
    except Exception as e:
        results["台股中型100 (Mid 100)"] = f"⚠️ Sync Error: {type(e).__name__}"

    # 3. Sync MSCI Taiwan (Via iShares EWT as reliable proxy)
    try:
        # We search for the current iShares CSV link or use a fallback mechanism
        # For MSCI, formal lists are often paywalled, so we use the ETF holdings
        msci_url = "https://www.blackrock.com/us/individual/products/239682/ishares-msci-taiwan-etf/1464253357814.ajax?fileType=csv&fileName=EWT_holdings&dataType=fund"
        resp = requests.get(msci_url, headers=headers, timeout=15)
        if resp.status_code == 200 and resp.text.strip():
            # Extract 4-digit codes from the CSV content
            content = resp.text
            # Look for patterns like "2330", "2317" which are common Taiwan stock IDs
            # in a CSV format that usually includes the ticker column
            potential_tickers = re.findall(r"(\d{4})\s", content)
            tickers = sorted(
                list(set([f"{t}.TW" for t in potential_tickers if t.isdigit()]))
            )

            if len(tickers) >= 70:
                new_data["MSCI台股指數 (MSCI Taiwan)"] = tickers
                results["MSCI台股指數 (MSCI Taiwan)"] = (
                    f"✅ Synced {len(tickers)} stocks from BlackRock/iShares"
                )
            else:
                results["MSCI台股指數 (MSCI Taiwan)"] = (
                    "⚠️ Sync failed: Could not parse CSV"
                )
        else:
            results["MSCI台股指數 (MSCI Taiwan)"] = f"⚠️ Sync failed: HTTP {resp.status_code}"
    except requests.exceptions.Timeout:
        results["MSCI台股指數 (MSCI Taiwan)"] = "⚠️ Sync Error: Request timeout"
    except requests.exceptions.ConnectionError:
        results["MSCI台股指數 (MSCI Taiwan)"] = "⚠️ Sync Error: Network unreachable"
    except Exception as e:
        results["MSCI台股指數 (MSCI Taiwan)"] = f"⚠️ Sync Error: {type(e).__name__}"

    # Save to cache if any sync was successful
    if any("✅" in v for v in results.values()):
        os.makedirs("data/models", exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(new_data, f)

    # Fill in failures with static status if they weren't synced
    for k in DEFAULT_INDEX_DATA.keys():
        if k not in results:
            results[k] = "📦 Using local cache (sync was not attempted)"

    return results
