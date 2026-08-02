"""
USA AI Trading System - Model Builder

Purpose: Factory for creating and training machine learning models with
standardized interfaces for prediction and backtesting for the US market.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import logging
import os
import time

import joblib
import numpy as np
import pandas as pd
import yfinance as yf

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
logging.getLogger("yfinance").setLevel(logging.ERROR)
logging.getLogger("yfinance.utils").setLevel(logging.ERROR)

from typing import Any

from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import (
    MinMaxScaler,
    QuantileTransformer,
    RobustScaler,
)

from core.config import Config


class ModelBuilder:
    """Handles data fetching, preprocessing, and model training."""

    def __init__(self, config: Config):
        self.config = config
        self.model: Any | None = None
        self.scaler: Any | None = None
        self.price_scaler: Any | None = None
        self.volume_scaler: Any | None = None
        self.technical_scaler: Any | None = None
        self.target_scaler: Any | None = None
        self.sequence_length = 30
        self._data_cache: dict[str, pd.DataFrame] = {}
        self._market_data: pd.DataFrame | None = None
        self._finmind_data_cache: dict[str, pd.DataFrame] = {}
        self._price_feature_indices: list[int] = []
        self._volume_feature_indices: list[int] = []
        self._technical_feature_indices: list[int] = []
        self.close_was_log_normalized: bool = False

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

    def get_company_name(self, ticker: str) -> str:
        """Fetches the long name of the company from yfinance."""
        try:
            info = yf.Ticker(ticker).info
            return info.get("longName", ticker)
        except Exception:
            return ticker

    def is_etf(self, ticker: str) -> bool:
        """Determines if a ticker is an ETF using yfinance info."""
        try:
            # We don't want to call .info for every run, so we might want a small cache
            # or just rely on the quoteType if we had it.
            # For now, a quick fetch is fine as it's only called during rendering once per ticker.
            info = yf.Ticker(ticker).info
            return info.get("quoteType") == "ETF"
        except Exception:
            return False

    def fetch_data(self, ticker: str, years: int) -> pd.DataFrame:
        cache_key = f"{ticker}_{years}"
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]

        end_date = pd.Timestamp.now()
        # Add a 60-day warm-up buffer (approx 2 months of trading days)
        # so that indicators and LSTM sequences are ready on the actual start date.
        start_date = end_date - pd.DateOffset(years=years) - pd.DateOffset(days=90)

        for attempt in range(3):
            try:
                data = yf.download(
                    ticker,
                    start=start_date,
                    end=end_date,
                    auto_adjust=True,
                    progress=False,
                    threads=False,
                )
                if not data.empty:
                    norm = self._normalize_df(data, ticker)
                    self._data_cache[cache_key] = norm
                    return norm
                time.sleep(1)
            except Exception:
                pass
        return pd.DataFrame()

    def prefetch_data_batch(self, tickers: list[str], years: int):
        if not tickers:
            return
        end_date = pd.Timestamp.now()
        start_date = end_date - pd.DateOffset(years=years)
        to_fetch = [t for t in tickers if f"{t}_{years}" not in self._data_cache]
        if not to_fetch:
            return

        for i in range(0, len(to_fetch), 20):
            batch = to_fetch[i : i + 20]
            try:
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

        for name, ticker in market_tickers.items():
            try:
                # Use history for cleaner single-ticker fetch
                # or download. we need daily close.
                df = yf.download(
                    ticker,
                    start=start_date,
                    progress=False,
                    auto_adjust=True,
                    threads=False,
                )

                if df.empty:
                    continue

                # Clean and normalize
                df = self._normalize_df(df, ticker)

                if "Close" in df.columns:
                    # Rename to prevent collision and identify source
                    col_name = f"MKT_{name}"
                    market_df[col_name] = df["Close"]

                    # Also add Returns for indices/macro (optional but useful)
                    # market_df[f"{col_name}_Ret"] = df["Close"].pct_change()
            except Exception as e:
                logging.warning(f"Failed to fetch market data {name} ({ticker}): {e}")

        # Forward fill to handle different trading calendars (e.g. US holidays vs AU)
        self._market_data = market_df.ffill().fillna(0)

    def prepare_features(
        self, data: pd.DataFrame, target_horizon_days: int | None = None
    ):
        """Prepare features and target for model training.

        Args:
            data: DataFrame with OHLCV columns
            target_horizon_days: Days ahead for target (default: self.target_horizon_days or 1)

        Returns:
            X, y tuple for training
        """
        if target_horizon_days is None:
            target_horizon_days = getattr(self, "target_horizon_days", 1)

        target_horizon_days = max(1, int(target_horizon_days))

        df = data.copy()

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

        # --- 6. Market Context Integration (New) ---
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

        # Target: Close price N days in the future (for multi-horizon training)
        df["Target"] = df["Close"].shift(-target_horizon_days)
        df = df.dropna()

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
            "Daily_Return",
        ]

        # Add dynamic market features
        if self._market_data is not None:
            for col in self._market_data.columns:
                if col in df.columns:
                    features.append(col)

        X = df[features].values
        y = df["Target"].values

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

    def train(self, ticker: str, target_horizon_days: int | None = None):
        if target_horizon_days is not None:
            self.target_horizon_days = max(1, int(target_horizon_days))

        buy_horizon = max(1, int(self.target_horizon_days))
        required_horizons = sorted({1, buy_horizon})

        data = self.fetch_data(ticker, self.config.backtest_years)
        if data.empty:
            raise ValueError(f"No data for {ticker}")

        # Validate minimum raw data rows (need at least 150 for rolling window indicators)
        min_raw_rows = 150
        if len(data) < min_raw_rows:
            raise ValueError(
                f"Insufficient raw data for {ticker}: {len(data)} rows (need ≥{min_raw_rows}). "
                f"Check data source or extend lookback period."
            )

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
            X, y = self.prepare_features(data, target_horizon_days=h)

            # Validate minimum engineered rows (need at least 50 for meaningful training)
            min_engineered_rows = 50
            if len(X) < min_engineered_rows:
                raise ValueError(
                    f"Insufficient data for {ticker} (horizon={h}d): "
                    f"Only {len(X)} rows after feature engineering (need ≥{min_engineered_rows}). "
                    f"Raw data had {len(data)} rows; lost {len(data) - len(X)} to rolling windows and NaN."
                )

            sample_weights = self._calculate_sample_weights(len(X))
            target_scaler = None
            y_scaled = y
            if m_type == "lstm":
                scalers_dict = self._init_scalers(n_samples=len(X))
                self.price_scaler = scalers_dict["price_scaler"]
                self.volume_scaler = scalers_dict["volume_scaler"]
                self.technical_scaler = scalers_dict["technical_scaler"]
                target_scaler = scalers_dict["target_scaler"]

                X_scaled = self._apply_multi_scalers_fit(X)
                y_scaled = target_scaler.fit_transform(y.reshape(-1, 1)).flatten()
            else:
                # Tree models & Prophet: no feature scaling needed
                X_scaled = X
                self.price_scaler = None
                self.volume_scaler = None
                self.technical_scaler = None
                target_scaler = None

            if m_type == "lstm":
                try:
                    X_seq, y_seq = self._create_sequences(X_scaled, y_scaled)

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
                    self.model.fit(X_scaled, y_scaled, sample_weight=sample_weights)
                    self.target_scaler = target_scaler
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
                    self.model.fit(
                        X, y, sample_weight=sample_weights
                    )  # Use raw X, y for fallback
            else:
                self.model = self._init_model()
                self.model.fit(X, y, sample_weight=sample_weights)

            # Determine log-normalization for this horizon
            if m_type == "lstm":
                self.close_was_log_normalized = True
                y_normalized = np.log1p(y)
            else:
                self.close_was_log_normalized = False
                y_normalized = y

            horizon_entry = {
                "price_scaler": self.price_scaler,
                "volume_scaler": self.volume_scaler,
                "technical_scaler": self.technical_scaler,
                "scaler": self.scaler,
                "target_scaler": getattr(self, "target_scaler", None),
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

    def load_or_build(self, ticker: str, target_horizon_days: int = 1) -> str:
        """Load or build a model, optionally for a specific prediction horizon.

        Args:
            ticker: Stock ticker symbol
            target_horizon_days: Prediction horizon in days (1 for exit, N for buy)

        Returns:
            Status string: "loaded", "trained", etc.
        """
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
                sample_data, target_horizon_days=self.target_horizon_days
            )
            current_dim = X_sample.shape[1]

            # Scaler feature count check (skip for LSTM with multi-scalers)
            if self.config.model_type != "lstm" and loaded_scaler is not None:
                if (
                    hasattr(loaded_scaler, "n_features_in_")
                    and loaded_scaler.n_features_in_ != current_dim
                ):
                    logging.warning(
                        f"Feature mismatch for {ticker}: expected {current_dim}, found {loaded_scaler.n_features_in_}. Retraining..."
                    )
                    self.train(ticker, target_horizon_days=self.target_horizon_days)
                    return "retrained"

            # For LSTM, check if multi-scalers are available (required for prediction)
            if self.config.model_type == "lstm":
                if (
                    "price_scaler" not in horizon_entry
                    or horizon_entry["price_scaler"] is None
                ):
                    logging.warning(
                        f"LSTM multi-scalers missing for {ticker}. Retraining..."
                    )
                    self.train(ticker, target_horizon_days=self.target_horizon_days)
                    return "retrained_missing_scalers"

            self.scaler = loaded_scaler
            self.target_scaler = horizon_entry.get("target_scaler", None)
            self.close_was_log_normalized = horizon_entry.get(
                "close_was_log_normalized", False
            )

            # Load multi-scalers for LSTM
            if self.config.model_type == "lstm":
                self.price_scaler = horizon_entry.get("price_scaler", None)
                self.volume_scaler = horizon_entry.get("volume_scaler", None)
                self.technical_scaler = horizon_entry.get("technical_scaler", None)

            # 4. Load Model
            if "keras_path" in horizon_entry or "lstm_h5" in horizon_entry:
                from tensorflow.keras.models import load_model

                keras_path = horizon_entry.get(
                    "keras_path", horizon_entry.get("lstm_h5")
                )
                if not os.path.exists(keras_path):
                    stored_path = horizon_entry.get("keras_path") or horizon_entry.get(
                        "lstm_h5"
                    )
                    if stored_path and os.path.exists(stored_path):
                        keras_path = stored_path

                try:
                    self.model = load_model(keras_path)
                except Exception:
                    self.train(ticker, target_horizon_days=self.target_horizon_days)
                    return "retrained_keras_error"
            else:
                self.model = horizon_entry.get("model")

            logging.debug(
                f"Loaded model (h{self.target_horizon_days}d) for {ticker} from {model_filename}"
            )
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

        model_filename = os.path.join(
            self.config.model_path,
            f"{ticker}_{self.config.model_type}_{self.config.weighting_type}_h{buy_horizon_days}d_model.joblib",
        )

        try:
            data_bundle = joblib.load(model_filename)
            horizon_entry = self._extract_horizon_entry(data_bundle, 1)

            self.scaler = horizon_entry["scaler"]
            self.target_horizon_days = 1
            self.target_scaler = horizon_entry.get("target_scaler", None)
            # Load LSTM multi-scalers for exit model prediction
            self.price_scaler = horizon_entry.get("price_scaler", None)
            self.volume_scaler = horizon_entry.get("volume_scaler", None)
            self.technical_scaler = horizon_entry.get("technical_scaler", None)
            self.close_was_log_normalized = horizon_entry.get(
                "close_was_log_normalized", False
            )

            if "keras_path" in horizon_entry or "lstm_h5" in horizon_entry:
                from tensorflow.keras.models import load_model

                keras_path = horizon_entry.get(
                    "keras_path", horizon_entry.get("lstm_h5")
                )
                self.model = load_model(keras_path)
            else:
                self.model = horizon_entry["model"]

            logging.debug(
                f"Loaded exit model (h1d) from bundle h{buy_horizon_days}d for {ticker}"
            )
        except Exception as e:
            logging.error(
                f"Failed to load exit model for {ticker} from h{buy_horizon_days}d bundle: {e}"
            )
            raise

    def _extract_horizon_entry(
        self, data_bundle: dict[str, Any], target_horizon_days: int
    ) -> dict[str, Any]:
        """Extract the requested horizon entry from a bundle.

        Supports both multi-horizon bundles (new) and single-horizon legacy bundles.

        Args:
            data_bundle: Loaded model bundle
            target_horizon_days: Requested horizon (typically 1 for exit, N for buy)

        Returns:
            Dictionary containing model, scalers, and metadata for this horizon
        """
        # Try multi-horizon format first
        horizons = data_bundle.get("horizons")
        if horizons is not None:
            resolved_horizon = int(target_horizon_days)
            entry = horizons.get(resolved_horizon)
            if entry is not None:
                return entry
            # Fallback to closest available horizon if exact match not found
            available = sorted(int(h) for h in horizons.keys())
            if available:
                closest = min(available, key=lambda x: abs(x - resolved_horizon))
                logging.warning(
                    f"Horizon {resolved_horizon} not found in bundle. Using closest: {closest}. "
                    f"Available: {available}"
                )
                return horizons[closest]
            # No horizons at all - shouldn't happen
            raise FileNotFoundError(
                f"Requested horizon {resolved_horizon} not found in bundle. "
                f"Available horizons: {available}"
            )

        # Fallback for legacy single-entry bundles (entire bundle is the entry)
        return data_bundle

    def predict(
        self, current_data: np.ndarray, date: pd.Timestamp | None = None
    ) -> float:
        if self.model is None:
            raise ValueError("Model not loaded.")
        m_type = self.config.model_type
        if m_type == "prophet" and hasattr(self.model, "predict"):
            future = pd.DataFrame(
                {"ds": [(date + pd.DateOffset(days=1)).tz_localize(None)]}
            )
            return float(self.model.predict(future)["yhat"].iloc[0])
        if m_type == "lstm" and hasattr(self.model, "predict"):
            if len(current_data.shape) == 2:
                X = self.scaler.transform(current_data)
                pred = float(
                    self.model.predict(
                        X.reshape(1, self.sequence_length, -1), verbose=0
                    )[0][0]
                )
                # Inverse transform if target was scaled
                if self.target_scaler is not None:
                    pred = float(self.target_scaler.inverse_transform([[pred]])[0][0])
                return pred
            return 0.0
        X_input = (
            current_data[-1].reshape(1, -1)
            if len(current_data.shape) == 2
            else current_data.reshape(1, -1)
        )
        X_scaled = self.scaler.transform(X_input)
        return float(self.model.predict(X_scaled)[0])

    def get_latest_features(self, ticker: str) -> np.ndarray | None:
        data = self.fetch_data(ticker, 1)
        if data.empty:
            return None
        X, y = self.prepare_features(data)
        if len(X) < self.sequence_length:
            return None
        return X[-self.sequence_length :]

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
