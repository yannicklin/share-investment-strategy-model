# AI Trading Bot System (Multi-Market Architecture)

A Python-based automated trading strategy system supporting multiple global markets with two operational modes:

## 🎯 Two-Mode Architecture

### **Mode 1: Analysis Dashboard** (Branch-Based)
Interactive Streamlit UI for manual backtesting and strategy analysis.
- **Switch Branches**: `git checkout asx` / `git checkout usa` / `git checkout twn`
- **Market-Specific**: Each branch has optimized configs for that market
- **Use Case**: Research, backtesting, strategy development

### **Mode 2: Bot Service** (Unified - This Branch: `bots`)
Flask-based automation service for scheduled signal generation across ALL markets.
- **Multi-Market Support**: ASX, USA, TWN in single codebase
- **Database Isolation**: `.for_market('ASX')` ensures data never mixes
- **Deployment**: Koyeb (compute) + Supabase (database) + Cloudflare R2 (backups)
- **Use Case**: Production automated trading signals

> **When coding bot features**: Reference individual market branches (`asx`/`usa`/`twn`) for market-specific configurations (trading hours, ticker suffixes, holidays).

## 🌍 Supported Markets

| Branch | Market | Ticker Suffix | Bot Status | Analysis Status |
|--------|--------|---------------|------------|----------------|
| `asx` | Australian Securities Exchange | `.AX` | ✅ Ready | ✅ Ready |
| `usa` | NYSE/NASDAQ | None | 📋 Planned | 📋 Planned |
| `twn` | Taiwan Stock Exchange | `.TW` | 📋 Planned | 📋 Planned |

## 🏗️ Deployment Architecture

**Production Stack** ($0.22/month):
- **Compute**: Koyeb eSmall (Singapore, auto-stop)
- **Database**: Supabase PostgreSQL Free (always-on, 500MB)
- **Storage**: Cloudflare R2 (backups, 10GB free)
- **DNS**: Cloudflare (subdomain delegation: `money.twoudia.com`)
- **CI/CD**: GitHub Actions (daily signal triggers)

See [CLOUD_PRICING_COMPARISON.md](CLOUD_PRICING_COMPARISON.md) for full architecture details.

## 🚀 Key Features

-   **Multi-Model Support**: Compare performance across 5 different algorithms:
    -   Random Forest, XGBoost, CatBoost (Gradient Boosting)
    -   Prophet (Time-series forecasting)
    -   **LSTM (Deep Learning / Sequential Memory)**
-   **Realistic Backtesting Engine**:
    -   **Tax-Aware Dynamic Hurdle Rate**: AI signals are filtered through a "break-even + buffer" check that accounts for fees, market slippage, and your personal ATO tax bracket.
    -   **Fee Profiles**: Supports `Default` (Percentage-based + Clearing) and **`CMC Markets`** ($11 min or 0.10%) structures.
    -   **ATO Taxation**: Implements 2024-25 Individual Tax Brackets with a 50% CGT discount for holdings $\ge$ 12 months, calculated based on your annual income.
    -   **Market Constraints**: Enforces stop-loss rules and minimum holding periods.
    -   **Price Gaps**: Handles scenarios where stop-loss cannot be executed at the exact threshold due to market gaps.
-   **Data Integration**: Seamlessly fetches historical and real-time data from Yahoo Finance (`yfinance`).
-   **Interactive Dashboard**: A built-in Streamlit UI featuring a **Segmented Selection Switch** for:
    -   **Models Comparison**: Benchmark 5 AI models for a specific fixed strategy.
    -   **Time-Span Comparison**: Compare ROI across different holding periods using model consensus with a custom **Tie-Breaker** rule.
    -   **Super Stars Scanner**: Scan entire market indices (**ASX 50**, **ASX 200**) to find the top 10 most profitable stocks using consensus logic.
    -   **Realized Equity Curves**: Visual tracking of capital growth connecting trade exit points.
    -   **Daily Recommendations**: AI-generated signals with consensus scoring.
-   **Input Validation**: Real-time ticker validation against Yahoo Finance — automatically removes invalid tickers before analysis with user warnings.
-   **Performance Metrics**: Track Net ROI, Win Rate, and Total Trades with standardized **2-decimal precision** (numeral.js format).
-   **T+1 Reinvestment Logic**: Simulates realistic brokerage cash flow where capital from a sale is available for the next trading day.

