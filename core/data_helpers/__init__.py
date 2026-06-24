"""
Market-Specific Data Helper Factory

Provides unified interface for fetching market-specific data
for USA market via Alpaca or yfinance fallback.

Usage:
    >>> from core.data_helpers import get_data_helper
    >>> helper = get_data_helper('USA')
    >>> df = helper.fetch_historical_data(ticker, start_date, end_date)
"""

_HELPER_CACHE = {}


def get_data_helper(market: str):
    """
    Factory function to get the appropriate data helper for a market.

    Args:
        market: Market code ('USA')

    Returns:
        Data helper instance for the specified market

    Raises:
        ValueError: If market not supported
    """
    market = market.upper()

    if market in _HELPER_CACHE:
        return _HELPER_CACHE[market]

    if market == "USA":
        from .usa_data_helper import USADataHelper

        helper = USADataHelper()
    else:
        raise ValueError(f"Unsupported market: {market}. Must be USA.")

    _HELPER_CACHE[market] = helper
    return helper


__all__ = ["get_data_helper"]
