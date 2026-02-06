# AI-Based Stock Investment System Requirements (BOT Automation Version - ASX Market)

## 1. Program Objective
Develop a **fully automated, bot-ready** stock trading intelligence system designed for **scheduled execution, agent orchestration, and zero-human-interaction operation** on the **Australian Securities Exchange (ASX)**. Unlike the interactive analysis versions built for human exploration, this branch focuses on:

- **Daily Automated Recommendations**: Generate BUY/HOLD/SELL signals at scheduled intervals
- **Cloud-Ready Execution**: Deployable as cron jobs, AWS Lambda, Google Cloud Functions, or Kubernetes CronJobs
- **Agent Bot Integration**: Provide machine-readable outputs for consumption by trading bots (e.g., OpenClaw agents)
- **Configuration Management**: Simple, version-controlled task definitions and parameter updates
- **Performance Tracking**: Automated logging and dashboard for suggestion accuracy and portfolio health
- **Future Auto-Trading**: Foundation for fully autonomous trade execution via broker APIs

**Key Principle**: This system operates as a "recommendation engine" that feeds downstream automation systems, NOT a human-facing analysis tool.

### 1.1 Operational Threads (3 Independent Services)

**Thread 1: Daily Signal Generation (Cron Job - DUAL TRIGGER RELIABILITY)**
```yaml
Schedule: 
  - First attempt:  08:00 AEST weekdays (GitHub Actions cron)
  - Second attempt: 10:00 AEST weekdays (reliability backup)
Duration: ~30 minutes (first run), ~5 seconds (second run if already complete)
Resources: 1GB RAM shared machine, 1 vCPU
RAM Usage: ~470MB peak (47% utilization)
Outputs:
  - BUY/SELL/HOLD signals → PostgreSQL
  - Email/SMS/Telegram/LINE alerts → SendGrid/Telnyx/LINE Messaging API
  - JSON webhook → OpenClaw (if connected)
Idempotency: YES (database checks prevent duplicate signals/notifications)
Auto-Suspend: Yes (after job completes)
Cost: ~0.5 hours/day × 20 = 10 hours/month (first runs)
      + 5 sec/day × 20 = 1.7 min/month (second runs)
      = ~10 hours/month × $0.01 = $0.10/month
Reliability: 99.9%+ (catches GitHub Actions failures, cold start timeouts)
```

**Thread 2: Web UI (On-Demand Access)**
```yaml
Access: User-initiated (visit URL)
Cold Start Mechanism: AUTOMATIC (no CLI commands needed)
  - Visit https://asx-bot.fly.dev in browser
  - Fly.io proxy detects machine is suspended
  - Proxy wakes machine automatically (boots in 10-20 seconds)
  - Flask/Streamlit app starts and serves UI
  - No manual intervention required
Cold Start Duration: 10-20 seconds (acceptable for admin dashboard)
Resources: 1GB RAM shared machine, 1 vCPU
RAM Usage: ~280MB peak (28% utilization)
Features:
  - Configuration editor (DATABASE-backed profiles, risk params)
  - Log viewer (job execution history)
  - Performance dashboard (charts, metrics)
  - Manual signal trigger ("Run now" button)
  - Backup management (view/restore Tigris backups)
Auto-Suspend: Yes (after 5 min idle, machine shuts down automatically)
Cost: ~1 hour/week × 4 = 4 hours/month × $0.01 = $0.04/month

How it works:
  1. User visits URL → Fly.io proxy intercepts request
  2. If machine suspended → Proxy queues request + boots machine
  3. Machine starts → Flask app initializes (10-20 sec)
  4. Request forwarded to app → UI rendered
  5. User idle for 5 min → Machine auto-suspends (saves $0.01/hour)

No CLI commands needed! Just visit the URL like any website.

Note: Configurations stored in PostgreSQL (SENSITIVE DATA)
      - Trading profiles, hurdle rates, position sizes
      - Broker API credentials, notification keys
      - Model hyperparameters, risk thresholds
      - Weekly encrypted backups to Tigris (AES-256)
```

