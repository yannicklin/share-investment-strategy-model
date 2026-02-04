# Infrastructure & Deployment Stack Comparison

**Companion Document:** See [bot_trading_system_requirements.md](bot_trading_system_requirements.md) for functional requirements and 3-thread operational architecture.

---

## PRIMARY RECOMMENDATION (Updated Feb 4, 2026)

### **Fly.io Sydney - $3.50 AUD/month** ⭐⭐⭐⭐⭐

**Optimized for: On-Demand Web UI + Auto-Suspend Cron Jobs**

```yaml
Single Machine (shared-cpu-1x, 1GB RAM):
  Location: Sydney, Australia (50ms to ASX data)
  Billing: Per-second when RUNNING (auto-suspend = massive savings)
  
Thread 1 - Daily Signal Cron (Dual Triggers for Reliability):
  - First attempt: 08:00 AEST (GitHub Actions cron)
  - Second attempt: 10:00 AEST (backup trigger)
  - Runs Python script (~30 min first run, ~5 sec if already done)
  - RAM usage: ~470MB (47% utilization)
  - Idempotent execution (no duplicate signals)
  - Auto-suspends after completion
  
Thread 2 - Web UI (On-Demand):
  - Visit: https://asx-bot.fly.dev (no CLI needed)
  - Automatic wake-up: Fly.io proxy boots machine on URL access
  - Cold start: 10-20 seconds ✅
  - RAM usage: ~280MB (28% utilization)
  - Auto-suspends after 5 min idle
  
Thread 3 - Weekly Retrain + Backup (Saturday 02:00):
  - Auto-wake via GitHub Actions cron trigger
  - Trains 5 models (~2 hours)
  - Database backup to Tigris (~5 min, encrypted AES-256)
  - RAM usage: ~800MB peak (80% utilization - adequate)
  - Saves to Tigris Object Storage (integrated)
  - Auto-suspends after completion

Active Compute Time: ~22 hours/month (3% uptime)
  - Thread 1 (dual triggers): 10 hours/month
  - Thread 2 (on-demand UI): 4 hours/month  
  - Thread 3 (weekly retrain): 8 hours/month
Suspended Time: ~698 hours/month (97% - NO compute charges)

Database: Supabase PostgreSQL (FREE 500MB)
Storage: Tigris Object Storage (FREE 5GB, S3-compatible)
Email: SendGrid (FREE 100 emails/day)
SMS: Telnyx (150 SMS/month = $3 AUD)

Monthly Cost Breakdown:
  Fly.io Compute (22 hours × $0.01/hour): $0.22
  Fly.io Disk (1GB persistent volume): $0.15
  Telnyx SMS (150 messages): $3.00
  Storage (Tigris): FREE
  Database (Supabase): FREE
  Email (SendGrid): FREE
  Cron Triggers (GitHub Actions): FREE
  
TOTAL: $3.37 AUD/month → rounded to $3.50
3-Year Total: $121 AUD → rounded to $126 (conservative estimate)

Alternative (Telegram instead of SMS): $0.50 AUD/month = $18 over 3 years
```

**Why Fly.io Wins:**
- ✅ **CHEAPEST**: $3.50/month (96% cheaper than 24/7 alternatives due to auto-suspend)
- ✅ **Sydney Region**: 50ms latency (vs 180ms US-based platforms)
- ✅ **Fast Cold Start**: 10-20 sec (acceptable for on-demand UI, automatic wake-up)
- ✅ **Per-Second Billing**: Only pay for 22 hours/month active time (vs 720 hours 24/7)
- ✅ **Right-Sized RAM**: 1GB handles all 3 threads comfortably (47-80% utilization)
- ✅ **Docker-Based**: Portable to any platform (no vendor lock-in)
- ✅ **Integrated Storage**: Tigris S3-compatible (FREE 5GB)
- ✅ **Dual Trigger Reliability**: 99.9%+ signal delivery (08:00 + 10:00 daily triggers)

**How Auto-Suspend Saves 96%:**
```yaml
Without Auto-Suspend (24/7 running):
  720 hours/month × $0.01/hour = $7.20/month

With Auto-Suspend (optimized workload):
  22 hours/month × $0.01/hour = $0.22/month ✅
  
Savings: $6.98/month ($251 over 3 years)
```

**Alternative Scenarios:**
- **If you want 24/7 always-on dashboard**: $7.50/month (720 hours active)
- **If you want zero Docker**: Render.com $6/month (native Python, US region, always-on)
- **If you want full SSH control**: BinaryLane VPS $8/month (Sydney, 24/7 running)

---

## 6. Infrastructure & Deployment

### 6.1 Infrastructure Requirements (Platform-Agnostic)

**Compute Requirements (Per Thread):**

Thread 1 (Daily Signals):
- Cron-compatible scheduler
- Python 3.12+ runtime
- 512MB RAM for inference (50 stocks × 5 models)
- Auto-suspend after ~30 min execution

Thread 2 (Web UI):
- HTTP server (Streamlit on port 8501)
- On-demand wake (10-20 sec cold start acceptable)
- 512MB RAM for dashboard
- Auto-suspend after 5 min idle

Thread 3 (Weekly Retrain):
- Heavy compute (1GB RAM minimum required)
- Cron trigger Saturday 02:00 AEST
- ~2 hours active time per week
- Auto-suspend after training completes

Total Active Time: ~27 hours/month (3.75% uptime)
Total Suspended Time: ~693 hours/month (96.25% - no compute charges)

**RAM Requirements Verification (50 stocks workload):**

```yaml
Thread 1 - Daily Signals:
  Load models: 300MB
  Fetch data: 50MB
  Inference: 50MB
  Overhead: 70MB
  PEAK: ~470MB (47% of 1GB) ✅ COMFORTABLE

Thread 2 - Web UI:
  Streamlit: 120MB
  Data: 30MB
  Charts: 80MB
  Overhead: 50MB
  PEAK: ~280MB (28% of 1GB) ✅ VERY COMFORTABLE

Thread 3 - Weekly Retrain:
  Data: 150MB
  Features: 100MB
  LSTM training (largest model): 400MB
  TensorFlow backend: 150MB
  PEAK: ~800MB (80% of 1GB) ✅ ADEQUATE (20% safety margin)
  
Note: Models train SEQUENTIALLY, not parallel
Upgrade to 2GB if: scaling to 100+ stocks or parallel training
```

**Database Requirements:**
- PostgreSQL or MongoDB compatibility
- <100MB storage for portfolio tracking
- Automated backups with point-in-time recovery
- Encryption at rest

**Storage Requirements:**
- Object storage for AI model artifacts (.pkl, .h5 files)
- 10-50GB for model versioning and backups
- S3-compatible API preferred

**Notification Requirements:**
- Email service (3,000+ emails/month capacity)
- SMS service (optional, for critical alerts)
- Webhook support (Slack, Discord, Telegram)

---

### 6.2 Email & SMS Services (Platform-Agnostic)

**All platforms (Fly.io, Render, Railway, etc.) require EXTERNAL notification services.**

#### 6.2.1 Email Services (FREE Options)

**Recommended: SendGrid**
```yaml
Free Tier: 100 emails/day (3,000/month)
Cost: $0 forever
Features:
  - Reliable deliverability (~99%)
  - Simple REST API + Python SDK
  - Email tracking & analytics
  - DKIM/SPF authentication

Setup:
  pip install sendgrid
  
Python Example:
  import sendgrid
  from sendgrid.helpers.mail import Mail
  
  message = Mail(
      from_email='bot@yourdomain.com',
      to_emails='you@gmail.com',
      subject='ASX BOT: BUY Signal - CBA.AX',
      html_content='<strong>BUY CBA.AX @ $115.50 (Confidence: 82%)</strong>'
  )
  
  sg = sendgrid.SendGridAPIClient(api_key=os.environ['SENDGRID_API_KEY'])
  response = sg.send(message)
```

**Alternatives:**
- **Mailgun**: FREE 5,000 emails/month
- **Resend**: FREE 3,000 emails/month (modern API)
- **AWS SES**: $0.10 per 1,000 emails (requires AWS account)

#### 6.2.2 SMS Services (Paid + FREE Options)

**Recommended: Telnyx (Cheapest Quality Provider)**
```yaml
Cost: $0.02 AUD per SMS to Australian mobiles
Monthly: 150 SMS = $3.00 AUD
3-Year Total: $108 AUD

Features:
  ✅ 55% cheaper than Twilio ($0.02 vs $0.045)
  ✅ Carrier-grade network (same quality as Twilio)
  ✅ Modern REST API + Python SDK
  ✅ Alphanumeric sender ID ("ASX-BOT")
  ✅ No monthly fees (pay-per-use)
  ✅ Free trial: $10 credit

Setup:
  pip install telnyx
  
Python Example:
  import telnyx
  
  telnyx.api_key = "YOUR_API_KEY"
  
  telnyx.Message.create(
      from_="ASX-BOT",  # Alphanumeric sender ID
      to="+61412345678",
      text="🟢 BUY CBA.AX @ $115.50 (Confidence: 82%)"
  )
```

**Price Comparison (150 SMS/month to AU mobiles):**
| Provider | Per SMS (AUD) | Monthly Cost | 3-Year Total | Notes |
|----------|---------------|--------------|--------------|-------|
| **Telnyx** (USA) | **$0.02** | **$3.00** | **$108** | ✅ Best value |
| BulkSMS (SA) | $0.022 | $3.30 | $119 | Prepaid credits |
| Sinch (Sweden) | $0.025 | $3.75 | $135 | Good for global |
| ClickSend (AU) | $0.033 | $4.95 | $178 | Australian company |
| MessageBird (NL) | $0.04 | $6.00 | $216 | Twilio alternative |
| Twilio (USA) | $0.045 | $6.75 | $243 | Most popular |
| Plivo (USA) | $0.04 | $6.00 | $216 | Similar to Twilio |

**FREE Alternative: Telegram Bot API**
```yaml
Cost: $0 (completely FREE, unlimited messages)
Delivery: Instant (faster than SMS)

Features:
  ✅ Rich formatting (bold, italics, code blocks)
  ✅ Send images/charts
  ✅ Interactive buttons
  ✅ No character limits (vs 160 chars for SMS)
  ✅ Works globally

Setup:
  1. Create bot via @BotFather on Telegram
  2. Get bot token
  3. Get your chat_id (send /start to bot)
  
Python Example:
  import requests
  
  telegram_token = "YOUR_BOT_TOKEN"
  chat_id = "YOUR_CHAT_ID"
  
  requests.post(
      f"https://api.telegram.org/bot{telegram_token}/sendMessage",
      json={
          "chat_id": chat_id,
          "text": "🟢 BUY CBA.AX @ $115.50\nConfidence: 82%\nTarget: $120",
          "parse_mode": "Markdown"
      }
  )
```

**Multi-Channel Strategy (Recommended):**
```yaml
Daily Summary: Email (SendGrid FREE)
High Confidence Signals (>75%): SMS (Telnyx $3/month)
All Signals + Charts: Telegram (FREE)

Total Cost: $3/month (or $0 if Telegram-only)
```

#### 6.2.3 Sender ID Configuration (SMS Anti-Blocking)

**To avoid SMS being blocked by Australian carriers:**

```yaml
Option 1: Alphanumeric Sender ID (RECOMMENDED)
  Format: "ASX-BOT" or "TradingBot" (up to 11 characters)
  Cost: FREE (included with Telnyx, Twilio, ClickSend)
  Pros:
    ✅ Professional appearance
    ✅ NOT blocked by Telstra/Optus
    ✅ No extra cost
  Cons:
    ❌ One-way only (can't receive replies)
  
Option 2: Dedicated Australian Number
  Format: +61 4XX XXX XXX (real AU mobile number)
  Cost: ~$1-2 AUD/month rental
  Pros:
    ✅ Two-way SMS (can receive replies)
    ✅ Looks like person texting
    ✅ Never blocked
  Cons:
    ❌ Extra monthly fee
  
  Providers:
    - Telnyx: $1.50 USD/month (~$2.25 AUD)
    - ClickSend: $1 AUD/month
    - MessageBird: €1/month (~$1.60 AUD)
```

**Anti-Spam Best Practices:**
- ✅ Keep volume <10 SMS/day to same number
- ✅ Send during business hours (avoid 11pm-7am)
- ✅ Don't use URL shorteners (bit.ly flagged as spam)
- ✅ Use alphanumeric sender ID (whitelisted by carriers)
- ✅ Include opt-out text if using dedicated number

---

### 6.3 Cron/Scheduled Triggers (Platform-Agnostic)

**Critical Limitation: Fly.io does NOT have native cron/EventBridge equivalent**

Unlike AWS (EventBridge), Google Cloud (Cloud Scheduler), or Railway (built-in cron), Fly.io requires **external trigger services** to wake machines on schedule.

---

#### 6.3.1 Option 1: GitHub Actions (RECOMMENDED) ⭐

```yaml
Cost: FREE (unlimited for public repos, 2,000 min/month for private)
Reliability: 99.9% uptime (GitHub SLA)
Setup Complexity: Easy (YAML configuration)

How it works:
  1. GitHub Actions runs on schedule
  2. Makes HTTP POST request to Fly.io app
  3. Fly.io machine wakes from suspend
  4. Executes scheduled task
  5. Auto-suspends after completion

Pros:
  ✅ Completely FREE (no cron service fees)
  ✅ Git-versioned schedule definitions
  ✅ Reliable (GitHub infrastructure)
  ✅ Easy to modify (edit YAML, push to repo)
  ✅ Preserves auto-suspend savings
  ✅ Works with any platform (not just Fly.io)
  
Cons:
  ❌ Requires GitHub repository
  ❌ 5-10 min delay possible (GitHub Actions queue)
  ❌ Not real-time (minimum 1-minute granularity)
```

