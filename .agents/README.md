# 🤖 AI Agent Setup & Documentation Hub

**Start here.** Every AI agent working on this project must read these documents in order.

---

## 📋 Required Reading (In Order)

### 1️⃣ **[SOUL.md](../SOUL.md)** — Philosophy & Core Values
**Read first. This sets the tone.**

- **Data-Driven Objectivity** - Trust data, not intuition
- **Grounded Realism** - Account for fees, taxes, market slippage
- **Radical Transparency** - No black boxes, fully auditable logic
- **Adaptive Flexibility** - Market-agnostic, strategy-agnostic, extensible

**Why**: Ensures every change aligns with project philosophy. Prevents vibe coding.

---

### 2️⃣ **[CONTEXT.md](../CONTEXT.md)** — Shared Domain Language
**Read second. This is how we talk about the system.**

| What | Where |
|------|-------|
| **Domain Concepts** | Strategy, Backtest, Signal, Model, Consensus, Hurdle Rate |
| **State Machines** | Model training, Backtest execution, Performance calculation |
| **Financial Constraints** | Fees, taxes, market slippage, The "Big Three" friction points |
| **Architectural Layers** | Core (logic), UI (presentation), Research (orchestration) |
| **Key Workflows** | Strategy backtesting, model training, performance comparison |
| **Performance Metrics** | ROI, Win Rate, Sharpe Ratio, Max Drawdown, Alpha, Beta |

**Why**: Eliminates jargon confusion. When you see "consensus", you know exactly what it means.

**Pro tip**: If a term isn't in CONTEXT.md, ask the user to clarify or add it.

---

### 3️⃣ **[AGENTS.md](../AGENTS.md)** — AI Workflows & Matt Pocock Skills
**Read third. This is how we work together.**

- **Matt Pocock Skills Framework** - `/grill-with-docs`, `/tdd`, `/to-spec`, `/code-review`
- **Mandatory Workflows** - Feature work, bug fixes, architecture, backtest logic
- **Core Mandates** - Non-negotiable constraints (realistic accounting, no secrets, TDD required)

**Why**: Ensures every feature follows the same discipline. No exceptions.

---

### 4️⃣ **[.claude.md](../.claude.md)** — Claude-Specific Configuration
**Read if you're Claude** (or any Claude-derived agent).

- Hard constraints (never skip tests, never commit secrets, etc.)
- Mandatory workflow (grill → spec → tdd → review → commit)
- Domain language quick reference
- Testing requirements for backtest logic
- Code review checklist

**Why**: Claude gets specific instructions that other agents don't need.

---

## 🎯 Quick Reference by Agent Type

### 👤 **GitHub Copilot**
Start with: SOUL.md → CONTEXT.md → `.github/copilot-instructions.md`

### 🤖 **Claude (Any Variant)**
Start with: SOUL.md → CONTEXT.md → `.claude.md` → AGENTS.md

### 📝 **Cline / OpenCode**
Start with: SOUL.md → CONTEXT.md → `.clinerules` / `opencode/rules.md`

### 🖱️ **Cursor**
Start with: SOUL.md → CONTEXT.md → `.cursorrules`

