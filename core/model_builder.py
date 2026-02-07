"""
Taiwan Stock AI Trading System - Model Builder (FinMind-Centric)

Purpose: Factory for creating and training machine learning models.
Uses FinMind as the primary source for Taiwan market data, including
Institutional Flows and KD indicators.

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

# Suppress heavy logging
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
logging.getLogger("prophet").setLevel(logging.ERROR)

from typing import Optional, Any, Dict, List, Tuple
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
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
        self._stock_info_cache: Optional[pd.DataFrame] = None

    def _init_scaler(self) -> Any:
        return (
            RobustScaler() if self.config.scaler_type == "robust" else StandardScaler()
        )

    @classmethod
    def get_available_models(cls) -> List[str]:
        available = ["random_forest", "gradient_boosting"]
        try:
            from catboost import CatBoostRegressor

            available.append("catboost")
        except ImportError:
            pass
        try:
            from prophet import Prophet

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
            import tensorflow as tf
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
        """Fetch Chinese name using FinMind primarily."""
        try:
            from FinMind.data import DataLoader

            dl = DataLoader()
            if self._stock_info_cache is None:
                self._stock_info_cache = dl.taiwan_stock_info()

            stock_id = ticker.split(".")[0]
            match = self._stock_info_cache[
                self._stock_info_cache["stock_id"] == stock_id
            ]
            if not match.empty:
                return match.iloc[0]["stock_name"]
        except Exception:
            pass

        # Fallback to Yahoo
        try:
            info = yf.Ticker(ticker).info
            return info.get("longName", ticker)
        except Exception:
            return ticker

    def is_etf(self, ticker: str) -> bool:
        stock_id = ticker.split(".")[0]
        # Taiwan ETFs usually start with 00 or 03
        if stock_id.startswith("00") or stock_id.startswith("03"):
            return True
        return False

    def fetch_data(self, ticker: str, years: int) -> pd.DataFrame:
        cache_key = f"{ticker}_{years}"
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]

        end_date = pd.Timestamp.now()
        start_date = end_date - pd.DateOffset(years=years) - pd.DateOffset(days=90)

        # PRIMARY: FinMind
        try:
            from FinMind.data import DataLoader

            dl = DataLoader()
            stock_id = ticker.split(".")[0]
            df = dl.taiwan_stock_daily(
                stock_id=stock_id,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
            )
            if not df.empty:
                df = df.rename(
                    columns={
                        "open": "Open",
                        "max": "High",
                        "min": "Low",
                        "close": "Close",
                        "Trading_Volume": "Volume",
                    }
                )
                df["date"] = pd.to_datetime(df["date"])
                df.set_index("date", inplace=True)

                # Add Institutional Net Buy
                try:
                    inst = dl.taiwan_stock_institutional_investors(
                        stock_id=stock_id,
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d"),
                    )
                    if not inst.empty:
                        inst["date"] = pd.to_datetime(inst["date"])
                        # Sum up Buy - Sell for all institutions
                        inst["net"] = inst["buy"] - inst["sell"]
                        inst_pivot = inst.pivot_table(
                            index="date", values="net", aggfunc="sum"
                        ).fillna(0)
                        df["Inst_Net_Buy"] = inst_pivot["net"]
                    else:
                        df["Inst_Net_Buy"] = 0
                except Exception:
                    df["Inst_Net_Buy"] = 0

                df.fillna(0, inplace=True)
                self._data_cache[cache_key] = df
                return df
        except Exception as e:
            logging.warning(
                f"FinMind failed for {ticker}: {e}. Falling back to YFinance."
            )

        # FALLBACK: Yahoo Finance
        try:
            data = yf.download(
                ticker, start=start_date, end=end_date, auto_adjust=True, progress=False
            )
            if not data.empty:
                # Basic normalization
                df = data.copy()
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [
                        c[0] if isinstance(c, tuple) else c for c in df.columns
                    ]
                df.rename(
                    columns={
                        "Open": "Open",
                        "High": "High",
                        "Low": "Low",
                        "Close": "Close",
                        "Volume": "Volume",
                    },
                    inplace=True,
                )
                df["Inst_Net_Buy"] = 0
                self._data_cache[cache_key] = df
                return df
        except Exception:
            pass

        return pd.DataFrame()

    def prefetch_data_batch(self, tickers: List[str], years: int):
        for ticker in tickers:
            self.fetch_data(ticker, years)

    def prepare_features(self, data: pd.DataFrame):
        df = data.copy()
        df["MA5"] = df["Close"].rolling(5).mean()
        df["MA20"] = df["Close"].rolling(20).mean()
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df["RSI"] = 100 - (100 / (1 + (gain / loss)))
        df["MACD"] = (
            df["Close"].ewm(span=12, adjust=False).mean()
            - df["Close"].ewm(span=26, adjust=False).mean()
        )
        df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["Daily_Return"] = df["Close"].pct_change(fill_method=None)

        # KD
        low_9 = df["Low"].rolling(9).min()
        high_9 = df["High"].rolling(9).max()
        rsv = (df["Close"] - low_9) / (high_9 - low_9 + 1e-9) * 100
        df["K"] = rsv.ewm(com=2).mean()
        df["D"] = df["K"].ewm(com=2).mean()

        if "Inst_Net_Buy" not in df.columns:
            df["Inst_Net_Buy"] = 0

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
            "K",
            "D",
            "Inst_Net_Buy",
            "Daily_Return",
        ]
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
            try:
                p_df = pd.DataFrame(
                    {"ds": data.index, "y": data["Close"].values.flatten()}
                )
                p_df["ds"] = pd.to_datetime(p_df["ds"]).dt.tz_localize(None)
                self.model = self._init_model()
                self.model.fit(p_df.dropna())
            except Exception:
                self.model = self._init_model()
                self.model.fit(X_scaled, y)
        else:
            self.model = self._init_model()
            self.model.fit(X_scaled, y)

        os.makedirs(self.config.model_path, exist_ok=True)
        joblib.dump(
            {"model": self.model, "scaler": self.scaler},
            os.path.join(self.config.model_path, f"{ticker}_{m_type}_model.joblib"),
        )

    def load_or_build(self, ticker: str) -> str:
        # Construct absolute path to avoid directory confusion
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
            self.scaler = bundle["scaler"]
            self.model = bundle["model"]

            # Validation check to ensure scaler is fitted
            if not hasattr(self.scaler, "mean_") and not hasattr(
                self.scaler, "center_"
            ):
                # If scaler looks unfitted, force retrain
                self.train(ticker)
                return "retrained_corrupt"

            return "loaded"
        except Exception:
            # If load fails, retrain immediately
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
            X = self.scaler.transform(current_data)
            return float(
                self.model.predict(X.reshape(1, self.sequence_length, -1), verbose=0)[
                    0
                ][0]
            )
        X_input = current_data[-1].reshape(1, -1)
        X_scaled = self.scaler.transform(X_input)
        return float(self.model.predict(X_scaled)[0])
