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
from typing import Optional, Any
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split
from core.config import Config

# Dynamic imports with availability flags
try:
    from xgboost import XGBRegressor

    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

try:
    from catboost import CatBoostRegressor

    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False

try:
    from prophet import Prophet

    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout

    LSTM_AVAILABLE = True
except ImportError:
    LSTM_AVAILABLE = False


class ModelBuilder:
    """Handles data fetching, preprocessing, and model training."""

    def __init__(self, config: Config):
        self.config = config
        self.model: Optional[Any] = None
        self.scaler: Optional[Any] = None
        self.sequence_length = 30  # Default lookback for LSTM

    def _init_scaler(self) -> Any:
        if self.config.scaler_type == "robust":
            return RobustScaler()
        return StandardScaler()

    def _init_model(self, input_dim: int = 0) -> Any:
        m_type = self.config.model_type

        if m_type == "xgboost":
            if not XGB_AVAILABLE:
                return RandomForestRegressor(n_estimators=100, random_state=42)
            return XGBRegressor(n_estimators=100, learning_rate=0.05, random_state=42)

        elif m_type == "catboost":
            if not CATBOOST_AVAILABLE:
                return RandomForestRegressor(n_estimators=100, random_state=42)
            return CatBoostRegressor(
                n_estimators=100, learning_rate=0.05, random_state=42, verbose=0
            )

        elif m_type == "prophet":
            if not PROPHET_AVAILABLE:
                return RandomForestRegressor(n_estimators=100, random_state=42)
            return Prophet(daily_seasonality=True, yearly_seasonality=True)

        elif m_type == "lstm":
            if not LSTM_AVAILABLE:
                return RandomForestRegressor(n_estimators=100, random_state=42)

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

        return RandomForestRegressor(n_estimators=100, random_state=42)

    def fetch_data(self, ticker: str, years: int) -> pd.DataFrame:
        end_date = pd.Timestamp.now()
        start_date = end_date - pd.DateOffset(years=years)
        data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True)
        return data

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
        df["RSI"] = 100 - (100 / (1 + (gain / loss)))

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

        if self.config.model_type == "lstm" and LSTM_AVAILABLE:
            X_seq, y_seq = self._create_sequences(X_scaled, y)
            self.model = self._init_model(input_dim=X.shape[1])
            self.model.fit(X_seq, y_seq, batch_size=32, epochs=10, verbose=0)
        elif self.config.model_type == "prophet" and PROPHET_AVAILABLE:
            # Prophet requires DataFrame with 'ds' (datetime) and 'y' (numeric) columns
            prophet_df = pd.DataFrame({
                'ds': data.index,
                'y': data['Close'].values
            })
            # Remove timezone if present
            prophet_df['ds'] = pd.to_datetime(prophet_df['ds']).dt.tz_localize(None)
            # Ensure y is numeric
            prophet_df['y'] = pd.to_numeric(prophet_df['y'], errors='coerce')
            prophet_df = prophet_df.dropna()
            
            self.model = self._init_model()
            self.model.fit(prophet_df)
        else:
            self.model = self._init_model()
            self.model.fit(X_scaled, y)

        os.makedirs(self.config.model_path, exist_ok=True)
        model_filename = os.path.join(
            self.config.model_path, f"{ticker}_{self.config.model_type}_model.joblib"
        )

        if self.config.model_type == "lstm" and LSTM_AVAILABLE:
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
            if "lstm_h5" in data_bundle and LSTM_AVAILABLE:
                self.model = load_model(data_bundle["lstm_h5"])
            else:
                self.model = data_bundle.get("model")

    def predict(
        self, current_data: np.ndarray, date: Optional[pd.Timestamp] = None
    ) -> float:
        if self.model is None:
            raise ValueError("Model not loaded.")

        if self.config.model_type == "prophet" and PROPHET_AVAILABLE:
            future = pd.DataFrame(
                {"ds": [(date + pd.DateOffset(days=1)).tz_localize(None)]}
            )
            return float(self.model.predict(future)["yhat"].iloc[0])

        if self.config.model_type == "lstm" and LSTM_AVAILABLE:
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
