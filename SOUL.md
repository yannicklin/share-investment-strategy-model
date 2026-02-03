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

### Phase 5: Reliability & Visual Intelligence (February 2026)
**Goal**: Enhance system portability, visual context, and backtest accuracy.

**Achieved**:
- Replaced XGBoost with native Scikit-Learn **Gradient Boosting** for better hardware portability (Apple Silicon).
- Implemented **90-day Warm-up Buffer** for fair comparison across all model types.
- Added **Dual-Axis Visualization** (Portfolio vs. Share Price Trend) to all equity curves.
- Integrated **Automatic ETF/Security Identification** labeling.
- Enhanced Super Stars mode with **Yahoo Finance Links** and full company names.
- Graceful error handling for stocks with insufficient data (e.g., new listings).

**Lesson Learned**: A trading system must be as portable as it is accurate. Visualizing the underlying asset price trend alongside capital performance provides critical context for understanding AI "fear" vs "greed."

---

## 🎓 Lessons Learned

### Technical Insights

1. **LSTM Requires Careful Tuning & Warm-up**
   - Sequential models need sufficient data (5+ years)
   - **Crucial**: Sequential models must be "primed" with a warm-up buffer (90 days) to ensure they can trade from the very first day of a backtest alongside simpler models.

2. **Gradient Boosting is Reliable & Portable**
   - Random Forest and Gradient Boosting (Scikit-Learn) provide the best mix of stability and performance.
   - Avoiding external C-library dependencies (like `libomp` for XGBoost) ensures the code runs natively on any hardware without local installation friction.

3. **Prophet Handles Seasonality**
   - Best for stocks with predictable cycles
   - Struggles with highly volatile tech stocks
   - Useful as a complementary model in consensus

4. **Data Preprocessing Matters**
   - `RobustScaler` handles outliers better than `StandardScaler`.
   - **Safety First**: Always validate feature array lengths before scaling to prevent crashes on "thin data" tickers.

---

*Last Updated: February 3, 2026*
*Copyright (c) 2026 Yannick*  
*Licensed under MIT License*