### 🎓 **Any New Agent**
Follow the [Required Reading](#-required-reading-in-order) order above. It works for everyone.

---

## ⚡ Fastest Onboarding

**If you have 5 minutes:**
1. Read CONTEXT.md (domain language)
2. Skim SOUL.md (philosophy)
3. Ask the user what they want

**If you have 15 minutes:**
1. Read SOUL.md (2 min)
2. Read CONTEXT.md (5 min)
3. Read AGENTS.md → Matt Pocock Skills section (5 min)
4. Ask the user what they want

**If you have 30 minutes:**
1. Read all four documents above
2. Understand testing requirements for backtest logic
3. Review code review checklist in `.claude.md`
4. Ready to work

---

## 🚨 Non-Negotiable Rules

These apply to **every agent, every task**:

1. **Financial Safety**
   - ❌ Never skip TDD for backtest logic
   - ❌ Never commit API keys or secrets
   - ❌ Never skip fee/tax accounting
   - ❌ Never use hardcoded data (use yfinance/Alpaca)

2. **Architectural Boundaries**
   - ❌ Never modify isolated market branches (research-only labs)
   - ❌ Never add code without updating specs first
   - ❌ Never change model interface without updating CONTEXT.md

3. **Code Quality**
   - ❌ Never commit without `/code-review`
   - ❌ Never skip realistic accounting (fees + taxes + slippage)
   - ❌ Never hardcode strategy logic (use config + factory patterns)

**If you're unsure, ask the user. Speculation kills backtesting systems.**

---

## 🔄 Workflows You'll Use

### For New Strategies or Models
```
1. /grill-with-docs  (understand the requirement)
2. /to-spec          (codify acceptance criteria)
3. /tdd              (red → green → refactor)
4. /code-review      (standards + spec check)
5. Commit            (only after approval)
```

### For Performance Bugs
```
1. /diagnosing-bugs  (isolate → hypothesize → fix)
2. /tdd              (regression test)
3. /code-review      (impact assessment)
4. Commit            (only after approval)
```

### For Architecture Questions
```
1. /improve-codebase-architecture  (scan for issues)
2. /domain-modeling                (sharpen terminology)
3. /codebase-design                (deep modules, simple interfaces)
```

---

## 📞 When to Ask the User

✅ **Always ask**:
- "Should I proceed with TDD implementation?"
- "Does this edge case change the fee calculation?"
- "Should I add this as a new model or modify existing consensus logic?"

❌ **Never ask**:
- "Should I write tests?" → Yes, always
- "Should I add type hints?" → Yes, always
- "Should I review the code?" → Yes, always

---

## 🔍 File Map

```
share-investment-strategy-model/
├── SOUL.md                        ← Philosophy (start here)
├── CONTEXT.md                     ← Domain language (read next)
├── AGENTS.md                      ← Workflows + Matt Pocock skills
├── .claude.md                     ← Claude-specific config
├── .agents/
│   └── README.md                  ← THIS FILE (universal entry point)
├── core/
│   ├── config.py                  ← Markets, tickers, fee structures
│   ├── model_builder.py           ← AI models (factory pattern)
│   ├── backtest_engine.py         ← Backtesting logic with fees/taxes
│   └── fee_calculator.py          ← Broker-specific fees
├── ui/
│   ├── app.py                     ← Streamlit dashboard
│   └── components/                ← UI modules
├── app/
│   ├── backtest_runner.py         ← Execute strategy
│   └── consensus_logic.py         ← Multi-model voting
└── data/
    ├── models/                    ← Trained model artifacts
    └── results/                   ← Backtest results cache
```

---

## 🎓 Learning Resources

**Want to understand the system deeper?**

- **How backtesting works** → See `ARCHITECTURE.md` (if exists) + `core/backtest_engine.py`
- **How models work** → See `core/model_builder.py` + factory pattern
- **How consensus voting works** → See `app/consensus_logic.py` + CONTEXT.md § Consensus
- **How fees/taxes are calculated** → See `core/fee_calculator.py` + testing requirements in `.claude.md`
- **How strategies are validated** → See CONTEXT.md § Common Patterns (Debugging a Bad Backtest)

---

## ✅ Before You Start Working

**Checklist for every agent session:**

- [ ] Read SOUL.md (understand philosophy)
- [ ] Read CONTEXT.md (understand terminology)
- [ ] Understand the user's request
- [ ] Run `/grill-with-docs` (align on requirements)
- [ ] Proceed with `/to-spec` → `/tdd` → `/code-review`
- [ ] Ask user for approval before committing

**That's it. Simple, repeatable, effective.**

---

## Questions?

If something is unclear:
1. Check CONTEXT.md first (probably defined there)
2. Check SOUL.md second (probably explained there)
3. Ask the user (they're the authority)

**Golden rule**: When in doubt, ask. Speculation kills backtesting systems.

---

**Last Updated**: August 23, 2026  
**Created by**: GitHub Copilot / Claude Agent Integration  
**Scope**: All AI agents working on share-investment-strategy-model
