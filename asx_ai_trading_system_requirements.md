
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
- **stop_profit_threshold** — E.g., `0.10` → 10% take-profit
- **model_path** — Local storage path for models
- **init_capital** — Initial backtest capital
- **max_hold_days** — Maximum holding period per trade
- **data_source** — **Fixed to `Yahoo Finance (yfinance)`** for ASX historical data

---
### 2.2 Model Building Module — `buildmodel.py`
**Input:** Configuration file, local model files

**Process:**
- If `rebuild_model = True`:
  - Fetch ASX historical data **from Yahoo Finance via `yfinance`** using `.AX` ticker suffix
  - **Feature Engineering**: Generate technical indicators including:
    - Moving Averages (MA5, MA20)
    - Relative Strength Index (RSI)
    - MACD (Moving Average Convergence Divergence) and Signal Line
    - Daily Returns
  - Train the model
  - Save to local model directory

- If `rebuild_model = False`:
  - Load existing model if available
  - Otherwise, fetch data from **Yahoo Finance (`yfinance`)**, train, and save the model

**Output:** A trained AI model that generates profitable trading recommendations.

---
### 2.3 Backtesting Module — `backtest.py`
**Input:** Configuration file, ASX OHLCV data

**Process:**
1. Determine backtest start date based on `backtest_year`
2. Fetch historical OHLCV **from Yahoo Finance (`yfinance`)**
3. Feed historical data into the model
4. Execute model-generated buy/sell actions
5. Log each transaction:
   - Buy date & price
   - Sell date & price
   - Profit/loss amount
   - Profit percentage
   - Holding duration
   - Exit reason (take-profit / stop-loss / max-hold)

**Output:**
- Full trade history
- Performance statistics:
  - Total number of trades
  - Win rate (percentage of profitable trades)
  - ROI based on `init_capital`
  - Average holding time

---
### 2.4 UI Module — `ui.py`
A Streamlit-based dashboard supporting:

- Editing configuration values
- Triggering backtests
- Displaying:
  - Transaction logs
  - Profitability statistics
  - Model-generated future trading recommendations (e.g., “Buy BHP at 38.00 AUD, expected +12% return”).

---
### 2.5 Main Module — `shareinvestment_AImodel.py`
Coordinates the entire pipeline:

- Load configuration
- Build or load the model
- Run the backtest
- Display results via UI

This module should remain lightweight, delegating logic to submodules.

---
## 3. Historical Data Source (ASX)
**The system will exclusively use _Yahoo Finance_ via the `yfinance` Python library** for ASX historical stock data.

- **Ticker format**: append `.AX` to the symbol (e.g., `BHP.AX`, `CBA.AX`).
- **Python snippet**:

```python
import yfinance as yf

def get_asx_data(ticker: str, start: str, end: str):
    # Return OHLCV DataFrame for an ASX ticker (e.g., 'BHP.AX').
    return yf.download(ticker, start=start, end=end)  # Open, High, Low, Close, Adj Close, Volume
```

---
## 4. Summary
This document defines the ASX-focused AI trading system. **All historical stock information is retrieved from Yahoo Finance (`yfinance`)**. The system must:

- Train an AI model on ASX historical data
- Backtest trades with strict rules
- Provide actionable trading recommendations
- Offer a simple UI for configuration and result browsing
