"""
AI Trading Bot System - Authentication Middleware

Decorator and middleware functions for protecting admin routes.

Usage:
    from app.bot.api.auth_middleware import auth_required
    
    @app.route('/admin/dashboard')
    @auth_required
    def dashboard():
        # Access authenticated phone hash via g.admin_phone_hash
        return render_template('dashboard.html')

Author: Yannick
Copyright (c) 2026 Yannick
"""

from functools import wraps
from flask import request, redirect, url_for, jsonify, g, make_response
from app.bot.services.session_service import SessionService
import logging

logger = logging.getLogger(__name__)

# Session service instance
session_service = SessionService()

# Cookie name for session token
SESSION_COOKIE_NAME = 'admin_session'

# Public endpoints that don't require authentication
PUBLIC_ENDPOINTS = [
    'auth_routes.request_code',
    'auth_routes.verify_code',
    'auth_routes.status',
    'static',
    'health'  # Health check endpoint
]


def auth_required(f):
    """
    Decorator to protect admin routes with authentication.
    
    Validates session cookie and ensures user is authenticated.
    If not authenticated:
    - For HTML requests: Redirects to login modal
    - For API/AJAX requests: Returns 401 JSON response
    
    Sets g.admin_phone_hash for access in route handlers.
    
    Usage:
        @app.route('/admin/dashboard')
        @auth_required
        def dashboard():
            phone_hash = g.admin_phone_hash
            return render_template('dashboard.html')
    
    Args:
        f: Route function to protect
    
    Returns:
        Wrapped function with authentication check
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get session token from cookie
        session_token = request.cookies.get(SESSION_COOKIE_NAME)
        
        # Validate session
        session_info = session_service.validate_session(
            session_token,
            extend_on_activity=True,
            check_ip=False  # Don't enforce IP (mobile networks change IPs)
        )
        
        if not session_info:
            # Not authenticated
            logger.debug(f"Unauthorized access attempt to {request.endpoint}")
            
            # Check if this is an AJAX/API request
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Return JSON 401 for AJAX requests
                return jsonify({
                    'error': 'Authentication required',
                    'authenticated': False
                }), 401
            else:
                # Redirect to login page (or show modal)
                # Store intended destination for post-login redirect
                session_redirect = request.url
                
                # For now, redirect to dashboard with auth modal
                # The frontend will detect no session and show modal
                return redirect(url_for('admin_ui_routes.dashboard', next=session_redirect))
        
        # Session is valid - store phone hash in Flask g for access in route
        g.admin_phone_hash = session_info['phone_hash']
        g.admin_session_info = session_info
        
        # Call the actual route function
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_admin_phone_hash():
    """
    Get authenticated admin's phone hash from current request context.
    
    Only works within a request that passed @auth_required.
    
    Returns:
        Phone hash string or None if not authenticated
    
    Examples:
        >>> phone_hash = get_current_admin_phone_hash()
        >>> if phone_hash:
        ...     print("Admin is authenticated")
    """
    return getattr(g, 'admin_phone_hash', None)


def get_current_session_info():
    """
    Get full session info for current authenticated admin.
    
    Returns:
        Dict with session info or None if not authenticated:
        {
            'phone_hash': str,
            'ip_address': str,
            'created_at': datetime,
            'expires_at': datetime
        }
    """
    return getattr(g, 'admin_session_info', None)


def set_session_cookie(response, session_token: str, max_age_hours: int = 24):
    """
    Set session cookie in HTTP response.
    
    Configures cookie with security flags:
    - HttpOnly: Prevent JavaScript access (XSS protection)
    - Secure: Only send over HTTPS (production)
    - SameSite: Prevent CSRF attacks
    
    Args:
        response: Flask response object
        session_token: Session token to store
        max_age_hours: Cookie expiration in hours
    
    Returns:
        Modified response object
    
    Examples:
        >>> resp = make_response(jsonify({'success': True}))
        >>> resp = set_session_cookie(resp, session_token)
        >>> return resp
    """
    # Calculate max age in seconds
    max_age_seconds = max_age_hours * 3600
    
    # Set cookie with security flags
    response.set_cookie(
        SESSION_COOKIE_NAME,
        session_token,
        max_age=max_age_seconds,
        httponly=True,  # Prevent JavaScript access
        secure=request.is_secure,  # Only send over HTTPS in production
        samesite='Lax'  # Prevent CSRF while allowing normal navigation
    )
    
    return response


def clear_session_cookie(response):
    """
    Clear session cookie (for logout).
    
    Args:
        response: Flask response object
    
    Returns:
        Modified response object
    
    Examples:
        >>> resp = make_response(jsonify({'success': True, 'message': 'Logged out'}))
        >>> resp = clear_session_cookie(resp)
        >>> return resp
    """
    response.set_cookie(
        SESSION_COOKIE_NAME,
        '',
        max_age=0,
        httponly=True,
        secure=request.is_secure,
        samesite='Lax'
    )
    
    return response


def is_endpoint_public(endpoint):
    """
    Check if endpoint should be accessible without authentication.
    
    Args:
        endpoint: Flask endpoint name (e.g., 'admin_ui_routes.dashboard')
    
    Returns:
        True if endpoint is public, False otherwise
    """
    if not endpoint:
        return False
    
    # Check against public endpoint list
    for public_ep in PUBLIC_ENDPOINTS:
        if endpoint == public_ep or endpoint.startswith(public_ep + '.'):
            return True
    
    return False


def init_app(app):
    """
    Initialize authentication middleware for Flask app.
    
    Registers before_request handler to check authentication globally.
    
    Args:
        app: Flask application instance
    
    Usage:
        from app.bot.api.auth_middleware import init_app
        init_app(app)
    """
    @app.before_request
    def check_authentication():
        """
        Global authentication check before each request.
        
        Allows public endpoints without authentication.
        Enforces authentication for all /admin/* routes.
        """
        # Get current endpoint
        endpoint = request.endpoint
        
        # Allow public endpoints
        if is_endpoint_public(endpoint):
            return None
        
        # Check if this is an admin route
        if endpoint and (endpoint.startswith('admin_') or request.path.startswith('/admin')):
            # Validate session
            session_token = request.cookies.get(SESSION_COOKIE_NAME)
            session_info = session_service.validate_session(session_token)
            
            if not session_info:
                # Not authenticated - redirect or return 401
                if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'error': 'Authentication required',
                        'authenticated': False
                    }), 401
                else:
                    # Redirect to login (dashboard will show modal)
                    return redirect(url_for('admin_ui_routes.dashboard'))
            
            # Store session info in g
            g.admin_phone_hash = session_info['phone_hash']
            g.admin_session_info = session_info
        
        return None
