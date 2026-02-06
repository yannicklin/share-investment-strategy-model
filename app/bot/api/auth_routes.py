"""
AI Trading Bot System - Authentication API Routes

REST API endpoints for admin authentication flow:
1. Request verification code
2. Verify code and create session
3. Check authentication status
4. Logout

Author: Yannick
Copyright (c) 2026 Yannick
"""

from flask import Blueprint, request, jsonify, make_response
from app.bot.services.verification_service import VerificationService
from app.bot.services.session_service import SessionService
from app.bot.services.auth_utils import hash_phone_number
from app.bot.api.auth_middleware import (
    set_session_cookie,
    clear_session_cookie,
    get_current_admin_phone_hash,
    SESSION_COOKIE_NAME
)
import logging

logger = logging.getLogger(__name__)

# Create blueprint
auth_routes = Blueprint('auth_routes', __name__, url_prefix='/api/admin/auth')

# Service instances
verification_service = VerificationService()
session_service = SessionService()


@auth_routes.route('/request-code', methods=['POST'])
def request_code():
    """
    Request verification code for phone number.
    
    Request Body:
        {
            "phone": "+61412345678"
        }
    
    Response (Success):
        {
            "success": true,
            "message": "Verification code sent via telegram",
            "expires_in": 300,
            "request_id": "abc123..."
        }
    
    Response (Error):
        {
            "success": false,
            "error": "Phone number not authorized"
        }
    """
    try:
        # Parse request
        data = request.get_json()
        
        if not data or 'phone' not in data:
            return jsonify({
                'success': False,
                'error': 'Phone number required'
            }), 400
        
        phone = data['phone']
        
        # Get IP address for rate limiting and logging
        ip_address = request.remote_addr
        if request.headers.get('X-Forwarded-For'):
            ip_address = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        
        # Request verification code
        success, message, request_id = verification_service.request_verification_code(
            phone=phone,
            ip_address=ip_address
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'expires_in': verification_service.code_expiry_minutes * 60,
                'request_id': request_id
            }), 200
        else:
            # Failed - return error
            return jsonify({
                'success': False,
                'error': message
            }), 400
    
    except Exception as e:
        logger.error(f"Error requesting verification code: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error. Please try again.'
        }), 500


@auth_routes.route('/verify-code', methods=['POST'])
def verify_code():
    """
    Verify code and create session.
    
    Request Body:
        {
            "phone": "+61412345678",
            "code": "123456",
            "request_id": "abc123..."  (optional)
        }
    
    Response (Success):
        {
            "success": true,
            "message": "Authentication successful",
            "redirect_url": "/admin/dashboard"
        }
        + Session cookie set in response
    
    Response (Error):
        {
            "success": false,
            "error": "Invalid verification code",
            "attempts_remaining": 2
        }
    """
    try:
        # Parse request
        data = request.get_json()
        
        if not data or 'phone' not in data or 'code' not in data:
            return jsonify({
                'success': False,
                'error': 'Phone number and code required'
            }), 400
        
        phone = data['phone']
        code = data['code']
        request_id = data.get('request_id')
        
        # Get IP address
        ip_address = request.remote_addr
        if request.headers.get('X-Forwarded-For'):
            ip_address = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        
        # Verify code
        success, message = verification_service.verify_code(
            phone=phone,
            code=code,
            request_id=request_id,
            ip_address=ip_address
        )
        
        if success:
            # Code verified - create session
            phone_hash = hash_phone_number(phone)
            user_agent = request.headers.get('User-Agent', '')
            
            session_token = session_service.create_session(
                phone_hash=phone_hash,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Get redirect URL from query params or default to dashboard
            redirect_url = request.args.get('next', '/admin/dashboard')
            
            # Create response with session cookie
            response = make_response(jsonify({
                'success': True,
                'message': 'Authentication successful',
                'redirect_url': redirect_url
            }), 200)
            
            # Set session cookie
            response = set_session_cookie(
                response,
                session_token,
                max_age_hours=session_service.session_expiry_hours
            )
            
            return response
        else:
            # Verification failed
            return jsonify({
                'success': False,
                'error': message
            }), 401
    
    except Exception as e:
        logger.error(f"Error verifying code: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error. Please try again.'
        }), 500


@auth_routes.route('/logout', methods=['POST'])
def logout():
    """
    Logout and invalidate session.
    
    Response:
        {
            "success": true,
            "message": "Logged out successfully"
        }
        + Session cookie cleared
    """
    try:
        # Get session token from cookie
        session_token = request.cookies.get(SESSION_COOKIE_NAME)
        
        # Get IP address
        ip_address = request.remote_addr
        if request.headers.get('X-Forwarded-For'):
            ip_address = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        
        # Invalidate session
        if session_token:
            session_service.invalidate_session(session_token, ip_address)
        
        # Create response
        response = make_response(jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200)
        
        # Clear session cookie
        response = clear_session_cookie(response)
        
        return response
    
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_routes.route('/status', methods=['GET'])
def status():
    """
    Check authentication status.
    
    Response (Authenticated):
        {
            "authenticated": true,
            "expires_at": "2026-02-07T10:00:00Z"
        }
    
    Response (Not Authenticated):
        {
            "authenticated": false
        }
    """
    try:
        # Get session token from cookie
        session_token = request.cookies.get(SESSION_COOKIE_NAME)
        
        # Validate session
        session_info = session_service.validate_session(session_token, extend_on_activity=False)
        
        if session_info:
            return jsonify({
                'authenticated': True,
                'expires_at': session_info['expires_at'].isoformat() + 'Z'
            }), 200
        else:
            return jsonify({
                'authenticated': False
            }), 200
    
    except Exception as e:
        logger.error(f"Error checking auth status: {str(e)}", exc_info=True)
        return jsonify({
            'authenticated': False,
            'error': 'Internal server error'
        }), 500
