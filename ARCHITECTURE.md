# System Architecture - AI Trading System

> **Complete technical reference** covering system design, multi-market architecture, and bot implementation status.

## Table of Contents

1. [Program Objective](#1-program-objective)
2. [Program Modules](#2-program-modules)
3. [Data Sources](#3-data-sources)
4. [Bot Database Isolation](#4-bot-database-isolation-critical)
5. [Reinvestment & Settlement](#5-reinvestment--settlement)
6. [Automation & Deployment](#6-automation--deployment)
7. [Testing](#7-testing)
8. [Bot Implementation Status](#8-bot-implementation-status)

---

## 📱 Recent Updates (February 2026)

### LINE Messaging API Integration Support
The system now supports **LINE Messaging API** as an additional notification channel, alongside Telegram and SMS.
- **Market Relevance**: LINE has 90%+ penetration in Taiwan, 80%+ in Japan, 90%+ in Thailand.
- **Cost**: FREE for up to 500 messages/month.
- **Implementation**: Multi-channel support (telegram, line, sms, or combinations).

### Admin Authentication System
- Phone-based verification via Telegram/LINE/SMS.
- Admin whitelist management UI at `/admin/whitelist`.
- Per-admin notification preferences.

---

## 1. Program Objective

Develop a Python-based stock trading strategy system using AI models trained on **historical stock data** to:
- Train AI models on market-specific data.
- Backtest historical performance.
- Generate buy/sell recommendations with strict risk management.
- Handle real-world scenarios (price gaps, stop-loss execution).

### Multi-Market Development Workflow (Critical)

This project uses a "Lab-to-Production" workflow across branches:

1.  **Market-Specific Branches (`asx`, `usa`, `twn`) — The "Labs"**:
    - **Purpose**: Evaluation, parameter testing, and model benchmarking.
    - **Logic**: Contains market-specific `core/config.py` and evaluation UIs.
    - **Goal**: Find the most profitable parameters (hurdle rates, indicators, algorithmic mix).

2.  **Unified `bots` Branch — The "Production"**:
    - **Purpose**: Automated execution and notification.
    - **Logic**: Ported (copied) wisdom from the Labs.
    - **Mandate**: When a strategy is proven in a market branch, its parameters and specialized logic must be explicitly ported into `app/bot/markets/{market}/config.py` and `signal_service.py`.

---

## 2. Program Modules

### 2.1 Architecture Overview
The system follows a **hybrid multi-market architecture**:

#### SHARED Components (Universal)
- **Database Schema** (`app/bot/shared/models.py`): Single source of truth with market isolation.
- **ML Algorithms** (`core/`): Universal logic works for any ticker.
- **Notification Services** (`app/bot/shared/notification_service.py`): Multi-channel support.

#### SEPARATE Components (Market-specific)
- **Signal Generation** (`app/bot/markets/{market}/signal_service.py`): Market-specific validation.
- **Configuration** (`app/bot/markets/{market}/config.py`): Trading hours, ticker suffix, holidays.

### 2.2 Core Modules (`core/`)
- **`config.py`**: Centralized configuration management.
- **`model_builder.py`**: AI factory supporting Random Forest, Gradient Boosting, CatBoost, Prophet, and LSTM.
- **`backtest_engine.py`**: Dual-mode simulation engine with 90-day warm-up buffer.

### 2.3 Bot Service Architecture (`app/bot/`)
Bot code lives in the `bots` branch but supports multiple markets through database isolation.

---

## 3. Data Sources

Exclusively uses **Yahoo Finance (`yfinance`)** for historical and real-time data.

| Market | Ticker Format | Example | Trading Hours |
|--------|--------------|---------|---------------|
| **ASX** | `{SYMBOL}.AX` | `BHP.AX` | 10:00-16:00 AEST |
| **USA** | `{SYMBOL}` | `AAPL` | 09:30-16:00 EST |
| **TWN** | `{SYMBOL}.TW` | `2330.TW` | 09:00-13:30 CST |

---

## 4. Bot Database Isolation (Critical)

### Query Safety Pattern
Always use the `.for_market()` helper to ensure ASX/USA/TWN data never mix.

```python
# ✅ CORRECT - Only ASX signals
signals = Signal.for_market('ASX').all()

# ❌ WRONG - Returns data from ALL markets mixed
signals = Signal.query.all()
```

### Database Constraints
Enforced via `UniqueConstraint('market', 'date', 'ticker')` to prevent duplicate signals per market.

---

## 5. Reinvestment & Settlement
- **Settlement Logic**: T+1 reinvestment cycle (capital available next business day after sale).
- **Signal-Driven Entry**: Reinvestment occurs when AI Consensus triggers a "BUY" exceeding the Hurdle Rate.

---

## 6. Automation & Deployment

### GitHub Actions
Scheduled workflows trigger signal generation for each market:
- **ASX**: 08:00 AEST (`cron: '0 22 * * 0-4'`)
- **USA**: 06:00 EST (`cron: '0 10 * * 1-5'`)
- **TWN**: 07:00 CST (`cron: '0 23 * * 0-4'`)

### Storage Organization
Backups and models are organized by market folder in Cloudflare R2:
- `models/ASX/`, `models/USA/`, `models/TWN/`
- `backups/ASX/`, etc.

---

## 7. Testing
- **Unit Tests**: Core logic, model builder, backtest engine.
- **Integration Tests**: Signal generation, idempotency, market isolation.

---

## 8. Bot Implementation Status

### ✅ Completed Components
- **Flask Framework**: Factory pattern, market-aware blueprints.
- **Database Schema**: All 4 tables (signals, config_profiles, api_credentials, job_logs) with isolation.
- **Idempotency Logic**: Dual-trigger reliability (08:00 + 10:00 AEST).
- **Admin Authentication**: Phone-based verification system.
- **Notification Engine**: Telegram and LINE integration.

### 🔧 Pending / TODOs
- **AI Consensus Integration**: Connect `core/model_builder.py` to `signal_service.py`.
- **Production Notification Deployment**: Finalize SendGrid/Telnyx credentials.
- **Backup Service**: Implement automated AES-256 encrypted backups to R2.

---
*Last Updated: February 6, 2026*
