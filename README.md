# AI-Based Trading Strategy Model (USA Edition)

A clinical research framework for the objective analysis of algorithmic trading in the **US Stock Market (NYSE, NASDAQ)**. This project is not a "trading bot"—it is an infrastructure designed to bridge the gap between theoretical AI signals and the reality of market costs.

## 🎯 The Philosophy

The identity of this model is defined by **Grounded Realism**. While many AI systems focus solely on price prediction accuracy, this framework prioritizes **Net Profitability**. It treats transaction fees, taxes (including foreign investor implications), and slippage as primary variables, not afterthoughts.

## 🚀 Getting Started

### Prerequisites
- Python 3.10, 3.11, or 3.12 (Recommended)
- macOS (Apple Silicon supported natively)

### Quick Start
This project includes a robust setup script and Makefile for easy management.

```bash
# 1. Setup Environment & Install Dependencies
make setup

# 2. Run the Dashboard
make run
```

Alternatively, you can run the setup script directly:
```bash
./setup.sh
source .venv/bin/activate
streamlit run main.py
```

## 🏛️ Core Pillars

- **The Clinical Filter**: Removing emotional bias through data-driven multi-model consensus.
- **The Hurdle Layer**: Enforcing financial sanity by requiring signals to exceed a "Tax-Aware Hurdle Rate."
- **The Factory Interface**: A modular standard for integrating diverse machine learning algorithms (Random Forest, LSTM, GBDT).
- **Auditability**: Every decision, fee, and tax calculation is transparent and auditable.
- **Sample Weighting Strategies**: Two sample weighting modes for model training:
    - **Normal (Uniform)**: All historical samples weighted equally (default, matches traditional ML approach).
    - **Recency Weighted**: Exponential decay favoring recent data with dynamic half-life = backtest_years / 2. Recent market conditions influence model more heavily.

## 📂 Structural Identity

This repository serves as the fundamental DNA of the project:

- **[SOUL.md](SOUL.md)**: The core personalities and values that drive all development.
- **[AGENTS.md](AGENTS.md)**: Rigorous mandates and structural directives for development.
- **[AUTHORS.md](AUTHORS.md)**: Authorship, credits, and the moral contract for contributors.
- **[CODE_HEADERS.md](CODE_HEADERS.md)**: Standards for clinical code attribution and integrity.
- **[LICENSE](LICENSE)**: MIT License.

## ⚠️ Disclaimer

This framework is for educational and research purposes only. It is a research tool, not financial advice. All financial research carries the risk of total capital loss.

---

**Copyright**: (c) 2026 Yannick  
**License**: MIT License
