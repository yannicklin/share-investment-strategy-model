"""
USA AI Trading System - Model Builder (USA Factory)

Purpose: Factory for creating and training machine learning models
using US market data with macro integration (^VIX, ^TNX).

Author: Yannick
Copyright (c) 2026 Yannick
"""

import os
import joblib
import numpy as np
import pandas as pd
import yfinance as yf
import logging
import gc
from typing import Optional, Any, Dict, List, Tuple
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, RobustScaler
from core.config import Config

# Suppress heavy logging
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

try:
    import tensorflow as tf

    tf.get_logger().setLevel("ERROR")
    tf.autograph.set_verbosity(0)
except ImportError:
    pass

logging.getLogger("prophet").setLevel(logging.ERROR)


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
        return (
            RobustScaler() if self.config.scaler_type == "robust" else StandardScaler()
        )

    @classmethod
    def get_available_models(cls) -> List[str]:
        available = ["random_forest", "gradient_boosting"]
        try:
            import catboost

            available.append("catboost")
        except ImportError:
            pass
        try:
            import prophet

            available.append("prophet")
        except ImportError:
            pass
        try:
            import tensorflow as tf

            available.append("lstm")
        except ImportError:
            pass
        return available

    def _init_model(self, input_dim: int = 0) -> Any:
        m_type = self.config.model_type
        if m_type == "catboost":
            from catboost import CatBoostRegressor

            return CatBoostRegressor(
                n_estimators=100,
                learning_rate=0.05,
                random_state=42,
                verbose=0,
                thread_count=-1,
                allow_writing_files=False,
            )
        elif m_type == "gradient_boosting":
            return GradientBoostingRegressor(n_estimators=100, random_state=42)
        elif m_type == "prophet":
            from prophet import Prophet

            return Prophet(daily_seasonality=True, yearly_seasonality=True)
        elif m_type == "lstm":
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import (
                LSTM,
                Dense,
                Dropout,
                Input,
                BatchNormalization,
            )

            model = Sequential(
                [
                    Input(shape=(self.sequence_length, input_dim)),
                    LSTM(64, return_sequences=True),
                    BatchNormalization(),
                    Dropout(0.2),
                    LSTM(32, return_sequences=False),
                    Dense(16, activation="relu"),
                    Dense(1),
                ]
            )
            model.compile(optimizer="adam", loss="huber")
            return model
        return RandomForestRegressor(n_estimators=100, random_state=42)

    def get_company_name(self, ticker: str) -> str:
        """Fetch long name using yfinance."""
        try:
            info = yf.Ticker(ticker).info
            return info.get("longName", ticker)
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
            tickers = ["^VIX", "^TNX"]
            df = yf.download(tickers, period="max", progress=False)["Close"]
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

            df = df.rename(columns={"^VIX": "MKT_VIX", "^TNX": "MKT_Yield10Y"})
            self._market_data = df.ffill().fillna(0)
        except Exception as e:
            logging.warning(f"Failed to fetch macro data: {e}")

    def fetch_data(self, ticker: str, years: int) -> pd.DataFrame:
        cache_key = f"{ticker}_{years}"
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]

        end_date = pd.Timestamp.now()
        start_date = end_date - pd.DateOffset(years=years) - pd.DateOffset(days=90)

        try:
            df = yf.download(
                ticker, start=start_date, end=end_date, auto_adjust=True, progress=False
            )
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [
                        c[0] if isinstance(c, tuple) else c for c in df.columns
                    ]

                self._ensure_market_data()
                if self._market_data is not None:
                    market_subset = self._market_data.shift(1).reindex(df.index).ffill()
                    df = df.join(market_subset).ffill().fillna(0)

                self._data_cache[cache_key] = df
                return df
        except Exception as e:
            logging.warning(f"Failed to fetch {ticker}: {e}")

        return pd.DataFrame()

    def prefetch_data_batch(self, tickers: List[str], years: int):
        for ticker in tickers:
            self.fetch_data(ticker, years)

    def prepare_features(self, data: pd.DataFrame):
        df = data.copy()
        df["Returns"] = df["Close"].pct_change()
        df["MA50"] = df["Close"].rolling(50).mean()
        df["MA200"] = df["Close"].rolling(200).mean()

        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df["RSI"] = 100 - (100 / (1 + (gain / (loss + 1e-9))))

        df["Target"] = df["Close"].shift(-1)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna()

        features = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "Returns",
            "MA50",
            "MA200",
            "RSI",
        ]
        if "MKT_VIX" in df.columns:
            features.append("MKT_VIX")
        if "MKT_Yield10Y" in df.columns:
            features.append("MKT_Yield10Y")

        return df[features].values, df["Target"].values

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
                self.model.fit(X_seq, y_seq, batch_size=32, epochs=50, verbose=0)
            except Exception:
                self.model = self._init_model()
                self.model.fit(X_scaled, y)
        elif m_type == "prophet":
            p_df = pd.DataFrame({"ds": data.index, "y": data["Close"].values.flatten()})
            p_df["ds"] = pd.to_datetime(p_df["ds"]).dt.tz_localize(None)
            self.model = self._init_model()
            self.model.fit(p_df.dropna())
        else:
            self.model = self._init_model()
            self.model.fit(X_scaled, y)

        os.makedirs(self.config.model_path, exist_ok=True)
        joblib.dump(
            {"model": self.model, "scaler": self.scaler, "features": X.shape[1]},
            os.path.join(self.config.model_path, f"{ticker}_{m_type}_model.joblib"),
        )

    def load_or_build(self, ticker: str) -> str:
        model_filename = os.path.abspath(
            os.path.join(
                self.config.model_path,
                f"{ticker}_{self.config.model_type}_model.joblib",
            )
        )

        if self.config.rebuild_model or not os.path.exists(model_filename):
            self.train(ticker)
            return "trained"

        try:
            bundle = joblib.load(model_filename)
            loaded_scaler = bundle["scaler"]

            sample_data = self.fetch_data(ticker, self.config.backtest_years)
            X_sample, _ = self.prepare_features(sample_data)
            if (
                hasattr(loaded_scaler, "n_features_in_")
                and loaded_scaler.n_features_in_ != X_sample.shape[1]
            ):
                self.train(ticker)
                return "retrained"

            self.scaler = loaded_scaler
            self.model = bundle["model"]
            return "loaded"
        except Exception:
            self.train(ticker)
            return "retrained_error"

    def predict(
        self, current_data: np.ndarray, date: Optional[pd.Timestamp] = None
    ) -> float:
        if self.model is None:
            raise ValueError("Model not loaded.")
        m_type = self.config.model_type
        if m_type == "prophet":
            future = pd.DataFrame(
                {"ds": [(date + pd.DateOffset(days=1)).tz_localize(None)]}
            )
            return float(self.model.predict(future)["yhat"].iloc[0])
        if m_type == "lstm":
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
        return float(self.model.predict(self.scaler.transform(X_input))[0])
