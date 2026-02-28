"""
USA AI Trading System - Model Builder

Purpose: Factory for creating and training machine learning models with
standardized interfaces for prediction and backtesting for the US market.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import os
import joblib
import numpy as np
import pandas as pd
import yfinance as yf
import time
import logging

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

from typing import Optional, Any, Dict, List

# Try to use curl-cffi for rate limit bypass
try:
    from curl_cffi import requests as cf_requests

    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, RobustScaler
from core.config import Config


class ModelBuilder:
    """Handles data fetching, preprocessing, and model training."""

    def __init__(self, config: Config):
        self.config = config
        self.model: Optional[Any] = None
        self.scaler: Optional[Any] = None
        self.target_scaler: Optional[Any] = None  # For LSTM target scaling
        self.sequence_length = 30
        self._data_cache: Dict[str, pd.DataFrame] = {}
        self._market_data: Optional[pd.DataFrame] = None

    def _init_scaler(self) -> Any:
        if self.config.scaler_type == "robust":
            return RobustScaler()
        return StandardScaler()

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
                    logging.info(
                        f"✅ Successfully downloaded data for {ticker} (Attempt {attempt + 1}/{max_retries})"
                    )
                    return df
                else:
                    logging.warning(
                        f"Downloaded empty DataFrame for {ticker} (Attempt {attempt + 1}/{max_retries})"
                    )

            except Exception as e:
                error_msg = str(e)
                logging.error(
                    f"Download attempt {attempt + 1}/{max_retries} failed for {ticker}: {e}"
                )
                if "Rate limit" in error_msg or "Too Many Requests" in error_msg:
                    if attempt < max_retries - 1:
                        logging.warning(f"Rate limit hit for {ticker}, will retry...")
                        continue
                    else:
                        logging.error(
                            f"Rate limit exceeded for {ticker} after {max_retries} attempts"
                        )
                else:
                    logging.error(
                        f"Download failed for {ticker} non-rate-limit reason: {e}"
                    )
                    break

        logging.error(
            f"❌ Failed to download data for {ticker} after {max_retries} attempts."
        )
        return pd.DataFrame()

    @classmethod
    def get_available_models(cls) -> List[str]:
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
            import tensorflow as tf
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense, Dropout, Input

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

        data = self._download_with_retry(ticker, start_date)
        if not data.empty:
            logging.info(f"✅ Successfully fetched yfinance data for {ticker}.")
            norm = self._normalize_df(data, ticker)
            self._data_cache[cache_key] = norm
            return norm
        else:
            logging.error(f"❌ yfinance returned empty data for {ticker}.")

        return pd.DataFrame()

    def prefetch_data_batch(self, tickers: List[str], years: int):
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
                df = self._download_with_retry(ticker, start_date)

                if df.empty:
                    logging.warning(f"No data returned for {name} ({ticker})")
                    failed_tickers.append(f"{name}({ticker})")
                    continue

                df = self._normalize_df(df, ticker)

                if "Close" in df.columns:
                    col_name = f"MKT_{name}"
                    market_df[col_name] = df["Close"]
                    successful_tickers.append(f"{name}({ticker})")
                else:
                    logging.warning(f"No 'Close' column for {name} ({ticker})")
                    failed_tickers.append(f"{name}({ticker})")
            except Exception as e:
                logging.warning(f"Failed to fetch market data {name} ({ticker}): {e}")
                failed_tickers.append(f"{name}({ticker})")

        logging.info(
            f"✅ Successfully fetched {len(successful_tickers)} market features: {', '.join(successful_tickers)}"
        )
        if failed_tickers:
            logging.warning(
                f"❌ Failed to fetch {len(failed_tickers)} market features: {', '.join(failed_tickers)}"
            )

        # Clean up market data (handle inf/nan)
        market_df.replace([np.inf, -np.inf], np.nan, inplace=True)
        self._market_data = market_df.ffill().fillna(0)

        logging.info(
            f"📈 Total market data columns: {len(self._market_data.columns)} - {list(self._market_data.columns)}"
        )

    def prepare_features(self, data: pd.DataFrame, ticker: str = None):
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

        df["Target"] = df["Close"].shift(-1)
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
            "Daily_Return",
        ]

        # Add dynamic market features
        if self._market_data is not None:
            for col in self._market_data.columns:
                if col in df.columns:
                    features.append(col)

        # Log feature details for debugging
        logging.debug(f"Total features prepared: {len(features)} - {features}")
        logging.debug(
            f"Market features included: {[f for f in features if f.startswith('MKT_')]}"
        )

        X = df[features].values
        y = df["Target"].values
        return X, y

    def _create_sequences(self, data_scaled, target):
        X_seq, y_seq = [], []
        for i in range(len(data_scaled) - self.sequence_length):
            X_seq.append(data_scaled[i : i + self.sequence_length])
            y_seq.append(target[i + self.sequence_length])
        return np.array(X_seq), np.array(y_seq)

    def train(self, ticker: str):
        logging.info(
            f"🎓 Starting training for {ticker} (model: {self.config.model_type})..."
        )
        data = self.fetch_data(ticker, self.config.backtest_years)
        if data.empty:
            logging.error(f"❌ No data fetched for {ticker}")
            raise ValueError(f"No data for {ticker}")

        X, y = self.prepare_features(data, ticker)
        if len(X) < 1:
            logging.error(
                f"❌ Insufficient data after feature engineering for {ticker}: X shape={X.shape}"
            )
            raise ValueError(
                f"Insufficient data rows for {ticker} after feature engineering."
            )

        logging.info(
            f"📊 Training data prepared for {ticker}: X shape={X.shape}, y shape={y.shape}"
        )

        self.scaler = self._init_scaler()
        X_scaled = self.scaler.fit_transform(X)

        m_type = self.config.model_type

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
                    f"⚠️ LSTM sequence training failed for {ticker}: {e}. Falling back to standard training."
                )
                self.model = self._init_model()
                self.model.fit(X_scaled, y, sample_weight=sample_weights)
                self.target_scaler = None
        elif m_type == "prophet":
            try:
                prophet_df = pd.DataFrame(
                    {"ds": data.index, "y": data["Close"].values.flatten()}
                )
                prophet_df["ds"] = pd.to_datetime(prophet_df["ds"]).dt.tz_localize(None)
                prophet_df = prophet_df.dropna()
                self.model = self._init_model()
                self.model.fit(prophet_df)
            except Exception as e:
                logging.warning(
                    f"⚠️ Prophet time-series training failed for {ticker}: {e}. Falling back to standard training."
                )
                self.model = self._init_model()
                self.model.fit(X_scaled, y, sample_weight=sample_weights)
        else:
            self.model = self._init_model()
            self.model.fit(X_scaled, y, sample_weight=sample_weights)

        os.makedirs(self.config.model_path, exist_ok=True)
        # Add weighting suffix to model filename
        weighting_suffix = self.config.weighting_type
        model_filename = os.path.join(
            self.config.model_path, f"{ticker}_{m_type}_{weighting_suffix}_model.joblib"
        )
        if m_type == "lstm" and hasattr(self.model, "save"):
            keras_path = model_filename.replace(".joblib", ".keras")
            self.model.save(keras_path)
            joblib.dump(
                {
                    "scaler": self.scaler,
                    "target_scaler": self.target_scaler,  # Save target scaler
                    "keras_path": keras_path,
                    "model_class": self.model.__class__.__name__,
                    "weighting_type": self.config.weighting_type,
                },
                model_filename,
            )
        else:
            joblib.dump(
                {
                    "model": self.model,
                    "scaler": self.scaler,
                    "target_scaler": getattr(
                        self, "target_scaler", None
                    ),  # Include if exists
                    "model_class": self.model.__class__.__name__,
                    "weighting_type": self.config.weighting_type,
                },
                model_filename,
            )

    def load_or_build(self, ticker: str) -> str:
        # Build filename with weighting suffix
        weighting_suffix = self.config.weighting_type
        model_filename = os.path.join(
            self.config.model_path,
            f"{ticker}_{self.config.model_type}_{weighting_suffix}_model.joblib",
        )

        # 1. Force train if requested or missing
        if self.config.rebuild_model or not os.path.exists(model_filename):
            logging.info(
                f"🔧 Training new model for {ticker} (rebuild={self.config.rebuild_model}, exists={os.path.exists(model_filename)})"
            )
            self.train(ticker)
            return "trained"

        try:
            # 2. Try loading bundle
            logging.info(
                f"📂 Loading existing model for {ticker} from {model_filename}"
            )
            data_bundle = joblib.load(model_filename)
            loaded_scaler = data_bundle["scaler"]

            # 3. Check for feature mismatch
            # We fetch a tiny slice of data to check current feature dimensions
            sample_data = self.fetch_data(ticker, self.config.backtest_years)
            if sample_data.empty:
                self.train(ticker)
                return "trained_fallback"

            X_sample, _ = self.prepare_features(sample_data, ticker)
            current_dim = X_sample.shape[1]
            logging.info(
                f"📊 Feature dimensions for {ticker}: current={current_dim}, cached={loaded_scaler.n_features_in_ if hasattr(loaded_scaler, 'n_features_in_') else 'unknown'}"
            )

            # Scaler feature count check
            if (
                hasattr(loaded_scaler, "n_features_in_")
                and loaded_scaler.n_features_in_ != current_dim
            ):
                logging.warning(
                    f"⚠️ Feature mismatch for {ticker}: current={current_dim}, cached={loaded_scaler.n_features_in_}. Retraining..."
                )
                self.train(ticker)
                return "retrained"

            self.scaler = loaded_scaler
            self.target_scaler = data_bundle.get(
                "target_scaler", None
            )  # Load target scaler for LSTM

            # 4. Load Model
            if "keras_path" in data_bundle or "lstm_h5" in data_bundle:
                from tensorflow.keras.models import load_model

                path = data_bundle.get("keras_path") or data_bundle.get("lstm_h5")
                # Final safety check: load_model might fail if architecture changed
                try:
                    self.model = load_model(path)
                except Exception:
                    self.train(ticker)
                    return "retrained_keras_error"
            else:
                self.model = data_bundle.get("model")

            return "loaded"

        except Exception as e:
            logging.error(f"Failed to load model for {ticker}: {e}. Retraining...")
            self.train(ticker)
            return "retrained_error"

    def predict(
        self, current_data: np.ndarray, date: Optional[pd.Timestamp] = None
    ) -> float:
        if self.model is None:
            logging.error("❌ Prediction failed: Model not loaded")
            raise ValueError("Model not loaded.")

        try:
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
                        pred = float(
                            self.target_scaler.inverse_transform([[pred]])[0][0]
                        )
                    return pred
                return 0.0
            X_input = (
                current_data[-1].reshape(1, -1)
                if len(current_data.shape) == 2
                else current_data.reshape(1, -1)
            )
            X_scaled = self.scaler.transform(X_input)
            return float(self.model.predict(X_scaled)[0])
        except Exception as e:
            logging.error(f"❌ Prediction error: {e}", exc_info=True)
            raise

    def get_latest_features(self, ticker: str) -> Optional[np.ndarray]:
        data = self.fetch_data(ticker, 1)
        if data.empty:
            return None
        X, y = self.prepare_features(data, ticker)
        if len(X) < self.sequence_length:
            return None
        return X[-self.sequence_length :]
