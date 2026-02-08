"""
Trading AI System - Model Builder (USA Factory)

Purpose: Factory for creating and training machine learning models (Random Forest, LSTM, etc.)
using US market data (yfinance). Adapted for robust handling of US ticker symbols.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import pandas as pd
import numpy as np
import yfinance as yf
import joblib
import os
import logging
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score
from sklearn.preprocessing import StandardScaler
from typing import Tuple, Any, Dict

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelBuilder:
    """
    Factory class for building and training AI models on US stock data.
    """

    SUPPORTED_ALGORITHMS = [
        "Random Forest",
        "Gradient Boosting (GBDT)",
        "LSTM (Neural Net)",  # Placeholder for future deep learning expansion
        "Prophet (Trend)",  # Placeholder for time-series forecasting
    ]

    def __init__(self, ticker: str, start_date: str, end_date: str):
        self.ticker = ticker.upper().strip()
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
        self.model = None
        self.scaler = StandardScaler()
        self.features = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "Returns",
            "MA_50",
            "MA_200",
            "RSI",
            "VIX",  # Market Regime: Fear Index
            "Yield_10Y",  # Market Regime: Treasury Yield
        ]

    def fetch_market_regime(self) -> pd.DataFrame:
        """
        Fetches macro indicators (VIX, 10Y Yield) from Yahoo Finance.
        """
        try:
            logger.info("Fetching Market Regime data (^VIX, ^TNX)...")
            regime_df = yf.download(
                ["^VIX", "^TNX"],
                start=self.start_date,
                end=self.end_date,
                progress=False,
            )

            # yfinance often returns MultiIndex for multiple tickers
            # We want the 'Close' prices
            if isinstance(regime_df.columns, pd.MultiIndex):
                regime_df = regime_df["Close"]

            # Rename columns if they exist
            # Note: yf might return columns as '^VIX', '^TNX'
            mapping = {"^VIX": "VIX", "^TNX": "Yield_10Y"}
            regime_df = regime_df.rename(columns=mapping)

            return regime_df

        except Exception as e:
            logger.warning(f"Could not fetch Market Regime data: {e}")
            return pd.DataFrame()

    def fetch_data(self) -> pd.DataFrame:
        """
        Fetches historical data from Yahoo Finance (yfinance).
        Now includes Market Regime (VIX + Yields) integration.
        """
        logger.info(f"Fetching data for {self.ticker}...")
        try:
            # 1. Fetch Main Stock Data
            df = yf.download(
                self.ticker, start=self.start_date, end=self.end_date, progress=False
            )

            if df.empty:
                logger.error(
                    f"No data found for {self.ticker}. Check symbol or date range."
                )
                self.data = pd.DataFrame()
                return self.data

            # Handle MultiIndex columns (common in newer yfinance versions)
            if isinstance(df.columns, pd.MultiIndex):
                # Check if it has 'Ticker' level, sometimes yfinance returns Close -> Ticker columns
                # If column levels > 1, try to simplify
                if df.columns.nlevels > 1:
                    # This is tricky with yf.download(list) vs single.
                    # For single ticker, it usually returns simple columns or Price -> Ticker.
                    # Let's drop level 1 if it exists.
                    df.columns = df.columns.droplevel(1)

            # Ensure we have standard OHLCV columns
            required_cols = ["Open", "High", "Low", "Close", "Volume"]
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Missing columns in fetched data: {df.columns}")
                self.data = pd.DataFrame()
                return self.data

            # 2. Fetch & Merge Market Regime Data
            regime_df = self.fetch_market_regime()

            if not regime_df.empty:
                # Join on Index (Date)
                # Forward fill missing weekend/holiday data in regime if necessary
                df = df.join(regime_df).ffill()

                # Verify columns exist after join, if not fill them
                if "VIX" not in df.columns:
                    df["VIX"] = 20.0
                if "Yield_10Y" not in df.columns:
                    df["Yield_10Y"] = 4.0
            else:
                # Fallback if regime fetch fails: Fill with 0 or neutral values
                df["VIX"] = 20.0  # Neutral VIX
                df["Yield_10Y"] = 4.0  # Neutral Yield

            self.data = df
            return self.data

            # 2. Fetch & Merge Market Regime Data
            regime_df = self.fetch_market_regime()

            if not regime_df.empty:
                # Join on Index (Date)
                # Forward fill missing weekend/holiday data in regime if necessary
                df = df.join(regime_df).ffill()
            else:
                # Fallback if regime fetch fails: Fill with 0 or neutral values
                df["VIX"] = 20.0  # Neutral VIX
                df["Yield_10Y"] = 4.0  # Neutral Yield

            self.data = df
            return self.data

        except Exception as e:
            logger.error(f"Error fetching data for {self.ticker}: {str(e)}")
            self.data = pd.DataFrame()
            return self.data

    def preprocess_data(self) -> pd.DataFrame:
        """
        Calculates technical indicators and prepares features for training.
        """
        if self.data is None or self.data.empty:
            return pd.DataFrame()

        df = self.data.copy()

        # Calculate Returns
        df["Returns"] = df["Close"].pct_change()

        # Moving Averages
        df["MA_50"] = df["Close"].rolling(window=50).mean()
        df["MA_200"] = df["Close"].rolling(window=200).mean()

        # RSI (Relative Strength Index)
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # Target Variable: 1 if Price goes UP tomorrow, 0 if DOWN
        df["Target"] = np.where(df["Close"].shift(-1) > df["Close"], 1, 0)

        # Drop NaNs created by indicators
        df.dropna(inplace=True)

        self.data = df
        return self.data

    def train_model(self, algorithm: str = "Random Forest") -> Dict[str, Any]:
        """
        Trains the selected model algorithm.
        Returns a dictionary with performance metrics.
        """
        if self.data is None or self.data.empty:
            return {"status": "error", "message": "No data to train on."}

        X = self.data[self.features]
        y = self.data["Target"]

        # Split Data (80% Train, 20% Test)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )

        # Scale Features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Initialize Model
        if algorithm == "Random Forest":
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        elif algorithm == "Gradient Boosting (GBDT)":
            self.model = GradientBoostingClassifier(
                n_estimators=100, learning_rate=0.1, random_state=42
            )
        else:
            return {
                "status": "error",
                "message": f"Algorithm {algorithm} not implemented yet.",
            }

        # Train
        self.model.fit(X_train_scaled, y_train)

        # Evaluate
        predictions = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, predictions)
        # Use simple precision calculation if sklearn version conflict
        try:
            precision = precision_score(y_test, predictions, zero_division=0)
        except TypeError:
            precision = precision_score(y_test, predictions)

        return {
            "status": "success",
            "algorithm": algorithm,
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "test_size": len(y_test),
        }

    def predict_next_day(self) -> Tuple[str, float]:
        """
        Predicts the movement for the next trading day.
        Returns: ("BUY"|"SELL", probability)
        """
        if self.model is None:
            return "ERROR", 0.0

        # use the last row of data
        last_row = self.data.iloc[[-1]][self.features]
        last_row_scaled = self.scaler.transform(last_row)

        prediction = self.model.predict(last_row_scaled)[0]
        probability = self.model.predict_proba(last_row_scaled)[0][
            1
        ]  # Probability of Class 1 (UP)

        signal = "BUY" if prediction == 1 else "SELL"
        return signal, probability

    def save_model(self, filepath: str):
        """Saves the trained model and scaler."""
        if self.model:
            joblib.dump({"model": self.model, "scaler": self.scaler}, filepath)

    def load_model(self, filepath: str):
        """Loads a trained model and scaler."""
        if os.path.exists(filepath):
            data = joblib.load(filepath)
            self.model = data["model"]
            self.scaler = data["scaler"]