**Thread 3: Weekly Model Retraining + Database Backup (Cron Job)**
```yaml
Schedule: Saturday 02:00 AEST (model retraining)
          Saturday 04:00 AEST (database backup, after retraining completes)
Duration: ~2 hours (retraining) + ~5 minutes (backup)
Resources: 1GB RAM shared machine, 1 vCPU (same machine as Threads 1 & 2)
RAM Usage: ~800MB peak (80% utilization - adequate with 20% safety margin)
Process:
  1. Fetch 2 years ASX data (yfinance)
  2. Train 5 models SEQUENTIALLY (RF, XGB, CatBoost, Prophet, LSTM)
  3. Champion/Challenger evaluation
  4. Save best models → Tigris Object Storage (Fly.io integrated)
  5. Export all database tables → JSON (encrypted AES-256)
  6. Upload backup to Tigris (backups/db-YYYYMMDD.json.gz.enc)
  7. Auto-delete backups older than 4 weeks (keep 4 versions = 1 month)
Auto-Suspend: Yes (after all tasks complete)
Cost: ~2 hours/week × 4 = 8 hours/month × $0.01 = $0.08/month

Note: Sequential training keeps RAM under 1GB (LSTM = largest at ~800MB)
Backup includes: Portfolio, signals (30 days), configs (SENSITIVE), job logs
```

**Why 3 Threads (Not One Monolith)?**
- **Cost Optimization**: Auto-suspend saves 96% on compute costs
  - 24/7 monolith: 720 hours/month × $0.01 = $7.20
  - 3 auto-suspend threads: 22 hours/month × $0.01 = $0.22 ✅
    * Thread 1 (dual triggers): 10 hours/month
    * Thread 2 (on-demand UI): 4 hours/month
    * Thread 3 (weekly retrain): 8 hours/month
- **Resource Efficiency**: All 3 threads run on same 1GB machine (80% peak utilization)
- **Fault Isolation**: If retraining crashes, daily signals unaffected (separate cron triggers)
- **Independent Scheduling**: Each thread wakes only when needed (cron/HTTP trigger)
- **Pay-Per-Second Billing**: Only charged when machine is RUNNING, not SUSPENDED
- **Reliability Enhancement**: Dual triggers (08:00 + 10:00) ensure 99.9%+ signal delivery
- **Backup Integration**: Weekly database exports to Tigris (encrypted, 4-week retention)

---

## 2. System Architecture

### 2.1 Core Modules (`core/`)

#### 2.1.1 Scheduler Engine (`scheduler.py`)
- **Purpose**: Orchestrates daily/hourly recommendation generation
- **Features**:
  - Cron-compatible job definitions (e.g., "Run every weekday at 08:00 TST")
  - Task queue management (Redis/Celery for distributed execution)
  - Retry logic with exponential backoff
  - Job lock mechanism to prevent overlapping executions
  - Health check endpoints for monitoring

#### 2.1.2 Signal Generator (`signal_engine.py`)
- **Purpose**: Produces actionable trading signals using AI consensus
- **Outputs**:
  - **Signal Type**: BUY / HOLD / SELL
  - **Confidence Score**: 0.0 to 1.0 (based on model consensus strength)
  - **Target Price**: Predicted optimal entry/exit point
  - **Risk Rating**: LOW / MEDIUM / HIGH
  - **Reasoning**: JSON metadata explaining the decision (features that triggered the signal)
- **Decision Logic**:
  - Multi-model consensus (same as interactive version)
  - Hurdle rate filtering (fee + tax-aware profitability threshold)
  - Risk-adjusted position sizing recommendations
- **Idempotent Execution (CRITICAL ENHANCEMENT)**:
  ```python
  # Dual daily trigger flow (08:00 + 10:00 AEST)
  def generate_daily_signals():
      today = date.today()
      
      # STEP 1: Check if signal already calculated today
      existing_signal = db.query(
          "SELECT * FROM signals WHERE date = %s AND job_type = 'daily'",
          (today,)
      )
      
      if not existing_signal:
          # First trigger: Calculate signal (30 min job)
          signal = run_ai_consensus(tickers, models)
          db.insert("signals", signal)  # Store result
      else:
          # Second trigger: Already done, exit in 5 seconds
          signal = existing_signal
      
      # STEP 2: Check if notification already sent today
      if not signal.sent_at:
          # Send email/SMS (first time only)
          send_notifications(signal)
          db.update("signals", {"sent_at": now()}, where={"date": today})
      
      return {"already_calculated": bool(existing_signal),
              "already_sent": bool(signal.sent_at)}
  ```
  - **Benefits**: No duplicate signals, no duplicate notifications
  - **Reliability**: Second trigger catches failures (GitHub Actions queue delays, cold start timeouts)
  - **Cost**: Second trigger costs ~$0.00001 when work already done (5 sec exit)

