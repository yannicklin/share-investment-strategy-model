"""Taiwan Stock AI Trading System - Model Builder

Factory for ML models with multi-scaler groups, log-normalization, and feature mapping.
See docs/MULTI_SCALER_AND_LOG_NORMALIZATION_ARCHITECTURE.md for architecture details.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import logging
import os
import time
from typing import Any

import joblib
import numpy as np
import pandas as pd
import yfinance as yf

# Try to use curl-cffi for rate limit bypass
try:
    from curl_cffi import requests as cf_requests

    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

# Try to import FinMind for Taiwan institutional data
try:
    from FinMind.data import DataLoader

    FINMIND_AVAILABLE = True
except ImportError:
    FINMIND_AVAILABLE = False
    logging.warning("FinMind not available. Taiwan institutional features disabled.")

# Suppress heavy logging and warnings from backends
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["STAN_LOG_LEVEL"] = "ERROR"
os.environ["CMDSTANPY_LOG_LEVEL"] = "ERROR"

try:
    import tensorflow as tf

    tf.get_logger().setLevel("ERROR")
    # Suppress retracing warnings
    tf.autograph.set_verbosity(0)
except ImportError:
    pass

logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
logging.getLogger("prophet").setLevel(logging.ERROR)
logging.getLogger("FinMind").setLevel(logging.ERROR)
logging.getLogger("FinMind.data").setLevel(logging.ERROR)
logging.getLogger("FinMind.data.finmind_api").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import (
    MinMaxScaler,
    QuantileTransformer,
    RobustScaler,
)

from core.config import Config

FINMIND_FEATURE_COLUMNS = [
    "FM_Foreign_NetBuy",
    "FM_Trust_NetBuy",
    "FM_Dealer_NetBuy",
    "FM_Margin_Balance",
    "FM_Short_Balance",
    "FM_Revenue_YoY",
]


class ModelBuilder:
    """Handles data fetching, preprocessing, and model training."""

    def __init__(self, config: Config):
        self.config = config
        self.model: Any | None = None
        self.price_scaler: Any | None = None
        self.volume_scaler: Any | None = None
        self.technical_scaler: Any | None = None
        self.scaler: Any | None = None
        self.target_scaler: Any | None = None
        self.close_was_log_normalized: bool = False
        self.sequence_length = 30
        self.target_horizon_days = 1
        self._data_cache: dict[str, pd.DataFrame] = {}
        self._market_data: pd.DataFrame | None = None
        self._company_name_cache: dict[str, str] = {}
        self._etf_cache: dict[str, bool] = {}
        self._finmind_data: pd.DataFrame | None = None
        self._finmind_data_cache: dict[str, pd.DataFrame] = {}
        self._stock_info_cache: pd.DataFrame | None = None
        self._price_feature_indices: list[int] = []
        self._volume_feature_indices: list[int] = []
        self._technical_feature_indices: list[int] = []

    def _init_scalers(self, n_samples: int | None = None) -> dict[str, Any]:
        """Initialize multi-scaler groups. See docs for architecture."""
        if n_samples is not None:
            n_quantiles = max(10, min(1000, n_samples - 1))
        else:
            n_quantiles = 500

        return {
            "price_scaler": MinMaxScaler(feature_range=(0.1, 0.9)),
            "volume_scaler": QuantileTransformer(
                output_distribution="normal", n_quantiles=n_quantiles, random_state=42
            ),
            "technical_scaler": RobustScaler(),
            "target_scaler": MinMaxScaler(feature_range=(0.1, 0.9)),
        }

    def _get_feature_group_indices(self, feature_list: list[str]) -> None:
        """Map feature columns to scaler groups."""
        price_features = {"Open", "High", "Low", "Close", "BB_Upper", "BB_Lower"}
        volume_features = {"Volume"}
        technical_features = {
            "MA5",
            "MA20",
            "MA50",
            "RSI",
            "MACD",
            "Signal_Line",
            "BB_Width",
            "ATR",
            "Daily_Return",
        }

        self._price_feature_indices = [
            i for i, f in enumerate(feature_list) if f in price_features
        ]
        self._volume_feature_indices = [
            i for i, f in enumerate(feature_list) if f in volume_features
        ]
        self._technical_feature_indices = [
            i for i, f in enumerate(feature_list) if f in technical_features
        ]

    def _apply_multi_scalers_fit(self, X: np.ndarray) -> np.ndarray:
        """Fit scalers on respective feature groups."""
        X_scaled = X.copy()

        if self._price_feature_indices:
            X_scaled[:, self._price_feature_indices] = self.price_scaler.fit_transform(
                X[:, self._price_feature_indices]
            )

        if self._volume_feature_indices:
            X_scaled[:, self._volume_feature_indices] = (
                self.volume_scaler.fit_transform(X[:, self._volume_feature_indices])
            )

        if self._technical_feature_indices:
            X_scaled[:, self._technical_feature_indices] = (
                self.technical_scaler.fit_transform(
                    X[:, self._technical_feature_indices]
                )
            )

        return X_scaled

    def _apply_multi_scalers_transform(self, X: np.ndarray) -> np.ndarray:
        """Transform feature matrix using fitted scalers."""
        X_scaled = X.copy()

        if self._price_feature_indices:
            X_scaled[:, self._price_feature_indices] = self.price_scaler.transform(
                X[:, self._price_feature_indices]
            )

        if self._volume_feature_indices:
            X_scaled[:, self._volume_feature_indices] = self.volume_scaler.transform(
                X[:, self._volume_feature_indices]
            )

        if self._technical_feature_indices:
            X_scaled[:, self._technical_feature_indices] = (
                self.technical_scaler.transform(X[:, self._technical_feature_indices])
            )

        return X_scaled

    def _calculate_sample_weights(self, n_samples: int) -> np.ndarray:
        """
        Calculate sample weights based on weighting type.
        For recency weighting: exponential decay with half-life = backtest_years * recency_half_life_multiplier
        """
        if self.config.weighting_type == "normal":
            # Uniform weights
            return np.ones(n_samples)

        # Recency weighting with exponential decay
        half_life = (
            self.config.backtest_years * self.config.recency_half_life_multiplier
        )
        lambda_decay = np.log(2) / half_life  # Decay constant

        # Time indices: 0 (oldest) to n_samples-1 (newest)
        time_indices = np.arange(n_samples)
        max_time = n_samples - 1

        # Exponential decay: w_i = exp(-lambda * (t_max - t_i))
        weights = np.exp(-lambda_decay * (max_time - time_indices))

        # Normalize to [0, 1] range with max weight = 1
        weights = weights / np.max(weights)

        return weights

    def _download_with_retry(
        self, ticker: str, start_date, max_retries: int = 3, base_delay: float = 2.0
    ) -> pd.DataFrame:
        """Download data with exponential backoff retry and curl-cffi session support."""

        # Create curl-cffi session if available
        session = None
        if CURL_CFFI_AVAILABLE:
            try:
                # Use environment CURL_IMPERSONATE or default to chrome131
                impersonate = os.environ.get("CURL_IMPERSONATE", "chrome131")
                session = cf_requests.Session(impersonate=impersonate)
            except Exception as e:
                logging.warning(f"Failed to create curl-cffi session: {e}")

        for attempt in range(max_retries):
            try:
                # Add small delay between attempts to avoid rate limits
                if attempt > 0:
                    delay = base_delay * (2**attempt) + (
                        0.5 * attempt
                    )  # Exponential backoff
                    logging.info(
                        f"Retry {attempt + 1}/{max_retries} for {ticker} after {delay:.1f}s delay..."
                    )
                    time.sleep(delay)

                # Download with optional curl-cffi session
                df = yf.download(
                    ticker,
                    start=start_date,
                    progress=False,
                    auto_adjust=True,
                    threads=False,
                    session=session if session else None,
                )

                if not df.empty:
                    return df

            except Exception as e:
                error_msg = str(e)
                if "Rate limit" in error_msg or "Too Many Requests" in error_msg:
                    if attempt < max_retries - 1:
                        logging.warning(f"Rate limit hit for {ticker}, will retry...")
                        continue
                    else:
                        logging.error(
                            f"Rate limit exceeded for {ticker} after {max_retries} attempts"
                        )
                else:
                    logging.error(f"Download failed for {ticker}: {e}")
                    break

        return pd.DataFrame()

    @classmethod
    def get_available_models(cls) -> list[str]:
        """Returns a list of models that have their dependencies installed."""
        available = ["random_forest"]

        try:
            from ngboost import NGBRegressor

            available.append("ngboost")
        except (ImportError, Exception):
            pass

        try:
            from catboost import CatBoostRegressor

            available.append("catboost")
        except (ImportError, Exception):
            pass

        try:
            from prophet import Prophet

            available.append("prophet")
        except (ImportError, Exception):
            pass

        try:
            import tensorflow as tf

            available.append("lstm")
        except (ImportError, Exception):
            pass

        return available

    def _init_model(self, input_dim: int = 0) -> Any:
        m_type = self.config.model_type

        if m_type == "ngboost":
            from ngboost import NGBRegressor

            logging.info("Initialized NGBoost model.")
            return NGBRegressor(
                n_estimators=100,
                learning_rate=0.01,
                random_state=42,
                verbose=False,
            )

        elif m_type == "catboost":
            from catboost import CatBoostRegressor

            logging.info("Initialized CatBoost model.")
            return CatBoostRegressor(
                n_estimators=100,
                learning_rate=0.05,
                random_state=42,
                verbose=0,
                thread_count=-1,
                allow_writing_files=False,
            )

        elif m_type == "prophet":
            from prophet import Prophet

            logging.info("Initialized Prophet model.")
            return Prophet(daily_seasonality=True, yearly_seasonality=True)

        elif m_type == "lstm":
            from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
            from tensorflow.keras.models import Sequential

            logging.info("Initialized LSTM model.")
            model = Sequential(
                [
                    Input(shape=(self.sequence_length, input_dim)),
                    LSTM(32, return_sequences=True),
                    Dropout(0.1),
                    LSTM(16, return_sequences=False),
                    Dense(8, activation="relu"),
                    Dense(1),
                ]
            )
            model.compile(optimizer="adam", loss="mean_squared_error")
            return model

        logging.info("Initialized RandomForest model.")
        return RandomForestRegressor(n_estimators=100, random_state=42)

    def _normalize_df(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """Forces any yfinance response into a clean, flat TitleCase DataFrame."""
        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            return pd.DataFrame()

        data = df.copy()

        # 1. Handle MultiIndex (Ticker/Price complexity)
        if isinstance(data.columns, pd.MultiIndex):
            # Try to extract the specific ticker level
            for i in range(data.columns.nlevels):
                if ticker in data.columns.get_level_values(i):
                    data = data.xs(ticker, axis=1, level=i)
                    break

            # If still MultiIndex, collapse it
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = [
                    str(c[0]) if isinstance(c, tuple) else str(c) for c in data.columns
                ]

        # 2. Force Flat String Columns and Clean names
        data.columns = [str(c).strip() for c in data.columns]

        # 3. Handle 'Ticker.Price' format
        new_cols = []
        for c in data.columns:
            if "." in c and ticker.lower() in c.lower():
                new_cols.append(c.split(".")[-1])
            else:
                new_cols.append(c)
        data.columns = new_cols

        # 4. Final Standardization Map
        name_map = {
            "close": "Close",
            "adj close": "Close",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "volume": "Volume",
        }

        mapping = {}
        for c in data.columns:
            low_c = c.lower()
            if low_c in name_map:
                mapping[c] = name_map[low_c]

        if mapping:
            data.rename(columns=mapping, inplace=True)

        # 5. Strict Deduplication & Type Casting
        data = data.loc[:, ~data.columns.duplicated()]
        for col in ["Close", "Open", "High", "Low", "Volume"]:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors="coerce")

        return data

    @staticmethod
    def _is_taiwan_ticker(ticker: str) -> bool:
        ticker_upper = ticker.upper().strip()
        return ticker_upper.endswith(".TW") or ticker_upper.endswith(".TWO")

    @staticmethod
    def _base_ticker_symbol(ticker: str) -> str:
        return ticker.split(".")[0].strip() if "." in ticker else ticker.strip()

    def get_company_name(self, ticker: str) -> str:
        """Fetches the long name of the company from yfinance."""
        if ticker in self._company_name_cache:
            return self._company_name_cache[ticker]

        if self._is_taiwan_ticker(ticker):
            chinese_name = self.get_chinese_name(ticker)
            company_name = chinese_name or self._base_ticker_symbol(ticker)
            self._company_name_cache[ticker] = company_name
            return company_name

        try:
            info = yf.Ticker(ticker).info
            company_name = info.get("longName", ticker)
            self._company_name_cache[ticker] = company_name
            return company_name
        except Exception:
            self._company_name_cache[ticker] = ticker
            return ticker

    def get_chinese_name(self, ticker: str) -> str:
        """Fetches the Chinese name of the Taiwan stock from FinMind."""
        if not ticker.endswith(".TW"):
            return ""

        stock_id = ticker.replace(".TW", "")

        try:
            if self._stock_info_cache is None:
                if FINMIND_AVAILABLE:
                    dl = DataLoader()
                    self._stock_info_cache = dl.taiwan_stock_info()
                else:
                    return ""

            if self._stock_info_cache is not None and not self._stock_info_cache.empty:
                # Filter by stock_id
                match = self._stock_info_cache[
                    self._stock_info_cache["stock_id"] == stock_id
                ]
                if not match.empty:
                    return str(match["stock_name"].iloc[0])

        except Exception as e:
            self._stock_info_cache = pd.DataFrame()
            logging.warning(f"Failed to fetch Chinese name for {ticker}: {e}")

        return ""

    def is_etf(self, ticker: str) -> bool:
        """Determines if a ticker is an ETF using yfinance info."""
        if ticker in self._etf_cache:
            return self._etf_cache[ticker]

        if self._is_taiwan_ticker(ticker):
            self._etf_cache[ticker] = False
            return False

        try:
            # We don't want to call .info for every run, so we might want a small cache
            # or just rely on the quoteType if we had it.
            # For now, a quick fetch is fine as it's only called during rendering once per ticker.
            info = yf.Ticker(ticker).info
            is_etf = info.get("quoteType") == "ETF"
            self._etf_cache[ticker] = is_etf
            return is_etf
        except Exception:
            self._etf_cache[ticker] = False
            return False

    def get_data_cache_snapshot(self) -> dict[str, pd.DataFrame]:
        """Return a shallow copy of the current data cache for worker reuse."""
        return dict(self._data_cache)

    def set_data_cache_snapshot(self, data_cache: dict[str, pd.DataFrame]) -> None:
        """Replace the local cache with a shallow copy of a shared snapshot."""
        self._data_cache = dict(data_cache)

    def set_cached_market_data(self, market_data: pd.DataFrame | None) -> None:
        """Prime the market data cache from an existing DataFrame snapshot."""
        self._market_data = market_data

    def get_finmind_cache_snapshot(self) -> dict[str, pd.DataFrame]:
        """Return a shallow copy of the current per-ticker FinMind cache."""
        return {ticker: df.copy() for ticker, df in self._finmind_data_cache.items()}

    def set_finmind_cache_snapshot(
        self, finmind_cache: dict[str, pd.DataFrame]
    ) -> None:
        """Prime the local per-ticker FinMind cache from a shared snapshot."""
        self._finmind_data_cache = {
            ticker: df.copy() for ticker, df in finmind_cache.items()
        }

    def fetch_data(self, ticker: str, years: int) -> pd.DataFrame:
        cache_key = f"{ticker}_{years}"
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]

        end_date = pd.Timestamp.now()
        # Add a 60-day warm-up buffer (approx 2 months of trading days)
        # so that indicators and LSTM sequences are ready on the actual start date.
        start_date = end_date - pd.DateOffset(years=years) - pd.DateOffset(days=90)

        data = self._download_with_retry(ticker, start_date)
        if not data.empty:
            norm = self._normalize_df(data, ticker)
            self._data_cache[cache_key] = norm
            return norm

        return pd.DataFrame()

    def prefetch_data_batch(self, tickers: list[str], years: int):
        if not tickers:
            return
        end_date = pd.Timestamp.now()
        start_date = end_date - pd.DateOffset(years=years) - pd.DateOffset(days=90)
        to_fetch = [t for t in tickers if f"{t}_{years}" not in self._data_cache]
        if not to_fetch:
            return

        # Phase 1: batch download — one HTTP call per 20 tickers (fast path)
        for i in range(0, len(to_fetch), 20):
            batch = to_fetch[i : i + 20]
            try:
                if i > 0:
                    time.sleep(2)  # Delay between batches to avoid rate limit

                data = yf.download(
                    batch,
                    start=start_date,
                    end=end_date,
                    auto_adjust=True,
                    progress=False,
                    threads=False,
                    group_by="ticker",
                )
                if data.empty:
                    continue
                for t in batch:
                    try:
                        # Extract ticker data carefully
                        if len(batch) == 1:
                            t_df = data
                        else:
                            if isinstance(
                                data.columns, pd.MultiIndex
                            ) and t in data.columns.get_level_values(0):
                                t_df = data[t]
                            else:
                                t_df = data
                        norm = self._normalize_df(t_df, t)
                        if not norm.empty:
                            self._data_cache[f"{t}_{years}"] = norm
                    except Exception:
                        continue
            except Exception:
                pass

        # Phase 2: individually retry any tickers still missing after the batch.
        # Done serially in the main process so that workers never need to make
        # network calls — eliminating parallel-download race conditions entirely.
        still_missing = [t for t in to_fetch if f"{t}_{years}" not in self._data_cache]
        if still_missing:
            logging.info(
                f"Retrying {len(still_missing)} tickers individually "
                f"after batch prefetch miss: {still_missing}"
            )
            for t in still_missing:
                df = self._download_with_retry(t, start_date)
                if not df.empty:
                    norm = self._normalize_df(df, t)
                    if not norm.empty:
                        self._data_cache[f"{t}_{years}"] = norm
                else:
                    logging.warning(
                        f"⚠️ {t}: could not fetch data — will be skipped in analysis."
                    )
                    self._data_cache[f"{t}_{years}"] = pd.DataFrame()

    @staticmethod
    def _empty_finmind_frame(index: pd.Index | None = None) -> pd.DataFrame:
        """Return the canonical Taiwan FinMind feature frame with zero rows."""
        return pd.DataFrame(index=index, columns=FINMIND_FEATURE_COLUMNS, dtype=float)

    def get_finmind_data_for_ticker(self, ticker: str) -> pd.DataFrame:
        """Return the per-ticker FinMind frame, fetching it once if needed."""
        self._ensure_finmind_data(ticker)
        return self._finmind_data_cache.get(ticker, self._empty_finmind_frame())

    def prefetch_finmind_batch(self, tickers: list[str]) -> None:
        """Serially prefetch TWN FinMind features in the main process."""
        tw_tickers = [
            ticker
            for ticker in tickers
            if ticker.endswith(".TW") and ticker not in self._finmind_data_cache
        ]
        if not tw_tickers:
            return

        logging.info(
            f"Prefetching FinMind features serially for {len(tw_tickers)} tickers..."
        )
        for index, ticker in enumerate(tw_tickers):
            self._ensure_finmind_data(ticker)
            if index < len(tw_tickers) - 1:
                time.sleep(0.5)

    def _ensure_market_data(self):
        """Fetches and caches market/macro data if not already present."""
        if self._market_data is not None:
            return

        logging.info("Fetching market and macro data...")
        market_tickers = {
            **self.config.market_indices,
            **self.config.macro_indicators,
        }

        # Download 10 years of data to be safe (covers all reasonable backtests)
        start_date = pd.Timestamp.now() - pd.DateOffset(years=10)

        market_df = pd.DataFrame()
        successful_tickers = []
        failed_tickers = []

        for name, ticker in market_tickers.items():
            try:
                # Use retry helper with curl-cffi session support
                df = self._download_with_retry(ticker, start_date)

                if df.empty:
                    logging.warning(f"No data returned for {name} ({ticker})")
                    failed_tickers.append(f"{name}({ticker})")
                    continue

                # Clean and normalize
                df = self._normalize_df(df, ticker)

                if "Close" in df.columns:
                    # Rename to prevent collision and identify source
                    col_name = f"MKT_{name}"
                    market_df[col_name] = df["Close"]
                    successful_tickers.append(f"{name}({ticker})")

                    # Also add Returns for indices/macro (optional but useful)
                    # market_df[f"{col_name}_Ret"] = df["Close"].pct_change()
                else:
                    logging.warning(f"No 'Close' column for {name} ({ticker})")
                    failed_tickers.append(f"{name}({ticker})")
            except Exception as e:
                logging.warning(f"Failed to fetch market data {name} ({ticker}): {e}")
                failed_tickers.append(f"{name}({ticker})")

        # Log summary (only warnings for failures, suppress success info)
        if failed_tickers:
            logging.warning(
                f"⚠️ Failed to fetch {len(failed_tickers)} market features: {', '.join(failed_tickers)}"
            )

        # Clean up market data (handle inf/nan)
        market_df.replace([np.inf, -np.inf], np.nan, inplace=True)
        self._market_data = market_df.ffill().fillna(0)

    def _ensure_finmind_data(self, ticker: str):
        """Fetch Taiwan institutional data from FinMind with fallback handling."""
        if ticker in self._finmind_data_cache:
            self._finmind_data = self._finmind_data_cache[ticker]
            return

        if not FINMIND_AVAILABLE:
            logging.warning(
                "FinMind not installed. Skipping Taiwan institutional features."
            )
            self._finmind_data = self._empty_finmind_frame()
            self._finmind_data_cache[ticker] = self._finmind_data.copy()
            return

        # Only fetch for Taiwan stocks (*.TW format)
        if not ticker.endswith(".TW"):
            self._finmind_data = self._empty_finmind_frame()
            self._finmind_data_cache[ticker] = self._finmind_data.copy()
            return

        # Extract stock ID (remove .TW suffix)
        stock_id = ticker.replace(".TW", "")

        # Calculate date range (10 years to cover all backtests)
        end_date = pd.Timestamp.now()
        start_date = end_date - pd.DateOffset(years=10)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        finmind_df = self._empty_finmind_frame()
        successful_features = []
        failed_features = []

        try:
            dl = DataLoader()

            # 1. Foreign/Trust/Dealer Flows (三大法人)
            try:
                institutional = dl.taiwan_stock_institutional_investors(
                    stock_id=stock_id, start_date=start_str, end_date=end_str
                )
                if institutional is not None and not institutional.empty:
                    institutional["date"] = pd.to_datetime(institutional["date"])
                    institutional.set_index("date", inplace=True)

                    # Net buy amounts (positive = buying, negative = selling)
                    if "Foreign_Investor_Diff" in institutional.columns:
                        finmind_df["FM_Foreign_NetBuy"] = institutional[
                            "Foreign_Investor_Diff"
                        ]
                        successful_features.append("Foreign_NetBuy")
                    if "Investment_Trust_Diff" in institutional.columns:
                        finmind_df["FM_Trust_NetBuy"] = institutional[
                            "Investment_Trust_Diff"
                        ]
                        successful_features.append("Trust_NetBuy")
                    if "Dealer_Diff" in institutional.columns:
                        finmind_df["FM_Dealer_NetBuy"] = institutional["Dealer_Diff"]
                        successful_features.append("Dealer_NetBuy")
            except Exception as e:
                logging.warning(
                    f"Failed to fetch institutional data for {stock_id}: {e}"
                )
                failed_features.append("Institutional")

            # 2. Margin Trading & Short Selling (融資融券)
            try:
                margin = dl.taiwan_stock_margin_purchase_short_sale(
                    stock_id=stock_id, start_date=start_str, end_date=end_str
                )
                if margin is not None and not margin.empty:
                    margin["date"] = pd.to_datetime(margin["date"])
                    margin.set_index("date", inplace=True)

                    # Margin balance and short balance
                    if "MarginPurchaseBuy" in margin.columns:
                        finmind_df["FM_Margin_Balance"] = margin["MarginPurchaseBuy"]
                        successful_features.append("Margin_Balance")
                    if "ShortSaleBuy" in margin.columns:
                        finmind_df["FM_Short_Balance"] = margin["ShortSaleBuy"]
                        successful_features.append("Short_Balance")
            except Exception as e:
                logging.warning(f"Failed to fetch margin data for {stock_id}: {e}")
                failed_features.append("Margin")

            # 3. Monthly Revenue (月營收) - requires different date handling
            try:
                revenue = dl.taiwan_stock_month_revenue(
                    stock_id=stock_id, start_date=start_str, end_date=end_str
                )
                if revenue is not None and not revenue.empty:
                    # Revenue is monthly, need to forward fill to daily
                    revenue["date"] = pd.to_datetime(revenue["date"])
                    revenue.set_index("date", inplace=True)

                    if "revenue_year_over_year" in revenue.columns:
                        # Resample to daily and forward fill
                        revenue_daily = (
                            revenue[["revenue_year_over_year"]].resample("D").ffill()
                        )
                        finmind_df["FM_Revenue_YoY"] = revenue_daily[
                            "revenue_year_over_year"
                        ]
                        successful_features.append("Revenue_YoY")
            except Exception as e:
                logging.warning(f"Failed to fetch revenue data for {stock_id}: {e}")
                failed_features.append("Revenue")

            # Log summary (only warnings, suppress info)
            if failed_features:
                logging.warning(
                    f"⚠️ FinMind: Failed features for {stock_id}: {', '.join(failed_features)}"
                )

        except Exception as e:
            logging.error(f"FinMind initialization failed for {stock_id}: {e}")

        self._finmind_data = finmind_df.ffill().fillna(0)
        self._finmind_data_cache[ticker] = self._finmind_data.copy()

    def ensure_market_data(self):
        """Public wrapper for market data initialization."""
        self._ensure_market_data()

    @property
    def market_data(self) -> pd.DataFrame | None:
        """Public read-only access to cached market data."""
        return self._market_data

    def _build_horizon_target(
        self, close_series: pd.Series, horizon_days: int
    ) -> pd.Series:
        """Build a future-close target aligned to the requested horizon."""
        horizon_days = max(1, int(horizon_days))
        close_index = pd.DatetimeIndex(close_series.index)
        close_values = close_series.to_numpy(dtype=float)
        target_values = np.full(len(close_values), np.nan, dtype=float)

        for i, current_date in enumerate(close_index):
            target_date = current_date + pd.DateOffset(days=horizon_days)
            target_pos = close_index.searchsorted(target_date, side="left")
            if target_pos < len(close_values):
                target_values[i] = close_values[target_pos]

        return pd.Series(target_values, index=close_index)

    def prepare_features(
        self,
        data: pd.DataFrame,
        ticker: str = None,
        target_horizon_days: int | None = None,
    ):
        df = data.copy()
        horizon_days = max(1, int(target_horizon_days or self.target_horizon_days))

        # Double check Close is a Series
        if "Close" not in df.columns:
            raise KeyError(f"Column 'Close' missing. Found: {list(df.columns)}")

        # --- 1. Basic Moving Averages ---
        df["MA5"] = df["Close"].rolling(window=5).mean()
        df["MA20"] = df["Close"].rolling(window=20).mean()
        df["MA50"] = df["Close"].rolling(window=50).mean()

        # --- 2. RSI ---
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        df["RSI"] = 100 - (100 / (1 + rs))

        # --- 3. MACD ---
        exp1 = df["Close"].ewm(span=12, adjust=False).mean()
        exp2 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = exp1 - exp2
        df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()

        # --- 4. Bollinger Bands (New) ---
        df["BB_Middle"] = df["Close"].rolling(window=20).mean()
        df["BB_Std"] = df["Close"].rolling(window=20).std()
        df["BB_Upper"] = df["BB_Middle"] + (2 * df["BB_Std"])
        df["BB_Lower"] = df["BB_Middle"] - (2 * df["BB_Std"])
        df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / (df["BB_Middle"] + 1e-9)

        # --- 5. ATR (New) ---
        high_low = df["High"] - df["Low"]
        high_close = np.abs(df["High"] - df["Close"].shift())
        low_close = np.abs(df["Low"] - df["Close"].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["ATR"] = tr.rolling(window=14).mean()

        # --- 6. KD (Taiwan Specific) ---
        low_9 = df["Low"].rolling(9).min()
        high_9 = df["High"].rolling(9).max()
        h_l_diff = high_9 - low_9
        h_l_diff = h_l_diff.replace(0, np.nan)
        rsv = ((df["Close"] - low_9) / (h_l_diff + 1e-9)) * 100
        rsv = rsv.fillna(50)
        df["K"] = rsv.ewm(com=2).mean()
        df["D"] = df["K"].ewm(com=2).mean()

        # --- 7. FinMind Institutional Data (Taiwan Only) ---
        if ticker and ticker.endswith(".TW"):
            fm_data = self.get_finmind_data_for_ticker(ticker)
            finmind_subset = fm_data.shift(1).reindex(df.index).ffill().fillna(0)
            df = df.join(finmind_subset)
            df = df.ffill().fillna(0)

        # --- 8. Market Context Integration (New) ---
        self._ensure_market_data()
        if self._market_data is not None and not self._market_data.empty:
            # Align market data to stock dates
            # CRITICAL: Shift market data by 1 day to prevent look-ahead bias.
            # We must use T-1 market data for T calculations to ensure the AI
            # only uses information available at the time of prediction.
            market_subset = self._market_data.shift(1).reindex(df.index).ffill()
            df = df.join(market_subset)

            # Fill any remaining NaNs (e.g. start of history)
            df = df.ffill().fillna(0)

        df["Daily_Return"] = df["Close"].pct_change(fill_method=None)

        df["Target"] = self._build_horizon_target(df["Close"], horizon_days)
        df = df.dropna()

        # Final safety cleanup for all features (including indicators and market data)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.ffill(inplace=True)
        df.fillna(0, inplace=True)

        # Update features list
        features = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "MA5",
            "MA20",
            "MA50",
            "RSI",
            "MACD",
            "Signal_Line",
            "BB_Upper",
            "BB_Lower",
            "BB_Width",
            "ATR",
            "K",
            "D",
            "Daily_Return",
        ]

        # Add dynamic market features
        if self._market_data is not None:
            for col in self._market_data.columns:
                if col in df.columns:
                    features.append(col)

        # Add fixed FinMind institutional features (Taiwan only)
        if ticker and ticker.endswith(".TW"):
            for col in FINMIND_FEATURE_COLUMNS:
                if col in df.columns:
                    features.append(col)

        X = df[features].values
        y = df["Target"].values

        # Detect log-normalization: if Close max/min ratio > 1.5, apply log transformation
        close_min = df["Close"].min()
        close_max = df["Close"].max()
        if close_min > 0 and (close_max / close_min) > 1.5:
            self.close_was_log_normalized = True
            y = np.log1p(y)
        else:
            self.close_was_log_normalized = False

        # Map features to scaler groups for multi-scaler training
        self._get_feature_group_indices(features)

        return X, y

    def _create_sequences(self, data_scaled, target):
        X_seq, y_seq = [], []
        for i in range(len(data_scaled) - self.sequence_length):
            X_seq.append(data_scaled[i : i + self.sequence_length])
            y_seq.append(target[i + self.sequence_length])
        return np.array(X_seq), np.array(y_seq)

    @staticmethod
    def _get_lstm_horizon_path(bundle_path: str, target_horizon_days: int) -> str:
        """Return the horizon-specific Keras sidecar path for a bundle file."""
        return bundle_path.replace(".joblib", f"_h{int(target_horizon_days)}.keras")

    @staticmethod
    def _extract_horizon_entry(data_bundle: dict, target_horizon_days: int) -> dict:
        """Extract a single horizon entry from a bundle dict.

        Handles both the new multi-horizon format (bundle["horizons"][N])
        and the legacy flat format (bundle["target_horizon_days"] == N).

        Raises:
            FileNotFoundError: If the requested horizon is not found in the bundle.
        """
        horizons = data_bundle.get("horizons")
        if horizons is not None:
            entry = horizons.get(int(target_horizon_days))
            if entry is None:
                raise FileNotFoundError(
                    f"Horizon {target_horizon_days} not found in bundle. "
                    f"Available horizons: {list(horizons.keys())}. Re-run training."
                )
            return entry
        # Legacy flat bundle — target_horizon_days stored at top level
        stored_horizon = int(data_bundle.get("target_horizon_days", 1))
        if stored_horizon != int(target_horizon_days):
            raise FileNotFoundError(
                f"Legacy bundle stores horizon={stored_horizon}, "
                f"requested horizon={target_horizon_days}. Re-run training."
            )
        return data_bundle

    def train(self, ticker: str, target_horizon_days: int | None = None):
        if target_horizon_days is not None:
            self.target_horizon_days = max(1, int(target_horizon_days))

        buy_horizon = max(1, int(self.target_horizon_days))
        required_horizons = sorted({1, buy_horizon})

        data = self.fetch_data(ticker, self.config.backtest_years)
        if data.empty:
            raise ValueError(f"No data for {ticker}")

        m_type = self.config.model_type
        weighting_suffix = self.config.weighting_type
        horizon_suffix = f"h{buy_horizon}d"
        os.makedirs(self.config.model_path, exist_ok=True)
        model_filename = os.path.join(
            self.config.model_path,
            f"{ticker}_{m_type}_{weighting_suffix}_{horizon_suffix}_model.joblib",
        )

        # Read-modify-write: preserve any existing horizons already in the bundle
        if os.path.exists(model_filename):
            try:
                existing = joblib.load(model_filename)
                bundle_payload = {
                    "model_type": m_type,
                    "weighting_type": self.config.weighting_type,
                    "horizons": dict(existing.get("horizons", {})),
                }
            except Exception:
                bundle_payload = {
                    "model_type": m_type,
                    "weighting_type": self.config.weighting_type,
                    "horizons": {},
                }
        else:
            bundle_payload = {
                "model_type": m_type,
                "weighting_type": self.config.weighting_type,
                "horizons": {},
            }

        for h in required_horizons:
            X, y = self.prepare_features(data, ticker, target_horizon_days=h)
            if len(X) < 1:
                raise ValueError(
                    f"Insufficient data rows for {ticker} (horizon={h}) after feature engineering."
                )

            # Conditional scaling based on model type
            if m_type == "lstm":
                scalers = self._init_scalers(len(X))
                self.price_scaler = scalers["price_scaler"]
                self.volume_scaler = scalers["volume_scaler"]
                self.technical_scaler = scalers["technical_scaler"]
                X_scaled = self._apply_multi_scalers_fit(X)
            else:
                X_scaled = X  # Tree models use raw data

            # Calculate sample weights based on weighting strategy
            sample_weights = self._calculate_sample_weights(len(X_scaled))

            # For LSTM, also scale the target
            target_scaler = None
            y_scaled = y
            if m_type == "lstm":
                from sklearn.preprocessing import StandardScaler

                target_scaler = StandardScaler()
                y_scaled = target_scaler.fit_transform(y.reshape(-1, 1)).flatten()

            if m_type == "lstm":
                try:
                    X_seq, y_seq = self._create_sequences(X_scaled, y_scaled)
                    # For LSTM sequences, we need to align weights with sequences
                    seq_sample_weights = self._calculate_sample_weights(len(X_seq))
                    self.model = self._init_model(input_dim=X.shape[1])
                    self.model.fit(
                        X_seq,
                        y_seq,
                        sample_weight=seq_sample_weights,
                        batch_size=32,
                        epochs=10,
                        verbose=0,
                    )
                    self.target_scaler = target_scaler  # Save for inverse transform
                except Exception as e:
                    logging.warning(
                        f"⚠️ LSTM sequence training failed for {ticker} (h={h}): {e}. "
                        f"Falling back to standard training."
                    )
                    self.model = self._init_model()
                    self.model.fit(X_scaled, y, sample_weight=sample_weights)
                    self.target_scaler = None
            elif m_type == "prophet":
                try:
                    prophet_df = pd.DataFrame(
                        {"ds": data.index, "y": data["Close"].values.flatten()}
                    )
                    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"]).dt.tz_localize(
                        None
                    )
                    prophet_df = prophet_df.dropna()
                    self.model = self._init_model()
                    self.model.fit(prophet_df)
                except Exception as e:
                    logging.warning(
                        f"⚠️ Prophet training failed for {ticker} (h={h}): {e}. "
                        f"Falling back to standard training."
                    )
                    self.model = self._init_model()
                    self.model.fit(X_scaled, y, sample_weight=sample_weights)
            else:
                self.model = self._init_model()
                self.model.fit(X_scaled, y, sample_weight=sample_weights)

            horizon_entry = {
                "scaler": self.scaler,
                "target_scaler": getattr(self, "target_scaler", None),
                "price_scaler": getattr(self, "price_scaler", None),
                "volume_scaler": getattr(self, "volume_scaler", None),
                "technical_scaler": getattr(self, "technical_scaler", None),
                "close_was_log_normalized": self.close_was_log_normalized,
                "model_class": self.model.__class__.__name__,
                "weighting_type": self.config.weighting_type,
                "target_horizon_days": h,
            }

            if m_type == "lstm" and hasattr(self.model, "save"):
                keras_path = self._get_lstm_horizon_path(model_filename, h)
                self.model.save(keras_path)
                horizon_entry["keras_path"] = keras_path
            else:
                horizon_entry["model"] = self.model

            bundle_payload["horizons"][h] = horizon_entry

        # After the loop self.model / self.scaler hold the BUY horizon (last iteration)
        joblib.dump(bundle_payload, model_filename)

    def load_or_build(self, ticker: str, target_horizon_days: int | None = None) -> str:
        if target_horizon_days is not None:
            self.target_horizon_days = max(1, int(target_horizon_days))

        # Bundle filename is keyed by the BUY horizon
        weighting_suffix = self.config.weighting_type
        horizon_suffix = f"h{self.target_horizon_days}d"
        model_filename = os.path.join(
            self.config.model_path,
            f"{ticker}_{self.config.model_type}_{weighting_suffix}_{horizon_suffix}_model.joblib",
        )

        # Train if bundle missing
        if not os.path.exists(model_filename):
            self.train(ticker, target_horizon_days=self.target_horizon_days)
            return "trained"

        try:
            data_bundle = joblib.load(model_filename)

            # Extract the requested horizon entry (supports new multi-horizon and legacy bundles)
            try:
                horizon_entry = self._extract_horizon_entry(
                    data_bundle, self.target_horizon_days
                )
            except FileNotFoundError:
                # Horizon not in bundle → retrain to populate it
                self.train(ticker, target_horizon_days=self.target_horizon_days)
                return "retrained_missing_horizon"

            loaded_scaler = horizon_entry["scaler"]

            # Feature dimension check
            sample_data = self.fetch_data(ticker, self.config.backtest_years)
            if sample_data.empty:
                self.train(ticker, target_horizon_days=self.target_horizon_days)
                return "trained_fallback"

            X_sample, _ = self.prepare_features(
                sample_data,
                ticker,
                target_horizon_days=self.target_horizon_days,
            )
            current_dim = X_sample.shape[1]

            # Scaler feature count check
            if (
                hasattr(loaded_scaler, "n_features_in_")
                and loaded_scaler.n_features_in_ != current_dim
            ):
                logging.warning(
                    f"Feature mismatch for {ticker}: expected {current_dim}, "
                    f"found {loaded_scaler.n_features_in_}. Retraining..."
                )
                self.train(ticker, target_horizon_days=self.target_horizon_days)
                return "retrained"

            self.scaler = loaded_scaler
            self.price_scaler = horizon_entry.get("price_scaler", None)
            self.volume_scaler = horizon_entry.get("volume_scaler", None)
            self.technical_scaler = horizon_entry.get("technical_scaler", None)
            self.close_was_log_normalized = horizon_entry.get(
                "close_was_log_normalized", False
            )
            bundle_horizon = horizon_entry.get("target_horizon_days")
            if bundle_horizon is not None:
                self.target_horizon_days = max(1, int(bundle_horizon))
            self.target_scaler = horizon_entry.get("target_scaler", None)

            # Load Model
            if "keras_path" in horizon_entry or "lstm_h5" in horizon_entry:
                from tensorflow.keras.models import load_model

                keras_path = self._get_lstm_horizon_path(
                    model_filename, self.target_horizon_days
                )
                if not os.path.exists(keras_path):
                    stored_path = horizon_entry.get("keras_path") or horizon_entry.get(
                        "lstm_h5"
                    )
                    if stored_path and os.path.exists(stored_path):
                        keras_path = stored_path
                    else:
                        self.train(ticker, target_horizon_days=self.target_horizon_days)
                        return "retrained_keras_missing"
                # Final safety check: load_model might fail if architecture changed
                try:
                    self.model = load_model(keras_path)
                except Exception:
                    self.train(ticker, target_horizon_days=self.target_horizon_days)
                    return "retrained_keras_error"
            else:
                self.model = horizon_entry.get("model")

            return "loaded"

        except Exception as e:
            logging.error(f"Failed to load model for {ticker}: {e}. Retraining...")
            self.train(ticker, target_horizon_days=self.target_horizon_days)
            return "retrained_error"

    def load_exit_model(self, ticker: str, buy_horizon_days: int) -> None:
        """Load the horizon=1 exit-confirmation model from the h{N}d bundle.

        For a 1-day strategy (buy_horizon_days=1), the BUY and EXIT models are
        identical so this simply delegates to load_or_build.
        """
        buy_horizon_days = max(1, int(buy_horizon_days))
        if buy_horizon_days == 1:
            self.load_or_build(ticker, target_horizon_days=1)
            return

        weighting_suffix = self.config.weighting_type
        model_filename = os.path.join(
            self.config.model_path,
            f"{ticker}_{self.config.model_type}_{weighting_suffix}_h{buy_horizon_days}d_model.joblib",
        )

        if not os.path.exists(model_filename):
            raise FileNotFoundError(
                f"Bundle not found for {ticker} exit model: {model_filename}. "
                f"Run training with holding_period={buy_horizon_days} first."
            )

        try:
            data_bundle = joblib.load(model_filename)
            horizon_entry = self._extract_horizon_entry(data_bundle, 1)

            self.scaler = horizon_entry["scaler"]
            self.target_horizon_days = 1
            self.target_scaler = horizon_entry.get("target_scaler", None)

            if "keras_path" in horizon_entry or "lstm_h5" in horizon_entry:
                from tensorflow.keras.models import load_model

                keras_path = self._get_lstm_horizon_path(model_filename, 1)
                if not os.path.exists(keras_path):
                    stored_path = horizon_entry.get("keras_path") or horizon_entry.get(
                        "lstm_h5"
                    )
                    if stored_path and os.path.exists(stored_path):
                        keras_path = stored_path
                    else:
                        raise FileNotFoundError(
                            f"Keras exit model (h=1) missing: {keras_path}"
                        )
                self.model = load_model(keras_path)
            else:
                self.model = horizon_entry.get("model")

            if self.model is None:
                raise RuntimeError(
                    f"Exit model is None after loading bundle: {model_filename}"
                )

        except (FileNotFoundError, RuntimeError):
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to load exit model for {ticker}: {e}") from e

    def predict(
        self,
        current_data: np.ndarray,
        date: pd.Timestamp | None = None,
        target_horizon_days: int | None = None,
    ) -> float:
        if self.model is None:
            raise ValueError("Model not loaded.")
        horizon_days = max(1, int(target_horizon_days or self.target_horizon_days))
        m_type = self.config.model_type
        if m_type == "prophet" and hasattr(self.model, "predict"):
            future = pd.DataFrame(
                {"ds": [(date + pd.DateOffset(days=horizon_days)).tz_localize(None)]}
            )
            pred = float(self.model.predict(future)["yhat"].iloc[0])
            if self.close_was_log_normalized:
                pred = np.expm1(pred)
            return pred
        if m_type == "lstm" and hasattr(self.model, "predict"):
            if len(current_data.shape) == 2:
                X_scaled = self._apply_multi_scalers_transform(current_data)
                pred = float(
                    self.model.predict(
                        X_scaled.reshape(1, self.sequence_length, -1), verbose=0
                    )[0][0]
                )
                # Sigmoid output (0-1) -> rescale to training range (0.1-0.9)
                if self.target_scaler is not None:
                    pred = pred * 0.8 + 0.1
                    pred = float(self.target_scaler.inverse_transform([[pred]])[0][0])
                if self.close_was_log_normalized:
                    pred = np.expm1(pred)
                return pred
            return 0.0
        X_input = (
            current_data[-1].reshape(1, -1)
            if len(current_data.shape) == 2
            else current_data.reshape(1, -1)
        )
        pred = float(self.model.predict(X_input)[0])
        if self.close_was_log_normalized:
            pred = np.expm1(pred)
        return pred

    def get_latest_features(self, ticker: str) -> np.ndarray | None:
        data = self.fetch_data(ticker, 1)
        if data.empty:
            return None
        X, y = self.prepare_features(data, ticker)
        if len(X) < self.sequence_length:
            return None
        return X[-self.sequence_length :]
