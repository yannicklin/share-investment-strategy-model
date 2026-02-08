"""
USA AI Trading System - Utility Functions

Purpose: Date formatting, market calendar management, and helper utilities.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
import pandas_market_calendars as mcal
import numpy as np
from typing import Optional, Any


def format_date_with_weekday(dt: Any) -> str:
    """Format pandas Timestamp as YYYY-MM-DD(DAY)."""
    ts = pd.Timestamp(dt)
    if pd.isna(ts):
        return "N/A"
    weekday = ts.strftime("%a").upper()
    return f"{ts.strftime('%Y-%m-%d')}({weekday})"


def get_usa_trading_days(
    start_date: Any, end_date: Any, use_cache: bool = True
) -> pd.DatetimeIndex:
    """Fetch USA (NYSE) trading days for specified date range."""
    s = pd.Timestamp(start_date)
    e = pd.Timestamp(end_date)

    try:
        if use_cache:
            nyse_calendar = mcal.get_calendar("XNYS")
            schedule = nyse_calendar.schedule(start_date=s, end_date=e)
            if schedule.empty:
                all_dates: Any = pd.date_range(start=s, end=e, freq="D")
                trading_days = all_dates[all_dates.dayofweek < 5]
            else:
                idx: Any = pd.to_datetime(schedule.index)
                trading_days = idx.tz_localize(None).normalize()
        else:
            all_dates: Any = pd.date_range(start=s, end=e, freq="D")
            trading_days = all_dates[all_dates.dayofweek < 5]
    except Exception:
        all_dates: Any = pd.date_range(start=s, end=e, freq="D")
        trading_days = all_dates[all_dates.dayofweek < 5]

    return pd.DatetimeIndex(trading_days).unique()


def calculate_trading_days_ahead(
    start_date: Any, num_days: int, trading_days: pd.DatetimeIndex
) -> Optional[pd.Timestamp]:
    """Calculate the date that is `num_days` TRADING DAYS ahead from start_date."""
    s = pd.Timestamp(start_date)
    if pd.isna(s):
        return None

    s = s.tz_localize(None).normalize()

    try:
        loc_result = trading_days.get_loc(s)
        if isinstance(loc_result, (int, np.integer)):
            start_idx = int(loc_result)
        elif isinstance(loc_result, slice):
            start_idx = int(loc_result.start)
        else:
            start_idx = 0
    except (KeyError, Exception):
        future_days = trading_days[trading_days >= s]
        if len(future_days) == 0:
            return None
        loc_result = trading_days.get_loc(future_days[0])
        if isinstance(loc_result, (int, np.integer)):
            start_idx = int(loc_result)
        elif isinstance(loc_result, slice):
            start_idx = int(loc_result.start)
        else:
            start_idx = 0

    target_idx = start_idx + num_days

    if target_idx >= len(trading_days):
        return None

    return pd.Timestamp(trading_days[target_idx])


def validate_buy_capacity(available_cash: float, price_dict: dict) -> dict:
    """Check if portfolio has sufficient cash to afford any tickers."""
    if not price_dict:
        return {
            "can_trade": False,
            "affordable_tickers": {},
            "reason": "No tickers provided",
        }

    min_price = float(min(price_dict.values()))

    if available_cash < min_price:
        return {
            "can_trade": False,
            "affordable_tickers": {},
            "reason": f"Insufficient cash: ${available_cash:.2f} < minimum price ${min_price:.2f}",
        }

    affordable = {}
    for ticker, price in price_dict.items():
        p = float(price)
        if available_cash >= p:
            max_units = int(available_cash / p)
            affordable[ticker] = max_units

    return {
        "can_trade": True,
        "affordable_tickers": affordable,
        "reason": "",
    }
