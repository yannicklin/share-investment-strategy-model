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
3. **Realistic Accounting**: All calculations must account for the "Big Three" of friction: Fees, Taxes, and Market Slippage.
4. **Algorithmic Pluralism**: Favor ensembles and consensus over single-model dependency to reduce bias. Support multiple algorithms (Random Forest, NGBoost, CatBoost, Prophet, LSTM) via factory pattern.
5. **Cold Visualization**: UI components must present financial data with standardized, honest precision (2-decimal, clear currency/percentage formatting).



6. **Taiwan Market Mandate**:
    - **T+2 Settlement**: Strictly enforce a 2-trading-day delay for cash clearance after a sale for Taiwan market.
    - **Institutional Data**: Prioritize FinMind for Foreign/Trust flows, Margin Trading (RongZi/RongQuan), and Revenue Growth.
    - **Global Context**: Integrate Yahoo Finance for ^SOX, ^IXIC, and TWD=X to capture US-Taiwan correlations.
    - **Price Limits**: Respect the ±10% daily ceiling/floor in all execution simulations.
    - **Fee Realism**: Use localized profiles (Fubon, First) with realistic online trading discounts.

...

## 3. Workflow & Automation Rules (Strict)

1. **Manual Commits Only**: NEVER run `git commit` or `git add` unless the user explicitly requests a commit. Do not assume a successful change implies a checkpoint is wanted.
2. **No Automatic Background Tasks**: NEVER start the dashboard or tests in the background (e.g., `make run &`) automatically after an edit. Wait for the user to request the start.
3. **Respect Local Environment**: Do not attempt to install system-level libraries (e.g., `brew install`). Stick strictly to `requirements.txt` via the local virtual environment.
4. **Code-Only Implementation**: Focus on editing the requested files. Do not chain multiple shell operations (like build or run) unless they are part of a verification step requested by the user.

---
*Last Updated: 2026-02-03 (Hardware Portability & Workflow Safety Updates)*
*Note: This is a living document. Update it as project conventions evolve.*
