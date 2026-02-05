# Trading Constraints & Transaction Ledger - Specification

**Version**: 1.0  
**Author**: ASX AI Trading System (Backtesting Dashboard)  
**Date**: 2026-02-06  
**Status**: ✅ INTEGRATED into Main Requirements  
**Branch**: `asx` (Streamlit Interactive Dashboard)

> **Note**: This detailed specification has been integrated into the main requirements document:  
> **`asx_ai_trading_system_requirements.md` → Section 4: Trading Constraints & Realism**
>
> This file serves as extended documentation with user scenarios, test cases, and implementation details.  
> For high-level requirements, refer to the main requirements document.

---

## Important Context: System Modes & Ledger Generation

The ASX AI Trading System has **3 backtest modes** with different ledger generation patterns:

### Mode 1: Models Comparison
- **Purpose**: Evaluate each AI model's performance separately
- **Ledger Generation**: **Each model creates separate ledger** for comparison
- **Example**: 1 stock × 5 models = **5 separate backtests** = 5 ledger files
- **Worst-case**: ASX 200 × 5 models = **1,000 backtests** = ~600-800 MB total disk output

### Mode 2: Time-Span Comparison
- **Purpose**: Compare different holding periods (e.g., 7-day vs 30-day vs quarterly)
- **Ledger Generation**: **Models vote as consensus team** → single ledger per holding period
- **Example**: 1 stock × 4 holding periods = **4 backtests** (not 4×5=20)
- **Signal process**: 5 models → consensus vote (BUY/SELL/HOLD) → single transaction entry

### Mode 3: Super Stars Scanner
- **Purpose**: Find top 10 performers from entire ASX 200 index
- **Ledger Generation**: **Models vote as consensus team** → single ledger per stock
- **Example**: ASX 200 × 1 consensus = **200 backtests** (not 200×5=1,000)
- **Signal process**: 5 models → consensus vote → single ledger per stock

**Key Insight**: Only Mode 1 generates "stocks × models" combinations. Modes 2 and 3 use consensus voting, so 5 models work as a single decision-making team.

---

## 1. User Scenarios & Testing

### User Story 1: Holiday-Aware Backtesting
**As a** backtesting user exploring historical strategies  
**I want** the system to automatically skip ASX public holidays in historical data  
**So that** my backtest results reflect realistic trading conditions (no impossible trades on closed days)

**Acceptance Scenarios**:
```
GIVEN: Backtesting period is 2025-12-20 to 2026-01-05
  AND: 2025-12-25 (Christmas Day) is ASX holiday
  AND: 2025-12-26 (Boxing Day) is ASX holiday
  AND: 2026-01-01 (New Year's Day) is ASX holiday
WHEN: Backtest engine processes historical data
THEN: System skips these dates:
  - 2025-12-21(SAT), 2025-12-22(SUN) ← Weekends
  - 2025-12-25(WED) ← Christmas Day
  - 2025-12-26(THU) ← Boxing Day
  - 2025-12-28(SAT), 2025-12-29(SUN) ← Weekends
  - 2026-01-01(THU) ← New Year's Day
  - 2026-01-03(SAT), 2026-01-04(SUN) ← Weekends
  AND: Only processes valid trading days
  AND: Dashboard displays filtered date range with holidays excluded

GIVEN: User runs "Models Comparison" mode for ABB.AX
  AND: Backtest period includes 2026-01-26 (Australia Day - ASX closed)
WHEN: Results displayed
THEN: Transaction ledger shows no trades on 2026-01-26
  AND: Date column skips from 2026-01-23(FRI) to 2026-01-27(MON)
  AND: Summary shows: "Trading days: 20 (2 holidays excluded)"
```

**Edge Cases**:
- Holiday falls on weekend → Skip anyway (already weekend constraint)
- Market half-day (e.g., Christmas Eve) → Mark as off-day (no trading allowed)
- Historical backtest spans multiple years → Correctly apply holidays for each year (2024, 2025, 2026 calendars)
- Backtest always uses "Year" range → No risk of selecting date range with ALL holidays

