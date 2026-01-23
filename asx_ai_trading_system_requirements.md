
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

### 2.1 Configuration Module — `config.py`
Configuration items include (but are not limited to):

- **rebuild_model** — Whether to retrain the AI model
- **target_stock_code** — One or more ASX tickers (e.g., `BHP.AX;CBA.AX`)
- **backtest_year** — Number of years of historical data to backtest
- **stop_loss_threshold** — E.g., `0.10` → 10% stop-loss
- **stop_profit_threshold** — E.g., `0.20` → 20% take-profit
- **init_capital** — Initial backtest capital
- **hold_period_unit** — Unit for **minimum** holding period (`day`, `month`, `quarter`, `year`)
- **hold_period_value** — Value for the chosen unit (e.g., `1` month)
- **brokerage_rate** — 0.12% per transaction
- **clearing_rate** — 0.00225% per transaction
- **settlement_fee** — $1.50 fixed fee per transaction
- **tax_rate** — 25% capital gains tax rate
- **model_types** — Multiple algorithm support (`random_forest`, `xgboost`, `lightgbm`, `catboost`, `elastic_net`, `svr`, `prophet`)

---
### 2.2 Model Building Module — `buildmodel.py`
**Process:**
- **Data Fetching**: Retrieve ASX historical data via `yfinance` with `auto_adjust=True`.
- **Feature Engineering**: Generate technical indicators:
    - Moving Averages (MA5, MA20)
    - RSI (Relative Strength Index)
    - MACD & Signal Line
    - Daily Returns
- **Data Preprocessing**: Mandatory **Feature Scaling** using `StandardScaler` to ensure model stability (especially for SVR and ElasticNet).
- **Model Training**: Support for 7 algorithms (Bagging, Boosting, Linear, Time-Series) via factory pattern.
- **Persistence**: Save/Load models and scalers with naming convention `{ticker}_{algorithm}_model.joblib`.

---
### 2.3 Backtesting Module — `backtest.py`
**Process:**
1. Determine backtest start date based on `backtest_year`.
2. Fetch historical OHLCV data focusing on the `Close` column.
3. **Execution Logic**:
    - **Entry**: Buy when AI model predicts positive next-day return.
    - **Minimum Hold**: Ignore model-exit and take-profit signals until the `min_hold` period expires.
    - **Exit**: Triggered by Stop-Loss (always active), Take-Profit, Model Prediction, or Period End.
4. **Financial Accounting**:
    - **Fees**: Deduct Brokerage, Clearing, and Settlement fees from every buy/sell.
    - **Taxes**: Apply **ATO 12-Month Rule** (50% CGT discount if held ≥ 365 days).
5. **Log Transactions**: Record date, price, fees, tax, and **net** profit.

---
### 2.4 UI Module — `ui.py`
Streamlit dashboard providing:
- **Comparison Sidebar**: Multiselect for algorithms and cost sliders.
- **Summary Dashboard**: Table and bar charts comparing ROI and Win Rate across models, plus a **Multi-line Equity Curve** showing capital growth over time with trade markers.
- **Detailed Drill-down**: Tabs for each algorithm showing transaction logs and profit trends.
- **Live Recommendation Engine**: 
  - Real-time (delayed) signal generation for "Today".
  - Calculation of expected returns based on the latest closing price.
  - Consensus scoring across multiple algorithms.
- **Glossary**: Built-in help for metrics (ROI, Win Rate, Net Profit) and exit reasons.

---
### 2.5 Main Module — `shareinvestment_AImodel.py`
Coordinates the pipeline: Load Config -> Build/Load Models -> Run Comparative Backtest -> Display CLI results.

---
## 3. Historical Data Source (ASX)
Exclusively uses **Yahoo Finance (`yfinance`)**. 
- **Ticker format**: `{SYMBOL}.AX`.
- **Adjustment**: Always use `auto_adjust=True` and target the `Close` price for calculations.

---
## 4. Summary
This system provides a rigorous, realistic backtesting environment for ASX trading, accounting for both technical AI signals and real-world financial constraints (fees, taxes, and holding preferences).
