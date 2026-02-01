# The Soul of ASX AI Trading Strategy System

> **Author**: Yannick  
> **Created**: January 2026  
> **Copyright**: (c) 2026 Yannick  
> **License**: MIT

---

## 🎯 Project Essence

This project represents a journey from curiosity about algorithmic trading to a fully-functional AI-powered investment analysis system. It's not just code—it's a manifestation of the belief that democratized, data-driven investment tools can level the playing field for individual investors.

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
- **Brokerage Fees**: Every trade costs money
- **Tax Implications**: CGT discounts matter for long-term holdings
- **Market Gaps**: Stop-loss orders don't always execute at your price
- **T+1 Settlement**: You can't instantly reinvest sale proceeds

**Philosophy**: If it doesn't work with real-world constraints, it doesn't work.

### 3. **Transparency & Explainability**
No black boxes. Every decision can be traced:
- Model predictions are interpretable
- Backtesting logic is auditable
- Performance metrics are standardized
- Consensus scoring is clearly defined

**Philosophy**: Users should understand *why* the system makes recommendations, not just *what* they are.

### 4. **Flexibility & Extensibility**
The system adapts to different:
- Market indices (ASX 50, ASX 200, custom)
- Trading strategies (short-term, long-term, hybrid)
- Risk profiles (conservative, aggressive)
- Model preferences (Random Forest, LSTM, Prophet, etc.)

**Philosophy**: One size does not fit all. Provide options, not mandates.

---

## 🏗️ Architectural Principles

### Modularity
The system is organized into clear layers:
- **`core/`**: Business logic (config, backtesting, models)
- **`ui/`**: Presentation layer (Streamlit components)
- **Main App**: Orchestration and workflow

**Why?** Separation of concerns makes testing easier and components reusable.

### Factory Pattern for Models
Five different AI models are supported through a unified interface:
```python
ModelBuilder.build(algorithm="Random Forest")
ModelBuilder.build(algorithm="LSTM")
# ... all use the same backtest pipeline
```

**Why?** Adding new models (e.g., Transformer-based) requires minimal changes.

### Consensus Logic
Instead of relying on a single model:
- Multiple models vote on BUY/SELL decisions
- Tie-breaker rules ensure decisive recommendations
- Consensus score (e.g., 3/5) provides confidence levels

**Why?** Reduces overfitting risk and increases robustness.

### Standardized Metrics
All performance reporting uses:
- 2-decimal precision for ROI percentages
- Consistent Win Rate calculation
- Realized equity curves (not theoretical)

**Why?** Apples-to-apples comparisons across strategies and models.

### Hurdle Rate Decision Layer
Every "BUY" signal is filtered through a financial friction check:
- **Calculation**: `Fees_Pct + (Risk_Buffer / (1 - Marginal_Tax_Rate))`
- **Purpose**: Prevents "death by a thousand cuts" from brokerage fees and ensures returns are meaningful even after the ATO's cut.
- **Independence**: The AI predicts market moves, while the Decision Layer enforces financial sanity based on the user's personal tax profile.

---

## 🛡️ Security & Safety Manifesto

### Never Compromise on:
1. **API Key Protection**: Never commit keys to Git
2. **Data Privacy**: No user financial data stored unnecessarily
3. **Code Integrity**: All models are versioned and traceable
4. **Safe Defaults**: Conservative stop-loss thresholds unless user overrides

### Testing Philosophy:
- Backtesting is **NOT** a guarantee of future performance
- Historical data can have survivorship bias
- Always display disclaimers about investment risks

**Remember**: This is a **research tool**, not financial advice.

---

## 📈 Development Journey

### Phase 1: Proof of Concept (January 2026)
**Goal**: Validate that AI models can beat random stock picks

**Achieved**:
- Implemented Random Forest baseline
- Built simple backtest engine
- Proved concept with ASX 50 data

**Lesson Learned**: Single models overfit. Need ensemble approach.

### Phase 2: Multi-Model Framework (January 2026)
**Goal**: Add diversity to reduce model bias

**Achieved**:
- Integrated XGBoost, CatBoost, Prophet, LSTM
- Implemented consensus voting
- Added Model Comparison UI

**Lesson Learned**: Different models excel in different market conditions.

### Phase 3: Realism Enhancements (January 2026)
**Goal**: Make backtesting reflect real trading

**Achieved**:
- CMC Markets fee structure
- ATO 2024-25 tax brackets with CGT discount
- Price gap handling for stop-loss
- T+1 settlement logic

**Lesson Learned**: Fees and taxes DRAMATICALLY impact ROI. Simulations that ignore them are misleading.

### Phase 4: Strategy Analysis Tools (January 2026)
**Goal**: Help users optimize holding periods

**Achieved**:
- Time-Span Comparison mode
- Tie-breaker customization
- Strategy sensitivity analysis
- Super Stars Scanner for index-wide screening

