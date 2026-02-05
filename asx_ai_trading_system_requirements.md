
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
    - **Market Calendar Compliance**: Automatically excludes ASX holidays and weekends from backtest timeline (dynamically fetched for date range).
    - **Transaction Ledger**: Records every simulated trade in machine-parseable format for audit trail and post-analysis.
    - **Portfolio Validation**: Pre-checks available cash before generating signals (skips ML execution if insufficient capital).
    - **Mode 1 (Models Comparison)**: Benchmarks individual AI performance for a fixed strategy.
    - **Mode 2 (Time-Span Comparison)**: Evaluates holding period efficiency using a **Multi-Model Consensus** (majority vote).
        - **Consensus Logic**: Odd number of models uses a natural majority; even number of models uses a user-selected **Tie-Breaker** (Chairman model).
        - **Holding Period Units**: "Day" = trading days; "Week/Month/Quarter/Year" = calendar days.
    - **Mode 3 (Find Super Stars)**: Scans entire market indexes to identify the **Top 10** performers for a chosen timeframe (1 day to 1 year).
        - **Company Profiles**: Displays full legal company names and provides direct links to **Yahoo Finance** for each winner.
        - **Error Transparency**: Includes a reviewable section for stocks that failed processing (e.g., insufficient data for new listings).

#### 2.4 UI Modules (`ui/`)
- **`sidebar.py`** — Analysis mode selection via a **Segmented Button Switch** (Models vs. Time-Span vs. Super Stars). Includes:
    - **Dynamic Algorithm Filtering**: Automatically hides algorithms if their dependencies are not functional in the current environment.
    - **Percentage-Based Controls**: Stop-Loss and Take-Profit thresholds are adjusted via intuitive **% sliders** (e.g., 15.0% instead of 0.15).
- **`algo_view.py`** — Renders the **Models Comparison** leaderboard and individual model deep-dives. Features **ETF labeling** in headers.
- **`strategy_view.py`** — Renders the **Time-Span Comparison** ROI bar charts and consensus equity paths.
- **`stars_view.py`** — Renders the **Super Stars** leaderboard (Hall of Fame) with comparative ROI charts (accurate % labeling) and drill-down trade analysis.
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
## 4. Trading Constraints & Realism

### 4.1 ASX Market Calendar Integration
- **Dynamic Holiday Detection**: System automatically fetches ASX public holidays based on the backtest date range (no hard-coded year limits).
  - **Data Source**: `pandas_market_calendars` library with fallback to static JSON cache.
  - **Scope**: Holidays fetched dynamically for the exact period defined by user's `start_date` and `end_date` parameters.
  - **Filtering**: Backtest engine excludes holidays BEFORE running simulations (pre-filtered date index).
  - **Weekend Handling**: Saturdays and Sundays automatically excluded via `pd.DatetimeIndex.dayofweek < 5`.
  
- **Trading Day Definition**:
  - Valid trading days = Monday-Friday excluding ASX public holidays.
  - Market half-days (e.g., Christmas Eve) marked as off-days (no trading allowed).
  - If holiday falls on weekend, no special handling needed (already excluded).
  
### 4.2 Holding Period Units
- **"Day" Unit**: Strictly interpreted as **TRADING DAYS** (excludes weekends + holidays).
  - Example: 30-day hold starting 2026-02-03(MON) → sell on trading day #30 (not calendar day #30).
  - Implementation: Use cumulative count of valid trading days, not `timedelta`.

- **Other Units ("Week", "Month", "Quarterly", "Year")**: Interpreted as **CALENDAR DAYS**.
  - Example: 1-month hold = 30 calendar days (includes weekends/holidays).
  - Example: 1-year hold = 365 calendar days.
  - Rationale: Longer timeframes naturally span multiple weekends/holidays; calendar-based is more intuitive.

### 4.3 Portfolio Validation Before Signal Generation
- **Pre-Transaction Check**: Before running ML models, system validates:
  1. **Available Cash**: Current portfolio cash balance >= minimum stock price in watchlist.
  2. **Affordable Tickers**: For each ticker, calculate `max_units = floor(cash / current_price)`.
  3. **Skip Logic**: If no tickers affordable (insufficient cash for any position), skip signal generation entirely.
  
- **Purpose**: Prevent wasted computation on signals that cannot be executed due to capital constraints.
- **Logging**: Display validation results in dashboard: "2026-02-06: Can afford ABB.AX (max 150 units), SIG.AX (max 35 units)".

### 4.4 Transaction Ledger (Audit Trail)
- **Machine-Parseable Format**: Transaction log stored in structured format (CSV or JSON) optimized for automated analysis.
  - **Not Required**: Human-readable formatting (AI agents or scripts can parse raw data).
  - **Schema**: Each transaction includes: `date`, `ticker`, `action`, `quantity`, `price`, `commission`, `cash_before`, `cash_after`, `positions_snapshot`.
  
- **Ledger Lifecycle & Access**:
  - Created fresh at start of each backtest run.
  - **Automatically cleared** when user re-runs with different parameters (no archiving).
  - **NOT accessible via Dashboard UI** — works as system log collection only.
  - Automatically saved to `data/ledgers/backtest_{timestamp}.csv` on completion.
  - Users access ledger files directly from `data/ledgers/` folder (see README.md for details).
  
- **Memory-Optimized Approach**:
  - During backtest: Keep only minimal state in RAM (~2 KB per active backtest).
    - Portfolio state (cash, positions): ~1 KB
    - Summary metrics (returns, Sharpe): ~500 bytes
    - Current transaction buffer: ~300 bytes
  - **Not storing full ledger in memory** during execution.
  - Batch write to disk after each backtest completes, then clear from memory.
  
- **Mode-Specific Ledger Generation**:
  - **Mode 1 (Models Comparison)**: Each model → separate ledger for performance evaluation.
    - Worst-case: ASX 200 × 5 models = 1,000 backtests = ~600-800 MB total disk output.
  - **Mode 2 (Time-Span)**: Models vote as consensus team → single ledger per holding period.
  - **Mode 3 (Super Stars)**: Models vote as consensus team → single ledger per stock.
  
- **Purpose**: Enable post-analysis debugging, transaction sequence verification, and AI-assisted audit reviews.

### 4.5 Date Display Format
- **Standard Format**: `YYYY-MM-DD(DAY)` where DAY is 3-letter weekday (MON, TUE, WED, THU, FRI, SAT, SUN).
  - Example: `2026-02-06(THU)`, `2026-12-25(FRI)`.
  
- **Application Scope**:
  - Dashboard result tables (transaction history, signal dates).
  - CSV/Excel exports.
  - Chart axis labels (Plotly/Matplotlib X-axis).
  - Transaction ledger date column.
  
- **Purpose**: Quick visual verification that trades occurred on valid trading days (not weekends/holidays).

---
## 5. Reinvestment & Settlement
- **Settlement Logic**: Backtesting assumes a **T+1 reinvestment** cycle (capital available the next business day after a sale), providing a realistic simulation of brokerage cash flow.
- **Signal-Driven Entry**: Reinvestment only occurs when the **AI Consensus** (or single model) triggers a "BUY" signal that exceeds the **Hurdle Rate**.
- **Exit Strategy**: Supports Stop-Loss, Take-Profit, and Model-Exit (consensus reversal).

---
## 6. Summary
This system provides a rigorous, realistic backtesting environment for ASX trading, accounting for both technical AI signals and real-world financial constraints (fees, taxes, market calendar constraints, and holding preferences).

---
*Last Updated: February 6, 2026*