**Setup Example:**

```yaml
# .github/workflows/daily-signals.yml
name: Daily ASX Signals
on:
  schedule:
    # DUAL TRIGGERS FOR RELIABILITY (2-hour gap)
    # First attempt:  08:00 AEST = 22:00 UTC (previous day), Monday-Friday
    - cron: '0 22 * * 0-4'
    # Second attempt: 10:00 AEST = 00:00 UTC, Tuesday-Saturday (backup)
    - cron: '0 0 * * 1-5'

jobs:
  trigger-daily-signals:
    runs-on: ubuntu-latest
    steps:
      - name: Wake Fly.io machine and trigger daily signals (idempotent)
        run: |
          curl -X POST https://asx-bot.fly.dev/cron/daily-signals \
            -H "Authorization: Bearer ${{ secrets.CRON_TOKEN }}" \
            -H "Content-Type: application/json"
            
      - name: Wait for job completion (optional)
        run: sleep 60
        
      - name: Check job status
        run: |
          curl https://asx-bot.fly.dev/api/job-status/latest

# .github/workflows/weekly-retrain.yml
name: Weekly Model Retraining
on:
  schedule:
    # Saturday 02:00 AEST = Friday 16:00 UTC
    - cron: '0 16 * * 5'

jobs:
  trigger-model-retrain:
    runs-on: ubuntu-latest
    steps:
      - name: Wake Fly.io machine and trigger retraining
        run: |
          curl -X POST https://asx-bot.fly.dev/cron/weekly-retrain \
            -H "Authorization: Bearer ${{ secrets.CRON_TOKEN }}" \
            -H "Content-Type: application/json"
```

**Flask API Endpoints (in your Fly.io app):**

```python
# api/cron_routes.py
from flask import Blueprint, request, jsonify
import os

cron_bp = Blueprint('cron', __name__, url_prefix='/cron')

CRON_TOKEN = os.environ.get('CRON_TOKEN')

def verify_cron_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return False
    token = auth_header.split('Bearer ')[1]
    return token == CRON_TOKEN

@cron_bp.route('/daily-signals', methods=['POST'])
def trigger_daily_signals():
    """Idempotent daily signal generation with dual-trigger reliability"""
    
    if not verify_cron_token():
        return jsonify({'error': 'Unauthorized'}), 401
    
    from datetime import datetime, date
    from core.database import get_db_connection
    
    today = date.today()
    db = get_db_connection()
    
    # STEP 1: Check if signal already calculated today
    existing_signal = db.execute('''
        SELECT id, signal, confidence, sent_at 
        FROM signals 
        WHERE date = %s AND job_type = 'daily'
    ''', (today,)).fetchone()
    
    if not existing_signal:
        # Calculate signal (30 min job)
        from core.signal_engine import generate_daily_signals
        result = generate_daily_signals()
        
        # Store in database
        db.execute('''
            INSERT INTO signals (date, signal, confidence, job_type, created_at)
            VALUES (%s, %s, %s, 'daily', NOW())
        ''', (today, result['signal'], result['confidence']))
        db.commit()
        
        signal_data = result
        already_calculated = False
    else:
        # Signal already exists (second trigger or retry)
        signal_data = {
            'signal': existing_signal['signal'],
            'confidence': existing_signal['confidence']
        }
        already_calculated = True
    
    # STEP 2: Check if signal already sent today
    sent_status = db.execute('''
        SELECT sent_at FROM signals 
        WHERE date = %s AND sent_at IS NOT NULL
    ''', (today,)).fetchone()
    
    if not sent_status:
        # Send notifications (email/SMS)
        from core.notifications import send_email, send_sms
        
        send_email(
            subject=f"ASX Signal: {signal_data['signal']} ({signal_data['confidence']}%)",
            body=f"Today's signal generated at {datetime.now()}"
        )
        send_sms(
            message=f"ASX: {signal_data['signal']} {signal_data['confidence']}%"
        )
        
        # Mark as sent
        db.execute('''
            UPDATE signals SET sent_at = NOW() WHERE date = %s
        ''', (today,))
        db.commit()
        
        already_sent = False
    else:
        # Notification already sent (second trigger or retry)
        already_sent = True
    
    return jsonify({
        'status': 'success',
        'date': str(today),
        'signal': signal_data['signal'],
        'confidence': signal_data['confidence'],
        'already_calculated': already_calculated,
        'already_sent': already_sent,
        'trigger_type': 'first' if not already_calculated else 'second_redundancy'
    })

@cron_bp.route('/weekly-retrain', methods=['POST'])
def trigger_weekly_retrain():
    if not verify_cron_token():
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Run model retraining (long-running task)
    from core.model_builder import retrain_all_models
    result = retrain_all_models()
    
    return jsonify({
        'status': 'success',
        'models_trained': result['model_count'],
        'duration_minutes': result['duration']
    })
```

**Security Setup:**

1. Generate secure CRON_TOKEN:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   # Output: abc123XYZ456...
   ```

2. Add to GitHub Secrets:
   - Go to repo Settings → Secrets → Actions
   - Add new secret: `CRON_TOKEN` = `abc123XYZ456...`

3. Add to Fly.io environment:
   ```bash
   flyctl secrets set CRON_TOKEN="abc123XYZ456..."
   ```

---

#### 6.3.2 Option 2: cron-job.org (Web UI Alternative)

```yaml
Cost: FREE (up to 50 jobs)
Reliability: 99.5% uptime
Setup: No code required (web UI only)

How it works:
  1. Sign up at cron-job.org
  2. Add job: https://asx-bot.fly.dev/cron/daily-signals
  3. Set schedule: Daily 22:00 UTC
  4. Add HTTP header: Authorization: Bearer <token>

Pros:
  ✅ No GitHub required
  ✅ Simple web UI (point-and-click)
  ✅ Email notifications on failure
  
Cons:
  ❌ Less reliable than GitHub Actions
  ❌ Not git-versioned (manual config)
  ❌ 50 job limit (FREE tier)
```

---

#### 6.3.3 Option 3: Railway/Render Native Cron (ALTERNATIVE PLATFORM)

**If you DON'T want external cron services, use Railway instead of Fly.io:**

```yaml
Railway.app Native Cron:
  Cost: $7.50/month (vs Fly.io $3.50 + GitHub FREE)
  Setup: railway.json configuration file
  
  {
    "deploy": {
      "cronJobs": [
        {
          "schedule": "0 22 * * 0-4",
          "command": "python signal_generator.py"
        },
        {
          "schedule": "0 16 * * 5",
          "command": "python model_trainer.py"
        }
      ]
    }
  }

Trade-off: Pay extra $4/month for built-in cron convenience

Pros:
  ✅ No external services needed
  ✅ Simple configuration
  ✅ Native platform integration
  
Cons:
  ❌ $4/month more expensive ($144 over 3 years)
  ❌ Vendor lock-in (Railway-specific config)
```

---

#### 6.3.4 Comparison with AWS EventBridge

| Feature | AWS EventBridge | Fly.io + GitHub Actions | Railway Native Cron |
|---------|----------------|------------------------|---------------------|
| **Native Integration** | ✅ Built-in | ❌ External service | ✅ Built-in |
| **Cost** | FREE (14M invocations) | FREE (GitHub Actions) | Included in $7.50 |
| **Reliability** | 99.99% SLA | 99.9% (GitHub) | 99.5% (Railway) |
| **Setup** | Medium (IAM, targets) | Easy (YAML + secret) | Easiest (JSON file) |
| **Vendor Lock-in** | ❌ AWS-only | ✅ Portable (HTTP) | ❌ Railway-only |
| **Min Frequency** | 1 minute | 1 minute (GitHub) | 1 minute |
| **Event-Driven** | ✅ Yes (not just cron) | ❌ Schedule-only | ❌ Schedule-only |

---

#### 6.3.5 Final Recommendation

**For Fly.io: Use GitHub Actions with DUAL DAILY TRIGGERS (Reliability Enhancement)**

```yaml
Total Stack Cost:
  Compute: Fly.io - $0.50/month
  Cron: GitHub Actions - FREE (dual triggers)
  SMS: Telnyx - $3/month
  Storage: Tigris - FREE
  Database: Supabase - FREE
  Email: SendGrid - FREE
  
Total: $3.50/month ($126 over 3 years)

Reliability Enhancement:
  ✅ 2 triggers per day (08:00 + 10:00 AEST)
  ✅ Idempotent endpoint (no duplicate signals)
  ✅ Fault-tolerant (catches GitHub Actions failures)
  ✅ Cost increase: ~$0.0003/month (negligible)
  
How it works:
  1. First trigger (08:00): Calculate + send signal
  2. Second trigger (10:00): Check if already done
     - If signal exists: Exit in 5 seconds (FREE)
     - If failed: Retry calculation + send
  
Cost Impact:
  - First trigger (new calculation): 30 min = $0.005
  - Second trigger (already done): 5 sec = $0.00001
  - Monthly overhead: 20 days × $0.00001 = $0.0002/month
  
Result: 99.9%+ delivery rate vs 99% with single trigger
  
TOTAL: $3.50/month = $126 over 3 years

Setup Time: 30 minutes (create workflows + add secret)
Complexity: Low (if comfortable with YAML)
```

**If you want zero external dependencies:**
- Use Railway ($7.50/month) with native cron
- Saves setup complexity, costs $144 more over 3 years

---

### 6.4 Backup & Restore Strategy

**All critical data stored in database (including sensitive configurations)**

---

#### 6.4.1 What Gets Backed Up

```yaml
PostgreSQL Database (Supabase):
  1. Portfolio State:
     - Current positions (ticker, quantity, entry_price, P&L)
     - Trade history (buy/sell transactions)
     
  2. Signal History:
     - BUY/SELL/HOLD signals (30 days retention)
     - Model consensus votes
     - Confidence scores
     
  3. Configuration (SENSITIVE):
     - Trading profiles (holding periods, hurdle rates)
     - Model settings (algorithms, hyperparameters)
     - Risk parameters (position sizing, stop-losses)
     - API credentials (broker tokens, notification keys)
     
  4. Job Execution Logs:
     - Cron job status (success/failure)
     - Error messages
     - Performance metrics

AI Models (Tigris Object Storage):
  - Trained model files (.pkl, .h5, .joblib)
  - Model metadata (accuracy, training date, feature importance)
```

---

#### 6.4.2 Automated Backup Schedule

**Primary: Supabase Auto-Backups (Daily)**
```yaml
Provider: Supabase (built-in)
Frequency: Daily (automatic)
Retention: 7 days (FREE tier)
Recovery Method: Point-in-time restore via dashboard
Cost: FREE

What's included:
  ✅ Full database snapshots
  ✅ Transaction logs (PITR)
  ✅ One-click restore
  
Limitations:
  ❌ Only 7 days retention (FREE tier)
  ❌ Cannot download backup files directly
  ❌ Restore requires Supabase dashboard access
```

**Secondary: Weekly Tigris Exports (Offline Backup)**
```yaml
Provider: Tigris Object Storage (Fly.io integrated)
Frequency: Weekly (Saturday 04:00 AEST, after model retraining)
Retention: 4 versions (1 month)
Recovery Method: Manual restore via Flask endpoint
Cost: FREE (within 5GB limit)

Trigger: GitHub Actions (same workflow as model retraining)

Backup Process:
  1. Export all database tables to JSON
  2. Compress (gzip)
  3. Encrypt (AES-256)
  4. Upload to Tigris: backups/db-YYYYMMDD.json.gz.enc
  5. Auto-delete backups older than 4 weeks

Benefits:
  ✅ Offline copy (survives Supabase account issues)
  ✅ Encrypted (sensitive configs protected)
  ✅ Downloadable (can restore to local dev)
  ✅ Version controlled (4 weekly snapshots)
```

---

#### 6.4.3 Backup Implementation (Flask Endpoints)

```python
# api/backup_routes.py
from flask import Blueprint, jsonify, request
import os
import json
import gzip
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from core.database import get_db_connection
from core.storage import upload_to_tigris, list_tigris_files, delete_from_tigris

backup_bp = Blueprint('backup', __name__, url_prefix='/admin/backup')

# Encryption key (stored in Fly.io secrets)
BACKUP_ENCRYPTION_KEY = os.environ.get('BACKUP_ENCRYPTION_KEY')
cipher = Fernet(BACKUP_ENCRYPTION_KEY)

