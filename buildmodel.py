"""Model building module for training and loading AI investment models."""

import os
import joblib
import numpy as np
import pandas as pd
import yfinance as yf
from typing import Optional, Any
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.linear_model import ElasticNet
from sklearn.preprocessing import StandardScaler

try:
    from xgboost import XGBRegressor

    XGB_AVAILABLE = True
except Exception:
    XGB_AVAILABLE = False

try:
    from lightgbm import LGBMRegressor

    LGBM_AVAILABLE = True
except Exception:
    LGBM_AVAILABLE = False

try:
    from catboost import CatBoostRegressor

    CATBOOST_AVAILABLE = True
except Exception:
    CATBOOST_AVAILABLE = False

try:
    from prophet import Prophet

    PROPHET_AVAILABLE = True
except Exception:
    PROPHET_AVAILABLE = False

from sklearn.model_selection import train_test_split
from config import Config


class ModelBuilder:
    """Handles data fetching, preprocessing, and model training."""

    def __init__(self, config: Config):
        """Initializes ModelBuilder with configuration.

        Args:
            config: Configuration object.
        """
        self.config = config
        self.model: Optional[Any] = None
        self.scaler: Optional[StandardScaler] = None

    def _init_model(self) -> Any:
        """Initializes the model based on configuration model_type.

        Returns:
            Any: Initialized model object.
        """
        m_type = self.config.model_type

        if m_type == "xgboost":
            if not XGB_AVAILABLE:
                print("Warning: XGBoost not available, falling back to Random Forest")
                return RandomForestRegressor(n_estimators=100, random_state=42)
            return XGBRegressor(n_estimators=100, learning_rate=0.05, random_state=42)

        elif m_type == "lightgbm":
            if not LGBM_AVAILABLE:
                print("Warning: LightGBM not available, falling back to Random Forest")
                return RandomForestRegressor(n_estimators=100, random_state=42)
            return LGBMRegressor(n_estimators=100, learning_rate=0.05, random_state=42)

        elif m_type == "catboost":
            if not CATBOOST_AVAILABLE:
                print("Warning: CatBoost not available, falling back to Random Forest")
                return RandomForestRegressor(n_estimators=100, random_state=42)
            return CatBoostRegressor(
                n_estimators=100, learning_rate=0.05, random_state=42, verbose=0
            )

        elif m_type == "elastic_net":
            return ElasticNet(alpha=1.0, l1_ratio=0.5, random_state=42)

        elif m_type == "prophet":
            if not PROPHET_AVAILABLE:
                print("Warning: Prophet not available, falling back to Random Forest")
                return RandomForestRegressor(n_estimators=100, random_state=42)
            return Prophet(daily_seasonality=True, yearly_seasonality=True)

        elif m_type == "svr":
            return SVR(kernel="rbf", C=10.0, epsilon=0.01)

        # Default to random_forest
        return RandomForestRegressor(n_estimators=100, random_state=42)

    def fetch_data(self, ticker: str, years: int) -> Any:
        """Fetches historical OHLCV data from Yahoo Finance.

        Args:
            ticker: ASX ticker (e.g., 'BHP.AX').
            years: Number of years of history.

        Returns:
            pd.DataFrame: Historical price data.
        """
        end_date = pd.Timestamp.now()
        start_date = end_date - pd.DateOffset(years=years)
        data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True)
        return data

    def prepare_features(self, data: pd.DataFrame) -> Any:
        """Prepares features and labels for training.

        Args:
            data: Raw OHLCV data.

        Returns:
            tuple: (X, y) features and labels.
        """
        df = data.copy()

        # Handle yfinance MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 1. Moving Averages
        df["MA5"] = df["Close"].rolling(window=5).mean()
        df["MA20"] = df["Close"].rolling(window=20).mean()

        # 2. RSI (Relative Strength Index)
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # 3. MACD (Moving Average Convergence Divergence)
        exp1 = df["Close"].ewm(span=12, adjust=False).mean()
        exp2 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = exp1 - exp2
        df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()

        # 4. Daily Return
        df["Daily_Return"] = df["Close"].pct_change()

        # Target: Next day's Close price
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

    def train(self, ticker: str) -> None:
        """Trains the AI model for a specific ticker.

        Args:
            ticker: ASX ticker.
        """
        print(f"Training model for {ticker}...")
        data = self.fetch_data(ticker, self.config.backtest_years)
        if data.empty:
            raise ValueError(f"No data found for {ticker}")

        X, y = self.prepare_features(data)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)

        self.model = self._init_model()
        assert self.model is not None

        # Prophet handles training differently (it needs a dataframe, not X, y)
        if self.config.model_type == "prophet" and PROPHET_AVAILABLE:
            prophet_df = data.reset_index()[["Date", "Close"]].rename(
                columns={"Date": "ds", "Close": "y"}
            )
            # Ensure no timezone in ds for Prophet
            prophet_df["ds"] = prophet_df["ds"].dt.tz_localize(None)
            self.model.fit(prophet_df)
        else:
            self.model.fit(X_train_scaled, y_train)

        # Save model and scaler
        os.makedirs(self.config.model_path, exist_ok=True)
        model_filename = os.path.join(
            self.config.model_path, f"{ticker}_{self.config.model_type}_model.joblib"
        )
        joblib.dump({"model": self.model, "scaler": self.scaler}, model_filename)
        print(f"Model and Scaler saved to {model_filename}")

    def load_or_build(self, ticker: str) -> None:
        """Loads existing model or trains a new one.

        Args:
            ticker: ASX ticker.
        """
        model_filename = os.path.join(
            self.config.model_path, f"{ticker}_{self.config.model_type}_model.joblib"
        )
        if self.config.rebuild_model or not os.path.exists(model_filename):
            self.train(ticker)
        else:
            print(f"Loading existing model and scaler for {ticker}...")
            data_bundle = joblib.load(model_filename)
            self.model = data_bundle["model"]
            self.scaler = data_bundle["scaler"]

    def get_latest_features(self, ticker: str) -> Optional[np.ndarray]:
        """Fetches and prepares the feature vector for the most recent day.

        Args:
            ticker: ASX ticker.

        Returns:
            Optional[np.ndarray]: The latest feature vector, or None if failed.
        """
        # Fetch slightly more than needed for indicators
        data = self.fetch_data(ticker, 1)  # 1 year is enough for MA20/RSI/MACD
        if data.empty:
            return None

        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Re-calculate indicators
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

        df = df.dropna()
        if df.empty:
            return None

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

        raw_features = df[features].iloc[-1].values
        if self.scaler is not None:
            scaled_features = self.scaler.transform(raw_features.reshape(1, -1))[0]
            return np.array(scaled_features)
        return np.array(raw_features)

    def predict(
        self, current_data: np.ndarray, date: Optional[pd.Timestamp] = None
    ) -> float:
        """Generates a price prediction.

        Args:
            current_data: Feature vector for the current state.
            date: Timestamp for the prediction (required for Prophet).

        Returns:
            float: Predicted next-day price.
        """
        if self.model is None:
            raise ValueError("Model not loaded or trained.")

        # Prophet handles prediction differently
        if self.config.model_type == "prophet" and PROPHET_AVAILABLE:
            if date is None:
                # Use current date as fallback
                date = pd.Timestamp.now()

            # Predict for the next day
            future_date = date + pd.DateOffset(days=1)
            future = pd.DataFrame({"ds": [future_date.tz_localize(None)]})
            forecast = self.model.predict(future)
            return float(forecast["yhat"].iloc[0])

        # Standard scikit-learn style prediction
        X = current_data.reshape(1, -1)
        if self.scaler is not None:
            X = self.scaler.transform(X)

        return float(self.model.predict(X)[0])
