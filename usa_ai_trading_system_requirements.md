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

#### 2.3 Decision Layer & Hurdle Rate
To ensure realism and profitability, the system employs a **Tax-Aware Dynamic Hurdle Rate** in the decision layer for all analysis modes:
- **Break-even Calculation**: For every potential trade, the system calculates the minimum required return (%) using `Fees_Pct + (Risk_Buffer / (1 - Marginal_Tax_Rate))`.
- **Hurdle-Filtered Signals**: The AI model (or consensus) only generates a "BUY" signal if the predicted price increase exceeds this hurdle rate.
- **Tax Sensitivity**: Higher income brackets result in a higher hurdle rate, as the system requires a larger gross gain to achieve the same net-of-tax risk buffer.
- **Small Capital Protection**: Prevents over-trading where brokerage fees or taxes would erode the majority of potential profits.

#### 2.2 UI Modules (`ui/`)
- **`sidebar.py`** — Analysis mode selection via a **Segmented Button Switch** (Models vs. Time-Span vs. Super Stars).
- **`algo_view.py`** — Renders the **Models Comparison** leaderboard.
- **`strategy_view.py`** — Renders the **Time-Span Comparison** dashboard.
- **`stars_view.py`** — Renders the **Super Stars** leaderboard (Hall of Fame).
- **`components.py`** — Shared dashboard elements including the **Realized Equity Curve**, transaction logs with 2-decimal precision, and US financial glossary.

---

## 3. Financial Accounting & Reinvestment

### 3.1 Fee Structures
The system supports broker profiles tailored for Australian investors trading the US market, ranging from "Classic" bank tiers to "Neobroker" and "Pro" levels.

- **Classic Standard (e.g., Saxo / Global Prime)**:
    - **Brokerage**: ~$5.00 USD per trade (Conservative Baseline).
    - **Purpose**: A realistic stress test. Strategies must be robust enough to survive this fee.

- **Stake (Retail Profile)**:
    - **Brokerage**: $3.00 USD per trade (for trades ≤ $30,000 USD).
    - **FX Friction**: ~70 basis points (0.70%) on AUD/USD transfers (Note: FX implied in model friction).
    - **Regulatory Fees**: Pass-through of SEC and FINRA fees.

- **Interactive Brokers (Pro Profile)**:
    - **Brokerage**: ~$1.00 USD (Min) or $0.005 per share.
    - **FX Friction**: Ultra-low (~0.20 bps + $2).
    - **Purpose**: The "Gold Standard" for algorithmic execution.

- **Big 4 Bank (Hard Mode)**:
    - **Brokerage**: ~$19.95 USD.
    - **Purpose**: Demonstrates why traditional AU banks are unsuitable for active algo trading.

### 3.2 Taxation (Foreign Investor - US Side Obligations)
The model simulates a Foreign Investor (e.g., Australian) trading in the US, focusing **exclusively on US tax obligations** collected at the source.

- **Base Currency**: **USD**.
- **W-8BEN Status**: Configurable option (Default: Filed).
    - **Filed (Treaty Benefit)**: 
        - **Dividends**: 15% Withholding Tax.
        - **Capital Gains**: $0.00 US Tax.
    - **Not Filed**: 
        - **Dividends**: 30% Withholding Tax.
        - **Capital Gains**: Potential 30% Backup Withholding (depending on broker enforcement).
- **Disclaimer**: This model **does not** calculate domestic taxes in the investor's home country (e.g., Australian ATO Capital Gains Tax). Users must calculate their local tax liability separately based on these USD returns.

### 3.3 Reinvestment & Settlement
- **Settlement Logic**: Backtesting assumes a **T+1 reinvestment** cycle (capital available the next business day after a sale), providing a realistic simulation of US brokerage cash flow.
- **Signal-Driven Entry**: Reinvestment only occurs when the **AI Consensus** triggers a "BUY" signal.

---

## 4. Custodianship & Risk (Safety Net)
Unlike the Australian **CHESS** system (HIN), where investors have direct legal ownership of shares on the registry, the US market operates on a **Custodian Model**.

- **Street Name**: Shares are held in the broker's name (or their custodian's) at the central depository (DTC). The investor is the "Beneficial Owner."
- **SIPC Protection**: To mitigate the lack of direct ownership, US brokers are members of **SIPC (Securities Investor Protection Corporation)**. This protects client assets up to **$500,000 USD** (limit $250,000 for cash) if the broker fails.
    - *Note for Model*: The strategy assumes the broker is SIPC-insured (e.g., Stake, IBKR, Schwab). The lack of HIN does not impact the algorithmic strategy but is a critical "Risk" factor for the user's capital allocation decisions.
- **Direct Registration (DRS)**: While possible (e.g., via Computershare), it is **not recommended** for active trading due to high friction and slow execution speeds.

---

## 5. Historical Data Source (USA) & Market Regime
Exclusively uses **Yahoo Finance (`yfinance`)** but with an enhanced "Regime Awareness" architecture.

- **Primary Asset Data**: Standard US symbols (e.g., `AAPL`, `TSLA`, `NVDA`).
    - **Adjustment**: `auto_adjust=True`, Target `Close`.
- **Market Regime Data (New)**: The AI model automatically fetches macro indicators to understand the "weather" of the market:
    - **Volatility Index (`^VIX`)**: The "Fear Gauge." High VIX signals defensive posturing.
    - **10-Year Treasury Yield (`^TNX`)**: The "Cost of Money." High yields signal headwinds for Growth/Tech stocks.
- **Market Hours**: Operates on US Eastern Time (ET).

---

## 6. Summary
This system provides a rigorous, realistic backtesting environment for US trading, mirroring the ASX version's AI intelligence while strictly adhering to US regulatory fees, federal tax laws, and market structure constraints.

---
*Last Updated: February 1, 2026*
