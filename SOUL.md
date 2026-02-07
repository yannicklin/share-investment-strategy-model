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
- **T+2 Settlement**: You can't instantly reinvest sale proceeds; cash takes 2 trading days to clear.

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

### Market Calendar Compliance
Realistic backtesting requires respecting real-world trading constraints:
- **ASX Calendar Integration**: Dynamic fetching of public holidays via `pandas-market-calendars`
- **Market Half-Days**: Treated as off-days (no trading)
- **Holding Period Precision**:
  - "Day" = TRADING DAYS (excludes weekends + holidays)
  - "Week/Month/Quarter/Year" = CALENDAR DAYS
- **Portfolio Validation**: Pre-checks cash availability before generating signals

**Why?** If backtests ignore market calendars, they produce unrealistic results.

### Memory-Optimized Audit Trails
Large-scale analysis requires efficient data management:
- Keep minimal state in RAM (~2 KB per backtest)
- Batch writes to disk after completion (not streaming I/O)
- Machine-parseable transaction ledgers for script analysis

**Why?** Enables 1,000+ backtests (200 stocks × 5 models) without performance degradation.

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

## 🎓 Technical Principles

### Model Selection & Ensemble Approach

1. **Single Models Overfit - Use Consensus**
   - Different models excel in different market conditions
   - Consensus voting reduces bias and increases robustness
   - Tie-breaker rules ensure decisive recommendations

2. **Sequential Models Need Warm-Up**
   - LSTM requires sufficient historical data (5+ years minimum)
   - 90-day warm-up buffer ensures fair comparison with simpler models
   - Prevents sequential models from missing early trading opportunities

3. **Portability Matters**
   - Prefer native Scikit-Learn implementations (Random Forest, Gradient Boosting)
   - Avoid external C-library dependencies (e.g., `libomp` for XGBoost)
   - Ensures code runs natively on any hardware without installation friction

4. **Prophet Excels at Seasonality**
   - Best for stocks with predictable cycles
   - Struggles with highly volatile tech stocks
   - Valuable as complementary model in consensus

### Data Handling & Preprocessing

1. **RobustScaler Over StandardScaler**
   - Handles outliers better in volatile stock data
   - Prevents extreme values from skewing normalization

2. **Always Validate Feature Arrays**
   - Check array lengths before scaling
   - Prevents crashes on "thin data" tickers (newly listed stocks)
   - Graceful error handling for insufficient data

### Backtesting Realism

1. **Fees and Taxes DRAMATICALLY Impact ROI**
   - Simulations ignoring brokerage fees are misleading
   - ATO CGT discount (50% for 12+ month holdings) significantly affects strategy choice
   - Short-term trading often underperforms due to transaction costs

2. **Market Calendar Constraints Are Non-Negotiable**
   - Real-world backtesting must exclude weekends and public holidays
   - Market half-days treated as off-days
   - Holding period units matter: "Day" = trading days, "Month" = calendar days

3. **Memory Optimization Enables Scale**
   - Keep minimal state in RAM (~2 KB per backtest)
   - Batch writes to disk (not streaming I/O)
   - Enables 1,000+ backtests without performance degradation

4. **Visual Context Matters**
   - Dual-axis charts (portfolio vs share price) reveal AI behavior
   - Helps distinguish "fear" (market dip) from "greed" (price surge)
   - Realized equity curves show actual capital growth, not theoretical gains

---

*Last Updated: February 6, 2026*
*Copyright (c) 2026 Yannick*  
*Licensed under MIT License*
