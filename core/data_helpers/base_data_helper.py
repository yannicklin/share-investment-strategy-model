"""
Abstract Base Class for Market-Specific Data Helpers

Defines the interface that all market-specific data helper implementations
must follow.
"""

from abc import ABC, abstractmethod

import pandas as pd


class BaseDataHelper(ABC):
    """
    Abstract base class for market-specific data fetching helpers.

    Subclasses implement market-specific data fetching logic (e.g., Alpaca for USA).
    """

    market: str  # 'USA' (set by subclasses)

    @abstractmethod
    def fetch_historical_data(
        self,
        ticker: str,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data.

        Args:
            ticker: Stock symbol (e.g., "AAPL", "MSFT")
            start_date: Start date for data fetch
            end_date: End date for data fetch

        Returns:
            DataFrame with OHLCV data (Close, Open, High, Low, Volume)
            or empty DataFrame if fetch fails
        """

    @abstractmethod
    def is_data_available(self) -> bool:
        """
        Check if data source is available.

        Returns:
            bool: True if data source is available, False otherwise
        """