@backup_bp.route('/create', methods=['POST'])
def create_backup():
    """Weekly database export to Tigris (encrypted)"""
    
    # 1. Export all tables from Supabase
    db = get_db_connection()
    
    backup_data = {
        'timestamp': datetime.now().isoformat(),
        'version': '1.0',
        'tables': {
            'portfolio': db.execute('SELECT * FROM portfolio').fetchall(),
            'signals': db.execute('SELECT * FROM signals WHERE created_at > NOW() - INTERVAL \'30 days\'').fetchall(),
            'config_profiles': db.execute('SELECT * FROM config_profiles').fetchall(),  # SENSITIVE
            'config_models': db.execute('SELECT * FROM config_models').fetchall(),
            'api_credentials': db.execute('SELECT * FROM api_credentials').fetchall(),  # SENSITIVE
            'job_logs': db.execute('SELECT * FROM job_logs WHERE created_at > NOW() - INTERVAL \'7 days\'').fetchall()
        }
    }
    
    # 2. Convert to JSON
    json_data = json.dumps(backup_data, default=str, indent=2)
    
    # 3. Compress (gzip)
    compressed = gzip.compress(json_data.encode('utf-8'))
    
    # 4. Encrypt (AES-256)
    encrypted = cipher.encrypt(compressed)
    
    # 5. Upload to Tigris
    filename = f"backups/db-{datetime.now().strftime('%Y%m%d')}.json.gz.enc"
    upload_to_tigris(filename, encrypted)
    
    # 6. Auto-delete old backups (keep only 4 versions)
    cleanup_old_backups()
    
    return jsonify({
        'status': 'success',
        'backup_file': filename,
        'size_mb': round(len(encrypted) / 1024 / 1024, 2),
        'encrypted': True
    })

def cleanup_old_backups():
    """Keep only the 4 most recent weekly backups"""
    
    # List all backup files
    all_backups = list_tigris_files(prefix='backups/db-')
    
    # Sort by filename (YYYYMMDD) descending
    all_backups.sort(reverse=True)
    
    # Delete backups beyond the 4th
    for old_backup in all_backups[4:]:
        delete_from_tigris(old_backup)
        print(f"Deleted old backup: {old_backup}")

@backup_bp.route('/restore', methods=['POST'])
def restore_backup():
    """Restore database from Tigris backup file"""
    
    backup_file = request.json.get('backup_file')  # e.g., "backups/db-20260204.json.gz.enc"
    
    # 1. Download from Tigris
    encrypted_data = download_from_tigris(backup_file)
    
    # 2. Decrypt
    compressed = cipher.decrypt(encrypted_data)
    
    # 3. Decompress
    json_data = gzip.decompress(compressed).decode('utf-8')
    
    # 4. Parse JSON
    backup_data = json.loads(json_data)
    
    # 5. Restore to database (with safety checks)
    db = get_db_connection()
    
    # Restore portfolio
    for row in backup_data['tables']['portfolio']:
        db.execute('''
            INSERT INTO portfolio (id, ticker, quantity, entry_price, current_price, unrealized_pl, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                quantity = EXCLUDED.quantity,
                entry_price = EXCLUDED.entry_price,
                current_price = EXCLUDED.current_price,
                unrealized_pl = EXCLUDED.unrealized_pl
        ''', tuple(row.values()))
    
    # Restore config_profiles (SENSITIVE)
    for row in backup_data['tables']['config_profiles']:
        db.execute('''
            INSERT INTO config_profiles (id, name, stocks, holding_period, hurdle_rate, max_position_size)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                stocks = EXCLUDED.stocks,
                holding_period = EXCLUDED.holding_period,
                hurdle_rate = EXCLUDED.hurdle_rate,
                max_position_size = EXCLUDED.max_position_size
        ''', tuple(row.values()))
    
    # ... (restore other tables)
    
    db.commit()
    
    return jsonify({
        'status': 'success',
        'restored_from': backup_file,
        'restored_timestamp': backup_data['timestamp'],
        'tables_restored': len(backup_data['tables'])
    })

@backup_bp.route('/list', methods=['GET'])
def list_backups():
    """List available backup files"""
    
    backups = list_tigris_files(prefix='backups/db-')
    backups.sort(reverse=True)  # Most recent first
    
    backup_info = []
    for backup_file in backups[:4]:  # Only show the 4 kept versions
        # Extract date from filename: db-20260204.json.gz.enc
        date_str = backup_file.split('db-')[1].split('.')[0]
        backup_info.append({
            'filename': backup_file,
            'date': date_str,
            'age_days': (datetime.now() - datetime.strptime(date_str, '%Y%m%d')).days
        })
    
    return jsonify({
        'backups': backup_info,
        'retention_policy': '4 weekly versions (1 month)'
    })
```

---

#### 6.4.4 GitHub Actions Backup Workflow

```yaml
# .github/workflows/weekly-backup.yml
name: Weekly Database Backup
on:
  schedule:
    # Saturday 04:00 AEST = Friday 18:00 UTC (after model retraining completes)
    - cron: '0 18 * * 5'

jobs:
  backup-database:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Fly.io backup endpoint
        run: |
          curl -X POST https://asx-bot.fly.dev/admin/backup/create \
            -H "Authorization: Bearer ${{ secrets.ADMIN_TOKEN }}" \
            -H "Content-Type: application/json"
            
      - name: Wait for backup completion
        run: sleep 60
        
      - name: List current backups
        run: |
          curl https://asx-bot.fly.dev/admin/backup/list \
            -H "Authorization: Bearer ${{ secrets.ADMIN_TOKEN }}"
```

---

#### 6.4.5 Disaster Recovery Procedures

**Scenario 1: Accidental Data Deletion (< 7 days ago)**
```yaml
Method: Supabase Point-in-Time Restore (FASTEST)
Steps:
  1. Go to Supabase dashboard
  2. Navigate to Database → Backups
  3. Select timestamp (e.g., "2026-02-03 10:00 AEST")
  4. Click "Restore"
  5. Wait ~10 minutes for restore to complete

Recovery Time: 15 minutes ✅
Data Loss: None (exact point-in-time)
```

**Scenario 2: Database Corruption (> 7 days ago)**
```yaml
Method: Tigris Weekly Backup Restore
Steps:
  1. List available backups:
     curl https://asx-bot.fly.dev/admin/backup/list
     
  2. Choose backup file (e.g., backups/db-20260127.json.gz.enc)
  
  3. Trigger restore:
     curl -X POST https://asx-bot.fly.dev/admin/backup/restore \
       -H "Authorization: Bearer $ADMIN_TOKEN" \
       -d '{"backup_file": "backups/db-20260127.json.gz.enc"}'
  
  4. Verify restored data via dashboard

Recovery Time: 5 minutes ✅
Data Loss: Up to 7 days (weekly backup granularity)
```

**Scenario 3: Complete Supabase Account Loss (worst case)**
```yaml
Method: Download Tigris backup + restore to new Supabase instance
Steps:
  1. Create new Supabase project
  2. Download latest backup from Tigris
  3. Decrypt locally: 
     python decrypt_backup.py backups/db-20260204.json.gz.enc
  4. Import to new Supabase via psql or web UI
  5. Update Fly.io DATABASE_URL secret

Recovery Time: 1 hour ⚠️
Data Loss: Up to 7 days
```

---

#### 6.4.6 Security Considerations

**Encryption Setup:**
```bash
# Generate encryption key (one-time setup)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Output: gAAAAAB... (44 characters)

# Add to Fly.io secrets
flyctl secrets set BACKUP_ENCRYPTION_KEY="gAAAAAB..."

# Add to GitHub Secrets (for local decrypt if needed)
# GitHub repo → Settings → Secrets → BACKUP_ENCRYPTION_KEY
```

**Why Encryption is Critical:**
```yaml
Backup files contain:
  ✅ Trading strategy parameters (competitive advantage)
  ✅ Broker API credentials (sensitive)
  ✅ Email/SMS API keys (sensitive)
  ✅ Historical positions (financial privacy)

Without encryption:
  ❌ Anyone with Tigris access sees all configs
  ❌ Leaked backups expose broker credentials
  
With encryption (AES-256):
  ✅ Backups unreadable without BACKUP_ENCRYPTION_KEY
  ✅ Even Fly.io employees cannot decrypt
  ✅ Safe to store in cloud storage
```

---

#### 6.4.7 Backup Cost Impact

```yaml
Current Total: $3.50/month

With Backup Strategy:
  Supabase auto-backups: FREE (included in FREE tier)
  Tigris storage (4 weekly backups):
    - Estimated size: ~50MB per backup × 4 = 200MB
    - Cost: FREE (within 5GB limit)
  GitHub Actions (weekly backup job):
    - Runtime: ~1 minute/week = 4 min/month
    - Cost: FREE (within 2,000 min/month limit)
  
TOTAL: Still $3.50/month (no cost increase!) ✅
```

---

**See [infrastructure_stack_comparison.md](infrastructure_stack_comparison.md) for:**
- Detailed platform comparisons (Render, Fly.io, Railway, BinaryLane VPS, AWS, etc.)
- Cost analysis over 3 years
- OpenClaw co-location strategies
- Security checklists
- ASX-specific deployment considerations

---

## 7. Success Metrics

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
- **Cost per Signal**: Cloud execution cost <AUD 1 per signal generated

---

## 8. Development Phases
```yaml
Compute:
  - AWS Lambda (Serverless Functions)
    - Signal generation jobs (1 million free requests/month)
    - Model inference execution
    - API endpoint handlers
    - EventBridge cron triggers (free)
    
Database:
  - AWS RDS PostgreSQL (db.t3.micro Free Tier eligible)
    - Portfolio state tracking
    - Job execution history
    - Signal archive
    - Automated backups (7-day retention)
    
Message Queue:
  - AWS SQS (Simple Queue Service)
    - Free Tier: 1M requests/month
    - More cost-effective than ElastiCache Redis for async tasks
    - Dead-letter queue for failed jobs
    
Object Storage:
  - AWS S3 (5GB free storage)
    - Model artifacts (.pkl, .h5 files)
    - Daily backup exports (portfolio snapshots)
    - Configuration history (YAML versions)
    
Logging & Monitoring:
  - AWS CloudWatch Logs (Free Tier: 5GB ingestion)
  - AWS CloudWatch Alarms (10 free alarms/month)
  - Custom metrics for signal accuracy tracking
```

#### 6.2.2 Notification Stack (Global Email/SMS)
```yaml
Email Service:
  - AWS SES (Simple Email Service)
    - 3,000 free emails/month (when sent from EC2/Lambda)
    - Highly reliable (~99.99% deliverability)
    - Supports Australia + global regions
    - DKIM/SPF authentication built-in
    
SMS Service (Multi-Provider for Redundancy):
  Primary:
    - AWS SNS (Simple Notification Service)
      - AU/Global coverage via Telstra/Optus routes
      - ~$0.045 AUD per SMS (Australian numbers)
      - Direct integration with Lambda
      
  Backup (Cost-Effective Alternative):
    - Twilio SendGrid (Email - 100 emails/day free)
    - Twilio SMS (Pay-as-you-go, fallback for critical alerts)
    
Webhook Integrations (FREE):
  - Slack Incoming Webhooks
  - Discord Webhooks
  - Telegram Bot API
```

#### 6.2.3 Authentication & Security
```yaml
User Authentication:
  - AWS Cognito User Pools (FREE for <50,000 MAU)
    - Multi-factor authentication (TOTP/SMS)
    - Email verification
    - Password policies (complexity requirements)
    - OAuth 2.0 / SAML support
    
Secrets Management:
  - AWS Secrets Manager
    - Broker API keys
    - Database credentials
    - Email/SMS API tokens
    - Auto-rotation for RDS passwords
    - $0.40/secret/month + $0.05 per 10,000 API calls
    
API Security:
  - AWS API Gateway (1M API calls/month free)
    - API key authentication
    - Request throttling (prevent abuse)
    - CORS policies
    - WAF integration (optional, for DDoS protection)
    
Network Security:
  - AWS VPC (Virtual Private Cloud)
    - Private subnets for RDS database
    - Security groups (whitelist IP ranges)
    - No direct internet access to DB
```

#### 6.2.4 Data Backup & Recovery
```yaml
Primary Backups:
  - RDS Automated Backups (FREE - 7 days retention)
    - Daily snapshots at 3 AM TST
    - Point-in-time recovery (restore to any second)
    - Cross-region replication (optional, for disaster recovery)
    
Offline Backups:
  - Daily S3 Export (Lambda-triggered)
    - Portfolio data → JSON/CSV → S3
    - Configuration history → YAML → S3 versioned bucket
    - Model artifacts → .pkl/.h5 → S3 Standard-IA (cheaper long-term storage)
    
Backup Encryption:
  - S3 Server-Side Encryption (SSE-S3, free)
  - RDS encryption at rest (using AWS KMS, minimal cost)
    
Restore Procedure:
  1. RDS: One-click restore from snapshot (< 10 minutes)
  2. S3: Download JSON/CSV, import via admin script
  3. Models: Restore .pkl files to Lambda deployment package
```

---

### 6.3 Deployment Strategy: BOT vs. OpenClaw Separation

#### 6.3.1 Isolation Architecture (RECOMMENDED)
```
┌─────────────────────────────────────────────┐
│          BOT Intelligence System            │
│  (AWS Lambda + RDS + SQS + S3)             │
│  - Generates BUY/HOLD/SELL signals         │
│  - Publishes to SQS queue                   │
│  - NO direct access to broker APIs          │
└──────────────────┬──────────────────────────┘
                   │ JSON Signal Messages
                   │ (via SQS / REST API)
                   ▼
