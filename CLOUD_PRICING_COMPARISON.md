# Cloud Platform Pricing Comparison
**AI Trading Bot (ASX Market)**
*Last Updated: February 5, 2026*

> **Purpose**: Compare hosting costs across major cloud platforms for a Python Flask app with scheduled cron jobs (30 hours/month active time).

---

## Application Profile

| Parameter | Value |
|-----------|-------|
| **Type** | Python Flask API (Serverless bot) |
| **Compute** | 1GB RAM, Shared CPU |
| **Storage** | 2GB persistent volume (database) |
| **Usage Pattern** | 30 hours/month active (cron-triggered) |
| **Network** | Minimal egress (~2MB/day for yfinance data) |
| **Database** | External Supabase (PostgreSQL) |
| **Regions** | Asia Pacific (Sydney preferred) |

---

## Platform Comparison Summary

| Platform | Monthly Cost | Bandwidth | Auto-Stop | Best For |
|----------|-------------|-----------|-----------|----------|
| **Koyeb** | **$0.22*** | 100GB free | ✅ Yes | Cheapest option |
| **AWS Fargate** | **$0.61** | +$0.01 | ✅ Yes | Docker as-is |
| **Fly.io** | **$0.61** | +$0.01 | ✅ Yes | Sydney region |
| **Railway** | **$5.00** | Included | ✅ Yes | $5 minimum |
| **Render** | **$7.50** | 100GB free | ❌ No | Always-on |
| **AWS Lambda** | **FREE** | 1GB free | ✅ Native | Refactoring OK |

**Winner**: **Koyeb** ($0.22/month with bandwidth) - Cheapest if Singapore latency OK  
**Runner-Up**: **Fly.io** ($0.61/month with bandwidth) - Best for Sydney region < 5ms  

***Koyeb**: $0.0072/hour × 30 hours = $0.216/month  
**Bandwidth**: Trading bot uses ~60MB/month egress (adds $0.01 for Fly.io/Fargate)

---

## Detailed Pricing Analysis

### 1. Fly.io (Recommended) 💚

**Official Pricing**: https://fly.io/docs/about/pricing/

#### Cost Breakdown (730 hours = 1 month)
```
Component Pricing:
- Compute (baseline):     $0.88/month  (for 730 hours)
- Memory 1GB (baseline):  $6.35/month  (for 730 hours)
- Volume 2GB (stopped):   $0.30/month  (persistent storage)
- Bandwidth: 100GB free/month (trading bot uses ~60MB)

Active Usage (30 hours):
- Compute portion:  $0.88 × (30/730) = $0.04
- Memory portion:   $6.35 × (30/730) = $0.26
- Stopped fees:     $0.30 (volume + rootfs 1GB)
- Bandwidth:        $0.01 (60MB egress)
─────────────────────────────────────────────
Total: $0.61/month (compute + storage + bandwidth)
```

#### Key Features
- ✅ **Auto-Stop**: Machine stops when idle, only pays for running time
- ⚠️ **Stopped Charges**: $0.15/GB/month for stopped rootfs storage (~$0.15-0.30/month)
- ✅ **Per-Second Billing**: Charges by actual usage
- ✅ **Sydney Region**: `syd` region available for low latency
- ✅ **GitHub Actions**: Easy CI/CD integration
- ⚠️ **No Free Tier**: Requires payment method from day 1

#### Scaling Scenarios
| Scenario | Hours/Month | Monthly Cost |
|----------|-------------|--------------|
| ASX only (current) | 30 | $0.60 |
| ASX + USA markets | 60 | $0.90 |
| ASX + USA + TWN | 90 | $1.20 |
| 24/7 always-on | 730 | $7.53 |

#### Verdict
✅ **Best for**: Cost-conscious production deployments with predictable low usage
📊 **Savings**: 92% cheaper than 24/7 hosting ($7.53 → $0.60)

---

### 2. Koyeb 🟡

**Official Pricing**: https://www.koyeb.com/pricing

#### Cost Breakdown
```
Koyeb eSmall Instance Pricing (from official website):
- Instance: eSmall (0.5 vCPU, 1GB RAM, 8GB storage)
- Hourly rate: $0.0072/hour
- Billing: Per-second billing (no minimum)

For 30 hours/month:
- Compute: 30 hours × $0.0072 = $0.216/month
- Bandwidth: 100GB free (included in Starter plan)
- Database: FREE Postgres (5 hours/month compute, 1GB storage)
─────────────────────────────────────────────
Total: $0.22/month (pay-as-you-go with database included)

Note: There is NO "reserved" vs "pay-as-you-go" pricing
- All instances are billed hourly ($0.0072/hour for eSmall)
- Scale-to-zero means $0 when stopped
- You only pay for running hours
- Free database included (sufficient for trading bot)
```

#### Key Features
- ✅ **No Minimum**: Pure pay-as-you-go ($0.0072/hour = $0.22 for 30 hours)
- ✅ **Scale-to-Zero**: Auto-stops when idle (NO CHARGE when stopped)
- ✅ **FREE Database**: Postgres included (5h/month, 1GB storage, auto-sleep)
- ✅ **Bandwidth Included**: 100GB/month free on Starter plan
- ✅ **Auto-Stop/Wake**: Admin panel accessible (wakes on HTTP request)
- ✅ **Global Regions**: Washington, Frankfurt, Singapore available
- ✅ **Free Trial**: Trial period with compute credits
- ❌ **No Sydney**: Closest region is Singapore (+100ms latency)

#### Scale-to-Zero Behavior (Official Koyeb Documentation):

**Auto-Stop Trigger (Services)**:
- **Idle Period**: 5 minutes (default for Standard CPU instances)
- Conditions for auto-stop:
  - ✅ No traffic from internet for 5 consecutive minutes
  - ✅ No held connections (WebSocket/HTTP2 streams)
  - ✅ No new deployments

**Auto-Stop Trigger (Database)**:
- **Idle Period**: 5 minutes of database inactivity
- Database automatically sleeps when no queries are executed
- Wakes up automatically on first new query with minor delay
- Storage charges paused during sleep (free tier has no storage charge)

**Cold Start Performance (Wake-Up Times)**:
- **Service Deep Sleep** (default): **1-5 seconds** cold start
  - Spins up new VM from scratch
  - Full container initialization
  
- **Service Light Sleep** (optional, public preview): **200ms** wake-up
  - Uses VM snapshotting for faster wake-up
  - Currently free during preview
  - Configurable idle timeout (5min - 6hr on Pro plan)

- **Database Wake-Up**: **Minor delay** on first query after 5min idle

**Admin Panel User Experience**:
- User visits admin URL → Triggers service wake-up
- **Service wait**: 1-5 seconds (Deep Sleep) or 200ms (Light Sleep)
- **Database wait**: Minor delay if database was sleeping
- Instance starts → Flask app initializes → Database connects → Page loads
- Subsequent requests: Instant (stays warm for 5+ minutes)

#### FREE Postgres Database Analysis

**Database Specifications** (Official Koyeb Documentation):
- **Compute Limit**: 5 hours/month FREE (Free tier instance)
- **Storage Limit**: 1GB maximum (no charge within limit)
- **Instance Type**: 0.25 vCPU, 1GB RAM
- **Auto-Sleep**: Sleeps after 5 minutes of inactivity
- **Connection Limit**: ~112 max connections (1GB RAM ÷ 9531392 bytes)
- **Overage Cost**: $0.04/hour ($29.76/month for always-on) if exceeds 5 hours

**Trading Bot Database Usage Estimation**:
```
Database Query Time (Active Compute Hours):
- Daily cron job: 2 min/day × 30 days = 60 min/month = 1.0h/month
- Admin panel access: ~5 sessions/month × 10 min = 50 min/month = 0.83h/month
- Data queries/updates: ~30 queries/month × 2 sec = 1 min/month = 0.02h/month
────────────────────────────────────────────────────
Total Database Compute: ~1.85 hours/month
Free Tier Limit: 5 hours/month
Remaining Buffer: 3.15 hours (63% unused)

Storage Requirements:
- Stock prices + recommendations: ~10-50MB
- 1GB limit = 20-100x larger than needed
- No growth concerns for single-market bot
```

**Is Free Database Suitable?** ✅ **YES - PERFECT FIT**

**Why It Works**:
1. **Compute Usage << Free Limit**: 1.85h/month vs 5h/month (63% buffer)
2. **Storage Well Within Limits**: 10-50MB vs 1GB limit (95% unused)
3. **Auto-Sleep Efficiency**: Database only counts time when actively querying
4. **Sleep periods don't consume quota**: Perfect for sporadic access pattern
5. **Connection limits sufficient**: 112 connections >> trading bot needs (<5)

**Cost Implications**:
- **Total Koyeb Cost**: $0.22/month (compute only)
- **Database Cost**: $0.00/month (within 5h free limit)
- **Combined**: **$0.22/month total** (no database charges)

**⚠️ Limitations to Consider**:
- 0.25 vCPU for free database (slower than paid tiers, but sufficient)
- Region must match app region (Singapore recommended)
- If database usage unexpectedly spikes >5h, charges apply
- Free tier database has 1GB storage hard limit (not expandable)

#### Verdict
✅ **Best for**: Cheapest overall ($0.22/month) with FREE database included
📊 **Value**: 64% cheaper than Fly.io ($0.22 vs $0.61), includes database
⚠️ **Latency**: Singapore closest to Sydney (+100ms vs Fly.io < 5ms)
💡 **Winner on cost + database**: Best if latency isn't critical and you need Postgres
🎯 **Database Perfect**: 5h/month limit >> 1.85h actual usage (63% buffer)

---

### 3. Railway 🟡

**Official Pricing**: https://railway.com/pricing

#### Cost Breakdown
```
Plans Available:
1. FREE TRIAL: $5 credits for 30 days (requires credit card)
2. HOBBY: $5/month minimum (includes $5 usage credits)
3. PRO: $20/month minimum (includes $20 usage credits)

Compute Pricing (pay-per-use):
- Memory: $0.00000386 per GB-second
- CPU: $0.00000772 per vCPU-second
- Volume: $0.00000006 per GB-second

For 1 vCPU, 1GB RAM, 30 hours:
- 30 hours = 108,000 seconds
- CPU cost:    108,000 × $0.00000772 = $0.83
- Memory cost: 108,000 × $0.00000386 = $0.42
- Volume 2GB:  2 × 108,000 × $0.00000006 = $0.01
- Bandwidth:   $0.00 (traffic included in Hobby plan)
─────────────────────────────────────────────
Usage: $1.26, but minimum charge is $5/month
Note: Includes $5 credits, so first $5 of usage is free
```

#### Key Features
- ⚠️ **$5 Minimum**: Must pay $5/month even if usage < $5
- ✅ **No Stopped Charges**: Truly free when scaled to zero
- ✅ **Excellent DX**: Best developer experience (CLI, dashboard, logs)
- ✅ **Auto-Scale**: Vertical and horizontal scaling
- ✅ **GitHub Integration**: Native CI/CD from GitHub repos
- ✅ **7-Day Logs**: Free log retention
- ❌ **No Sydney**: Closest region TBD (likely Singapore/Tokyo)

#### Verdict
⚠️ **Best for**: Teams valuing developer experience over lowest cost
📊 **Value**: Premium DX but 8× more expensive than Fly.io

---

### 4. Render 🟠

**Official Pricing**: https://render.com/pricing

#### Cost Breakdown
```
Plans Available:
1. FREE: $0/month (512MB RAM, 0.1 CPU, spins down after 15min)
2. STARTER: $7/month (512MB RAM, 0.5 CPU, always-on)
3. STANDARD: $25/month (2GB RAM, 1 CPU, always-on)

For ASX Bot:
- FREE plan: Not suitable (512MB may be insufficient + spins down)
- STARTER plan: $7/month (no auto-stop, always-on pricing)

Storage & Bandwidth:
- Persistent disks: $0.25/GB per month = $0.50 for 2GB
- Bandwidth: 100GB free/month (trading bot uses only 60MB)
─────────────────────────────────────────────
Total: $7.50/month (Starter + 2GB disk, bandwidth free)
```

#### Key Features
- ⚠️ **No Auto-Stop**: Starter plan is always-on, no usage-based pricing
- ✅ **Simple Setup**: Very easy deployment from GitHub
- ✅ **Free PostgreSQL**: Free tier includes database (256MB)
- ✅ **Zero-Downtime**: Automatic zero-downtime deploys
- ❌ **No Sydney**: US/EU regions only (higher latency for AU)
- ❌ **Poor Value**: Paying for 730 hours but only using 30 hours

#### Verdict
❌ **Not Recommended**: 12.5× more expensive than Fly.io with no cost optimization
📊 **Use Case**: Better for always-on web apps, not scheduled jobs

---

### 5. AWS Lambda ⚡

**Official Pricing**: https://aws.amazon.com/lambda/pricing/

#### Cost Breakdown
```
Free Tier (Monthly):
- 1 million requests
- 400,000 GB-seconds compute
- 100GB HTTP response streaming

Pricing (after free tier):
- Requests: $0.20 per million
- Duration: $0.0000166667 per GB-second (x86)
- Duration: $0.0000133334 per GB-second (ARM/Graviton2)

For ASX Bot (30 hours/month, 1GB memory):
Assumptions:
- 30 cron jobs per month (once per day)
- Average execution: 1 hour per job = 3,600 seconds
- Memory: 1GB (1024MB)

Monthly compute:
- Total seconds: 30 jobs × 3,600s = 108,000 seconds
- Total GB-seconds: 108,000 × 1GB = 108,000 GB-s
- Billable: 108,000 - 400,000 free tier = 0 (WITHIN FREE TIER!)

Monthly requests:
- Total requests: 30 (well under 1M free tier)
- Billable: $0

Additional costs:
- EventBridge Scheduler: 30 invocations = FREE (1M free)
- Data transfer: Minimal (< 1GB) = FREE (1GB free)
─────────────────────────────────────────────
Total: $0.00/month (within free tier!)

BUT:
If we need longer runs (e.g., 3 hours per job):
- Total GB-seconds: 30 × 10,800s × 1GB = 324,000 GB-s
- Still within 400,000 free tier = $0.00

If we exceed free tier (e.g., 15 hours per day):
- Total GB-seconds: 450 hours × 3,600s = 1,620,000 GB-s
- Billable: 1,620,000 - 400,000 = 1,220,000 GB-s
- Cost: 1,220,000 × $0.0000166667 = $20.33/month
```

#### Key Features
- ✅ **PERMANENT Free Tier**: 400,000 GB-seconds/month for ALL users (not just first year)
- ✅ **True Serverless**: Pay only for actual execution time (no stopped charges)
- ✅ **Auto-Scale**: Infinite scaling capabilities
- ✅ **Sydney Region**: `ap-southeast-2` available
- ⚠️ **Complexity**: Requires Lambda function architecture, EventBridge setup
- ⚠️ **Cold Starts**: ~1-3 second cold start delay
- ⚠️ **15-Min Limit**: Maximum execution time is 15 minutes per invocation
- ❌ **Architectural Change**: Not drop-in replacement for Flask app

