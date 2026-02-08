# ASX AI Trading Strategy System (`asx` branch)

A Python-based automated trading strategy system designed specifically for the **Australian Securities Exchange (ASX)**. This system utilizes advanced AI models to predict stock price movements, perform realistic backtesting (accounting for fees, taxes, and price gaps), and provide real-time investment recommendations via a Streamlit dashboard.

## 🚀 Key Features

-   **Multi-Model Support**: Compare performance across 5 different algorithms:
    -   Random Forest, XGBoost, CatBoost (Gradient Boosting)
    -   Prophet (Time-series forecasting)
    -   **LSTM (Deep Learning / Sequential Memory)**
-   **Realistic Backtesting Engine**:
    -   **Tax-Aware Dynamic Hurdle Rate**: AI signals are filtered through a "break-even + buffer" check that accounts for fees, market slippage, and your personal ATO tax bracket.
    -   **Fee Profiles**: Supports `Default`, **`CMC Markets`** ($11 min), and **`Tiger AU`** ($4 min) structures.
    -   **ATO Taxation**: Implements 2024-25 Individual Tax Brackets with a 50% CGT discount for holdings $\ge$ 12 months, calculated based on your annual income.
    -   **Market Calendar Compliance**: Automatically excludes ASX holidays and weekends (dynamically fetched for backtest date range). Market half-days treated as off-days.
    -   **Transaction Ledger**: Records every trade in machine-parseable format, saved to `data/ledgers/` folder (not shown in Dashboard).
    -   **Portfolio Validation**: Pre-checks available cash before generating signals (skips ML execution if insufficient capital).
    -   **Market Constraints**: Enforces stop-loss rules and minimum holding periods.
    -   **Price Gaps**: Handles scenarios where stop-loss cannot be executed at the exact threshold due to market gaps.
-   **Global Market Intelligence**: Incorporates **S&P 500**, **VIX**, **Gold**, **Oil**, and **AUD/USD** data to understand market sentiment and macro drivers (with strict T-1 shifting to prevent look-ahead bias).
-   **Data Integration**: Seamlessly fetches historical and real-time data from Yahoo Finance (`yfinance`).
-   **Interactive Dashboard**: A built-in Streamlit UI featuring a **Segmented Selection Switch** for:
-   **Models Comparison**: Benchmark 5 AI models for a specific fixed strategy.
-   **Time-Span Comparison**: Compare ROI across different holding periods using model consensus with a custom **Tie-Breaker** rule.
-   **Super Stars Scanner**: Scan entire market indices (**ASX 50**, **ASX 200**) to find the top 10 most profitable stocks using consensus logic.
-   **Realized Equity Curves**: Visual tracking of capital growth connecting trade exit points.
-   **Daily Recommendations**: AI-generated signals with consensus scoring.
-   **Input Validation**: Real-time ticker validation against Yahoo Finance — automatically removes invalid tickers before analysis with user warnings.
-   **Performance Metrics**: Track Net ROI, Win Rate, and Total Trades with standardized **2-decimal precision** (numeral.js format).
-   **T+2 Settlement Logic**: Simulates strict ASX realism where capital from a sale is locked for 2 trading days before becoming available for reinvestment.

## 🛠️ Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd share-investment-strategy-model
    git checkout asx  # Switch to the ASX-specific branch
    ```

> **Note**: This repository uses a branch-per-market structure. Ensure you are on the `asx` branch for the Australian market implementation. Other branches like `usa` is for different research tracks.

2.  **Using `uv` (Recommended)**:
    This project is optimized for `uv`. Install dependencies and run in one go:
    ```bash
    uv run streamlit run ASX_AImodel.py
    ```

3.  **Manual Installation**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

## 💻 Usage

### Streamlit Dashboard
Launch the interactive dashboard to configure parameters, run backtests, and view AI recommendations:
```bash
uv run streamlit run ASX_AImodel.py
```

### GitHub Codespaces (Cloud Development)
This project includes a devcontainer configuration for GitHub Codespaces:
- **Pre-configured**: Debian base + Python 3.12 + UV + SSH
- **Automatic setup**: Dependencies installed on container creation
- **SSH access**: Enabled via `gh codespace ssh`

Simply open the repository in GitHub Codespaces to start developing immediately.

## 🧪 Testing

Run the test suite to verify core functionality and integration:

```bash
# Run all tests
make test