## 🛠️ Local Development

### 1. Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials (DATABASE_URL, TELEGRAM_BOT_TOKEN, etc.)
```

### 3. Run Locally
```bash
python run_bot.py
```

### 4. Run Tests
```bash
pytest tests/bot/ -v
```

## 🏗️ Deployment
Refer to **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** for step-by-step production setup on Koyeb.

## 📂 Project Structure

### **Analysis Mode** (Market-Specific Branches)
```
share-investment-strategy-model/ (asx/usa/twn branch)
├── core/                    # ML algorithms & backtesting
│   ├── config.py           # Market-specific settings
│   ├── model_builder.py    # AI models (RF, XGB, LSTM, etc.)
│   └── backtest_engine.py  # Simulation engine
├── ui/                      # Streamlit dashboard
│   ├── sidebar.py
│   ├── algo_view.py        # AI benchmarking
│   └── strategy_view.py    # Strategy comparison
└── ASX_AImodel.py          # Entry point
```

### **Bot Service** (This Branch - Multi-Market)
```
share-investment-strategy-model/ (bot branch)
├── app/bot/
│   ├── shared/
│   │   ├── models.py           # DB schema with market isolation
│   │   └── notification.py     # Telegram/LINE/Email/SMS sender
│   ├── markets/
│   │   ├── asx/               # ASX signal generation
│   │   │   ├── config.py      # Import from asx branch
│   │   │   └── signal_service.py
│   │   ├── usa/               # USA signal generation
│   │   └── twn/               # TWN signal generation
│   └── api/
│       └── cron_routes.py     # /cron/daily-signals?market=ASX
├── core/                      # Shared ML algorithms
└── run_bot.py                 # Bot entry point
```

> **Key Pattern**: Bot references market configs from individual branches but runs unified database.

### Bot Framework Status
**Current State**: Framework complete, core logic pending
- ✅ Flask app structure (`app/bot/`)
- ✅ Database models (signals, profiles, credentials, job_logs)
- ✅ Idempotent signal generation logic
- ✅ GitHub Actions workflows (dual-trigger reliability)
- ✅ Test suite (5 comprehensive tests)
- ✅ Admin authentication system with phone-based verification
- ✅ Multi-channel notifications (Telegram/LINE/SMS support)
- ⏸️ **Pending**: AI consensus integration, production notification deployment, backup service

See [ARCHITECTURE.md](ARCHITECTURE.md#bot-implementation-status) for detailed setup guide and TODOs.

## ⚠️ Disclaimer

This software is for educational and research purposes only. It is **not** financial advice. Trading stocks involves significant risk of loss. Always perform your own due diligence and consult with a licensed financial advisor before making any investment decisions. The developers of this system are not responsible for any financial losses incurred through its use.

---

## 📚 Attribution & Project Documentation

### Core Documentation
- **[SOUL.md](SOUL.md)** - Project philosophy, values, and architectural principles
- **[AUTHORS.md](AUTHORS.md)** - Contributors, acknowledgments, and technology credits
- **[CODE_HEADERS.md](CODE_HEADERS.md)** - Code attribution templates and current status

### AI Assistant Development
- **[AGENTS.md](AGENTS.md)** - Comprehensive AI development guidelines
- **[.cursorrules](.cursorrules)** - Cursor AI configuration
- **[.clinerules](.clinerules)** - Cline AI configuration
- **[.aiderignore](.aiderignore)** - Aider AI configuration

### Technical Documentation
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Complete system architecture, multi-market design, and bot implementation status
- **[AGENTS.md](AGENTS.md)** - AI agent development guidelines
- **[bot_trading_system_requirements.md](bot_trading_system_requirements.md)** - Original bot requirements (reference)

### License & Copyright

**Copyright**: (c) 2026 Yannick  
**License**: MIT License (see [LICENSE](LICENSE))  
**Attribution**: All source code files include copyright headers per `CODE_HEADERS.md`

**Current Attribution Status**: 100% coverage (13/13 Python files)

---

*Last Updated: February 5, 2026*  
*Multi-Market Trading System (ASX Production Ready)*
