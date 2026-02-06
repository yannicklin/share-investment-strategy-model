# Admin Panel Authentication System - Specification

**Feature**: Phone-Based Authentication for Admin Dashboard  
**Version**: 1.0  
**Date**: February 6, 2026  
**Author**: Yannick  
**Status**: Implementation Ready

---

## User Scenarios & Testing

### User Story 1: Admin Access via Phone Verification
**As an** authorized administrator  
**I want to** access the admin panel using my registered phone number  
**So that** I can securely manage the trading bot system without password management

**Acceptance Scenarios**:
1. **Scenario: Successful Login**
   - GIVEN I navigate to `/admin/dashboard`
   - WHEN the page loads
   - THEN I see a modal popup asking for phone number
   - WHEN I enter my whitelisted phone number "+61412345678"
   - AND I click "Send Verification Code"
   - THEN I receive a 6-digit code via Telegram
   - WHEN I enter the correct code within 5 minutes
   - THEN I am redirected to the admin dashboard
   - AND my session is valid for 24 hours

2. **Scenario: Unauthorized Phone Number**
   - GIVEN I navigate to `/admin/dashboard`
   - WHEN I enter a non-whitelisted phone number "+61499999999"
   - AND I click "Send Verification Code"
   - THEN I see error message: "Phone number not authorized"
   - AND no verification code is sent

3. **Scenario: Expired Verification Code**
   - GIVEN I requested a verification code
   - WHEN 5 minutes pass without entering the code
   - AND I try to submit the expired code
   - THEN I see error: "Verification code expired"
   - AND I must request a new code

4. **Scenario: Invalid Verification Code**
   - GIVEN I received a verification code "123456"
   - WHEN I enter "999999" instead
   - THEN I see error: "Invalid verification code"
   - AND I have 3 attempts remaining (configurable)

5. **Scenario: Rate Limiting**
   - GIVEN I have requested 3 verification codes in 15 minutes
   - WHEN I try to request another code
   - THEN I see error: "Too many requests. Try again in 10 minutes"

### User Story 2: Session Management
**As an** authenticated administrator  
**I want** my session to remain active for a reasonable time  
**So that** I don't need to re-authenticate constantly

**Acceptance Scenarios**:
1. **Scenario: Active Session**
   - GIVEN I authenticated successfully at 10:00 AM
   - WHEN I navigate to `/admin/signals` at 10:30 AM
   - THEN I access the page without re-authentication
   - AND my session is extended by another 24 hours

2. **Scenario: Session Expiry**
   - GIVEN I authenticated successfully yesterday
   - WHEN I navigate to any `/admin/*` page today (25 hours later)
   - THEN I am redirected to the authentication modal
   - AND I must re-authenticate

3. **Scenario: Manual Logout**
   - GIVEN I am authenticated
   - WHEN I click the "Logout" button
   - THEN my session is immediately invalidated
   - AND I am redirected to the authentication screen

---

## Requirements

### Functional Requirements

#### FR-001: Phone Whitelist Management
- System MUST maintain a whitelist of authorized phone numbers
- Whitelist MUST be stored in encrypted format in database
- Whitelist MUST support international formats (E.164 standard)
- Admin MUST be able to add/remove numbers via environment variables or API

#### FR-002: Verification Code Generation
- System MUST generate cryptographically secure 6-digit codes
- Each code MUST be single-use (invalidated after verification)
- Each code MUST have configurable expiration time (default: 5 minutes)
- Each phone number MUST NOT have more than 1 active code at a time

#### FR-003: Verification Code Delivery
- System MUST support multiple delivery channels:
  - Telegram Bot API (primary)
  - SMS via Twilio/Telnyx (fallback)
- System MUST log all delivery attempts for audit
- System MUST retry failed deliveries (max 2 retries)

#### FR-004: Rate Limiting
- System MUST limit verification requests to 3 per 15 minutes per phone number
- System MUST limit verification requests to 10 per hour per IP address
- System MUST implement progressive delays (1s, 5s, 30s) for failed attempts

#### FR-005: Session Management
- System MUST create secure session tokens after successful verification
- Session tokens MUST be stored server-side (not JWT)
- Sessions MUST expire after configurable time (default: 24 hours)
- Sessions MUST be invalidated on logout
- Sessions MUST support "remember device" option (future enhancement)

#### FR-006: Authentication Middleware
- System MUST protect all `/admin/*` routes with authentication
- System MUST redirect unauthenticated users to login modal
- System MUST preserve intended destination URL for post-login redirect
- System MUST support whitelisting certain public endpoints (e.g., `/admin/health`)

#### FR-007: Audit Logging
- System MUST log all authentication attempts (success/failure)
- System MUST log all verification code requests
- System MUST log session creation/expiration events
- Logs MUST include: timestamp, phone number (masked), IP address, user agent

### Technical Requirements

#### TR-001: Database Schema
- `admin_whitelist` table: id, phone_number_hash, created_at, created_by
- `verification_codes` table: id, phone_hash, code_hash, expires_at, used_at, attempts
- `admin_sessions` table: id, session_token, phone_hash, ip_address, user_agent, expires_at
- `auth_logs` table: id, event_type, phone_hash, ip_address, success, created_at

#### TR-002: Security Standards
- Phone numbers MUST be hashed using bcrypt before storage
- Verification codes MUST be hashed using SHA-256 before storage
- Session tokens MUST be 32-byte random strings (hex-encoded)
- All communication MUST use HTTPS in production
- Rate limiting MUST use Redis/in-memory cache for performance

