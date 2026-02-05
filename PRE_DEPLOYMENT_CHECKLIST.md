# Pre-Deployment Checklist for Fly.io

**Date**: February 5, 2026  
**Branch**: bots  
**Target Platform**: Fly.io (Sydney region)

---

## 1. Code Quality Checks

### ✅ Import Dependencies
- [x] All imports from `core/` module are valid
- [x] `yfinance`, `pandas`, `numpy` available
- [x] `scikit-learn`, `catboost` for AI models
- [x] `requests` for Telegram API
- [x] No circular imports detected

### ✅ Database Models
- [x] All models inherit from `MarketIsolatedModel`
- [x] `.for_market()` helper implemented
- [x] UniqueConstraints for idempotency
- [x] ARRAY type for PostgreSQL (stocks column)
- [x] No `.query.all()` without market filter

### ✅ API Routes
- [x] `/health` endpoint exists
- [x] `/cron/daily-signals?market=ASX` accepts market parameter
- [x] Bearer token authentication via `CRON_TOKEN`
- [x] CORS configured for admin UI

### ✅ Environment Variables
- [x] `.env.example` documented
- [ ] **ACTION REQUIRED**: Copy `.env.example` to `.env` and configure:
  - `DATABASE_URL` (Supabase PostgreSQL)
  - `CRON_TOKEN` (GitHub Actions auth)
  - `TELEGRAM_BOT_TOKEN` (notification)
  - `TELEGRAM_CHAT_ID` (notification target)
  - `BACKUP_ENCRYPTION_KEY` (AES-256 backups)

---

## 2. Database Setup

### Migration Status
- [ ] **ACTION REQUIRED**: Create database migrations
  ```bash
  # Install Flask-Migrate
  pip install Flask-Migrate
  
  # Initialize migrations
  flask db init
  
  # Create initial migration
  flask db migrate -m "Initial schema: signals, config_profiles, job_logs, api_credentials"
  
  # Apply migration
  flask db upgrade
  ```

### Default Data Initialization
- [ ] **ACTION REQUIRED**: Run initialization script (see `scripts/init_default_profile.py`)
  ```bash
  python scripts/init_default_profile.py
  ```

### Data Validation
- [ ] Verify ASX default profile created
- [ ] Verify 10 stocks loaded from ASX branch config
- [ ] Check market isolation (no USA/TWN data yet)

---

## 3. Testing Checklist

### Local Environment Tests
- [ ] **Unit Tests**: Run `pytest tests/bot/`
  ```bash
  pytest tests/bot/test_signal_generation.py -v
  pytest tests/bot/test_market_isolation.py -v
  ```

- [ ] **Manual API Test**: Start Flask app and trigger signal generation
  ```bash
  # Terminal 1: Start Flask
  python run_bot.py
  
  # Terminal 2: Test health check
  curl http://localhost:8080/health
  
  # Terminal 3: Trigger signal generation (requires CRON_TOKEN)
  curl -X POST http://localhost:8080/cron/daily-signals?market=ASX \
    -H "Authorization: Bearer YOUR_CRON_TOKEN"
  ```

- [ ] **Telegram Notification Test**: Verify message received
  - Check Telegram app for signal summary
  - Verify emoji formatting (📈 BUY, 📉 SELL, ⏸️ HOLD)
  - Confirm confidence percentages displayed

