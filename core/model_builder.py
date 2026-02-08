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
    tf.autograph.set_verbosity(0)
except (ImportError, Exception):
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
        available = ["random_forest", "gradient_boosting"]

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

        if m_type == "catboost":
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

        elif m_type == "gradient_boosting":
            logging.info("Initialized Scikit-Learn Gradient Boosting model.")
            return GradientBoostingRegressor(n_estimators=100, random_state=42)

        elif m_type == "prophet":
            from prophet import Prophet

            logging.info("Initialized Prophet model.")
            return Prophet(daily_seasonality="auto", yearly_seasonality="auto")

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
            model.compile(optimizer="adam", loss="huber")
            return model

        logging.info("Initialized Scikit-Learn Random Forest model.")
        return RandomForestRegressor(n_estimators=100, random_state=42)

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
        known_etfs = ["SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "VEU"]
        if ticker in known_etfs:
            return True
        return False

    def _ensure_market_data(self):
        """Pre-fetch macro data (^VIX, ^TNX)."""
        if self._market_data is not None:
            return

        try:
            indices = self.config.market_indices
            if not indices:
                return

            tickers = list(indices.values())
            df_raw = yf.download(tickers, period="10y", progress=False)
            if df_raw is None or df_raw.empty:
                return

            df: Any = df_raw["Close"] if "Close" in df_raw.columns else df_raw

            # Normalize index for consistency
            dt_idx: Any = pd.to_datetime(df.index)
            df.index = dt_idx.tz_localize(None).normalize()

            # Rename to internal standard
            rename_map = {v: f"MKT_{k}" for k, v in indices.items()}
            df = df.rename(columns=rename_map)

            self._market_data = df.ffill().fillna(0)
        except Exception as e:
            logging.warning(f"Failed to fetch market data: {e}")

    def fetch_data(self, ticker: str, years: int) -> pd.DataFrame:
        """Fetch historical price data with caching."""
        cache_key = f"{ticker}_{years}"
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]

        end_date = pd.Timestamp.now()
        start_date = end_date - pd.DateOffset(years=years) - pd.DateOffset(days=90)

        try:
            df_raw = yf.download(
                ticker, start=start_date, end=end_date, auto_adjust=True, progress=False
            )

            if df_raw is None or df_raw.empty:
                return pd.DataFrame()

            df: Any = df_raw

            # Clean columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [
                    str(c[0]) if isinstance(c, tuple) else str(c) for c in df.columns
                ]

            # Standardize names and normalize index
            df.index.name = "Date"
            dt_idx: Any = pd.to_datetime(df.index)
            df.index = dt_idx.tz_localize(None).normalize()

            self._data_cache[cache_key] = df
            return df
        except Exception as e:
            logging.error(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()

    def prefetch_data_batch(self, tickers: List[str], years: int):
        """Sequential pre-fetch."""
        for ticker in tickers:
            self.fetch_data(ticker, years)

    def prepare_features(
        self, data: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Unified feature engineering pipeline."""
        if data.empty:
            return np.array([], dtype=np.float32), np.array([], dtype=np.float32), []

        df = data.copy()

        # Indicators
        df["MA5"] = df["Close"].rolling(window=5).mean()
        df["MA20"] = df["Close"].rolling(window=20).mean()
        df["MA50"] = df["Close"].rolling(window=50).mean()

        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        df["RSI"] = 100 - (100 / (1 + rs))

        exp1 = df["Close"].ewm(span=12, adjust=False).mean()
        exp2 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = exp1 - exp2
        df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()

        df["BB_Middle"] = df["Close"].rolling(window=20).mean()
        df["BB_Std"] = df["Close"].rolling(window=20).std()
        df["BB_Upper"] = df["BB_Middle"] + (2 * df["BB_Std"])
        df["BB_Lower"] = df["BB_Middle"] - (2 * df["BB_Std"])
        df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / (df["BB_Middle"] + 1e-9)

        high_low = df["High"] - df["Low"]
        high_close = np.abs(df["High"] - df["Close"].shift())
        low_close = np.abs(df["Low"] - df["Close"].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["ATR"] = tr.rolling(window=14).mean()

        df["Daily_Return"] = df["Close"].pct_change(fill_method=None)

        # Market Context
        self._ensure_market_data()
        m_data = self._market_data
        if m_data is not None and not m_data.empty:
            market_subset = m_data.shift(1).reindex(df.index).ffill()
            df = df.join(market_subset)

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

        scaler = self._init_scaler()
        X_scaled = scaler.fit_transform(X)

        m_type = self.config.model_type
        model = None
        if m_type == "lstm":
            X_seq, y_seq = self._create_sequences(X_scaled, y)
            model = self._init_model(input_dim=X.shape[1])
            model.fit(X_seq, y_seq, batch_size=32, epochs=20, verbose=0)
        elif m_type == "prophet":
            from prophet import Prophet

            p_df = pd.DataFrame({"ds": data.index, "y": data["Close"].values.flatten()})
            p_df["ds"] = pd.to_datetime(p_df["ds"]).dt.tz_localize(None)
            model = Prophet(daily_seasonality=True, yearly_seasonality=True)
            model.fit(p_df.dropna())
        else:
            model = self._init_model()
            model.fit(X_scaled, y)

        # Persistence
        self.model = model
        self.scaler = scaler

        os.makedirs(self.config.model_path, exist_ok=True)
        model_filename = os.path.join(
            self.config.model_path, f"{ticker}_{m_type}_model.joblib"
        )
        joblib.dump(
            {
                "model": model,
                "scaler": scaler,
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

            # Validation
            sample_data = self.fetch_data(ticker, self.config.backtest_years)
            X_sample, _, _ = self.prepare_features(sample_data)

            if bundle["features_count"] != X_sample.shape[1]:
                logging.warning(f"Feature mismatch for {ticker}. Retraining...")
                self.train(ticker)
                return "retrained"

            self.scaler = bundle["scaler"]
            self.model = bundle["model"]
            return "loaded"
        except Exception as e:
            logging.error(f"Failed to load model for {ticker}: {e}")
            self.train(ticker)
            return "retrained_on_error"
