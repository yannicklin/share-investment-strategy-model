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

## 🎯 **MATT POCOCK SKILLS INTEGRATION (Non-Negotiable Workflows)**

This project uses **Matt Pocock's engineering skills** for all development work. These skills enforce best practices around alignment, testing, architecture, and code quality.

### **Mandatory Workflows by Task Type**

#### 🔧 Any New Feature or Bug Fix
1. **`/grill-with-docs`** - Align on requirements + build shared terminology
   - Input: Your request
   - Output: Spec + updated CONTEXT.md (shared domain language)
   - Why: Prevents miscommunication between you and the agent

2. **`/to-spec`** - Codify requirements as structured spec
   - Input: Grilled conversation
   - Output: GitHub issue with acceptance criteria
   - Why: Makes success measurable and prevents scope creep

3. **`/tdd`** - Red-green-refactor development cycle
   - Input: Spec + acceptance criteria
   - Output: Failing test → passing test → refactored code
   - Why: Financial system = correctness is non-negotiable

4. **`/code-review`** - Two-axis review before committing
   - Input: Diff to review
   - Output: Standards + spec compliance assessment
   - Why: Catches regressions before they ship to production

#### 🐛 Production Issues (Critical)
1. **`/diagnosing-bugs`** - Structured debugging discipline
   - Step 1: Build feedback loop (make bug reproducible)
   - Step 2: Minimize (isolate the failing case)
   - Step 3: Hypothesize (what changed?)
   - Step 4: Instrument (add logging/monitoring)
   - Step 5: Fix + regression test
   - Why: Prevents band-aid fixes; solves root cause

#### 🏗️ Architecture & Refactoring
1. **`/improve-codebase-architecture`** - Run weekly
   - Scans for complexity, dead code, abstraction opportunities
   - Outputs HTML report with candidates ranked by impact
   - Why: Prevents entropy accumulation

2. **`/domain-modeling`** - Challenge terminology quarterly
   - Review CONTEXT.md glossary against actual usage
   - Test edge cases (what breaks these definitions?)
   - Update ADRs when terminology evolves
   - Why: Keeps shared language sharp and prevents miscommunication

3. **`/codebase-design`** - Deep modules, simple interfaces
   - Check: Does this module hide complexity well?
   - Check: Is the interface minimal and clear?
   - Check: Is it testable at the seam?
   - Why: Prevents ball-of-mud architecture

#### 🧪 Strategy Backtesting (Highest Risk)
1. **`/tdd`** - REQUIRED for any backtest logic change
   - Test strategy correctness BEFORE implementation
   - Test fee/tax accounting BEFORE deployment
   - Test warmup period logic BEFORE model training
   - Why: Incorrect backtests = false trading signals

2. **`/grill-with-docs`** - REQUIRED for new strategies
   - Clarify: What's the entry/exit rule?
   - Clarify: What edge cases break this strategy?
   - Clarify: How do we handle market gaps or halts?
   - Why: Market conditions are unpredictable; spec must be ironclad

#### 🔄 Large Multi-Session Work
1. **`/wayfinder`** - Plan huge projects as decision tickets
   - Breaks work into decision points on issue tracker
   - Resolves one decision at a time (agent picks next)
   - Why: Prevents losing context across multiple sessions

2. **`/handoff`** - Compact conversation for next agent
   - Current state, blockers, next steps
   - Why: Smooth handoff between development sessions

---

### **Agent Capabilities (How to Use Them)**

| Skill | User Types | When to Invoke | Output |
|-------|-----------|----------------|--------|
| `/grill-with-docs` | You + Agent | Before ANY feature work | Spec + CONTEXT.md updates |
| `/tdd` | Agent (model-invoked) | During implementation | Test suite + working code |
| `/to-spec` | You | After grilling | GitHub issue + acceptance criteria |
| `/code-review` | Agent | Before commit | Standards audit + spec audit |
| `/diagnosing-bugs` | Agent | On production failures | Root cause + fix + regression test |
| `/improve-codebase-architecture` | You | Weekly health check | HTML report + refactor candidates |
| `/domain-modeling` | Agent | Quarterly + as-needed | Updated CONTEXT.md + ADRs |
| `/codebase-design` | Agent | During refactoring | Architecture audit + improvements |
| `/wayfinder` | You | For 2+ week projects | Decision map on issue tracker |
| `/handoff` | Agent | End of session | Compact handoff document |

---

### **CONTEXT.md: Shared Domain Language**

Read **[CONTEXT.md](CONTEXT.md)** for shared terminology:
- **Strategy**, **Backtest**, **Signal**, **Model**, **Consensus**
- **State machines** (Model training, Backtest execution)
- **Financial constraints** (Fees, taxes, market slippage)
- **Performance metrics** (ROI, win rate, Sharpe ratio, drawdown)
- **Common debugging patterns**

This eliminates jargon confusion and speeds up agent reasoning.

---

This document provides instructions for AI agents working on the **AI-Based Stock Investment System (USA Version)**. All agents MUST follow these guidelines to ensure consistency, safety, and code quality.

---

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

## 3. Workflow & Automation Rules (Strict)

1. **Manual Commits Only**: NEVER run `git commit` or `git add` unless the user explicitly requests a commit. Do not assume a successful change implies a checkpoint is wanted.
2. **No Automatic Background Tasks**: NEVER start the dashboard or tests in the background (e.g., `make run &`) automatically after an edit. Wait for the user to request the start.
3. **Respect Local Environment**: Do not attempt to install system-level libraries (e.g., `brew install`). Stick strictly to `requirements.txt` via the local virtual environment.
4. **Code-Only Implementation**: Focus on editing the requested files. Do not chain multiple shell operations (like build or run) unless they are part of a verification step requested by the user.

---

## 4. Workflow & Automation Rules (Strict)

1. **Manual Commits Only**: NEVER run `git commit` or `git add` unless the user explicitly requests a commit.
2. **No Automatic Background Tasks**: NEVER start the dashboard or tests in the background automatically.
3. **Respect Local Environment**: Stick strictly to `requirements.txt` via the local virtual environment.
4. **Code-Only Implementation**: Focus on editing the requested files.

---
*Last Updated: 2026-02-09*
