# AI-Based Stock Investment System Requirements (Taiwan Version)

## 1. Program Objective
Develop a Python-based stock trading strategy system for the **Taiwan Stock Market (TWSE, TPEx)**. The system uses AI models trained on **historical Taiwan market data** (e.g., OHLCV/K-line, MACD, RSI, KD, Volume indicators, Institutional Buying Pressure) to:

- Train an AI investment model on Taiwan stock data
- Backtest historical performance in TWD (New Taiwan Dollar)
- Generate buy/sell recommendations for future trading
- Predict optimal entry and exit points
- Maximise investment returns while enforcing strict stop-loss rules
- Handle real-world scenarios such as price gaps (e.g., selling at actual market price when stop-loss cannot be executed)
- Account for Taiwan-specific market characteristics (high retail participation, institutional flows, margin trading activity)

The model may buy even if projected returns do not meet take-profit thresholds, as long as it identifies favourable conditions. Stop-loss rules must always be followed.

---

## 2. Program Modules

#### 2.1 Core Modules (`core/`)
- **`config.py`** — Centralized configuration management (tickers, capital in TWD, Taiwan brokerage profiles).
- **`model_builder.py`** — AI factory supporting 5 algorithms (Random Forest, XGBoost, CatBoost, Prophet, LSTM) with automated scaling and sequential processing for LSTM.
    - **Enhanced Feature Set**: Includes Taiwan-specific indicators:
        - **Volume Indicators**: Volume Ratio, 5/10/20-day Volume MA
        - **Institutional Flows**: Foreign Investors Net Buy, Investment Trust Net Buy, Dealer Net Buy
        - **Technical Indicators**: RSI, KD (Stochastic), Bollinger Bands, DMI, William %R
        - **Margin Trading**: Margin Balance Ratio, Short Interest Ratio
        - **Market Breadth**: Advancing/Declining Volume Ratio
- **`backtest_engine.py`** — Dual-mode simulation engine:
    - **Mode 1 (Models Comparison)**: Benchmarks individual AI performance for a fixed strategy.
    - **Mode 2 (Time-Span Comparison)**: Evaluates holding period efficiency using a **Multi-Model Consensus** (majority vote).
        - **Tie-Breaker Rule**: In the event of a 50/50 vote split, a user-selected Tie-Breaker model makes the final decision.
    - **Mode 3 (Find Super Stars)**: Scans Taiwan market indFee-Aware Dynamic Hurdle Rate** in the decision layer for all analysis modes:
- **Break-even Calculation**: For every potential trade, the system calculates the minimum required return (%) using `(Brokerage_Fee_Pct + STT_Pct) + Risk_Buffer`.
    - **Note**: Taiwan has **NO capital gains tax** for individual stock investors, simplifying the calculation significantly.
- **Hurdle-Filtered Signals**: The AI model (or consensus) only generates a "BUY" signal if the predicted price increase exceeds this hurdle rate.
- **Small Capital Protection**: Prevents over-trading where brokerage fees and Securities Transaction Tax (STT) would erode the majority of potential profits.
- **Day Trading Consideration**: Taiwan allows day trading (buy and sell same stock on same day), but STT is still charged on the sell side
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

### 3.1 Fee StructurTaiwan-specific broker profiles:
- **Online Discount Broker (e.g., Fubon, Yuanta, KGI)**:
    - **Brokerage Fee (Buy & Sell)**: 0.1425% of trade value (negotiable, typically 0.1% to 0.06% for online trading)
    - **Securities Transaction Tax (STT, Sell-side only)**: 0.3% of sell value (government mandated)
    - **Minimum Brokerage**: NT$20 per transaction
- **Full-Service Broker**:
    - **Brokerage Fee (Buy & Sell)**: 0.1425% of trade value (standard rate)
    - **Securities Transaction Tax (STT, Sell-side only)**: 0.3% of sell value
    - **Minimum Brokerage**: NT$20 per transaction

**Total Round-Trip Cost (Buy + Sell)**:
- Discount Online: ~0.485% (0.1% + 0.1% + 0.3%)
- Full Service: ~0.585% (0.1425% + 0.1425% + 0.3%)

