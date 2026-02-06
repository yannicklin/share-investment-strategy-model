# AI Trading Bot System - Deployment Guide

**Target Architecture**: Koyeb + Supabase + Cloudflare R2  
**Custom Domain**: money.twoudia.com (subdomain delegation)  
**Total Cost**: $0.22/month ($2.64/year)

---

## 📋 Prerequisites Checklist

- [ ] GitHub account (for repository and Actions)
- [ ] Domain ownership: `twoudia.com` (for subdomain delegation)
- [ ] Telegram account (for bot notifications)
- [ ] Cloudflare account (free)
- [ ] Supabase account (free)
- [ ] Koyeb account (free)

---

## 🚀 Deployment Steps

### **Step 1: Cloudflare Subdomain Delegation** (10 minutes)

**Goal**: Delegate `money.twoudia.com` to Cloudflare while keeping `twoudia.com` at current DNS provider.

#### 1.1 Create Cloudflare Account
1. Go to: https://dash.cloudflare.com/sign-up
2. Create free account

#### 1.2 Get Cloudflare Nameservers
1. **WORKAROUND**: Create dummy domain "money-twoudia.com" in Cloudflare
   - Dashboard → Add Site → Enter: `money-twoudia.com`
   - Select: **Free Plan**
2. Cloudflare assigns nameservers:
   ```
   ns1.cloudflare.com
   ns2.cloudflare.com
   ```
3. **Save these nameservers** - you'll use them next

#### 1.3 Delegate Subdomain at Your Current DNS Provider
1. Log into your current DNS provider (GoDaddy/Namecheap/Route53/etc.)
2. Add **2 NS records**:

   **Record 1**:
   ```
   Type: NS
   Host: money.twoudia.com  (or just "money" depending on provider)
   Value: ns1.cloudflare.com
   TTL: 1 hour
   ```

   **Record 2**:
   ```
   Type: NS
   Host: money.twoudia.com  (or just "money")
   Value: ns2.cloudflare.com
   TTL: 1 hour
   ```

3. **Wait 5-30 minutes** for DNS propagation

#### 1.4 Verify Subdomain Delegation
```bash
# Check if subdomain is delegated to Cloudflare
dig NS money.twoudia.com

# Should show:
# money.twoudia.com.  3600  IN  NS  ns1.cloudflare.com.
# money.twoudia.com.  3600  IN  NS  ns2.cloudflare.com.
```

✅ **Result**: `money.twoudia.com` now managed by Cloudflare, `twoudia.com` stays at current provider.

---

### **Step 2: Supabase PostgreSQL Setup** (15 minutes)

**Goal**: Create always-on PostgreSQL database (500MB free tier).

#### 2.1 Create Supabase Project
1. Go to: https://supabase.com/dashboard
2. Sign in with GitHub
3. Create New Organization → Enter your name
4. Create New Project:
   ```
   Organization: Your Name
   Project Name: trading-bot-asx
   Database Password: <generate-strong-password>  # SAVE THIS!
   Region: Southeast Asia (Singapore)  # Closest to Koyeb
   Plan: Free
   ```

#### 2.2 Get Connection String
1. Project Settings → Database → Connection String → **URI**
2. Copy connection string:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.abcdefghijk.supabase.co:5432/postgres
   ```
3. **Save this** - you'll add to Koyeb later

#### 2.3 Create Database Schema
1. SQL Editor → New Query
2. Paste and run:

```sql
-- Trading signals table (market-isolated)
CREATE TABLE signals (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    signal VARCHAR(10),
    predicted_return DECIMAL(5,2),
    confidence DECIMAL(3,2),
    model VARCHAR(50),
    market VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW(),
    sent_at TIMESTAMP DEFAULT NULL,
    UNIQUE(market, date, ticker)  -- Prevents duplicates
);

-- Indexes for faster queries
CREATE INDEX idx_signals_market_date ON signals(market, date);
CREATE INDEX idx_signals_ticker ON signals(ticker);
CREATE INDEX idx_signals_sent ON signals(sent_at);

-- Job execution logs
CREATE TABLE job_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20),
    market VARCHAR(10),
    signals_generated INTEGER,
    execution_time DECIMAL(5,2),
    error_message TEXT
);

