# Admin Panel Authentication System - Implementation Plan

**Feature**: Phone-Based Authentication for Admin Dashboard  
**Version**: 1.0  
**Date**: February 6, 2026  
**Author**: Yannick

---

## Work Package Overview

| WP ID | Title | Priority | Effort | Dependencies |
|-------|-------|----------|--------|--------------|
| WP-1.1 | Database Models & Schema | P1 | 2-3h | None |
| WP-1.2 | Phone Verification Service | P1 | 3-4h | WP-1.1 |
| WP-1.3 | Session Management Service | P1 | 2-3h | WP-1.1 |
| WP-1.4 | Authentication Middleware | P1 | 2h | WP-1.2, WP-1.3 |
| WP-1.5 | Frontend Authentication UI | P1 | 4-5h | WP-1.2, WP-1.3 |
| WP-1.6 | Admin Routes Protection | P1 | 1-2h | WP-1.4 |
| WP-2.1 | Rate Limiting Implementation | P2 | 2-3h | WP-1.2 |
| WP-2.2 | Audit Logging System | P2 | 2h | WP-1.2, WP-1.3 |
| WP-3.1 | SMS Fallback Integration | P3 | 3-4h | WP-1.2 |
| WP-3.2 | Admin Whitelist Management UI | P3 | 2-3h | WP-1.1, WP-1.5 |

**Total Estimated Effort**: 23-32 hours

---

## WP-1.1: Database Models & Schema

**Priority**: P1  
**Effort**: 2-3 hours  
**Dependencies**: None

**Addresses Spec Requirements**:
- FR-001: Phone Whitelist Management
- TR-001: Database Schema
- TR-002: Security Standards

**Implementation Tasks**:
1. Create `AdminWhitelist` model
   - `id`, `phone_number_hash`, `notification_preference`, `created_at`, `created_by`
2. Create `VerificationCode` model
   - `id`, `phone_number_hash`, `code_hash`, `expires_at`, `used_at`, `attempts`, `ip_address`
3. Create `AdminSession` model
   - `id`, `session_token`, `phone_number_hash`, `ip_address`, `user_agent`, `created_at`, `expires_at`
4. Create `AuthLog` model
   - `id`, `event_type`, `phone_number_hash`, `ip_address`, `success`, `error_message`, `created_at`
5. Add database indexes for performance:
   - Index on `phone_number_hash` for all tables
   - Index on `session_token` for AdminSession
   - Index on `created_at` for AuthLog (for log cleanup)
6. Implement helper methods:
   - `hash_phone_number()` - bcrypt hashing
   - `verify_phone_hash()` - verification

**Acceptance Criteria**:
- [ ] All models inherit from `MarketIsolatedModel` or `db.Model`
- [ ] Phone numbers are hashed with bcrypt (never stored plaintext)
- [ ] Verification codes are hashed with SHA-256
- [ ] Session tokens are 32-byte random hex strings
- [ ] Database migration runs successfully
- [ ] Models have proper `__repr__` methods

**Files to Create**:
- `app/bot/shared/models.py` (append to existing)

**Files to Modify**:
- `app/bot/shared/models.py` (add new models)

---

## WP-1.2: Phone Verification Service

**Priority**: P1  
**Effort**: 3-4 hours  
**Dependencies**: WP-1.1

**Addresses Spec Requirements**:
- FR-002: Verification Code Generation
- FR-003: Verification Code Delivery
- TR-004: Notification Integration

**Implementation Tasks**:
1. Create `VerificationService` class in `app/bot/services/verification_service.py`
2. Implement `generate_verification_code()`:
   - Generate 6-digit cryptographically secure code
   - Hash and store in database with expiration
   - Invalidate any previous codes for same phone
3. Implement `send_verification_code()`:
   - Check if phone is whitelisted
   - Check rate limits (placeholder, full implementation in WP-2.1)
   - Send via Telegram Bot API
   - Log delivery attempt
4. Implement `verify_code()`:
   - Check code hash matches
   - Check not expired
   - Check not already used
   - Increment attempts counter
   - Mark as used if valid