### Data Integrity Tests
- [ ] Verify idempotency (running twice = no duplicate signals)
- [ ] Check trading day validation (weekends skipped)
- [ ] Verify market isolation (ASX signals don't leak to USA/TWN)

---

## 4. Fly.io Configuration

### App Creation
- [ ] **ACTION REQUIRED**: Initialize Fly.io app
  ```bash
  fly launch --name asx-bot-trading --region syd
  ```

- [ ] **ACTION REQUIRED**: Set Fly.io secrets
  ```bash
  fly secrets set DATABASE_URL="postgresql://..." \
    CRON_TOKEN="..." \
    TELEGRAM_BOT_TOKEN="..." \
    TELEGRAM_CHAT_ID="..." \
    BACKUP_ENCRYPTION_KEY="..."
  ```

### Database Connection
- [ ] **ACTION REQUIRED**: Create Supabase PostgreSQL database
  - Region: Sydney (ap-southeast-2)
  - Plan: Free tier (500MB)
  - Extensions: None required (SQLAlchemy handles schema)

- [ ] **ACTION REQUIRED**: Get connection string from Supabase
  ```
  postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
  ```

### Deployment
- [ ] **ACTION REQUIRED**: Deploy to Fly.io
  ```bash
  fly deploy
  ```

- [ ] **ACTION REQUIRED**: Verify deployment
  ```bash
  fly status
  fly logs
  ```

---

## 5. GitHub Actions Configuration

### Secrets Setup
- [ ] **ACTION REQUIRED**: Add repository secrets
  - Go to: Settings → Secrets and variables → Actions
  - Add: `BOT_API_URL` = `https://asx-bot-trading.fly.dev`
  - Add: `CRON_TOKEN` = (same token used in Fly.io secrets)

### Workflow Verification
- [ ] Check `.github/workflows/daily-signals.yml` syntax
- [ ] Verify cron schedule: `'0 22 * * 0-4'` (08:00 AEST Mon-Fri)
- [ ] Verify backup schedule: `'0 0 * * 1-5'` (10:00 AEST Mon-Fri)
- [ ] Confirm market matrix: `[ASX]` (expandable to [ASX, USA, TWN])

### Test Trigger
- [ ] **ACTION REQUIRED**: Manually trigger workflow
  - Go to: Actions → Daily Signal Generation → Run workflow
  - Select branch: `bots`
  - Verify execution logs

---

## 6. Monitoring & Alerting

### Logging
- [ ] Configure Fly.io log shipping (optional)
  ```bash
  fly logs --app asx-bot-trading -f
  ```

### Database Queries
- [ ] **ACTION REQUIRED**: Verify signal storage
  ```python
  from app.bot import create_app, db
  from app.bot.shared.models import Signal
  
  app = create_app()
  with app.app_context():
      signals = Signal.for_market('ASX').order_by(Signal.created_at.desc()).limit(10).all()
      for s in signals:
          print(f"{s.ticker}: {s.signal} ({s.confidence*100:.0f}%)")
  ```

### Telegram Monitoring
- [ ] Verify daily signal messages arrive at 08:00 AEST
- [ ] Check backup notifications arrive at 10:00 AEST
- [ ] Monitor for error messages (fallback notifications)

---

## 7. Security Review

### Secrets Management
- [x] No hardcoded API keys in code
- [x] `.env` file in `.gitignore`
- [x] Secrets loaded from environment variables
- [ ] **ACTION REQUIRED**: Rotate `CRON_TOKEN` after initial deployment

### Database Security
- [x] Connection strings encrypted (SSL mode required)
- [x] Passwords NOT stored in plaintext (hashed via bcrypt)
- [x] Market isolation prevents cross-contamination

### API Security
- [x] Bearer token authentication on `/cron/*` endpoints
- [x] No public admin endpoints (requires auth)
- [x] CORS restricted to allowed origins

---

## 8. Default Profile Configuration

**From ASX Branch (`asx:core/config.py`)**:
```python
DEFAULT_ASX_PROFILE = {
    'market': 'ASX',
    'name': 'Default Growth Portfolio',
    'stocks': [
        'ABB',    # Aussie Broadband
        'SIG',    # Sigma Healthcare
        'IOZ',    # iShares Core S&P/ASX 200 ETF
        'INR',    # Ioneer
        'IMU',    # Imugene
        'MQG',    # Macquarie Group
        'PLS',    # Pilbara Minerals
        'XRO',    # Xero
        'TCL',    # Transurban Group
        'SHL'     # Sonic Healthcare
    ],
    'holding_period': 30,           # days
    'hurdle_rate': 0.05,            # 5% minimum return
    'stop_loss': 0.15,              # 15% stop loss
    'max_position_size': 3000.0,    # $3,000 per position
}
```

**Cost & Tax Settings**:
- Brokerage: 0.12% (`0.0012`)
- Clearing: 0.00225% (`0.0000225`)
- Settlement: $1.50 fixed
- Tax Rate: 25% (`0.25`)
- Annual Income: $90,000 (for tax bracket calculation)
- Risk Buffer: 0.5% (`0.005`) for slippage/volatility

---

## 9. Rollback Plan

### If Deployment Fails
1. Check Fly.io logs: `fly logs --app asx-bot-trading`
2. Verify database connection: `fly ssh console -a asx-bot-trading`
3. Rollback to previous version: `fly releases --app asx-bot-trading`
4. Restore previous release: `fly releases restore [VERSION]`

### If Signal Generation Fails
1. Check job logs in database: `SELECT * FROM job_logs ORDER BY created_at DESC LIMIT 10;`
2. Verify profile configuration: `SELECT * FROM config_profiles WHERE market='ASX';`
3. Test locally with same data: `python scripts/test_signal_generation.py`

### Emergency Contacts
- GitHub Actions: Check workflow run logs
- Telegram: @BotFather for bot token issues
- Supabase: Dashboard → Project Settings → Database

---

## 10. Post-Deployment Verification

### Day 1 Checklist (First Trading Day)
- [ ] Verify signal generation triggered at 08:00 AEST
- [ ] Check Telegram notification received
- [ ] Verify signals stored in database
- [ ] Confirm no duplicate signals created
- [ ] Review job logs for errors

### Week 1 Checklist
- [ ] Verify 5 days of signals generated (Mon-Fri)
- [ ] Check backup notifications (10:00 AEST daily)
- [ ] Monitor Fly.io resource usage (CPU/Memory)
- [ ] Review database size (should be < 100MB)
- [ ] Test manual trigger via GitHub Actions

### Month 1 Checklist
- [ ] Analyze signal accuracy vs actual market movements
- [ ] Review confidence scores distribution
- [ ] Optimize hurdle rate based on performance
- [ ] Consider adding USA/TWN markets
- [ ] Implement advanced notification channels (Email/SMS)

---

## ✅ Final Sign-Off

**All critical checks completed?**
- [ ] Code quality verified
- [ ] Database initialized with default profile
- [ ] Environment variables configured
- [ ] Fly.io deployment successful
- [ ] GitHub Actions workflows active
- [ ] Telegram notifications working
- [ ] First signal generation tested

**Deployment Approved By**: _________________  
**Date**: _________________

**Deployment Command**:
```bash
git push origin bots && fly deploy --app asx-bot-trading
```

---

**CRITICAL REMINDERS**:
1. Never deploy without `.env` configured locally first
2. Always test signal generation locally before deploying
3. Verify Telegram bot responds before enabling cron
4. Check Fly.io logs immediately after deployment
5. Monitor first trading day closely (08:00 AEST trigger)