#### Refactoring Required
To use Lambda, you would need to:
1. Convert Flask app to Lambda handler functions
2. Split long-running jobs into smaller chunks (< 15 min each)
3. Use EventBridge for cron scheduling
4. Implement state management (S3/DynamoDB for intermediate results)
5. Handle cold starts and timeout retries

#### Verdict
✅ **Best for**: AWS-native architectures, existing AWS users, or free-tier-only projects
⚠️ **Trade-off**: 2-3 weeks refactoring to save $7.20/year (Fly.io) or $60/year (Railway)
📊 **Free Tier Status**: Permanent for ALL users (returning customers still get 400K GB-s/month)
💡 **When Worth It**: If you're already building serverless or need complete cost elimination

---

### 6. AWS ECS Fargate 🐳

**Official Pricing**: https://aws.amazon.com/fargate/pricing/

#### Cost Breakdown
```
Architecture: Run Docker containers without managing servers

Pricing (Sydney ap-southeast-2 region):
- CPU: $0.000011244 per vCPU-second (x86)
- Memory: $0.000001235 per GB-second
- Ephemeral Storage: $0.0000000308 per GB-second (20GB free)
- ARM/Graviton2: 20% cheaper CPU costs

For ASX Bot (30 hours/month, 0.5 vCPU, 1GB):
- 30 hours = 108,000 seconds
- CPU cost (0.5 vCPU):    108,000 × 0.5 × $0.0000089944 = $0.49
- Memory cost (1GB):      108,000 × 1 × $0.0000009889 = $0.11
- Storage (20GB free):    $0.00
- Bandwidth (60MB egress): $0.01
─────────────────────────────────────────────
Total: $0.61/month (ARM Graviton2 + bandwidth)
Total: $0.75/month (x86 + bandwidth)

Scheduled Tasks with EventBridge:
- EventBridge rule: FREE (1M invocations/month free tier)
- **IMPORTANT**: NO stopped charges (only pay when running)
- Task starts: 30/month (via EventBridge Scheduler)
- Only charged for actual running time (stopped = $0)
```

#### Key Features
- ✅ **No Refactoring**: Run existing Docker container as-is
- ⚠️ **NO Auto-Shutdown**: Task runs until process exits (not like Fly.io auto-stop)
- ✅ **Scheduled Tasks**: Perfect for cron jobs (EventBridge starts → runs → exits)
- ⚠️ **Admin Panel Issue**: For web UI, task must run 24/7 ($14.35/month) ❌
- ✅ **Sydney Region**: `ap-southeast-2` available
- ✅ **EventBridge Integration**: Native cron scheduling
- ✅ **CloudWatch Logs**: 5GB free, 7-day retention
- ⚠️ **Setup Complexity**: ECS Task Definition, IAM roles, VPC config
- ⚠️ **Cold Start**: ~30-60 seconds (Docker pull + container start)
- ❌ **No Permanent Free Tier**: Unlike Lambda (charges for compute time)

#### Comparison vs Lambda
| Feature | Lambda | ECS Fargate |
|---------|--------|-------------|
| **Code Changes** | Major refactoring | None (Docker as-is) |
| **Cost (30h)** | $0.00 (free tier) | $0.59-0.74 |
| **Execution Limit** | 15 minutes | No limit |
| **Cold Start** | 1-3 seconds | 30-60 seconds |
| **Best For** | Short functions | Long-running tasks |

#### Setup Requirements
1. Create ECS Task Definition (point to Docker image)
2. Configure IAM roles (ECS Task Execution Role)
3. Set up EventBridge Scheduler (cron expression)
4. Deploy to Fargate (no EC2 management)
5. CloudWatch for logs/monitoring
Scheduled cron jobs ONLY (signal generation, not web UI)
⚠️ **NOT for**: Admin panel / web dashboard (no auto-stop, 24/7 = $14.35/month)
📊 **Cron Jobs**: $0.59/month (runs → exits → $0 until next schedule)
❌ **Web UI**: $14.35/month (must run 24/7, no auto-stop feature)
💡 **Use Case**: Signal sender bot ✅ | Admin dashboard ❌

#### How Fargate Works (Critical Understanding):
```
Cron Job Mode (✅ CHEAP):
EventBridge triggers → Task starts → Runs signal generation → Process exits
Cost: Only running time ($0.59 for 30 hours/month)

Web UI Mode (❌ EXPENSIVE):
Task starts → Flask runs forever (listening on port) → Never exits
Cost: 730 hours × $0.02/hour = $14.35/month (no auto-stop!)
```

**Key Limitation**: Fargate has NO "idle detection" or "auto-stop" like Fly.io  
- Fly.io: Stops machine after inactivity, wakes on HTTP request
- Fargate: Task runs until YOU stop it OR process exits
⚠️ **Setup**: More complex than Fly.io but simpler than Lambda refactoring
💡 **Sweet Spot**: Drop-in Docker deployment + AWS services (S3, RDS, etc.)

---

## 🌐 Bandwidth Pricing Analysis

**Trading Bot Network Traffic Profile**:

**Ingress (Inbound - Data Fetching)**:
- Yahoo Finance API: ~5-10MB per run (stock data for 50-100 tickers)
- 30 runs/month: 5MB × 30 = **150MB/month inbound**

**Egress (Outbound - Data Upload)**:
- Supabase database updates: ~1MB per run
- Telegram notifications: ~0.5MB per run
- API responses/logs: ~0.5MB per run
- 30 runs/month: 2MB × 30 = **60MB/month outbound**

**Total Monthly Traffic**: 
- Ingress: 150MB
- Egress: 60MB
- **Combined: 210MB/month**

### ⚠️ **Critical Note: Most Platforms Only Charge for EGRESS**

| Platform | Ingress Cost | Egress Cost | Free Tier | Your Cost (60MB egress) |
|----------|--------------|-------------|-----------|-------------------------|
| **Koyeb** | **FREE** | $0.02/GB (US/EU), $0.04/GB (Asia) | **100GB/month** | **$0.00** |
| **Fly.io** | **FREE** | $0.02/GB (US/EU), $0.04/GB (APAC) | **None*** | **$0.01** |
| **Render** | **FREE** | $0.10/GB | **100GB/month** | **$0.00** |
| **Railway** | **FREE** | $0.05/GB | **Included** | **$0.00** |
| **AWS Fargate** | **FREE** | $0.04/GB (APAC) | **None** | **$0.01** |
| **AWS Lambda** | **FREE** | $0.04/GB (APAC) | **1GB/month** | **$0.00** |

***Fly.io** charges from first GB (no free tier mentioned in official docs)

**Revised Total Bandwidth Costs**:
- **Koyeb**: $0.00 (100GB free tier)
- **Fly.io**: $0.01/month
- **Render**: $0.00 (100GB free tier)
- **Railway**: $0.00 (included in plan)
- **AWS Fargate**: $0.01/month
- **AWS Lambda**: $0.00 (1GB free tier)

**Conclusion**: Bandwidth cost is minimal ($0.00 - $0.01/month) for 60MB/month egress

### If You Scale to Multiple Markets (180MB egress/month):

**ASX + USA + TWN Markets** (3× traffic = 180MB egress):
- **Koyeb**: $0.00 (still under 100GB free tier)
- **Fly.io**: $0.01/month
- **Railway**: $0.00 (traffic included)
- **Render**: $0.00 (still under 100GB free tier)
- **AWS Fargate**: $0.01/month
- **AWS Lambda**: $0.00 (still under 1GB free tier)

**Verdict**: Bandwidth cost remains minimal even with 3-market expansion ($0.00-$0.01/month)

---

## ⏱️ Auto-Stop & Cold Start Comparison

**Critical for Admin Panel UX**: How long users wait when accessing your dashboard

| Platform | Auto-Stop After | Cold Start Time | User Experience | Best For |
|----------|-----------------|-----------------|-----------------|----------|
| **Koyeb (Deep Sleep)** | 5 minutes | **1-5 seconds** | Good - Brief wait | Cost priority |
| **Koyeb (Light Sleep)** | 5 minutes | **200ms** | Excellent - Near instant | Best UX + cost |
| **Fly.io** | Configurable | **~1 second** | Excellent - Very fast | Best overall |
| **Railway** | Auto-detects | **~2-3 seconds** | Good - Acceptable wait | Premium DX |
| **Render** | ❌ No auto-stop | N/A (always-on) | Perfect - Instant | Always-on apps |
| **AWS Fargate** | ❌ Manual only | **30-60 seconds** | ❌ Poor - Long wait | Cron jobs only |
| **AWS Lambda** | Instant | **1-3 seconds** | Good - Brief wait | Serverless |

### 🎯 **Admin Panel Recommendations**:

1. **Best UX + Lowest Cost**: **Koyeb with Light Sleep** ($0.22/month, 200ms wake-up)
   - Enable Light Sleep in configuration
   - 96% faster wake-up than Deep Sleep
   - Currently free during public preview

2. **Best Latency + Fast Wake**: **Fly.io** ($0.61/month, ~1s wake-up)
   - Sydney region (< 5ms)
   - Consistently fast cold starts
   - Most reliable auto-stop/wake

3. **NOT for Admin Panel**: **AWS Fargate** (30-60s cold start)
   - Good for cron jobs
   - Terrible UX for web dashboards
   - Users would wait 30-60 seconds every time

---

## Cost Comparison Table

### Monthly Costs (30 Hours Active + Bandwidth)

### Monthly Costs (30 Hours Active + Bandwidth)

| Platform | Compute | Storage | Bandwidth | Database | Total | vs Koyeb |
|----------|---------|---------|-----------|----------|-------|----------|
| **Koyeb** | $0.22 | $0 | $0 | **$0 (FREE)** | **$0.22** | **Baseline** |
| **AWS Fargate (ARM)** | $0.60 | $0 | $0.01 | N/A | **$0.61** | +177% |
| **Fly.io** | $0.30 | $0.30 | $0.01 | N/A | **$0.61** | +177% |
| **Railway** | $0 (credit) | $0 | $0 | Included | **$5.00** | +2,173% |
| **Render** | $7.00 | $0.50 | $0 | Included | **$7.50** | +3,309% |
| **AWS Lambda** | $0 (free tier) | $0 | $0 | N/A | **$0.00*** | -100% |

***AWS Lambda**: PERMANENTLY free (400K GB-seconds/month for ALL users)  
**Koyeb Database**: FREE Postgres (5h/month, 1GB storage) - Perfect for trading bot (uses ~1.85h/month)  
**Note**: Bandwidth is $0 for all platforms at 60MB/month usage

### Annual Cost Projections (with Bandwidth)

| Platform | Monthly | Annual | 3-Year Total |
|----------|---------|--------|--------------|
| **AWS Lambda** | $0.00 | $0.00 | $0.00 |
| **Koyeb** | $0.22 | $2.64 | $7.92 |
| **AWS Fargate (ARM)** | $0.61 | $7.32 | $21.96 |
| **Fly.io** | $0.61 | $7.32 | $21.96 |
| **Railway** | $5.00 | $60.00 | $180.00 |
| **Render** | $7.50 | $90.00 | $270.00 |

---

## Scaling Analysis

### Multi-Market Expansion Costs

| Scenario | AWS Lambda* | AWS Fargate | Fly.io | Koyeb** | Railway | Render |
|----------|-------------|-------------|--------|---------|---------|--------|
| **ASX only** (30h) | $0.00 | $0.59 | $0.60 | $0.94 | $5.00 | $7.50 |
| **ASX + USA** (60h) | $0.00 | $1.18 | $0.90 | $1.88 | $5.00 | $7.50 |
| **ASX + USA + TWN** (90h) | $0.00 | $1.77 | $1.20 | $2.82 | $5.00 | $7.50 |
| **All 3 + 24/7** (730h) | $0.00*** | $14.35 | $7.53 | $22.84 or $5.36† | $20.00‡ | $25.00 |

*Lambda requires refactoring (2-3 weeks); Fargate runs Docker as-is  
**Koyeb: Pay-as-you-go pricing shown (use this for scheduled jobs)  
***May exceed 400K GB-seconds free tier if running continuously  
†At 730h, Koyeb reserved instance ($5.36) becomes cheaper than pay-as-you-go ($22.84)  
‡Would need to upgrade to higher tier plan

### Cost Efficiency by Usage Pattern

| Usage Pattern | Best Choice | Monthly Cost | Rationale |
|---------------|-------------|--------------|-----------||
| **Minimal (<50h/month)** | AWS Fargate | $0.59-1.00 | Drop-in Docker, no refactoring |
| **Low (50-150h/month)** | AWS Fargate | $1.00-2.50 | Better than Koyeb, AWS ecosystem |
| **Medium (150-400h/month)** | Railway Hobby | $5.00 | $5 credits cover ~200h usage |
| **High (400-730h/month)** | Railway Pro | $20.00 | $20 credits + better support |
| **Always-On (730h/month)** | Fly.io | $7.53 | Cheapest for 24/7 (vs Fargate $14.35) |

---

## Key Considerations

### Latency & Regional Availability

| AWS Fargate | ✅ `ap-southeast-2` | N/A | < 10ms |
| AWS Lambda | ✅ `ap-southeast-2` | N/A | < 10ms |
| Koyeb | ❌ | Singapore | ~100ms |
| Railway | ❌ | TBD | Unknown |
| Render | ❌ | US/EU | ~20
| Railway | ❌ | TBD | Unknown |
| Render | ❌ | US/EU | ~200ms |
| AWS Lambda | ✅ `ap-southeast-2` | N/A | < 10ms |

**Impact**: For ASX market trading signals, low latency is critical. Fly.io and AWS Lambda have Sydney presence.

### Developer Experience
AWS Fargate | 30 min | GitHub Actions | CloudWatch 5GB free | ⭐⭐⭐ |
| 
| Platform | Setup Time | CI/CD | Logs/Metrics | Ease of Use |
|----------|-----------|-------|--------------|-------------|
| Fly.io | 10 min | GitHub Actions | 30-day logs | ⭐⭐⭐⭐ |
| Koyeb | 5 min | Native GitHub | 7-day logs | ⭐⭐⭐⭐ |
| Railway | 5 min | Native GitHub | 7-day logs | ⭐⭐⭐⭐⭐ |
| Render | 5 min | Native GitHub | 7-day logs | ⭐⭐⭐⭐⭐ |
| AWS Lambda | 60+ min | Custom setup | CloudWatch | ⭐⭐ |

**Railway wins DX**, but **Fly.io best value** for cost.

### Free Tier Comparison

| Platform | Free Tier | Limitations | Duration |
|----------|-----------|-------------|----------|
| Fly.io | ❌ None | N/A | N/A |
| Koyeb | ⚠️ 5 hours compute | Trial only | Limited |
| Railway | ⚠️ $5 credits | 30 days | Trial only |
| Render | ⚠️ 512MB, spins down | Always | Permanent |
| AWS Lambda | ✅ 400K GB-s/month | Resets monthly | Permanent |

**AWS Lambda** has the most generous permanent free tier.

---

## Recommendations

### 1. **Production Deployment (Recommended)** 🏆
**Platform**: **Fly.io**
- **Cost**: $0.60/month
- **Reason**: Best cost efficiency, Sydney region, auto-stop optimization
- **Setup**: Simple `fly launch`, GitHub Actions deployment
- **Trade-off**: No free tier, but cost is negligible