5. Add utility functions:
   - `is_phone_whitelisted(phone)` - Check whitelist
   - `get_notification_channel(phone)` - Telegram/SMS preference
6. Integrate with existing `notification_service.py`

**Acceptance Criteria**:
- [ ] Verification codes are 6 digits (000000-999999)
- [ ] Codes expire after configurable time (ENV: `ADMIN_CODE_EXPIRY_MINUTES`)
- [ ] Only one active code per phone number at a time
- [ ] Codes are invalidated after use
- [ ] Telegram delivery works for whitelisted numbers
- [ ] Clear error messages for all failure scenarios
- [ ] Unit tests for code generation and verification

**Files to Create**:
- `app/bot/services/verification_service.py`

**Files to Modify**:
- `app/bot/services/notification_service.py` (add verification code template)

---

## WP-1.3: Session Management Service

**Priority**: P1  
**Effort**: 2-3 hours  
**Dependencies**: WP-1.1

**Addresses Spec Requirements**:
- FR-005: Session Management
- TR-002: Security Standards

**Implementation Tasks**:
1. Create `SessionService` class in `app/bot/services/session_service.py`
2. Implement `create_session()`:
   - Generate secure 32-byte random token
   - Store session in database
   - Set expiration time from ENV config
   - Return session token
3. Implement `validate_session()`:
   - Check token exists in database
   - Check not expired
   - Check IP address matches (optional - configurable)
   - Extend session expiry on activity (sliding window)
4. Implement `invalidate_session()`:
   - Delete session from database
   - Clear session cookie
5. Implement `cleanup_expired_sessions()`:
   - Background task to delete expired sessions
   - Run daily via cron or on-demand
6. Add Flask session integration:
   - Store session token in secure HTTP-only cookie
   - Configure cookie security (SameSite, Secure flag)

**Acceptance Criteria**:
- [ ] Session tokens are cryptographically secure (32 bytes)
- [ ] Sessions expire after configured time (ENV: `ADMIN_SESSION_EXPIRY_HOURS`)
- [ ] Session validation is fast (< 50ms)
- [ ] Sessions are properly cleaned up on expiry
- [ ] Cookies are HTTP-only and Secure in production
- [ ] Unit tests for session lifecycle

**Files to Create**:
- `app/bot/services/session_service.py`

---

## WP-1.4: Authentication Middleware

**Priority**: P1  
**Effort**: 2 hours  
**Dependencies**: WP-1.2, WP-1.3

**Addresses Spec Requirements**:
- FR-006: Authentication Middleware
- User Story 1: Admin Access

**Implementation Tasks**:
1. Create `auth_required` decorator in `app/bot/api/auth_middleware.py`
2. Implement middleware logic:
   - Check for session cookie
   - Validate session using SessionService
   - Allow access if valid
   - Redirect to auth modal if invalid
   - Preserve intended URL for post-login redirect
3. Create whitelist for public endpoints:
   - `/api/admin/auth/*` (authentication endpoints)
   - `/admin/health` (health check)
4. Handle AJAX requests:
   - Return 401 JSON response (not redirect)
   - Frontend handles modal display
5. Add request context:
   - Store authenticated phone hash in Flask `g`
   - Available for audit logging

**Acceptance Criteria**:
- [ ] All `/admin/*` routes require authentication by default
- [ ] Public endpoints are accessible without auth
- [ ] Invalid sessions redirect to login modal
- [ ] Post-login redirect to intended destination works
- [ ] AJAX requests receive proper JSON responses
- [ ] Middleware has minimal performance impact (< 10ms)

**Files to Create**:
- `app/bot/api/auth_middleware.py`

**Files to Modify**:
- `app/bot/api/admin_routes.py` (apply decorators)
- `app/bot/api/admin_ui_routes.py` (apply decorators)

---

## WP-1.5: Frontend Authentication UI

**Priority**: P1  
**Effort**: 4-5 hours  
**Dependencies**: WP-1.2, WP-1.3

**Addresses Spec Requirements**:
- User Story 1: Admin Access
- User Story 2: Session Management
- TR-005: Frontend Requirements

