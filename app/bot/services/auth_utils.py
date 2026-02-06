"""
AI Trading Bot System - Authentication Utilities

Security functions for phone number hashing, code generation, and verification.

Author: Yannick
Copyright (c) 2026 Yannick
"""

import hashlib
import secrets
import bcrypt
from typing import Tuple


def hash_phone_number(phone: str) -> str:
    """
    Hash phone number using bcrypt for secure storage.
    
    Args:
        phone: Phone number in E.164 format (e.g., '+61412345678')
    
    Returns:
        Bcrypt hash string
    
    Examples:
        >>> hash_phone_number('+61412345678')
        '$2b$12$...'  # bcrypt hash
    """
    # Normalize phone number (remove spaces, ensure + prefix)
    normalized = phone.strip().replace(' ', '').replace('-', '')
    if not normalized.startswith('+'):
        normalized = '+' + normalized
    
    # Bcrypt hash (includes salt automatically)
    hashed = bcrypt.hashpw(normalized.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')


def verify_phone_hash(phone: str, phone_hash: str) -> bool:
    """
    Verify phone number against bcrypt hash.
    
    Args:
        phone: Plain phone number to verify
        phone_hash: Bcrypt hash to check against
    
    Returns:
        True if phone matches hash, False otherwise
    
    Examples:
        >>> hash_val = hash_phone_number('+61412345678')
        >>> verify_phone_hash('+61412345678', hash_val)
        True
        >>> verify_phone_hash('+61499999999', hash_val)
        False
    """
    # Normalize phone number same way as hash_phone_number
    normalized = phone.strip().replace(' ', '').replace('-', '')
    if not normalized.startswith('+'):
        normalized = '+' + normalized
    
    try:
        return bcrypt.checkpw(normalized.encode('utf-8'), phone_hash.encode('utf-8'))
    except Exception:
        return False


def generate_verification_code() -> Tuple[str, str]:
    """
    Generate cryptographically secure 6-digit verification code.
    
    Returns:
        Tuple of (plain_code, hashed_code)
        - plain_code: 6-digit string to send to user
        - hashed_code: SHA-256 hash for database storage
    
    Examples:
        >>> code, hash_val = generate_verification_code()
        >>> len(code)
        6
        >>> code.isdigit()
        True
        >>> len(hash_val)
        64  # SHA-256 produces 64 hex characters
    """
    # Generate cryptographically secure 6-digit code
    code = str(secrets.randbelow(1000000)).zfill(6)
    
    # Hash with SHA-256 for storage
    code_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()
    
    return code, code_hash


def hash_verification_code(code: str) -> str:
    """
    Hash verification code using SHA-256.
    
    Args:
        code: 6-digit verification code
    
    Returns:
        SHA-256 hash (64 hex characters)
    
    Examples:
        >>> hash_verification_code('123456')
        '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92'
    """
    return hashlib.sha256(code.encode('utf-8')).hexdigest()


def generate_session_token() -> str:
    """
    Generate cryptographically secure session token.
    
    Returns:
        32-byte random token (64 hex characters)
    
    Examples:
        >>> token = generate_session_token()
        >>> len(token)
        64
    """
    return secrets.token_hex(32)


def mask_phone_number(phone: str) -> str:
    """
    Mask phone number for logging (show only last 4 digits).
    
    Args:
        phone: Phone number in any format
    
    Returns:
        Masked phone number like '****5678'
    
    Examples:
        >>> mask_phone_number('+61412345678')
        '****5678'
        >>> mask_phone_number('0412 345 678')
        '****5678'
    """
    # Remove non-digit characters
    digits = ''.join(c for c in phone if c.isdigit())
    
    if len(digits) < 4:
        return '****'
    
    return '****' + digits[-4:]


def validate_phone_format(phone: str) -> bool:
    """
    Validate phone number format (E.164 standard).
    
    Requirements:
    - Starts with '+'
    - Contains only digits after '+'
    - Length between 10-15 characters (including '+')
    
    Args:
        phone: Phone number to validate
    
    Returns:
        True if valid format, False otherwise
    
    Examples:
        >>> validate_phone_format('+61412345678')
        True
        >>> validate_phone_format('+1234567890')
        True
        >>> validate_phone_format('04123456789')  # Missing +
        False
        >>> validate_phone_format('+123')  # Too short
        False
    """
    if not phone or not phone.startswith('+'):
        return False
    
    # Remove '+' and check if remaining characters are digits
    digits = phone[1:]
    if not digits.isdigit():
        return False
    
    # Check length (E.164: 1-15 digits after '+')
    if len(digits) < 9 or len(digits) > 15:
        return False
    
    return True