---

### User Story 2: Weekday Constraint in Simulations
**As a** backtesting user  
**I want** the system to only simulate trades Monday-Friday  
**So that** my backtest results exclude weekend noise and reflect real ASX operating hours

**Acceptance Scenarios**:
```
GIVEN: Historical price data includes Saturday/Sunday data points
WHEN: Backtest engine loads data for ABB.AX
THEN: Weekends automatically filtered out
  AND: Date sequence shows: 2026-02-06(FRI) → 2026-02-09(MON)
  AND: No Saturday/Sunday entries in transaction ledger

GIVEN: User selects "Time-Span Comparison" mode with "Day" unit
  AND: Compares 7-day vs 14-day vs 30-day holding periods
WHEN: Backtest runs
THEN: "Day" holding periods calculated in TRADING DAYS (not calendar days)
  - 7-day hold = 7 weekdays (excludes weekends + holidays)
  - 14-day hold = 14 weekdays (excludes weekends + holidays)
  - 30-day hold = 30 weekdays (skips ~8 weekend days + holidays)

GIVEN: User selects "Time-Span Comparison" mode with other units
  AND: Compares "Week" vs "Month" vs "Quarterly" vs "Year" holding periods
WHEN: Backtest runs
THEN: Non-Day units calculated in CALENDAR DAYS (includes weekends)
  - 1-week hold = 7 calendar days (includes 2 weekend days)
  - 1-month hold = ~30 calendar days (includes ~8 weekend days)
  - 1-quarter hold = ~90 calendar days (includes ~25 weekend days)
  - Rationale: Longer timeframes naturally span weekends; calendar-based more intuitive
```

**Independent Tests**:
```python
# Test weekday filtering
def test_filter_trading_days_removes_weekends():
    dates = pd.date_range("2026-02-01", "2026-02-08")  # Sun-Sun
    trading_days = filter_trading_days(dates)
    assert len(trading_days) == 5  # Mon-Fri only
    assert all(d.dayofweek < 5 for d in trading_days)

# Test holding period calculation - "Day" unit (TRADING DAYS)
def test_holding_period_day_unit_excludes_weekends():
    buy_date = pd.Timestamp("2026-02-06")  # Friday
    sell_date = calculate_sell_date(buy_date, holding_period=7, unit="Day")
    assert sell_date == pd.Timestamp("2026-02-17")  # Mon (after 7 TRADING days)

# Test holding period calculation - Other units (CALENDAR DAYS)
def test_holding_period_month_unit_includes_weekends():
    buy_date = pd.Timestamp("2026-02-06")  # Friday
    sell_date = calculate_sell_date(buy_date, holding_period=1, unit="Month")
    # 1 month = ~30 calendar days (includes weekends)
    expected = buy_date + pd.DateOffset(months=1)
    assert sell_date == expected  # 2026-03-06 (includes weekends)
```

---

### User Story 3: Pre-Transaction Portfolio Validation in Backtest
**As a** backtesting user with simulated $10,000 starting capital  
**I want** the system to check available cash and positions BEFORE generating signals  
**So that** my backtest doesn't show impossible trades (buying stocks I can't afford)

**Acceptance Scenarios**:
```
GIVEN: Backtest starts with $10,000 cash
  AND: On 2026-02-10, portfolio state:
    - Cash available: $1,200
    - Positions: {ABB.AX: 50 units @ $15 = $750 value}
  AND: Current prices: ABB.AX=$16, SIG.AX=$55, XRO.AX=$120
WHEN: Backtest evaluates BUY signals for 2026-02-10
THEN: System checks BEFORE running models:
  - Can afford SIG.AX? $1,200 >= $55 ✓ (max 21 units)
  - Can afford XRO.AX? $1,200 >= $120 ✓ (max 10 units)
  - Can afford additional ABB.AX? $1,200 >= $16 ✓ (max 75 units)
  AND: Proceeds with signal generation

GIVEN: Portfolio cash depleted to $50
  AND: Cheapest stock in watchlist = ABB.AX @ $55
WHEN: Backtest evaluates 2026-02-12
THEN: System skips model execution for BUY signals
  AND: Logs "2026-02-12: Insufficient cash ($50) - cannot afford ABB.AX ($55)"
  AND: Transaction ledger shows no BUY attempts
  AND: Can only process SELL signals (if positions exist)

GIVEN: Portfolio has 100 units ABB.AX (all capital tied up)
  AND: Model suggests BUY MQG.AX
WHEN: Pre-transaction check runs
THEN: System detects $0 available cash
  AND: BUY signal skipped (cannot execute)
  AND: SELL signals still evaluated (can sell ABB.AX to free cash)
```

