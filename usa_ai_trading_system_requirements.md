# AI-Based Stock Investment System Requirements (USA Version)

## 1. Program Objective
Develop a Python-based stock trading strategy system for the **United States Stock Markets (NYSE/NASDAQ)**. The system uses AI models trained on **historical stock data** (e.g., OHLCV/K-line, MACD, indicators) to:

- Train an AI investment model on US market data
- Backtest historical performance in USD
- Generate buy/sell recommendations for future trading
- Predict optimal entry and exit points
- Maximise investment returns
- Enforce strict stop-loss rules
- Handle real-world scenarios such as price gaps (e.g., selling at actual market price when stop-loss cannot be executed)

The model may buy even if projected returns do not meet take-profit thresholds, as long as it identifies favourable conditions. Stop-loss rules must always be followed.

---
## 2. Program Modules

### 2.1 Core Modules (`core/`)
- **`config.py`** — Centralized configuration management (tickers, capital, Broker/Tax profiles). Defaults to **Random Forest**, **NGBoost**, and **CatBoost** for benchmarking.
- **`model_builder.py`** — AI factory supporting 5 algorithms (Random Forest, NGBoost, CatBoost, Prophet, LSTM) with automated scaling and sequential processing for LSTM.
    - **Hardware Portability**: Uses **NGBoost** (Natural Gradient Boosting) and **CatBoost** to ensure native ARM64 support on Mac without external C-library (libomp) issues found in XGBoost/LightGBM.
    - **ETF Identification**: Automatic security type detection to label ETFs in the results display.
- **`backtest_engine.py`** — Dual-mode simulation engine:
    - **Warm-up Buffer**: Implements a **90-day pre-test buffer** to prime technical indicators and LSTM sequences, ensuring all models can trade from Day 1 of the requested period.
    - **Market Calendar Compliance**: Automatically excludes USA market holidays and weekends from backtest timeline (dynamically fetched via `pandas_market_calendars`).
    - **Transaction Ledger**: Records every simulated trade in machine-parseable format for audit trail and post-analysis.
    - **Portfolio Validation**: Pre-checks available cash before generating signals (skips ML execution if insufficient capital).
    - **Mode 1 (Models Comparison)**: Benchmarks individual AI performance for a fixed strategy.
        - **File Naming Convention**: `{ticker}_algorithm_{mode_type}_{timespan}.csv` (e.g., `AAPL_algorithm_random_forest_14day.csv`).
    - **Mode 2 (Time-Span Comparison)**: Evaluates holding period efficiency using a **Multi-Model Consensus** (majority vote).
        - **Consensus Logic**: Odd number of models uses a natural majority; even number of models uses a user-selected **Tie-Breaker** (Chairman model).
        - **Holding Period Units**: "Day" = trading days; "Week/Month/Year" = calendar days.
    - **Mode 3 (Find Super Stars)**: Scans entire market indexes (S&P 500, Nasdaq 100) to identify the **Top 10** performers for a chosen timeframe.
        - **Company Profiles**: Displays full legal company names and provides direct links to **Yahoo Finance** for each winner.

#### 2.2 UI Modules (`ui/`)
- **`sidebar.py`** — Analysis mode selection via a **Segmented Button Switch**. Includes:
    - **Dynamic Algorithm Filtering**: Automatically hides algorithms if their dependencies are not functional.
    - **Percentage-Based Controls**: Stop-Loss and Take-Profit thresholds are adjusted via intuitive **% sliders**.
- **`algo_view.py`** — Renders the **Models Comparison** leaderboard and individual model deep-dives. Features **ETF labeling** in headers.
- **`strategy_view.py`** — Renders the **Time-Span Comparison** ROI bar charts and consensus equity paths.
- **`stars_view.py`** — Renders the **Super Stars** leaderboard (Hall of Fame) with comparative ROI charts and drill-down trade analysis.
- **`components.py`** — Shared dashboard elements including:
    - **Dual-Axis Equity Curve**: Visualizes **Realized Capital** (solid line) against the **Share Price Trend** (dotted line) on a secondary Y-axis.
    - **Standardized Logs**: numeral.js format: `$0,0.00` for currency, `0.00%` for percentages.
    - **Financial Glossary**.

---
## 3. Historical Data Source (USA)
Exclusively uses **Yahoo Finance (`yfinance`)**. 
- **Ticker format**: Standard US symbols (e.g., `AAPL`, `MSFT`, `SPY`).
- **Adjustment**: Always use `auto_adjust=True` and target the `Close` price for calculations.
- **Warm-up**: Fetches an additional 90 days of history prior to the start date for sequence initialization.

### 3.1 Market Context & Macro Data
- **Global Market Intelligence**:
  - **S&P 500 (`^GSPC`)**: Captures US market sentiment.
  - **Nasdaq 100 (`^NDX`)**: Captures tech sector performance.
  - **VIX (`^VIX`)**: Global volatility/fear gauge.
  - **10Y Yield (`^TNX`)**: US Treasury 10-year yield for rate environment context.
- **Macroeconomic Drivers**:
  - **Gold (`GC=F`)** and **Oil (`CL=F`)** futures for resource/inflation context.
  - **Currency**: USD based; other pairs (e.g., `JPY=X`) as secondary indicators.

### 3.2 Advanced Technical Indicators
- **Bollinger Bands (20, 2)**: Adds `Upper`, `Lower`, and `Width` (Squeeze) to detect mean reversion and volatility breakouts.
- **ATR (14)**: Average True Range added to measure pure price volatility for risk sizing.

---
## 4. Trading Constraints & Realism

### 4.1 US Market Calendar Integration
- **Dynamic Holiday Detection**: System automatically fetches NYSE/NASDAQ public holidays based on the backtest date range.
- **Trading Day Definition**: Monday-Friday excluding US market holidays. Market half-days treated as off-days.

### 4.2 Holding Period Units
- **"Day" Unit**: Strictly interpreted as **TRADING DAYS** (excludes weekends + holidays).
- **Other Units ("Week", "Month", "Year")**: Interpreted as **CALENDAR DAYS**.

### 4.3 Portfolio Validation Before Signal Generation
- **Pre-Transaction Check**: Before running ML models, system validates if current cash is sufficient to afford at least one ticker in the watchlist at current market prices.

### 4.4 Transaction Ledger (Audit Trail)
- **Machine-Parseable Format**: Transaction log stored in CSV format for automated analysis.
- **Memory-Optimized Approach**: Batch write to disk after each backtest completes to maintain low RAM footprint.

### 4.5 Date Display Format
- **Standard Format**: `YYYY-MM-DD(DAY)` where DAY is 3-letter weekday abbreviation.

### 4.6 Supported Broker Cost Profiles
- **Saxo / Global Prime**: Conservative standard rates.
- **Stake**: Low-cost flat fee for US trades.
- **IBKR Pro Fixed**: Per-share commission model.

---
## 5. Reinvestment & Settlement
- **Settlement Logic**: Backtesting assumes a **T+1 settlement cycle** for US markets (funds clear next business day), matching current SEC regulations.
- **Signal-Driven Entry**: Reinvestment only occurs when the **AI Consensus** triggers a "BUY" signal that exceeds the **Hurdle Rate**.
- **Exit Strategy**: Supports Stop-Loss, Take-Profit, and Model-Exit.

---
## 6. Summary
This system provides a rigorous, realistic backtesting environment for US stock trading, accounting for technical AI signals and real-world financial constraints (SEC/FINRA fees, W-8BEN tax, T+1 settlement).

---
*Last Updated: February 9, 2026*