**Implementation Tasks**:
1. Create authentication modal template `app/bot/templates/auth_modal.html`:
   - Phone number input (with country code selector or manual entry)
   - "Send Verification Code" button
   - Verification code input (6 digits)
   - "Verify" button
   - Loading states
   - Error message display
   - Timer countdown (5 minutes)
2. Add modal to base template conditionally:
   - Show modal if not authenticated
   - Hide once authenticated
3. Implement JavaScript for modal interactions:
   - Form validation (phone format)
   - AJAX requests to API endpoints
   - Progress indicators
   - Countdown timer
   - Auto-submit on 6-digit entry
   - Error handling
4. Style with Tailwind CSS:
   - Responsive design (mobile-first)
   - Accessibility (ARIA labels)
   - Focus states
   - Loading spinners
5. Add logout button to admin navbar:
   - Clear session on click
   - Redirect to login modal

**Acceptance Criteria**:
- [ ] Modal is responsive on mobile (tested iOS/Android simulators)
- [ ] Form validation prevents invalid phone numbers
- [ ] Loading states provide clear feedback
- [ ] Countdown timer shows remaining time
- [ ] Error messages are user-friendly
- [ ] Keyboard navigation works (Tab, Enter)
- [ ] ARIA labels for screen readers
- [ ] Modal cannot be dismissed without authentication
- [ ] Logout button clears session and shows modal

**Files to Create**:
- `app/bot/templates/auth_modal.html`
- `app/bot/static/js/auth.js` (if using separate JS files)

**Files to Modify**:
- `app/bot/templates/base.html` (include modal)
- `app/bot/templates/dashboard.html` (add logout button to navbar)

---

## WP-1.6: Admin Routes Protection

**Priority**: P1  
**Effort**: 1-2 hours  
**Dependencies**: WP-1.4

**Addresses Spec Requirements**:
- FR-006: Authentication Middleware
- All admin routes must be protected

**Implementation Tasks**:
1. Apply `@auth_required` decorator to all admin routes:
   - `/admin/dashboard`
   - `/admin/signals`
   - `/admin/config_profiles`
   - `/admin/job_logs`
   - `/api/admin/*` (all API endpoints)
2. Create authentication API endpoints:
   - `POST /api/admin/auth/request-code`
   - `POST /api/admin/auth/verify-code`
   - `POST /api/admin/auth/logout`
   - `GET /api/admin/auth/status` (check if authenticated)
3. Update route handlers to use authenticated phone:
   - Access via `g.authenticated_phone_hash`
   - Use for audit logging
4. Test all protected routes:
   - Verify redirect to auth modal when not authenticated
   - Verify access granted when authenticated

**Acceptance Criteria**:
- [ ] All admin routes require authentication
- [ ] API endpoints return proper responses (401 for unauth, 200 for auth)
- [ ] Authentication endpoints work correctly
- [ ] Logout endpoint clears session
- [ ] No routes are accidentally left unprotected
- [ ] Integration tests pass for all scenarios

**Files to Modify**:
- `app/bot/api/admin_routes.py`
- `app/bot/api/admin_ui_routes.py`

**Files to Create**:
- `app/bot/api/auth_routes.py` (authentication endpoints)

---

## WP-2.1: Rate Limiting Implementation

**Priority**: P2  
**Effort**: 2-3 hours  
**Dependencies**: WP-1.2

**Addresses Spec Requirements**:
- FR-004: Rate Limiting
- TR-002: Security Standards

**Implementation Tasks**:
1. Create `RateLimiter` class in `app/bot/services/rate_limiter.py`
2. Implement in-memory storage (dict with TTL):
   - Key: `phone_hash` or `ip_address`
   - Value: list of timestamps
3. Implement rate limit checks:
   - `check_phone_limit(phone, max_requests, window_minutes)`
   - `check_ip_limit(ip, max_requests, window_minutes)`
4. Add progressive delays:
   - 1st failure: no delay
   - 2nd failure: 1 second
   - 3rd failure: 5 seconds
   - 4th+ failure: 30 seconds
