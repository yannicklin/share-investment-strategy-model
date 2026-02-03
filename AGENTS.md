# AGENTS.md: Framework Directives

## 🎯 **CRITICAL: Align with SOUL.md**

Every modification to this codebase must be a reflection of the core personalities defined in **[SOUL.md](SOUL.md)**. If a proposed change compromises **Realism**, **Objectivity**, or **Transparency**, it must be rejected.

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
4. **Algorithmic Pluralism**: Favor ensembles and consensus over single-model dependency to reduce bias.
5. **Cold Visualization**: UI components must present financial data with standardized, honest precision (2-decimal, clear currency/percentage formatting).



...

## 3. Workflow & Automation Rules (Strict)

1. **Manual Commits Only**: NEVER run `git commit` or `git add` unless the user explicitly requests a commit. Do not assume a successful change implies a checkpoint is wanted.
2. **No Automatic Background Tasks**: NEVER start the dashboard or tests in the background (e.g., `make run &`) automatically after an edit. Wait for the user to request the start.
3. **Respect Local Environment**: Do not attempt to install system-level libraries (e.g., `brew install`). Stick strictly to `requirements.txt` via the local virtual environment.
4. **Code-Only Implementation**: Focus on editing the requested files. Do not chain multiple shell operations (like build or run) unless they are part of a verification step requested by the user.

---
*Last Updated: 2026-02-03 (Hardware Portability & Workflow Safety Updates)*
*Note: This is a living document. Update it as project conventions evolve.*
