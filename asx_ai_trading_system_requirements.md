
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
- **brokerage_rate** — 0.12% per transaction (Default)
- **clearing_rate** — 0.00225% per transaction (Default)
- **settlement_fee** — $1.50 fixed fee per transaction (Default)
- **cost_profile** — Choice between `default` and `cmc_markets`
- **annual_income** — Base annual income for marginal tax bracket calculation
- **tax_rate** — (Deprecated) Replaced by ATO 2024-25 bracket logic
- **scaler_type** — Choice of stabilizer (`standard`, `robust`)
- **model_types** — Multiple algorithm support (`random_forest`, `xgboost`, `catboost`, `prophet`, `lstm`)

---
### 2.2 Model Building Module — `buildmodel.py`
**Process:**
- **Data Fetching**: Retrieve ASX historical data via `yfinance` with `auto_adjust=True`.
- **Feature Engineering**: Generate technical indicators:
    - Moving Averages (MA5, MA20)
    - RSI (Relative Strength Index)
    - MACD & Signal Line
    - Daily Returns
- **Data Preprocessing**: **Feature Scaling** using either `StandardScaler` (conservative) or `RobustScaler` (handles outliers) based on configuration.
- **Model Training**: Support for 5 algorithms (Bagging, Boosting, Time-Series) via factory pattern.
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
    - **Fees**: Deduct Brokerage, Clearing, and Settlement fees. Support for **CMC Markets** ($11 or 0.10%).
    - **Taxes**: Apply **ATO 2024-25 Individual Tax Brackets**. Includes 12-Month Rule (50% CGT discount if held ≥ 365 days). Tax is calculated as the marginal increase in liability based on the user's `annual_income`.
5. **Log Transactions**: Record date, price, fees, tax, and **net** profit.

---
### 2.4 UI Module — `ui.py`
Streamlit dashboard providing:
- **Comparison Sidebar**: Multiselect for algorithms and cost sliders.
- **Summary Dashboard**: Metrics table comparing ROI and Win Rate across models, plus a **Realized Equity Curve** connecting trade exit points to show actual capital growth over time.
- **Detailed Drill-down**: Tabs for each algorithm showing core metrics (ROI, Win Rate, Avg Profit/Trade) and transaction logs.
- **Live Recommendation Engine**: 
  - Real-time (delayed) signal generation for "Today".
  - Automated state management: Running a backtest clears previous recommendations, and vice-versa.
  - Consensus scoring across multiple algorithms.
- **Glossary**: Built-in help for metrics (ROI, Win Rate, Net Profit) and exit reasons.

---
### 2.5 Main Module — `ASX_AImodel.py`
Coordinates the pipeline: Load Config -> Build/Load Models -> Run Comparative Backtest -> Display CLI results.

---
## 3. Historical Data Source (ASX)
Exclusively uses **Yahoo Finance (`yfinance`)**. 
- **Ticker format**: `{SYMBOL}.AX`.
- **Adjustment**: Always use `auto_adjust=True` and target the `Close` price for calculations.

---
## 4. Summary
This system provides a rigorous, realistic backtesting environment for ASX trading, accounting for both technical AI signals and real-world financial constraints (fees, taxes, and holding preferences).