#### 2.1.3 Portfolio Tracker (`portfolio_engine.py`)
- **Purpose**: Maintains virtual/real portfolio state across executions
- **Features**:
  - Position tracking (entry price, quantity, current P&L)
  - Realized vs. unrealized gains
  - Trade history with timestamps
  - Performance metrics (Sharpe ratio, max drawdown, win rate)
  - Persistent storage (PostgreSQL/MongoDB for production, SQLite for local)

#### 2.1.4 Configuration Manager (`config_loader.py`)
- **Purpose**: Centralized configuration system with DATABASE storage for sensitive data
- **Storage Architecture**:
  - **Database (PostgreSQL)**: SENSITIVE configurations (PRIMARY storage)
    * Trading profiles (stocks, holding periods, hurdle rates)
    * Broker API credentials (tokens, secrets)
    * Model hyperparameters (algorithm selection, parameters)
    * Risk limits (position sizes, stop-losses, capital allocation)
    * Notification settings (email/SMS/Telegram/LINE credentials)
  - **Git YAML (Read-Only)**: Non-sensitive defaults and documentation
    * Default profile templates
    * Fee structure reference tables
    * Example configurations
- **Security Features**:
  - AES-256 encrypted weekly backups to Tigris
  - 4-week retention (4 backup versions)
  - Restore via Flask endpoint `/admin/backup/restore`
- **Hot Reload**: Database config changes take effect immediately (no deployment needed)
- **Web UI Editing**: Thread 2 provides admin interface for config management

#### 2.1.5 Profile Manager (`profile_manager.py`) - **CRITICAL NEW MODULE**
- **Purpose**: Manage multiple trading strategies with different parameters
- **Profile Definition**:
  ```yaml
  # profiles.yaml example
  profiles:
    - id: "swing-trading"
      name: "Short-Term Swing (1 Week)"
      stocks: ["BHP.AX", "RIO.AX", "FMG.AX"]  # Mining stocks
      holding_period: 7  # days
      hurdle_rate: 0.02  # 2% minimum return
      max_position_size: 5000  # AUD
      rebalance_frequency: "daily"
      
    - id: "dividend-growth"
      name: "Dividend Growth (1 Month)"
      stocks: ["CBA.AX", "WBC.AX", "NAB.AX", "ANZ.AX"]  # Banks
      holding_period: 30  # days
      hurdle_rate: 0.015  # 1.5% (lower due to dividends)
      max_position_size: 10000  # AUD
      rebalance_frequency: "weekly"
      consider_franking: true  # ASX-specific
      
    - id: "aggressive-tech"
      name: "Tech Growth (1 Month, High Risk)"
      stocks: ["APT.AX", "XRO.AX", "WTC.AX"]  # Tech stocks
      holding_period: 30  # days
      hurdle_rate: 0.05  # 5% higher threshold
      max_position_size: 3000  # AUD (smaller due to risk)
      rebalance_frequency: "daily"
      stop_loss: 0.08  # Tighter 8% stop-loss
  ```

- **Features**:
  - **Independent Signal Generation**: Each profile runs its own AI consensus
  - **Isolated Performance Tracking**: Separate P&L, Sharpe ratio, win rate per profile
  - **Custom Risk Parameters**: Different hurdle rates, position sizes, stop-losses
  - **Flexible Rebalancing**: Daily, weekly, or event-driven (e.g., earnings release)
  - **Profile-Specific Models**: Optionally use different AI algorithms per strategy
    - Example: Use LSTM for volatile tech stocks, Random Forest for stable dividends

- **Daily Execution Flow**:
  ```python
  # Pseudo-code for profile-based signal generation
  for profile in load_profiles():
      for ticker in profile.stocks:
          # Fetch data
          data = fetch_market_data(ticker, lookback=90)
          
          # Generate signal using profile's parameters
          signal = generate_signal(
              ticker=ticker,
              data=data,
              holding_period=profile.holding_period,
              hurdle_rate=profile.hurdle_rate,
              models=profile.models  # Can override global models
          )
          
          # Filter by confidence and hurdle
          if signal.confidence > 0.6 and signal.expected_return > profile.hurdle_rate:
              publish_signal(profile_id=profile.id, signal=signal)
              log_to_db(profile.id, ticker, signal)
  ```

- **Why Profiles Matter**:
  1. **Risk Diversification**: Don't put all stocks in one strategy basket
  2. **Holding Period Optimization**: Short-term momentum ≠ long-term value
  3. **Tax Efficiency**: Profiles approaching 12-month CGT discount can be flagged
  4. **Psychological Safety**: Test aggressive strategies with small capital allocation
  5. **Performance Comparison**: A/B test which strategy performs best

### 2.2 Automation Modules (`automation/`)

