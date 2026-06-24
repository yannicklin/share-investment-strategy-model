"""
USA (NYSE/NASDAQ) Market Data Helper

Purpose: Fetch USA stock market data via Alpaca paper account API.

Implementation:
- Primary: Alpaca paper account REST API (production-grade, no rate limits)
- Fallback: yfinance (if Alpaca unavailable)

Alpaca provides:
- Real-time and historical OHLCV data
- Better reliability than yfinance (no rate limit issues)
- Proper data handling for tech stocks, fractional shares, etc.

Usage:
    1. Set ALPACA_API_KEY and ALPACA_SECRET_KEY in environment
    2. API automatically uses paper account (https://paper-api.alpaca.markets)
    3. If Alpaca fails, fallback to yfinance automatically
"""

import logging
import os
from datetime import datetime
from typing import Optional

import pandas as pd
import yfinance as yf

from .base_data_helper import BaseDataHelper

logger = logging.getLogger(__name__)


class USADataHelper(BaseDataHelper):
    """USA market data helper using Alpaca paper account API."""

    market = "USA"

    def __init__(self):
        """Initialize Alpaca client if credentials available."""
        self._alpaca_client = None
        self._alpaca_available = False
        self._init_alpaca()

    def _init_alpaca(self):
        """Initialize Alpaca client with credentials from environment."""
        try:
            api_key = os.getenv("ALPACA_API_KEY")
            secret_key = os.getenv("ALPACA_SECRET_KEY")

            if not api_key or not secret_key:
                logger.debug(
                    "Alpaca credentials not found. Set ALPACA_API_KEY and ALPACA_SECRET_KEY. "
                    "Using yfinance fallback."
                )
                self._alpaca_available = False
                return

            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.timeframe import TimeFrame

            # Initialize Alpaca client (paper trading)
            self._alpaca_client = StockHistoricalDataClient(
                api_key=api_key, secret_key=secret_key
            )
            self._stock_bars_request = StockBarsRequest
            self._timeframe = TimeFrame
            self._alpaca_available = True
            logger.info("✅ Alpaca client initialized successfully")

        except ImportError:
            logger.debug(
                "alpaca-trade-api not installed. Install with: pip install alpaca-trade-api"
            )
            self._alpaca_available = False
        except Exception as e:
            logger.debug(
                f"Failed to initialize Alpaca client: {e}. Using yfinance fallback."
            )
            self._alpaca_available = False

    def _fetch_alpaca(
        self, ticker: str, start_date: datetime, end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Fetch data from Alpaca API.

        Args:
            ticker: Stock symbol (e.g., "AAPL", "MSFT")
            start_date: Start date (datetime or pd.Timestamp)
            end_date: End date (datetime or pd.Timestamp)

        Returns:
            DataFrame with OHLCV data or None if failed
        """
        if not self._alpaca_available or not self._alpaca_client:
            return None

        try:
            # Convert to datetime if pd.Timestamp
            if isinstance(start_date, pd.Timestamp):
                start_date = start_date.to_pydatetime()
            if isinstance(end_date, pd.Timestamp):
                end_date = end_date.to_pydatetime()

            # Create request
            request = self._stock_bars_request(
                symbol_or_symbols=ticker,
                timeframe=self._timeframe.Day,
                start=start_date,
                end=end_date,
                limit=None,  # Fetch all available data
            )

            # Fetch bars
            bars = self._alpaca_client.get_stock_bars(request)

            if not bars or ticker not in bars:
                logger.debug(f"No Alpaca data for {ticker}")
                return None

            # Convert to DataFrame
            data = bars[ticker]
            df = pd.DataFrame(
                {
                    "Open": [bar.open for bar in data],
                    "High": [bar.high for bar in data],
                    "Low": [bar.low for bar in data],
                    "Close": [bar.close for bar in data],
                    "Volume": [int(bar.volume) for bar in data],
                },
                index=[bar.timestamp.date() for bar in data],
            )

            df.index.name = "Date"
            df.index = pd.to_datetime(df.index)

            logger.debug(
                f"✅ Fetched {len(df)} bars from Alpaca for {ticker} "
                f"({df.index[0].date()} to {df.index[-1].date()})"
            )
            return df

        except Exception as e:
            logger.debug(f"Alpaca fetch failed for {ticker}: {e}")
            return None

    def _fetch_yfinance(
        self, ticker: str, start_date: pd.Timestamp, end_date: pd.Timestamp
    ) -> pd.DataFrame:
        """Fetch data from yfinance as fallback.

        Args:
            ticker: Stock symbol (e.g., "AAPL", "MSFT")
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with OHLCV data or empty DataFrame on failure
        """
        try:
            df = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                auto_adjust=True,
                progress=False,
                threads=False,
            )

            if not df.empty:
                logger.debug(
                    f"Fetched {len(df)} bars from yfinance for {ticker} "
                    f"(fallback from Alpaca)"
                )
            return df

        except Exception as e:
            logger.error(f"yfinance fallback also failed for {ticker}: {e}")
            return pd.DataFrame()

    def fetch_historical_data(
        self, ticker: str, start_date: pd.Timestamp, end_date: pd.Timestamp
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data (primary method for backtesting).

        Args:
            ticker: Stock symbol (e.g., "AAPL", "MSFT")
            start_date: Start date for data fetch
            end_date: End date for data fetch

        Returns:
            DataFrame with OHLCV data (Close, Open, High, Low, Volume)
        """
        # Try Alpaca first
        if self._alpaca_available:
            df = self._fetch_alpaca(ticker, start_date, end_date)
            if df is not None and not df.empty:
                return df

        # Fallback to yfinance
        logger.debug(f"Falling back to yfinance for {ticker}")
        return self._fetch_yfinance(ticker, start_date, end_date)

    def is_data_available(self) -> bool:
        """Check if USA data source is available (Alpaca or yfinance).

        Always True because yfinance fallback is always available.
        """
        return True
