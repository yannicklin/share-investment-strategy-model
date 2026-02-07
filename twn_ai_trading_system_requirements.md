# AI-Based Stock Investment System Requirements (Taiwan Version)

## 1. Program Objective
Develop a Python-based stock trading strategy system for the **Taiwan Stock Market (TWSE, TPEx)**. The system uses AI models trained on **historical Taiwan market data** (e.g., OHLCV/K-line, MACD, RSI, KD, Volume indicators) to:

- Train an AI investment model on Taiwan stock data
- Backtest historical performance in TWD (New Taiwan Dollar)
- Generate buy/sell recommendations for future trading
- Predict optimal entry and exit points
- Maximise investment returns while enforcing strict stop-loss rules
- Handle real-world scenarios such as price gaps (e.g., selling at actual market price when stop-loss cannot be executed)
- Account for Taiwan-specific market characteristics (high retail participation, daily price limits)

The model may buy even if projected returns do not meet take-profit thresholds, as long as it identifies favourable conditions. Stop-loss rules must always be followed.

---

## 2. Program Modules

#### 2.1 Core Modules (`core/`)
- **`config.py`** — Centralized configuration management (tickers, capital in TWD, Taiwan brokerage profiles).
- **`model_builder.py`** — AI factory supporting 5 algorithms (Random Forest, Gradient Boosting, CatBoost, Prophet, LSTM) with automated scaling and sequential processing for LSTM.
- **`backtest_engine.py`** — Dual-mode simulation engine:
    - **Mode 1 (Models Comparison)**: Benchmarks individual AI performance for a fixed strategy.
    - **Mode 2 (Time-Span Comparison)**: Evaluates holding period efficiency using a **Multi-Model Consensus** (majority vote).
        - **Tie-Breaker Rule**: In the event of a 50/50 vote split, a user-selected Tie-Breaker model makes the final decision.
    - **Mode 3 (Find Super Stars)**: Scans Taiwan market indices to identify the **Top 10** performers for a chosen timeframe.

#### 2.2 Decision Layer & Hurdle Rate
To ensure realism and profitability, the system employs a **Fee-Aware Dynamic Hurdle Rate** in the decision layer for all analysis modes:
- **Break-even Calculation**: For every potential trade, the system calculates the minimum required return (%) using `(Total_Brokerage_Fee_Pct + STT_Pct) + Risk_Buffer`.
- **Note**: Taiwan has **NO capital gains tax** for individual stock investors, simplifying the calculation significantly.
- **Hurdle-Filtered Signals**: The AI model (or consensus) only generates a "BUY" signal if the predicted price increase exceeds this hurdle rate.
- **Small Capital Protection**: Prevents over-trading where brokerage fees and Securities Transaction Tax (STT) would erode the majority of potential profits.

#### 2.3 UI Modules (`ui/`)
- **`sidebar.py`** — Analysis mode selection and parameter configuration (holding periods, ticker selection).
- **`algo_view.py`** — Renders the **Models Comparison** leaderboard.
- **`strategy_view.py`** — Renders the **Time-Span Comparison** dashboard.
- **`stars_view.py`** — Renders the **Super Stars** leaderboard (Hall of Fame).
- **`components.py`** — Shared dashboard elements including the **Realized Equity Curve** and transaction logs with 2-decimal precision.

---

## 3. Financial Accounting & Reinvestment

### 3.1 Brokerage Fee Structure
Taiwan-specific broker profiles:
- **Fubon Securities (富邦證券)**:
    - **Brokerage Fee (Buy & Sell)**: 0.1425% (often discounted for online trades to ~0.06% or lower).
    - **Minimum Fee**: NT$20.
    - **API Support**: Fubon offers Python SDK for programmatic trading.
- **First Securities (第一證券)**:
    - **Brokerage Fee (Buy & Sell)**: 0.1425% (standard).
    - **Minimum Fee**: NT$20.
    - **API Support**: Traditional order placement, API integration via standard protocols.
- **Securities Transaction Tax (STT)**: 
    - **0.3% of sell value** (Government mandated, sell-side only).

### 3.2 Taxation (Taiwan MOF Rules)
- **Capital Gains Tax**: **ZERO** for individual investors trading domestic stocks.
- **Dividends**: Subject to individual income tax (can be consolidated or separated at 28%). *Note: Backtest currently focuses on price appreciation.*

### 3.3 Reinvestment & Settlement
- **T+2 Settlement**: Backtesting assumes a **T+2 settlement cycle** (capital available the second business day after a sale), providing a realistic simulation of Taiwan market cash flow.
- **Signal-Driven Entry**: Reinvestment only occurs when the **AI Consensus** triggers a "BUY" signal that exceeds the Hurdle Rate.

---

## 4. Market Characteristics & Data

### 4.1 Data Sources
- **FinMind API (Primary)**:
    - **Enhanced Features**: Includes OHLCV + **Institutional Net Buy (三大法人)**.
    - **Stability**: Highly reliable for Taiwan market data.
- **Yahoo Finance (`yfinance`) (Fallback)**:
    - **TWSE Tickers**: `[4-digit].TW` (e.g., `2330.TW`)
    - **TPEx Tickers**: `[4-digit].TWO` (e.g., `6488.TWO`)

### 4.2 Trading Rules
- **Trading Hours**: 09:00 - 13:30 Taiwan Standard Time (TST).
- **Price Limits (Ceiling/Floor)**: Daily movement limited to **±10%**. The system respects these limits in execution simulation.
- **Lot Size**: Standard trading unit is **1,000 shares**.

---

## 5. Summary
This system provides a rigorous, realistic backtesting environment for Taiwan trading, incorporating the zero-CGT advantage while strictly enforcing the high-friction STT and T+2 settlement constraints.

---
*Last Updated: February 7, 2026 (Sync with ASX Realism & T+2 standards)*