┌─────────────────────────────────────────────┐
│      OpenClaw Trading Agent (Separate)      │
│  (Dedicated EC2 / On-Premise Server)       │
│  - Consumes signals from BOT system         │
│  - Executes trades via broker APIs          │
│  - Manages live capital & positions         │
│  - Reports execution status back to BOT     │
└─────────────────────────────────────────────┘
```

**Rationale for Separation**:
1. **Blast Radius Containment**: If BOT system has a bug, it CANNOT accidentally execute trades
2. **Security**: Broker API keys ONLY stored in OpenClaw environment, never in BOT Lambda
3. **Independent Scaling**: BOT can analyze 100 stocks; OpenClaw only acts on 2-3 signals
4. **Audit Compliance**: Clear separation between "recommendation engine" and "execution engine"
5. **Development Safety**: You can test/redeploy BOT system without risking live trading

#### 6.3.2 Security Boundaries
```yaml
BOT System Permissions:
  ✅ Read market data (yfinance .AX tickers, ASX Data API)
  ✅ Write to SQS queue (signal publishing)
  ✅ Read/write RDS (portfolio tracking)
  ✅ Send emails/SMS (notifications)
  ❌ NO access to broker APIs
  ❌ NO ability to execute trades
  
OpenClaw Agent Permissions:
  ✅ Read from SQS queue (signal consumption)
  ✅ Access broker APIs (CommSec/IBKR/SelfWealth)
  ✅ Report execution status to BOT (via webhook)
  ⚠️  Rate-limited API calls (prevent runaway orders)
  ⚠️  Trade amount caps (max AUD per order)
  ⚠️  Chess sponsorship compliance
```

#### 6.3.3 Communication Protocol
```python
# BOT System publishes signal
signal = {
    "signal_id": "20260204-CBA-BUY-001",
    "timestamp": "2026-02-04T10:00:00+11:00",  # AEDT (Australian Eastern Daylight Time)
    "ticker": "CBA.AX",  # Commonwealth Bank
    "action": "BUY",
    "confidence": 0.82,
    "target_price": 115.50,
    "stop_loss": 109.80,
    "reasoning": {
        "models_vote": {"rf": 1, "xgb": 1, "lstm": 1, "prophet": 0, "catboost": 1},
        "consensus": "4/5 models agree",
        "key_features": ["dividend_yield", "rsi_oversold", "volume_spike"]
    }
}

# OpenClaw Agent consumes signal, validates, and executes
execution_report = {
    "signal_id": "20260204-CBA-BUY-001",
    "executed_at": "2026-02-04T10:05:32+11:00",
    "status": "SUCCESS",
    "entry_price": 114.75,
    "quantity": 100,  # ASX allows 1 share minimum (no lot system)
    "brokerage_fee": 19.95,  # CommSec standard fee
    "broker": "CommSec"
}
```

---

### 6.4 Local Development Environment
```bash
# Docker Compose Setup (Single Command)
services:
  bot-engine:
    build: .
    environment:
      - DATABASE_URL=postgresql://bot:password@db:5432/botdb
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
      
  db:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
      
  redis:
    image: redis:7-alpine
    
  streamlit-ui:
    build: .
    command: streamlit run ui_bot/dashboard.py
    ports:
      - "8501:8501"

# Makefile Commands
make dev         # Start local Docker environment
make test        # Run pytest suite
make deploy-prod # Deploy to AWS (Terraform apply)
make backup      # Export portfolio data to S3
```

---

### 6.5 Honest Provider Comparison (Taiwan Trading Bot Use Case)

#### Scenario: 20 ASX stocks monitored, daily signals, 5 users

---

### **Option 1: VPS (BinaryLane / Hetzner) - SIMPLEST & CHEAPEST** ⭐⭐⭐⭐⭐

#### BinaryLane (Sydney, Australia) - **RECOMMENDED FOR ASX TRADERS**
```yaml
Plan: Standard 1GB RAM (Minimal) ⚡ SUFFICIENT FOR 50+ STOCKS
Cost: $8 AUD/month (cheapest plan, fixed pricing)

Specs:
  - 1 vCPU, 1GB RAM, 30GB NVMe SSD
  - Sydney datacenter (low latency to AU brokers)
  - Daily backups included
  - 1TB monthly transfer
  - 99.9% uptime SLA

Why 1GB RAM is Enough:
  - Inference (not training) runs in <100MB RAM per stock
  - 50 stocks × 100MB = 5GB theoretical max, BUT:
    → Process stocks sequentially (not parallel) = 100MB RAM usage
    → PostgreSQL uses ~50MB for small portfolio DB
    → Python + dependencies: ~150MB
    → TOTAL: ~300MB active RAM usage (70% headroom)
  
  - Model training (weekly):
    → Happens overnight (low memory pressure)
    → scikit-learn RandomForest: ~200MB for 2 years ASX data
    → Even with 50 stocks, models train sequentially
  
  - Upgrade path:
    → If you scale to 200+ stocks → $12/month 2GB plan
    → If you add real-time tick data → $24/month 4GB plan
    → But for daily EOD signals? 1GB is perfect.

Upgrade Option (If Needed Later):
  Plan: Standard 2GB RAM
  Cost: $12 AUD/month
  Specs: 2 vCPU, 2GB RAM, 60GB NVMe SSD

Tech Stack (Single Server):
  - PostgreSQL (installed on VM)
  - Python + Streamlit dashboard
  - Nginx reverse proxy
  - Systemd for cron jobs
  - Fail2ban for security
  - SSL via Let's Encrypt (free)

Notification Options:
  - SMTP via SendGrid (100 emails/day FREE)
  - Twilio SMS ($0.045 AUD/SMS)
  - Telegram Bot API (FREE, unlimited)

TOTAL MONTHLY COST: $8-15 AUD ✅ CHEAPEST SOLUTION
  - Base VPS (1GB): $8 AUD
  - SMS (150/month): $6.75 AUD (optional, can use Telegram FREE)
  - Email: FREE (SendGrid)
  - TOTAL: ~$15 AUD/month ALL-IN (or $8 if using free Telegram)

Computational Load Reality Check:
  - 50 ASX stocks × 5 models × 2 min inference = 500 minutes/month
  - That's 8.3 hours of CPU time spread over 30 days
  - 1 vCPU handles this at <1% average utilization
  - Even with 3 profiles (150 stock-model combinations) = still <3% CPU

PROS ✅:
  ✅ Predictable fixed cost (no usage spikes)
  ✅ Full control (install anything, debug easily)
  ✅ Simple architecture (no AWS service maze)
  ✅ Australian company (ACCC regulated, AUD billing)
  ✅ Low latency to ASX/Taiwan brokers
  ✅ Easy SSH access for troubleshooting
  ✅ Can run OpenClaw on SAME server (isolated Docker containers)
  ✅ No "free tier expiration" surprise after 12 months
  ✅ Easier for solo developers (no DevOps expertise needed)

