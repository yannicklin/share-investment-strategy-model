"""
AI Trading Bot System - Phone Verification Service

Handles verification code generation, delivery, and validation for admin authentication.

Flow:
1. Admin requests code via phone number
2. System checks whitelist and rate limits
3. Code generated and sent via Telegram/SMS
4. Admin enters code for verification
5. Session created on successful verification

Author: Yannick
Copyright (c) 2026 Yannick
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
from app.bot import db
from app.bot.shared.models import AdminWhitelist, VerificationCode, AuthLog
from app.bot.services.auth_utils import (
    hash_phone_number,
    verify_phone_hash,
    generate_verification_code,
    hash_verification_code,
    mask_phone_number,
    validate_phone_format
)
from app.bot.services.notification_service import notify_verification_code
import secrets

logger = logging.getLogger(__name__)

# Configuration from environment
CODE_EXPIRY_MINUTES = int(os.getenv('ADMIN_CODE_EXPIRY_MINUTES', '5'))
MAX_VERIFICATION_ATTEMPTS = int(os.getenv('ADMIN_MAX_VERIFICATION_ATTEMPTS', '3'))


class VerificationService:
    """
    Manages verification code lifecycle for admin authentication.
    
    Responsibilities:
    - Generate cryptographically secure codes
    - Deliver codes via Telegram/SMS
    - Validate codes against stored hashes
    - Enforce rate limits and expiration
    - Audit logging
    """
    
    def __init__(self):
        self.code_expiry_minutes = CODE_EXPIRY_MINUTES
        self.max_attempts = MAX_VERIFICATION_ATTEMPTS
    
    def request_verification_code(
        self,
        phone: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Request verification code for phone number.
        
        Args:
            phone: Phone number in E.164 format (e.g., '+61412345678')
            ip_address: IP address of requester (for rate limiting)
        
        Returns:
            Tuple of (success: bool, message: str, request_id: Optional[str])
        
        Examples:
            >>> service = VerificationService()
            >>> success, msg, req_id = service.request_verification_code('+61412345678')
            >>> if success:
            ...     print(f"Code sent! Request ID: {req_id}")
        """
        # Validate phone format
        if not validate_phone_format(phone):
            self._log_auth_event(
                event_type='request_code',
                phone=phone,
                ip_address=ip_address,
                success=False,
                error='Invalid phone format'
            )
            return False, "Invalid phone number format. Use E.164 format (e.g., +61412345678)", None
        
        # Check if phone is whitelisted
        phone_hash = hash_phone_number(phone)
        is_whitelisted, notification_pref = self._check_whitelist(phone_hash)
        
        if not is_whitelisted:
            self._log_auth_event(
                event_type='request_code',
                phone=phone,
                ip_address=ip_address,
                success=False,
                error='Phone not whitelisted'
            )
            return False, "Phone number not authorized. Contact system administrator.", None
        
        # TODO: Check rate limits (implement in WP-2.1)
        # For now, just check if there's an active unexpired code
        active_code = VerificationCode.query.filter_by(
            phone_number_hash=phone_hash
        ).filter(
            VerificationCode.used_at.is_(None),
            VerificationCode.expires_at > datetime.utcnow()
        ).first()
        
        if active_code:
            seconds_remaining = (active_code.expires_at - datetime.utcnow()).total_seconds()
            return False, f"Code already sent. Wait {int(seconds_remaining)} seconds before requesting new code.", None
        
        # Generate verification code
        plain_code, code_hash = generate_verification_code()
        request_id = secrets.token_hex(16)
        
        # Create verification code record
        expires_at = datetime.utcnow() + timedelta(minutes=self.code_expiry_minutes)
        
        verification = VerificationCode(
            phone_number_hash=phone_hash,
            code_hash=code_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            request_id=request_id
        )
        
        db.session.add(verification)
        db.session.commit()
        
        # Send code via Telegram/SMS
        delivery_success = self._send_code(phone, plain_code, notification_pref)
        
        if not delivery_success:
            # Log delivery failure but don't delete code (allow manual retry)
            self._log_auth_event(
                event_type='request_code',
                phone=phone,
                ip_address=ip_address,
                success=False,
                error='Code delivery failed'
            )
            return False, "Failed to send verification code. Please try again.", None
        
        # Log success
        self._log_auth_event(
            event_type='request_code',
            phone=phone,
            ip_address=ip_address,
            success=True
        )
        
        logger.info(f"Verification code sent to {mask_phone_number(phone)} via {notification_pref}")
        
        return True, f"Verification code sent via {notification_pref}. Expires in {self.code_expiry_minutes} minutes.", request_id
    
    def verify_code(
        self,
        phone: str,
        code: str,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Verify submitted code against stored hash.
        
        Args:
            phone: Phone number in E.164 format
            code: 6-digit code entered by user
            request_id: Optional request ID from code request
            ip_address: IP address (for logging)
        
        Returns:
            Tuple of (success: bool, message: str)
        
        Examples:
            >>> service = VerificationService()
            >>> success, msg = service.verify_code('+61412345678', '123456')
            >>> if success:
            ...     print("Code verified! Create session now.")
        """
        # Validate inputs
        if not validate_phone_format(phone):
            return False, "Invalid phone number format"
        
        if not code or not code.isdigit() or len(code) != 6:
            return False, "Invalid verification code format (must be 6 digits)"
        
        # Hash phone and code for lookup
        phone_hash = hash_phone_number(phone)
        code_hash = hash_verification_code(code)
        
        # Find verification code
        query = VerificationCode.query.filter_by(
            phone_number_hash=phone_hash,
            code_hash=code_hash
        )
        
        if request_id:
            query = query.filter_by(request_id=request_id)
        
        verification = query.first()
        
        # Check if code exists
        if not verification:
            self._log_auth_event(
                event_type='verify_code',
                phone=phone,
                ip_address=ip_address,
                success=False,
                error='Code not found'
            )
            return False, "Invalid verification code"
        
        # Check if already used
        if verification.used_at:
            self._log_auth_event(
                event_type='verify_code',
                phone=phone,
                ip_address=ip_address,
                success=False,
                error='Code already used'
            )
            return False, "Verification code already used"
        
        # Check if expired
        if datetime.utcnow() > verification.expires_at:
            self._log_auth_event(
                event_type='verify_code',
                phone=phone,
                ip_address=ip_address,
                success=False,
                error='Code expired'
            )
            return False, "Verification code expired. Request a new one."
        
        # Check attempts limit
        verification.attempts += 1
        
        if verification.attempts > self.max_attempts:
            db.session.commit()
            self._log_auth_event(
                event_type='verify_code',
                phone=phone,
                ip_address=ip_address,
                success=False,
                error='Max attempts exceeded'
            )
            return False, "Too many failed attempts. Request a new code."
        
        # Mark as used
        verification.used_at = datetime.utcnow()
        db.session.commit()
        
        # Log success
        self._log_auth_event(
            event_type='verify_code',
            phone=phone,
            ip_address=ip_address,
            success=True
        )
        
        logger.info(f"Verification successful for {mask_phone_number(phone)}")
        
        return True, "Verification successful"
    
    def _check_whitelist(self, phone_hash: str) -> Tuple[bool, str]:
        """
        Check if phone hash exists in whitelist.
        
        Args:
            phone_hash: Bcrypt hash of phone number
        
        Returns:
            Tuple of (is_whitelisted: bool, notification_preference: str)
        """
        # NOTE: This is inefficient for large whitelists (needs optimization)
        # For production, consider caching whitelist in memory
        
        whitelist_entry = AdminWhitelist.query.filter_by(
            phone_number_hash=phone_hash
        ).first()
        
        if whitelist_entry:
            return True, whitelist_entry.notification_preference
        
        return False, 'telegram'
    
    def _send_code(self, phone: str, code: str, channel: str) -> bool:
        """
        Send verification code via notification channel.
        
        Args:
            phone: Phone number
            code: Plain 6-digit code
            channel: 'telegram', 'sms', or 'both'
        
        Returns:
            True if sent successfully, False otherwise
        """
        message = f"🔐 Your admin verification code: {code}\n\nExpires in {self.code_expiry_minutes} minutes.\n\nDo not share this code with anyone."
        
        try:
            # For now, use existing notification service
            # TODO: Map phone to Telegram chat ID
            result = notify_verification_code(phone, code, channel)
            return result
        except Exception as e:
            logger.error(f"Failed to send verification code: {str(e)}")
            return False
    
    def _log_auth_event(
        self,
        event_type: str,
        phone: str,
        ip_address: Optional[str],
        success: bool,
        error: Optional[str] = None
    ):
        """
        Log authentication event for audit trail.
        
        Args:
            event_type: Type of event (request_code, verify_code, etc.)
            phone: Phone number (will be masked in log)
            ip_address: IP address
            success: Whether event succeeded
            error: Error message if failed
        """
        phone_hash = hash_phone_number(phone)
        phone_masked = mask_phone_number(phone)
        
        log_entry = AuthLog(
            event_type=event_type,
            phone_number_masked=phone_masked,
            phone_number_hash=phone_hash,
            ip_address=ip_address,
            success=success,
            error_message=error
        )
        
        db.session.add(log_entry)
        db.session.commit()
