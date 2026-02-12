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

CACHE_FILE = "data/models/index_cache.json"

DEFAULT_INDEX_DATA = {
    "Taiwan 50": [
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
    """Updates index data. For Taiwan, we use the hardcoded list as primary source."""
    new_data = DEFAULT_INDEX_DATA

    os.makedirs("data/models", exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(new_data, f)

    return {"Taiwan 50": "Loaded from static list"}
