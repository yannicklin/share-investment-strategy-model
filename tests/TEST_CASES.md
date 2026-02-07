# Test Cases: AI Trading Bot (Multi-Market)

This document outlines the standard test suite for the `bots` branch. These tests ensure the system remains stable, secure, and market-isolated before deployment to production.

---

## 1. End-to-End System Simulation (Feature Tour)
**File**: `tests/test_feature_tour.py`  
**Requirement**: Verify the complete user journey for a new market setup.

| Step | Action | Expected Outcome |
|:---|:---|:---|
| 1.1 | **Admin Auth Request** | System generates a 6-digit code; code is NOT sent if phone is not whitelisted. |
| 1.2 | **Admin Auth Verify** | Entering correct code creates a secure session cookie; redirects to Dashboard. |
| 1.3 | **Profile Creation** | Creating a profile with specific tickers (e.g., `BHP.AX`) persists to the correct market (`ASX`). |
| 1.4 | **Profile Modification**| Updating hurdle rates or stock lists reflects immediately in the database. |
| 1.5 | **Manual Signal Trigger**| Triggering a manual run generates a signal based on current profile parameters. |
| 1.6 | **Audit Logging** | Every action (login, signal gen, profile edit) is recorded in `job_logs`. |

---

## 2. Market Isolation & Security
**File**: `tests/test_feature_tour.py` (Market Context)  
**Requirement**: Ensure data integrity across global markets.

| ID | Case | Expected Outcome |
|:---|:---|:---|
| 2.1 | **Data Leakage** | `Signal.for_market('ASX')` must NEVER return results from 'USA' or 'TWN'. |
| 2.2 | **Defaulting** | New profiles created in the `bots` branch must default to `market='ASX'` unless specified. |
| 2.3 | **Session Security** | Accessing `/admin/` routes without an active session redirects to the Auth Modal. |

---

## 3. Signal Idempotency & Reliability
**File**: `tests/bot/test_idempotent_signals.py`  
**Requirement**: Ensure the bot is reliable across redundant trigger windows (e.g., 08:00 and 10:00 AEST).

| ID | Case | Expected Outcome |
|:---|:---|:---|
| 3.1 | **First Trigger** | System calculates signals and marks `sent_at` timestamp. |
| 3.2 | **Second Trigger** | System detects existing signals for `today`; skips calculation and notification. |
| 3.3 | **Partial Failure** | If notification fails in trigger 1, trigger 2 must attempt re-sending. |
| 3.4 | **DB Constraint** | `UniqueConstraint` on `(market, date, ticker)` prevents accidental duplicate rows. |

---

## 4. Risk & Hurdle Logic
**File**: `tests/test_feature_tour.py` (Mocked Engine)  
**Requirement**: Validate that buy signals respect the profit threshold.

| ID | Case | Expected Outcome |
|:---|:---|:---|
| 4.1 | **Hurdle Filtering** | If Predicted Return < Hurdle Rate (e.g., 10%), signal must be `HOLD` or `None`. |
| 4.2 | **Resource Check** | `BUY` signals should include a `notes` warning if portfolio cash is insufficient. |

---

## 🔧 Running Tests
All test cases can be executed locally using the following command:

```bash
# Run the complete integrated suite
export PYTHONPATH=$PYTHONPATH:.
.venv/bin/pytest tests/ -v
```