#### 2.2.1 Notification Service (`notifier.py`)
- **Purpose**: Deliver signals to external systems
- **Channels**:
  - **Email**: Daily summary reports with signal table (SendGrid)
  - **SMS**: Critical alerts via SMS (Twilio/Telnyx - paid)
  - **Telegram Bot**: Mobile push notifications with trade buttons (FREE unlimited)
  - **LINE Messaging API**: Asia-Pacific push notifications (FREE 500/month, popular in Taiwan 90%+ penetration)
  - **Slack/Discord Webhooks**: Real-time alerts for HIGH confidence signals
  - **REST API**: JSON endpoint for agent consumption
  - **Message Queue**: Publish to Kafka/RabbitMQ for event-driven systems

**Multi-Channel Support**:
- Supports simultaneous delivery (e.g., `telegram+line`, `all`)
- Graceful fallback if primary channel fails
- Per-admin notification preferences (database-driven)
- Cost-optimized: Telegram (FREE) + LINE (FREE <500 msg) for most users

#### 2.2.2 Data Fetcher (`data_pipeline.py`)
- **Purpose**: Automated daily data updates
- **Features**:
  - Fetch latest OHLCV from Yahoo Finance (Taiwan .TW/.TWO tickers)
  - Download institutional flow data from TWSE open data platform
  - Cache management with TTL expiration
  - Data quality validation (missing data detection, anomaly flagging)
  - Historical data gap filling

#### 2.2.3 Model Retraining Pipeline (`retrainer.py`)
- **Purpose**: Continuously improve AI models to adapt to market regime changes

**Automated Retraining Workflow**:
```yaml
Schedule:
  - Daily: Incremental update (append new day's data, no retrain)
  - Weekly: Full retrain if performance degraded >5%
  - Monthly: Mandatory retrain + hyperparameter tuning
  
Triggers (Auto-Retrain Events):
  - Accuracy drops below 55% win rate (7-day rolling)
  - 3 consecutive days of losses exceeding hurdle rate
  - Major market event detected (e.g., ASX200 drops >3% in 1 day)
  - New quarter starts (earnings season data refresh)
  
Retrain Process:
  1. Fetch latest data (last 2 years OHLCV + indicators)
  2. Split: 70% train, 15% validation, 15% test
  3. Train 5 models in parallel (RF, XGB, CatBoost, Prophet, LSTM)
  4. Evaluate on test set (Sharpe ratio, win rate, max drawdown)
  5. Champion/Challenger comparison:
     - If new model Sharpe ratio > current + 10% → promote to production
     - Else → keep current model, log challenger performance
  6. Shadow mode: Run new model for 1 week (generate signals but don't act)
  7. If shadow signals outperform → swap models
  
Model Versioning:
  - All models saved to S3 with timestamp: `models/rf_v20260204_083015.pkl`
  - Git-tag config file: `models.yaml` committed with version hash
  - Rollback command: `bot rollback --model-version v20260201`
  
Monitoring:
  - Track model drift (feature distribution changes)
  - Log prediction confidence over time (detect degradation)
  - Alert if model file size changes >50% (potential corruption)
```

**Key Insight**: Models retrain automatically, but YOU approve production deployment via dashboard (safety gate)

### 2.3 UI Dashboard Modules (`ui_bot/`)

#### 2.3.1 Performance Dashboard (`performance_view.py`)
- **Metrics Display**:
  - Portfolio equity curve (realized + unrealized)
  - Individual stock performance leaderboard
  - Signal accuracy tracking (% of profitable BUY signals)
  - Model contribution analysis (which models are most accurate)
  - Risk metrics (VaR, beta, correlation matrix)
- **Time Filters**: 1D / 1W / 1M / 3M / YTD / All Time

#### 2.3.2 Job Execution Log (`job_log_view.py`)
- **Log Details**:
  - Execution timestamp and duration
  - Stocks analyzed and signals generated
  - Data quality issues encountered
  - Error stack traces (if job failed)
  - Resource usage (CPU/memory/API quota consumption)
- **Search & Filter**: By date, ticker, signal type, success/failure status
- **Export**: Download logs as CSV/JSON for auditing

#### 2.3.3 Configuration Editor (`config_editor_view.py`)
- **Features**:
  - Web-based YAML editor with syntax highlighting
  - Validation before save (prevent invalid config)
  - Git integration (commit changes with message)
  - Diff view (compare current vs. previous versions)
  - One-click rollback to last working config