### 2. **AWS-Native Architecture** ⚡
**Platform**: **AWS Lambda**
- **Cost**: $0.00/month (within free tier)
- **Reason**: Completely free, true serverless, Sydney region
- **Setup**: Requires refactoring Flask app to Lambda handlers
- **Trade-off**: 2-3 weeks development time, not worth $0.60 savings

### 3. **Premium Developer Experience** 🎨
**Platform**: **Railway**
- **Cost**: $5.00/month
- **Reason**: Best DX, excellent logs/metrics, easy scaling
- **Setup**: 5 minutes, native GitHub integration
- **Trade-off**: 8× more expensive than Fly.io

### 4. **Budget-Conscious Side Project** 💰
**Platform**: **Koyeb**
- **Cost**: $5.00/month
- **Reason**: Good balance of features and cost
- **Setup**: 5 minutes, scale-to-zero
- **Trade-off**: No Sydney region (Singapore fallback)

### 5. **Not Recommended** ❌
**Platform**: **Render**
- **Cost**: $7.50/month
- **Reason**: No auto-stop, always-on pricing, poor value for scheduled jobs
- **Use Case**: Better for always-on web apps, not cron jobs

---

## Migration Considerations

### Current Setup (Local/Development)
- ✅ Python Flask app with UV environment
- ✅ Supabase PostgreSQL database (external)
## 🏆 Winner: **Koyeb** (Cheapest) or **Fly.io** (Best Latency)

### 💰 **Final Ranking by Cost** (30 hours/month + bandwidth):

1. **AWS Lambda**: $0.00 (free, requires refactoring)
2. **Koyeb**: $0.22/month (⭐ **CHEAPEST** if you can tolerate +100ms latency)
3. **AWS Fargate**: $0.60/month (Docker as-is, AWS ecosystem)
4. **Fly.io**: $0.60/month (⭐ **BEST LATENCY** Sydney < 5ms)
5. **Railway**: $5.00/month ($5 minimum wasted)
6. **Render**: $7.50/month (always-on, poor value)

---

### 🚨 **CRITICAL DECISION FACTORS**

#### **Do You Need Admin Panel?**

**YES** → Choose platform with **auto-stop/wake**:
- **Koyeb**: $0.22/month ✅ Cheapest (Singapore region)
- **Fly.io**: $0.60/month ✅ Best latency (Sydney region)
- **Railway**: $5.00/month (Premium DX)
- **Render**: $7.50/month ❌ Must run 24/7

**NO** (Cron jobs only):
- **AWS Fargate**: $0.60/month ✅ Best for cron-only
- **Koyeb**: $0.22/month ✅ Cheapest

#### **Do You Need Low Latency?**

**YES** (Sydney critical):
- **Fly.io**: $0.60/month (Sydney `syd` region < 5ms)
- **AWS Fargate**: $0.60/month (Sydney `ap-southeast-2`)

**NO** (Singapore OK):
- **Koyeb**: $0.22/month (Singapore +100ms) ✅ **73% cheaper**

---

### 📊 **Recommended Choice by Priority**

#### **Priority: Cost** 💰
**Choose**: **Koyeb** ($0.22/month = $2.64/year)
- ✅ 64% cheaper than Fly.io
- ✅ Auto-stop/wake (admin panel works)
- ✅ 100GB bandwidth free
- ✅ **FREE Postgres database** (5h/month, 1GB storage - trading bot uses ~1.85h)
- ⚠️ Singapore region (+100ms vs Sydney)

#### **Priority: Latency** ⚡
**Choose**: **Fly.io** ($0.61/month = $7.32/year)
- ✅ Sydney region (< 5ms latency)
- ✅ Auto-stop/wake (admin panel works)
- ✅ 10-minute setup
- ⚠️ 177% more expensive than Koyeb ($7.32 vs $2.64/year)

#### **Priority: AWS Ecosystem** ☁️
**Choose**: **AWS Fargate** ($0.61/month = $7.32/year)
- ✅ Easy S3/RDS/SNS integration
- ✅ Docker as-is (no refactoring)
- ✅ Sydney `ap-southeast-2` region
- ⚠️ NO auto-stop (bad for admin panel - would cost $14.35/month 24/7)

#### **Priority: Free** 🆓
**Choose**: **AWS Lambda** ($0.00 permanently)
- ✅ Completely free (400K GB-seconds/month)
- ✅ True serverless
- ❌ Requires 2-3 weeks refactoring
- ❌ 15-minute execution limit

---

### 🎯 **Final Recommendation for Your Use Case**

**Best Overall**: **Koyeb** ($0.22/month) if Singapore latency OK  
**Best Latency**: **Fly.io** ($0.61/month) if Sydney region critical

**Cost Comparison Table**:
| Use Case | Koyeb (Singapore) | Fly.io (Sydney) | Savings |
|----------|-------------------|-----------------|---------||
| **Admin Panel + Cron** | $0.22/month | $0.61/month | 64% cheaper |
| **Annual** | $2.64 | $7.32 | Save $4.68/year |
| **3-Year** | $7.92 | $21.96 | Save $14.04 |

**Latency Trade-Off**:
- Koyeb: ~120ms (Singapore → Sydney)
- Fly.io: ~3ms (Sydney local)
- **Is 117ms extra worth $4.68/year savings?** → Probably YES for a bot!

**Fargate Alternative**: $14.35/month (24× more expensive!)
- To run admin panel, task must stay alive 24/7
- No auto-stop functionality
- Cold start: 30-60 seconds (poor UX for web UI) |
| Render | 🟢 Low (30 min) | Connect GitHub repo, auto-detects |
| AWS Lambda | 🔴 High (2 weeks) | Refactor to handlers, EventBridge setup |

---
Detailed Comparison:

#### **Option 1: Fly.io** (Best for Admin Panel) ⚡ **WINNER**
**Cost**: $0.60/month ($7.20/year)
- ✅ **Auto-Stop/Wake**: Sleeps when idle, wakes in ~1 second on HTTP request
- ✅ Admin panel accessible anytime (invisible to user)
- ✅ Cron jobs work perfectly (GitHub Actions → HTTP trigger → wakes machine)
- ✅ Sydney `syd` region (< 5ms latency)
- ⚠️ $0.30/month stopped storage (includes rootfs + volume)
- 💡 **Perfect for**: Web UI + scheduled jobs in ONE deployment

#### **Option 2: AWS Fargate** (Cron Jobs ONLY) 🐳
**Cost**: $0.59/month (cron) OR $14.35/month (web UI)
- ✅ **Best for cron-only**: Signal generation without UI
- ❌ **Bad for web UI**: No auto-stop, must run 24/7
- ⚠️ Cold start: 30-60 seconds (pulling Docker image)
- ⚠️ Admin panel requires: Always-on task ($14.35/month) OR Lambda + ALB setup
- 💡 **Use if**: You don't need admin panel OR willing to pay $14.35/monthno stopped charges
3. ✅ **Sydney Region**: `ap-southeast-2` for low latency (< 10ms)
4. ✅ **AWS Ecosystem**: Easy integration with S3, RDS, Secrets Manager
5. ✅ **No Stopped Fees**: Unlike Fly.io ($0.30/month stopped storage)
6. ✅ **EventBridge Cron**: Native scheduling, no external tools

### Runner-Up Options:

#### **Option 1: Fly.io** (Best Latency) ⚡
**Cost**: $0.61/month ($7.32/year)
- ✅ 10-minute setup (fastest)
- ✅ Sydney `syd` region (< 5ms latency)
- ✅ ~1 second admin panel wake-up
- ⚠️ $0.30/month stopped storage charges
- ⚠️ 233% more expensive than Koyeb ($7.32 vs $2.64/year)
- ⚠️ No database included (need external service)
- 💡 Best for: Sydney-based users who need instant latency

#### **Option 2: AWS Fargate** (AWS Ecosystem) ☁️
**Cost**: $0.61/month ($7.32/year) - Cron jobs only
- ✅ Drop-in Docker deployment (30 min setup)
- ✅ Sydney `ap-southeast-2` region
- ✅ AWS native (easy RDS/S3/SNS integration)
- ⚠️ NO auto-stop (bad for admin panel - $14.35/month 24/7)
- ⚠️ 30-60s cold start (terrible web UI experience)
- ⚠️ No database included (need RDS separately ~$15/month)
- 💡 Best for: Cron-only deployment with AWS integrations

#### **Option 3: AWS Lambda** (Free Forever) 💰
**Cost**: $0.00/month permanently
- ✅ Completely free (400K GB-seconds/month)
- ✅ True serverless
- ❌ Requires 2-3 weeks refactoring (separate functions)
- ❌ 15-minute execution limit per function
- ❌ No admin panel (web UI requires API Gateway + Lambda combo)
- ⚠️ No database included (need RDS/DynamoDB)
- 💡 Best for: New projects built serverless-first from day 1

### 📊 **Final Recommendation**:

**Choose Koyeb** ($0.22/month = $2.64/year) because:
- **Cheapest overall**: 64% cheaper than Fly.io ($2.64 vs $7.32/year)
- **FREE Postgres database**: 5 hours/month compute included (bot uses ~1.85h)
- **No hidden fees**: $0 when stopped (vs Fly.io $0.30/month storage)
- **Admin panel works**: Light Sleep (200ms wake) or Deep Sleep (1-5s wake)
- **Perfect for trading bot**: Low usage pattern fits free database limits
- **Singapore region**: +100ms latency acceptable for daily cron jobs

**3-Year TCO Comparison** (with Database):
- Koyeb: **$7.92** (includes FREE database) ✅ WINNER
- Fly.io: $21.96 (+$14.04) - No database included
- AWS Fargate: $21.96 (+$14.04) - No database included
- Railway: $180.00 (+$172.08) - Database included
- Render: $270.00 (+$262.08) - Database included

**Why Koyeb Wins**:
1. **$0.22/month** vs $0.61/month (Fly.io/Fargate) = **$4.68/year savings**
2. **FREE database** worth ~$360/year (typical Postgres costs $30-50/month elsewhere)
3. **No stopped charges** (Fly.io charges $0.30/month when stopped)
4. **Auto-sleep database** fits sporadic access pattern perfectly
5. **5h/month database limit** >> 1.85h actual usage = 63% buffer

**Important Note on Koyeb**:
- $0.94/month = Pay-as-you-go (30 hours) ✅ USE THIS
- $5.36/month = Reserved "Small" instance (730 hours always-on) ❌ DON'T USE for scheduled jobs

---

## 🏗️ Complete System Architecture Recommendations

### 🤔 **CRITICAL QUESTION: Do You Even Need PostgreSQL?**

**Let's analyze what data your trading bot ACTUALLY stores:**

#### What Data Does the Bot Need?

Based on your codebase (`bot_trading_system_requirements.md`, `core/config.py`, `DEPLOYMENT_SUMMARY.md`):

**Data Types**:
1. **Trading Signals** (generated daily):
   ```sql
   CREATE TABLE signals (
       id SERIAL PRIMARY KEY,
       date DATE NOT NULL,
       ticker VARCHAR(10) NOT NULL,
       signal VARCHAR(10),  -- 'BUY', 'SELL', 'HOLD'
       predicted_return DECIMAL(5,2),
       confidence DECIMAL(3,2),
       model VARCHAR(50),
       market VARCHAR(10),
       UNIQUE(market, date, ticker)  -- Prevents duplicates
   );
   ```

2. **Job Logs** (execution tracking):
   ```sql
   CREATE TABLE job_logs (
       id SERIAL PRIMARY KEY,
       timestamp TIMESTAMP DEFAULT NOW(),
       status VARCHAR(20),
       market VARCHAR(10),
       signals_generated INTEGER,
       execution_time DECIMAL(5,2)
   );
   ```

3. **Config Profiles** (trading parameters):
   ```sql
   CREATE TABLE config_profiles (
       id SERIAL PRIMARY KEY,
       market VARCHAR(10),
       name VARCHAR(50),
       holding_period INTEGER,
       hurdle_rate DECIMAL(4,2),
       stop_loss DECIMAL(4,2),
       tickers JSONB,  -- ["ABB.AX", "SIG.AX", ...]
       UNIQUE(market, name)
   );
   ```

4. **API Credentials** (encrypted secrets):
   ```sql
   CREATE TABLE api_credentials (
       id SERIAL PRIMARY KEY,
       service VARCHAR(50),
       encrypted_token TEXT,
       market VARCHAR(10)
   );
   ```

**Storage Characteristics**:
- **Daily Writes**: ~10-15 signal records/day (tiny!)
- **Total Size**: <1MB/month (1 year = 12MB, 10 years = 120MB)
- **Query Pattern**: Simple lookups (latest signals, history by ticker/date)
- **Relationships**: Minimal (signals linked to market, but no complex JOINs)

---

### 🆚 **Database Options Comparison for Trading Bot**

| Option | Cost | Complexity | Why Use It? | Why NOT? |
|--------|------|------------|-------------|----------|
| **Cloudflare D1** | $0 (5GB free) | 2-3 weeks rewrite | Serverless SQLite, free SQL | Must rewrite Flask → Workers (JS/TS) |
| **Cloudflare KV** | $0 (1GB free) | 3-5 days refactor | Simple key-value, no DB | No SQL queries, no JOINs, no indexes |
| **Cloudflare R2 + JSON** | $0 (10GB free) | 1-2 days refactor | No database at all! | Manual file management, slow queries |
| **PostgreSQL (Supabase Free)** | $0 (500MB) | 0 days | ✅ **Fully functional, production-ready** | Cross-region latency (+100ms) |
| **PostgreSQL (Neon Free)** | $0 (10GB) | 0 days | Always-on, larger storage | Cross-region latency (+100ms) |

---

### 🔍 **Why NOT Cloudflare D1 or KV?**

**Cloudflare D1 (SQLite Database)**:

**Pricing** (from official docs):
```
FREE Tier:
- 5 GB storage
- 5 million rows read/day
- 100,000 rows written/day
- No data transfer charges

PAID Tier (Workers Paid required):
- First 25 billion rows read/month included
- $0.001 per million additional rows read
- First 50 million rows written/month included
- $1.00 per million additional rows written
- First 5 GB included, $0.75/GB-month after
```

**Pros**:
- ✅ **FREE for trading bot** - 100K writes/day >> 15 signals/day
- ✅ **SQL**: Proper relational database (JOINs, indexes, transactions)
- ✅ **Serverless**: Auto-scales, no cold starts
- ✅ **No Egress**: Free data transfer
- ✅ **Global Replication**: Data replicated to 300+ locations

**Cons**:
- ❌ **Workers Only**: Must rewrite Flask (Python) → Cloudflare Workers (JavaScript/TypeScript)
- ❌ **SQLite Dialect**: Different from PostgreSQL (DATE types, JSON operators, window functions)
- ❌ **2-3 Weeks Rewrite**: Need to port:
  - `bot/models/*.py` (SQLAlchemy → D1 client)
  - `bot/services/*.py` (business logic)
  - `bot/routes/*.py` (Flask → Workers routing)
  - SQL migrations (PostgreSQL → SQLite syntax)
  - Testing stack (pytest → Workers testing framework)
