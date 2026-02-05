# Bot Quick Start Guide

## ✅ Implementation Status

**Core Components**: Complete
- ✅ Multi-market signal generation (ASX implemented, USA/TWN ready for expansion)
- ✅ AI consensus logic integrated (Random Forest + CatBoost)
- ✅ Telegram/Email/SMS notifications (with graceful fallbacks)
- ✅ Database models with market isolation (`.for_market()` helper)
- ✅ GitHub Actions workflow (dual-trigger reliability)
- ✅ Idempotent signal generation (no duplicates)

**Pending**:
- Database migrations (schema ready, need to run migrations)
- Environment configuration (copy .env.example to .env)
- Comprehensive test suite

---

## 🚀 Local Development Setup

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or use UV for faster installation
uv pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env with your credentials
# Minimum required:
# - DATABASE_URL (PostgreSQL connection string)
# - CRON_TOKEN (for GitHub Actions auth)
# - TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID (for notifications)
```

### 3. Set Up Database

```bash
# Create PostgreSQL database
# Option 1: Local PostgreSQL
createdb asx_bot

# Option 2: Supabase (recommended for production)
# 1. Create project at https://supabase.com
# 2. Copy connection string to .env

# Run migrations (TODO: create migration files)
# flask db upgrade
```

### 4. Create First Trading Profile

```python
# Python console
from app.bot import create_app, db
from app.bot.shared.models import ConfigProfile

app = create_app()
with app.app_context():
    # Create ASX profile
    profile = ConfigProfile(
        market='ASX',
        name='Growth Stocks',
        stocks=['BHP', 'CBA', 'CSL', 'RIO'],  # Without .AX suffix
        holding_period=30,
        hurdle_rate=0.05,  # 5% minimum return
        max_position_size=10000.0,
        stop_loss=0.10  # 10% stop loss
    )
    db.session.add(profile)
    db.session.commit()
    print(f"✅ Created profile: {profile.name}")
```

### 5. Run Flask App Locally

```bash
# Development mode
python run_bot.py

# Or with gunicorn (production-like)
gunicorn -w 2 -b 0.0.0.0:8080 'app.bot:create_app()'
```

### 6. Test Signal Generation

```bash
# Health check
curl http://localhost:8080/health

# Manual signal generation (requires CRON_TOKEN in .env)
curl -X POST http://localhost:8080/cron/daily-signals?market=ASX \
  -H "Authorization: Bearer YOUR_CRON_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 📱 Telegram Bot Setup

### 1. Create Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow instructions
3. Copy the Bot Token (e.g., `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
4. Add to `.env` as `TELEGRAM_BOT_TOKEN`

### 2. Get Your Chat ID

```bash
# Method 1: Send message to your bot, then:
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates

# Look for "chat":{"id":123456789} in the response
# Add to .env as TELEGRAM_CHAT_ID=123456789

# Method 2: Use @userinfobot
# 1. Message @userinfobot on Telegram
# 2. It will reply with your chat ID
```

### 3. Test Notification

```python
# Python console
from app.bot.services.notification_service import send_telegram
send_telegram("🤖 ASX Bot is online!")
# Check your Telegram app for the message
```

---

## 🧪 Testing

### Run Tests

```bash
# All bot tests
pytest tests/bot/ -v

# With coverage
pytest tests/bot/ --cov=app.bot --cov-report=html

# Specific test
pytest tests/bot/test_idempotent_signals.py -v
```

### Test Checklist

- [ ] Market isolation (ASX signals don't mix with USA)
- [ ] Idempotency (duplicate signals prevented)
- [ ] Notification delivery (Telegram/Email/SMS)
- [ ] AI consensus logic (models voting correctly)
- [ ] Trading day validation (weekends/holidays skipped)

---

## 🚢 Deployment (Fly.io)

### 1. Install Fly CLI

```bash
# macOS
brew install flyctl

# Login
fly auth login
```

### 2. Create Fly App

```bash
# Initialize (uses existing Dockerfile)
fly launch --name asx-bot-trading --region syd

# Set secrets
fly secrets set \
  CRON_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" \
  TELEGRAM_BOT_TOKEN="your-token" \
  TELEGRAM_CHAT_ID="your-chat-id" \
  DATABASE_URL="postgresql://..."
```

### 3. Deploy

```bash
# Deploy app
fly deploy

# Check logs
fly logs

# Scale (if needed)
fly scale vm shared-cpu-1x
fly scale count 1
```

### 4. Configure GitHub Secrets

In your GitHub repo settings → Secrets and variables → Actions:

- `BOT_API_URL`: `https://asx-bot-trading.fly.dev`
- `CRON_TOKEN`: (same as Fly secret)

---

## 📊 Monitoring

### View Signals

```bash
# Query database directly
psql $DATABASE_URL -c "SELECT * FROM signals WHERE market='ASX' ORDER BY date DESC LIMIT 10;"

# Or use admin UI (if implemented)
# https://asx-bot-trading.fly.dev/admin/asx/signals
```

### Check Job Logs

```python
from app.bot import create_app, db
from app.bot.shared.models import JobLog

app = create_app()
with app.app_context():
    logs = JobLog.for_market('ASX').order_by(JobLog.created_at.desc()).limit(10).all()
    for log in logs:
        print(f"{log.created_at} - {log.job_type}: {log.status}")
```

---

## 🎯 Next Steps

1. **Create database migrations** (Flask-Migrate or Alembic)
2. **Write comprehensive tests** (pytest suite)
3. **Implement model caching** (save trained models to Tigris)
4. **Add USA/TWN markets** (copy ASX config, update trading hours)
5. **Build admin UI** (Flask-Admin or custom dashboard)
6. **Set up backup service** (weekly encrypted backups to Tigris)

---

## 🐛 Troubleshooting

### Signals not generating?

1. Check trading day validation (weekends/holidays skipped)
2. Verify ConfigProfile exists for market
3. Check logs: `fly logs` or local console output

### Notifications not sending?

1. Verify environment variables set
2. Test Telegram bot manually: `curl https://api.telegram.org/bot<TOKEN>/getMe`
3. Check logs for error messages

### Database connection issues?

1. Verify `DATABASE_URL` format: `postgresql://user:pass@host:port/database`
2. Test connection: `psql $DATABASE_URL -c "SELECT 1;"`
3. Check Fly secrets: `fly secrets list`

---

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).
