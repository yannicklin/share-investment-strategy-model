"""
AI Trading Bot System - Phone Number Normalization Utilities

Smart phone number handling that accepts multiple formats:
- E.164 international: +61431121011
- Local format: 0431121011
- Formatted: 0431-121-011, 0431 121 011

Author: Yannick
Copyright (c) 2026 Yannick
"""

import re
from typing import Optional


# Country code mappings for normalization
COUNTRY_CODES = {
    'AU': {
        'code': '+61',
        'local_prefix': '0',
        'min_length': 9,  # After removing leading 0
        'max_length': 9
    },
    'US': {
        'code': '+1',
        'local_prefix': '1',
        'min_length': 10,
        'max_length': 10
    },
    'TW': {
        'code': '+886',
        'local_prefix': '0',
        'min_length': 9,
        'max_length': 9
    }
}

# Default country for normalization
DEFAULT_COUNTRY = 'AU'


def normalize_phone_number(phone: str, country: str = DEFAULT_COUNTRY) -> str:
    """
    Normalize phone number to E.164 international format.
    
    Accepts various input formats:
    - Local: 0431121011 → +61431121011
    - E.164: +61431121011 → +61431121011
    - With dashes: 0431-121-011 → +61431121011
    - With spaces: 0431 121 011 → +61431121011
    - Without prefix: 431121011 → +61431121011
    
    Args:
        phone: Phone number in any supported format
        country: Country code ('AU', 'US', 'TW')
    
    Returns:
        Phone number in E.164 format (+[country_code][number])
    
    Raises:
        ValueError: If phone number is invalid
    
    Examples:
        >>> normalize_phone_number('0431121011')
        '+61431121011'
        >>> normalize_phone_number('+61-431-121-011')
        '+61431121011'
        >>> normalize_phone_number('431121011')
        '+61431121011'
    """
    if not phone:
        raise ValueError("Phone number cannot be empty")
    
    # Get country configuration
    if country not in COUNTRY_CODES:
        raise ValueError(f"Unsupported country: {country}")
    
    config = COUNTRY_CODES[country]
    country_code = config['code']
    local_prefix = config['local_prefix']
    
    # Remove all formatting characters (spaces, dashes, parentheses)
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Check if already in E.164 format (starts with +)
    if cleaned.startswith('+'):
        # Validate it matches expected country code
        if cleaned.startswith(country_code):
            # Extract digits after country code
            digits = cleaned[len(country_code):]
            
            # Validate length
            if len(digits) < config['min_length'] or len(digits) > config['max_length']:
                raise ValueError(
                    f"Invalid phone number length for {country}: {len(digits)} digits "
                    f"(expected {config['min_length']}-{config['max_length']})"
                )
            
            return country_code + digits
        else:
            # Has + but different country code - just validate format
            if not re.match(r'^\+[0-9]{8,15}$', cleaned):
                raise ValueError(f"Invalid E.164 format: {cleaned}")
            return cleaned
    
    # Check if has country code digits without + (e.g., 61431121011)
    if cleaned.startswith(country_code.lstrip('+')):
        # Has country code, just missing +
        return '+' + cleaned
    
    # Local format - process based on country rules
    digits = cleaned
    
    # Remove local prefix if present (e.g., leading 0 in Australia)
    if digits.startswith(local_prefix):
        digits = digits[len(local_prefix):]
    
    # Validate digit length
    if len(digits) < config['min_length'] or len(digits) > config['max_length']:
        raise ValueError(
            f"Invalid phone number length for {country}: {len(digits)} digits "
            f"(expected {config['min_length']}-{config['max_length']})"
        )
    
    # Validate all characters are digits
    if not digits.isdigit():
        raise ValueError(f"Phone number contains invalid characters: {phone}")
    
    # Combine country code with digits
    normalized = country_code + digits
    
    return normalized


def format_phone_display(phone: str) -> str:
    """
    Format E.164 phone number for human-readable display.
    
    Converts E.164 to formatted display:
    +61431121011 → +61-431-121-011
    +14155551234 → +1-415-555-1234
    
    Args:
        phone: Phone number in E.164 format
    
    Returns:
        Formatted phone number for display
    
    Examples:
        >>> format_phone_display('+61431121011')
        '+61-431-121-011'
        >>> format_phone_display('+14155551234')
        '+1-415-555-1234'
    """
    if not phone or not phone.startswith('+'):
        return phone
    
    # Australia: +61-4XX-XXX-XXX
    if phone.startswith('+61'):
        country = '+61'
        digits = phone[3:]
        if len(digits) == 9:
            return f"{country}-{digits[0:3]}-{digits[3:6]}-{digits[6:9]}"
    
    # USA: +1-XXX-XXX-XXXX
    elif phone.startswith('+1'):
        country = '+1'
        digits = phone[2:]
        if len(digits) == 10:
            return f"{country}-{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
    
    # Taiwan: +886-9XX-XXX-XXX
    elif phone.startswith('+886'):
        country = '+886'
        digits = phone[4:]
        if len(digits) == 9:
            return f"{country}-{digits[0:3]}-{digits[3:6]}-{digits[6:9]}"
    
    # Default: return as-is
    return phone


def detect_country_from_phone(phone: str) -> Optional[str]:
    """
    Detect country from phone number format.
    
    Args:
        phone: Phone number (any format)
    
    Returns:
        Country code ('AU', 'US', 'TW') or None if cannot detect
    
    Examples:
        >>> detect_country_from_phone('+61431121011')
        'AU'
        >>> detect_country_from_phone('0431121011')
        'AU'
        >>> detect_country_from_phone('+14155551234')
        'US'
    """
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Check E.164 format
    if cleaned.startswith('+61'):
        return 'AU'
    elif cleaned.startswith('+1'):
        return 'US'
    elif cleaned.startswith('+886'):
        return 'TW'
    
    # Check local formats
    if cleaned.startswith('0') and len(cleaned) == 10:
        return 'AU'  # Australian mobile
    elif cleaned.startswith('1') and len(cleaned) == 11:
        return 'US'  # US with leading 1
    
    # Default to configured default
    return DEFAULT_COUNTRY


def validate_and_normalize(phone: str, auto_detect_country: bool = True) -> str:
    """
    Validate and normalize phone number with automatic country detection.
    
    Args:
        phone: Phone number in any format
        auto_detect_country: If True, auto-detect country from number
    
    Returns:
        Normalized phone number in E.164 format
    
    Raises:
        ValueError: If phone number is invalid
    
    Examples:
        >>> validate_and_normalize('0431121011')
        '+61431121011'
        >>> validate_and_normalize('+1-415-555-1234')
        '+14155551234'
    """
    if auto_detect_country:
        country = detect_country_from_phone(phone)
    else:
        country = DEFAULT_COUNTRY
    
    return normalize_phone_number(phone, country)
