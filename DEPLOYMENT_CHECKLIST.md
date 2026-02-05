# AI Trading Bot System - Deployment Readiness Checklist

**Stack**: Koyeb (compute + secrets) + Cloudflare R2 (storage) + Supabase (database) + GitHub Actions (automation)

**Target**: Production deployment at `https://money.twoudia.com`

**Cost**: $0.22/month ($2.64/year)

---

## ✅ Pre-Deployment Verification

### 1. Code & Configuration Files

- [x] **Dockerfile** - Multi-stage production build
  - Custom system dependencies (gcc, g++, libpq-dev)
  - Python 3.12 with AI/ML libraries
  - Non-root user (botuser)
  - Health check configured
  - Gunicorn WSGI server

- [x] **requirements.txt** - All Python dependencies
  - Flask 3.0.0 + SQLAlchemy 2.0.23
  - psycopg 3.1.18 (PostgreSQL adapter)
  - AI/ML: scikit-learn, catboost, prophet, tensorflow
  - Market data: yfinance, pandas, numpy
  - Cloud: boto3 (R2), cryptography (encryption)
  - Production: gunicorn

- [x] **koyeb.yaml** - Koyeb deployment config
  - eSmall instance (Singapore region)
  - Auto-stop enabled (5 min idle, Light Sleep)
  - Environment variables with Koyeb Secrets
  - Health check: /health endpoint
  - Custom domain: money.twoudia.com

- [x] **.env.example** - Environment variables template
  - Supabase DATABASE_URL
  - Cloudflare R2 credentials
  - Telegram bot tokens
  - API bearer token
  - Flask secret key

- [x] **run_bot.py** - Application entry point
  - Flask app factory initialization
  - Database table creation
  - Gunicorn-compatible (run_bot:app)

- [x] **.github/workflows/daily-signals.yml** - GitHub Actions cron
  - Primary: 08:00 AEST Mon-Fri
  - Backup: 10:00 AEST Mon-Fri
  - Market: ASX (expandable to USA, TWN)

- [x] **DEPLOYMENT_GUIDE.md** - Step-by-step deployment
  - 7 deployment steps (70 minutes total)
  - SQL schema creation scripts
  - Verification checklist
  - Troubleshooting guide

---

## ✅ Architecture Components Ready

### Compute: Koyeb
- [x] Configuration: `koyeb.yaml` ready
- [ ] Account created: https://app.koyeb.com/signup
- [ ] Secrets configured (8 secrets required)
- [ ] Service deployed (CLI or Web UI)
- [ ] Custom domain added: money.twoudia.com
- [ ] Health check passing: /health endpoint

### Database: Supabase PostgreSQL (FREE)
- [x] Schema: 4 tables (signals, job_logs, config_profiles, api_credentials)
- [ ] Account created: https://supabase.com/dashboard
- [ ] Project created (Singapore region)
- [ ] SQL schema executed (DEPLOYMENT_GUIDE.md Step 2.3)
- [ ] Default ASX profile inserted
- [ ] DATABASE_URL saved

### Storage: Cloudflare R2 (FREE)
- [x] boto3 client configured
- [ ] R2 bucket created: trading-bot-backups
- [ ] API tokens generated (Access Key ID, Secret Access Key)
- [ ] Account ID saved
- [ ] Backup script tested (manual run)

