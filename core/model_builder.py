"""
ASX AI Trading System - Model Builder

Purpose: Factory for creating and training machine learning models with
standardized interfaces for prediction and backtesting.

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
logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
logging.getLogger("prophet").setLevel(logging.ERROR)

from typing import Optional, Any, Dict, List
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, RobustScaler
from core.config import Config


class ModelBuilder:
    """Handles data fetching, preprocessing, and model training."""

    def __init__(self, config: Config):
        self.config = config
        self.model: Optional[Any] = None
        self.scaler: Optional[Any] = None
        self.sequence_length = 30
        self._data_cache: Dict[str, pd.DataFrame] = {}

    def _init_scaler(self) -> Any:
        if self.config.scaler_type == "robust":
            return RobustScaler()
        return StandardScaler()

    def _init_model(self, input_dim: int = 0) -> Any:
        m_type = self.config.model_type

        if m_type == "xgboost":
            try:
                from xgboost import XGBRegressor

                return XGBRegressor(
                    n_estimators=100, learning_rate=0.05, random_state=42, n_jobs=-1
                )
            except ImportError:
                return RandomForestRegressor(n_estimators=100, random_state=42)

        elif m_type == "catboost":
            try:
                from catboost import CatBoostRegressor

                return CatBoostRegressor(
                    n_estimators=100,
                    learning_rate=0.05,
                    random_state=42,
                    verbose=0,
                    thread_count=-1,
                    allow_writing_files=False,
                )
            except ImportError:
                return RandomForestRegressor(n_estimators=100, random_state=42)

        elif m_type == "prophet":
            try:
                from prophet import Prophet

                return Prophet(daily_seasonality=True, yearly_seasonality=True)
            except Exception:
                return RandomForestRegressor(n_estimators=100, random_state=42)

        elif m_type == "lstm":
            try:
                import tensorflow as tf
                # Disable GPU if it's causing crashes on M3/Metal
                # tf.config.set_visible_devices([], 'GPU')

                from tensorflow.keras.models import Sequential
                from tensorflow.keras.layers import LSTM, Dense, Dropout

                model = Sequential(
                    [
                        LSTM(
                            32,
                            return_sequences=True,
                            input_shape=(self.sequence_length, input_dim),
                        ),
                        Dropout(0.1),
                        LSTM(16, return_sequences=False),
                        Dense(8, activation="relu"),
                        Dense(1),
                    ]
                )
                model.compile(optimizer="adam", loss="mean_squared_error")
                return model
            except Exception:
                from sklearn.ensemble import RandomForestRegressor

                return RandomForestRegressor(n_estimators=100, random_state=42)

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

    def fetch_data(self, ticker: str, years: int) -> pd.DataFrame:
        cache_key = f"{ticker}_{years}"
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]

        end_date = pd.Timestamp.now()
        start_date = end_date - pd.DateOffset(years=years)

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

    def prepare_features(self, data: pd.DataFrame):
        df = data.copy()

        # Double check Close is a Series
        if "Close" not in df.columns:
            raise KeyError(f"Column 'Close' missing. Found: {list(df.columns)}")

        df["MA5"] = df["Close"].rolling(window=5).mean()
        df["MA20"] = df["Close"].rolling(window=20).mean()

        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        exp1 = df["Close"].ewm(span=12, adjust=False).mean()
        exp2 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = exp1 - exp2
        df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["Daily_Return"] = df["Close"].pct_change()

        df["Target"] = df["Close"].shift(-1)
        df = df.dropna()

        features = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "MA5",
            "MA20",
            "RSI",
            "MACD",
            "Signal_Line",
            "Daily_Return",
        ]
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
        data = self.fetch_data(ticker, self.config.backtest_years)
        if data.empty:
            raise ValueError(f"No data for {ticker}")

        X, y = self.prepare_features(data)
        self.scaler = self._init_scaler()
        X_scaled = self.scaler.fit_transform(X)

        m_type = self.config.model_type
        if m_type == "lstm":
            try:
                X_seq, y_seq = self._create_sequences(X_scaled, y)
                self.model = self._init_model(input_dim=X.shape[1])
                self.model.fit(X_seq, y_seq, batch_size=32, epochs=10, verbose=0)
            except Exception:
                self.model = self._init_model()
                self.model.fit(X_scaled, y)
        elif m_type == "prophet":
            try:
                prophet_df = pd.DataFrame(
                    {"ds": data.index, "y": data["Close"].values.flatten()}
                )
                prophet_df["ds"] = pd.to_datetime(prophet_df["ds"]).dt.tz_localize(None)
                prophet_df = prophet_df.dropna()
                self.model = self._init_model()
                self.model.fit(prophet_df)
            except Exception:
                self.model = self._init_model()
                self.model.fit(X_scaled, y)
        else:
            self.model = self._init_model()
            self.model.fit(X_scaled, y)

        os.makedirs(self.config.model_path, exist_ok=True)
        model_filename = os.path.join(
            self.config.model_path, f"{ticker}_{m_type}_model.joblib"
        )
        if m_type == "lstm" and hasattr(self.model, "save"):
            h5_path = model_filename.replace(".joblib", ".h5")
            self.model.save(h5_path)
            joblib.dump({"scaler": self.scaler, "lstm_h5": h5_path}, model_filename)
        else:
            joblib.dump({"model": self.model, "scaler": self.scaler}, model_filename)

    def load_or_build(self, ticker: str) -> str:
        model_filename = os.path.join(
            self.config.model_path, f"{ticker}_{self.config.model_type}_model.joblib"
        )
        if self.config.rebuild_model or not os.path.exists(model_filename):
            self.train(ticker)
            return "trained"
        else:
            data_bundle = joblib.load(model_filename)
            self.scaler = data_bundle["scaler"]
            if "lstm_h5" in data_bundle:
                try:
                    from tensorflow.keras.models import load_model

                    self.model = load_model(data_bundle["lstm_h5"])
                except Exception:
                    self.model = data_bundle.get("model")
            else:
                self.model = data_bundle.get("model")
            return "loaded"

    def predict(
        self, current_data: np.ndarray, date: Optional[pd.Timestamp] = None
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
                return float(
                    self.model.predict(
                        X.reshape(1, self.sequence_length, -1), verbose=0
                    )[0][0]
                )
            return 0.0
        X_input = (
            current_data[-1].reshape(1, -1)
            if len(current_data.shape) == 2
            else current_data.reshape(1, -1)
        )
        X_scaled = self.scaler.transform(X_input)
        return float(self.model.predict(X_scaled)[0])

    def get_latest_features(self, ticker: str) -> Optional[np.ndarray]:
        data = self.fetch_data(ticker, 1)
        if data.empty:
            return None
        X, y = self.prepare_features(data)
        if len(X) < self.sequence_length:
            return None
        return X[-self.sequence_length :]
