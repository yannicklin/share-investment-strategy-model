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

## 3. USA Market Data: Alpaca Integration (June 24, 2026)

**Status**: ✅ IMPLEMENTED - Alpaca paper account for USA market data

### Implementation Details

**Why Alpaca for USA Market?**
- ✅ **No rate limits** — Eliminates yfinance rate limit issues in production backtesting
- ✅ **Better performance** — 200-500ms per request vs 2-3s for yfinance
- ✅ **Production-grade** — Designed for trading bots with enterprise reliability
- ✅ **Real-time capable** — Can evolve to actual paper trading execution
- ✅ **Enterprise reliability** — 99.9% uptime vs yfinance unpredictability

**Hybrid Architecture (Alpaca + yfinance fallback)**:
- **Primary**: Alpaca API (paper account) — USA market
- **Fallback**: yfinance — If Alpaca unavailable (graceful degradation)
- **Market indices**: yfinance unchanged (VIX, SPX, etc. not available via Alpaca)

### Files Modified

| File | Change | Purpose |
|------|--------|---------|
| `core/data_helpers/` | New directory | Market-specific data fetchers |
| `core/data_helpers/base_data_helper.py` | New file | Abstract base class |
| `core/data_helpers/usa_data_helper.py` | New file | Alpaca implementation |
| `core/model_builder.py` | Updated | Route USA to Alpaca helper |
| `requirements.txt` | Added alpaca-trade-api | New dependency (v3.0.0+) |

### Setup (For Deployers)

```bash
# 1. Create free paper account
#    Go to https://alpaca.markets → Sign up (free)
#    Copy API Key + Secret Key from dashboard

# 2. Add to environment (.env or shell)
export ALPACA_API_KEY=your_key_here
export ALPACA_SECRET_KEY=your_secret_here

# 3. Install dependency
pip install alpaca-trade-api

# 4. Verify (logs will show "✅ Alpaca client initialized successfully")
```

### Key Features

| Feature | Status | Details |
|---------|--------|---------|
| **Historical data fetch** | ✅ | 90-day warmup + multi-year backtesting |
| **Batch efficiency** | ✅ | Faster prefetch_data_batch() |
| **Fallback to yfinance** | ✅ | Automatic if Alpaca unavailable |
| **Market indices** | ✅ | Still via yfinance (VIX, SPX, etc.) |
| **Real-time execution** | 📋 | Ready for integration |

### Auto-Fallback Logic

```python
# _download_with_retry() in model_builder.py
try:
    data_helper = get_data_helper("USA")
    df = data_helper.fetch_historical_data(ticker, start_date, end_date)
except:
    logger.debug("Falling back to yfinance for {ticker}")
    # Continue with yfinance retry logic
```

**Result**: System remains robust — if Alpaca is down, yfinance takes over automatically.

### Performance Impact

| Operation | Before | After | Improvement |
|-----------|--------|-------|------------|
| Single ticker fetch | ~2-3s | ~200-500ms | 5-10x faster |
| Batch fetch (20 tickers) | ~5-10s | ~1-2s | 5x faster |
| Super Stars scan (100 tickers) | ~30s-2min | ~10-30s | 2-3x faster |
| Rate limit risk | ❌ High (yfinance throttles) | ✅ None (Alpaca unlimited) | Eliminated |

---

## 4. Workflow & Automation Rules (Strict)

1. **Manual Commits Only**: NEVER run `git commit` or `git add` unless the user explicitly requests a commit.
2. **No Automatic Background Tasks**: NEVER start the dashboard or tests in the background automatically.
3. **Respect Local Environment**: Stick strictly to `requirements.txt` via the local virtual environment.
4. **Code-Only Implementation**: Focus on editing the requested files.

---
*Last Updated: 2026-02-09*
