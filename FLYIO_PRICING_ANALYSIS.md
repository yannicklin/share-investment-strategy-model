# 💰 Fly.io Pricing Analysis for ASX Bot Trading System

**Generated**: February 5, 2026  
**Source**: [Fly.io Official Pricing](https://fly.io/docs/about/pricing/)  
**Configuration**: shared-cpu-1x with 1GB RAM, Sydney region

---

## Official Fly.io Pricing (February 2026)

### Compute - Started Machines

From Fly.io's pricing table for **shared-cpu-1x**:

| Configuration | vCPU | RAM | Per Second | Per Hour | Per Month (24/7) |
|--------------|------|-----|-----------|----------|------------------|
| shared-cpu-1x | 1 shared | 256MB | $0.00000075 | $0.0027 | $1.94 |
| shared-cpu-1x | 1 shared | 512MB | $0.00000123 | $0.0044 | $3.19 |
| **shared-cpu-1x** | **1 shared** | **1GB** | **$0.00000220** | **$0.0079** | **$5.70** |
| shared-cpu-1x | 1 shared | 2GB | $0.00000413 | $0.0149 | $10.70 |

**Our Configuration**: shared-cpu-1x with 1GB RAM

### Compute - Stopped Machines

> "For stopped Machines we charge only for the root file system (rootfs) needed for each Machine."

**Rate**: $0.15/GB per month

Our Docker image rootfs: ~1GB  
**Cost when stopped**: $0.15/month

---

## Auto-Stop/Start Optimization

Our `fly.toml` configuration leverages Fly.io's auto-stop feature:

```toml
[http_service]
  auto_stop_machines = true   # Stop after idle timeout
  auto_start_machines = true  # Wake on HTTP request
  min_machines_running = 0    # No machines running when idle (FREE!)
  max_machines_running = 1    # Only 1 instance max
```

### Cost Breakdown

**Daily Schedule**:
- **08:00 AEST**: GitHub Actions triggers `/cron/daily-signals` → Machine starts
- **08:00-09:00**: Signal generation runs (~120 seconds = 2 minutes active)
- **09:00+**: Machine auto-stops after idle timeout

**Monthly Active Time** (730 hours/month standard):
- Active: 1 hour/day × 30 days = 30 hours/month
- Stopped: 23 hours/day × 30 days = 700 hours/month

**Cost Calculation** (from Fly.io calculator for 1GB RAM, shared CPU):

24/7 baseline (730 hours):
- Compute: $0.88/month
- Memory (1GB): $6.35/month
- Volume (2GB): $0.30/month
- Total if running 24/7: $7.53/month (excluding bandwidth)

Our usage (30 hours/month):
```
Compute:  $0.88 × (30/730) = $0.036/month
Memory:   $6.35 × (30/730) = $0.261/month
Stopped:  2GB rootfs × $0.15 = $0.300/month (when not running)
                              ─────────────
TOTAL COMPUTE:                  $0.597/month ≈ $0.60/month
```

---

## Database Cost (Supabase PostgreSQL)

**Provider**: Supabase (managed PostgreSQL)  
**Plan**: Free tier

### Free Tier Includes:
- 500MB database storage
- 2 concurrent connections
- 2GB monthly data transfer
- SSL encryption

**Our Usage**:
- Database size: ~50MB (signals + logs for 1 year)
- Connections: 1 concurrent (Flask app)
- Well within free limits

**Cost**: $0/month

---

## Storage Cost (Tigris Object Storage)

**Provider**: Tigris (Fly.io integrated S3-compatible storage)  
**Plan**: Free tier

### Free Tier Includes:
- First 5GB storage: FREE
- No egress charges (data transfer to Tigris is free)

**Our Usage**:
- Weekly backups: ~10MB/month
- Well within free limits

**Cost**: $0/month

---

## Network Cost

### Inbound Data Transfer
**All inbound data is FREE** (unlimited)

### Outbound Data Transfer

From Fly.io pricing for **Sydney (syd) region** (Asia Pacific):

| Destination | Egress to Internet | Private Network (between regions) |
|------------|-------------------|-----------------------------------|
| Asia Pacific | **$0.04/GB** | $0.015/GB |

**Our Usage**:
- Telegram Bot API calls: ~30 requests/month × 1KB = 30KB
- HTTP responses: ~30 responses × 1KB = 30KB
- yfinance data downloads: 10 stocks × 2 years × ~50KB = 1MB
- Total: ~2MB/month = 0.002GB

**Cost Calculation**:
```
0.002 GB × $0.04/GB = $0.00008/month ≈ $0.00/month
```

**Note**: Fly.io calculator estimates ~$4/month for bandwidth, but this seems to be for typical web apps with significant traffic. Our minimal API usage should be well under $1/month.

---

## Total Monthly Cost Summary
** | 30 hours × $0.88/730hr | $0.036 |
| **Memory (1GB)** | 30 hours × $6.35/730hr | $0.261 |
| **Stopped rootfs** | 2GB × $0.15/GB | $0.300 |
| **Database** | Supabase free tier | $0.000 |
| **Storage** | Tigris free tier | $0.000 |
| **Network** | ~2MB egress | $0.000 |
| **TOTAL** | | **$0.597** |

**Rounded**: **~$0.60/month** or **~$7.20
| **TOTAL** | | **$0.387** |

**Rounded**: **~$0.39/month** or **~$4.68/year**

---

## Comparison: Without Auto-Stop
 for 730 hours/month):

