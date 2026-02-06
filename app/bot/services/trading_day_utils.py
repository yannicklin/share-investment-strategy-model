"""
AI Trading Bot System - Trading Day Validation Utilities

Purpose: Market calendar management and trading day validation for bot automation.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
import pandas_market_calendars as mcal
from datetime import datetime, date
from typing import Optional


def get_trading_days(
    market: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    use_cache: bool = True
) -> pd.DatetimeIndex:
    """
    Fetch trading days for specified market and date range (excludes holidays and weekends).
    
    Args:
        market: Market code ('ASX', 'USA', 'TWN')
        start_date: Start date for period
        end_date: End date for period
        use_cache: If True, uses pandas_market_calendars; if False, uses basic weekday filter
    
    Returns:
        DatetimeIndex of valid trading days
    
    Notes:
        - Automatically excludes Saturdays and Sundays
        - Excludes market-specific public holidays
        - Market half-days treated as off-days
        - Dynamically fetches holidays for exact date range
    """
    # Map market codes to calendar codes
    calendar_map = {
        'ASX': 'XASX',  # Australian Securities Exchange
        'USA': 'NYSE',  # New York Stock Exchange
        'TWN': 'XTAI',  # Taiwan Stock Exchange
    }
    
    calendar_code = calendar_map.get(market)
    
    try:
        if use_cache and calendar_code:
            # Preferred: Use pandas_market_calendars library
            calendar = mcal.get_calendar(calendar_code)
            schedule = calendar.schedule(start_date=start_date, end_date=end_date)
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


def is_trading_day(market: str, check_date: Optional[date] = None) -> bool:
    """
    Check if a specific date is a trading day for the given market.
    
    Args:
        market: Market code ('ASX', 'USA', 'TWN')
        check_date: Date to check (defaults to today)
    
    Returns:
        True if the date is a trading day, False otherwise
    
    Examples:
        >>> is_trading_day('ASX', date(2026, 2, 6))  # Thursday
        True
        >>> is_trading_day('ASX', date(2026, 2, 8))  # Saturday
        False
        >>> is_trading_day('ASX', date(2026, 1, 1))  # New Year's Day
        False
    """
    if check_date is None:
        check_date = date.today()
    
    # Convert to pandas Timestamp
    check_ts = pd.Timestamp(check_date)
    
    # Get trading days for a window around the check date
    # (use a 7-day window to avoid edge cases)
    start = check_ts - pd.Timedelta(days=3)
    end = check_ts + pd.Timedelta(days=3)
    
    trading_days = get_trading_days(market, start, end)
    
    # Check if check_date is in the trading days
    return check_ts in trading_days


def get_next_trading_day(market: str, from_date: Optional[date] = None) -> date:
    """
    Get the next trading day for the given market.
    
    Args:
        market: Market code ('ASX', 'USA', 'TWN')
        from_date: Starting date (defaults to today)
    
    Returns:
        Next trading day as date object
    
    Examples:
        >>> get_next_trading_day('ASX', date(2026, 2, 7))  # Friday
        datetime.date(2026, 2, 9)  # Monday (skip weekend)
    """
    if from_date is None:
        from_date = date.today()
    
    # Convert to pandas Timestamp
    from_ts = pd.Timestamp(from_date)
    
    # Get trading days for next 30 days
    end = from_ts + pd.Timedelta(days=30)
    trading_days = get_trading_days(market, from_ts, end)
    
    # Find first trading day after from_date
    future_days = trading_days[trading_days > from_ts]
    
    if len(future_days) == 0:
        raise ValueError(f"No trading days found in next 30 days from {from_date}")
    
    return future_days[0].date()


def calculate_trading_days_ahead(
    market: str,
    start_date: pd.Timestamp,
    num_days: int,
) -> Optional[pd.Timestamp]:
    """
    Calculate the date that is `num_days` TRADING DAYS ahead from start_date.
    
    Args:
        market: Market code ('ASX', 'USA', 'TWN')
        start_date: Starting date
        num_days: Number of trading days to count forward
    
    Returns:
        Timestamp of the target date, or None if insufficient trading days available
    
    Examples:
        >>> calculate_trading_days_ahead('ASX', pd.Timestamp("2026-02-03"), 30)
        Timestamp('2026-03-20 00:00:00')  # 30 trading days later
    """
    # Get trading days for a reasonable window
    end_estimate = start_date + pd.Timedelta(days=num_days * 2)  # Account for weekends/holidays
    trading_days = get_trading_days(market, start_date, end_estimate)
    
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