**Independent Tests**:
```python
def test_pre_transaction_validation_sufficient_cash():
    portfolio = Portfolio(cash=10000, positions={})
    state = portfolio.get_state_at("2026-02-10")
    result = validate_buy_capacity(state, price_dict={"ABB.AX": 15, "SIG.AX": 55})
    assert result["can_buy"]["ABB.AX"] == True
    assert result["max_units"]["ABB.AX"] == 666  # $10000 / $15
    assert result["can_buy"]["SIG.AX"] == True
    assert result["max_units"]["SIG.AX"] == 181  # $10000 / $55

def test_pre_transaction_validation_insufficient_cash():
    portfolio = Portfolio(cash=50, positions={})
    result = validate_buy_capacity(portfolio.get_state(), {"ABB.AX": 55})
    assert result["can_buy"]["ABB.AX"] == False
    assert result["reason"] == "Insufficient cash: $50 < $55"
```

---

### User Story 4: Transaction Ledger for Backtest Audit Trail
**As a** backtesting user debugging strategy performance  
**I want** every simulated trade logged in a machine-parseable ledger  
**So that** I can audit exactly what happened via AI agents or scripts and verify no logic errors occurred

**Acceptance Scenarios**:
```
GIVEN: Backtest generates BUY signal for ABB.AX on 2026-02-06(FRI)
WHEN: Signal executed in simulation
THEN: Transaction ledger entry created:
  {
    "date": "2026-02-06(FRI)",
    "ticker": "ABB.AX",
    "action": "BUY",
    "quantity": 50,
    "price": 15.25,
    "total_value": 762.50,
    "commission": 9.95,
    "cash_before": 10000.00,
    "cash_after": 9227.55,
    "positions_before": {},
    "positions_after": {"ABB.AX": 50},
    "strategy": "consensus-30d",
    "model_votes": {"random_forest": "BUY", "catboost": "BUY", "lstm": "HOLD"},
    "confidence": 0.87,
    "notes": "Initial purchase"
  }

GIVEN: Backtest sells ABB.AX on 2026-03-10(TUE) after 30-day hold
WHEN: SELL executed
THEN: Ledger entry includes:
  {
    "date": "2026-03-10(TUE)",
    "action": "SELL",
    "quantity": 50,
    "price": 17.80,
    "profit_loss": +$117.55,  # ($17.80 - $15.25) × 50 - fees
    "holding_days": 30,
    "buy_date": "2026-02-06(FRI)",
    "capital_gains_eligible": false,  # <12 months = no CGT discount
    "notes": "30-day hold completed"
  }

GIVEN: User re-runs same backtest (debugging)
WHEN: Backtest starts
THEN: Previous ledger automatically cleared (overwritten)
  AND: New empty ledger created
  AND: System writes new ledger to "data/ledgers/backtest_{timestamp}.csv"
  AND: Ledger metadata includes: run_id, timestamp, strategy_id, tickers
```

**Ledger Management Rules**:
- Each backtest run creates new ledger (not persistent across sessions)
- Ledger automatically cleared (overwritten) when user clicks "Re-run Backtest" or changes parameters
- Ledger NOT accessible via Dashboard UI - works as system log collection only
- Ledger automatically saved to `data/ledgers/backtest_{timestamp}.csv` on each run
- Users can access ledger files directly from `data/ledgers/` folder (documented in README.md)
- AI agents or scripts can parse raw CSV/JSON files directly (machine-parseable format, not human-optimized)
- Market-specific ledgers (ASX separate from future USA/TWN implementations)