```
Compute:        $0.88/month
Memory (1GB):   $6.35/month
Volume (2GB):   $0.30/month
                           ─────────────
TOTAL:                       $7.53/month
```

**Savings with auto-stop**: $6.93/month (92
**Savings with auto-stop**: $5.30/month (93% reduction!)

---

## Scaling Scenarios

### Scenario 1: Add USA Mark60 hours/month)
```
Compute:  $0.88 × (60/730) = $0.072/month
Memory:   $6.35 × (60/730) = $0.522/month
Stopped:  $0.300/month
TOTAL: $0.894/month ≈ $0.90/month
```

### Scenario 2: Add USA + TWN Markets
**Impact**: 3× active time (90 hours/month)
```
Compute:  $0.88 × (90/730) = $0.108/month
Memory:   $6.35 × (90/730) = $0.783/month
Stopped:  $0.300/month
TOTAL: $1.191/month ≈ $1.20/month
```

### Scenario 3: Upgrade to 2GB RAM (more stocks)
**24/7 rate**: Compute $0.88 + Memory (2GB) $11.65 = $12.53/month
```
Compute:  $0.88 × (30/730) = $0.036/month
Memory:   $11.65 × (30/730) = $0.479/month
Stopped:  2GB × $0.15 = $0.300/month
TOTAL: $0.815/month ≈ $0.82× $0.15 = $0.300/month
TOTAL: $0.747/month
```

---

## Free Trial Credit

Fly.io offers **free trial credits** for new users:
- Check your dashboard for available credits
- Typically $5-$50 depending on promotion
- Covers first 1-12 months at our usage level

**First month may be $0** if you have trial credits.

---

## Cost Control Recommendations

### 1. Monitor Usage
```bash
# Check current month spending
fly dashboard --org personal

# View cost breakdown
fly billing show
```

### 2. Set Up Billing Alerts
- Go to: [Fly.io Dashboard → Billing](https://fly.io/dashboard/personal/billing)
- Set alert threshold: $1.00/month
- Get email when approaching limit

### 3. Optimize Machine Size
If memory usage stays under 512MB:
``24/7 rate**: Compute $0.88 + Memory (512MB) $3.19 = $4.07/month
**Our usage**: ($0.88 + $3.19) × (30/730) + $0.15 stopped = **$0.32
[[vm]]
  memory = "512mb"  # Reduce from 1GB
```
**New cost**: $0.0044/hour × 30 hours = $0.132 + $0.075 stopped = **$0.21/month**

### 4. Increase Idle Timeout
Current: Default (~5 minutes idle before stop)  
Consider: 1 minute idle to stop faster after signal generation

```toml
[http_service]
  min_machines_running = 0
  # Stops ~1 minute after last request
```

---

## Cost Guarantees

### What's Free Forever:
✅ Supabase database (under 500MB)  
✅ Tigris storage (under 5GB)  
✅ Inbound network traffic (unlimited)  
✅ GitHub Actions runtime (2000 minutes/month free)  
✅ Telegram Bot API (unlimited messages)

### What Costs Money:
💵 Fly.io compute (running + stopped rootfs)  
💵 Outbound network traffic (>1GB/month)

**Worst-case scenario** (compute-only):  
$0.60/month = **$7.20/year**

---

## Payment Methods

Fly.io accepts:
- Credit cards (Visa, Mastercard, Amex)
- PayPal (in some regions)

**Note**: Credit card required even for free tier usage.

---

## Invoice Example

```
Fly.io Monthly Invoice - February 2026
Organization: personal

Resources:
  Machines (shared-cpu-1x, 1GB RAM, 730hr month)
    - Compute: 30.00 hours @ $0.88/730hr         $0.04
    - Memory (1GB): 30.00 hours @ $6.35/730hr    $0.26
    - Stopped rootfs: 2.00 GB @ $0.15/GB         $0.30
  
  Data Transfer (Sydney region)
    - Egress to Internet: 0.002 GB @ $0.04/GB    $0.00
  
                                        SUBTOTAL  $0.60
                                             TAX  $0.00
                                       ─────────────────
                                           TOTAL  $0.60

Credits Applied: $0.00
Amount Due: $0.60
```

---
60
## Frequently Asked Questions

### Q: Can I stay under $1/month?
**A**: Yes! With auto-stop enabled, you'll stay around $0.39/month.

### Q: What if I forget to stop the machine manually?
**A**: Auto-stop handles this automatically. You can't "forget" - the machine stops after idle.

### Q: Will costs increase if stock data gets bigger?
**A**: No. We fetch fixed 2-year history (same size each time). Database grows slowly (~1MB/month).

### Q: What if GitHub Actions fail to trigger?
**A**: No cost impact. Machine only starts when HTTP request received. Failed cron = no charges.

### Q: Can I run this completely60ree?
**A**: Almost. Compute costs $0.39/month. Everything else (database, storage, networking) is free.

---

## Official Documentation Links

- [Fly.io Pricing](https://fly.io/docs/about/pricing/)
- [Machine Billing](https://fly.io/docs/about/billing/#machine-billing)
- [Cost Management](https://fly.io/docs/about/cost-management/)
- [Free Trial](https://fly.io/docs/about/free-trial/)
- [Supabase Pricing](https://supabase.com/pricing)
- [Tigris Pricing](https://www.tigrisdata.com/docs/pricing/)

---

**Last Updated**: February 5, 2026  
**Pricing Verified**: [Fly.io official website](https://fly.io/docs/about/pricing/)  
**Next Review**: Check pricing quarterly for changes
