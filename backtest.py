"""Backtesting engine for evaluating AI trading strategies."""

import pandas as pd
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

        # Handle yfinance MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        exp1 = df["Close"].ewm(span=12, adjust=False).mean()
        exp2 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = exp1 - exp2
        df["Signal_Line"] = df["MACD"].ewm(span=9, adjust=False).mean()

        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        df["MA5"] = df["Close"].rolling(window=5).mean()
        df["MA20"] = df["Close"].rolling(window=20).mean()
        df["Daily_Return"] = df["Close"].pct_change()
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

        capital = self.config.init_capital
        position = 0.0
        buy_price = 0.0
        buy_date = None
        buy_fees = 0.0
        trades = []
        equity_history = []

        # Iterate through the data day by day
        for i in range(len(df) - 1):
            current_row = df.iloc[i]
            date = df.index[i]
            current_price = float(current_row["Close"])

            # Record current equity before any potential trades today
            if position > 0:
                current_equity = position * current_price
            else:
                current_equity = capital
            equity_history.append({"date": date, "capital": current_equity})

            # Feature vector for current day
            X_current = current_row[features].values
            predicted_next_price = self.model_builder.predict(X_current, date=date)
            current_price = float(current_row["Close"])

            # Logic: If predicted price is higher than current, and we don't have a position
            if position == 0:
                if predicted_next_price > current_price:
                    # Buy
                    # Calculate Fees
                    buy_value = capital
                    fees = (
                        (buy_value * self.config.brokerage_rate)
                        + (buy_value * self.config.clearing_rate)
                        + self.config.settlement_fee
                    )

                    net_capital = capital - fees
                    position = net_capital / current_price
                    buy_price = current_price
                    buy_date = date
                    buy_fees = fees
                    capital = 0

            # Logic: If we have a position, check for sell conditions
            elif position > 0:
                # Calculate minimum hold date based on unit and value
                unit_map = {
                    "day": "days",
                    "month": "months",
                    "quarter": "weeks",
                    "year": "years",
                }

                offset_args = {}
                if self.config.hold_period_unit == "quarter":
                    offset_args["weeks"] = 13 * self.config.hold_period_value
                else:
                    offset_args[unit_map[self.config.hold_period_unit]] = (
                        self.config.hold_period_value
                    )

                assert buy_date is not None
                min_hold_date = buy_date + pd.DateOffset(**offset_args)
                is_min_period_passed = date >= min_hold_date

                # Check stop-loss (Always active for safety)
                low_price = float(current_row["Low"])
                high_price = float(current_row["High"])

                stop_loss_price = buy_price * (1 - self.config.stop_loss_threshold)
                take_profit_price = buy_price * (1 + self.config.stop_profit_threshold)

                sell_reason = None
                sell_price = 0.0

                # 1. Stop-Loss (Safety - Always checked)
                if low_price <= stop_loss_price:
                    sell_reason = "stop-loss"
                    sell_price = min(stop_loss_price, float(current_row["Open"]))

                # 2. These conditions only apply AFTER the minimum holding period
                elif is_min_period_passed:
                    if high_price >= take_profit_price:
                        sell_reason = "take-profit"
                        sell_price = max(take_profit_price, float(current_row["Open"]))
                    elif predicted_next_price < current_price:
                        sell_reason = "model-exit"
                        sell_price = float(current_row["Close"])

                if sell_reason:
                    days_held = (date - buy_date).days
                    sell_value = position * sell_price

                    # Sell Fees
                    sell_fees = (
                        (sell_value * self.config.brokerage_rate)
                        + (sell_value * self.config.clearing_rate)
                        + self.config.settlement_fee
                    )

                    total_fees = buy_fees + sell_fees
                    gross_profit = sell_value - (position * buy_price) - total_fees

                    # Tax Calculation
                    tax = 0.0
                    if gross_profit > 0:
                        # ATO 12-month rule: 50% discount if held >= 365 days
                        tax_discount = 0.5 if days_held >= 365 else 1.0
                        taxable_amount = gross_profit * tax_discount
                        tax = taxable_amount * self.config.tax_rate

                    capital = sell_value - sell_fees - tax
                    profit_loss = capital - (position * buy_price + buy_fees)
                    profit_pct = profit_loss / (position * buy_price + buy_fees)

                    trades.append(
                        {
                            "buy_date": buy_date,
                            "buy_price": buy_price,
                            "sell_date": date,
                            "sell_price": sell_price,
                            "fees": total_fees,
                            "tax": tax,
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
            sell_price = float(last_row["Close"])
            sell_value = position * sell_price
            sell_fees = (
                (sell_value * self.config.brokerage_rate)
                + (sell_value * self.config.clearing_rate)
                + self.config.settlement_fee
            )
            capital = sell_value - sell_fees
            # Don't count as a completed trade for stats if it's still open,
            # or just close it at the end.

        total_profit = capital - self.config.init_capital
        roi = total_profit / self.config.init_capital

        # Gross ROI calculation (before fees and tax)
        gross_profit_sum = sum(
            [t["profit_loss"] + t["fees"] + t["tax"] for t in trades]
        )
        gross_roi = gross_profit_sum / self.config.init_capital

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
            "gross_roi": gross_roi,
            "final_capital": capital,
            "trades": trades,
            "equity_history": equity_history,
        }
        self.history.append(results)
        return results