**Independent Tests**:
```python
def test_transaction_ledger_records_buy():
    ledger = TransactionLedger()
    portfolio = Portfolio(cash=10000)
    
    result = portfolio.buy(ticker="ABB.AX", date="2026-02-06", price=15.25, quantity=50)
    entry = ledger.get_last_entry()
    
    assert entry["action"] == "BUY"
    assert entry["ticker"] == "ABB.AX"
    assert entry["date"] == "2026-02-06(FRI)"
    assert entry["cash_after"] == 9227.55

def test_ledger_clear_overwrites_previous_run():
    ledger = TransactionLedger()
    ledger.add_entry({"date": "2026-02-05", "action": "BUY"})
    
    ledger.clear()  # No archiving, just clear
    assert len(ledger.entries) == 0
    
    # New ledger written to file on next backtest completion
    ledger.save_to_file("data/ledgers/backtest_20260206.csv")
    assert os.path.exists("data/ledgers/backtest_20260206.csv")
```

---

### User Story 5: Human-Readable Date Display with Weekday
**As a** backtesting user reviewing results  
**I want** all dates displayed with weekday names (e.g., 2026-02-06(FRI))  
**So that** I can quickly verify trades occurred on valid trading days and spot weekend/holiday errors

**Acceptance Scenarios**:
```
GIVEN: Backtest completes for ABB.AX (2026-02-01 to 2026-02-28)
WHEN: Dashboard displays "Models Comparison" results table
THEN: Date column shows:
  2026-02-03(MON) | BUY | 50 units @ $15.25
  2026-02-04(TUE) | HOLD | Position maintained
  2026-02-05(WED) | HOLD | Position maintained
  2026-02-06(THU) | SELL | 50 units @ $16.80
  # 2026-02-07(FRI) = Holiday skipped
  2026-02-10(MON) | BUY | 60 units @ $15.10

GIVEN: User opens transaction ledger CSV from data/ledgers/ folder
WHEN: File opened in Excel or text editor
THEN: Date column displays:
  Date,Ticker,Action,Quantity,Price
  2026-02-03(MON),ABB.AX,BUY,50,15.25
  2026-02-04(TUE),ABB.AX,HOLD,50,15.30
  2026-02-06(THU),ABB.AX,SELL,50,16.80

GIVEN: Streamlit dashboard "Time-Span Comparison" mode
WHEN: Results shown for 7-day, 14-day, 30-day strategies
THEN: Equity curve chart X-axis labels:
  2026-01-03(MON), 2026-01-06(THU), 2026-01-09(SUN)...
  # Clear weekday names visible in chart
```

**Format Requirements**:
- ISO date format: YYYY-MM-DD
- 3-letter weekday abbreviation: MON, TUE, WED, THU, FRI, SAT, SUN (uppercase)
- Parentheses wrapping weekday: (FRI)
- No spaces between date and weekday: `2026-02-06(FRI)` NOT `2026-02-06 (FRI)`
- Applied to ALL outputs: Dashboard tables, CSV exports, chart labels, log files

**Independent Tests**:
```python
def test_format_date_with_weekday():
    formatted = format_date_with_weekday(pd.Timestamp("2026-02-06"))
    assert formatted == "2026-02-06(FRI)"
    
    formatted = format_date_with_weekday(pd.Timestamp("2026-12-25"))
    assert formatted == "2026-12-25(FRI)"  # Christmas

def test_parse_date_with_weekday():
    parsed = parse_date_with_weekday("2026-02-06(FRI)")
    assert parsed.date() == pd.Timestamp("2026-02-06").date()
    assert parsed.strftime("%a").upper() == "FRI"

def test_csv_export_includes_weekday():
    ledger = TransactionLedger()
    ledger.add_entry({"date": "2026-02-06", "ticker": "ABB.AX"})
    
    ledger.save_to_file("data/ledgers/test.csv")
    csv_content = open("data/ledgers/test.csv").read()
    assert "2026-02-06(FRI)" in csv_content
```