# Or manually with pytest
uv run pytest tests/

# Run specific test file
uv run pytest tests/test_integration.py

# Run with verbose output
uv run pytest tests/ -v

# Run security scans (Trivy & Semgrep)
make scan
```

**Test Coverage**:
- **`test_core.py`**: Unit tests for model builder and backtest engine
- **`test_integration.py`**: Integration tests for trading constraints, market calendar, and transaction ledger

## 📂 Project Structure

-   **`core/`**:
    -   `config.py`: Global settings and defaults (Tickers, Capital, ATO Tax).
    -   `model_builder.py`: AI model factory (RF, XGB, CatBoost, Prophet, LSTM).
    -   `backtest_engine.py`: Dual-mode simulation logic with consensus voting, market calendar compliance, transaction ledger, and portfolio validation.
    -   `index_manager.py`: Reliable constituent fetcher for market indices.
-   **`ui/`**:
    -   `sidebar.py`: Navigation and parameter inputs.
    -   `algo_view.py`: AI Benchmarking dashboard.
    -   `strategy_view.py`: Strategy Sensitivity (Consensus) dashboard.
    -   `stars_view.py`: Index-wide "Super Stars" ranking view.
    -   `components.py`: Shared UI elements (Realized Equity Curve, formatted logs).
-   `ASX_AImodel.py`: Main Streamlit application entry point.

-   `tests/`: Unit and integration tests for core logic.
    -   `test_core.py`: Unit tests for model builder and backtest engine.
    -   `test_integration.py`: Integration tests for trading constraints and ledger.
-   **`data/`**: Data directory.
    -   `models/`: Trained AI models (.joblib, .h5 files).
    -   `ledgers/`: Transaction logs for completed backtests (see below).
    -   `downloads/`: Cached market data.

## 📊 Transaction Ledger Access

Every backtest automatically generates a **transaction ledger** (audit trail) saved to the `data/ledgers/` folder. These files are **not displayed in the Dashboard** but can be accessed directly for analysis.

### File Location & Naming
-   **Directory**: `data/ledgers/`
-   **File Format**: CSV (machine-parseable, optimized for AI agents/scripts)
-   **Naming Convention**: `backtest_{timestamp}.csv` (e.g., `backtest_2026-02-06_143022.csv`)

### Ledger Contents
Each transaction includes:
-   Date (YYYY-MM-DD(DAY) format with weekday)
-   Ticker, Action (BUY/SELL/HOLD), Quantity, Price
-   Commission, Cash Before/After
-   Portfolio positions snapshot

### Memory & Performance
-   **Memory-Optimized**: System keeps only ~2 KB active memory per backtest (not full ledger).
-   **Batch Writes**: Ledger written to disk after each backtest completes, then cleared from memory.
-   **Worst-Case** (Mode 1 on ASX 200): 1,000 backtests = ~600-800 MB total disk output.

### Mode-Specific Generation
-   **Mode 1 (Models Comparison)**: Each model → separate ledger file for performance evaluation.
-   **Mode 2/3 (Time-Span/Super Stars)**: Models vote as consensus team → single ledger per test.

### Accessing Ledger Files
```bash
# View ledger files
ls -lh data/ledgers/

# Open in Excel or text editor
open data/ledgers/backtest_2026-02-06_143022.csv

# Parse with Python/pandas
import pandas as pd
ledger = pd.read_csv("data/ledgers/backtest_2026-02-06_143022.csv")
```

---

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

### License & Copyright

**Copyright**: (c) 2026 Yannick  
**License**: MIT License (see [LICENSE](LICENSE))  
**Attribution**: All source code files include copyright headers per `CODE_HEADERS.md`

**Current Attribution Status**: 100% coverage (13/13 Python files)

---

*Last Updated: February 6, 2026*  
*Developed for ASX Trading Analysis*
