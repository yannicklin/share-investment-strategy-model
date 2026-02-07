# AGENTS.md: AI Agent Instructions

## 🎯 **CRITICAL: Read SOUL.md First**

**Before making ANY changes, read [SOUL.md](SOUL.md)** to understand:
- Project philosophy and core values (Data-Driven, Realism, Transparency, Flexibility)
- Architectural principles (Modularity, Factory Pattern, Consensus Logic)
- Security-first mindset and financial safety standards
- Development journey and lessons learned (4 phases)
- Code ownership and attribution standards

**All AI agents MUST align their work with SOUL.md principles. Non-compliance = rejected work.**

---

This document provides instructions for AI agents working on the **AI Trading System (Multi-Market Architecture)**. All agents MUST follow these guidelines to ensure consistency, safety, and code quality.

> **Technical Reference**: See [ARCHITECTURE.md](ARCHITECTURE.md) for complete system architecture and specifications.

## 1. Project Overview

A Python-based trading strategy system supporting multiple stock exchanges through a **branch-based architecture**:
- **`asx`** branch → Australian Securities Exchange
- **`usa`** branch → NYSE/NASDAQ  
- **`twn`** branch → Taiwan Stock Exchange

Each branch is a standalone implementation with market-specific configurations. The system uses AI models trained on Yahoo Finance data to backtest and generate trading recommendations.

### Core Modules
- `core/config.py`: Configuration management (tickers, capital, thresholds).
- `core/model_builder.py`: AI model training and persistence.
- `core/backtest_engine.py`: Dual-mode backtesting engine with performance logging.
- `ui/`: Modular Streamlit dashboard components.
- `ASX_AImodel.py`: Main application entry point.

## 2. Lab-to-Production Workflow (Porting Rules)

Agents must respect the distinct roles of the project branches:

1.  **Market Branches (`asx`, `usa`, `twn`) — The "Research Labs"**:
    - Used for backtesting, parameter tuning, and algorithm evaluation.
    - If you are asked to "optimize" or "test" a strategy, work in these branches.
    - Result: Found the best `Config` parameters (hurdle rates, stop losses) for a specific market.

2.  **Bots Branch (`bots`) — The "Production Service"**:
    - Used for automated signal execution and notification.
    - **Sync Mandate**: Before implementing signal generation, you MUST check the corresponding lab branch for the latest optimized `Config`.
    - **Porting**: Copy the proven parameters into `app/bot/markets/{market}/config.py` and implement market-specific nuances in the `signal_service.py`.

## 3. Core Mandates

1. **Documentation-First Development**: Always update `ARCHITECTURE.md` before implementing changes.
2. **Security Priorities**: NEVER commit API keys or sensitive financial data.
3. **Data Integrity**: Use `.AX` ticker suffix. Use `auto_adjust=True` and the `Close` column for all calculations.
4. **Technical Indicators**: Implement RSI, MACD, and Moving Averages as standard features.
5. **Model Flexibility**: Support multiple algorithms (Random Forest, Gradient Boosting, CatBoost, Prophet, LSTM) via factory pattern. Prefer native Scikit-Learn versions for maximum portability.
6. **Dual-Mode Analysis**:
   - **Mode 1**: Compare algorithms for a fixed strategy (Models Comparison).
   - **Mode 2**: Compare strategy timing/holding periods (Time-Span Comparison) using multi-model **Consensus**.
    - **Mode 3**: **Super Stars Scanner** — Benchmarking entire indexes to find top-performing individual stocks.
7. **Hurdle-Aware Decisions**: All buy signals MUST be filtered through the `get_hurdle_rate()` logic in the decision layer. This logic MUST be tax-aware, ensuring the predicted return covers fees and a risk buffer after accounting for the user's marginal tax rate.
8. **Fair Comparison (Warm-up)**: Fetch 90 days of additional historical data *before* the backtest start date to prime technical indicators and sequence-based models (LSTM).
9. **Index Management**: Always maintain an automated way to refresh stock symbols from live market lists (e.g., `index_manager.py`).
10. **Data Preprocessing**: Support both `StandardScaler` and `RobustScaler`. Always validate array shapes before scaling to prevent crashes on "thin data" tickers.
    - **ASX Calendar Compliance**: Use `get_trading_days('ASX', ...)` to exclude weekends and holidays.
    - **T+2 Settlement Enforcement**: Strictly enforce a 2-trading-day delay for cash clearance after a sale for ASX market. Funds from a Monday sale are available on Wednesday at 10:15 AM.
    - **Holding Period Units**:
      - `"Day"` = **TRADING DAYS** (excludes weekends + holidays)
      - `"Week"/"Month"/"Year"` = **CALENDAR DAYS** (uses `pd.DateOffset()`)
15. **Performance Optimization**: Use `st.session_state` in the UI to cache results.
16. **Input Validation**: All ticker inputs MUST be validated against Yahoo Finance API before processing.
13. **Display Formatting**: Use numeral.js format strings for Streamlit NumberColumn:
    - Currency: `"$0,0.00"` (NOT Python format `"$,.2f"`)
    - Percentage: `"0.00%"` (auto-multiplies by 100, NOT `".2%"`)
    - Integer: `"0"` for whole numbers
14. **Multi-Channel Notifications**: System supports Telegram, LINE Messaging API, Email, and SMS for alerts and admin authentication. LINE integration is documented and ready for implementation (see `/docs/LINE_MESSAGING_INTEGRATION_GUIDE.md`). FREE tier (500 msg/month) covers typical bot usage.

---
*Last Updated: 2026-02-06 (Lab-to-Production Workflow Update)*
*Note: This is a living document. Update it as project conventions evolve.*
