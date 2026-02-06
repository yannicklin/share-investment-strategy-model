"""
ASX AI Trading System - Utility Functions

Purpose: Date formatting, market calendar management, and helper utilities.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
import pandas_market_calendars as mcal
from typing import Optional
from datetime import datetime


def format_date_with_weekday(dt: pd.Timestamp) -> str:
    """
    Format pandas Timestamp as YYYY-MM-DD(DAY).
    
    Args:
        dt: Timestamp object (timezone-aware or naive)
    
    Returns:
        String like "2026-02-06(THU)"
    
    Examples:
        >>> format_date_with_weekday(pd.Timestamp("2026-02-06"))
        '2026-02-06(THU)'
        >>> format_date_with_weekday(pd.Timestamp("2026-12-25"))
        '2026-12-25(FRI)'
    """
    weekday = dt.strftime("%a").upper()
    return f"{dt.strftime('%Y-%m-%d')}({weekday})"


def get_asx_trading_days(
    start_date: pd.Timestamp, end_date: pd.Timestamp, use_cache: bool = True
) -> pd.DatetimeIndex:
    """
    Fetch ASX trading days for specified date range (excludes holidays and weekends).
    
    Args:
        start_date: Start date for backtest period
        end_date: End date for backtest period
        use_cache: If True, uses pandas_market_calendars; if False, uses basic weekday filter
    
    Returns:
        DatetimeIndex of valid trading days
    
    Notes:
        - Automatically excludes Saturdays and Sundays
        - Excludes ASX public holidays (Christmas, New Year, Australia Day, etc.)
        - Market half-days (e.g., Christmas Eve) treated as off-days
        - Dynamically fetches holidays for exact date range (no hard-coded year limits)
    """
    try:
        if use_cache:
            # Preferred: Use pandas_market_calendars library
            asx_calendar = mcal.get_calendar("XASX")
            schedule = asx_calendar.schedule(start_date=start_date, end_date=end_date)
            trading_days = schedule.index
        else:
            # Fallback: Basic weekday filtering (no holiday awareness)
            all_dates = pd.date_range(start=start_date, end=end_date, freq="D")
            trading_days = all_dates[all_dates.dayofweek < 5]  # Mon-Fri only
    except Exception:
        # Ultimate fallback: Manual weekday filter
        all_dates = pd.date_range(start=start_date, end=end_date, freq="D")
        trading_days = all_dates[all_dates.dayofweek < 5]
    
    return pd.DatetimeIndex(trading_days)


def calculate_trading_days_ahead(
    start_date: pd.Timestamp, num_days: int, trading_days: pd.DatetimeIndex
) -> Optional[pd.Timestamp]:
    """
    Calculate the date that is `num_days` TRADING DAYS ahead from start_date.
    
    Args:
        start_date: Starting date (must be a valid trading day)
        num_days: Number of trading days to count forward
        trading_days: Pre-filtered DatetimeIndex of valid trading days
    
    Returns:
        Timestamp of the target date, or None if insufficient trading days available
    
    Examples:
        >>> trading_days = get_asx_trading_days(
        ...     pd.Timestamp("2026-01-01"), pd.Timestamp("2026-12-31")
        ... )
        >>> calculate_trading_days_ahead(
        ...     pd.Timestamp("2026-02-03"), 30, trading_days
        ... )
        Timestamp('2026-03-20 00:00:00')  # 30 trading days later
    """
    # Find index of start_date in trading_days
    try:
        loc_result = trading_days.get_loc(start_date)
        # get_loc can return int, slice, or boolean array - we want int
        if isinstance(loc_result, int):
            start_idx = loc_result
        else:
            # If slice or array, get the first index
            start_idx = 0
    except KeyError:
        # start_date not in trading_days (e.g., weekend/holiday)
        # Find next valid trading day
        future_days = trading_days[trading_days >= start_date]
        if len(future_days) == 0:
            return None
        loc_result = trading_days.get_loc(future_days[0])
        start_idx = loc_result if isinstance(loc_result, int) else 0
    
    target_idx = int(start_idx) + num_days
    
    if target_idx >= len(trading_days):
        return None  # Not enough trading days available
    
    return pd.Timestamp(trading_days[target_idx])


def validate_buy_capacity(
    available_cash: float, price_dict: dict
) -> dict:
    """
    Check if portfolio has sufficient cash to afford any tickers.
    
    Args:
        available_cash: Current portfolio cash balance
        price_dict: {ticker: current_price} mapping
    
    Returns:
        {
            "can_trade": bool,  # True if can afford at least one ticker
            "affordable_tickers": dict,  # {ticker: max_units}
            "reason": str  # Explanation if can_trade is False
        }
    
    Examples:
        >>> validate_buy_capacity(10000, {"ABB.AX": 15.25, "SIG.AX": 55.0})
        {
            'can_trade': True,
            'affordable_tickers': {'ABB.AX': 655, 'SIG.AX': 181},
            'reason': ''
        }
        >>> validate_buy_capacity(50, {"ABB.AX": 55.0})
        {
            'can_trade': False,
            'affordable_tickers': {},
            'reason': 'Insufficient cash: $50.00 < minimum price $55.00'
        }
    """
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
