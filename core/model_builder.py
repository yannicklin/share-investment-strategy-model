"""
USA AI Trading System - Model Builder

Purpose: Factory for creating and training machine learning models with
standardized interfaces for prediction and backtesting for US stocks.

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

from typing import Optional, Any, Dict, List, Tuple
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, RobustScaler
from core.config import Config


class ModelBuilder:
    """Handles data fetching, preprocessing, and model training for US stocks."""

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
        """Fetch long name using yfinance."""
        try:
            info = yf.Ticker(ticker).info
            if info is not None:
                return str(info.get("longName", ticker))
            return ticker
        except Exception:
            return ticker

    def is_etf(self, ticker: str) -> bool:
        """Heuristic for US ETFs."""
        try:
            info = yf.Ticker(ticker).info
            return info.get("quoteType") == "ETF"
        except Exception:
            known_etfs = ["SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "VEU"]
            return ticker in known_etfs

    def fetch_data(self, ticker: str, years: int) -> pd.DataFrame:
        """Fetch historical price data with caching and normalization."""
        cache_key = f"{ticker}_{years}"
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]

        end_date = pd.Timestamp.now()
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
            except Exception as e:
                logging.error(
                    f"Error fetching data for {ticker} (attempt {attempt + 1}): {e}"
                )
        return pd.DataFrame()

    def prefetch_data_batch(self, tickers: List[str], years: int):
        """Batch pre-fetch data for multiple tickers."""
        if not tickers:
            return
        end_date = pd.Timestamp.now()
        start_date = end_date - pd.DateOffset(years=years) - pd.DateOffset(days=90)
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
        """Pre-fetch macro data for US market context."""
        if self._market_data is not None:
            return

        logging.info("Fetching US market and macro data...")
        market_tickers = {
            **self.config.market_indices,
            **self.config.macro_indicators,
        }

        start_date = pd.Timestamp.now() - pd.DateOffset(years=10)
        market_df = pd.DataFrame()

        for name, ticker in market_tickers.items():
            try:
                df = yf.download(
                    ticker,
                    start=start_date,
                    progress=False,
                    auto_adjust=True,
                    threads=False,
                )

                if df.empty:
                    continue

                df = self._normalize_df(df, ticker)

                if "Close" in df.columns:
                    col_name = f"MKT_{name}"
                    market_df[col_name] = df["Close"]
            except Exception as e:
                logging.warning(f"Failed to fetch market data {name} ({ticker}): {e}")

        self._market_data = market_df.ffill().fillna(0)

    def prepare_features(
        self, data: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Unified feature engineering pipeline."""
        if data.empty:
            return np.array([], dtype=np.float32), np.array([], dtype=np.float32), []

        df = data.copy()

        # 1. Basic Moving Averages
        df["MA5"] = df["Close"].rolling(window=5).mean()
        df["MA20"] = df["Close"].rolling(window=20).mean()
        df["MA50"] = df["Close"].rolling(window=50).mean()

        # 2. RSI
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        df["RSI"] = 100 - (100 / (1 + rs))

        # 3. MACD
        exp1 = df["Close"].ewm(span=12, adjust=False).mean()
        exp2 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = exp1 - exp2
        df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()

        # 4. Bollinger Bands
        df["BB_Middle"] = df["Close"].rolling(window=20).mean()
        df["BB_Std"] = df["Close"].rolling(window=20).std()
        df["BB_Upper"] = df["BB_Middle"] + (2 * df["BB_Std"])
        df["BB_Lower"] = df["BB_Middle"] - (2 * df["BB_Std"])
        df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / (df["BB_Middle"] + 1e-9)

        # 5. ATR
        high_low = df["High"] - df["Low"]
        high_close = np.abs(df["High"] - df["Close"].shift())
        low_close = np.abs(df["Low"] - df["Close"].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["ATR"] = tr.rolling(window=14).mean()

        # 6. Market Context
        self._ensure_market_data()
        m_data = self._market_data
        if m_data is not None and not m_data.empty:
            market_subset = m_data.shift(1).reindex(df.index).ffill()
            df = df.join(market_subset)

        df["Daily_Return"] = df["Close"].pct_change(fill_method=None)

        # Target: Next Day Close
        df["Target"] = df["Close"].shift(-1)

        # Clean up
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna()

        if df.empty:
            return np.array([], dtype=np.float32), np.array([], dtype=np.float32), []

        # Standard Feature List
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
        if m_data is not None:
            for col in m_data.columns:
                col_str = str(col)
                if col_str in df.columns and col_str not in features:
                    features.append(col_str)

        return (
            df[features].values.astype(np.float32),
            df["Target"].values.astype(np.float32),
            features,
        )

    def _create_sequences(
        self, data_scaled: np.ndarray, target: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Convert time-series to supervised sequences for LSTM."""
        if len(data_scaled) <= self.sequence_length:
            return np.array([], dtype=np.float32), np.array([], dtype=np.float32)

        X_seq, y_seq = [], []
        for i in range(len(data_scaled) - self.sequence_length):
            X_seq.append(data_scaled[i : i + self.sequence_length])
            y_seq.append(target[i + self.sequence_length])
        return np.array(X_seq, dtype=np.float32), np.array(y_seq, dtype=np.float32)

    def train(self, ticker: str):
        """Full training pipeline for a single ticker."""
        data = self.fetch_data(ticker, self.config.backtest_years)
        if data.empty:
            raise ValueError(f"No historical data available for {ticker}")

        X, y, features_list = self.prepare_features(data)
        if len(X) < 50:
            raise ValueError(f"Insufficient data for training {ticker} (min 50 days).")

        self.scaler = self._init_scaler()
        X_scaled = self.scaler.fit_transform(X)

        m_type = self.config.model_type

        # For LSTM, also scale the target
        target_scaler = None
        y_scaled = y
        if m_type == "lstm":
            from sklearn.preprocessing import StandardScaler

            target_scaler = StandardScaler()
            y_scaled = target_scaler.fit_transform(y.reshape(-1, 1)).flatten()

        if m_type == "lstm":
            logging.info(f"Training LSTM for {ticker}. Input Shape: {X_scaled.shape}")
            X_seq, y_seq = self._create_sequences(X_scaled, y_scaled)
            if len(X_seq) == 0:
                raise ValueError(f"Not enough data for LSTM sequences for {ticker}")
            self.model = self._init_model(input_dim=X.shape[1])
            self.model.fit(X_seq, y_seq, batch_size=32, epochs=10, verbose=0)
            self.target_scaler = target_scaler
        elif m_type == "prophet":
            from prophet import Prophet

            p_df = pd.DataFrame({"ds": data.index, "y": data["Close"].values.flatten()})
            p_df["ds"] = pd.to_datetime(p_df["ds"]).dt.tz_localize(None)
            self.model = Prophet(daily_seasonality=True, yearly_seasonality=True)
            self.model.fit(p_df.dropna())
            self.target_scaler = None
        else:
            self.model = self._init_model()
            self.model.fit(X_scaled, y)
            self.target_scaler = None

        # Persistence
        os.makedirs(self.config.model_path, exist_ok=True)
        model_filename = os.path.join(
            self.config.model_path, f"{ticker}_{m_type}_model.joblib"
        )

        if m_type == "lstm" and hasattr(self.model, "save"):
            keras_path = model_filename.replace(".joblib", ".keras")
            self.model.save(keras_path)
            joblib.dump(
                {
                    "scaler": self.scaler,
                    "target_scaler": self.target_scaler,
                    "keras_path": keras_path,
                    "features_count": X.shape[1],
                    "features_list": features_list,
                },
                model_filename,
            )
        else:
            joblib.dump(
                {
                    "model": self.model,
                    "scaler": self.scaler,
                    "target_scaler": self.target_scaler,
                    "features_count": X.shape[1],
                    "features_list": features_list,
                    "timestamp": time.time(),
                },
                model_filename,
            )
        logging.info(f"Saved model to {model_filename}")

    def load_or_build(self, ticker: str) -> str:
        """Smart loader that checks for feature consistency."""
        model_filename = os.path.join(
            self.config.model_path, f"{ticker}_{self.config.model_type}_model.joblib"
        )

        if self.config.rebuild_model or not os.path.exists(model_filename):
            self.train(ticker)
            return "trained"

        try:
            bundle = joblib.load(model_filename)

            # Feature check
            sample_data = self.fetch_data(ticker, self.config.backtest_years)
            if sample_data.empty:
                self.train(ticker)
                return "retrained_no_data"

            X_sample, _, _ = self.prepare_features(sample_data)
            if bundle.get("features_count") != X_sample.shape[1]:
                logging.warning(f"Feature mismatch for {ticker}. Retraining...")
                self.train(ticker)
                return "retrained_mismatch"

            self.scaler = bundle["scaler"]
            self.target_scaler = bundle.get("target_scaler")

            if "keras_path" in bundle:
                from tensorflow.keras.models import load_model

                try:
                    self.model = load_model(bundle["keras_path"])
                except Exception:
                    self.train(ticker)
                    return "retrained_keras_error"
            else:
                self.model = bundle["model"]

            return "loaded"
        except Exception as e:
            logging.error(f"Failed to load model for {ticker}: {e}")
            self.train(ticker)
            return "retrained_error"

    def predict(
        self, current_data: np.ndarray, date: Optional[pd.Timestamp] = None
    ) -> float:
        """Standardized prediction interface."""
        if self.model is None:
            return 0.0

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
