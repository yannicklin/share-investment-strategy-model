# AI-Based Stock Investment System Requirements (USA Version)

## 1. Program Objective
Develop a Python-based stock trading strategy system for the **USA Stock Market (NYSE, NASDAQ)**. The system uses AI models trained on **historical US market data** (e.g., OHLCV/K-line, MACD, indicators) to:

- Train an AI investment model on US stock data
- Backtest historical performance in USD
- Generate buy/sell recommendations for future trading
- Predict optimal entry and exit points
- Maximise investment returns while enforcing strict stop-loss rules
- Handle real-world scenarios such as price gaps (e.g., selling at actual market price when stop-loss cannot be executed)

The model may buy even if projected returns do not meet take-profit thresholds, as long as it identifies favourable conditions. Stop-loss rules must always be followed.

---

## 2. Program Modules

#### 2.1 Core Modules (`core/`)
- **`config.py`** — Centralized configuration management (tickers, capital in USD, IRS tax brackets).
- **`model_builder.py`** — AI factory supporting 5 algorithms (Random Forest, XGBoost, CatBoost, Prophet, LSTM) with automated scaling and sequential processing for LSTM.
- **`backtest_engine.py`** — Dual-mode simulation engine:
    - **Mode 1 (Models Comparison)**: Benchmarks individual AI performance for a fixed strategy.
    - **Mode 2 (Time-Span Comparison)**: Evaluates holding period efficiency using a **Multi-Model Consensus** (majority vote).
        - **Tie-Breaker Rule**: In the event of a 50/50 vote split, a user-selected Tie-Breaker model makes the final decision.
    - **Mode 3 (Find Super Stars)**: Scans US market indexes to identify the **Top 10** high-profit stocks.
        - **Index Support**: S&P 500, Nasdaq 100, Dow Jones 30, and Russell 2000.
        - **Trustable Data Sources**: Fetch constituents from authoritative sources (e.g., Wikipedia's real-time maintained tables or official ETF holding CSVs).
        - **Consensus Analysis**: Ranks stocks using the multi-model consensus strategy.

#### 2.2 UI Modules (`ui/`)
- **`sidebar.py`** — Analysis mode selection via a **Segmented Button Switch** (Models vs. Time-Span vs. Super Stars).
- **`algo_view.py`** — Renders the **Models Comparison** leaderboard.
- **`strategy_view.py`** — Renders the **Time-Span Comparison** dashboard.
- **`stars_view.py`** — Renders the **Super Stars** leaderboard (Hall of Fame).
- **`components.py`** — Shared dashboard elements including the **Realized Equity Curve**, transaction logs with 2-decimal precision, and US financial glossary.

---

## 3. Financial Accounting & Reinvestment

### 3.1 Fee Structures
The system supports US-specific broker profiles:
- **Commission-Free (e.g., Robinhood/Schwab)**:
    - Brokerage: $0.00
    - Regulatory Fees (Sell-side only): 
        - SEC Fee: $0.0000278 x Sell Value
        - FINRA TAF: $0.000166 x Quantity (Max $8.30 per trade)
- **Pro-Tier (e.g., Interactive Brokers)**:
    - Brokerage: $0.005 per share (Min $1.00, Max 1% of Trade Value)

### 3.2 Taxation (IRS Rules)
Federal Capital Gains Tax calculation based on holding period:
- **Short-Term (Held < 365 days)**: Taxed as ordinary income (Marginal Rate based on user's annual income).
- **Long-Term (Held ≥ 365 days)**: Tiered rates based on income (typically 0%, 15%, or 20%).

### 3.3 Reinvestment & Settlement
- **Settlement Logic**: Backtesting assumes a **T+1 reinvestment** cycle (capital available the next business day after a sale), providing a realistic simulation of US brokerage cash flow.
- **Signal-Driven Entry**: Reinvestment only occurs when the **AI Consensus** triggers a "BUY" signal.

---

## 4. Historical Data Source (USA)
Exclusively uses **Yahoo Finance (`yfinance`)**. 
- **Ticker format**: Standard US symbols (e.g., `AAPL`, `TSLA`, `NVDA`). No suffix required.
- **Adjustment**: Always use `auto_adjust=True` and target the `Close` price for calculations.
- **Market Hours**: Operates on US Eastern Time (ET).

---

## 5. Summary
This system provides a rigorous, realistic backtesting environment for US trading, mirroring the ASX version's AI intelligence while strictly adhering to US regulatory fees and federal tax laws.