-- Trading configuration profiles
CREATE TABLE config_profiles (
    id SERIAL PRIMARY KEY,
    market VARCHAR(10),
    name VARCHAR(50),
    holding_period INTEGER,
    hurdle_rate DECIMAL(4,2),
    stop_loss DECIMAL(4,2),
    tickers JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(market, name)
);

-- Encrypted API credentials
CREATE TABLE api_credentials (
    id SERIAL PRIMARY KEY,
    service VARCHAR(50),
    encrypted_token TEXT,
    market VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert default ASX profile
INSERT INTO config_profiles (market, name, holding_period, hurdle_rate, stop_loss, tickers)
VALUES (
    'ASX',
    'default',
    30,
    0.05,
    0.15,
    '["ABB.AX","SIG.AX","IOZ.AX","INR.AX","IMU.AX","MQG.AX","PLS.AX","XRO.AX","TCL.AX","SHL.AX"]'::jsonb
);
```

✅ **Result**: Database ready with schema and default ASX configuration.

---

### **Step 3: Cloudflare R2 Storage Setup** (10 minutes)

**Goal**: Create S3-compatible storage for database backups (10GB free).

#### 3.1 Create R2 Bucket
1. Cloudflare Dashboard → R2 → Create Bucket
2. Bucket Name: `trading-bot-backups`
3. Location: Automatic (global)

#### 3.2 Generate API Tokens
1. R2 → Manage R2 API Tokens → Create API Token
2. Token Name: `trading-bot-backup`
3. Permissions: **Object Read & Write**
4. TTL: Never
5. Click Create
6. **SAVE THESE CREDENTIALS**:
   ```
   Access Key ID: <copy-this>
   Secret Access Key: <copy-this>
   Account ID: <copy-this>
   ```

✅ **Result**: R2 bucket ready for automated backups.

---

### **Step 4: Telegram Bot Setup** (5 minutes)

**Goal**: Create notification bot for daily trading signals.

#### 4.1 Create Bot via BotFather
1. Open Telegram → Search for `@BotFather`
2. Send: `/newbot`
3. Bot Name: `AI Trading Bot`
4. Bot Username: `ai_trading_asx_bot` (must be unique)
5. **SAVE BOT TOKEN**: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

#### 4.2 Get Chat ID
1. Send message to your new bot: `/start`
2. Get Chat ID:
   ```bash
   # Replace BOT_TOKEN with your token
   curl https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
   
   # Look for "chat":{"id":123456789}
   ```
3. **SAVE CHAT ID**: `123456789`

✅ **Result**: Telegram bot ready to send signals.

---

### **Step 5: Koyeb Deployment** (20 minutes)

**Goal**: Deploy Flask bot to Singapore with auto-stop.

#### 5.1 Create Koyeb Account
1. Go to: https://app.koyeb.com/signup
2. Sign up with GitHub

#### 5.2 Create Koyeb Secrets (CLI method - RECOMMENDED)
```bash
# Install Koyeb CLI
brew install koyeb/tap/koyeb  # macOS
# or download from: https://www.koyeb.com/docs/cli

# Login
koyeb login

# Create secrets
koyeb secrets create database_url --value "postgresql://postgres:..."
koyeb secrets create r2_account_id --value "your-account-id"
koyeb secrets create r2_access_key --value "your-access-key-id"
koyeb secrets create r2_secret_key --value "your-secret-access-key"
koyeb secrets create telegram_bot_token --value "123456:ABC..."
koyeb secrets create telegram_chat_id --value "123456789"
koyeb secrets create flask_secret_key --value "$(openssl rand -hex 32)"
koyeb secrets create api_bearer_token --value "$(openssl rand -hex 32)"
```

**Alternative: Web UI Method**:
1. Koyeb Dashboard → Secrets → Create Secret
2. Add each secret manually

#### 5.3 Deploy Service (CLI method)
```bash
# Clone repository (if not already)
git clone https://github.com/your-username/share-investment-strategy-model.git
cd share-investment-strategy-model
git checkout bots

# Deploy using koyeb.yaml
koyeb service create --config koyeb.yaml
```

**Alternative: Web UI Method**:
1. Services → Create Service → GitHub
2. Repository: `your-username/share-investment-strategy-model`
3. Branch: `bots`
4. Builder: Dockerfile
5. Instance: **eSmall** (0.5 vCPU, 1GB RAM)
6. Region: **Singapore**
7. Auto-stop: ✅ Enabled (5 min idle)
8. Light Sleep: ✅ Enabled
9. Environment Variables: Reference secrets created in Step 5.2

#### 5.4 Get Koyeb Domain
After deployment (3-5 minutes):
```
https://trading-bot-abc123.koyeb.app
```
**SAVE THIS DOMAIN** - you'll add to Cloudflare DNS next.

#### 5.5 Add Custom Domain in Koyeb
1. Service → Networking → Domains → Add Custom Domain
2. Domain: `money.twoudia.com`
3. Wait for validation (1-2 minutes)
4. ✅ Let's Encrypt SSL auto-provisioned

---

### **Step 6: Cloudflare DNS + AI Bot Blocking** (5 minutes)

#### 6.1 Add CNAME in Cloudflare
1. Go back to Cloudflare → "money-twoudia-top" site
2. DNS → Add Record:
   ```
   Type: CNAME
   Name: @  (represents money.twoudia.top)
   Target: trading-bot-abc123.koyeb.app  (from Step 5.4)
   Proxy: 🟠 Proxied (ORANGE CLOUD) - CRITICAL for AI bot blocking!
   TTL: Auto
   ```

✅ **Use "Proxied"** (🟠 orange cloud) to enable Cloudflare network-level bot protection
- Blocks AI crawlers even when they spoof user agents (GPTBot, ClaudeBot, PerplexityBot)
- Koyeb health checks still work through Cloudflare proxy
- SSL provided by Cloudflare (Let's Encrypt)
- DDoS protection included

#### 6.2 Enable FREE AI Bot Blocking (Network-Level Enforcement)
1. Cloudflare Dashboard → Security → Bots
2. Scroll to "AI Scrapers and Crawlers"
3. Toggle: **ON** (blue)
4. ✅ Now physically blocks:
   - **GPTBot** (ChatGPT/OpenAI training)
   - **ClaudeBot** (Anthropic/Claude training)
   - **CCBot** (Common Crawl - used by many AI companies)
   - **Bytespider** (TikTok/ByteDance AI)
   - **PerplexityBot** (even when lying about user agent)
   - **Google-Extended** (AI training, NOT search)
   - **Amazonbot**, **ImagesiftBot**, and more

**How It Works**:
- Cloudflare's ML model fingerprints scraping tools across 57M requests/second globally
- Detects AI bots even when they pretend to be real browsers
- Auto-updated as new AI bots emerge (you don't need to do anything)

**Defense Layers**:
1. ✅ **Cloudflare AI Blocking** (Layer 1) - Network-level enforcement, blocks dishonest bots
2. ✅ **robots.txt** (Layer 2) - Polite notice for honest bots
3. ✅ **HTTP X-Robots-Tag** (Layer 3) - Header-level blocking
4. ✅ **HTML Meta Tags** (Layer 4) - Page-level instructions

**Why Use Cloudflare + robots.txt?**
- Cloudflare might miss brand-new AI bots (released yesterday)
- robots.txt provides legal evidence ("we explicitly said no")
- Defense in depth (multiple layers = stronger privacy)

---

### **Step 7: GitHub Actions Setup** (10 minutes)

**Goal**: Automate daily signal generation via cron triggers.

#### 7.1 Add Secrets to GitHub
1. Repository → Settings → Secrets and Variables → Actions
2. Add Repository Secrets:
   ```
   KOYEB_API_TOKEN=<from-koyeb-dashboard>
   TELEGRAM_CHAT_ID=123456789
   TELEGRAM_BOT_TOKEN=123456:ABC...
   API_BEARER_TOKEN=<same-as-koyeb-secret>
   ```

#### 7.2 Verify Workflow File
Check `.github/workflows/daily-signals.yml` exists:
```yaml
name: Daily Trading Signals (ASX)

on:
  schedule:
    - cron: '0 22 * * 0-4'  # 08:00 AEST Mon-Fri (Primary)
    - cron: '0 0 * * 1-5'   # 10:00 AEST Mon-Fri (Backup)
  workflow_dispatch:

jobs:
  trigger-asx-signals:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Koyeb Signal Endpoint
        run: |
          curl -X POST https://money.twoudia.com/cron/daily-signals?market=ASX \
            -H "Authorization: Bearer ${{ secrets.API_BEARER_TOKEN }}"
```

#### 7.3 Test Manual Trigger
1. Actions → "Daily Trading Signals (ASX)" → Run workflow
2. Check execution logs
3. Verify Telegram notification received

---

## ✅ Deployment Verification Checklist

### DNS & Domain
- [ ] `dig NS money.twoudia.top` shows Cloudflare nameservers (ns1.cloudflare.com, ns2.cloudflare.com)
- [ ] `https://money.twoudia.top/health` returns `{"status":"healthy"}`
- [ ] SSL certificate valid (Let's Encrypt from Cloudflare Proxy)
- [ ] CNAME is **Proxied** (🟠 orange cloud in Cloudflare DNS)

### 🔒 **PRIVACY VERIFICATION (CRITICAL for Family-Only Use)**
- [ ] `curl -I https://money.twoudia.top` shows `X-Robots-Tag: noindex, nofollow, noarchive, nosnippet, noimageindex`
- [ ] `https://money.twoudia.top/robots.txt` returns `User-agent: * Disallow: /`
- [ ] Admin dashboard `<head>` contains `<meta name="robots" content="noindex, nofollow">`
- [ ] **Cloudflare AI Bot Blocking**: Security → Bots → "AI Scrapers and Crawlers" toggle is **ON** (blue)
- [ ] **Cloudflare Proxy Status**: DNS record shows 🟠 orange cloud (Proxied)
- [ ] Google Search Console NOT configured (intentionally)
- [ ] Sitemap does NOT exist (intentionally - no `sitemap.xml`)
- [ ] **Domain Strategy**: Using money.twoudia.top (private domain family) NOT money.twoudia.com (public site)
- [ ] **Context**: This is a PRIVATE family-only trading bot. No public discovery allowed via:
  - **Network-Level Blocking** (Cloudflare AI Bot Blocking - FREE):
    - GPTBot, ClaudeBot, PerplexityBot, Bytespider, Google-Extended
    - Detects bots even when they spoof user agents (ML-powered)
  - **Application-Level Blocking** (robots.txt + HTTP headers):
    - Traditional search engines (Google, Bing, Yahoo, DuckDuckGo, Baidu, Yandex)
    - Archive services (Internet Archive, Wayback Machine)

### Database
- [ ] Supabase project status: **Active**
- [ ] 4 tables created: signals, job_logs, config_profiles, api_credentials
- [ ] Default ASX profile inserted

### Storage
- [ ] R2 bucket `trading-bot-backups` exists
- [ ] API tokens created and saved in Koyeb secrets

### Bot Service
- [ ] Koyeb service status: **Running** or **Sleeping** (idle)
- [ ] Health check passing: `/health` endpoint
- [ ] Auto-stop configured: 5 min idle timeout
- [ ] Light Sleep enabled: 200ms wake time

### Notifications
- [ ] Telegram bot responds to `/start`
- [ ] Test notification sent successfully

### GitHub Actions
- [ ] Secrets configured in repository
- [ ] Manual workflow trigger successful
- [ ] Cron schedule set for 08:00 AEST Mon-Fri

---

## 🎯 Post-Deployment Testing

### Test 1: Manual Signal Generation
```bash
curl -X POST https://money.twoudia.top/cron/daily-signals?market=ASX \
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

### Test 2: Admin Dashboard
1. Open: https://money.twoudia.top/admin/ui
2. Verify signal history displayed
3. Check job execution logs

### Test 3: Database Query
```sql
-- In Supabase SQL Editor
SELECT * FROM signals WHERE market='ASX' ORDER BY date DESC LIMIT 10;
SELECT * FROM job_logs ORDER BY timestamp DESC LIMIT 5;
```

### Test 4: Auto-Stop/Wake
1. Wait 5 minutes (no requests)
2. Service should enter "Sleeping" state in Koyeb dashboard
3. Make new request: `curl https://money.twoudia.top/health`
4. Service wakes in ~200ms (Light Sleep enabled)

### Test 5: Cloudflare AI Bot Blocking (Privacy Verification)
```bash
# Check Cloudflare proxy is active
curl -I https://money.twoudia.top | grep -i "cf-ray"
# Expected: cf-ray: xxx-SIN (confirms Cloudflare proxy)

# Verify robots.txt accessible
curl https://money.twoudia.top/robots.txt
# Expected: User-agent: * Disallow: /

# Check HTTP security headers
curl -I https://money.twoudia.top | grep -i "x-robots-tag"
# Expected: x-robots-tag: noindex, nofollow, noarchive, nosnippet, noimageindex
```

---

## 📊 Cost Summary

| Service | Plan | Cost |
|---------|------|------|
| **Koyeb Compute** | eSmall (30h/month) | **$0.22/month** |
| Supabase PostgreSQL | Free (500MB, always-on) | $0.00 |
| Cloudflare R2 | Free (10GB) | $0.00 |
| Cloudflare DNS | Free | $0.00 |
| Telegram Bot API | Free (unlimited) | $0.00 |
| GitHub Actions | Free (2000 min/month) | $0.00 |
| **Total** | | **$0.22/month** |

**Annual Cost**: $2.64/year 🎉

---

## 🔧 Maintenance Tasks

### Daily (Automated)
- ✅ Signal generation (08:00 AEST via GitHub Actions)
- ✅ Telegram notifications
- ✅ Database backup to R2

### Weekly
- Check GitHub Actions execution logs
- Verify no failed jobs

### Monthly
- Review Koyeb usage dashboard (should be ~30 hours)
- Verify Supabase storage usage (<50MB expected)
- Check R2 backup retention (30-day rolling)

### Quarterly
- Update dependencies: `pip install --upgrade -r requirements.txt`
- Review and archive old job_logs (>90 days)

---

## 🆘 Troubleshooting

### Issue: Health check fails
**Symptom**: `/health` returns 500 error
**Solution**:
1. Check Koyeb logs: Service → Logs
2. Verify DATABASE_URL secret is correct
3. Test database connection manually

### Issue: No Telegram notifications
**Symptom**: Signals generated but no message
**Solution**:
1. Verify TELEGRAM_BOT_TOKEN secret
2. Check bot is not blocked in Telegram
3. Verify TELEGRAM_CHAT_ID is correct

### Issue: Domain not resolving
**Symptom**: `money.twoudia.top` doesn't work
**Solution**:
1. Verify NS records at DNS provider: `dig NS money.twoudia.top`
2. Check Cloudflare CNAME record points to Koyeb domain
3. Verify CNAME is **Proxied** (🟠 orange cloud)
4. Wait 5-30 minutes for DNS propagation

### Issue: Cloudflare AI bot blocking not working
**Symptom**: AI bots still crawling site
**Solution**:
1. Verify CNAME is **Proxied** (🟠 orange cloud) - AI blocking ONLY works with proxy
2. Security → Bots → "AI Scrapers and Crawlers" toggle is ON (blue)
3. Check Cloudflare Analytics → Security Events to see blocked bots

### Issue: Auto-stop not working
**Symptom**: Service always running
**Solution**:
1. Koyeb Dashboard → Service → Settings
2. Verify auto-stop enabled: 5 min idle
3. Ensure Light Sleep enabled

---

## ✅ Why Dockerfile vs Buildpacks?

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

---

## 📚 Reference Links

- **Koyeb Docs**: https://www.koyeb.com/docs
- **Supabase Docs**: https://supabase.com/docs
- **Cloudflare R2 Docs**: https://developers.cloudflare.com/r2/
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **GitHub Actions Cron**: https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule

---

**Deployment Complete!** 🚀

 Your AI Trading Bot is now live at `https://money.twoudia.top` with:
- **PRIVACY PROTECTED**: Cloudflare AI bot blocking + robots.txt + HTTP headers
  - Network-level blocking of GPTBot, ClaudeBot, PerplexityBot, Bytespider, etc.
  - Detects AI crawlers even when they spoof user agents
  - Using private domain family (.top) for lower crawler attention
- Daily automated signal generation (08:00 AEST Mon-Fri)
- Telegram notifications (family-only)
- Always-on database (Supabase PostgreSQL)
- Auto-stop compute (Koyeb) to save costs
- Automated backups to Cloudflare R2

**Total setup time**: ~75 minutes (added Cloudflare AI blocking setup)  
**Ongoing cost**: $0.22/month ($2.64/year)

**Privacy Verification**:
```bash
# Confirm Cloudflare proxy active
curl -I https://money.twoudia.top | grep cf-ray

# Verify AI bot blocking enabled
# Cloudflare Dashboard → Security → Bots → "AI Scrapers and Crawlers" ON
```
