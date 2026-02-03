
# AI-Based Stock Investment System Requirements (ASX Version)

## 1. Program Objective
Develop a Python-based stock trading strategy system for the **Australian Securities Exchange (ASX)**. The system uses AI models trained on **historical stock data** (e.g., OHLCV/K-line, MACD, indicators) to:

- Train an AI investment model on ASX data
- Backtest historical performance
- Generate buy/sell recommendations for future trading
- Predict optimal entry and exit points
- Maximise investment returns
- Enforce strict stop-loss rules
- Handle real-world scenarios such as price gaps (e.g., selling at actual market price when stop-loss cannot be executed)

The model may buy even if projected returns do not meet take-profit thresholds, as long as it identifies favourable conditions. Stop-loss rules must always be followed.

---
## 2. Program Modules

### 2. Program Modules

#### 2.1 Core Modules (`core/`)
- **`config.py`** — Centralized configuration management (tickers, capital, ATO tax brackets). Defaults to **Random Forest** and **CatBoost** for benchmarking.
- **`model_builder.py`** — AI factory supporting 5 algorithms (Random Forest, Gradient Boosting, CatBoost, Prophet, LSTM) with automated scaling and sequential processing for LSTM.
    - **Hardware Portability**: Replaced XGBoost/LightGBM with Scikit-Learn **Gradient Boosting** to ensure native ARM64 support on Mac without external C-libraries (libomp).
    - **ETF Identification**: Automatic security type detection to label ETFs in the results display.
- **`backtest_engine.py`** — Dual-mode simulation engine:
    - **Warm-up Buffer**: Implements a **90-day pre-test buffer** to prime technical indicators and LSTM sequences, ensuring all models can trade from Day 1 of the requested period.
    - **Mode 1 (Models Comparison)**: Benchmarks individual AI performance for a fixed strategy.
    - **Mode 2 (Time-Span Comparison)**: Evaluates holding period efficiency using a **Multi-Model Consensus** (majority vote).
        - **Consensus Logic**: Odd number of models uses a natural majority; even number of models uses a user-selected **Tie-Breaker** (Chairman model).
    - **Mode 3 (Find Super Stars)**: Scans entire market indexes to identify the **Top 10** performers for a chosen timeframe.

#### 2.4 UI Modules (`ui/`)
- **`sidebar.py`** — Analysis mode selection via a **Segmented Button Switch** (Models vs. Time-Span vs. Super Stars). Includes:
    - **Dynamic Algorithm Filtering**: Automatically hides algorithms if their dependencies are not functional in the current environment.
- **`algo_view.py`** — Renders the **Models Comparison** leaderboard and individual model deep-dives. Features **ETF labeling** in headers.
- **`strategy_view.py`** — Renders the **Time-Span Comparison** ROI bar charts and consensus equity paths.
- **`stars_view.py`** — Renders the **Super Stars** leaderboard (Hall of Fame) with comparative ROI charts and drill-down trade analysis for the top 10 winners.
- **`components.py`** — Shared dashboard elements including:
    - **Dual-Axis Equity Curve**: Visualizes **Realized Capital** (solid line) against the **Share Price Trend** (dotted line) on a secondary Y-axis.
    - **Standardized Logs**: numeral.js format: `$0,0.00` for currency, `0.00%` for percentages.
    - **Financial Glossary**.

---
## 3. Historical Data Source (ASX)
Exclusively uses **Yahoo Finance (`yfinance`)**. 
- **Ticker format**: `{SYMBOL}.AX`.
- **Adjustment**: Always use `auto_adjust=True` and target the `Close` price for calculations.
- **Warm-up**: Fetches an additional 90 days of history prior to the start date for sequence initialization.

---
## 4. Reinvestment & Settlement
- **Settlement Logic**: Backtesting assumes a **T+1 reinvestment** cycle (capital available the next business day after a sale), providing a realistic simulation of brokerage cash flow.
- **Signal-Driven Entry**: Reinvestment only occurs when the **AI Consensus** (or single model) triggers a "BUY" signal that exceeds the **Hurdle Rate**.
- **Exit Strategy**: Supports Stop-Loss, Take-Profit, and Model-Exit (consensus reversal).

---
## 5. Summary
This system provides a rigorous, realistic backtesting environment for ASX trading, accounting for both technical AI signals and real-world financial constraints (fees, taxes, and holding preferences).

---
*Last Updated: February 3, 2026*
