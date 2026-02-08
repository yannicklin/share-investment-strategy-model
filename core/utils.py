"""
USA AI Trading System - Utility Functions

Purpose: Date formatting, market calendar management, and helper utilities.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
import pandas_market_calendars as mcal
from typing import Optional
from datetime import datetime


def format_date_with_weekday(dt: pd.Timestamp) -> str:
    """Format pandas Timestamp as YYYY-MM-DD(DAY)."""
    weekday = dt.strftime("%a").upper()
    return f"{dt.strftime('%Y-%m-%d')}({weekday})"


def get_usa_trading_days(
    start_date: pd.Timestamp, end_date: pd.Timestamp, use_cache: bool = True
) -> pd.DatetimeIndex:
    """Fetch USA (NYSE) trading days for specified date range."""
    try:
        if use_cache:
            nyse_calendar = mcal.get_calendar("XNYS")
            schedule = nyse_calendar.schedule(start_date=start_date, end_date=end_date)
            trading_days = schedule.index
        else:
            all_dates = pd.date_range(start=start_date, end=end_date, freq="D")
            trading_days = all_dates[all_dates.dayofweek < 5]
    except Exception:
        all_dates = pd.date_range(start=start_date, end=end_date, freq="D")
        trading_days = all_dates[all_dates.dayofweek < 5]

    return pd.DatetimeIndex(trading_days)


def calculate_trading_days_ahead(
    start_date: pd.Timestamp, num_days: int, trading_days: pd.DatetimeIndex
) -> Optional[pd.Timestamp]:
    """Calculate the date that is `num_days` TRADING DAYS ahead from start_date."""
    try:
        loc_result = trading_days.get_loc(start_date)
        if isinstance(loc_result, int):
            start_idx = loc_result
        else:
            start_idx = 0
    except KeyError:
        future_days = trading_days[trading_days >= start_date]
        if len(future_days) == 0:
            return None
        loc_result = trading_days.get_loc(future_days[0])
        start_idx = loc_result if isinstance(loc_result, int) else 0

    target_idx = int(start_idx) + num_days

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

    min_price = min(price_dict.values())

    if available_cash < min_price:
        return {
            "can_trade": False,
            "affordable_tickers": {},
            "reason": f"Insufficient cash: ${available_cash:.2f} < minimum price ${min_price:.2f}",
        }

    affordable = {}
    for ticker, price in price_dict.items():
        if available_cash >= price:
            max_units = int(available_cash / price)
            affordable[ticker] = max_units

    return {
        "can_trade": True,
        "affordable_tickers": affordable,
        "reason": "",
    }