- ❌ **Ecosystem**: No SQLAlchemy, pandas, numpy (Workers = JS environment)
- ❌ **AI Models**: Can't run RandomForest/CatBoost (Python-only libraries)

**Example Code Change**:
```python
# Current (Flask + PostgreSQL + SQLAlchemy):
from models import Signal
signals = Signal.query.filter_by(market='ASX', date=today).all()

# D1 (Workers + SQLite):
// JavaScript/TypeScript Workers
const result = await env.DB.prepare(
  'SELECT * FROM signals WHERE market = ? AND date = ?'
).bind('ASX', today).all();
```

**Verdict**: **NOT worth 2-3 weeks of rewriting + losing Python ecosystem for $0.22/month savings**

---

**Cloudflare KV (Key-Value Store)**:

**Pricing** (from official docs):
```
FREE Tier:
- 1 GB stored data
- 100,000 reads/day
- 1,000 writes/day
- 1,000 deletes/day
- 1,000 list operations/day

PAID Tier (Workers Paid required):
- First 1 GB included
- $0.50/GB-month after
- First 10 million reads/month included
- $0.50 per million additional reads
- First 1 million writes/month included
- $5.00 per million additional writes
```

**Pros**:
- ✅ **FREE for trading bot** - 1K writes/day >> 15 signals/day
- ✅ **Simple**: Just key-value pairs (like Redis)
- ✅ **Global CDN**: Replicates to 300+ locations (fast reads)
- ✅ **Fast**: <100ms reads globally

**Cons**:
- ❌ **No Queries**: Can't do `SELECT * FROM signals WHERE ticker='ABB.AX' AND date > '2026-01-01'`
- ❌ **No JOINs**: Can't link signals → job_logs → config_profiles
- ❌ **No Indexes**: Must iterate ALL keys to find matches
- ❌ **Manual Serialization**: Must JSON.stringify() everything
- ❌ **3-5 Days Refactor**: Replace SQLAlchemy models with KV logic

**Example Complexity**:
```python
# PostgreSQL (current code - 1 line):
signals = Signal.query.filter_by(market='ASX', date=today).all()

# Cloudflare KV (would need - 10+ lines):
// Must list all keys with prefix
const keys = await KV.list({ prefix: 'signal:ASX:' });

// Fetch each key individually
const signals = await Promise.all(
  keys.keys.map(async (key) => {
    const value = await KV.get(key.name);
    return JSON.parse(value);
  })
);

// Then manually filter by date in JavaScript
const filtered = signals.filter(s => s.date === today);
```

**Query Performance Comparison**:
```
PostgreSQL: SELECT WHERE date BETWEEN X AND Y
→ Uses index, scans ~100 rows in 5ms

KV: List all keys, fetch each, filter in memory
→ No indexes, scans 1000+ keys, fetches all, filters locally = 500ms+
```

**Verdict**: **KV too simple for trading bot's query patterns (historical analysis, filtering, aggregations)**

---

**Cloudflare R2 + JSON Files (No Database)**:

**Pricing** (from official docs):
```
FREE Tier:
- 10 GB storage
- Unlimited egress (no charges!)
- 10 million Class A operations/month (write/list)
- 10 million Class B operations/month (read)

PAID Tier:
- $0.015 per GB-month storage
- $4.50 per million Class A operations
- $0.36 per million Class B operations
```

**Pros**:
- ✅ **FREE**: 10GB >> 120MB needed (10-year capacity)
- ✅ **S3-Compatible**: Works with boto3 (Python SDK)
- ✅ **Simplest**: Just write JSON files daily
- ✅ **No Egress Fees**: Free bandwidth (unlike AWS S3)

**Cons**:
- ❌ **No Queries**: Must download entire file to filter data
- ❌ **No Transactions**: Risk of corrupt writes (no ACID)
- ❌ **No Concurrency**: File locking issues if multiple writes
- ❌ **Performance**: Slow for "find signals from last 30 days across 10 tickers"
- ❌ **Manual Indexing**: Must build your own query logic

**Example**:
```python
# PostgreSQL (current - fast):
signals = Signal.query.filter(
    Signal.ticker == 'ABB.AX',
    Signal.date >= '2026-01-01'
).all()  # 5ms with index

# R2 JSON Files (slow):
# Must download entire year's data
s3.download_file('signals-2026.json', '/tmp/signals.json')
with open('/tmp/signals.json') as f:
    all_signals = json.load(f)  # Load 3,650 records (365 days × 10 stocks)
    filtered = [s for s in all_signals if s['ticker'] == 'ABB.AX' and s['date'] >= '2026-01-01']
    # Inefficient: O(N) scan, no indexes
```

**File Structure Complexity**:
```
r2://trading-bot/
├── signals/
│   ├── 2026-01.json  (310 records)
│   ├── 2026-02.json  (280 records)
│   └── 2026-03.json  (310 records)
├── job_logs/
│   └── 2026-Q1.json
└── config_profiles/
    └── asx.json

# Must manage:
- File partitioning (monthly? daily?)
- Append vs overwrite logic
- Concurrent write locks
- File compaction/cleanup
```

**Verdict**: **Acceptable for append-only logs, but painful for queries (no indexes, no filtering)**

---

### ✅ **Why PostgreSQL (Supabase Free) Wins**

**Comprehensive Comparison**:

| Feature | Koyeb Free | Supabase Free | Cloudflare D1 | Cloudflare KV | Cloudflare R2 | Winner |
|---------|------------|---------------|---------------|---------------|---------------|--------|
| **Compute Hours** | ❌ 5h/month | ✅ Always-on | N/A | N/A | N/A | **Supabase** ✅ |
| **Storage** | 1GB | 500MB | 5GB | 1GB | 10GB | D1/R2 |
| **SQL Queries** | Full Postgres | Full Postgres | SQLite | ❌ None | ❌ None | **Supabase** ✅ |
| **Code Changes** | 0 days | 0 days | 2-3 weeks | 3-5 days | 1-2 days | **Supabase** ✅ |
| **Python Ecosystem** | ✅ Full | ✅ Full | ❌ JS only | ❌ JS only | ⚠️ boto3 only | **Supabase** ✅ |
| **AI Models** | ✅ Runs | ✅ Runs | ❌ Can't | ❌ Can't | ❌ Can't | **Supabase** ✅ |
| **Indexes/JOINs** | ✅ Full SQL | ✅ Full SQL | ⚠️ SQLite | ❌ None | ❌ Manual | **Supabase** ✅ |
| **Transactions** | ✅ ACID | ✅ ACID | ✅ ACID | ❌ None | ❌ None | **Supabase** ✅ |
| **Scaling Cost** | $29.76/mo | $25/mo Pro | $0.75/GB | $0.50/GB | $0.015/GB | **D1/KV/R2** |
| **Backup** | Manual | Pro: Auto | Manual | Manual | Manual | **Supabase Pro** |
| **Auto-Pause** | 5 min | 1 week | Never | Never | N/A | D1/KV |

**Why Cross-Region Latency Doesn't Matter for Trading Bot**:
- Trading bot queries database **~5 times per day** (not 5,000/second)
- Each query: **+50-100ms latency** from Koyeb Singapore → Supabase cross-region
- **Total daily latency**: 5 queries × 100ms = **0.5 seconds per day** (negligible)
- This is a **daily batch job**, NOT a real-time API (latency irrelevant for 08:00 cron)

**Key Advantages of PostgreSQL (Supabase)**:
1. ✅ **Zero Code Changes** - Already using PostgreSQL + SQLAlchemy + Python
2. ✅ **Production-Ready** - Schema, migrations, backups all working
3. ✅ **Always-On** - No 5h/month quota anxiety (vs Koyeb Free Postgres)
4. ✅ **500MB Sufficient** - Trading bot uses ~12MB/year (40x buffer for 40 years!)
5. ✅ **Python Ecosystem** - Can run RandomForest/CatBoost AI models
6. ✅ **Better Scaling** - $25/month Pro vs $29.76 Koyeb Small if >500MB needed
7. ✅ **ACID Transactions** - Data integrity guaranteed (vs file corruption risk)
8. ✅ **SQL Queries** - Complex filtering, aggregations, JOINs (vs manual iteration)

**When You SHOULD Consider Alternatives**:
- **D1**: If rewriting to Workers anyway (serverless edge compute benefits)
- **KV**: If you only store simple key-value data (no queries needed)
- **R2**: If you're storing large files (models, CSVs) - use R2 alongside Postgres!

**Current Recommendation**: **Use Supabase Free (always-on) + Cloudflare R2 (backups/files)**

---

### 🎯 **BEST Architecture: Koyeb Compute + Supabase Database** ($0.22/month)

#### Why Supabase Free Database Instead of Koyeb?

**Complete Analysis: PostgreSQL vs Cloudflare Alternatives**

**Option 1: Keep PostgreSQL (Supabase Free)** ✅ RECOMMENDED
- **Cost**: $0.00
- **Effort**: 0 days (already deployed)
- **Pros**: Production-ready, always-on, Python ecosystem, ACID transactions, SQL queries
- **Cons**: Cross-region +100ms latency (negligible for daily cron)

