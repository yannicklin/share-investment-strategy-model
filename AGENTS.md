# AGENTS.md: Framework Directives

## 🎯 **CRITICAL: Align with SOUL.md**

Every modification to this codebase must be a reflection of the core personalities defined in **[SOUL.md](SOUL.md)**. If a proposed change compromises **Realism**, **Objectivity**, or **Transparency**, it must be rejected.

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

## 1. Framework Identity

This is a Python-based research infrastructure designed for the cold, clinical analysis of trading strategies. It does not chase "hype"; it hunts for statistically significant patterns within the constraints of real-world friction.

### Structural Pillars:
- **Modular Logic**: Separation of data, modeling, and financial accounting.
- **Factory Interfacing**: Unified standards for integrating diverse AI algorithms.
- **Decision Layer**: A mandatory filter for financial sanity and consensus.

## 2. Core Mandates

1. **Integrity-First Development**: Documentation and requirements must be updated to reflect architectural changes before any code is written.
2. **Financial Safety**: Zero tolerance for hardcoded secrets or exposed sensitive data.
3. **Data Integrity**: Use TWD currency notation. Use `auto_adjust=True` and the `Close` column for all calculations from FinMind/yfinance.
4. **Technical Indicators**: Implement RSI, MACD, Bollinger Bands, ATR, and Moving Averages as standard features.
5. **Model Flexibility**: Support multiple algorithms (Random Forest, NGBoost, CatBoost, Prophet, LSTM) via factory pattern. Prefer native Scikit-Learn versions for maximum portability.
6. **Dual-Mode Analysis**:
   - **Mode 1**: Compare algorithms for a fixed strategy (Models Comparison).
   - **Mode 2**: Compare strategy timing/holding periods (Time-Span Comparison) using multi-model **Consensus**.
   - **Mode 3**: **Super Stars Scanner** — Benchmarking entire indices (TAIEX, Electronics, Finance) to find top-performing individual stocks.
7. **Hurdle-Aware Decisions**: All buy signals MUST be filtered through the `get_hurdle_rate()` logic in the decision layer. This logic MUST be tax-aware, ensuring the predicted return covers fees and a risk buffer after accounting for the user's marginal tax rate.
8. **Fair Comparison (Warm-up)**: Fetch 90 days of additional historical data *before* the backtest start date to prime technical indicators and sequence-based models (LSTM).
9. **Index Management**: Always maintain an automated way to refresh stock symbols from live market lists (e.g., `index_manager.py` for TAIEX, Electronics sector).
10. **Data Preprocessing**: Support both `StandardScaler` and `RobustScaler`. Always validate array shapes before scaling to prevent crashes on "thin data" tickers.
11. **Performance Optimization**: Use `st.session_state` in the UI to cache results.
12. **Input Validation**: All ticker inputs MUST be validated against FinMind/Yahoo Finance API before processing — use `validate_ticker()` function.
13. **Display Formatting**: Use numeral.js format strings for Streamlit NumberColumn:
    - Currency: `"$0,0.00"` (NOT Python format `"$,.2f"`)
    - Percentage: `"0.00%"` (auto-multiplies by 100, NOT `".2%"`)
    - Integer: `"0"` for whole numbers
14. **Trading Constraints & Market Calendar**:
    - **Taiwan Calendar Compliance**: Use `get_tse_trading_days()` from `core/utils.py` to exclude weekends and holidays (Chinese New Year, etc.).
    - **Market Hours**: TSE opens 09:00, closes 13:30 (morning session) + 14:30-15:00 (afternoon session).
    - **Portfolio Validation**: ALWAYS call `validate_buy_capacity()` BEFORE generating ML signals to prevent unnecessary computation when funds are insufficient.
    - **T+2 Settlement Enforcement**: Strictly enforce a 2-trading-day delay for cash clearance after a sale. Funds from a Monday sale are available on Wednesday at 10:15 AM.
    - **Holding Period Units**:
      - `"Day"` = **TRADING DAYS** (excludes weekends + holidays via `calculate_trading_days_ahead()`)
      - `"Week"/"Month"/"Year"` = **CALENDAR DAYS** (uses `pd.DateOffset()`)
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

## 3. Taiwan Market Implementation (FinMind Integration)

**Status**: ✅ IMPLEMENTED - FinMind API for Taiwan market data + institutional flows

### Implementation Details

**Why FinMind for Taiwan Market?**
- ✅ **Taiwan-native data** — Official TSE/OTC data with institutional flows (Foreign/Trust)
- ✅ **No rate limits** — Enterprise API designed for Taiwan market analysis
- ✅ **Institutional insight** — Margin Trading (RongZi/RongQuan), Foreign investor flows
- ✅ **Revenue growth data** — TTM revenue by company for fundamental screening
- ✅ **Market calendar compliance** — Respects TSE holidays (Chinese New Year, etc.)
- ✅ **Price limit enforcement** — ±10% daily ceiling/floor built-in

