
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
- **`config.py`** — Centralized configuration management (tickers, capital, ATO tax brackets).
- **`model_builder.py`** — AI factory supporting 5 algorithms (Random Forest, XGBoost, CatBoost, Prophet, LSTM) with automated scaling and sequential processing for LSTM.
- **`backtest_engine.py`** — Dual-mode simulation engine:
    - **Mode 1 (Models Comparison)**: Benchmarks individual AI performance for a fixed strategy.
    - **Mode 2 (Time-Span Comparison)**: Evaluates holding period efficiency using a **Multi-Model Consensus** (majority vote).
        - **Tie-Breaker Rule**: In the event of a 50/50 vote split, a user-selected Tie-Breaker model makes the final decision.
    - **Mode 3 (Find Super Stars)**: Scans entire market indexes to identify the **Top 10** performers for a chosen timeframe.
        - **Index Support**: Includes ASX 50, ASX 200, Small Ordinaries, and All Ordinaries.
        - **Live Updates**: Built-in constituent manager to refresh index lists from live market data.

#### 2.2 UI Modules (`ui/`)
- **`sidebar.py`** — Analysis mode selection via a **Segmented Button Switch** (Models vs. Time-Span). Includes three configuration sections:
    - **Global Settings**: Shared parameters (Tickers, Capital, Risk thresholds).
    - **Mode-Specific Settings**: Context-aware fields (Fixed strategy for Models Comparison; AI Committee & Tie-Breaker for Time-Span Comparison).
    - **Preprocessing & Accounting**: Scaler type, costs, and taxes.
- **`algo_view.py`** — Renders the **Models Comparison** leaderboard and individual model deep-dives.
- **`strategy_view.py`** — Renders the **Time-Span Comparison** ROI bar charts and consensus equity paths.
- **`components.py`** — Shared dashboard elements including the **Realized Equity Curve**, formatted transaction logs, and the financial glossary.

### 2.3 Main Module — `ASX_AImodel.py`
The unified entry point for the Streamlit dashboard. Integrates core logic with the modular UI views.


---
## 3. Historical Data Source (ASX)
Exclusively uses **Yahoo Finance (`yfinance`)**. 
- **Ticker format**: `{SYMBOL}.AX`.
- **Adjustment**: Always use `auto_adjust=True` and target the `Close` price for calculations.

---
## 4. Summary
This system provides a rigorous, realistic backtesting environment for ASX trading, accounting for both technical AI signals and real-world financial constraints (fees, taxes, and holding preferences).