---

## 2. Requirements

### Functional Requirements

**FR-001: ASX Holiday Calendar Integration**
- System MUST dynamically fetch ASX public holidays based on user-specified backtest date range (no hard-coded year limits)
- Calendar scope determined by `start_date` and `end_date` parameters (e.g., 2020-2030 if user selects 10-year backtest)
- System MUST filter out holidays from historical data BEFORE running backtest simulations
- System MUST treat market half-days (e.g., Christmas Eve) as off-days (no trading allowed)
- System MUST skip trading operations on identified holidays in backtest timeline
- System MUST display holiday names in logs/dashboard when dates are skipped (e.g., "2026-01-26 (Australia Day) excluded")

**FR-002: Weekday Constraint in Backtests**
- System MUST only process Monday-Friday dates in historical backtests (weekday filter)
- System MUST calculate "Day" holding periods in TRADING DAYS (excludes weekends + holidays)
- System MUST calculate "Week/Month/Quarterly/Year" holding periods in CALENDAR DAYS (includes all days)
- System MUST display filtered date ranges showing: "Trading days: X (Y holidays excluded)"
- Dashboard equity curves MUST show only valid trading days on X-axis

**FR-003: Pre-Transaction Portfolio Validation**
- System MUST check simulated portfolio cash balance BEFORE generating BUY signals
- System MUST skip BUY signal generation if insufficient cash for any ticker
- System MUST calculate maximum affordable quantity: `floor(cash / price)` for each ticker
- System MUST allow SELL signals even when cash is depleted (can sell existing positions)
- System MUST log validation results: "2026-02-10: Can afford ABB.AX (max 66 units), SIG.AX (max 18 units)"

**FR-004: Transaction Ledger Persistence**
- System MUST create transaction ledger entry for EVERY simulated trade in backtest
- Ledger format MUST be machine-parseable (CSV, JSON, or similar structured format)
- Human-readable formatting NOT required (AI agents or scripts can parse raw data)
- System MUST clear ledger when user re-runs backtest or changes parameters (no archiving)
- System MUST use memory-efficient approach: keep only minimal state (~2 KB) during backtest, not full ledger
- System MUST automatically save ledger to `data/ledgers/backtest_{timestamp}.csv` on completion via batch write
- Ledger NOT displayed in Dashboard UI - accessible via file system only
- Ledger location documented in README.md for users to access transaction logs

**FR-005: Transaction Ledger Schema**
Required fields for each ledger entry:
- `date` (string): YYYY-MM-DD(DAY) format with weekday
- `ticker` (string): Stock symbol (e.g., ABB.AX)
- `action` (string): BUY, SELL, HOLD
- `quantity` (integer): Number of units transacted
- `price` (decimal): Price per unit at transaction
- `total_value` (decimal): quantity × price
- `commission` (decimal): Transaction fee (CMC Markets or Default profile)
- `cash_before` (decimal): Portfolio cash before transaction
- `cash_after` (decimal): Portfolio cash after transaction
- `positions_before` (dict): All positions before trade
- `positions_after` (dict): All positions after trade
- `strategy` (string): Strategy name (e.g., "consensus-30d", "random_forest-7d")
- `model_votes` (dict): Individual model predictions (for consensus strategies)
- `confidence` (decimal): Signal confidence score (0-1)
- `notes` (string): Optional metadata (e.g., "Stop-loss triggered")

**FR-006: Date Display Standardization**
- ALL date displays MUST use format: `YYYY-MM-DD(DAY)`
- Weekday abbreviation MUST be 3 letters uppercase (MON, TUE, WED, THU, FRI, SAT, SUN)
- Format MUST be applied to:
  - Streamlit dashboard result tables
  - Ledger CSV/JSON files (data/ledgers/ folder)
  - Chart axis labels (Plotly/Matplotlib)
  - Log file entries
  - Terminal debug output