**Hybrid Architecture (FinMind + yfinance fallback)**:
- **Primary**: FinMind API — Taiwan market (TSE/OTC stocks)
- **Fallback**: yfinance — If FinMind unavailable (graceful degradation)
- **Global context**: yfinance for ^TWII (TAIEX), ^SOX (USA semiconductors), ^IXIC (tech), TWD=X (currency correlation)

### Files Modified

| File | Change | Purpose |
|------|--------|---------|
| `core/data_helpers/` | New directory | Market-specific data fetchers |
| `core/data_helpers/base_data_helper.py` | New file | Abstract base class |
| `core/data_helpers/twn_data_helper.py` | New file | FinMind implementation |
| `core/model_builder.py` | Updated | Route TWN to FinMind helper |
| `requirements.txt` | Added finmind | New dependency (v1.0.0+) |

### Setup (For Deployers)

```bash
# 1. Create free FinMind account
#    Go to https://finmind.github.io/ → Sign up (free tier available)
#    Copy API Token from dashboard

# 2. Add to environment (.env or shell)
export FINMIND_API_TOKEN=your_token_here

# 3. Install dependency
pip install finmind

# 4. Verify (logs will show "✅ FinMind client initialized successfully")
```

### Institutional Data Integration

**Foreign Investor Flows** (daily sentiment):
- Endpoint: `/data?dataset=TaiwaneseStockInfo&data_id=foreign_trade_volume`
- Interpretation: Positive = foreign buying (bullish); Negative = foreign selling (bearish)
- Usage: Secondary signal for momentum confirmation

**Margin Trading (RongZi/RongQuan)**:
- Endpoint: `/data?dataset=TaiwaneseStockInfo&data_id=margin_trading`
- Interpretation: Rising margin % = leverage buildup (increased risk); Falling margin = de-leveraging
- Usage: Risk gauge for position sizing

**Revenue Growth** (TTM):
- Endpoint: `/data?dataset=FinancialSummary&data_id=revenue`
- Interpretation: YoY revenue growth screens for fundamental quality
- Usage: Filter out low-growth or declining companies before backtesting

### Key Features

| Feature | Status | Details |
|---------|--------|---------|
| **Historical data fetch** | ✅ | 90-day warmup + multi-year backtesting |
| **Institutional flows** | ✅ | Foreign/Trust/Margin data integration |
| **Revenue screening** | ✅ | TTM growth for fundamental filters |
| **Price limit enforcement** | ✅ | ±10% daily limits validated |
| **Fallback to yfinance** | ✅ | Automatic if FinMind unavailable |
| **TSE calendar** | ✅ | Respects Taiwan holidays |

### Auto-Fallback Logic

```python
# _download_with_retry() in model_builder.py
try:
    data_helper = get_data_helper("TWN")
    df = data_helper.fetch_historical_data(ticker, start_date, end_date)
    institutional_flows = data_helper.fetch_institutional_flows(ticker)
except:
    logger.debug("Falling back to yfinance for {ticker}")
    # Continue with yfinance retry logic
```

**Result**: System remains robust — if FinMind is down, yfinance takes over automatically.

### Performance Impact

| Operation | Before | After | Improvement |
|-----------|--------|-------|------------|
| Single ticker fetch | ~2-3s | ~200-500ms | 5-10x faster |
| Batch fetch (20 tickers) | ~5-10s | ~1-2s | 5x faster |
| Super Stars scan (50 TAIEX stocks) | ~30s-2min | ~10-30s | 2-3x faster |
| Institutional flow integration | ❌ Manual lookup | ✅ Automated | Eliminated friction |
| Rate limit risk | ❌ High (yfinance throttles) | ✅ None (FinMind enterprise) | Eliminated |

## 4. Workflow & Automation Rules (Strict)

1. **Manual Commits Only**: NEVER run `git commit` or `git add` unless the user explicitly requests a commit. Do not assume a successful change implies a checkpoint is wanted.
2. **No Automatic Background Tasks**: NEVER start the dashboard or tests in the background (e.g., `make run &`) automatically after an edit. Wait for the user to request the start.
3. **Respect Local Environment**: Do not attempt to install system-level libraries (e.g., `brew install`). Stick strictly to `requirements.txt` via the local virtual environment.
4. **Code-Only Implementation**: Focus on editing the requested files. Do not chain multiple shell operations (like build or run) unless they are part of a verification step requested by the user.

---
*Last Updated: 2026-08-23 (Taiwan Market Implementation - FinMind Integration)*
*Note: This is a living document. Update it as project conventions evolve.*