### 3.2 Taxation (Taiwan MOF Rules)
**Capital Gains Tax**: 
- **Individual Investors**: **ZERO** — Taiwan does NOT impose capital gains tax on stock trading profits for individuals.
- **Corporate Investors**: Subject to corporate income tax (not applicable to this system).
- **Securities Transaction Tax (STT)**: The 0.3% sell-side STT is the only tax burden, already included in fee calculations above.

### 3.3 Reinvestment & SettlemTaiwan)

### 4.1 Primary Data Sources
- **Yahoo Finance (`yfinance`)**: 
    - **Ticker Format**: 4-digit stock code + `.TW` suffix for TWSE stocks (e.g., `2330.TW` for TSMC, `2317.TW` for Hon Hai).
    - **TPEx Stocks**: Use `.TWO` suffix (e.g., `6488.TWO` for Onward Security).
    - **Adjustment**: Always use `auto_adjust=True` and target the `Close` price for calculations.
    - **Coverage**: Good for OHLCV data, but lacks institutional flow data.

- **Taiwan Economic Journal (TEJ) API** (Optional, Professional):Taiwan trading, incorporating:
- **Zero Capital Gains Tax**: Simplified profitability calculations without complex tax brackets.
- **Transparent Fee Structure**: Fixed brokerage + 0.3% STT on sell side.
- **Taiwan-Specific Indicators**: KD, Institutional Flows, Margin Trading metrics.
- **T+2 Settlement**: Realistic cash flow modeling aligned with Taiwan market rules.
- **TAIEX Focus**: Analyzing Taiwan's technology-heavy market with appropriate features.

The system delivers AI-powered insights while strictly adhering to Taiwan Securities and Futures Bureau (SFB) regulations and Taiwan Stock Exchange trading rules.

---
*Last Updated: February 4, 2026 (Converted to Taiwan Version)
- **TWSE Open Data Platform** (Free, Official):
    - Real-time institutional trading data (Foreign Investors, Investment Trust, Dealers).
    - Daily margin trading and short selling statistics.
    - Market breadth indicators.
    - **Recommendation**: Supplement `yfinance` with TWSE data for enhanced feature engineering.

### 4.2 Enhanced Feature Engineering
Beyond standard OHLCV, the system should incorporate:
- **Volume Indicators**: Volume Ratio (Current / 20-day MA), Volume Trend
- **KD Indicator**: K value, D value, J value (extremely popular in Taiwan)
- **RSI**: 6-day, 12-day RSI
- **Bollinger Bands**: Upper, Middle, Lower bands with 20-day MA
- **Institutional Flows**: Foreign Investor Net Buy (NT$), Investment Trust Net Buy (NT$)
- **Margin Trading**: Margin Balance, Short Interest, Margin Ratio
- **Market Breadth**: Advancing/Declining issues ratio

### 4.3 Market Characteristics
- **Trading Hours**: 09:00 - 13:30 Taiwan Standard Time (TST, UTC+8)
- **No Lunch Break**: Continuous trading session (unlike some Asian markets)
- **Price Limits**: Daily price movement limited to ±10% (circuit breaker)
- **Tick Size**: Varies by price range (e.g., NT$0.01 for stocks < NT$10, NT$0.05 for NT$10-50, NT$0.1 for NT$50-100, etc.)hen the **AI Consensus** triggers a "BUY" signal.

---

## 4. Historical Data Source (USA)
Exclusively uses **Yahoo Finance (`yfinance`)**. 
- **Ticker format**: Standard US symbols (e.g., `AAPL`, `TSLA`, `NVDA`). No suffix required.
- **Adjustment**: Always use `auto_adjust=True` and target the `Close` price for calculations.
- **Market Hours**: Operates on US Eastern Time (ET).

---

## 5. Summary
This system provides a rigorous, realistic backtesting environment for US trading, mirroring the ASX version's AI intelligence while strictly adhering to US regulatory fees and federal tax laws.

---
*Last Updated: February 1, 2026*