5. Integrate into VerificationService:
   - Check before sending verification code
   - Return clear error messages with retry time
6. Add cleanup of old entries (avoid memory leak):
   - Background task or on-demand cleanup

**Acceptance Criteria**:
- [ ] Phone rate limit: max 3 requests per 15 minutes
- [ ] IP rate limit: max 10 requests per hour
- [ ] Progressive delays implemented correctly
- [ ] Clear error messages with retry times
- [ ] Memory usage stays reasonable (< 10MB)
- [ ] Rate limits configurable via ENV variables

**Files to Create**:
- `app/bot/services/rate_limiter.py`

**Files to Modify**:
- `app/bot/services/verification_service.py` (integrate rate limiter)

---

## WP-2.2: Audit Logging System

**Priority**: P2  
**Effort**: 2 hours  
**Dependencies**: WP-1.2, WP-1.3

**Addresses Spec Requirements**:
- FR-007: Audit Logging
- Security compliance

**Implementation Tasks**:
1. Implement `log_auth_event()` function in `app/bot/services/audit_logger.py`
2. Add logging to all authentication events:
   - Verification code request (success/failure)
   - Verification code verification (success/failure with attempts)
   - Session creation
   - Session validation failure
   - Logout
3. Mask phone numbers in logs:
   - Only show last 4 digits: `****5678`
   - Store full hash in database for correlation
4. Implement log rotation:
   - Keep last 90 days of logs
   - Archive older logs to CSV/backup
5. Add audit log viewer in admin panel (future):
   - Filter by date, phone, event type
   - Export to CSV

**Acceptance Criteria**:
- [ ] All authentication events are logged
- [ ] Logs include: timestamp, event type, phone (masked), IP, success/failure
- [ ] Phone numbers never appear in plaintext in logs
- [ ] Logs are queryable (indexed on created_at)
- [ ] Old logs are cleaned up automatically
- [ ] Log viewer UI (basic version)

**Files to Create**:
- `app/bot/services/audit_logger.py`
- `app/bot/templates/audit_logs.html` (viewer UI)

**Files to Modify**:
- `app/bot/services/verification_service.py` (add logging)
- `app/bot/services/session_service.py` (add logging)
- `app/bot/api/auth_routes.py` (add logging)

---

## WP-3.1: SMS Fallback Integration

**Priority**: P3  
**Effort**: 3-4 hours  
**Dependencies**: WP-1.2

**Addresses Spec Requirements**:
- FR-003: Verification Code Delivery (SMS fallback)
- Risk mitigation: Telegram API down

**Implementation Tasks**:
1. Add SMS provider support (Twilio or Telnyx):
   - Install SDK: `pip install twilio` or `telnyx`
   - Add ENV variables for API credentials
2. Implement SMS sending in `notification_service.py`:
   - `send_sms(phone, message)`
   - Template for verification code message
3. Update `VerificationService.send_verification_code()`:
   - Try Telegram first
   - If Telegram fails, try SMS
   - Log which channel succeeded
4. Add notification preference to AdminWhitelist:
   - `notification_preference`: 'telegram', 'sms', 'both'
   - Respect user preference
5. Handle SMS-specific formatting:
   - International phone format (E.164)
   - Message length limits
   - Sender ID configuration

**Acceptance Criteria**:
- [ ] SMS sent successfully when Telegram fails
- [ ] SMS delivery success rate > 99% (monitored)
- [ ] User can choose preferred notification channel
- [ ] SMS costs are logged for billing
- [ ] Fallback logic is automatic (no user action needed)

**Files to Modify**:
- `app/bot/services/notification_service.py` (add SMS support)
- `app/bot/services/verification_service.py` (add fallback logic)
- `requirements.txt` (add SMS SDK)

---

## WP-3.2: Admin Whitelist Management UI

**Priority**: P3  
**Effort**: 2-3 hours  
**Dependencies**: WP-1.1, WP-1.5

**Addresses Spec Requirements**:
- FR-001: Phone Whitelist Management
- Admin self-service