#### TR-003: Configuration
- All timeouts/limits MUST be configurable via environment variables:
  - `ADMIN_CODE_EXPIRY_MINUTES` (default: 5)
  - `ADMIN_SESSION_EXPIRY_HOURS` (default: 24)
  - `ADMIN_MAX_CODE_REQUESTS` (default: 3 per 15 min)
  - `ADMIN_MAX_VERIFICATION_ATTEMPTS` (default: 3)
  - `ADMIN_RATE_LIMIT_WINDOW_MINUTES` (default: 15)

#### TR-004: Notification Integration
- System MUST integrate with existing `notification_service.py`
- System MUST gracefully handle notification failures
- System MUST provide clear error messages for delivery issues

#### TR-005: Frontend Requirements
- Modal MUST be responsive (mobile-friendly)
- Modal MUST use Tailwind CSS (consistent with project)
- Modal MUST show loading states during verification
- Modal MUST support accessibility (ARIA labels, keyboard navigation)

---

## Success Criteria

### Security Metrics
- ✅ Zero unauthorized access attempts succeed
- ✅ All verification codes expire within configured time
- ✅ All sessions are properly invalidated on logout
- ✅ Phone numbers never stored in plaintext

### User Experience Metrics
- ✅ Authentication completes in < 30 seconds (normal case)
- ✅ Modal is responsive on mobile devices (tested on iOS/Android)
- ✅ Error messages are clear and actionable
- ✅ No false positive rate limiting (legitimate users not blocked)

### Operational Metrics
- ✅ Telegram delivery success rate > 95%
- ✅ SMS fallback delivery success rate > 99%
- ✅ Authentication service uptime > 99.9%
- ✅ Complete audit trail for all authentication events

### Performance Metrics
- ✅ Verification code generation < 100ms
- ✅ Authentication check < 50ms
- ✅ Database queries optimized (indexed on phone_hash, session_token)

---

## Dependencies and Assumptions

### Dependencies
1. **Telegram Bot API** - Primary notification channel
   - Requires: `TELEGRAM_BOT_TOKEN` environment variable
   - Requires: Telegram chat IDs mapped to phone numbers

2. **SMS Service** (Optional fallback)
   - Twilio or Telnyx account
   - Requires: API credentials in environment

3. **Database** - PostgreSQL (Supabase)
   - Existing database connection
   - Migration support for new tables

4. **Frontend Framework** - Flask Jinja2 templates
   - Modal component library or custom implementation

### Assumptions
1. Administrators have access to Telegram or SMS-capable phones
2. Phone numbers are in E.164 format (e.g., +61412345678)
3. Telegram Bot is already configured (from existing notification system)
4. Production environment has HTTPS enabled
5. Admin panel is low-traffic (< 100 logins/day)

### Risks & Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| Telegram API down | High | Implement SMS fallback |
| SMS delivery delays | Medium | Extend code expiry to 10 minutes |
| Brute force attacks | High | Implement progressive rate limiting |
| Session hijacking | Critical | Use secure cookies, rotate tokens |
| Phone number leakage | Critical | Always hash, never log plaintext |

---

## Non-Functional Requirements

### NFR-001: Scalability
- System MUST support up to 50 concurrent admin users
- Rate limiting MUST use in-memory cache (avoid DB overload)

### NFR-002: Maintainability
- Code MUST follow existing project patterns (PortfolioService style)
- All functions MUST have docstrings with examples
- Configuration MUST be externalized (no hardcoded values)

### NFR-003: Testability
- All authentication logic MUST be unit-testable
- Mock services MUST be provided for Telegram/SMS
- Test suite MUST cover success/failure scenarios

### NFR-004: Monitoring
- Authentication failures MUST trigger alerts (> 10/minute)
- Verification code delivery failures MUST be logged to Sentry
- Session expiry rate MUST be monitored (identify UX issues)

---

## Future Enhancements (Not in v1.0)

1. **Multi-Factor Authentication (MFA)**
   - Add TOTP authenticator app support
   - Add backup recovery codes

2. **Remember Device**
   - Store device fingerprint
   - Skip verification for trusted devices (30 days)

3. **Admin Role-Based Access Control (RBAC)**
   - Super Admin vs. Viewer roles
   - Granular permissions (view-only vs. execute)

4. **WebAuthn/Passkey Support**
   - Biometric authentication
   - Hardware security keys

5. **Admin Activity Dashboard**
   - Real-time login monitoring
   - Suspicious activity detection

---

## API Design (Internal)

### Authentication Flow Endpoints

#### POST /api/admin/auth/request-code
**Request**:
```json
{
  "phone": "+61412345678"
}
```

**Response (Success)**:
```json
{
  "success": true,
  "message": "Verification code sent via Telegram",
  "expires_in": 300,
  "request_id": "req_abc123"
}
```

**Response (Rate Limited)**:
```json
{
  "success": false,
  "error": "Too many requests. Try again in 12 minutes.",
  "retry_after": 720
}
```

#### POST /api/admin/auth/verify-code
**Request**:
```json
{
  "phone": "+61412345678",
  "code": "123456",
  "request_id": "req_abc123"
}
```

**Response (Success)**:
```json
{
  "success": true,
  "message": "Authentication successful",
  "redirect_url": "/admin/dashboard",
  "session_expires_at": "2026-02-07T10:00:00Z"
}
```

**Response (Invalid)**:
```json
{
  "success": false,
  "error": "Invalid verification code",
  "attempts_remaining": 2
}
```

#### POST /api/admin/auth/logout
**Request**: (Session cookie)

**Response**:
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## Implementation Notes

### Phase 1: Core Authentication (Priority)
- Database models
- Verification code service
- Session management
- Basic modal UI

### Phase 2: Enhanced Security (Important)
- Rate limiting
- Audit logging
- Progressive delays

### Phase 3: Polish (Nice-to-Have)
- SMS fallback
- Better error messages
- Admin whitelist management UI

---

**Sign-off**: Ready for implementation planning
