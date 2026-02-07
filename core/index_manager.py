"""
Taiwan Stock AI Trading System - Index Manager

Purpose: Manages Taiwan index constituents with live updates and caching
for Taiwan 50 (0050) and other custom lists.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
import json
import os
import re
import requests
from typing import List, Dict

CACHE_FILE = "data/models/index_cache.json"

# Note: Scraping TWSE directly requires handling complex POST requests or JS.
# We'll use a curated default list for Taiwan 50.
SOURCE_URLS = {
    "Taiwan 50": "https://www.twse.com.tw/zh/indices/index/MS",  # Placeholder
}

DEFAULT_INDEX_DATA = {
    "Taiwan 50": [
        "2330.TW",
        "2317.TW",
        "2454.TW",
        "2308.TW",
        "2303.TW",
        "2881.TW",
        "2882.TW",
        "2412.TW",
        "2382.TW",
        "3711.TW",
        "2886.TW",
        "2891.TW",
        "1301.TW",
        "1303.TW",
        "1216.TW",
        "2002.TW",
        "2884.TW",
        "2885.TW",
        "2357.TW",
        "2327.TW",
        "3008.TW",
        "3231.TW",
        "2379.TW",
        "5880.TW",
        "2892.TW",
        "2880.TW",
        "2395.TW",
        "2883.TW",
        "2912.TW",
        "1101.TW",
        "2603.TW",
        "1326.TW",
        "2890.TW",
        "2301.TW",
        "3045.TW",
        "2408.TW",
        "2207.TW",
        "5871.TW",
        "2609.TW",
        "2345.TW",
        "1590.TW",
        "2615.TW",
        "2376.TW",
        "3034.TW",
        "2474.TW",
        "4938.TW",
        "9910.TW",
        "2377.TW",
        "2409.TW",
        "3481.TW",
    ],
    "Taiwan ETFs": ["0050.TW", "0056.TW", "00878.TW", "00919.TW", "00929.TW"],
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
    """Fetches latest constituents. (Manual update recommended for Taiwan)"""
    # For Taiwan branch, we maintain the curated list manually due to TWSE anti-scraping.
    updated_counts = {
        "Taiwan 50": "Curated list maintained manually.",
        "Taiwan ETFs": "Curated list maintained manually.",
    }

    os.makedirs("data/models", exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(DEFAULT_INDEX_DATA, f)

    return updated_counts
