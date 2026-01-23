"""Model building module for training and loading AI investment models."""

import os
import joblib
import numpy as np
import pandas as pd
import yfinance as yf
from typing import Optional, Any
from sklearn.ensemble import RandomForestRegressor
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
        data = yf.download(ticker, start=start_date, end=end_date)
        return data

    def prepare_features(self, data: pd.DataFrame) -> Any:
        """Prepares features and labels for training.

        Args:
            data: Raw OHLCV data.

        Returns:
            tuple: (X, y) features and labels.
        """
        df = data.copy()

        # 1. Moving Averages
        df["MA5"] = df["Adj Close"].rolling(window=5).mean()
        df["MA20"] = df["Adj Close"].rolling(window=20).mean()

        # 2. RSI (Relative Strength Index)
        delta = df["Adj Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # 3. MACD (Moving Average Convergence Divergence)
        exp1 = df["Adj Close"].ewm(span=12, adjust=False).mean()
        exp2 = df["Adj Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = exp1 - exp2
        df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()

        # 4. Daily Return
        df["Daily_Return"] = df["Adj Close"].pct_change()

        # Target: Next day's Adj Close price
        df["Target"] = df["Adj Close"].shift(-1)

        df = df.dropna()

        features = [
            "Open",
            "High",
            "Low",
            "Adj Close",
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

        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        assert self.model is not None
        self.model.fit(X_train, y_train)

        # Save model
        os.makedirs(self.config.model_path, exist_ok=True)
        model_filename = os.path.join(self.config.model_path, f"{ticker}_model.joblib")
        joblib.dump(self.model, model_filename)
        print(f"Model saved to {model_filename}")

    def load_or_build(self, ticker: str) -> None:
        """Loads existing model or trains a new one.

        Args:
            ticker: ASX ticker.
        """
        model_filename = os.path.join(self.config.model_path, f"{ticker}_model.joblib")
        if self.config.rebuild_model or not os.path.exists(model_filename):
            self.train(ticker)
        else:
            print(f"Loading existing model for {ticker}...")
            self.model = joblib.load(model_filename)

    def predict(self, current_data: np.ndarray) -> float:
        """Generates a price prediction.

        Args:
            current_data: Feature vector for the current state.

        Returns:
            float: Predicted next-day price.
        """
        if self.model is None:
            raise ValueError("Model not loaded or trained.")
        return float(self.model.predict(current_data.reshape(1, -1))[0])
