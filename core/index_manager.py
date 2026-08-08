"""
Taiwan Stock AI Trading System - Index Manager

Purpose: Manages Taiwan index constituents (TWSE 50, etc.) with caching.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import json
import os

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


def load_index_constituents() -> dict[str, list[str]]:
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


import re

import pandas as pd
import requests


def update_index_data() -> dict[str, str]:
    """Returns current index data status.

    NOTE: External data sources (Yahoo Finance, BlackRock, TWSE API) are
    currently blocked or returning 404 errors. System uses local cache only.

    This function is retained for future use when sources become available.
    """
    results = {}
    new_data = DEFAULT_INDEX_DATA.copy()

    # All external sources blocked - return cache status only
    results["台股50 (Taiwan 50)"] = "📦 Using local cache (Yahoo Finance blocked)"
    results["台股中型100 (Mid 100)"] = "📦 Using local cache (TWSE API blocked)"
    results["MSCI台股指數 (MSCI Taiwan)"] = "📦 Using local cache (BlackRock blocked)"

    return results