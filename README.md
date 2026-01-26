# ASX AI Trading Strategy System

A Python-based automated trading strategy system designed specifically for the **Australian Securities Exchange (ASX)**. This system utilizes advanced AI models to predict stock price movements, perform realistic backtesting (accounting for fees, taxes, and price gaps), and provide real-time investment recommendations via a Streamlit dashboard.

## 🚀 Key Features

-   **Multi-Model Support**: Compare performance across 5 different algorithms:
    -   Random Forest, XGBoost, CatBoost (Gradient Boosting)
    -   Prophet (Time-series forecasting)
    -   **LSTM (Deep Learning / Sequential Memory)**
-   **Realistic Backtesting Engine**:
    -   **Fee Profiles**: Supports `Default` (Percentage-based + Clearing) and **`CMC Markets`** ($11 min or 0.10%) structures.
    -   **ATO Taxation**: Implements 2024-25 Individual Tax Brackets with a 50% CGT discount for holdings $\ge$ 12 months, calculated based on your annual income.
    -   **Market Constraints**: Enforces stop-loss rules and minimum holding periods.
    -   **Price Gaps**: Handles scenarios where stop-loss cannot be executed at the exact threshold due to market gaps.
-   **Data Integration**: Seamlessly fetches historical and real-time data from Yahoo Finance (`yfinance`).
-   **Interactive Dashboard**: A built-in Streamlit UI featuring a **Segmented Selection Switch** for:
    -   **Models Comparison**: Benchmark 5 AI models for a specific fixed strategy.
    -   **Time-Span Comparison**: Compare ROI across different holding periods using model consensus with a custom **Tie-Breaker** rule.
    -   **Realized Equity Curves**: Visual tracking of capital growth connecting trade exit points.
    -   **Daily Recommendations**: AI-generated signals with consensus scoring.
-   **Performance Metrics**: Track Net ROI, Gross ROI, Win Rate, and **Average Profit per Trade**.
-   **Feature Engineering**: Includes technical indicators like RSI, MACD, and Moving Averages.
-   **Customizable Scaling**: Supports both `StandardScaler` and `RobustScaler` for data preprocessing.

## 🛠️ Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd share-investment-strategy-model
    ```

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## 💻 Usage

### Streamlit Dashboard (Recommended)
Launch the interactive dashboard to configure parameters, run backtests, and view AI recommendations:
```bash
streamlit run ASX_AImodel.py
```

### Command Line Interface
Run the main pipeline (training and backtesting) for tickers specified in `config.py`:
```bash
python ASX_AImodel.py
```

## 🧪 Testing

The project uses `pytest` for unit testing. To run the tests:
```bash
pytest
```

## ⚙️ Configuration

System parameters can be adjusted in `config.py` or directly via the Streamlit sidebar:
-   `target_stock_code`: ASX tickers (e.g., `BHP.AX`, `CBA.AX`).
-   `init_capital`: Starting investment amount.
-   `stop_loss_threshold`: Percentage drop to trigger a safety exit.
-   `hold_period_unit`/`value`: Minimum duration to hold a position before non-safety exits.
-   `scaler_type`: Choose between `standard` or `robust` scaling.

## 📂 Project Structure

-   **`core/`**:
    -   `config.py`: Global settings and defaults (Tickers, Capital, ATO Tax).
    -   `model_builder.py`: AI model factory (RF, XGB, CatBoost, Prophet, LSTM).
    -   `backtest_engine.py`: Dual-mode simulation logic.
-   **`ui/`**:
    -   `sidebar.py`: Navigation and parameter inputs.
    -   `algo_view.py`: AI Benchmarking dashboard.
    -   `strategy_view.py`: Strategy Sensitivity (Consensus) dashboard.
    -   `components.py`: Shared UI elements (Realized Equity Curve, formatted logs).
-   `ASX_AImodel.py`: Main Streamlit application entry point.
-   `tests/`: Unit tests for core logic.
-   `models/`: Directory for persistent model storage.

## ⚠️ Disclaimer

This software is for educational and research purposes only. It is **not** financial advice. Trading stocks involves significant risk of loss. Always perform your own due diligence and consult with a licensed financial advisor before making any investment decisions. The developers of this system are not responsible for any financial losses incurred through its use.

---
*Developed for ASX Trading Analysis.*