**Option 2: Switch to Cloudflare D1 (SQLite)**
- **Cost**: $0.00
- **Effort**: 2-3 weeks (rewrite Flask → Workers, port SQLAlchemy → D1 client)
- **Pros**: Serverless edge database, global replication
- **Cons**: Lose Python ecosystem (can't run RandomForest/CatBoost), SQLite dialect differences

**Option 3: Switch to Cloudflare KV (Key-Value)**
- **Cost**: $0.00  
- **Effort**: 3-5 days (replace SQLAlchemy with KV client)
- **Pros**: Simple key-value storage, fast global reads
- **Cons**: No SQL queries, no indexes, no JOINs (must iterate all keys)

**Option 4: Switch to Cloudflare R2 + JSON Files**
- **Cost**: $0.00
- **Effort**: 1-2 days (write file manager)
- **Pros**: Simplest storage, no database overhead
- **Cons**: No transactions, slow queries (download entire file), manual indexing

**🎯 Verdict: Keep PostgreSQL (Supabase Free)**

**Supabase vs Koyeb Free Postgres**:

| Feature | Koyeb Free | Supabase Free | Winner |
|---------|------------|---------------|--------|
| **Compute Hours** | ❌ 5h/month limit | ✅ Always-on (unlimited) | **Supabase** ✅ |
| **Storage** | ✅ 1GB | ⚠️ 500MB | Koyeb (but 500MB sufficient) |
| **Auto-Pause** | 5 min idle | 1 week idle | **Supabase** ✅ |
| **Region Co-location** | ✅ Same (Singapore) | ⚠️ Cross-region latency | Koyeb |
| **Query Latency** | <5ms | +50-100ms | Koyeb |
| **Scaling Path** | $29.76/month | $25/month Pro | **Supabase** ✅ |
| **Backups** | Manual only | CLI + Pro auto | **Supabase** ✅ |
| **Extra Features** | None | Realtime, Auth, Storage | **Supabase** ✅ |

**Why Supabase Wins Over ALL Options**:
1. ✅ **No 5h/month limit** - Always-on is simpler, no quota monitoring
2. ✅ **500MB >> 12MB/year needed** - Trading bot has 40+ years capacity
3. ✅ **Zero rewrite cost** - Already deployed, tested, production-ready
4. ✅ **Python ecosystem** - Can run AI models (RandomForest, CatBoost)
5. ✅ **SQL queries** - Complex filtering, JOINs, indexes (vs manual KV iteration)
6. ✅ **ACID transactions** - Data integrity (vs R2 file corruption risk)
7. ✅ **Better scaling path** - $25/month Pro vs $29.76 Koyeb Small
8. ⚠️ **Cross-region latency acceptable** - Daily cron queries (not real-time app)

**When Cross-Region Latency Doesn't Matter**:
- Trading bot queries database **~5 times per day** (not 5,000/second)
- Each query: +50-100ms latency = negligible for batch processing
- Total daily latency cost: 5 queries × 100ms = 0.5 seconds (acceptable)
- **Real-time apps** would suffer, but **daily cron jobs** don't care

#### Full Stack Components Analysis (REVISED)

| Component | Service | Cost/Month | Notes |
|-----------|---------|------------|-------|
| **Compute** | Koyeb eSmall | $0.22 | Flask app (30h/month) ✅ |
| **Database** | **Supabase Free** | **$0.00** | **Always-on, 500MB storage** ✅ |
| **Secrets** | Koyeb Secrets | $0.00 | Built-in secret management ✅ |
| **Storage** | Cloudflare R2 | $0.00 | 10GB free, CSV/JSON backups ✅ |
| **Monitoring** | Koyeb Metrics | $0.00 | Built-in logs/metrics (1 day) ✅ |
| **Domain** | Cloudflare DNS | $0.00 | Free DNS management ✅ |
| **SSL/CDN** | Koyeb/Cloudflare | $0.00 | Automatic HTTPS ✅ |
| **Notifications** | Telegram Bot API | $0.00 | Free notifications ✅ |
| **Total** | | **$0.22/month** | Complete system |

---

### 🎯 Recommended Architecture: Koyeb + Supabase + Cloudflare Stack

#### Why This Combination?

**✅ Pros**:
1. **Total Cost**: $0.22/month (Koyeb compute only)
2. **Everything Else Free**: Database (always-on!), storage, secrets, CDN, monitoring
3. **Zero Vendor Lock-In**: Can migrate compute to Fly.io/Railway anytime
4. **Simple Stack**: 3 vendors (Koyeb + Supabase + Cloudflare)
5. **Battle-Tested**: All three are production-grade platforms
6. **No compute quotas**: Database runs 24/7 (vs Koyeb 5h/month)

**⚠️ Trade-Offs**:
- Singapore compute + Cross-region database (+50-100ms per query, acceptable)
- 1-day log retention (sufficient for trading bot debugging)
- 500MB database storage (10x larger than needed ~50MB)

---

### 🔧 Component Deep Dive

#### 1. Compute: Koyeb eSmall
```yaml
Service: Koyeb Web Service
Instance: eSmall (0.5 vCPU, 1GB RAM, 8GB disk)
Region: Singapore
Cost: $0.22/month (30h active, auto-stop after 5min)
Deployment: Docker or Git (Flask native support)
```

**Built-In Features (FREE)**:
- ✅ Auto HTTPS/TLS certificates
- ✅ HTTP/2 and HTTP/3 support  - ✅ Zero-downtime deploys
- ✅ Health checks
- ✅ Auto-scaling (if needed)
- ✅ Private networking (service mesh)

#### 2. Database: Koyeb Postgres (FREE)
```yaml
Service: Koyeb Database Service
Instance: Free tier (0.25 vCPU, 1GB RAM)
Region: Singapore (must match compute region)
Cost: $0.00/month (5h compute limit, 1GB storage)
Engine: PostgreSQL 14/15/16/17
Auto-Sleep: 5 minutes idle
```

**What You Get**:
- ✅ Fully managed Postgres (backups, updates)
- ✅ Connection pooling (~112 connections)
- ✅ pgvector, PostGIS, timescaledb extensions available
- ✅ Bidirectional sync (control panel + SQL client)
- ✅ Auto-sleep on idle (saves compute hours)

**🔄 Cloudflare Database Alternatives?**

| Service | Type | Free Tier | Cost After Free | Trade-Offs |
|---------|------|-----------|----------------|------------|
| **Koyeb Postgres** ✅ | PostgreSQL | ⚠️ **NO COMPUTE LIMIT** (always-on free tier), 500MB storage | $29.76/month always-on | Same region, zero latency, perfect fit |
| Cloudflare D1 | SQLite | 5GB, 5M reads | $0.75/million reads | SQLite (not Postgres), need SQL rewrite |
| **Supabase** | PostgreSQL | ⚠️ **NO COMPUTE LIMIT** (always-on free tier), 500MB storage, **auto-pause after 1 week idle** | $25/month Pro | Always-on free tier, cross-region latency |
| Neon | PostgreSQL | 10GB, ⚠️ **NO COMPUTE LIMIT** (always-on but slower on free tier) | $19/month | Generous free tier, good for scaling |
| PlanetScale | MySQL | 5GB, 1B reads | $29/month | MySQL (not Postgres), need dialect changes |
| Turso | SQLite | 9GB, 1B reads | $29/month | SQLite, edge network overhead |

**⚠️ IMPORTANT CORRECTION: Koyeb vs Supabase Free Tiers**

I made an error about compute hour limits. Here's the truth:

**Koyeb Free Postgres**:
- ❌ **5h/month COMPUTE LIMIT** - Database only runs 5 hours total per month
- ✅ **1GB storage**
- ✅ **Auto-sleep after 5 min** - Efficient for sporadic usage
- 🎯 **Perfect for**: Trading bot with ~1.85h/month usage

**Supabase Free Postgres**:
- ✅ **NO COMPUTE LIMIT** - Database runs 24/7 (always-on)
- ⚠️ **500MB storage** (half of Koyeb)
- ⚠️ **Auto-pause after 1 week of inactivity** - Need manual unpause
- ⚠️ **Limit of 2 active projects** simultaneously
- 🎯 **Perfect for**: Always-on apps with frequent database access

**🎯 Verdict: Which Database to Use?**

| Scenario | Best Choice | Why |
|----------|-------------|-----|
| **Trading bot (1.85h/month)** | **Koyeb Postgres** ✅ | 5h limit > 1.85h usage, perfect fit |
| **Frequent admin panel access (10-20h/month)** | **Supabase Free** ✅ | Always-on, no compute limit, free |
| **Always-on production app** | **Supabase Free** ✅ | No compute limit, 24/7 availability |
| **Need >500MB storage on free tier** | **Koyeb Free** ✅ | 1GB vs Supabase 500MB |
| **Need >1GB storage** | **Neon Free** ✅ | 10GB storage, no compute limit |
| **Production with high usage** | **Supabase Pro ($25)** | Unlimited compute, 8GB storage, daily backups |

**When to use alternatives**:
- **Supabase Free** ($0): If database needs to run 24/7 or >5h/month, switch NOW
- **Neon** ($0 or $19/month): If database grows >1GB or needs >5h/month
- **Supabase Pro** ($25/month): If you need realtime subscriptions, auth, storage, daily backups
- **Cloudflare D1** ($0): Only if starting from scratch with SQLite
- **PlanetScale** ($0 or $29/month): If you prefer MySQL over Postgres

---

### 🔄 Supabase Database Backup & Restore Options

**Official Pricing Source**: https://supabase.com/pricing  
**Official Backup Docs**: https://supabase.com/docs/guides/platform/backups

#### Backup Types Available on Supabase:

| Backup Type | Free Plan | Pro Plan ($25/month) | How It Works |
|-------------|-----------|----------------------|--------------|
| **Automatic Daily Backups** | ❌ Not included | ✅ 7 days retention | pg_dumpall every 24h, downloadable SQL file |
| **Point-in-Time Recovery (PITR)** | ❌ Not included | ✅ $100-400/month add-on | WAL archiving, restore to any second (7-28 day retention) |
| **Manual Backups** | ✅ Included (DIY) | ✅ Included (DIY) | Use `pg_dump` or Supabase CLI anytime |
| **Physical Backups** | ❌ Auto (if >15GB) | ✅ Auto (if >15GB or PITR enabled) | WAL-G snapshots, not downloadable |

#### Detailed Backup & Restore Capabilities:

**1. FREE PLAN Backups**:
```yaml
Automatic Backups: ❌ None (you must do manual backups yourself)
Manual Backup Options:
  - Supabase CLI: supabase db dump -f backup.sql
  - pg_dump: Direct Postgres connection
  - Export via Dashboard: SQL Editor → Export queries
  
Restore Options:
  - Manual restore via psql or Supabase CLI
  - No one-click restore (must re-import SQL file)

Cost: $0/month
Best For: Non-critical projects where manual backups acceptable
```

**2. PRO PLAN ($25/month) - Daily Backups**:
```yaml
Automatic Daily Backups: ✅ Yes (7-day retention)
Backup Method: Logical backups (pg_dumpall)
Backup Time: Daily at fixed time (managed by Supabase)
Downloadable: ✅ Yes (SQL files from Dashboard)

Restore Process:
  1. Dashboard → Database → Backups → Scheduled backups
  2. Select backup date (last 7 days)
  3. Click "Restore" → Confirmation → Automatic restore
  4. Downtime: Depends on database size (5 min - 2 hours)

Recovery Point Objective (RPO): Up to 24 hours data loss
Cost: Included in $25/month Pro plan
Best For: Production apps with acceptable 24h data loss window
```

**3. PRO PLAN + PITR Add-On ($100-400/month)**:
```yaml
Point-in-Time Recovery: ✅ Yes (restore to any second)
Retention Options:
  - 7 days: $100/month ($0.137/hour)
  - 14 days: $200/month ($0.274/hour)
  - 28 days: $400/month ($0.55/hour)

Backup Method: Physical backups + WAL archiving
WAL Backup Frequency: Every 2 minutes (or when 16MB reached)
Granularity: Down to the second

Restore Process:
  1. Dashboard → Database → Backups → Point in Time
  2. Select exact date/time (calendar picker)
  3. Restore to chosen second (e.g., 2026-02-05 14:23:47)
  4. Downtime: Depends on database size + WAL replay time

Recovery Point Objective (RPO): 2 minutes maximum data loss
Cost: $25/month (Pro) + $100-400/month (PITR addon)
Total: $125-425/month
Best For: Mission-critical apps requiring <2 min RPO
```

**4. Manual Backup Strategy (All Plans)**:
```bash
# Using Supabase CLI (recommended)
supabase db dump --db-url "postgresql://..." -f backup.sql.gz

# Using pg_dump directly
pg_dump "postgresql://postgres:[password]@[host]:5432/postgres" > backup.sql

# Schedule via cron (free backup automation)
0 2 * * * /usr/local/bin/supabase db dump -f /backups/$(date +\%Y\%m\%d).sql.gz

# Upload to Cloudflare R2 (free storage)
aws s3 cp backup.sql.gz s3://your-bucket/ --endpoint-url https://...r2.cloudflarestorage.com
```

#### 📊 Backup Strategy Comparison:

| Strategy | Cost/Month | RPO | Restore Difficulty | Best For |
|----------|------------|-----|-------------------|----------|
| **Manual + R2** | $0.22 (Koyeb) + $0 (R2) | 24h (daily cron) | Manual (1-2h) | Trading bot ✅ |
| **Supabase Pro Daily** | $25 | 24h | One-click (5min-2h) | Production apps |
| **Supabase PITR 7-day** | $125 | 2 minutes | One-click (10min-4h) | High-value data |
| **Koyeb + Manual** | $0.22 | 24h | Manual (1-2h) | Cost-conscious ✅ |

#### 🎯 Recommended Backup Strategy for Trading Bot:

**Option A: Koyeb + Manual Backups to R2** ($0.22/month total) - **RECOMMENDED**

```yaml
Setup:
  1. Daily cron job (part of existing 30h/month compute)
  2. pg_dump Koyeb database → compress → upload to Cloudflare R2
  3. Retention: 30 days rolling (within R2 10GB free tier)

Cost Breakdown:
  - Koyeb compute: $0.22/month (includes backup cron time)
  - Cloudflare R2: $0/month (backups ~50MB × 30 days = 1.5GB << 10GB free)
  - Total: $0.22/month

Restore Process (if disaster):
  1. Download backup from R2
  2. Create new Koyeb database (or restore existing)
  3. psql < backup.sql (5-10 minutes)

Recovery Point Objective: 24 hours (acceptable for daily trading signals)
Pros: ✅ Completely free, ✅ Full control
Cons: ⚠️ Manual restore (1-2 hours work)
```

**Option B: Migrate to Supabase Free** ($0.22/month Koyeb compute) - **If >5h/month database usage**

```yaml
Setup:
  1. Migrate database from Koyeb → Supabase Free
  2. Always-on database (no 5h limit)
  3. Manual backups via Supabase CLI → R2

Cost Breakdown:
  - Koyeb compute: $0.22/month (Flask app)
  - Supabase database: $0/month (free tier, always-on)
  - Cloudflare R2: $0/month (backups)
  - Total: $0.22/month

Restore Process:
  - Same as Option A (manual pg_dump/restore)

When to choose:
  - If database usage exceeds 5h/month
  - If you want always-on database availability
  - If 500MB storage sufficient (trading bot uses ~50MB)
```

**Option C: Upgrade to Supabase Pro** ($25.22/month total) - **If backups critical**

```yaml
Setup:
  1. Migrate to Supabase Pro ($25/month)
  2. Automatic daily backups (7-day retention)
  3. One-click restore from Dashboard

Cost Breakdown:
  - Koyeb compute: $0.22/month (Flask app)
  - Supabase Pro: $25/month (8GB database + daily backups)
  - Total: $25.22/month

Restore Process:
  - Dashboard → Backups → Select date → Restore (5-10 min)

When to choose:
  - If manual backups feel risky
  - If you want professional backup infrastructure
  - If one-click restore worth $25/month peace of mind
```

#### ✅ Final Recommendation:

**For Trading Bot**: Use **Option A** (Koyeb + Manual R2 Backups) at $0.22/month

**Why**:
1. ✅ Total cost: $0.22/month (vs $25/month Supabase Pro)
2. ✅ 30-day backup history (vs 7 days Supabase Pro)
3. ✅ Full control over backup schedule
4. ✅ Disaster recovery acceptable: Daily signal generation means 24h RPO is fine
5. ✅ Storage is free: Cloudflare R2 10GB >> 1.5GB backups

**Backup Script** (add to cron job):
```python
# Add to daily cron job (runs within existing 30h/month)
import subprocess
import boto3
from datetime import datetime

def backup_database():
    # Dump database
    timestamp = datetime.now().strftime('%Y%m%d')
    dump_file = f"/tmp/trading_bot_{timestamp}.sql.gz"
    subprocess.run([
        "pg_dump", 
        os.getenv("DATABASE_URL"),
        "|", "gzip", ">", dump_file
    ])
    
    # Upload to R2
    r2 = boto3.client('s3', endpoint_url=os.getenv("R2_ENDPOINT"))
    r2.upload_file(dump_file, "trading-bot", f"backups/{timestamp}.sql.gz")
    
    # Delete local file
    os.remove(dump_file)
    
    # Cleanup old backups (>30 days)
    # ... retention logic ...
```

**When to upgrade to Supabase Pro**:
- If trading bot becomes production SaaS with paying users
- If 24h RPO becomes unacceptable (need <2 min RPO → PITR)

---

### 🚨 Database Scaling Strategy: What If You Exceed 5 Hours/Month?

**Question**: *"If in future I have multiple sessions querying Postgres, what can I do? Should I move to Cloudflare D1?"*

**Answer**: ❌ **NO, don't move to Cloudflare D1** - here's why and what to do instead:

#### Why NOT Cloudflare D1?

| Issue | Impact | Migration Effort |
|-------|--------|------------------|
| **SQLite vs Postgres** | Completely different database engines | 2-3 weeks rewrite |
| **SQL Dialect** | Different syntax (`AUTOINCREMENT` vs `SERIAL`, `||` vs `CONCAT`) | Rewrite all queries |
| **No Extensions** | No pgvector, PostGIS, timescaledb support | Remove ML features |
| **Different Limits** | Max 10MB per query result | Redesign data fetch logic |
| **No JSONB** | Less efficient JSON handling | Rewrite JSON columns |

**Cost of Migration**: 2-3 weeks developer time = $5,000-$10,000 equivalent vs **$29.76/month** to upgrade Koyeb = 17-34 months of hosting costs.

---

#### ✅ Proper Database Scaling Path

**Scenario 1: Exceeding 5h/month but <100h/month** (Most Likely)

```yaml
Current: Koyeb Free Postgres (5h/month)
Problem: Usage grows to 10-20h/month (more admin panel access, longer queries)
Solution: Upgrade to Koyeb Small Postgres
Cost: $29.76/month (0.25 vCPU, 1GB RAM, always-on)

Why This Works:
- ✅ Zero migration (same database, just upgrade tier)
- ✅ Same region (no latency change)
- ✅ 730h/month available (always-on)
- ✅ Same connection strings (no code changes)
- ✅ Automatic upgrade path (1-click in dashboard)

Total System Cost:
- Compute: $0.22/month (Koyeb eSmall, 30h)
- Database: $29.76/month (Koyeb Small, always-on)
─────────────────────────────────────────────
Total: $29.98/month = $359.76/year
```

**Scenario 2: Need More Storage (>1GB database)**

```yaml
Current: Koyeb Free Postgres (1GB storage limit)
Problem: Database grows to 5-10GB (years of historical data)
Solution Option A: Koyeb Medium Postgres
Cost: $59.52/month (0.5 vCPU, 2GB RAM, unlimited storage)

Solution Option B: Migrate to Neon
Cost: $19/month (10GB storage, 100h compute)
Migration: Export Koyeb → Import Neon (1-2 hours, zero rewrite)

Why Neon Wins for Storage:
- ✅ $19/month vs $59.52/month (68% cheaper)
- ✅ 10GB storage included vs 2GB RAM limit
- ✅ 100h compute/month (trading bot uses ~2h/month)
- ✅ Same PostgreSQL (pgdump → pgrestore)
- ✅ Better scaling (can grow to 200GB on Pro plan)

Total System Cost with Neon:
- Compute: $0.22/month (Koyeb eSmall)
- Database: $19.00/month (Neon Launch)
─────────────────────────────────────────────
Total: $19.22/month = $230.64/year
```

**Scenario 3: High Query Volume (>100h/month)**

```yaml
Current: Koyeb Free Postgres (5h/month)
Problem: Multiple concurrent sessions, 200h/month database usage
Solution: Migrate to managed Postgres with better pricing
Options:
  A. Supabase Pro: $25/month (8GB database, unlimited compute hours)
  B. Neon Scale: $69/month (50GB database, 750h compute)
  C. AWS RDS: $45/month (db.t4g.micro, 20GB SSD, always-on)

Best Choice: Supabase Pro ($25/month)
- ✅ Unlimited compute hours (no 5h/100h limits)
- ✅ 8GB database storage
- ✅ Connection pooling (handles concurrent sessions)
- ✅ Realtime subscriptions (bonus feature)
- ✅ Auto backups daily

Total System Cost with Supabase:
- Compute: $0.22/month (Koyeb eSmall)
- Database: $25.00/month (Supabase Pro)
─────────────────────────────────────────────
Total: $25.22/month = $302.64/year
```

---

#### 📊 Database Migration Cost Comparison

| Scenario | Current | Solution | Monthly Cost | Migration Effort |
|----------|---------|----------|--------------|------------------|
| **<5h/month** | Koyeb Free | Keep free tier | **$0.22** | None ✅ |
| **5-100h/month** | Koyeb Free | Upgrade Koyeb Small | **$29.98** | 1-click upgrade ✅ |
| **>1GB storage** | Koyeb Free | Migrate to Neon | **$19.22** | 1-2 hours ✅ |
| **>100h + concurrent** | Koyeb Free | Migrate to Supabase | **$25.22** | 1-2 hours ✅ |
| **Wrong path** ❌ | Koyeb Free | Rewrite for D1 | **$0.22** | 2-3 weeks ❌ |

**Time-to-Value Analysis**:
- **Upgrade Koyeb**: 5 minutes (dashboard click)
- **Migrate to Neon/Supabase**: 1-2 hours (pgdump + connection string update)
- **Rewrite for D1**: 2-3 weeks (SQL dialect conversion, testing, debugging)

---

#### 🎯 Recommended Scaling Strategy

**Phase 1: Monitor Usage (Months 1-3)**
```yaml
Action: Check Koyeb database metrics monthly
Watch for:
  - Compute hours approaching 5h/month
  - Storage approaching 1GB
  - Connection limit warnings (~112 connections)
Tool: Koyeb Dashboard → Database Service → Metrics
```

**Phase 2: Proactive Upgrade (Month 4+)**
```yaml
If compute >4h/month for 2 consecutive months:
  → Upgrade to Koyeb Small ($29.76/month)
  → Prevents unexpected service disruption
  → 1-click upgrade, zero downtime

If storage >800MB:
  → Plan migration to Neon ($19/month)
  → More cost-effective for storage scaling
  → Schedule during maintenance window
```

**Phase 3: Optimization Before Upgrade**
```yaml
Before upgrading, try these optimizations:
1. Query optimization:
   - Add indexes on frequently queried columns
   - Reduce SELECT * queries (fetch only needed columns)
   - Use connection pooling (pgbouncer)
   
2. Data archiving:
   - Move old data to Cloudflare R2 (CSV exports)
   - Keep only last 90 days in database
   - Reduces storage and query time

3. Caching:
   - Cache frequently accessed data in Redis/Memcached
   - Reduces database compute hours
   - Cloudflare KV ($0.50/million reads) as cache layer
```

---

#### 💡 Real-World Example: Trading Bot Growth

**Year 1** (Months 1-12):
```
Database Usage: 1.85h/month (admin panel + cron jobs)
Storage: 50MB (12 months of data)
Cost: $0.22/month (Koyeb Free tier sufficient)
Action: None needed
```

**Year 2** (Months 13-24):
```
Database Usage: 6.5h/month (expanded to 3 markets, more admin access)
Storage: 150MB (24 months of data)
Solution: Still within Supabase Free 500MB, no action needed
Cost: Still $0.22/month total
Action: None
```

**Year 3** (Months 25-36):
```
Database Usage: Still within always-on Supabase Free limits
Storage: 400MB (36 months of data, still <500MB)
Cost: Still $0.22/month total
Action: If approaching 500MB, migrate to Supabase Pro ($25/month) or Neon ($19/month)
Migration: 1-2 hours if needed, pgdump → import
Savings: Stayed on free tier for 3 years = $0 database cost
```

**Why This Growth Path Works with Supabase Free**:
1. ✅ **No compute hour anxiety** - Always-on means no 5h/month quota to worry about
2. ✅ **500MB sufficient for years** - Trading bot data grows slowly (~50MB/year)
3. ✅ **Only upgrade when storage limit reached** - Not compute hours
4. ✅ **Better paid tier** - Supabase Pro $25/month < Koyeb Small $29.76/month

---

#### 🚫 Why Cloudflare D1 is NOT the Answer

**D1 is designed for**:
- ✅ New apps built from scratch with SQLite
- ✅ Edge compute (Cloudflare Workers + D1 co-location)
- ✅ Read-heavy workloads (5 million reads/month free)
- ✅ Small datasets (<5GB)

**D1 is NOT suitable for**:
- ❌ Migrating existing Postgres apps (SQL rewrite required)
- ❌ Complex queries (SQLite has fewer features)
- ❌ Heavy write workloads (optimized for reads)
- ❌ PostgreSQL extensions (pgvector, PostGIS, etc.)

**Migration Comparison**:

| Task | Upgrade Koyeb | Migrate Neon | Migrate D1 |
|------|---------------|--------------|------------|
| **Time** | 5 minutes | 1-2 hours | 2-3 weeks |
| **Code Changes** | Zero | Connection string only | Rewrite all SQL |
| **Risk** | None | Low | High |
| **Rollback** | Instant | Easy | Difficult |
| **Cost** | +$29.76/month | +$19/month | +$0/month |
| **Value** | ✅ Effortless | ✅ Best ROI | ❌ High risk |

---

#### ✅ Final Answer to Your Question

**"If in future I have multiple sessions querying Postgres, what can I do?"**

**Short Answer**: You're already using **Supabase Free** (always-on, unlimited compute), so multiple sessions work out-of-the-box. If you exceed **500MB storage**, migrate to **Supabase Pro** ($25/month) or **Neon** ($19/month). Both take <2 hours and require zero SQL rewriting.

**Do NOT** migrate to Cloudflare D1 because:
1. ❌ SQLite ≠ Postgres (2-3 weeks rewrite)
2. ❌ Developer time worth more than $25/month hosting
3. ❌ Risk of bugs from SQL dialect differences
4. ✅ Supabase Free already handles unlimited sessions (no 5h limit like Koyeb)

**Migration Priority**:
1. **First**: Use Supabase Free (recommended architecture, always-on)
2. **Then**: Optimize queries and add indexes if slow (free)
3. **Finally**: Upgrade to Supabase Pro ($25) or Neon ($19) only when storage >500MB

**Cost Impact**:
- Supabase Free: $0.22/month (compute only, unlimited database sessions)
- Supabase Pro: $25.22/month (if >500MB storage needed)
- Never rewrite for D1: Saves 2-3 weeks developer time

**Data Backup Strategy**:
```python
# Daily backup to Cloudflare R2 via cron job
# Cost: $0 (within R2 10GB free tier)
import boto3  # S3-compatible API

def backup_to_r2():
    # pg_dump → compress → upload to R2
    # Retention: 30 days (rolling)
```

#### 3. Secret Management: Koyeb Secrets (FREE)

**What Are Koyeb Secrets?**

Koyeb Secrets is a **built-in secret management system** included with every Koyeb account at no cost. It's similar to AWS Secrets Manager, HashiCorp Vault, or Doppler, but integrated directly into the Koyeb platform.

```yaml
Service: Koyeb Secrets (Built-in Feature)
Cost: $0.00/month (unlimited secrets on all plans)
Storage: Encrypted at rest (AES-256)
Access: Encrypted in transit, injected as environment variables
Regions: Global (secrets replicated across regions)
Features:
  - ✅ Unlimited secrets (no per-secret charges like AWS $0.40/secret/month)
  - ✅ Automatic injection into services at runtime
  - ✅ Secret rotation via CLI/API
  - ✅ Version history (Pro plan)
  - ✅ Audit logging (Pro plan)
  - ✅ Access control per service
```

**How Koyeb Secrets Work**:

1. **Create Secret** (one-time):
   ```bash
   # Via CLI
   koyeb secrets create TELEGRAM_BOT_TOKEN --value "7123456789:AAHdqTcvCH1vGW..." 
   koyeb secrets create SUPABASE_KEY --value "eyJhbGciOiJIUzI1NiIs..."
   koyeb secrets create DATABASE_URL --value "postgresql://user:pass@host/db"
   
   # Via Web UI
   # Koyeb Dashboard → Secrets → Create Secret → Name + Value
   ```

2. **Reference in Service** (deployment time):
   ```bash
   # Environment variables automatically injected
   koyeb service update trading-bot \
     --env TELEGRAM_TOKEN=@TELEGRAM_BOT_TOKEN \
     --env SUPABASE_KEY=@SUPABASE_KEY \
     --env DATABASE_URL=@DATABASE_URL
   ```

3. **Use in Code** (runtime):
   ```python
   # Flask app reads from environment variables
   import os
   
   TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')  # Decrypted at runtime
   SUPABASE_KEY = os.getenv('SUPABASE_KEY')
   DATABASE_URL = os.getenv('DATABASE_URL')
   ```

**🔄 Alternative Secret Management Options**:

| Service | Free Tier | Paid Plan | When to Use |
|---------|-----------|-----------|-------------|
| **Koyeb Secrets** ✅ | Unlimited | $0/month | Default choice, perfect for most use cases |
| Doppler | 5 secrets | $7/month | If you need advanced features (branching, approval workflows) |
| AWS Secrets Manager | 30-day trial | $0.40/secret/month | If already using AWS heavily |
| HashiCorp Vault | Self-hosted | $0 (OSS) | If you need on-premise or complex policies |
| Infisical | Unlimited | $0/month (OSS) | If you want self-hosted open-source |
| 1Password Secrets | 25 secrets | $7/month | If team already uses 1Password |

**🎯 Verdict: Use Koyeb Secrets** because:
- ✅ **Free unlimited secrets** (vs AWS $0.40/secret)
- ✅ **Zero configuration** (already integrated)
- ✅ **No external vendor** (one less service to manage)
- ✅ **Automatic rotation** via API (can script updates)
- ✅ **Sufficient for trading bot** (5-10 secrets: API keys, DB credentials)

**When to use alternatives**:
- **Doppler**: If you need multi-environment secrets (dev/staging/prod) with approval workflows
- **AWS Secrets Manager**: If you're already using 10+ AWS services
- **Infisical**: If you need self-hosted due to compliance requirements

**How It Works**:
```bash
# Store secrets in Koyeb
koyeb secrets create TELEGRAM_BOT_TOKEN --value "your-token"
koyeb secrets create SUPABASE_KEY --value "your-key"

# Reference in service
koyeb service update trading-bot \
  --env TELEGRAM_TOKEN=@TELEGRAM_BOT_TOKEN \
  --env SUPABASE_KEY=@SUPABASE_KEY
```

**Alternative: Doppler** (if you need advanced features)
- Cost: $0/month (Hobby plan, 5 secrets)
- Features: Secret rotation, version history, multi-environment
- Integration: Doppler → Koyeb env vars

#### 4. Storage: Cloudflare R2 (FREE)
```yaml
Service: Cloudflare R2 (S3-compatible)
Free Tier: 10GB storage, 1M Class A operations/month
Cost: $0.00/month (trading bot uses ~50MB)
Use Cases:
  - CSV/JSON data backups
  - Model training data archives
  - Historical price data (long-term)
```

**Pricing After Free Tier**:
- Storage: $0.015/GB/month ($0.75 for 50GB)
- Class A (writes): $4.50 per million requests
- Class B (reads): $0.36 per million requests
- **No egress fees** (huge advantage vs S3)

**Why R2 vs S3?**:
| Feature | Cloudflare R2 | AWS S3 |
|---------|---------------|--------|
| **Storage** | $0.015/GB | $0.023/GB (Standard) |
| **Egress** | **$0** | $0.09/GB (expensive!) |
| **API** | S3-compatible | Native |
| **Free Tier** | 10GB forever | 5GB first year only |
| **Use Case** | Perfect for backups | Better for AWS ecosystem |

**Setup Example**:
```python
# Install: pip install boto3
import boto3

r2 = boto3.client(
    's3',
    endpoint_url='https://<account-id>.r2.cloudflarestorage.com',
    aws_access_key_id='<r2-access-key>',
    aws_secret_access_key='<r2-secret-key>'
)

# Upload daily backup
r2.upload_file('backup.sql.gz', 'trading-bot', 'backups/2026-02-05.sql.gz')
```

---

## 8. Final Deployment Setup Guide

### 🎯 **Complete Architecture: Koyeb + Supabase + Cloudflare** ($0.22/month)

**System Components**:
```
money.twoudia.com (Cloudflare DNS - FREE)
    ↓
Koyeb Web Service - Singapore ($0.22/month)
    ↓
Supabase PostgreSQL - Singapore/Tokyo (FREE, always-on)
    ↓
Cloudflare R2 - Backups (FREE, 10GB)
```

---

### 📋 **Step-by-Step Deployment**

#### **Step 1: Domain & DNS Setup** (5-10 minutes)

**⚠️ Your Current Situation**: `twoudia.com` DNS is NOT on Cloudflare

**Choose ONE option below:**

---

**Option A: Delegate ONLY Subdomain to Cloudflare** ✅ **PERFECT SOLUTION** (10 minutes)

**What This Does**:
- Keep `twoudia.com` at your current DNS provider
- Delegate ONLY `money.twoudia.com` to Cloudflare
- Get Cloudflare features (DDoS, CDN, R2) for subdomain only

**Setup Steps**:

**Part 1: Setup Cloudflare (5 minutes)**

1. **Create Cloudflare Account** (free):
   - Go to: https://dash.cloudflare.com/sign-up

2. **DON'T add twoudia.com to Cloudflare!** (this would require full DNS transfer)

3. **Just note Cloudflare's nameservers** (you'll need these):
   ```
   You'll use Cloudflare's assigned nameservers later
   We'll get these in Part 2
   ```