CONS ❌:
  ❌ Manual OS patching (apt update/upgrade)
  ❌ You manage backups (automate via rsync/rclone)
  ❌ Single point of failure (if server dies, downtime until restore)
  ❌ Scaling requires manual server upgrade
  ❌ No auto-scaling (but you don't need it for 20 stocks)
```

#### Hetzner (Germany) - **CHEAPEST, BUT EUROPE-BASED**
```yaml
Plan: CX22 (Falkenstein, Germany)
Cost: €5.83/month (~$9.50 AUD)

Specs:
  - 2 vCPU, 4GB RAM, 40GB SSD
  - AMAZING value (50% cheaper than BinaryLane)
  - 20TB monthly transfer

PROS ✅:
  ✅ CHEAPEST option globally
  ✅ Excellent reputation (German engineering)
  ✅ Same VPS benefits as BinaryLane

CONS ❌:
  ❌ Germany location (200ms+ latency to ASX, 250ms+ to AU brokers)
  ❌ EUR billing (currency conversion fees)
  ❌ EU data residency (may complicate AU compliance/ASIC)
  ❌ No AU support hours (CEST timezone, 8-10 hours behind AEST)
```

---

### **Option 2: Cloudflare Workers + R2 - HYBRID SERVERLESS** ⭐⭐⭐

### **CRITICAL CORRECTION: AWS Free Tier Only for NEW Accounts**

**Reality Check**: If you've EVER created an AWS account before, there's NO free tier. Here's the REAL cost from Day 1:

```yaml
AWS Lambda + RDS (FULL PRICING, No Free Tier):

RDS PostgreSQL db.t3.micro:
  - 720 hours/month × $0.025 USD/hour = $18 USD/month (~$27 AUD)
  
Lambda:
  - 500 requests/month × $0.0000002/request = $0.0001 USD
  - 5,000 GB-seconds/month × $0.0000166667/GB-sec = $0.08 USD
  - Total: ~$0.10 USD/month (~$0.15 AUD) ✅ MINIMAL
  
S3:
  - 1GB storage × $0.023/GB = $0.023 USD (~$0.04 AUD)
  
CloudWatch Logs:
  - 500MB × $0.50/GB = $0.25 USD (~$0.40 AUD)
  
Secrets Manager:
  - 5 secrets × $0.40/month = $2.00 USD (~$3 AUD)
  
Data Transfer Out:
  - ~100MB/month = $0.01 USD
  
ACTUAL MONTHLY COST (From Day 1):
  - RDS: $27 AUD (biggest cost!)
  - Lambda: $0.15 AUD
  - S3: $0.04 AUD
  - CloudWatch: $0.40 AUD
  - Secrets Manager: $3 AUD
  - SMS: $9 AUD (or FREE Telegram)
  
TOTAL: $30-40 AUD/month (ALL YEARS)
```

**AWS is now 4-5x MORE expensive than Railway ($7.50) with NO advantages for your light workload.**

---

### **REVISED HONEST COMPARISON (Full Pricing, All Years)**

| Option | Monthly Cost | 3-Year Total | Setup Time | Complexity |
|--------|--------------|--------------|------------|------------|
| **Railway.app** | **$7.50 AUD** | **$270** | 1 hour | ⭐ Easy |
| **BinaryLane VPS 1GB** | $8 AUD | $288 | 2 hours | ⭐⭐ Medium |
| **AWS Lambda + RDS** | $30-40 AUD | **$1,080-1,440** | 2 days | ⭐⭐⭐⭐⭐ Hard |
| **Cloudflare + Supabase** | $0 AUD | **$0** | 1 week (JS port) | ⭐⭐⭐ Medium |

**AWS went from "best" to WORST option when free tier doesn't apply.** 😬

---

### **NEW FINAL RECOMMENDATION: Railway.app** 🏆

**Why Railway Wins (No Free Tier Fairy Tale):**

```yaml
Railway.app ($7.50 AUD/month fixed):
  ✅ Native Python (no code changes)
  ✅ 24/7 Streamlit dashboard included
  ✅ Auto-sleeps when idle (not paying for 98.9% idle time)
  ✅ Supabase PostgreSQL (FREE 500MB, managed)
  ✅ GitHub auto-deploy (90 seconds to production)
  ✅ Simple (one service, not 10 AWS services)
  ✅ Predictable ($7.50 forever, no surprise bills)
  
  vs AWS:
  ❌ AWS costs 4x more ($30 vs $7.50)
  ❌ AWS takes 2 days to learn vs 1 hour
  ❌ AWS has 10+ services to manage vs Railway's 1
  ❌ AWS billing surprises common (forgot to turn off RDS? $27/month)
```

**For 50 stocks × daily signals:**
- Railway: $270 over 3 years
- AWS: $1,080-1,440 over 3 years
- **You save $810-1,170 with Railway**

---

### **When AWS Still Makes Sense (Rare Cases):**
- [ ] You have a NEW AWS account (actually get free tier)
- [ ] You're scaling to 500+ stocks (need auto-scaling)
- [ ] Your employer pays (not your personal budget)
- [ ] You're building a SaaS product for clients (need enterprise SLAs)

**For personal ASX trading bot? Railway wins. Period.**

---

### **Alternative: Cloudflare Workers (FREE Forever)**

If you're willing to port Python → JavaScript:
```yaml
Cloudflare Workers + Supabase:
  - Compute: FREE (100K req/day)
  - Database: FREE (Supabase 500MB)
  - Storage: FREE (R2 10GB)
  - Total: $0/month forever
  
Effort:
  - 1 week to port scikit-learn → TensorFlow.js
  - OR: Train models locally, export JSON weights
```

**Verdict: If FREE matters more than 1 week of work, do it.**

---

### **Option 3: Railway.app Python Cron - $7.50 AUD/month (FIXED FOREVER)** ⭐⭐⭐⭐

```yaml
Stack:
  Compute: Railway.app ($5 USD = $7.50 AUD)
  Database: Supabase PostgreSQL (FREE, 500MB)
  Dashboard: Streamlit included (24/7 available)
  
Cost (Year 1, 2, 3... forever):
  - Railway: $7.50 AUD
  - SMS: $9 AUD (or FREE Telegram)
  TOTAL: $7.50-16 AUD (no surprises)
```

**PROS ✅**:
- ✅ **Predictable forever** ($7.50 Year 1 = Year 10)
- ✅ **Setup in 1 hour** (vs 2 days for AWS)
- ✅ **24/7 Streamlit dashboard** included
- ✅ **GitHub auto-deploy** (push → live in 90 seconds)
- ✅ **Simple mental model** (one service, not 10)

**CONS ❌**:
- ❌ 500MB RAM limit (fine for 50 stocks, tight for 200+)
- ❌ VC-backed startup (pricing could change)
- ❌ Year 1 costs MORE than AWS ($7.50 vs $0)

---

### **Option 4: Cloudflare Workers + Supabase - $0/month** ⭐⭐⭐

```yaml
Free Tier (Generous, NO EXPIRATION):
  Workers: 100,000 requests/day FREE
  R2 Storage: 10GB FREE
  D1 Database: 5M reads/day FREE
  
Paid (Workers Unbound):
  - $5 USD/month base (~$7.50 AUD)
  - $0.15 per million requests

Tech Stack:
  - Cloudflare Workers (signal generation cron)
  - R2 (model storage, cheaper than S3)
  - D1 SQLite (portfolio tracking, free tier likely sufficient)
  - Workers KV (config storage)
  - Email Workers (send via SMTP relay)

TOTAL MONTHLY COST: $7-12 AUD
  - Workers: $7.50 AUD (if exceeding free tier)
  - SMS: $6.75 AUD (via Twilio API)
  - TOTAL: ~$14 AUD/month

PROS ✅:
  ✅ Global edge network (fast everywhere)
  ✅ No server management
  ✅ Generous free tier (100K req/day = 3K/month easily covered)
  ✅ R2 storage cheaper than S3
  ✅ Automatic scaling
  ✅ DDoS protection included

CONS ❌:
  ❌ JavaScript/TypeScript environment (need to port Python code)
  ❌ Max 10ms CPU time per request (OK for inference, tight for training)
  ❌ D1 is Beta (PostgreSQL more mature)
  ❌ Limited Python support (Pyodide workaround, but slow)
  ❌ No native scikit-learn/pandas (need WASM builds)
  ⚠️ VERDICT: Not ideal for ML workloads, better for simple bots
```

---

### **Option 3: AWS Lambda + RDS - ENTERPRISE-GRADE** ⭐⭐⭐

```yaml
YEAR 1 (Free Tier):
  - Lambda: FREE (400K GB-seconds/month)
  - RDS: FREE (750 hours/month)
  - S3: FREE (5GB)
  - SES: FREE (3,000 emails/month)
  - SMS: $6.75 AUD/month
  TOTAL: ~$9 AUD/month

YEAR 2+ (Post Free Tier):
  - RDS db.t3.micro: $17 USD/month (~$26 AUD)
  - S3: $1 USD/month
  - Lambda: $2 USD/month (small overages)
  - Secrets Manager: $2 USD/month
  - SMS: $6.75 AUD/month
  TOTAL: ~$35 AUD/month

PROS ✅:
  ✅ Zero server management (fully managed)
  ✅ Auto-scaling (handle 1,000 stocks without changes)
  ✅ 99.99% uptime SLA (financial-grade reliability)
  ✅ Security best practices built-in (IAM, VPC, encryption)
  ✅ Integrated monitoring (CloudWatch, X-Ray)
  ✅ Disaster recovery (multi-AZ RDS, cross-region replication)
  ✅ Compliance certifications (ISO, SOC2, PCI-DSS if needed)

CONS ❌:
  ❌ Complex setup (IAM roles, VPC config, security groups)
  ❌ Steep learning curve (30+ AWS services to understand)
  ❌ Cost creep risk (easy to overspend without monitoring)
  ❌ Vendor lock-in (hard to migrate away)
  ❌ Overkill for 20 stocks (enterprise solution for startup problem)
  ❌ Free tier expires (Year 2 costs jump 3x)
  ❌ USD billing (currency risk for AUD budget)
```

---

### **HONEST ANALYSIS: For Light Loads, Why Pay for 24/7 Idle VM?**

#### The Reality Check You Deserve:
```
VM Running 24/7:
  - 720 hours/month of uptime
  - ACTUAL usage: ~8 hours/month (500 min compute)
  - Idle time: 98.9% 😬
  - You're paying for 712 hours of NOTHING
  
Serverless (Pay-Per-Execution):
  - Pay only for 500 minutes/month
  - No idle charges
  - Auto-scales to zero when not in use
  - But... there's a catch (see below)
```

---

### **REVISED RECOMMENDATION: It Depends on Your Dashboard Needs**

#### **Option A: Serverless (Cloudflare Workers + Supabase) - $0-3 AUD/month** ⭐⭐⭐⭐⭐

**BEST IF**: You only need daily email/SMS alerts, NO 24/7 dashboard access

```yaml
Stack:
  Compute: Cloudflare Workers (100K req/day FREE)
  Database: Supabase PostgreSQL (500MB FREE forever)
  Storage: Cloudflare R2 (10GB FREE)
  Cron: Cloudflare Cron Triggers (FREE)
  
Architecture:
  08:00 AEST Daily:
    → Cloudflare Worker triggers
    → Fetch 50 stocks from yfinance
    → Run model inference (5 models × 50 stocks = 250 executions)
    → Save signals to Supabase DB
    → Send email/SMS via Twilio
    → Worker shuts down (charges = $0)
    
  Idle Hours (23 hours/day):
    → Nothing running
    → Cost = $0
    
Monthly Cost Breakdown:
  - Workers: FREE (< 100K requests)
  - Supabase DB: FREE (< 500MB, < 2GB bandwidth)
  - R2 Storage: FREE (< 10GB)
  - Email (SendGrid): FREE (100/day)
  - SMS (Twilio): $6.75 AUD (150 SMS)
  
  TOTAL: $6.75 AUD/month (ONLY if you use SMS)
  OR: $0 AUD/month (if using Telegram Bot instead)
```

**PROS ✅**:
- ✅ **98% cheaper** than running idle VM
- ✅ Zero maintenance (no OS updates, no security patches)
- ✅ Global edge network (fast from AU/US/EU)
- ✅ Auto-scales (can handle 1000 stocks with zero config changes)
- ✅ Never goes down (Cloudflare 99.99% SLA)
- ✅ Free SSL, DDoS protection included

**CONS ❌**:
- ❌ **NO 24/7 dashboard** (Streamlit UI would need separate hosting)
  - Workaround: Host dashboard on Streamlit Cloud (FREE tier, but public access)
  - Or: Pay $5/month for Streamlit Cloud private deployment
- ❌ Cold starts (~200ms first request, then fast)
- ❌ 10ms CPU limit per request (OK for inference, tight for training)
  - Workaround: Retrain models on local laptop, upload to R2
- ❌ No native Python (uses JavaScript/Pyodide)
  - **DEALBREAKER?** Need to port Python AI code to JS
  - Or: Use Cloudflare + **Railway.app** for Python Workers ($5/month)
- ❌ **CRITICAL LIMITATION: TensorFlow.js cannot handle CatBoost or Prophet models**
  - TensorFlow.js only supports: Neural networks (LSTM), Random Forest (limited), XGBoost (onnx-js port)
  - CatBoost has NO JavaScript implementation (Python-only)
  - Prophet uses Stan backend (C++/Python, not portable to JS)
  - **VERDICT: Cloudflare Workers CANNOT act as ASX BOT signal generator if using multi-model consensus**
  - **Alternative**: Train models weekly on Railway/VPS, export ONNX format, serve inference on Cloudflare
    - But this loses real-time retraining capability (must pre-bake models)

---

#### **Option B: Hybrid (Serverless Compute + Cheap Dashboard Host) - $5-8 AUD/month** ⭐⭐⭐⭐

**BEST IF**: You want 24/7 dashboard access but still save on compute costs

```yaml
Stack:
  Compute: Railway.app Python Cron ($5 USD/month = $7.50 AUD)
  Database: Supabase PostgreSQL (FREE)
  Dashboard: Railway.app Streamlit (included in $5/month)
  
How Railway Works:
  - Sleeps when idle (like serverless)
  - Wakes up on cron trigger (08:00 AEST daily)
  - Runs Python natively (no JS port needed)
  - Streamlit dashboard available 24/7
  - 500MB RAM included ($5 tier)
  
Monthly Cost:
  - Railway: $7.50 AUD
  - SMS: $6.75 AUD (optional)
  TOTAL: $7.50 AUD (without SMS)
```

**PROS ✅**:
- ✅ Cheaper than constant VM ($7.50 vs $8 BinaryLane)
- ✅ Native Python support (no code changes)
- ✅ 24/7 Streamlit dashboard included
- ✅ Auto-sleeps when idle (saves compute credits)
- ✅ GitHub auto-deploy (push code → live in 2 min)

**CONS ❌**:
- ❌ 500MB RAM limit (enough for 50 stocks, tight for 200+)
- ❌ USD billing (Railway.app is US-based)
- ❌ 100GB/month bandwidth cap (usually fine)

---

#### **Option C: Constant VM (BinaryLane 1GB) - $8 AUD/month** ⭐⭐⭐

**BEST IF**: You want full control, no cold starts, can SSH anytime

```yaml
Why Keep VM Running 24/7 Despite 98.9% Idle?
  
1. Dashboard Always Available:
   - SSH in anytime to debug
   - Streamlit UI responsive 24/7 (no cold start)
   - Live tail logs: `journalctl -u trading-bot -f`
   
2. Database Co-Located:
   - PostgreSQL on same machine (no network latency)
   - No managed DB vendor lock-in
   - Easy pg_dump backups to local disk
   
3. Simplicity Tax Worth It?
   - For $8/month, you avoid:
     → Learning Cloudflare Workers API
     → Debugging serverless cold starts
     → Managing multiple services (DB separate from compute)
   - Trade-off: Pay $8 for peace of mind
   
4. Future Flexibility:
   - Want to add real-time WebSocket feed? Easy on VM.
   - Want to run Jupyter Notebook for analysis? Already there.
   - Want to host OpenClaw on same box? Docker it.
```

**Honest Take**: VM is **simplicity insurance**, not compute efficiency.

---

### **FINAL VERDICT: Choose Based on Your Priorities**

| Priority | Best Option | Monthly Cost |
|----------|-------------|--------------|
| **"I just want email alerts, no dashboard needed"** | Cloudflare Workers + Supabase | **$0-7 AUD** |
| **"I want dashboard + native Python + simplicity"** | Railway.app Hybrid | **$7.50 AUD** |
| **"I want full control + can SSH debug anytime"** | BinaryLane 1GB VPS | **$8 AUD** |
| **"I need 200+ stocks, co-locate OpenClaw"** | BinaryLane 2GB VPS | **$12 AUD** |

---

### **My Updated Recommendation (Honest Version):**

**Start with Railway.app ($7.50 AUD/month)** for these reasons:
1. ✅ Native Python (reuse all your ASX bot code, zero changes)
2. ✅ 24/7 Streamlit dashboard (critical for monitoring)
3. ✅ Auto-sleeps when idle (you're not paying for 712 idle hours)
4. ✅ GitHub auto-deploy (push to main → live in 2 min)
5. ✅ Supabase free DB (managed, backed up, replicated)
6. ✅ Easy migration to VPS later if you outgrow it

**Only choose BinaryLane VPS if**:
- [ ] You'll scale to 200+ stocks (need 2GB RAM)
- [ ] You want to co-locate OpenClaw trading agent
- [ ] You're already comfortable with Linux sysadmin
- [ ] You need custom firewall rules / network config

**Railway vs VPS = $7.50 vs $8 → Railway wins on features, VPS wins on control.**

---

### **HONEST RECOMMENDATION: Start with BinaryLane VPS** 🏆

#### Why BinaryLane Wins for Taiwan/AU Trading Bots:

1. **Simplicity Beats Features**  
   - You're a solo developer, not a DevOps team
   - No need to learn AWS IAM, VPC, Security Groups, Lambda layers, EventBridge, etc.
   - SSH in, install Python, run cron jobs. Done.

2. **True Cost Transparency**  
   - $19 AUD/month is your FINAL bill. No surprises.
   - AWS "free tier" is marketing — Year 2 costs jump to $35 AUD (84% increase!)
   - BinaryLane: Same price in Year 1, 2, 3, 4...

3. **Australian Presence Matters**  
   - BinaryLane support = Sydney business hours (not 2 AM AWS callbacks)
   - AUD billing (no 3% Visa currency conversion fees)
   - Low latency to Australian brokers (critical for real-time trading)

4. **Co-Location with OpenClaw**  
   - Run BOT + OpenClaw on SAME server (Docker containers isolated)
   - No network latency between signal generation and execution
   - Shared backups, shared monitoring, shared security

5. **No Over-Engineering**  
   - AWS Lambda is for Netflix-scale systems (millions of requests/hour)
   - You need: 2 cron jobs/day, 20 stock tickers, 5 users
   - A $12 VPS handles this workload at 5% CPU utilization

6. **Migration Path Exists**  
   - If you later scale to 500 stocks → upgrade to $24 4GB VPS
   - If you need multi-region → THEN migrate to AWS
   - But 99% chance you'll never outgrow a VPS

#### **When AWS Makes Sense Instead:**
- [ ] You're analyzing 1,000+ stocks (need horizontal scaling)
- [ ] You have unpredictable traffic spikes (need auto-scaling)
- [ ] You need multi-region disaster recovery (AU + US + EU)
- [ ] You're a team with dedicated DevOps engineer
- [ ] Compliance requires AWS-certified environment
- [ ] You plan to raise VC funding (investors expect "cloud native")

**For a personal trading bot? VPS wins. Every. Single. Time.**

---

### **VPS Setup Guide (BinaryLane Quickstart)**

```bash
# 1. Provision Server (via BinaryLane dashboard)
#    - OS: Ubuntu 24.04 LTS
#    - Plan: Standard 2GB ($12 AUD/month)
#    - Location: Sydney

# 2. Initial Security Hardening
ssh root@your-server-ip

# Create non-root user
adduser trader
usermod -aG sudo trader
su - trader

# Disable root SSH
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# 3. Install Dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3-pip postgresql nginx certbot

# 4. Setup PostgreSQL
sudo -u postgres createuser trader
sudo -u postgres createdb botdb -O trader
sudo -u postgres psql -c "ALTER USER trader PASSWORD 'secure_password';"

# 5. Deploy Bot Application
git clone https://github.com/your-repo/trading-bot.git
cd trading-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. Setup Systemd Service (Auto-restart on failure)
sudo tee /etc/systemd/system/trading-bot.service > /dev/null <<EOF
[Unit]
Description=Trading Bot Signal Generator
After=network.target postgresql.service

[Service]
Type=simple
User=trader
WorkingDirectory=/home/trader/trading-bot
ExecStart=/home/trader/trading-bot/venv/bin/python scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable trading-bot
sudo systemctl start trading-bot

# 7. Setup Streamlit Dashboard (Port 8501)
sudo tee /etc/systemd/system/streamlit-ui.service > /dev/null <<EOF
[Unit]
Description=Trading Bot Dashboard
After=network.target

[Service]
Type=simple
User=trader
WorkingDirectory=/home/trader/trading-bot
ExecStart=/home/trader/trading-bot/venv/bin/streamlit run ui_bot/dashboard.py --server.port=8501
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable streamlit-ui
sudo systemctl start streamlit-ui

# 8. Setup Nginx Reverse Proxy + SSL
sudo certbot --nginx -d bot.yourdomain.com
# Follow prompts, auto-renews via cron

# 9. Setup Daily Backups to Cloudflare R2 (Free 10GB)
pip install rclone
rclone config  # Configure R2 as remote "r2-backup"

# Add to crontab (daily 3 AM)
crontab -e
0 3 * * * pg_dump botdb | gzip | rclone rcat r2-backup:trading-bot-backups/db-$(date +\%Y\%m\%d).sql.gz

# 10. Monitoring (Free with Uptime Robot)
# Create account at uptimerobot.com
# Monitor: https://bot.yourdomain.com/health
# Get email alerts if down for >5 minutes
```

**Total Setup Time: 2 hours (vs. 2 weeks for AWS architecture)**

---

### **Final Verdict**

```
                    COST      SIMPLICITY    AU-OPTIMIZED
BinaryLane VPS:     ⭐⭐⭐⭐⭐   ⭐⭐⭐⭐⭐      ⭐⭐⭐⭐⭐
Hetzner VPS:        ⭐⭐⭐⭐⭐   ⭐⭐⭐⭐⭐      ⭐⭐
Cloudflare:         ⭐⭐⭐⭐    ⭐⭐⭐        ⭐⭐⭐⭐
AWS Lambda:         ⭐⭐       ⭐⭐          ⭐⭐⭐⭐
```

**PYTHON-NATIVE CLOUD PLATFORM COMPARISON (Honest Analysis)**

### **6.5.1 The Python Serverless Landscape (2026)**

You're right to question the Railway recommendation. Let's compare ALL major Python-friendly cloud platforms:

| Platform | Monthly Cost (AUD) | 3-Year Total | Setup Time | Python Support | Auto-Sleep | Dashboard Hosting | AU Region |
|----------|-------------------|--------------|------------|----------------|------------|-------------------|-----------|
| **Render.com** | **$6** | **$216** | 30 min | ⭐⭐⭐⭐⭐ Native | ✅ Yes | ✅ Included | ❌ US/EU only |
| **Railway.app** | $7.50 | $270 | 1 hour | ⭐⭐⭐⭐⭐ Native | ✅ Yes | ✅ Included | ❌ US/EU only |
| **Fly.io** | $4.50 | $162 | 45 min | ⭐⭐⭐⭐ Docker | ✅ Yes (suspend) | ⚠️ Extra $3 | ✅ Sydney region |
| **BinaryLane VPS** | $8 | $288 | 2 hours | ⭐⭐⭐⭐⭐ Native | ❌ 24/7 | ✅ Self-hosted | ✅ Sydney |
| **DigitalOcean App** | $7.50 | $270 | 1 hour | ⭐⭐⭐⭐⭐ Native | ✅ Yes | ✅ Included | ❌ US/EU |
| **Google Cloud Run** | $9 | $324 | 2 hours | ⭐⭐⭐⭐ Docker | ✅ Yes (scale-to-0) | ⚠️ Separate | ❌ Sydney (GCP) |
| **PythonAnywhere** | $7.50 | $270 | 15 min | ⭐⭐⭐⭐⭐ Native | ❌ 24/7 | ✅ Included | ❌ US only |
| **Replit Deployments** | $12 | $432 | 10 min | ⭐⭐⭐⭐⭐ Native | ✅ Yes | ✅ Included | ❌ US only |

---

### **6.5.2 Detailed Platform Analysis**

#### **Option 1: Render.com - $6 AUD/month** ⭐⭐⭐⭐⭐ **CHEAPEST**

```yaml
Render.com Stack:
  Compute: $4 USD/month ($6 AUD) - Starter tier
  Database: Free PostgreSQL (90 days, then Supabase $0)
  Dashboard: Streamlit included
  Auto-sleep: Yes (after 15 min idle)
  
Total: $6 AUD/month
3-Year Total: $216 AUD
```

**✅ PROS:**
- ✅ **CHEAPEST Python PaaS** ($6 vs Railway $7.50)
- ✅ Native Python (no Docker required)
- ✅ Auto-sleep when idle (same as Railway)
- ✅ GitHub auto-deploy (push → live in 90 sec)
- ✅ Free SSL, DDoS protection
- ✅ Simpler pricing (no usage-based surprises)
- ✅ Background workers included (for cron jobs)

**❌ CONS:**
- ❌ No Sydney region (US West/EU only - adds 180ms latency)
- ❌ Free DB expires after 90 days (must migrate to Supabase)
- ❌ 512MB RAM limit on Starter (vs Railway 1GB)
- ❌ Slower cold starts (~5 sec vs Railway 2 sec)

**Verdict:** **Best if you prioritize cost over latency** (saves $54 vs Railway over 3 years)

---

#### **Option 2: Fly.io - $4.50 AUD/month** ⭐⭐⭐⭐⭐ **BEST LATENCY**

```yaml
Fly.io Stack:
  Compute: $3 USD/month ($4.50 AUD) - 1x shared CPU
  Database: Supabase PostgreSQL ($0)
  Dashboard: Fly Machines ($2 USD = $3 AUD/month)
  Auto-suspend: Yes (after 5 min idle)
  
Total: $4.50 AUD (without dashboard) or $7.50 AUD (with dashboard)
3-Year Total: $162-270 AUD
```

**✅ PROS:**
- ✅ **SYDNEY REGION AVAILABLE** (lowest latency to ASX data)
- ✅ Cheapest base compute ($4.50 AUD)
- ✅ Docker-based (portable, no vendor lock-in)
- ✅ Auto-suspend when idle (scale-to-zero)
- ✅ Free outbound bandwidth (vs AWS egress fees)
- ✅ Built-in metrics and logging

**❌ CONS:**
- ❌ Requires Dockerfile (more complex setup than Railway)
- ❌ Dashboard costs extra $3/month (total = $7.50)
- ❌ Steeper learning curve (Fly CLI vs Railway web UI)
- ❌ Smaller community (less StackOverflow answers)

**Verdict:** **Best if you value AU proximity and don't mind Docker**

---

#### **Option 3: Railway.app - $7.50 AUD/month** ⭐⭐⭐⭐ **EASIEST**

```yaml
Railway.app Stack:
  Compute: $5 USD/month ($7.50 AUD)
  Database: Supabase PostgreSQL ($0)
  Dashboard: Streamlit included
  Auto-sleep: Yes
  
Total: $7.50 AUD/month
3-Year Total: $270 AUD
```

**✅ PROS:**
- ✅ **EASIEST SETUP** (literally 3 clicks: Connect GitHub → Deploy → Done)
- ✅ 1GB RAM included (vs Render 512MB)
- ✅ Fastest cold starts (2 sec)
- ✅ Best documentation and tutorials
- ✅ Large community (lots of Python/Streamlit examples)
- ✅ Nixpacks auto-detects Python deps (no Dockerfile needed)

**❌ CONS:**
- ❌ NOT the cheapest ($1.50 more than Render, $3 more than Fly)
- ❌ No Sydney region (US-based, 180ms latency)
- ❌ Usage-based billing (can spike if you exceed limits)

**Verdict:** **Best if you value simplicity over $1.50/month savings**

---

#### **Option 4: DigitalOcean App Platform - $7.50 AUD/month** ⭐⭐⭐

```yaml
DigitalOcean Stack:
  Compute: $5 USD/month ($7.50 AUD)
  Database: Managed PostgreSQL ($11 USD = $16.50 AUD)
  OR: Supabase ($0)
  
Total: $7.50 AUD (with Supabase) or $24 AUD (with DO DB)
```

**✅ PROS:**
- ✅ Established brand (reliable, won't disappear)
- ✅ Native Python support
- ✅ Auto-scaling included
- ✅ Predictable billing (fixed $5 USD)

**❌ CONS:**
- ❌ **EXPENSIVE DATABASE** ($16.50 AUD if using DO managed DB)
- ❌ No auto-sleep (always running = wasted $)
- ❌ Slower than Fly/Railway for cold starts
- ❌ No Sydney region

**Verdict:** **Avoid - Same price as Railway but worse features**

---

#### **Option 5: Google Cloud Run - $9 AUD/month** ⭐⭐⭐

```yaml
Google Cloud Run Stack:
  Compute: $6 USD/month ($9 AUD) - estimated for light usage
  Database: Cloud SQL ($13 USD = $19.50 AUD)
  OR: Supabase ($0)
  
Total: $9 AUD (with Supabase)
```

**✅ PROS:**
- ✅ True scale-to-zero (pay per request)
- ✅ Handles traffic spikes well (auto-scales to 1000 instances)
- ✅ GCP ecosystem (BigQuery, Vertex AI integration)

**❌ CONS:**
- ❌ **COMPLEX BILLING** (hard to predict monthly cost)
- ❌ Requires Dockerfile
- ❌ Separate dashboard hosting needed ($5-10/month)
- ❌ GCP learning curve (IAM, VPC, service accounts)
- ❌ No Sydney region for Cloud Run (only GCE)

**Verdict:** **Overkill for personal trading bot**

---

#### **Option 6: PythonAnywhere - $7.50 AUD/month** ⭐⭐⭐

```yaml
PythonAnywhere Stack:
  Compute: $5 USD/month ($7.50 AUD) - Hacker tier
  Database: MySQL included (1GB)
  Dashboard: Web-based file editor
  
Total: $7.50 AUD/month
```

**✅ PROS:**
- ✅ Python-specific (optimized for Django/Flask)
- ✅ Super simple (web-based editor, no git needed)
- ✅ MySQL included (no external DB)
- ✅ Good for beginners

**❌ CONS:**
- ❌ **NO AUTO-SLEEP** (24/7 running even when idle)
- ❌ OLD STACK (Python 3.10 max, no 3.12)
- ❌ Can't run Streamlit (web framework restrictions)
- ❌ US-only servers
- ❌ Limited to scheduled tasks (no true cron flexibility)

**Verdict:** **Not suitable for ASX BOT (can't run Streamlit dashboard)**

---

#### **Option 7: Replit Deployments - $12 AUD/month** ⭐⭐

```yaml
Replit Stack:
  Compute: $8 USD/month ($12 AUD) - Reserved VM
  Database: Built-in Neon PostgreSQL ($0)
  Dashboard: Built-in web IDE
  
Total: $12 AUD/month
```

**✅ PROS:**
- ✅ Instant setup (literally zero config)
- ✅ Built-in IDE (code in browser)
- ✅ Native Python support
- ✅ Auto-scaling

**❌ CONS:**
- ❌ **MOST EXPENSIVE** ($12 vs Render $6)
- ❌ Designed for prototyping, not production
- ❌ Public Repls visible (need paid tier for private)
- ❌ US-only servers

**Verdict:** **Too expensive for production use**

---

### **6.5.3 REVISED FINAL RECOMMENDATION**

```
📊 COST vs FEATURES vs LATENCY Matrix:

                    COST      EASE-OF-USE   AU-LATENCY   MATURITY
Render.com:         ⭐⭐⭐⭐⭐   ⭐⭐⭐⭐⭐      ⭐⭐⭐        ⭐⭐⭐⭐
Fly.io:             ⭐⭐⭐⭐⭐   ⭐⭐⭐          ⭐⭐⭐⭐⭐    ⭐⭐⭐⭐
Railway.app:        ⭐⭐⭐⭐    ⭐⭐⭐⭐⭐      ⭐⭐⭐        ⭐⭐⭐⭐
BinaryLane VPS:     ⭐⭐⭐⭐    ⭐⭐⭐⭐        ⭐⭐⭐⭐⭐    ⭐⭐⭐⭐⭐
```

**MY REVISED RECOMMENDATION:**

| Your Priority | Choose | Monthly Cost | 3-Year Savings vs Railway |
|---------------|--------|--------------|---------------------------|
| **"CHEAPEST + Dead Simple"** | **Render.com** | **$6** | Save $54 |
| **"AU Latency + Cost Balance"** | **Fly.io** | **$4.50** | Save $108 (no dashboard) |
| **"Easiest Setup (3 clicks)"** | **Railway.app** | **$7.50** | Baseline |
| **"Full Control + AU Region"** | **BinaryLane VPS** | **$8** | Pay $18 more |

---

### **6.5.4 The Honest Truth About Railway**

**Why Railway was initially recommended:**
- ✅ Genuinely easiest setup (Nixpacks auto-detects Python)
- ✅ Best beginner experience (web UI vs CLI)
- ✅ Most tutorials online (popular in indie hacker community)

**But Railway is NOT the cheapest or fastest:**
- ❌ **Render.com is $1.50/month cheaper** (20% savings)
- ❌ **Fly.io is $3/month cheaper + has Sydney region** (40% savings + better latency)
- ❌ Both Render and Fly support Python just as well

**When Railway makes sense:**
- If you're NEW to DevOps (Railway has gentlest learning curve)
- If $1.50/month difference doesn't matter to you
- If you want 1GB RAM (vs Render's 512MB)

**When to choose alternatives:**
- **Render.com** → If you want cheapest PaaS and don't need Sydney region
- **Fly.io** → If you want Sydney region + cheapest + willing to write Dockerfile
- **BinaryLane VPS** → If you want co-location with OpenClaw + SSH access

---

### **6.5.5 FINAL WINNER (Reconsidered)**

**For ASX Retail Trader (50 stocks, 3 profiles, smart budget):**

```yaml
🏆 WINNER: Render.com ($6 AUD/month)

Render.com Stack:
  Compute: $4 USD/month ($6 AUD) - Starter
  Database: Supabase PostgreSQL (FREE 500MB)
  Dashboard: Streamlit 24/7 (included)
  Notifications: Telegram Bot (FREE)
  
Total: $6 AUD/month (fixed forever)
3-Year Total: $216 AUD

Setup Process:
  1. Sign up Render.com (5 min)
  2. Connect GitHub repo (2 min)
  3. Add Supabase PostgreSQL (3 min)
  4. Set environment variables (10 min)
  5. Deploy → Live in 2 minutes
  
Total Setup Time: 45 min
```

**Why Render.com beats Railway:**
- ✅ **$54 cheaper over 3 years** (20% cost savings)
- ✅ Same ease of use (native Python, GitHub auto-deploy)
- ✅ Same features (auto-sleep, Streamlit hosting, cron jobs)
- ✅ Better free tier (no usage surprises)

**Trade-off:** No Sydney region (180ms latency vs 50ms for Fly.io Sydney)

**Final Verdict:** **Use Render.com for ASX BOT unless you need Sydney region (then Fly.io)**

**Total 3-Year Savings:**
- Render vs Railway: Save $54 AUD
- Render vs AWS: Save $864-1,224 AUD 💰

---

### **Decision Tree: Which Platform for YOU?**

```
START HERE: What's your DevOps comfort level?

├─ BEGINNER (first cloud deployment) 
│  └─ Choose: Render.com ($6/month)
│     - Easiest setup, native Python, cheapest
│
├─ INTERMEDIATE (used Docker before)
│  ├─ Do you need Sydney region for low latency?
│  │  ├─ YES → Choose: Fly.io ($4.50/month + $3 dashboard = $7.50)
│  │  └─ NO  → Choose: Render.com ($6/month - save $1.50)
│  │
│  └─ Want to co-locate OpenClaw on same server?
│     └─ YES → Choose: BinaryLane VPS 2GB ($12/month)
│
└─ ADVANCED (want full control, SSH access)
   └─ Choose: BinaryLane VPS ($8/month standalone)
      - Can upgrade to 2GB for co-location later
```

**Platform-Specific Use Cases:**

**Render.com** ($6/month) - Choose if:
- ✅ You want **cheapest Python PaaS** (saves $54 vs Railway over 3 years)
- ✅ You're OK with US region (180ms latency acceptable)
- ✅ You want native Python (no Docker learning needed)
- ✅ You value simplicity over $2/month

**Fly.io** ($4.50-7.50/month) - Choose if:
- ✅ **Sydney region is critical** (50ms latency to ASX data vs 180ms)
- ✅ You're comfortable with Dockerfile + CLI tools
- ✅ You want cheapest compute ($4.50) and can skip dashboard
- ✅ You might scale internationally later (global edge network)

**Railway.app** ($7.50/month) - Choose if:
- ✅ You want **absolute easiest setup** (literally 3 clicks)
- ✅ You need 1GB RAM (vs Render 512MB)
- ✅ $1.50/month extra cost doesn't matter
- ✅ You want fastest cold starts (2 sec vs Render 5 sec)

**BinaryLane VPS** ($8/month) - Choose if:
- ✅ You'll co-locate OpenClaw trading agent (same server, Docker isolated)
- ✅ You love SSH debugging and full system control
- ✅ You're scaling to 200+ stocks (upgrade to 2GB for $12/month)
- ✅ You want **Australian company** (data sovereignty)

**Cloudflare Workers** ($0/month) - ~~Not viable for ASX BOT signal generation~~
- ❌ Cannot run CatBoost or Prophet models (TensorFlow.js limitation)
- ❌ No Python runtime for weekly/monthly model retraining
- ✅ **BUT: Excellent choice for OpenClaw trade executor** (see Section 7.7)
  - Durable Objects for stateful order management
  - FREE tier covers typical trading volume
  - Global edge network for fast broker API calls

**AWS Lambda** ($30-40/month) - ~~Don't choose this for personal trading bot~~
- Only makes sense for enterprise/commercial applications
- Or if you have NEW AWS account (12-month free tier)

---

## **7. OpenClaw Integration & Co-Location Cost Analysis**

### **7.1 What is OpenClaw?**

**OpenClaw** is a separate trading agent system that:
- Consumes signals from this ASX BOT system
- Executes actual trades via broker APIs (CommSec, Interactive Brokers)
- Manages order lifecycle (limit orders, stop-losses, position tracking)
- Provides risk management layer (daily loss limits, position sizing)

**Key Architectural Decision: Should OpenClaw run on the same infrastructure as ASX BOT?**

---

### **7.2 Deployment Scenarios**

#### **Scenario A: Separate Infrastructure (Recommended for Development)**

```yaml
ASX BOT System (Signal Generator):
  Platform: Railway.app
  Cost: $7.50 AUD/month
  Resources: 512MB RAM, 0.5 vCPU
  Purpose: Generate BUY/SELL/HOLD signals daily
  Output: JSON signals → PostgreSQL table
  
OpenClaw Agent (Trade Executor):
  Platform: Separate BinaryLane VPS
  Cost: $8 AUD/month (1GB RAM)
  Purpose: Read signals → Execute trades via broker API
  Isolation: Fully separated from signal generation
  
Total Monthly Cost: $15.50 AUD/month
Total 3-Year Cost: $558 AUD
```

**✅ Pros:**
- **Security**: Trading credentials isolated from analysis system
- **Flexibility**: Can restart/redeploy ASX BOT without touching OpenClaw
- **Debugging**: Easier to troubleshoot when systems are independent
- **Scaling**: Can scale each system independently (e.g., upgrade OpenClaw to 2GB if needed)

**❌ Cons:**
- **Cost**: Paying for 2 separate servers ($15.50 vs $8/month)
- **Network Latency**: Signals must transfer between systems (adds 50-100ms)
- **Operational Overhead**: Managing 2 deployment pipelines

---

#### **Scenario B: Co-Located on BinaryLane VPS (Production-Ready)**

```yaml
Combined System (BinaryLane 2GB VPS):
  Platform: BinaryLane Sydney
  Cost: $12 AUD/month
  Resources: 2GB RAM, 1 vCPU, 50GB SSD
  
Docker Containers:
  - asx-bot-container (512MB limit)
    - Signal generation, Streamlit dashboard
    - PostgreSQL database (shared)
  
  - openclaw-container (1GB limit)
    - Trade execution engine
    - Broker API client (CommSec/IBKR)
    - Order management system
  
  - postgres-container (256MB)
    - Shared database for both systems
    - Portfolio state, signal history
  
Total Monthly Cost: $12 AUD/month
Total 3-Year Cost: $432 AUD
```

**✅ Pros:**
- **Cost Savings**: $3.50/month cheaper than separate infrastructure ($126 saved over 3 years)
- **Low Latency**: Both systems share same database (no network transfer)
- **Simple Backup**: One server to backup/restore (not two)
- **Portability**: Can migrate entire stack with one Docker Compose file

**❌ Cons:**
- **Shared Resources**: If ASX BOT crashes, could affect OpenClaw (mitigated by Docker limits)
- **Security Risk**: If server compromised, both signal generator AND trading credentials exposed
- **Scaling Limit**: Can't independently upgrade (e.g., if OpenClaw needs 4GB, must upgrade entire VPS to 4GB)

---

#### **Scenario C: Co-Located on Railway.app (Cloud-Native)**

```yaml
Combined System (Railway.app):
  Platform: Railway.app
  Cost: $10 AUD/month
  
Services:
  - asx-bot-service ($5 USD)
    - Signal generation, Streamlit dashboard
  
  - openclaw-service ($5 USD)
    - Trade execution, broker integration
  
  - supabase-postgres (FREE)
    - Shared database
  
Total Monthly Cost: $15 AUD/month
Total 3-Year Cost: $540 AUD
```

**✅ Pros:**
- **Auto-Scaling**: Both services scale independently
- **Zero-Downtime Deploy**: Update ASX BOT without touching OpenClaw
- **Built-in Secrets**: Railway Secrets Manager (no .env files)
- **GitHub Auto-Deploy**: Push code → both services update automatically

**❌ Cons:**
- **Most Expensive**: $15 vs $12 (BinaryLane) or $15.50 (separate)
- **Vendor Lock-In**: Harder to migrate off Railway (vs portable Docker Compose)
- **Network Latency**: Services communicate via internal Railway network (not localhost)

---

### **7.3 Cost Comparison Table**

| Scenario | Infrastructure | Monthly Cost | 3-Year Total | Best For |
|----------|---------------|--------------|--------------|----------|
| **A: Separate** | Railway ($7.50) + BinaryLane VPS ($8) | **$15.50** | **$558** | Development, high security needs |
| **B: BinaryLane Co-Locate** | BinaryLane 2GB VPS | **$12** | **$432** | ⭐ Production (best value) |
| **C: Railway Co-Locate** | Railway.app 2 services | **$15** | **$540** | Cloud-native, auto-scaling |
| **D: Railway Bot + FREE OpenClaw** | Railway ($7.50) + Local OpenClaw | **$7.50** | **$270** | Testing, non-24/7 trading |

---

### **7.4 Technical Implementation: Docker Compose Co-Location**

**BinaryLane VPS 2GB Setup** (Scenario B - Recommended):

```yaml
# docker-compose.yml
version: '3.8'

services:
  # ASX Signal Generator
  asx-bot:
    image: ghcr.io/yourname/asx-bot:latest
    container_name: asx-bot
    restart: unless-stopped
    mem_limit: 512m
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/trading_db
      - PYTHONUNBUFFERED=1
    ports:
      - "8501:8501"  # Streamlit dashboard
    volumes:
      - ./models:/app/models  # Shared AI models
      - ./logs:/app/logs
    depends_on:
      - postgres
    networks:
      - trading-net
  
  # OpenClaw Trade Executor
  openclaw:
    image: ghcr.io/yourname/openclaw:latest
    container_name: openclaw
    restart: unless-stopped
    mem_limit: 1024m
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/trading_db
      - BROKER_API_KEY=${BROKER_API_KEY}  # From .env file
      - BROKER_API_SECRET=${BROKER_API_SECRET}
    volumes:
      - ./logs:/app/logs
    depends_on:
      - postgres
      - asx-bot
    networks:
      - trading-net
  
  # Shared PostgreSQL Database
  postgres:
    image: postgres:16-alpine
    container_name: trading-db
    restart: unless-stopped
    mem_limit: 256m
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=trading_db
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - trading-net

volumes:
  postgres-data:

networks:
  trading-net:
    driver: bridge
```

**Resource Allocation (2GB VPS):**
- PostgreSQL: 256MB (always running)
- ASX BOT: 512MB (runs 08:00-08:30 AEST daily)
- OpenClaw: 1GB (runs when signals detected, typically 09:00-10:00)
- System overhead: ~256MB

**Uptime Estimate:**
- ASX BOT: 30 min/day = 2% active, 98% idle (auto-sleeps)
- OpenClaw: 1-2 hours/day = 8% active (only when trading)
- PostgreSQL: 24/7 running

**Actual RAM Usage:** ~512-768MB peak, ~256MB idle (well under 2GB limit)

---

### **7.5 Security Considerations for Co-Location**

#### **Risk: Shared Database Access**
- **Threat**: If ASX BOT compromised, attacker could read OpenClaw's broker credentials
- **Mitigation**: Use separate PostgreSQL schemas with role-based access:
  ```sql
  CREATE SCHEMA asx_bot;
  CREATE SCHEMA openclaw;
  GRANT ALL ON SCHEMA asx_bot TO asx_bot_user;
  GRANT SELECT ON asx_bot.signals TO openclaw_user;  -- Read-only
  GRANT ALL ON SCHEMA openclaw TO openclaw_user;
  ```

#### **Risk: Container Escape**
- **Threat**: Vulnerability in Docker could allow container-to-container breach
- **Mitigation**:
  - Enable Docker AppArmor profiles (BinaryLane Ubuntu 24.04 default)
  - Use `--read-only` flag for immutable containers
  - Scan images with Trivy before deployment

#### **Risk: Broker API Key Exposure**
- **Threat**: Broker credentials in environment variables could leak
- **Mitigation**:
  - Store in `.env` file with `chmod 600` (owner-only read)
  - Use Docker secrets instead of environment variables:
    ```yaml
    secrets:
      broker_api_key:
        file: ./secrets/broker_api_key.txt
    ```

---

### **7.6 Final Recommendation for OpenClaw Integration**

```
📊 Cost vs Security vs Simplicity Matrix:

                    COST      SECURITY    SIMPLICITY
Separate Infra:     ⭐⭐⭐     ⭐⭐⭐⭐⭐    ⭐⭐⭐
BinaryLane Co-Loc:  ⭐⭐⭐⭐⭐   ⭐⭐⭐⭐      ⭐⭐⭐⭐⭐
Railway Co-Loc:     ⭐⭐⭐     ⭐⭐⭐⭐⭐    ⭐⭐⭐⭐
```

**MY RECOMMENDATION: BinaryLane 2GB Co-Location** ($12/month)

**Why?**
- ✅ **Cheapest Production Setup**: $432 over 3 years (saves $126 vs separate)
- ✅ **Good Security**: Docker isolation + PostgreSQL schema separation
- ✅ **Simple Management**: One server, one Docker Compose file, one backup
- ✅ **AU-Based**: BinaryLane Sydney = low latency to ASX data sources
- ✅ **Upgrade Path**: Can migrate to separate infra later if needed

**Decision Tree:**

```
Are you in development/testing phase?
├─ YES → Use Scenario D (Railway $7.50 + Local OpenClaw)
│         Run OpenClaw on your laptop, signals from cloud
│
└─ NO (Production) → Do you need 99.9% uptime?
    ├─ YES → Use Scenario C (Railway Co-Locate $15/month)
    │         Auto-scaling, zero-downtime deploys
    │
    └─ NO (Personal trading) → Use Scenario B (BinaryLane $12/month)
              Best value, sufficient reliability
```

**3-Year Total Cost with OpenClaw:**
- **Development**: $270 AUD (Railway BOT only, local OpenClaw)
- **Production**: $432 AUD (BinaryLane 2GB co-located)

**Savings vs AWS**: $648-1,008 AUD over 3 years 💰

---

### **7.7 Cloudflare Workers as OpenClaw Trade Executor (FREE Alternative)**

#### **Why Cloudflare FAILS as Signal Generator but WINS as Trade Executor**

**❌ Signal Generation (ASX BOT):**
- Requires CatBoost + Prophet + XGBoost + LSTM consensus
- TensorFlow.js only supports LSTM (not CatBoost/Prophet)
- Needs weekly/monthly model retraining (Python scikit-learn pipelines)
- **Verdict: NOT VIABLE**

**✅ Trade Execution (OpenClaw):**
- Only needs:
  - Read signals from PostgreSQL (simple SQL queries)
  - Call broker REST APIs (CommSec, Interactive Brokers)
  - Manage order state (limit orders, fills, cancellations)
  - Send notifications (Telegram, email)
- All of above work perfectly in JavaScript/TypeScript
- **Cloudflare Durable Objects** = Stateful serverless (perfect for order tracking)
- **Verdict: EXCELLENT CHOICE**

---

#### **Scenario E: Render ASX BOT + Cloudflare OpenClaw (CHEAPEST HYBRID)**

```yaml
ASX BOT System (Signal Generator):
  Platform: Render.com
  Cost: $6 AUD/month
  Purpose: Multi-model AI consensus, weekly retraining, Streamlit dashboard
  Output: Writes BUY/SELL signals to Supabase PostgreSQL
  
OpenClaw Agent (Trade Executor):
  Platform: Cloudflare Workers + Durable Objects
  Cost: $0 AUD/month (FREE tier)
  Purpose: Read signals → Execute trades → Track orders → Send alerts
  Resources:
    - 100K requests/day (enough for 50 stocks × 20 checks/day)
    - Durable Objects: $0.15/million reads (virtually FREE for retail)
    - R2 Storage: 10GB FREE (store order history)
  
Shared Database:
  Platform: Supabase PostgreSQL
  Cost: $0 (FREE 500MB)
  
Total Monthly Cost: $6 AUD/month
Total 3-Year Cost: $216 AUD
```

**✅ Advantages:**
- ✅ **CHEAPEST Production Setup**: $216 over 3 years (saves $216 vs BinaryLane co-locate)
- ✅ **99.99% Uptime for Trading**: Cloudflare's edge network never sleeps
- ✅ **Zero Maintenance**: No VM to update, no Docker to manage
- ✅ **Global Edge**: Fast broker API calls from anywhere (CF auto-routes)
- ✅ **Infinite Scale**: Can handle 1000 stocks if needed (no code changes)
- ✅ **Separation of Concerns**: Signal generation and trade execution fully isolated
- ✅ **Uses cheapest Python PaaS**: Render ($6) instead of Railway ($7.50)

**❌ Disadvantages:**
- ❌ **Requires TypeScript Rewrite**: OpenClaw must be ported from Python to JS/TS
  - Estimated effort: 3-5 days (broker API client + order state machine)
  - But: Once done, zero ongoing maintenance
- ❌ **Debugging Harder**: No SSH access (must use Cloudflare Wrangler CLI)
- ❌ **Durable Objects Learning Curve**: New paradigm vs traditional database

---

#### **Cloudflare Durable Objects: Order Management Example**

```typescript
// openclaw-worker.ts (Cloudflare Worker)
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Triggered by cron (every 5 minutes during market hours)
    const signals = await fetchSignalsFromSupabase(env.SUPABASE_URL);
    
    for (const signal of signals) {
      if (signal.action === 'BUY' && signal.confidence > 0.75) {
        // Create Durable Object for this order
        const orderId = env.ORDERS.idFromName(signal.ticker);
        const orderStub = env.ORDERS.get(orderId);
        
        // Execute trade via broker API
        await orderStub.fetch(request.url, {
          method: 'POST',
          body: JSON.stringify({
            ticker: signal.ticker,
            action: 'BUY',
            quantity: signal.position_size,
            limit_price: signal.target_price
          })
        });
      }
    }
    
    return new Response('Orders processed', { status: 200 });
  },
  
  // Cron trigger: Every 5 min (9:00-16:00 AEST weekdays)
  async scheduled(event: ScheduledEvent, env: Env) {
    await this.fetch(new Request('https://openclaw.example.com/cron'), env);
  }
};