#### 2.3.4 Signal Inspector (`signal_detail_view.py`)
- **Per-Signal Breakdown**:
  - Feature values that led to the decision
  - Individual model votes (Random Forest: BUY, LSTM: HOLD, etc.)
  - Confidence score calculation breakdown
  - Historical performance of similar signals
  - Clickable "Approve for Trading" button (for semi-auto mode)

---

## 2.4 Data Storage & Backup Strategy

### 2.4.1 PostgreSQL Schema (Supabase FREE 500MB)

**Table: `signals`** (Daily signal archive)
```sql
CREATE TABLE signals (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    signal VARCHAR(10) NOT NULL,  -- BUY/SELL/HOLD
    confidence FLOAT NOT NULL,     -- 0.0 to 1.0
    job_type VARCHAR(20) NOT NULL, -- 'daily' or 'on-demand'
    created_at TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,             -- NULL if notifications not sent yet
    UNIQUE(date, ticker, job_type) -- Prevent duplicate signals
);
CREATE INDEX idx_signals_date ON signals(date DESC);
CREATE INDEX idx_signals_sent ON signals(sent_at) WHERE sent_at IS NULL;
```

**Table: `config_profiles`** (Trading strategy configurations - SENSITIVE)
```sql
CREATE TABLE config_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    stocks TEXT[] NOT NULL,          -- Array of tickers ["BHP.AX", "RIO.AX"]
    holding_period INT NOT NULL,     -- Days
    hurdle_rate FLOAT NOT NULL,      -- Minimum return threshold
    max_position_size FLOAT NOT NULL,-- AUD
    stop_loss FLOAT,                 -- Optional
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

**Table: `api_credentials`** (Broker/notification API keys - SENSITIVE)
```sql
CREATE TABLE api_credentials (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) UNIQUE NOT NULL,  -- 'telegram', 'line', 'sendgrid', 'twilio'
    encrypted_value TEXT NOT NULL,              -- AES-256 encrypted API key/token
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```
**Supported Services**:
- `telegram`: Telegram Bot Token (FREE unlimited messages)
- `line`: LINE Channel Access Token (FREE 500 messages/month, then $0.05/msg)
- `sendgrid`: Email API key
- `twilio`: SMS API credentials (paid per message)

**LINE Cost Analysis** (February 2026):
- FREE tier: 500 push messages/month
- Typical bot usage: ~130-200 messages/month (3-5 admins × daily signals + alerts)
- Paid tier: $0.05/message for 501-25,000 messages
- **Recommendation**: Use Telegram (unlimited free) + LINE (free tier) for redundancy

**Table: `job_logs`** (Execution history)
```sql
CREATE TABLE job_logs (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,   -- 'daily-signals', 'weekly-retrain'
    status VARCHAR(20) NOT NULL,     -- 'success', 'failure'
    duration_seconds INT,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL
);
CREATE INDEX idx_job_logs_created ON job_logs(created_at DESC);
```

### 2.4.2 Backup Strategy (Weekly Encrypted Exports)

**Schedule**: Saturday 04:00 AEST (after model retraining completes)

**Backup Process**:
1. Export all database tables to JSON
2. Compress (gzip)
3. Encrypt (AES-256 with `BACKUP_ENCRYPTION_KEY`)
4. Upload to Tigris: `backups/db-YYYYMMDD.json.gz.enc`
5. Auto-delete backups older than 4 weeks (keep 4 versions = 1 month retention)

**What Gets Backed Up**:
- Portfolio state (positions, trade history)
- Signal history (last 30 days)
- **SENSITIVE configs** (profiles, hurdle rates, API credentials)
- Job execution logs (last 7 days)

**Recovery Options**:
- **< 7 days**: Supabase point-in-time restore (15 min, FREE)
- **7-28 days**: Tigris weekly backup restore (5 min, decrypt + import)
- **Complete disaster**: Download from Tigris + restore to new Supabase (1 hour)

**Security**:
- Backups encrypted with AES-256 (stored in Fly.io secrets)
- Even Fly.io employees cannot decrypt without key
- Safe to store in cloud object storage

**Cost**: FREE (within Tigris 5GB limit, Supabase auto-backups included)

**Flask Endpoints** (Thread 2 Web UI):
- `POST /admin/backup/create` - Trigger manual backup
- `POST /admin/backup/restore` - Restore from specific backup file
- `GET /admin/backup/list` - List available backups (4 versions)

### 2.4.3 Tigris Object Storage (Fly.io Integrated)

**Stored Objects**:
```yaml
models/
  rf_20260204.pkl          # Random Forest trained model
  xgb_20260204.pkl         # XGBoost trained model
  catboost_20260204.pkl    # CatBoost trained model
  prophet_20260204.pkl     # Prophet time-series model
  lstm_20260204.h5         # LSTM neural network
  