**Part 2: Get Cloudflare DNS Nameservers for Subdomain (2 minutes)**

Since Cloudflare doesn't have a UI for subdomain-only DNS, we'll use **Cloudflare for SaaS** or a workaround:

**Workaround Method** (works immediately):

1. **Create a dummy domain in Cloudflare**:
   - Dashboard → Add Site → Enter "money-twoudia.com" (not your real domain)
   - Select: Free Plan
   - Cloudflare will assign nameservers like:
     ```
     ns1.cloudflare.com
     ns2.cloudflare.com
     ```
   - **SAVE THESE** - you'll use them in Part 3

2. **After setup, manage DNS for "money.twoudia.com" here**:
   - Even though Cloudflare thinks it's "money-twoudia.com", we'll make it work for "money.twoudia.com"

**Part 3: Delegate Subdomain at Your Current DNS Provider (3 minutes)**

1. **Log into your current DNS provider** (GoDaddy/Namecheap/Route53/etc.)

2. **Add NS Records for subdomain**:
   ```
   Add DNS Record #1:
   Type:    NS
   Host:    money.twoudia.com  (or just "money" depending on provider)
   Value:   ns1.cloudflare.com
   TTL:     1 hour
   
   Add DNS Record #2:
   Type:    NS
   Host:    money.twoudia.com  (or just "money")
   Value:   ns2.cloudflare.com
   TTL:     1 hour
   ```

3. **Wait 5-30 minutes for DNS propagation**