---

### Technical Requirements

**TR-001: Holiday Calendar Data Source**
- Use `pandas_market_calendars` library for ASX trading days (preferred)
- Dynamically fetch holidays for exact date range: `mcal.get_calendar('XASX').schedule(start_date, end_date)`
- Fallback: Static JSON file with extended coverage (e.g., 2015-2035)
- Format: `[{"date": "2026-01-26", "name": "Australia Day"}, ...]`
- Load calendar at backtest initialization, cache in memory for session duration
- No hard-coded year limits - system adapts to user's backtest period

**TR-002: Timezone Handling**
- ALL date operations use Australia/Sydney timezone (AEST/AEDT) via `pandas.tz_localize`
- Historical data from yfinance: Convert to Sydney timezone immediately after fetch
- Date filtering: Use `.dt.dayofweek` (0=Mon, 6=Sun) to exclude weekends
- No timezone conversion needed for display (already AEST/AEDT)

**TR-003: Transaction Ledger Storage**
- **In-Memory (Optimized)**: Keep only minimal state during backtest (~2 KB per active backtest)
  - Portfolio state: cash, positions (~1 KB)
  - Summary metrics: returns, Sharpe, win rate (~500 bytes)
  - Current transaction buffer: 1 transaction (~300 bytes)
  - **NOT storing full ledger in memory** during backtest execution
- **File Output**: Automatically saved to `data/ledgers/backtest_{timestamp}.csv` on backtest completion
- **Batch Write**: Write completed backtest ledger to disk immediately, then clear from memory
- **Format**: CSV or JSON with all FR-005 columns (machine-parseable, not human-optimized)
- **CSV Schema**: Standard pandas CSV with header row (parseable by AI agents, Excel, Python scripts)
- **JSON Schema**: Array of transaction objects with nested positions snapshots
- **No Dashboard Display**: Ledger NOT shown in Streamlit UI - users access via file system
- **File Location**: Document in README.md: "Transaction logs saved to `data/ledgers/` folder"
- **No Database**: Backtest ledger is ephemeral (not persisted to PostgreSQL)

**TR-004: Portfolio State Tracking**
- Use Python class `Portfolio` with methods: `buy()`, `sell()`, `get_state()`
- Track state changes in chronological order (append-only ledger)
- Each transaction updates: `cash`, `positions`, `ledger`
- Snapshot portfolio state BEFORE and AFTER each transaction for audit trail
- Support "what-if" scenarios: Rollback to checkpoint, try different strategy

**TR-005: Performance Optimization**
- Holiday check: Pre-filter dates ONCE at start of backtest (not per-ticker)
  ```python
  trading_days = filter_non_trading_days(date_range, asx_calendar)
  ```
- Portfolio validation: Cache current state, update incrementally per transaction
- **Memory-efficient ledger**: Don't hold full transaction ledger in memory during backtest
  - Keep only: portfolio state (~1 KB), summary metrics (~500 bytes), current transaction buffer (~300 bytes)
  - Peak memory per backtest: ~2 KB (minimal)
- **Batch write strategy**: Write completed backtest ledger to disk, then clear from memory
  - No streaming I/O (too slow) - prefer batch writes after each backtest completes
  - Append to master CSV file: ~630 KB chunks per backtest
- CSV write performance: `pandas.to_csv()` handles <1M rows efficiently

**TR-006: Date Formatting Utility**
```python
def format_date_with_weekday(dt: pd.Timestamp) -> str:
    """
    Format pandas Timestamp as YYYY-MM-DD(DAY)
    
    Args:
        dt: Timestamp object (timezone-aware or naive)
    
    Returns:
        String like "2026-02-06(FRI)"
    """
    weekday = dt.strftime("%a").upper()  # MON, TUE, ...
    return f"{dt.strftime('%Y-%m-%d')}({weekday})"
```
- Centralized in `core/utils.py` (shared across modules)
- Used in: backtest_engine.py, dashboard components, CSV exports
- Supports: `datetime.date`, `datetime.datetime`, `pd.Timestamp`

