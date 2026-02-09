# The Soul of USA AI Trading Strategy System

> **Author**: Yannick  
> **Created**: January 2026  
> **Copyright**: (c) 2026 Yannick  
> **License**: MIT

---

## 🎯 Project Essence

This model is a manifestation of the belief that individual investors deserve access to professional-grade, data-driven analysis tools. It is designed to be a cold, objective filter for the emotional chaos of the stock market—providing a grounded framework for research and strategy validation for the United States markets.

---

## 💡 Core Values

### 1. **Data-Driven Decision Making**
Markets are emotional. This system is not. Every recommendation is backed by:
- Historical backtesting with realistic constraints
- Multi-model consensus to reduce bias
- Transparent performance metrics

**Philosophy**: Trust data, not intuition. Let algorithms find patterns humans miss.

### 2. **Realism Over Fantasy**
Many trading simulators ignore the harsh realities of:
- **Brokerage Fees**: Every trade costs money.
- **Tax Implications**: W-8BEN treaty benefits and backup withholding matter.
- **Market Gaps**: Stop-loss orders don't always execute at your price.
- **T+1 Settlement**: Standard US settlement cycle where funds clear next business day.

**Philosophy**: If it doesn't work with real-world constraints, it doesn't work.

### 3. **Transparency & Explainability**
No black boxes. Every decision can be traced:
- Model predictions are interpretable.
- Backtesting logic is auditable.
- Performance metrics are standardized.
- Consensus scoring is clearly defined.

**Philosophy**: Users should understand *why* the system makes recommendations, not just *what* they are.

### 4. **Flexibility & Extensibility**
The system adapts to different:
- Market indices (S&P 500, Nasdaq 100, custom).
- Trading strategies (short-term, long-term, hybrid).
- Risk profiles (conservative, aggressive).
- Model preferences (Random Forest, NGBoost, CatBoost, etc.).

**Philosophy**: One size does not fit all. Provide options, not mandates.

---

## 🏗️ Architectural Principles

### Modularity
The system is organized into clear layers:
- **`core/`**: Business logic (config, backtesting, models).
- **`ui/`**: Presentation layer (Streamlit components).
- **Main App**: Orchestration and workflow.

**Why?** Separation of concerns makes testing easier and components reusable.

### Factory Pattern for Models
Multiple AI models are supported through a unified interface:
- **NGBoost**: Natural Gradient Boosting for cross-platform stability.
- **CatBoost**: High-performance gradient boosting.
- **LSTM**: Deep learning for sequential patterns.
- **Prophet**: Time-series forecasting for seasonal trends.

**Why?** Adding new models requires minimal changes to the core engine.

### Consensus Logic
Instead of relying on a single model:
- Multiple models vote on BUY/SELL decisions.
- Tie-breaker rules ensure decisive recommendations.
- Consensus scoring provides confidence levels.

**Why?** Reduces overfitting risk and increases robustness.

### Hurdle Rate Decision Layer
Every "BUY" signal is filtered through a financial friction check:
- **Calculation**: `Fees_Pct + Risk_Buffer`
- **Purpose**: Prevents over-trading where fees would erode the majority of potential profits.

---

## 🛡️ Security & Safety Manifesto

### Never Compromise on:
1. **API Key Protection**: Never commit keys to Git.
2. **Data Privacy**: No user financial data stored unnecessarily.
3. **Code Integrity**: All models are versioned and traceable.
4. **Safe Defaults**: Conservative stop-loss thresholds unless user overrides.

### Testing Philosophy:
- Backtesting is **NOT** a guarantee of future performance.
- Historical data can have survivorship bias.
- Always display disclaimers about investment risks.

**Remember**: This is a **research tool**, not financial advice.

---

## 📜 Code Ownership & Attribution

All source code in this repository is:
- **Copyright (c) 2026 Yannick**
- **Licensed under MIT License** (see LICENSE file)
- **Open Source**: Free to use, modify, and distribute with attribution

### Attribution Requirements
When using this code:
1. **Preserve copyright notices** in source files.
2. **Include LICENSE file** in distributions.
3. **Credit original author** (Yannick) in derivative works.

---

*Last Updated: February 9, 2026*
*Copyright (c) 2026 Yannick*  
*Licensed under MIT License*