### DNS: Cloudflare (FREE)
- [x] Subdomain delegation strategy documented
- [ ] NS records added at current DNS provider
- [ ] Delegation verified: `dig NS money.twoudia.com`
- [ ] CNAME record added in Cloudflare → Koyeb domain
- [ ] SSL certificate auto-provisioned (Let's Encrypt)

### Notifications: Telegram Bot API (FREE)
- [ ] Bot created via @BotFather
- [ ] Bot token saved
- [ ] Chat ID obtained
- [ ] Test message sent successfully

### Automation: GitHub Actions (FREE)
- [x] Workflow file: `.github/workflows/daily-signals.yml`
- [ ] Repository secrets configured (4 secrets)
- [ ] Manual trigger tested
- [ ] Cron schedule verified (08:00 AEST Mon-Fri)

---

## ✅ Deployment Sequence (Follow DEPLOYMENT_GUIDE.md)

**Total Time**: ~70 minutes

1. [ ] **Step 1**: Cloudflare subdomain delegation (10 min)
   - Add NS records at current DNS provider
   - Verify delegation: `dig NS money.twoudia.com`

2. [ ] **Step 2**: Supabase PostgreSQL setup (15 min)
   - Create project (Singapore region)
   - Execute SQL schema (4 tables + indexes)
   - Insert default ASX profile
   - Save DATABASE_URL

3. [ ] **Step 3**: Cloudflare R2 storage (10 min)
   - Create bucket: trading-bot-backups
   - Generate API tokens
   - Save credentials (Account ID, Access Key, Secret Key)

4. [ ] **Step 4**: Telegram bot setup (5 min)
   - Create bot via @BotFather
   - Get bot token and chat ID
   - Send test message

5. [ ] **Step 5**: Koyeb deployment (20 min)
   - Create Koyeb account
   - Create 8 secrets (CLI or Web UI)
   - Deploy service (via koyeb.yaml)
   - Get Koyeb domain: trading-bot-abc123.koyeb.app
   - Add custom domain: money.twoudia.com
   - Verify health: `curl https://money.twoudia.com/health`

6. [ ] **Step 6**: Cloudflare DNS CNAME (2 min)
   - Add CNAME: @ → trading-bot-abc123.koyeb.app
   - Set to DNS Only (gray cloud)
   - Wait for DNS propagation (5-30 min)

7. [ ] **Step 7**: GitHub Actions setup (10 min)
   - Add repository secrets (4 secrets)
   - Test manual workflow trigger
   - Verify cron schedule

---

## ✅ Post-Deployment Testing

### Test 1: Health Check
```bash
curl https://money.twoudia.com/health

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-02-05T00:00:00Z"
}
```
- [ ] Health check passes
- [ ] Database connection confirmed

### Test 2: Manual Signal Generation
```bash
curl -X POST https://money.twoudia.com/cron/daily-signals?market=ASX \
  -H "Authorization: Bearer your-api-bearer-token"

# Expected response:
{
  "status": "success",
  "market": "ASX",
  "signals_generated": 3,
  "notifications_sent": true,
  "execution_time": 45.2
}
```
- [ ] Signals generated successfully
- [ ] Telegram notification received
- [ ] Database records created

### Test 3: Admin Dashboard
```bash
open https://money.twoudia.com/admin/ui
```
- [ ] Dashboard loads
- [ ] Signal history displayed
- [ ] Job execution logs visible

### Test 4: Database Verification
In Supabase SQL Editor:
```sql
SELECT * FROM signals WHERE market='ASX' ORDER BY date DESC LIMIT 10;
SELECT * FROM job_logs ORDER BY timestamp DESC LIMIT 5;
SELECT * FROM config_profiles WHERE market='ASX';
```
- [ ] Signals table has data
- [ ] Job logs recorded
- [ ] Default ASX profile exists

### Test 5: Auto-Stop/Wake Cycle
1. [ ] Wait 5 minutes (no requests)
2. [ ] Koyeb dashboard shows "Sleeping"
3. [ ] Make request: `curl https://money.twoudia.com/health`
4. [ ] Service wakes in ~200ms (Light Sleep)
5. [ ] Health check returns success

### Test 6: GitHub Actions Automation
1. [ ] Go to Actions tab → "Daily Trading Signals (ASX)"
2. [ ] Click "Run workflow"
3. [ ] Verify execution completes
4. [ ] Check Telegram for notification
5. [ ] Verify signal in database

---

## ✅ Why Dockerfile vs Buildpacks?

### **TLDR: Use Dockerfile** ✅

**Buildpacks are great for simple Flask apps, but this AI trading bot needs Dockerfile for:**

| Requirement | Buildpacks | Dockerfile |
|-------------|------------|------------|
| **Custom system deps** (gcc, g++, libpq-dev) | ❌ Not supported | ✅ Full control |
| **AI/ML libraries** (scikit-learn, tensorflow) | ⚠️ May fail (missing C compilers) | ✅ Installs gcc/g++ |
| **PostgreSQL client tools** (pg_dump for backups) | ❌ Not included | ✅ postgresql-client |
| **Explicit Python 3.12** | ⚠️ Auto-detects (may pick 3.11) | ✅ python:3.12-slim |
| **Multi-stage builds** (smaller images) | ❌ Not supported | ✅ FROM base AS... |
| **Non-root user** (security) | ⚠️ Runs as root | ✅ useradd botuser |
| **Custom health check** (DB connectivity) | ❌ Basic HTTP only | ✅ HEALTHCHECK with curl |
| **Production WSGI** (gunicorn workers/timeouts) | ⚠️ Generic config | ✅ Custom CMD |

### **When to Use Buildpacks**:
- Simple Python web app (Flask/Django with no C extensions)
- No system dependencies (pure Python packages)
- Want auto-detection (language, dependencies, runtime)
- Rapid prototyping (no Dockerfile to write)

### **When to Use Dockerfile** ✅ (This Project):
- AI/ML workloads (numpy, pandas, scikit-learn, tensorflow)
- Need compiled extensions (C/C++ libraries)
- PostgreSQL client tools (backups, database migrations)
- Custom security (non-root user)
- Production optimization (multi-stage builds, layer caching)

---

## ✅ Final Readiness Checklist

### Code
- [x] All bot service files have correct headers (multi-market)
- [x] Dockerfile optimized for AI/ML dependencies
- [x] requirements.txt complete (Flask, PostgreSQL, AI, R2, Telegram)
- [x] run_bot.py entry point configured
- [x] Database models have market isolation (`.for_market()`)

### Configuration
- [x] koyeb.yaml deployment config
- [x] .env.example environment variables template
- [x] .github/workflows/daily-signals.yml cron automation
- [x] .dockerignore (excludes .env, models/, data/)

### Documentation
- [x] DEPLOYMENT_GUIDE.md (step-by-step 70-min setup)
- [x] DEPLOYMENT_CHECKLIST.md (this file)
- [x] CLOUD_PRICING_COMPARISON.md (architecture analysis)
- [x] README.md (updated for multi-market bot)

### Testing
- [ ] Local development run successful
- [ ] Database migrations work
- [ ] Health check endpoint responds
- [ ] Signal generation tested manually

---

## 🚀 Ready to Deploy!

**All configuration files are ready**. Follow the **7-step deployment guide** in `DEPLOYMENT_GUIDE.md`:

1. Cloudflare subdomain delegation (10 min)
2. Supabase PostgreSQL (15 min)
3. Cloudflare R2 (10 min)
4. Telegram bot (5 min)
5. Koyeb deployment (20 min)
6. Cloudflare DNS (2 min)
7. GitHub Actions (10 min)

**Total**: ~70 minutes to production at `https://money.twoudia.com`

**Cost**: $0.22/month ($2.64/year) 🎉

---

## 📊 Stack Summary

```
money.twoudia.com
    ↓ (subdomain delegation)
Cloudflare DNS (FREE)
    ↓ (CNAME → koyeb.app)
Koyeb eSmall - Singapore ($0.22/month)
    ├─ Flask Bot (Python 3.12)
    ├─ Auto-stop (5 min idle, 200ms wake)
    └─ Koyeb Secrets (8 secrets)
    ↓
┌─────────────────┬──────────────────┬────────────────┐
│ Supabase Free   │ Cloudflare R2    │ GitHub Actions │
│ (PostgreSQL)    │ (Backups)        │ (Cron Trigger) │
│ Always-on       │ 10GB free        │ Free 2000 min  │
│ 500MB storage   │ No egress fees   │ Daily 08:00    │
│ Singapore       │ Global           │ AEST Mon-Fri   │
└─────────────────┴──────────────────┴────────────────┘
         ↓                  ↓
    Telegram Bot API (FREE notifications)
```

**Next**: Open `DEPLOYMENT_GUIDE.md` and start with Step 1!