// Order Durable Object (stateful)
export class Order {
  state: DurableObjectState;
  
  async fetch(request: Request) {
    const order = await request.json();
    
    // Call CommSec API
    const response = await fetch('https://api.commsec.com.au/orders', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.env.BROKER_API_KEY}` },
      body: JSON.stringify({
        symbol: order.ticker,
        side: 'buy',
        quantity: order.quantity,
        order_type: 'limit',
        limit_price: order.limit_price
      })
    });
    
    const result = await response.json();
    
    // Store order state in Durable Object
    await this.state.storage.put('order', {
      ticker: order.ticker,
      status: result.status,  // 'pending', 'filled', 'cancelled'
      fill_price: result.fill_price,
      timestamp: Date.now()
    });
    
    // Send Telegram notification
    await sendTelegramAlert(`✅ BUY ${order.ticker} @ $${result.fill_price}`);
    
    return new Response(JSON.stringify(result));
  }
}
```

**How Durable Objects Work:**
- Each stock order gets its own stateful "mini-server"
- State persists across Worker invocations (survives restarts)
- Automatic geo-replication (survive datacenter failure)
- Strong consistency (no race conditions on order updates)

**Cost Example (50 stocks, daily trading):**
```yaml
Monthly Usage:
  - Cron triggers: 12 checks/hour × 6 hours × 22 days = 1,584 invocations
  - Durable Object reads: 50 stocks × 1,584 = 79,200 reads
  - Broker API calls: ~5 trades/day × 22 days = 110 calls
  
Cloudflare Pricing:
  - Workers: 1,584 requests (< 100K FREE limit) = $0
  - Durable Objects: 79,200 reads ($0.15 per 1M) = $0.01
  - R2 Storage: 10MB order history (< 10GB FREE) = $0
  
Total: $0.01 AUD/month (virtually FREE)
```

---

#### **When to Choose Cloudflare OpenClaw:**

**Choose Cloudflare Durable Objects if:**
- ✅ You're comfortable with TypeScript (or willing to learn)
- ✅ You want $0 trade execution costs forever
- ✅ You value 99.99% uptime (no "server down" during market hours)
- ✅ You might scale to 200+ stocks later (infinite headroom)
- ✅ You want separation: Railway handles AI, Cloudflare handles trading

**Choose BinaryLane Co-Location if:**
- ✅ You want everything in one Docker Compose file (simpler mental model)
- ✅ You're not comfortable with JavaScript/TypeScript
- ✅ You want SSH access for debugging (tail logs, inspect database)
- ✅ You prefer paying $4.50 more/month to avoid porting code

---

#### **Final Cost Comparison (Including OpenClaw):**

| Setup | ASX BOT | OpenClaw | Total/Month | 3-Year Total |
|-------|---------|----------|-------------|-------------|
| **Render + Cloudflare** ⭐ | $6 | $0 | **$6** | **$216** |
| **Fly.io + Cloudflare** | $4.50-7.50 | $0 | **$4.50-7.50** | **$162-270** |
| **BinaryLane Co-Locate** | $6 | $6 | **$12** | **$432** |
| **Railway + Cloudflare** | $7.50 | $0 | $7.50 | $270 |
| **Railway + BinaryLane** | $7.50 | $8 | $15.50 | $558 |
| **Railway + Railway** | $7.50 | $7.50 | $15 | $540 |

**Winner: Render ASX BOT + Cloudflare OpenClaw** ($216 over 3 years)

**Runner-up: Fly.io (Sydney) + Cloudflare OpenClaw** ($162 over 3 years if skipping dashboard, $270 with dashboard)

**Tradeoff:** Requires 3-5 days to port OpenClaw to TypeScript, but saves $216-342 over 3 years.

**ROI Calculation:**
- TypeScript port effort: 5 days × 8 hours = 40 hours
- Savings: $216-342 over 3 years (vs BinaryLane)
- **Hourly savings rate: $5.40-8.55/hour**

**Verdict:** If your time is worth less than $10/hour, port to Cloudflare. Otherwise, pay $12/month for BinaryLane simplicity.

---

### **ASX-Specific Considerations**

#### Market Hours & Scheduling
```yaml
ASX Trading Hours (AEST/AEDT):
  - Pre-Market: 07:00-10:00
  - Normal Trading: 10:00-16:00
  - After-Hours (CSPA): 16:12-17:00

Recommended Cron Schedule:
  - Daily Signal Generation: 08:00 AEST (before market open)
  - Post-Market Analysis: 17:30 AEST (after close)
  - Weekly Model Retrain: Saturday 02:00 AEST
```

#### ASX Data Peculiarities
```yaml
Ticker Format:
  - Yahoo Finance: "BHP.AX", "CBA.AX", "CSL.AX"
  - Note: Some stocks have multiple codes (ordinary vs CDI)
  
Data Quality:
  - Yahoo Finance: 15-minute delay (free tier)
  - ASX Official: Real-time requires $50+ AUD/month subscription
  - Dividends: ASX is dividend-heavy (adjust models for yield)
  
Market Microstructure:
  - No circuit breakers (unlike US ±7%/13%/20%)
  - T+2 settlement (shares/cash settled 2 business days later)
  - CGT discount: 50% if held >12 months (model implications!)
```

#### Australian Tax Implications
```yaml
Capital Gains Tax (CGT):
  - Short-term (<12 months): Taxed at marginal rate (up to 45% + Medicare)
  - Long-term (≥12 months): 50% CGT discount
  - Implication: BOT should flag "approaching 12-month" positions
  
Franking Credits:
  - ASX dividends often franked (tax credits attached)
  - Model should consider dividend yield + franking
  - Example: 5% dividend + franking = ~7% effective yield
  
GST:
  - NO GST on financial services (brokerage fees excluded)
```

---

### 6.6 Security Checklist

#### Pre-Deployment Requirements
- [ ] Enable AWS MFA (Multi-Factor Authentication) for root account
- [ ] Create IAM users with least-privilege policies (no root access)
- [ ] Rotate all secrets in Secrets Manager every 90 days
- [ ] Enable RDS encryption at rest
- [ ] Enable S3 bucket versioning for backups
- [ ] Configure CloudWatch alarms for suspicious activity (e.g., >10 failed logins/hour)
- [ ] Set up AWS Budget alerts (email if cost exceeds $50 AUD/month)
- [ ] Document disaster recovery plan (who can restore, how long to recover)
- [ ] Test restore procedure monthly (restore RDS snapshot to dev environment)
- [ ] Review IAM permissions quarterly (remove unused policies)

#### Authentication Layers
1. **AWS Console Access**: MFA-protected IAM users only
2. **Streamlit Dashboard**: Cognito login (email + password + TOTP)
3. **API Endpoints**: API keys rotated every 30 days
4. **Database Access**: Firewall rules (only Lambda security group allowed)

---