---

## 3. Success Criteria

### Correctness Criteria
✅ **Holiday Detection**: Backtest correctly excludes all ASX public holidays for user-selected date range (dynamically fetched from pandas_market_calendars, verified against official ASX calendar)

✅ **Zero Weekend Trading**: No transactions logged on Saturday/Sunday across any backtest period

✅ **Capital Validation Accuracy**: Pre-transaction checks prevent 100% of impossible trades (buying stocks with insufficient cash)

✅ **Ledger Completeness**: Every simulated trade has corresponding ledger entry with all FR-005 required fields

✅ **Date Format Consistency**: 100% of date displays in Dashboard, ledger files, and charts use `YYYY-MM-DD(DAY)` format

---

### User Experience Criteria
✅ **Dashboard Clarity**: Backtest results show dates like "2026-02-06(FRI)" with clear weekday visibility

✅ **Ledger File Quality**: Saved ledger files (`data/ledgers/`) open correctly in Excel with readable date format (no epoch timestamps)

✅ **Backtest Feedback**: Dashboard displays summary: "Trading days: 252 (3 holidays excluded, 104 weekends excluded)"

✅ **Holiday Visibility**: When backtest completes, dashboard shows excluded dates with holiday names

✅ **Ledger Access Documentation**: README.md clearly documents ledger file location and how to access transaction logs

---

### Performance Criteria
✅ **Fast Date Filtering**: Holiday/weekend filtering completes in <500ms for 10-year historical data

✅ **Ledger Growth Manageable**: Standard backtest (single stock, 1 model) consumes <2 MB memory for ledger

✅ **File Write Speed**: 10,000-row ledger writes to CSV in <3 seconds

⚠️ **Worst-Case Scenario - Mode 1 (Models Comparison) on ASX 200**:
- **Scenario**: Models Comparison mode for ASX 200 index, 10-year backtest, 1-Day holding period
- **Understanding**: Mode 1 evaluates each model's performance SEPARATELY (not consensus voting)
  - Mode 1: Each model → separate backtest → separate ledger
  - Mode 2/3: Models vote together (consensus) → single ledger

- **Calculations**:
  - 200 stocks × 5 models = **1,000 separate backtests**
  - 10 years × 252 trading days/year = 2,520 trading days
  - 1-Day holding period: potential buy/sell every 2 days
  - Assuming 50% signal generation rate: ~1,260 transactions per backtest
  - **Total transactions**: 1,000 backtests × 1,260 = **1,260,000 transactions**

- **Memory Impact (Optimized Strategy)**:
  - **NOT storing full ledger in memory** during backtest
  - Store only minimal state per active backtest:
    - Portfolio state: cash, positions (~1 KB)
    - Summary metrics: returns, Sharpe ratio, win rate (~500 bytes)
    - Current transaction buffer: 1 transaction × 300 bytes
  - **Peak memory per backtest**: ~2 KB (minimal)
  - **Sequential execution**: Process 1 backtest at a time → **~2 KB active memory**
  - **Batch write strategy**: Write ledger to disk after each backtest completes, then clear from memory

- **Disk Impact**:
  - Each backtest ledger: ~1,260 transactions × 500 bytes/row (CSV) = **~630 KB per file**
  - Output options:
    - **Option A**: 1,000 separate CSV files (e.g., `CBA.AX_random_forest.csv`) = 630 MB total
    - **Option B**: Single master CSV file (all backtests combined) = **600-800 MB file**
  - CSV write: Batch append every backtest completion (~630 KB chunks)

- **Mitigation Strategies**:
  - ✅ Memory-efficient: Keep only portfolio state + summary metrics in RAM (not full ledger)
  - ✅ Batch writes: Write completed backtest to disk immediately, clear from memory
  - ⚠️ No streaming I/O: Batch writes preferred over continuous streaming (better performance)
  - ✅ Disk space check: Require 1GB+ free space before starting Mode 1 on ASX 200
  - ✅ Warning prompt: "This will run 1,000 backtests (~700MB file). Continue?"
  - ✅ Progress indicator: "Processing CBA.AX (50/200 stocks, 25% complete, 250/1000 backtests)"
  - ✅ Partial results: Allow cancellation with partial results saved