backups/
  db-20260204.json.gz.enc  # Encrypted database export (latest)
  db-20260128.json.gz.enc  # Previous week backup
  db-20260121.json.gz.enc  # 2 weeks ago
  db-20260114.json.gz.enc  # 3 weeks ago (oldest kept)
```

**Retention Policy**:
- Models: Keep last 10 versions (automatic rotation)
- Backups: Keep last 4 weeks (4 versions)
- Total storage: ~500MB (well within 5GB FREE limit)

---

## 3. Configuration Management (Database-Backed with Web UI Editing)

**CRITICAL ARCHITECTURAL CHANGE**: Configurations now stored in **PostgreSQL** (not Git YAML files)

### 3.1 Why Database Storage for Sensitive Configs?

**Security Reasons**:
- Trading profiles contain competitive strategy information
- API credentials (broker tokens, SMS keys) must be encrypted at rest
- Git commits expose config history (leakage risk if repo becomes public)
- Database encryption + weekly AES-256 backups provide better security

**Operational Benefits**:
- **Hot reload**: Config changes take effect immediately (no deployment)
- **Web UI editing**: Thread 2 dashboard provides admin interface
- **Audit trail**: Database tracks who changed what and when
- **Rollback**: Restore from Tigris backups if bad config deployed
- **No Git conflicts**: Multiple admins can edit configs simultaneously

**Example: Old YAML vs New Database**:
```yaml
# OLD: Git YAML files (deprecated)
# profiles.yaml - PROBLEM: Credentials in plaintext
profiles:
  - id: "swing-trading"
    stocks: ["BHP.AX", "RIO.AX"]
    broker_api_key: "sk_live_abc123"  # ❌ Exposed in Git history
```

```sql
-- NEW: Database storage with encryption
-- config_profiles table
INSERT INTO config_profiles (name, stocks, holding_period, hurdle_rate)
VALUES ('swing-trading', ARRAY['BHP.AX', 'RIO.AX'], 7, 0.02);

-- api_credentials table (encrypted)
INSERT INTO api_credentials (service, credential_type, encrypted_value)
VALUES ('broker', 'api_key', encrypt('sk_live_abc123', :encryption_key));
```

### 3.2 Database Configuration Tables (Replaces YAML Files)

**Profile Configuration** (replaces `profiles.yaml`)
```sql
SELECT * FROM config_profiles;
-- Returns:
-- id | name           | stocks             | holding_period | hurdle_rate | max_position_size
-- 1  | swing-trading  | {BHP.AX, RIO.AX}  | 7              | 0.02        | 5000
-- 2  | dividend-growth| {CBA.AX, WBC.AX}  | 30             | 0.015       | 10000
  min_confidence: 0.6   # Only output signals with 60%+ consensus

hyperparameters:
  random_forest:
    n_estimators: 200
    max_depth: 10
  xgboost:
    learning_rate: 0.05
    n_estimators: 300
```

### 3.3 Execution Schedule (`execution.yaml`)
```yaml
schedules:
  daily_scan:
    cron: "0 8 * * 1-5"  # 08:00 weekdays (TST)
    task: "generate_signals"
    enabled: true
    
  weekly_retrain:
    cron: "0 2 * * 6"    # 02:00 Saturdays (TST)
    task: "retrain_models"
    enabled: true
    
risk_limits:
  max_daily_trades: 5
  max_portfolio_drawdown: 0.15  # Stop all trading if -15%
  position_size_pct: 0.20       # Max 20% of capital per stock
