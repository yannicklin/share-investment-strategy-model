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

This document provides instructions for AI agents working on the **AI-Based Stock Investment System (ASX Version)**. All agents MUST follow these guidelines to ensure consistency, safety, and code quality.

## 1. Project Overview

The goal is to build a Python-based trading strategy system for the Australian Securities Exchange (ASX). The system uses AI models trained on historical Yahoo Finance data (`yfinance`) to backtest and generate recommendations.

### Core Modules
- `core/config.py`: Configuration management (tickers, capital, thresholds).
- `core/model_builder.py`: AI model training and persistence.
- `core/backtest_engine.py`: Dual-mode backtesting engine with performance logging.
- `ui/`: Modular Streamlit dashboard components.
- `ASX_AImodel.py`: Main application entry point.

## 2. Core Mandates

1. **Documentation-First Development**: Always update `asx_ai_trading_system_requirements.md` before implementing changes.
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
11. **Performance Optimization**: Use `st.session_state` in the UI to cache results.
12. **Input Validation**: All ticker inputs MUST be validated against Yahoo Finance API before processing — use `validate_ticker()` function.
13. **Display Formatting**: Use numeral.js format strings for Streamlit NumberColumn:
    - Currency: `"$0,0.00"` (NOT Python format `"$,.2f"`)
    - Percentage: `"0.00%"` (auto-multiplies by 100, NOT `".2%"`)
    - Integer: `"0"` for whole numbers
14. **Trading Constraints & Market Calendar**:
    - **ASX Calendar Compliance**: Use `get_asx_trading_days()` from `core/utils.py` to exclude weekends and holidays.
    - **Market Half-Days**: Treat as off-days (no trading).
    - **Portfolio Validation**: ALWAYS call `validate_buy_capacity()` BEFORE generating ML signals to prevent unnecessary computation when funds are insufficient.
    - **Holding Period Units**:
      - `"Day"` = **TRADING DAYS** (excludes weekends + holidays via `calculate_trading_days_ahead()`)
      - `"Week"/"Month"/"Quarter"/"Year"` = **CALENDAR DAYS** (uses `pd.DateOffset()`)
15. **Transaction Ledger**:
    - **Memory-Optimized Design**: Keep only ~2 KB active state (portfolio + metrics + buffer), not full ledger.
    - **Batch Writes**: Save to `data/ledgers/` on backtest completion, then clear from memory. NO streaming I/O.
    - **Machine-Parseable Format**: CSV with 15 fields (date, ticker, action, quantity, price, commission, cash_before, cash_after, positions_before, positions_after, strategy, model_votes, confidence, notes).
    - **Date Format**: Use `format_date_with_weekday()` → `"YYYY-MM-DD(DAY)"` (e.g., `"2026-02-06(THU)"`).
    - **Ledger Generation**:
      - **Mode 1 (Models Comparison)**: Each model → separate ledger file.
      - **Mode 2/3 (Time-Span/Super Stars)**: Consensus voting → single ledger.
    - **Lifecycle**: Cleared on rerun (no archiving), NOT accessible via Dashboard UI (file system only).
    - **Location**: `data/ledgers/` folder, excluded from git via `.gitignore`.

## 3. Workflow & Automation Rules (Strict)

1. **Manual Commits Only**: NEVER run `git commit` or `git add` unless the user explicitly requests a commit. Do not assume a successful change implies a checkpoint is wanted.
2. **No Automatic Background Tasks**: NEVER start the dashboard or tests in the background (e.g., `make run &`) automatically after an edit. Wait for the user to request the start.
3. **Respect Local Environment**: Do not attempt to install system-level libraries (e.g., `brew install`). Stick strictly to `requirements.txt` via the local virtual environment.
4. **Code-Only Implementation**: Focus on editing the requested files. Do not chain multiple shell operations (like build or run) unless they are part of a verification step requested by the user.

---
*Last Updated: 2026-02-06 (Trading Constraints & Transaction Ledger Integration)*
*Note: This is a living document. Update it as project conventions evolve.*
