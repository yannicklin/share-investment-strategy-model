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
import requests
import time
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
        self.sequence_length = 30  # Default lookback for LSTM
        self._data_cache: Dict[str, pd.DataFrame] = {}
        # Removing custom session to let yfinance handle its own session requirements (curl_cffi)

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
                from tensorflow.keras.models import Sequential
                from tensorflow.keras.layers import LSTM, Dense, Dropout

                model = Sequential(
                    [
                        LSTM(
                            50,
                            return_sequences=True,
                            input_shape=(self.sequence_length, input_dim),
                        ),
                        Dropout(0.2),
                        LSTM(50, return_sequences=False),
                        Dropout(0.2),
                        Dense(25),
                        Dense(1),
                    ]
                )
                model.compile(optimizer="adam", loss="mean_squared_error")
                return model
            except Exception:
                return RandomForestRegressor(n_estimators=100, random_state=42)

        return RandomForestRegressor(n_estimators=100, random_state=42)

    def fetch_data(self, ticker: str, years: int) -> pd.DataFrame:
        cache_key = f"{ticker}_{years}"
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]

        end_date = pd.Timestamp.now()
        start_date = end_date - pd.DateOffset(years=years)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                data = yf.download(
                    ticker,
                    start=start_date,
                    end=end_date,
                    auto_adjust=True,
                    progress=False,
                    timeout=30,
                    threads=False,  # Sequential to avoid rate limits
                )
                if not data.empty:
                    self._data_cache[cache_key] = data
                    return data

                # If data is empty but no exception, might be rate limited
                time.sleep(1 * (attempt + 1))
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Final error fetching data for {ticker}: {e}")
                time.sleep(2 * (attempt + 1))

        return pd.DataFrame()

    def prefetch_data_batch(self, tickers: List[str], years: int):
        """Fetches multiple tickers in one go to reduce overhead and connection count."""
        if not tickers:
            return

        end_date = pd.Timestamp.now()
        start_date = end_date - pd.DateOffset(years=years)

        # Filter out already cached
        to_fetch = [t for t in tickers if f"{t}_{years}" not in self._data_cache]
        if not to_fetch:
            return

        # Download in batches of 20 to balance speed and reliability
        batch_size = 20
        for i in range(0, len(to_fetch), batch_size):
            batch = to_fetch[i : i + batch_size]
            try:
                data = yf.download(
                    batch,
                    start=start_date,
                    end=end_date,
                    auto_adjust=True,
                    progress=False,
                    timeout=60,
                    group_by="ticker",
                )

                for ticker in batch:
                    cache_key = f"{ticker}_{years}"
                    if len(batch) == 1:
                        ticker_df = data
                    else:
                        try:
                            ticker_df = data[ticker]
                        except KeyError:
                            ticker_df = pd.DataFrame()

                    if not ticker_df.empty:
                        # Standardize columns (remove multi-index if single ticker result)
                        if isinstance(ticker_df.columns, pd.MultiIndex):
                            ticker_df.columns = ticker_df.columns.get_level_values(0)
                        self._data_cache[cache_key] = ticker_df

                time.sleep(1)  # Gap between batches
            except Exception as e:
                print(f"Batch prefetch error: {e}")

    def prepare_features(self, data: pd.DataFrame):
        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

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
        print(f"Training {self.config.model_type} for {ticker}...")
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
                # Prophet requires DataFrame with 'ds' (datetime) and 'y' (numeric) columns
                close_data = data["Close"]
                if isinstance(close_data, pd.DataFrame):
                    close_data = close_data.iloc[:, 0]

                prophet_df = pd.DataFrame(
                    {"ds": data.index, "y": close_data.values.flatten()}
                )
                prophet_df["ds"] = pd.to_datetime(prophet_df["ds"]).dt.tz_localize(None)
                prophet_df["y"] = pd.to_numeric(prophet_df["y"], errors="coerce")
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

    def load_or_build(self, ticker: str):
        model_filename = os.path.join(
            self.config.model_path, f"{ticker}_{self.config.model_type}_model.joblib"
        )
        if self.config.rebuild_model or not os.path.exists(model_filename):
            self.train(ticker)
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
            if len(current_data.shape) == 2:  # (Seq, Features)
                X = self.scaler.transform(current_data)
                return float(
                    self.model.predict(
                        X.reshape(1, self.sequence_length, -1), verbose=0
                    )[0][0]
                )
            return 0.0

        if len(current_data.shape) == 2:
            X_input = current_data[-1].reshape(1, -1)
        else:
            X_input = current_data.reshape(1, -1)

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