```

---

## 4. Data Sources & Integration

### 4.1 Market Data
- **Yahoo Finance API**: Primary OHLCV source (`.AX` suffix for ASX tickers, e.g., `CBA.AX`, `BHP.AX`)
- **ASX Data API**: Official market data (requires subscription, ~$50 AUD/month for delayed data)
- **Alpha Vantage**: Alternative free tier (500 API calls/day)
- **Fallback**: Refinitiv/Bloomberg API for institutional-grade data (expensive)

### 4.2 Broker API Integration (Future Phase)
Secure integration with Australian brokerage APIs for auto-trading:
- **Supported Brokers**: 
  - CommSec API (Commonwealth Bank)
  - Interactive Brokers (IBKR) API - full programmatic access
  - SelfWealth API (if available)
  - Stake API (US stocks, but ASX coming)
- **Order Types**: Market orders, limit orders, stop-loss, trailing stops
- **Authentication**: OAuth 2.0 with encrypted token storage (AWS Secrets Manager / HashiCorp Vault)
- **Rate Limiting**: Respect broker API quotas (e.g., 100 requests/minute)
- **Safety Features**:
  - Dry-run mode (simulate trades without execution)
  - Trade amount caps (max AUD per order)
  - Kill switch (emergency stop-all-trading button)
  - Chess sponsorship validation

### 4.3 OpenClaw Agent Integration (Advanced)
- **Message Format**: Standardized JSON schema for signals
- **Execution Flow**:
  1. BOT system generates BUY signal for 2330.TW
  2. Publishes message to Redis queue
  3. OpenClaw agent consumes message
  4. Agent validates signal against risk rules
  5. Agent submits order via broker API
  6. Agent reports execution status back to BOT system
- **Monitoring**: Real-time dashboard showing agent status, pending orders, executed trades

---

## 5. Security & Compliance

### 5.1 Secrets Management
- **API Keys**: Store in encrypted vaults (AWS Secrets Manager, Azure Key Vault, or local `.env` with git-ignored)
- **Database Credentials**: Environment variables only, never hardcoded
- **Broker Tokens**: Rotate every 30 days, encrypt at rest

### 5.2 Audit Trail
- **Immutable Log**: Every signal generated, trade executed, and config change logged with timestamp and user/system ID
- **Compliance**: Export logs in format compatible with Taiwan SFB regulations (if required)

### 5.3 Error Handling
- **Graceful Degradation**: If one data source fails, fall back to cached data or alternative source
- **Alerting**: Send critical errors to on-call notification channel (PagerDuty/Opsgenie)
- **Circuit Breaker**: Auto-disable trading if error rate exceeds threshold

---

## 6. Infrastructure & Deployment

> **📋 See [infrastructure_comparison.md](infrastructure_comparison.md) for detailed platform comparisons, cost analysis, and deployment recommendations.**

This document contains only functional and business requirements. For infrastructure-specific information, consult the companion document:

**infrastructure_comparison.md** includes:
- Python-native cloud platform comparison (Render, Fly.io, Railway, BinaryLane, AWS)
- Cost analysis over 3 years
- OpenClaw co-location strategies
- Cloudflare Workers as trade executor
- ASX-specific deployment considerations
- Security checklists
- Decision trees and final recommendations

### 6.1 Platform-Agnostic Requirements

**Compute:**
- Scheduled execution (cron-compatible)
- Python 3.11+ runtime
- 300-500MB RAM for inference
- Auto-scaling or sleep mode (98.9% idle workload)

**Database:**
- PostgreSQL or MongoDB
- <100MB storage for portfolio tracking
- Automated backups with point-in-time recovery
- Encryption at rest

**Storage:**
- Object storage for AI models (.pkl, .h5)
- 10-50GB for model versioning
- S3-compatible API preferred

**Notifications:**
- Email (3,000+/month capacity)
- SMS (optional)
- Webhooks (Slack, Telegram)

---

## 7. Success Metrics

### 7.1 System Reliability
- **Uptime**: 99.5% availability for scheduled job execution
- **Latency**: Signal generation completes within 5 minutes
- **Data Freshness**: Market data updated within 30 minutes of market close

### 7.2 Trading Performance (Backtested)
- **Win Rate**: >55% of BUY signals result in profitable trades
- **Sharpe Ratio**: >1.0 over 12-month period
- **Max Drawdown**: <20% from peak equity

### 7.3 Operational Efficiency
- **False Positive Rate**: <30% of HIGH confidence signals fail to reach profit target
- **Model Staleness**: Automatic retraining triggered if accuracy drops >10%
- **Cost per Signal**: Cloud execution cost <TWD 1 per signal generated

---

## 8. Development Phases

### Phase 1: Core Automation (MVP)
- ✅ Scheduler engine with cron support
- ✅ Signal generator with consensus logic
- ✅ YAML-based configuration system
- ✅ Email notification service
- ✅ Basic performance dashboard

### Phase 2: Enhanced Monitoring
- 📋 Job execution log UI
- 📋 Signal inspector with feature breakdown
- 📋 Portfolio tracker with P&L calculation
- 📋 Configuration editor with validation

### Phase 3: Data Pipeline
- 📋 Automated TWSE institutional data fetcher
- 📋 Data quality validation and alerting
- 📋 Model retraining pipeline

### Phase 4: External Integration
- 📋 REST API for agent consumption
- 📋 Kafka/RabbitMQ message queue
- 📋 Slack/Telegram notification bots

### Phase 5: Auto-Trading (Advanced)
- 📋 Broker API integration (Fubon/Yuanta)
- 📋 OpenClaw agent orchestration
- 📋 Trade execution monitoring
- 📋 Emergency kill switch and safety rails

---

## 9. Key Differences from Interactive Version

| Feature | Interactive (ASX/TWN) | BOT Automation |
|---------|----------------------|----------------|
| **Primary User** | Human analyst | Scheduled jobs, agents |
| **Execution Mode** | On-demand analysis | Cron-triggered |
| **Output Format** | Visual charts, tables | JSON signals, logs |
| **Configuration** | UI sliders/dropdowns | YAML files, git-versioned |
| **Decision Making** | Human interprets results | System auto-generates BUY/HOLD/SELL |
| **Deployment** | Local laptop, Streamlit Cloud | AWS Lambda, Kubernetes |
| **Logging** | Minimal (console only) | Comprehensive audit trail |
| **Integration** | None (standalone) | Broker APIs, messaging queues |

---

## 10. Technology Stack

### 10.1 Core Framework
- **Python 3.11+**: Main programming language
- **Celery + Redis**: Distributed task queue
- **APScheduler**: Advanced cron scheduling
- **SQLAlchemy**: Database ORM for portfolio tracking

### 10.2 Data & ML
- **yfinance**: Market data fetching
- **pandas/numpy**: Data processing
- **scikit-learn, XGBoost, CatBoost**: ML models (same as interactive version)
- **Prophet, TensorFlow**: Time-series forecasting

### 10.3 UI Dashboard
- **Streamlit**: Lightweight web UI for monitoring
- **Plotly**: Interactive performance charts
- **ag-Grid**: Advanced table for job logs

### 10.4 DevOps
- **Docker**: Containerization
- **GitHub Actions**: CI/CD pipeline
- **Terraform**: Infrastructure as Code (for cloud deployment)
- **Prometheus + Grafana**: Metrics and alerting

---

## 11. Sample Workflow

### Daily Execution Flow (08:00 TST)
1. **Scheduler triggers** `daily_scan` job
2. **Data Fetcher** downloads latest OHLCV and institutional data for watchlist stocks
3. **Signal Generator** runs AI consensus for each stock:
   - 2330.TW → BUY (confidence: 0.78, target: +3.2%)
   - 2317.TW → HOLD (confidence: 0.55, weak signal)
   - 2454.TW → SELL (confidence: 0.82, stop-loss triggered)
4. **Portfolio Tracker** updates virtual positions and P&L
5. **Notifier** sends:
   - Email report with signal table
   - Slack alert for 2330.TW BUY (HIGH confidence)
   - JSON published to Redis queue for OpenClaw agent
6. **Job Logger** records execution details (3 signals, 2.1 min runtime, success)
7. **Dashboard** updates with new data points

---

## 12. Future Enhancements

### 12.1 Advanced AI
- **Sentiment Analysis**: Incorporate Taiwan financial news sentiment (e.g., TVBS, Economic Daily News)
- **Reinforcement Learning**: Optimize position sizing and exit timing dynamically
- **Multi-Timeframe Signals**: Combine daily + weekly + monthly consensus

### 12.2 Portfolio Optimization
- **Multi-Stock Balancing**: Correlation-aware diversification across watchlist
- **Dynamic Hedging**: Auto-generate short positions for downside protection
- **Tax Harvesting**: Optimize trade timing to minimize STT impact

### 12.3 User Management
- **Multi-Tenant**: Support multiple users with isolated portfolios
- **Permission Roles**: Admin (full access), Viewer (read-only), Trader (execute signals)
- **Audit Compliance**: Export trade logs in SFB-compliant format

---

## 13. Summary

This BOT Automation System transforms the interactive AI trading analysis tool into a **production-ready, cloud-native recommendation engine**. It prioritizes:

- **Reliability**: Scheduled execution with robust error handling
- **Traceability**: Comprehensive logging and audit trails
- **Configurability**: Git-versioned, hot-reloadable settings
- **Extensibility**: Ready for broker API integration and auto-trading
- **Security**: Encrypted secrets, role-based access, kill switches

The system serves as the **intelligence layer** feeding downstream automation systems, enabling fully autonomous trading workflows while maintaining human oversight through dashboards and approval gates.

---

*Document Version: 1.0*  
*Last Updated: February 4, 2026*  
*Target Market: Taiwan Stock Exchange (TWSE/TPEx)*
