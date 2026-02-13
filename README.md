# AI-Based Trading Strategy Model

A clinical research framework for the objective analysis of algorithmic trading. This project is not a "trading bot"—it is an infrastructure designed to bridge the gap between theoretical AI signals and the harsh reality of market friction.

## 🎯 The Philosophy

The identity of this model is defined by **Grounded Realism**. While many AI systems focus solely on price prediction accuracy, this framework prioritizes **Net Profitability**. It treats transaction fees, slippage, and taxation as primary variables, not afterthoughts.

## 🏛️ Core Pillars

- **The Clinical Filter**: Removing emotional bias through data-driven multi-model consensus.
- **The Hurdle Layer**: Enforcing financial sanity by requiring signals to exceed a "Tax-Aware Hurdle Rate."
- **The Factory Interface**: A modular standard for integrating diverse machine learning algorithms (Random Forest, LSTM, GBDT).
- **Auditability**: Every decision, fee, and tax calculation is transparent and auditable.

## 📂 Structural Identity

This repository serves as the fundamental DNA of the project:

- **[SOUL.md](SOUL.md)**: The core personalities and values that drive all development.
- **[AGENTS.md](AGENTS.md)**: Rigorous mandates and structural directives for development.
- **[AUTHORS.md](AUTHORS.md)**: Authorship, credits, and the moral contract for contributors.
- **[CODE_HEADERS.md](CODE_HEADERS.md)**: Standards for clinical code attribution and integrity.
- **[LICENSE](LICENSE)**: MIT License.

## ⚠️ Disclaimer

This framework is for educational and research purposes only. It is a research tool, not financial advice. All financial research carries the risk of total capital loss.

## 🇹🇼 Taiwan Market Infrastructure (TWN Branch Only)

This branch includes specialized logic for the Taiwan (TWSE/TPEx) market:

- **Real-Time Index Synchronization**: The "Find Super Stars" mode supports live constituent synchronization from authoritative sources via the sidebar sync button:
    - **台股50 (Taiwan 50)**: (Online sync pending formal API stabilization).
    - **台股中型100 (Mid 100)**: (Online sync pending formal API stabilization).
    - **MSCI台股指數 (MSCI Taiwan)**: (Online sync pending formal API stabilization).
- **Broker Profiles**: Localized fee structures with realistic online trading discounts for **富邦證券 (Fubon)** and **第一金證券 (First Securities)**.
- **Realistic Friction**: Automatic enforcement of the 0.3% Securities Transaction Tax (STT), T+2 settlement delays, and the daily ±10% price limit.
- **Institutional Metadata**: Integrated support for FinMind data (Institutional flows, Margin trading, and Revenue) alongside Yahoo Finance price data.

---

**Copyright**: (c) 2026 Yannick  
**License**: MIT License
