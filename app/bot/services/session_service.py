"""
AI Trading Bot System - Session Management Service

Handles admin session lifecycle: creation, validation, renewal, and invalidation.

Security:
- Session tokens are 32-byte cryptographically secure random strings
- Tokens stored server-side (not JWT) for revocation capability
- Sliding expiration window (extends on activity)
- HTTP-only cookies to prevent XSS attacks

Author: Yannick
Copyright (c) 2026 Yannick
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from app.bot import db
from app.bot.shared.models import AdminSession, AuthLog
from app.bot.services.auth_utils import generate_session_token, mask_phone_number
from flask import request

logger = logging.getLogger(__name__)

# Configuration from environment
SESSION_EXPIRY_HOURS = int(os.getenv('ADMIN_SESSION_EXPIRY_HOURS', '24'))


class SessionService:
    """
    Manages admin session lifecycle for authenticated users.
    
    Responsibilities:
    - Create secure sessions after successful verification
    - Validate session tokens on each request
    - Extend session expiry on activity (sliding window)
    - Invalidate sessions on logout
    - Clean up expired sessions
    """
    
    def __init__(self):
        self.session_expiry_hours = SESSION_EXPIRY_HOURS
    
    def create_session(
        self,
        phone_hash: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Create new admin session after successful authentication.
        
        Args:
            phone_hash: Bcrypt hash of authenticated phone number
            ip_address: IP address of user
            user_agent: Browser user agent string
        
        Returns:
            Session token (64 hex characters)
        
        Examples:
            >>> service = SessionService()
            >>> token = service.create_session(phone_hash, '127.0.0.1', 'Mozilla...')
            >>> len(token)
            64
        """
        # Generate secure session token
        session_token = generate_session_token()
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(hours=self.session_expiry_hours)
        
        # Create session record
        session = AdminSession(
            session_token=session_token,
            phone_number_hash=phone_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        
        db.session.add(session)
        db.session.commit()
        
        # Log session creation
        self._log_session_event(
            event_type='session_created',
            phone_hash=phone_hash,
            ip_address=ip_address,
            success=True
        )
        
        logger.info(f"Session created for admin (expires: {expires_at})")
        
        return session_token
    
    def validate_session(
        self,
        session_token: str,
        extend_on_activity: bool = True,
        check_ip: bool = False
    ) -> Optional[Dict]:
        """
        Validate session token and optionally extend expiration.
        
        Args:
            session_token: Session token from cookie
            extend_on_activity: If True, extends session expiry (sliding window)
            check_ip: If True, validates IP matches session creation IP
        
        Returns:
            Dict with session info if valid:
            {
                'phone_hash': str,
                'ip_address': str,
                'created_at': datetime,
                'expires_at': datetime
            }
            None if invalid or expired
        
        Examples:
            >>> service = SessionService()
            >>> session_info = service.validate_session(token)
            >>> if session_info:
            ...     print(f"Valid session for {session_info['phone_hash']}")
        """
        if not session_token:
            return None
        
        # Find session in database
        session = AdminSession.query.filter_by(session_token=session_token).first()
        
        if not session:
            logger.debug("Session not found")
            return None
        
        # Check expiration
        if datetime.utcnow() > session.expires_at:
            logger.info("Session expired")
            
            # Log expiration event
            self._log_session_event(
                event_type='session_expired',
                phone_hash=session.phone_number_hash,
                ip_address=session.ip_address,
                success=False
            )
            
            # Delete expired session
            db.session.delete(session)
            db.session.commit()
            
            return None
        
        # Optional: Check IP address matches
        if check_ip:
            current_ip = self._get_request_ip()
            if current_ip and session.ip_address and current_ip != session.ip_address:
                logger.warning(f"IP mismatch: {current_ip} != {session.ip_address}")
                
                # Log suspicious activity
                self._log_session_event(
                    event_type='session_ip_mismatch',
                    phone_hash=session.phone_number_hash,
                    ip_address=current_ip,
                    success=False
                )
                
                # Optional: Invalidate session on IP mismatch (configurable)
                # For now, just log and allow (IP can change on mobile networks)
        
        # Update last activity
        session.last_activity = datetime.utcnow()
        
        # Extend expiration (sliding window)
        if extend_on_activity:
            session.expires_at = datetime.utcnow() + timedelta(hours=self.session_expiry_hours)
        
        db.session.commit()
        
        # Return session info
        return {
            'phone_hash': session.phone_number_hash,
            'ip_address': session.ip_address,
            'user_agent': session.user_agent,
            'created_at': session.created_at,
            'last_activity': session.last_activity,
            'expires_at': session.expires_at
        }
    
    def invalidate_session(
        self,
        session_token: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Invalidate session (logout).
        
        Args:
            session_token: Session token to invalidate
            ip_address: IP address (for logging)
        
        Returns:
            True if session was found and deleted, False otherwise
        
        Examples:
            >>> service = SessionService()
            >>> service.invalidate_session(token)
            True
        """
        if not session_token:
            return False
        
        # Find and delete session
        session = AdminSession.query.filter_by(session_token=session_token).first()
        
        if not session:
            return False
        
        phone_hash = session.phone_number_hash
        
        # Delete session
        db.session.delete(session)
        db.session.commit()
        
        # Log logout
        self._log_session_event(
            event_type='logout',
            phone_hash=phone_hash,
            ip_address=ip_address or session.ip_address,
            success=True
        )
        
        logger.info("Session invalidated (logout)")
        
        return True
    
    def cleanup_expired_sessions(self) -> int:
        """
        Delete all expired sessions from database.
        
        Should be run periodically (e.g., daily cron job) to prevent
        table bloat.
        
        Returns:
            Number of sessions deleted
        
        Examples:
            >>> service = SessionService()
            >>> deleted = service.cleanup_expired_sessions()
            >>> print(f"Cleaned up {deleted} expired sessions")
        """
        expired_sessions = AdminSession.query.filter(
            AdminSession.expires_at < datetime.utcnow()
        ).all()
        
        count = len(expired_sessions)
        
        if count > 0:
            for session in expired_sessions:
                db.session.delete(session)
            
            db.session.commit()
            logger.info(f"Cleaned up {count} expired sessions")
        
        return count
    
    def get_active_sessions_count(self) -> int:
        """
        Get count of currently active (non-expired) sessions.
        
        Useful for monitoring admin activity.
        
        Returns:
            Number of active sessions
        """
        return AdminSession.query.filter(
            AdminSession.expires_at > datetime.utcnow()
        ).count()
    
    def invalidate_all_sessions_for_phone(self, phone_hash: str) -> int:
        """
        Invalidate all sessions for a specific phone number.
        
        Useful for:
        - Forcing logout after security breach
        - Removing admin access
        
        Args:
            phone_hash: Phone hash to invalidate sessions for
        
        Returns:
            Number of sessions invalidated
        """
        sessions = AdminSession.query.filter_by(
            phone_number_hash=phone_hash
        ).all()
        
        count = len(sessions)
        
        if count > 0:
            for session in sessions:
                db.session.delete(session)
            
            db.session.commit()
            
            # Log forced logout
            self._log_session_event(
                event_type='forced_logout_all',
                phone_hash=phone_hash,
                ip_address=None,
                success=True
            )
            
            logger.warning(f"Invalidated {count} sessions for admin")
        
        return count
    
    def _get_request_ip(self) -> Optional[str]:
        """
        Get IP address from current Flask request.
        
        Handles proxy headers (X-Forwarded-For, X-Real-IP).
        
        Returns:
            IP address or None if not in request context
        """
        try:
            # Check proxy headers first
            if request.headers.get('X-Forwarded-For'):
                # X-Forwarded-For can be a comma-separated list
                return request.headers.get('X-Forwarded-For').split(',')[0].strip()
            elif request.headers.get('X-Real-IP'):
                return request.headers.get('X-Real-IP')
            else:
                return request.remote_addr
        except RuntimeError:
            # Not in request context
            return None
    
    def _log_session_event(
        self,
        event_type: str,
        phone_hash: str,
        ip_address: Optional[str],
        success: bool
    ):
        """
        Log session event for audit trail.
        
        Args:
            event_type: Type of event (session_created, logout, etc.)
            phone_hash: Phone hash
            ip_address: IP address
            success: Whether event succeeded
        """
        # Create masked phone for display (we don't have plaintext, so just use hash prefix)
        phone_masked = '****' + phone_hash[-8:] if phone_hash else None
        
        log_entry = AuthLog(
            event_type=event_type,
            phone_number_masked=phone_masked,
            phone_number_hash=phone_hash,
            ip_address=ip_address,
            success=success
        )
        
        db.session.add(log_entry)
        db.session.commit()