4. **Verify delegation works**:
   ```bash
   # Check if subdomain is delegated to Cloudflare
   dig NS money.twoudia.com
   
   # Should show:
   # money.twoudia.com.  3600  IN  NS  ns1.cloudflare.com.
   # money.twoudia.com.  3600  IN  NS  ns2.cloudflare.com.
   ```

**Part 4: Add CNAME in Cloudflare (1 minute)**

1. **Go back to Cloudflare** → The dummy domain you created

2. **Add DNS Record**:
   ```
   Type:    CNAME
   Name:    @  (this represents money.twoudia.com)
   Target:  trading-bot-abc123.koyeb.app  (from Koyeb deployment)
   Proxy:   🔘 DNS Only (gray cloud)
   TTL:     Auto
   ```

**Done!** Now:
- ✅ `money.twoudia.com` is managed by Cloudflare
- ✅ `twoudia.com` stays at your current DNS provider
- ✅ You get Cloudflare DDoS protection, CDN, R2 for the subdomain
- ✅ No full domain transfer needed

**Pros**:
- ✅ Keep main domain at current provider (no disruption)
- ✅ Get Cloudflare features for subdomain only
- ✅ Easy R2 integration
- ✅ Faster than full DNS transfer (works in 10 minutes)

**Cons**:
- ⚠️ Slightly more complex setup (but only one-time)
- ⚠️ Two DNS providers to manage (but isolated by subdomain)

---

**Option B: Use Your Current DNS Provider** ✅ **SIMPLEST** (5 minutes)

**Setup Steps**:

1. **Log into your current DNS provider** (GoDaddy/Namecheap/Google Domains/etc.)

2. **Add CNAME Record for Subdomain**:
   ```
   Add DNS Record:
   
   Type:    CNAME
   Host:    money
   Target:  <will-get-from-koyeb>.koyeb.app
   TTL:     1 hour (or default)
   ```

3. **Get Koyeb Domain** (from Step 3 below):
   - After creating Koyeb service, you'll get: `trading-bot-abc123.koyeb.app`
   - Update CNAME Target to: `trading-bot-abc123.koyeb.app`

4. **Wait for DNS Propagation** (5-30 minutes):
   ```bash
   # Check if DNS updated
   dig money.twoudia.com
   # or
   nslookup money.twoudia.com
   ```

**Pros**:
- ✅ Fastest (5 minutes setup, no DNS transfer)
- ✅ Keep existing DNS provider
- ✅ No Cloudflare account needed

**Cons**:
- ⚠️ No Cloudflare CDN/DDoS protection
- ⚠️ No Cloudflare R2 integration (but can still use R2 via API)

---

**Option B: Transfer DNS to Cloudflare** ✅ **RECOMMENDED** (24-48 hours)

**Why Transfer to Cloudflare?**:
- ✅ FREE DNS management (no annual fees)
- ✅ DDoS protection included
- ✅ Faster DNS resolution (global Anycast network)
- ✅ Easy R2 integration
- ✅ Web Application Firewall (WAF) available
- ✅ Analytics and monitoring included

**Setup Steps**:

1. **Create Cloudflare Account** (if you don't have one):
   - Go to: https://dash.cloudflare.com/sign-up
   - Free plan is sufficient

2. **Add Domain to Cloudflare**:
   ```
   Dashboard → Add Site → Enter "twoudia.com"
   Select: Free Plan ($0/month)
   ```

3. **Cloudflare Scans Your DNS Records**:
   - Cloudflare auto-imports existing DNS records
   - Review and confirm all records are correct

4. **Update Nameservers at Your Registrar**:
   ```
   Cloudflare will show you two nameservers:
   
   ns1.cloudflare.com
   ns2.cloudflare.com
   
   Log into your domain registrar (GoDaddy/Namecheap/etc.)
   → Domain Settings → Nameservers
   → Change to Custom Nameservers:
      - ns1.cloudflare.com
      - ns2.cloudflare.com
   ```

5. **Wait for DNS Propagation** (24-48 hours):
   - Cloudflare will email when transfer is complete
   - Usually takes 4-8 hours in practice

6. **Add CNAME Record in Cloudflare**:
   ```
   DNS → Add Record:
   
   Type:    CNAME
   Name:    money
   Target:  trading-bot-abc123.koyeb.app  (from Koyeb)
   Proxy:   🔘 DNS Only (gray cloud) ← IMPORTANT!
   TTL:     Auto
   ```

   **⚠️ CRITICAL**: Use **"DNS Only"** (gray cloud), NOT "Proxied" (orange cloud)
   - **Why?**: Koyeb health checks need direct connection
   - **SSL?**: Still works! Koyeb provides Let's Encrypt certificate

**Pros**:
- ✅ Best long-term solution
- ✅ FREE forever (no DNS fees)
- ✅ DDoS protection + CDN
- ✅ Easy R2 integration

**Cons**:
- ⚠️ Takes 24-48 hours for nameserver change
- ⚠️ Requires updating registrar settings

---

**Option C: Use Koyeb Default Domain** ✅ **NO CUSTOM DOMAIN** (0 minutes)

**Setup Steps**:

1. **Deploy to Koyeb** (Step 3 below)
2. **Use Koyeb's auto-generated domain**:
   ```
   https://trading-bot-abc123.koyeb.app
   ```

**Pros**:
- ✅ Instant (no DNS setup)
- ✅ Free SSL included
- ✅ No domain registration needed

**Cons**:
- ⚠️ Long, ugly URL (`trading-bot-abc123.koyeb.app`)
- ⚠️ Can't use your brand (`twoudia.com`)
- ⚠️ URL changes if you recreate service

**Use Case**: Testing/development before custom domain setup

---

**Option D: Buy New Domain on Cloudflare** (if starting fresh)

**Cost**: $9.77/year (.com domain)

**Setup Steps**:
1. Cloudflare Dashboard → Domain Registration → Buy `trading-bot.com`
2. Auto-configures Cloudflare DNS (no manual nameserver setup)
3. Add CNAME record for subdomain

---

**Recommended Decision Tree**:

```
Do you want Cloudflare features (DDoS, CDN, R2) for money.twoudia.com?
├─ YES → Want to keep twoudia.com at current DNS provider?
│   ├─ YES → Option A: Delegate subdomain to Cloudflare ✅ PERFECT!
│   └─ NO  → Option C: Transfer entire domain to Cloudflare
└─ NO  → Option B: Use current DNS provider (simple CNAME)

Quick start for testing?
└─ Option D: Use Koyeb default domain (no DNS setup)
```

**My Recommendation for You**: **Option A - Subdomain Delegation** ✅

**Why?**
- ✅ Keep `twoudia.com` unchanged at current provider
- ✅ Get Cloudflare R2 integration for trading bot backups
- ✅ DDoS protection for trading bot specifically
- ✅ Works in 10 minutes (vs 24-48 hours for full transfer)
- ✅ Isolated setup (if something breaks, main domain unaffected)

---

#### **Step 2: Supabase Database Setup** (10 minutes)

1. **Create Supabase Account**:
   - Go to: https://supabase.com/dashboard
   - Sign up with GitHub (free)

2. **Create New Project**:
   ```
   Organization: Your Name
   Project Name: trading-bot-asx
   Database Password: <generate-strong-password>  # SAVE THIS!
   Region: Southeast Asia (Singapore)  # Closest to Koyeb
   Plan: Free
   ```

3. **Get Connection String**:
   ```
   Project Settings → Database → Connection String → URI
   
   Example:
   postgresql://postgres:[YOUR-PASSWORD]@db.abcdefghijk.supabase.co:5432/postgres
   ```

4. **Create Database Schema**:
   - SQL Editor → New Query:
   ```sql
   -- Create signals table
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
       UNIQUE(market, date, ticker)
   );

   -- Create index for faster queries
   CREATE INDEX idx_signals_market_date ON signals(market, date);
   CREATE INDEX idx_signals_ticker ON signals(ticker);

   -- Create job_logs table
   CREATE TABLE job_logs (
       id SERIAL PRIMARY KEY,
       timestamp TIMESTAMP DEFAULT NOW(),
       status VARCHAR(20),
       market VARCHAR(10),
       signals_generated INTEGER,
       execution_time DECIMAL(5,2)
   );

   -- Create config_profiles table
   CREATE TABLE config_profiles (
       id SERIAL PRIMARY KEY,
       market VARCHAR(10),
       name VARCHAR(50),
       holding_period INTEGER,
       hurdle_rate DECIMAL(4,2),
       stop_loss DECIMAL(4,2),
       tickers JSONB,
       created_at TIMESTAMP DEFAULT NOW(),
       UNIQUE(market, name)
   );
   ```

5. **Enable Realtime** (optional):
   - Database → Replication → Enable for `signals` table
   - Useful for live dashboard updates

6. **Save Environment Variables**:
   ```bash
   # Save these for Koyeb deployment
   SUPABASE_URL=https://abcdefghijk.supabase.co
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   DATABASE_URL=postgresql://postgres:[PASSWORD]@db.abcdefghijk.supabase.co:5432/postgres
   ```

---

#### **Step 3: Koyeb Deployment** (15 minutes)

1. **Create Koyeb Account**:
   - Go to: https://app.koyeb.com/signup
   - Sign up with GitHub (free)

2. **Connect GitHub Repository**:
   ```
   Services → Create Service → GitHub
   
   Repository: <your-username>/share-investment-strategy-model
   Branch: bots  # Or main/master
   ```

3. **Configure Build Settings**:
   ```
   Builder: Dockerfile
   Dockerfile: ./Dockerfile
   Build Context: .
   
   Advanced:
   ✅ Enable automatic deploys on git push
   ```

4. **Configure Instance Settings**:
   ```
   Instance Type: eSmall (0.5 vCPU, 1GB RAM)
   Region: Singapore (sgp)
   Scaling: 1 instance (min=1, max=1)
   
   Auto-stop: ✅ Enabled
   ├─ Idle Timeout: 5 minutes
   └─ Light Sleep: ✅ Enabled (200ms wake)
   ```

5. **Configure Environment Variables**:
   ```
   Environment Variables → Add Secret:
   
   DATABASE_URL=@database_url  # Create secret first
   SUPABASE_URL=@supabase_url
   SUPABASE_KEY=@supabase_key
   TELEGRAM_BOT_TOKEN=@telegram_token
   FLASK_ENV=production
   SECRET_KEY=<generate-random-32-char-string>
   ```

   **Create Secrets First**:
   ```bash
   # Via Koyeb CLI
   koyeb secrets create database_url --value "postgresql://..."
   koyeb secrets create supabase_url --value "https://..."
   koyeb secrets create supabase_key --value "eyJ..."
   koyeb secrets create telegram_token --value "123456:ABC..."
   ```

6. **Configure Custom Domain**:
   ```
   Networking → Domains → Add Custom Domain:
   
   Domain: money.twoudia.com
   
   ⚠️ Wait for DNS propagation (1-5 minutes)
   ✅ Koyeb auto-provisions Let's Encrypt SSL certificate
   ```

7. **Configure Health Check**:
   ```
   Health Checks:
   ├─ Path: /health
   ├─ Port: 5000
   ├─ Protocol: HTTP
   ├─ Initial Delay: 30s
   ├─ Interval: 30s
   └─ Timeout: 5s
   ```

8. **Deploy**:
   - Click "Deploy"
   - Wait 3-5 minutes for build + deployment
   - Check logs for errors

9. **Get Koyeb Domain**:
   ```
   After deployment, you'll get:
   https://trading-bot-abc123.koyeb.app
   
   Update Cloudflare CNAME:
   Name: money
   Target: trading-bot-abc123.koyeb.app  # Copy this exact domain
   ```

10. **Test Deployment**:
   ```bash
   # Health check
   curl https://money.twoudia.com/health
   
   # Expected response:
   {
     "status": "healthy",
     "database": "connected",
     "timestamp": "2026-02-05T00:00:00Z"
   }
   ```

---

#### **Step 4: Cloudflare R2 Backup Setup** (10 minutes)

1. **Create R2 Bucket**:
   ```
   Cloudflare Dashboard → R2 → Create Bucket:
   
   Bucket Name: trading-bot-backups
   Location: Automatic (global)
   ```

2. **Generate API Tokens**:
   ```
   R2 → Manage R2 API Tokens → Create API Token:
   
   Token Name: trading-bot-backup
   Permissions: Object Read & Write
   TTL: Never
   
   Save:
   - Access Key ID: <save-this>
   - Secret Access Key: <save-this>
   - Account ID: <save-this>
   ```

3. **Add to Koyeb Secrets**:
   ```bash
   koyeb secrets create r2_access_key --value "<access-key-id>"
   koyeb secrets create r2_secret_key --value "<secret-access-key>"
   koyeb secrets create r2_account_id --value "<account-id>"
   ```

4. **Update Application Code** (add backup function):
   ```python
   # bot/services/backup_service.py
   import boto3
   from datetime import datetime
   
   def backup_to_r2():
       r2 = boto3.client(
           's3',
           endpoint_url=f'https://{os.getenv("R2_ACCOUNT_ID")}.r2.cloudflarestorage.com',
           aws_access_key_id=os.getenv('R2_ACCESS_KEY'),
           aws_secret_access_key=os.getenv('R2_SECRET_KEY')
       )
       
       # Export database to SQL
       filename = f'backup-{datetime.now().strftime("%Y%m%d")}.sql.gz'
       # ... pg_dump logic ...
       
       # Upload to R2
       r2.upload_file(filename, 'trading-bot-backups', f'backups/{filename}')
   ```

5. **Schedule Daily Backup** (add to cron):
   ```python
   # Add to daily signal generation job
   @app.route('/cron/daily-signals')
   def daily_signals():
       # ... existing logic ...
       
       # Backup after signals generated
       backup_to_r2()
   ```

---

#### **Step 5: GitHub Actions Setup** (5 minutes)

1. **Add Secrets to GitHub**:
   ```
   Repository → Settings → Secrets and Variables → Actions:
   
   Add Repository Secrets:
   - KOYEB_API_TOKEN=<from-koyeb-dashboard>
   - TELEGRAM_CHAT_ID=<your-telegram-chat-id>
   - TELEGRAM_BOT_TOKEN=<same-as-koyeb>
   ```

2. **Verify Workflow File** (already exists):
   ```yaml
   # .github/workflows/daily-signals.yml
   name: Daily Trading Signals
   
   on:
     schedule:
       - cron: '0 22 * * 0-4'  # 08:00 AEST Mon-Fri
     workflow_dispatch:
   
   jobs:
     trigger-signals:
       runs-on: ubuntu-latest
       steps:
         - name: Trigger Koyeb Endpoint
           run: |
             curl -X POST https://money.twoudia.com/cron/daily-signals?market=ASX \
               -H "Authorization: Bearer ${{ secrets.KOYEB_API_TOKEN }}"
   ```

3. **Test Manual Trigger**:
   ```
   Actions → Daily Trading Signals → Run workflow
   ```

---

### ✅ **Final Architecture Summary**

**Deployment Stack** ($0.22/month):
```
┌─────────────────────────────────────────────────┐
│  Cloudflare DNS (FREE)                          │
│  ├─ money.twoudia.com → CNAME → koyeb.app     │
│  └─ SSL: Koyeb Let's Encrypt (auto-provisioned)│
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  Koyeb eSmall - Singapore ($0.22/month)         │
│  ├─ Flask App (Python)                          │
│  ├─ Auto-stop after 5min idle                   │
│  ├─ Light Sleep: 200ms wake                     │
│  └─ 30h/month active time                       │
└─────────────────────────────────────────────────┘
       ↓                           ↓
┌──────────────────┐    ┌──────────────────────┐
│ Supabase Free    │    │ Cloudflare R2 (FREE) │
│ Singapore (FREE) │    │ Backups (10GB)       │
│ ├─ PostgreSQL    │    │ ├─ Daily SQL dumps   │
│ ├─ Always-on     │    │ └─ 30-day retention  │
│ └─ 500MB storage │    └──────────────────────┘
└──────────────────┘
```

**Cost Breakdown**:
- Compute: $0.22/month (Koyeb)
- Database: $0.00 (Supabase Free)
- DNS/CDN: $0.00 (Cloudflare)
- Storage: $0.00 (R2 Free Tier)
- Secrets: $0.00 (Koyeb built-in)
- Monitoring: $0.00 (Koyeb Metrics)
- **Total: $0.22/month** ($2.64/year)

**Next Steps**:
1. ✅ Verify all endpoints working: `https://money.twoudia.com/health`
2. ✅ Test manual signal generation: `/cron/daily-signals?market=ASX`
3. ✅ Verify GitHub Actions trigger
4. ✅ Check Telegram notifications
5. ✅ Monitor first week of automated trading signals

#### 5. Monitoring: Koyeb Metrics + Better Stack (FREE)

**What Are Koyeb Metrics?**

Koyeb Metrics is a **built-in monitoring dashboard** included with every service at no cost. It provides real-time visibility into your application's performance and resource usage.

```yaml
Built-In Koyeb Monitoring (FREE):
  Service: Koyeb Metrics Dashboard
  Cost: $0.00/month (included in all plans)
  
  Metrics Available:
    - ✅ CPU usage (%) - Real-time graphs
    - ✅ Memory usage (MB) - RAM consumption
    - ✅ Network (requests/sec) - Inbound traffic
    - ✅ HTTP status codes (2xx/4xx/5xx) - Error rates
    - ✅ Response times (ms) - Latency percentiles
    - ✅ Instance state (running/stopped) - Health status
  
  Logs:
    - ✅ Realtime log streaming (tail -f style)
    - ✅ Search and filter by severity
    - ⚠️ Retention: 1 day only (last 24 hours)
    - ✅ Export via Log Exporter feature
  
  Access:
    - Koyeb Dashboard → Services → Your Service → Metrics tab
    - Koyeb Dashboard → Services → Your Service → Logs tab
```

**What is Better Stack?**

Better Stack (formerly Logtail) is an **external log management service** that extends your log retention from 1 day to 30+ days. It's optional but useful for historical debugging.

```yaml
External Better Stack (OPTIONAL):
  Service: Better Stack Logs (formerly Logtail)
  Cost: $0.00/month (1GB logs/month free tier)
  Website: https://betterstack.com/logs
  
  Features:
    - ✅ 30-day log retention (vs Koyeb 1 day)
    - ✅ Advanced search (regex, SQL-like queries)
    - ✅ Log alerting (Slack, email, webhook)
    - ✅ Custom dashboards
    - ✅ Team collaboration
  
  Setup:
    1. Create Better Stack account (free)
    2. Koyeb Dashboard → Log Exporter → Add Better Stack destination
    3. Logs automatically streamed from Koyeb to Better Stack
```

**How Log Export Works**:

```mermaid
Koyeb Service → Logs Generated → Koyeb Dashboard (1 day) 
                                    ↓ (Log Exporter)
                              Better Stack (30 days)
```

**Example: Setting Up Log Export**:

```bash
# 1. Get Better Stack source token
# Visit: https://logs.betterstack.com/team/<your-team>/sources
# Create source → Copy token

# 2. Configure Koyeb Log Exporter
koyeb log-exporter create \
  --service trading-bot \
  --type better-stack \
  --token "YOUR_BETTER_STACK_TOKEN"

# 3. Logs now stream to Better Stack automatically
```

**🔄 Alternative Monitoring Options**:

| Service | Free Tier | Paid Plan | Best For |
|---------|-----------|-----------|----------|
| **Koyeb Metrics** ✅ | Unlimited | $0/month | CPU/RAM/Network monitoring (built-in) |
| **Better Stack** | 1GB logs/month | $19/month (10GB) | Extended log retention (30 days vs 1 day) |
| Datadog | 14-day trial | $15/host/month | Enterprise monitoring (overkill for trading bot) |
| New Relic | 100GB/month | $99/month | APM + infrastructure (too expensive) |
| Grafana Cloud | 10K series, 50GB logs | $49/month | Custom dashboards (more than you need) |
| Sentry | 5K errors/month | $26/month | Error tracking only (narrow focus) |
| Uptime Robot | 50 monitors | $7/month | Uptime monitoring (useful addition) |
| Honeycomb | 20M events/month | $0/month | Observability (if you need traces) |

**🎯 Monitoring Strategy Recommendation**:

**Option A: Koyeb Only** ($0/month) - **Recommended**
```yaml
Use: Koyeb built-in metrics + 1-day logs
Cost: $0.00/month
Why: Trading bot is simple, 1-day logs sufficient for debugging
When to check:
  - Daily: Quick glance at dashboard (2 minutes)
  - On errors: Check logs for last 24 hours
  - Weekly: Review CPU/RAM trends
```

**Option B: Koyeb + Better Stack** ($0/month) - If you want history
```yaml
Use: Koyeb metrics + Better Stack for 30-day log retention
Cost: $0.00/month (within 1GB free tier)
Why: Useful if you want to compare trends week-over-week
Log volume estimate:
  - Daily cron job: ~5MB logs/day = 150MB/month
  - Admin panel access: ~2MB/session × 5 = 10MB/month
  - Total: ~160MB/month << 1GB free tier ✅
```

**Option C: Full Observability Stack** ($19-26/month) - Overkill
```yaml
Use: Better Stack ($19) + Sentry ($26) + Uptime Robot ($7)
Cost: $52/month = 236x more expensive than Koyeb alone
Why: Only if trading bot becomes production SaaS with paying users
```

**🎯 Verdict: Use Koyeb Built-In Only** because:
- ✅ **1-day retention sufficient** for daily cron job debugging
- ✅ **Free unlimited metrics** (CPU, RAM, requests)
- ✅ **Real-time log streaming** when you need it
- ✅ **Zero configuration** (already built-in)
- 💡 **Add Better Stack later** if you find yourself needing historical logs

**When to upgrade**:
- **Better Stack** ($0): If you need to debug issues that happened 2+ days ago
- **Uptime Robot** ($0 for 50 monitors): If you want 5-min interval uptime checks
- **Sentry** ($0 for 5K errors/month): If you deploy to production and need error tracking

**Log Export to Better Stack** (if 1 day isn't enough):
```yaml
# Koyeb Log Exporter (built-in feature)
Destination: Better Stack (formerly Logtail)
Retention: 30 days (free tier)
Cost: $0.00/month (within 1GB limit)
```

#### 6. Domain & CDN: Cloudflare (FREE)
```yaml
Service: Cloudflare DNS + CDN
Cost: $0.00/month (Free plan)
Features:
  - DNS management (unlimited domains)
  - DDoS protection
  - SSL/TLS (automatic)
  - CDN caching (global)
  - Page Rules (3 free)
```

**Setup**:
1. Register domain at Cloudflare Registrar ($9/year for .com)
2. Point A record to Koyeb app: `bot.yourdomain.com`
3. Cloudflare auto-provisions SSL certificate
4. Optional: Cache static assets via CDN

---

### 🆚 Alternative Architectures

#### Option 2: Koyeb + AWS Services (Hybrid)

| Component | Service | Cost/Month | Why? |
|-----------|---------|------------|------|
| **Compute** | Koyeb eSmall | $0.22 | Cheapest compute |
| **Database** | AWS RDS Postgres | $15.00 | Always-on, 20GB storage |
| **Secrets** | AWS Secrets Manager | $0.40 | 1 secret ($0.40/secret/month) |
| **Storage** | AWS S3 | $0.50 | 20GB standard |
| **Monitoring** | CloudWatch | $0.00 | Free tier (5GB logs) |
| **Total** | | **$16.12/month** | AWS-heavy |

**When to Choose**:
- ❌ **Don't** - Way more expensive ($16.12 vs $0.22)
- ✅ **Maybe** - If you need 99.99% database uptime SLA
- ✅ **Maybe** - If scaling to 100GB+ database in future

#### Option 3: Full Cloudflare Stack (Workers + D1)

| Component | Service | Cost/Month | Why? |
|-----------|---------|------------|------|
| **Compute** | Cloudflare Workers | $0.00 | 100K requests/day free |
| **Database** | Cloudflare D1 | $0.00 | 5GB storage, 5M reads free |
| **Secrets** | Workers Secrets | $0.00 | Built-in |
| **Storage** | Cloudflare R2 | $0.00 | 10GB free |
| **Monitoring** | Workers Analytics | $0.00 | Built-in |
| **Total** | | **$0.00/month** | Completely free |

**Trade-Offs**:
- ✅ **Pros**: Completely free, global edge network, no cold starts
- ❌ **Cons**: 
  - Workers = JavaScript/TypeScript only (need to rewrite Flask app)
  - D1 = SQLite (not Postgres, different syntax/features)
  - 10ms CPU time limit per request (tight for ML models)
  - 2-3 weeks refactoring time (similar to Lambda)

**Verdict**: Only if starting from scratch with JS/TS

#### Option 4: All-In-One Railway ($5/month)

| Component | Service | Cost/Month | Why? |
|-----------|---------|------------|------|
| **Compute** | Railway | $5.00 | Included in minimum |
| **Database** | Railway Postgres | $0.00 | Included |
| **Secrets** | Railway Variables | $0.00 | Built-in |
| **Storage** | Railway Volumes | $0.00 | Up to 50GB included |
| **Monitoring** | Railway Logs | $0.00 | Built-in |
| **Total** | | **$5.00/month** | All-in-one |

**When to Choose**:
- ✅ **Simplicity**: Single vendor, zero config
- ✅ **Developer Experience**: Best DX (GitHub auto-deploy, preview envs)
- ❌ **Cost**: 22x more expensive ($5.00 vs $0.22/month)
- 💡 **Best for**: Production apps with >100h/month usage

---

### 📊 Total Cost of Ownership (3 Years)

| Architecture | Year 1 | Year 2 | Year 3 | Total | Notes |
|--------------|--------|--------|--------|-------|-------|
| **Koyeb + Cloudflare** | $2.64 | $2.64 | $2.64 | **$7.92** | Cheapest ✅ |
| **Fly.io + Cloudflare** | $7.32 | $7.32 | $7.32 | **$21.96** | Sydney region |
| **Koyeb + AWS Services** | $193.44 | $193.44 | $193.44 | **$580.32** | RDS expensive |
| **Railway All-In-One** | $60.00 | $60.00 | $60.00 | **$180.00** | Best DX |
| **Cloudflare Workers** | $0.00 | $0.00 | $0.00 | **$0.00** | Requires rewrite |

---

### 🎯 Final Architecture Recommendation

**Choose: Koyeb + Cloudflare Stack** ($0.22/month)

**Complete Setup**:
```yaml
# Infrastructure
Compute: Koyeb eSmall (Singapore)
Database: Koyeb Postgres (Free tier, 5h/month)
Storage: Cloudflare R2 (10GB free)
Secrets: Koyeb Secrets (built-in)
CDN: Cloudflare (free plan)
Monitoring: Koyeb Metrics + Better Stack (1GB logs free)
Notifications: Telegram Bot API (free)

# Monthly Costs
Koyeb Compute: $0.22
Everything Else: $0.00
─────────────────────
Total: $0.22/month = $2.64/year

# 3-Year TCO: $7.92 (saves $172.08 vs Railway, $14.04 vs Fly.io)
```

**Why This Is Solid**:
1. **Battle-Tested**: Koyeb runs on AWS bare metal, Cloudflare powers 20% of internet
2. **Zero Lock-In**: Standard Postgres, S3-compatible R2, can migrate anytime
3. **Complete Coverage**: Compute, DB, storage, secrets, monitoring - nothing missing
4. **Room to Grow**: Can scale to 100GB R2 storage for $1.50/month if needed
5. **Free Database**: 5h/month >> 1.85h actual usage (63% buffer)

**What You're NOT Getting** (acceptable trade-offs):
- ❌ Sydney region (Singapore +100ms, fine for daily cron)
- ❌ Long-term logs (1 day default, can export to Better Stack for 30 days free)
- ❌ 24/7 support (email only, community forum)

**Migration Path** (if needed later):
- Compute: Koyeb → Fly.io (10 min, +$0.39/month for Sydney)
- Database: Export SQL → Import to RDS/Neon (if >1GB needed)
- Storage: R2 stays (S3-compatible, works with any compute)

---

## Cost Optimization Tips

### Fly.io Optimization Strategies

1. **Auto-Stop Configuration**
```toml
# fly.toml
[http_service]
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0  # Stop when idle
```

2. **Right-Size Memory**
- Current: 1GB RAM ($6.35/month baseline)
- Consider: 512MB RAM ($3.18/month baseline) if sufficient
- **Savings**: $0.13/month for 30 hours usage

3. **Optimize Cron Schedule**
- Current: Daily at 9 AM (30 hours/month)
- Alternative: Every other day (15 hours/month)
- **Savings**: $0.30/month (50% reduction)

4. **Volume Optimization**
- Current: 2GB persistent volume ($0.30/month)
- Alternative: 1GB volume ($0.15/month) if DB size < 1GB
- **Savings**: $0.15/month

### Railway Optimization (If Choosing Railway)

1. **Shared Workspaces**
- Run multiple projects in one workspace
- Split $5 minimum cost across projects

2. **Use Included Credits**
- $5/month = $5 usage credits
- Maximize usage within credits (up to ~200 hours with 1GB RAM)

3. **Hibernate Unused Services**
- Stop services when not needed (e.g., testing/staging)

---

## Appendix: Pricing Sources

### Official Documentation Links
- **Fly.io**: https://fly.io/docs/about/pricing/
- **Koyeb**: https://www.koyeb.com/pricing
- **Railway**: https://railway.com/pricing
- **Render**: https://render.com/pricing
- **AWS Lambda**: https://aws.amazon.com/lambda/pricing/

### Pricing Verification Date
- **Last Checked**: February 5, 2026
- **Currency**: USD
- **Region**: Asia Pacific (Sydney/Singapore)

### Calculation Assumptions
1. **Month Definition**: 730 hours (365 days / 12 months × 24 hours)
2. **Active Usage**: 30 hours/month (1 hour daily for ASX market)
3. **Memory**: 1GB RAM, Shared CPU (1 vCPU)
4. **Storage**: 2GB persistent volume for database files
5. **Network**: Minimal egress (< 100MB/month) - covered by free quotas
6. **Database**: External Supabase PostgreSQL (not included in platform costs)

---

*This analysis was prepared for the ASX AI Trading Bot project using official pricing documentation from each cloud provider as of February 2026.*