**Implementation Tasks**:
1. Create whitelist management page `/admin/whitelist`:
   - List all whitelisted phone numbers (masked)
   - Add new phone number form
   - Remove phone number button (with confirmation)
   - Edit notification preference
2. Create API endpoints:
   - `GET /api/admin/whitelist` - List all
   - `POST /api/admin/whitelist` - Add new
   - `DELETE /api/admin/whitelist/<id>` - Remove
   - `PATCH /api/admin/whitelist/<id>` - Update preference
3. Add validation:
   - Phone format validation (E.164)
   - Duplicate check
   - At least 1 admin must remain (cannot delete last one)
4. Implement permission check:
   - Only super admin can manage whitelist (future: RBAC)
   - For now: check if requester is first admin
5. Add initialization script:
   - `scripts/init_admin.py` - Add first admin phone from ENV

**Acceptance Criteria**:
- [ ] Phone numbers can be added via UI
- [ ] Phone numbers can be removed (with safeguards)
- [ ] Notification preferences can be updated
- [ ] UI shows masked phone numbers (last 4 digits only)
- [ ] Validation prevents invalid formats
- [ ] Cannot delete last remaining admin
- [ ] Init script works for first-time setup

**Files to Create**:
- `app/bot/templates/admin_whitelist.html`
- `scripts/init_admin.py`

**Files to Modify**:
- `app/bot/api/admin_routes.py` (add whitelist endpoints)

---

## Testing Plan

### Unit Tests
- [ ] `test_verification_service.py` - Code generation, verification, expiration
- [ ] `test_session_service.py` - Session lifecycle, expiration, validation
- [ ] `test_rate_limiter.py` - Rate limit enforcement, progressive delays
- [ ] `test_auth_middleware.py` - Protected routes, redirects, AJAX handling

### Integration Tests
- [ ] `test_auth_flow.py` - End-to-end authentication flow
- [ ] `test_session_expiry.py` - Session expiration and renewal
- [ ] `test_rate_limiting.py` - Rate limit scenarios with multiple requests

### Manual Testing Checklist
- [ ] Mobile responsiveness (iOS Safari, Android Chrome)
- [ ] Telegram code delivery (live test)
- [ ] SMS fallback (if implementing WP-3.1)
- [ ] Session persistence across browser tabs
- [ ] Logout functionality
- [ ] Rate limiting with rapid requests
- [ ] Expired code handling

---

## Environment Variables

Add to `.env.example`:

```bash
# Admin Authentication
ADMIN_CODE_EXPIRY_MINUTES=5
ADMIN_SESSION_EXPIRY_HOURS=24
ADMIN_MAX_CODE_REQUESTS=3
ADMIN_MAX_VERIFICATION_ATTEMPTS=3
ADMIN_RATE_LIMIT_WINDOW_MINUTES=15

# Admin Whitelist (comma-separated phone numbers in E.164 format)
# Example: +61412345678,+61498765432
ADMIN_WHITELIST_PHONES=

# Optional: SMS Fallback (Twilio)
# TWILIO_ACCOUNT_SID=
# TWILIO_AUTH_TOKEN=
# TWILIO_FROM_NUMBER=
```

---

## Deployment Checklist

1. [ ] Run database migrations
2. [ ] Initialize admin whitelist via script or ENV
3. [ ] Test Telegram bot integration
4. [ ] Configure SMS fallback (optional)
5. [ ] Set HTTPS-only cookies in production
6. [ ] Enable rate limiting
7. [ ] Monitor authentication logs
8. [ ] Set up alerts for failed auth attempts

---

## Rollout Strategy

### Phase 1: Core (Week 1)
- Implement WP-1.1 through WP-1.6
- Deploy to development environment
- Test with 2-3 admin users

### Phase 2: Security Hardening (Week 2)
- Implement WP-2.1 and WP-2.2
- Load testing for rate limits
- Security audit

### Phase 3: Polish & Fallback (Week 3)
- Implement WP-3.1 (SMS fallback)
- Implement WP-3.2 (Whitelist UI)
- Documentation and training

---

**Sign-off**: Ready to begin implementation with WP-1.1
