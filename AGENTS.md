# AGENTS.md: AI Agent Instructions

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
5. **Model Flexibility**: Support 5 algorithms (Random Forest, XGBoost, CatBoost, Prophet, LSTM) via factory pattern.
6. **Dual-Mode Analysis**:
   - **Mode 1**: Compare algorithms for a fixed strategy (Models Comparison).
   - **Mode 2**: Compare strategy timing/holding periods (Time-Span Comparison) using multi-model **Consensus**.
   - **Mode 3**: **Super Stars Scanner** — Benchmarking entire indexes to find top-performing individual stocks.
7. **Index Management**: Always maintain an automated way to refresh stock symbols from live market lists (e.g., `index_manager.py`).
8. **Data Preprocessing**: Support both `StandardScaler` and `RobustScaler` to ensure consistency and handle market outliers effectively.
9. **Performance Optimization**: Use `st.session_state` in the UI to cache results.


...

---
*Last Updated: 2026-01-24 (Added Tie-Breaker & Strategy Sensitivity Toggle)*
*Note: This is a living document. Update it as project conventions evolve.*
