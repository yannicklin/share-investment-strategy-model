"""Backtesting engine for evaluating AI trading strategies."""

from typing import List, Dict, Any
from config import Config
from buildmodel import ModelBuilder


class BacktestEngine:
    """Simulates trading strategy on historical data."""

    def __init__(self, config: Config, model_builder: ModelBuilder):
        """Initializes BacktestEngine.

        Args:
            config: Configuration object.
            model_builder: Prepared ModelBuilder instance.
        """
        self.config = config
        self.model_builder = model_builder
        self.history: List[Dict[str, Any]] = []

    def run(self, ticker: str) -> Dict[str, Any]:
        """Runs the backtest for a specific ticker.

        Args:
            ticker: ASX ticker.

        Returns:
            Dict[str, Any]: Backtest results summary.
        """
        data = self.model_builder.fetch_data(ticker, self.config.backtest_years)
        if data.empty:
            return {"error": f"No data for {ticker}"}

        # Prepare features for the entire dataset using the centralized method
        # Note: prepare_features also drops NaN and adds a 'Target' column
        # which is fine for backtesting historical data.
        # We also need to know which features were used.
        df = data.copy()
        # We call prepare_features but we need the DataFrame back to iterate with index
        # Let's modify ModelBuilder to allow returning the DataFrame or just reuse logic
        # Actually, let's keep it simple for now and just make sure the feature list matches

        # Centralized feature generation logic (internal helper to avoid redundancy)
        X, y = self.model_builder.prepare_features(data)

        # We need to map X back to a structure we can iterate over easily
        # or just re-calculate indicators on 'data' to keep it as a DataFrame
        # Redoing indicator logic here to keep DataFrame structure for backtest
        df = data.copy()
        exp1 = df["Adj Close"].ewm(span=12, adjust=False).mean()
        exp2 = df["Adj Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = exp1 - exp2
        df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()

        delta = df["Adj Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        df["MA5"] = df["Adj Close"].rolling(window=5).mean()
        df["MA20"] = df["Adj Close"].rolling(window=20).mean()
        df["Daily_Return"] = df["Adj Close"].pct_change()
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

        capital = self.config.init_capital
        position = 0.0
        buy_price = 0.0
        buy_date = None
        trades = []

        # Iterate through the data day by day
        for i in range(len(df) - 1):
            current_row = df.iloc[i]
            date = df.index[i]

            # Feature vector for current day
            X_current = current_row[features].values
            predicted_next_price = self.model_builder.predict(X_current)
            current_price = float(current_row["Adj Close"])

            # Logic: If predicted price is higher than current, and we don't have a position
            if position == 0:
                if predicted_next_price > current_price:
                    # Buy
                    position = capital / current_price
                    buy_price = current_price
                    buy_date = date
                    capital = 0

            # Logic: If we have a position, check for sell conditions
            elif position > 0:
                days_held = (date - buy_date).days

                # Check stop-loss (using next day's open if it gaps down)
                # In backtest, we can check the High/Low of the current day too
                low_price = float(current_row["Low"])
                high_price = float(current_row["High"])

                stop_loss_price = buy_price * (1 - self.config.stop_loss_threshold)
                take_profit_price = buy_price * (1 + self.config.stop_profit_threshold)

                sell_reason = None
                sell_price = 0.0

                if low_price <= stop_loss_price:
                    sell_reason = "stop-loss"
                    # Handle price gaps: sell at stop-loss price unless Open is lower
                    sell_price = min(stop_loss_price, float(current_row["Open"]))
                elif high_price >= take_profit_price:
                    sell_reason = "take-profit"
                    sell_price = max(take_profit_price, float(current_row["Open"]))
                elif days_held >= self.config.max_hold_days:
                    sell_reason = "max-hold"
                    sell_price = float(current_row["Adj Close"])
                elif predicted_next_price < current_price:
                    sell_reason = "model-exit"
                    sell_price = float(current_row["Adj Close"])

                if sell_reason:
                    capital = position * sell_price
                    profit_loss = capital - (position * buy_price)
                    profit_pct = (sell_price - buy_price) / buy_price

                    trades.append(
                        {
                            "buy_date": buy_date,
                            "buy_price": buy_price,
                            "sell_date": date,
                            "sell_price": sell_price,
                            "profit_loss": profit_loss,
                            "profit_pct": profit_pct,
                            "duration": days_held,
                            "reason": sell_reason,
                        }
                    )
                    position = 0
                    buy_price = 0
                    buy_date = None

        # Final cleanup
        if position > 0:
            last_row = df.iloc[-1]
            sell_price = float(last_row["Adj Close"])
            capital = position * sell_price
            # Don't count as a completed trade for stats if it's still open,
            # or just close it at the end.

        total_profit = capital - self.config.init_capital
        roi = total_profit / self.config.init_capital
        win_rate = (
            len([t for t in trades if t["profit_loss"] > 0]) / len(trades)
            if trades
            else 0
        )

        results = {
            "ticker": ticker,
            "total_trades": len(trades),
            "win_rate": win_rate,
            "roi": roi,
            "final_capital": capital,
            "trades": trades,
        }
        self.history.append(results)
        return results