---

### Reliability Criteria
✅ **Zero False Positives**: No valid trading days incorrectly marked as holidays/weekends (verified against ASX official calendar)

✅ **File Write Integrity**: Ledger file writes preserve 100% of transaction data (no truncation)

✅ **Portfolio State Consistency**: `cash_after` from transaction N always equals `cash_before` from transaction N+1

✅ **No Data Loss**: Ledger file captures all trades from start to end of backtest (no missing rows when written to disk)

---

## 4. Dependencies and Assumptions

### Dependencies
- **pandas_market_calendars** (Python library): ASX trading day calendar (install: `pip install pandas-market-calendars`)
- **pandas**: Date filtering, timezone handling, DataFrame for ledger storage
- **Streamlit**: Dashboard UI for displaying results and transaction history
- **yfinance**: Historical price data (already used, no changes needed)

### Assumptions
- **ASX Holiday Schedule**: Dynamically fetched from pandas_market_calendars library, scoped to user's backtest date range
- **Daily Backtesting Only**: System simulates daily trades (no intraday/minute-level simulations)
- **Historical Data Available**: yfinance provides complete price data for backtest date range (no gaps)
- **Single Timezone**: All operations in Australia/Sydney timezone (no multi-region support)
- **Ledger Ephemeral**: Transaction ledger exists only during active Streamlit session (not persisted between runs unless exported)

### Risk Factors
⚠️ **Holiday Calendar Outdated**: If pandas_market_calendars library has outdated ASX calendar, backtest may include invalid trading day
- **Mitigation**: Static JSON fallback with manually verified holidays (extended coverage), annual library update check

⚠️ **Timezone DST Transitions**: AEST ↔ AEDT transitions might cause date misalignment (October/April)
- **Mitigation**: Use pandas timezone-aware DatetimeIndex, test across DST boundaries

⚠️ **yfinance Data Gaps**: If historical data missing for certain dates, backtest may fail
- **Mitigation**: Fill forward missing values (`df.ffill()`), log warning when gaps detected

⚠️ **Memory Growth**: Mode 1 (Models Comparison) on large indexes may generate large disk files
- **Worst-case**: ASX 200 × 5 models = 1,000 backtests = ~600-800 MB final CSV file
- **Memory optimized**: Keep only ~2 KB per active backtest in RAM (not full ledger)
- **Mitigation**: Batch write to disk after each backtest completes, 1GB+ disk space check, warn user before starting

---

## 5. Out of Scope (Future Enhancements)

❌ **Real-Time Trading**: This spec focuses on historical backtesting only (not live trading execution)

❌ **Intraday Backtesting**: Minute-level or second-level simulations not supported (daily trades only)

❌ **After-Hours Trading**: ASX pre-market/post-market hours not simulated

❌ **Multi-Currency Support**: Assumes AUD only (no forex conversions for international stocks)

❌ **Fractional Shares**: Ledger assumes whole unit quantities only (no 0.5 shares)

❌ **Tax Loss Harvesting**: No automatic capital gains/loss optimization in backtest

❌ **Portfolio Rebalancing**: No automatic position sizing or allocation adjustment

❌ **Live Market Data**: Backtest uses historical data only (not real-time prices)

❌ **Database Persistence**: Ledger is in-memory/file-based only (no PostgreSQL storage for backtest ledgers)

❌ **Dashboard Ledger Display**: Transaction ledger NOT displayed in Streamlit UI (accessible via file system only at `data/ledgers/`)

❌ **Multi-User Support**: Single-user Streamlit dashboard (no concurrent backtest sessions)

---

**Next Steps**: Create `plan.md` to break down implementation into Work Packages (WP-1, WP-2, etc.)