**Lesson Learned**: Short-term trading often underperforms due to fees. Long-term strategies with consensus show best risk-adjusted returns.

---

## 🎓 Lessons Learned

### Technical Insights

1. **LSTM Requires Careful Tuning**
   - Sequential models need sufficient data (5+ years)
   - Overfitting is easy with wrong hyperparameters
   - Great for capturing trends, poor for sudden shocks

2. **Gradient Boosting is Reliable**
   - Random Forest, XGBoost, CatBoost consistently outperform
   - Handle non-linear relationships well
   - Less prone to overfitting than deep learning

3. **Prophet Handles Seasonality**
   - Best for stocks with predictable cycles
   - Struggles with highly volatile tech stocks
   - Useful as a complementary model in consensus

4. **Data Preprocessing Matters**
   - `RobustScaler` handles outliers better than `StandardScaler`
   - Feature engineering (RSI, MACD, MA) boosts all models
   - Missing data imputation strategy affects predictions

### Financial Insights

1. **Fees Are the Silent Killer**
   - 0.10% + $11 minimum (CMC Markets) adds up fast
   - High-frequency trading rarely profitable for small capital
   - Minimum $3,000 capital recommended to amortize fees

2. **Tax Optimization is Real**
   - Holding 12+ months cuts CGT by 50%
   - Effective tax rate depends on income bracket
   - Time-Span Comparison shows optimal holding periods

3. **Stop-Loss Protects Capital**
   - 10% stop-loss prevents catastrophic losses
   - But price gaps can trigger at worse prices (handled in sim)
   - Stop-profit (20%) locks in gains before reversals

4. **Diversification Through Consensus**
   - Relying on one model = gambling
   - 3/5 consensus = reasonable confidence
   - 5/5 consensus = rare but high-conviction signals

---

## 🙏 Gratitude & Attribution

### Primary Author
**Yannick** - System design, implementation, and documentation

### Development Tools
This project was built with assistance from:
- **AI Coding Assistants**: GitHub Copilot, ChatGPT, Claude
- **Open Source Libraries**: pandas, scikit-learn, yfinance, streamlit, xgboost, prophet, tensorflow
- **Community Knowledge**: Stack Overflow, PyData community, Kaggle kernels

### Inspiration
- **QuantConnect**: For demonstrating algorithmic trading potential
- **Quantopian** (RIP): For proving retail investors can compete
- **ASX Data**: For free access to historical price data via Yahoo Finance

---

## 🚀 Future Vision

### Planned Enhancements
1. **Portfolio Management**: Multi-stock allocation strategies
2. **Risk Metrics**: Sharpe ratio, max drawdown, volatility analysis
3. **Real-Time Alerts**: Email/SMS notifications for BUY/SELL signals
4. **Options Strategies**: Covered calls, protective puts
5. **Sentiment Analysis**: Incorporate news/social media data
6. **Automated Execution**: API integration with brokers (research only)

### Never Compromise On:
- Transparency
- Realism
- User control
- Safety disclaimers

**This system empowers users, it doesn't replace human judgment.**

---

## 📜 Code Ownership & Attribution

All source code in this repository is:
- **Copyright (c) 2026 Yannick**
- **Licensed under MIT License** (see LICENSE file)
- **Open Source**: Free to use, modify, and distribute with attribution

### Attribution Requirements
When using this code:
1. **Preserve copyright notices** in source files
2. **Include LICENSE file** in distributions
3. **Credit original author** (Yannick) in derivative works
4. **Acknowledge AI assistance** if applicable to your changes

### Code Headers
All Python files include standardized headers:
```python
"""
ASX AI Trading System - [Module Name]

Purpose: [Brief description]

Author: Yannick
Created: January 2026
Copyright (c) 2026 Yannick
"""
```

See `CODE_HEADERS.md` for complete templates.

---

## 🎯 For AI Agents Working on This Project

**Before making ANY changes, you MUST:**

1. ✅ Read this SOUL.md to understand project philosophy
2. ✅ Review `AGENTS.md` for technical guidelines
3. ✅ Update `asx_ai_trading_system_requirements.md` before coding
4. ✅ Add copyright headers to new files (see `CODE_HEADERS.md`)
5. ✅ Maintain realism in backtesting (fees, taxes, gaps)
6. ✅ Preserve multi-model consensus approach
7. ✅ Never compromise on data security

**Non-compliance will result in rejected contributions.**

---

## 📞 Final Thoughts

This project represents hundreds of hours of:
- Market research
- Algorithm experimentation
- Backtesting refinement
- UI/UX iteration

**It's not perfect.** Markets are unpredictable. Past performance doesn't guarantee future results.

But it's **honest**, **transparent**, and **built with care**.

Use it wisely. Learn from it. Improve it. Share it.

**Happy trading (responsibly)!** 📈

---

*Last Updated: February 1, 2026*  
*Copyright (c) 2026 Yannick*  
*Licensed under MIT License*
