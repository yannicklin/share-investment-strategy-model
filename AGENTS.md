# AGENTS.md: AI Agent Instructions

This document provides instructions for AI agents working on the **AI-Based Stock Investment System (ASX Version)**. All agents MUST follow these guidelines to ensure consistency, safety, and code quality.

## 1. Project Overview

The goal is to build a Python-based trading strategy system for the Australian Securities Exchange (ASX). The system uses AI models trained on historical Yahoo Finance data (`yfinance`) to backtest and generate recommendations.

### Core Modules
- `config.py`: Configuration management (tickers, capital, thresholds).
- `buildmodel.py`: AI model training and persistence.
- `backtest.py`: Backtesting engine with performance logging.
- `ui.py`: Streamlit dashboard for configuration and results.
- `shareinvestment_AImodel.py`: Main application entry point.

## 2. Core Mandates

1. **Documentation-First Development**: Always update `asx_ai_trading_system_requirements.md` before implementing changes.
2. **Security Priorities**: NEVER commit API keys or sensitive financial data.
3. **Data Integrity**: Use `.AX` ticker suffix. Use `auto_adjust=True` and the `Close` column for all calculations.
4. **Technical Indicators**: Implement RSI, MACD, and Moving Averages as standard features.
5. **Model Flexibility**: Support 7 algorithms (Random Forest, XGBoost, LightGBM, CatBoost, ElasticNet, SVR, Prophet) via factory pattern.
6. **Data Preprocessing**: Always apply `StandardScaler` to ensure consistency across linear and non-linear models.
7. **Comparative Analysis**: Support side-by-side comparison of different algorithms in the UI.
8. **Realistic Cost Accounting**: Include brokerage (0.12%), clearing (0.00225%), and settlement ($1.5) fees.
9. **Taxation Logic**: Implement ATO Capital Gains Tax rules (50% discount for holdings >= 12 months).
10. **Logic Constraints**: 
   - Enforce strict stop-loss rules (active at all times).
   - Enforce **Minimum Holding Periods** before allowing non-safety exits.
11. **Performance Optimization**: Use `st.session_state` in the UI to cache results.

...

---
*Last Updated: 2026-01-24 (Finalized 7-Algorithm Suite & Scaling)*
*Note: This is a living document. Update it as project conventions evolve.*
