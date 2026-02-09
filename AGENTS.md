# AGENTS.md: AI Agent Instructions

## 🎯 **CRITICAL: Read SOUL.md First**

**Before making ANY changes, read [SOUL.md](SOUL.md)** to understand:
- Project philosophy and core values (Data-Driven, Realism, Transparency, Flexibility)
- Architectural principles (Modularity, Factory Pattern, Consensus Logic)
- Security-first mindset and financial safety standards
- Development journey and lessons learned
- Code ownership and attribution standards

**All AI agents MUST align their work with SOUL.md principles. Non-compliance = rejected work.**

---

This document provides instructions for AI agents working on the **AI-Based Stock Investment System (USA Version)**. All agents MUST follow these guidelines to ensure consistency, safety, and code quality.

## 1. Project Overview

The goal is to build a Python-based trading strategy system for the United States Stock Markets (NYSE/NASDAQ). The system uses AI models trained on historical Yahoo Finance data (`yfinance`) to backtest and generate recommendations.

### Core Modules
- `core/config.py`: Configuration management (tickers, capital, thresholds, broker profiles).
- `core/model_builder.py`: AI model training and persistence.
- `core/backtest_engine.py`: Dual-mode backtesting engine with performance logging.
- `ui/`: Modular Streamlit dashboard components.
- `USA_AImodel.py`: Main application entry point.

## 2. Core Mandates

1. **Documentation-First Development**: Always update `usa_ai_trading_system_requirements.md` before implementing changes.
2. **Security Priorities**: NEVER commit API keys or sensitive financial data.
3. **Data Integrity**: Use standard US ticker symbols. Use `auto_adjust=True` and the `Close` column for all calculations.
4. **Technical Indicators**: Implement RSI, MACD, **Bollinger Bands, ATR**, and Moving Averages as standard features.
5. **Model Flexibility**: Support multiple algorithms (Random Forest, NGBoost, CatBoost, Prophet, LSTM) via factory pattern.
6. **Dual-Mode Analysis**:
   - **Mode 1**: Compare algorithms for a fixed strategy (Models Comparison).
   - **Mode 2**: Compare strategy timing/holding periods (Time-Span Comparison) using multi-model **Consensus**.
   - **Mode 3**: **Super Stars Scanner** — Benchmarking entire indexes to find top-performing individual stocks.
7. **Hurdle-Aware Decisions**: All buy signals MUST be filtered through the `get_hurdle_rate()` logic. This logic MUST be tax-aware (W-8BEN context).
8. **Fair Comparison (Warm-up)**: Fetch 90 days of additional historical data *before* the backtest start date.
9. **Data Preprocessing**: Support both `StandardScaler` and `RobustScaler`.
10. **Trading Constraints & Market Calendar**:
    - **US Calendar Compliance**: Use `get_usa_trading_days()` from `core/utils.py` to exclude weekends and holidays.
    - **T+1 Settlement Enforcement**: Strictly enforce a 1-trading-day delay for cash clearance after a sale in US markets.
11. **Transaction Ledger**:
    - **Memory-Optimized Design**: Keep only ~2 KB active state, not full ledger.
    - **Batch Writes**: Save to `data/ledgers/` on backtest completion.

## 3. Workflow & Automation Rules (Strict)

1. **Manual Commits Only**: NEVER run `git commit` or `git add` unless the user explicitly requests a commit.
2. **No Automatic Background Tasks**: NEVER start the dashboard or tests in the background automatically.
3. **Respect Local Environment**: Stick strictly to `requirements.txt` via the local virtual environment.
4. **Code-Only Implementation**: Focus on editing the requested files.

---
*Last Updated: 2026-02-09*
