"""
AI Trading Bot System - Admin Whitelist Management API Routes

REST API endpoints for managing authorized admin phone numbers:
- List all admins
- Add new admin
- Update notification preferences
- Activate/deactivate admins
- Delete admins

Author: Yannick
Copyright (c) 2026 Yannick
"""

from flask import Blueprint, request, jsonify
from app.bot import db
from app.bot.shared.models import AdminWhitelist, AuthLog
from app.bot.services.phone_utils import validate_and_normalize, format_phone_display
from app.bot.services.auth_utils import hash_phone_number
from app.bot.api.auth_middleware import auth_required, get_current_admin_phone_hash
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Create blueprint
whitelist_routes = Blueprint('whitelist_routes', __name__, url_prefix='/api/admin/whitelist')


@whitelist_routes.route('', methods=['GET'])
@auth_required
def list_admins():
    """
    Get list of all admins in whitelist.
    
    Response:
        {
            "success": true,
            "admins": [
                {
                    "id": 1,
                    "display_phone": "+61-431-121-011",
                    "notification_preference": "telegram",
                    "is_active": true,
                    "created_at": "2026-02-06T10:00:00Z"
                }
            ]
        }
    """
    try:
        admins = AdminWhitelist.query.order_by(AdminWhitelist.created_at.desc()).all()
        
        admin_list = []
        for admin in admins:
            # Note: We cannot reverse the phone hash, so we'll need to store display version
            admin_list.append({
                'id': admin.id,
                'notification_preference': admin.notification_preference,
                'is_active': admin.is_active,
                'created_at': admin.created_at.isoformat() + 'Z'
            })
        
        return jsonify({
            'success': True,
            'admins': admin_list
        }), 200
    
    except Exception as e:
        logger.error(f"Error listing admins: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@whitelist_routes.route('', methods=['POST'])
@auth_required
def add_admin():
    """
    Add new admin to whitelist.
    
    Request Body:
        {
            "phone": "0431121011" or "+61431121011",
            "notification_preference": "telegram" | "sms" | "both"
        }
    
    Response:
        {
            "success": true,
            "message": "Admin added successfully",
            "admin_id": 123
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'phone' not in data:
            return jsonify({
                'success': False,
                'error': 'Phone number required'
            }), 400
        
        phone = data['phone']
        notification_preference = data.get('notification_preference', 'telegram')
        
        # Validate notification preference
        valid_prefs = ['telegram', 'sms', 'line', 'telegram+line', 'sms+line', 'telegram+sms', 'all']
        if notification_preference not in valid_prefs:
            return jsonify({
                'success': False,
                'error': f'Invalid notification preference. Must be one of: {", ".join(valid_prefs)}'
            }), 400
        
        # Normalize phone number
        try:
            normalized_phone = validate_and_normalize(phone)
            display_phone = format_phone_display(normalized_phone)
        except ValueError as e:
            logger.warning(f"Invalid phone format: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Invalid phone number format: {str(e)}'
            }), 400
        
        # Hash phone number
        phone_hash = hash_phone_number(normalized_phone)
        
        # Check if already exists
        existing = AdminWhitelist.query.filter_by(phone_number_hash=phone_hash).first()
        if existing:
            return jsonify({
                'success': False,
                'error': 'This phone number is already in the whitelist'
            }), 400
        
        # Get current admin for audit
        current_admin_hash = get_current_admin_phone_hash()
        
        # Create new admin
        admin = AdminWhitelist(
            phone_number_hash=phone_hash,
            display_phone=display_phone,
            notification_preference=notification_preference,
            is_active=True,
            created_by=current_admin_hash  # Track who added this admin
        )
        
        db.session.add(admin)
        db.session.flush()  # Get ID before commit
        
        # Log action
        log = AuthLog(
            phone_number_hash=current_admin_hash,
            event_type='admin_added',
            ip_address=request.remote_addr,
            success=True,
            details={
                'new_admin_id': admin.id,
                'notification_preference': notification_preference
            }
        )
        db.session.add(log)
        db.session.commit()
        
        logger.info(f"New admin added: ID={admin.id}")
        
        return jsonify({
            'success': True,
            'message': 'Admin added successfully',
            'admin_id': admin.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding admin: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@whitelist_routes.route('/<int:admin_id>', methods=['PUT'])
@auth_required
def update_admin(admin_id):
    """
    Update admin notification preference.
    
    Request Body:
        {
            "notification_preference": "telegram" | "sms" | "both"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'notification_preference' not in data:
            return jsonify({
                'success': False,
                'error': 'Notification preference required'
            }), 400
        
        notification_preference = data['notification_preference']
        
        # Validate preference
        valid_prefs = ['telegram', 'sms', 'line', 'telegram+line', 'sms+line', 'telegram+sms', 'all']
        if notification_preference not in valid_prefs:
            return jsonify({
                'success': False,
                'error': f'Invalid notification preference. Must be one of: {", ".join(valid_prefs)}'
            }), 400
        
        # Get admin
        admin = AdminWhitelist.query.get(admin_id)
        if not admin:
            return jsonify({
                'success': False,
                'error': 'Admin not found'
            }), 404
        
        # Update preference
        old_preference = admin.notification_preference
        admin.notification_preference = notification_preference
        admin.updated_at = datetime.utcnow()
        
        # Log action
        current_admin_hash = get_current_admin_phone_hash()
        log = AuthLog(
            phone_number_hash=current_admin_hash,
            event_type='admin_updated',
            ip_address=request.remote_addr,
            success=True,
            details={
                'admin_id': admin_id,
                'old_preference': old_preference,
                'new_preference': notification_preference
            }
        )
        db.session.add(log)
        db.session.commit()
        
        logger.info(f"Admin {admin_id} updated: {old_preference} → {notification_preference}")
        
        return jsonify({
            'success': True,
            'message': 'Admin updated successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating admin: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@whitelist_routes.route('/<int:admin_id>/activate', methods=['POST'])
@auth_required
def activate_admin(admin_id):
    """Activate admin access."""
    try:
        admin = AdminWhitelist.query.get(admin_id)
        if not admin:
            return jsonify({'success': False, 'error': 'Admin not found'}), 404
        
        admin.is_active = True
        admin.updated_at = datetime.utcnow()
        
        # Log action
        current_admin_hash = get_current_admin_phone_hash()
        log = AuthLog(
            phone_number_hash=current_admin_hash,
            event_type='admin_activated',
            ip_address=request.remote_addr,
            success=True,
            details={'admin_id': admin_id}
        )
        db.session.add(log)
        db.session.commit()
        
        logger.info(f"Admin {admin_id} activated")
        return jsonify({'success': True, 'message': 'Admin activated'}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error activating admin: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@whitelist_routes.route('/<int:admin_id>/deactivate', methods=['POST'])
@auth_required
def deactivate_admin(admin_id):
    """Deactivate admin access."""
    try:
        admin = AdminWhitelist.query.get(admin_id)
        if not admin:
            return jsonify({'success': False, 'error': 'Admin not found'}), 404
        
        # Prevent self-deactivation
        current_admin_hash = get_current_admin_phone_hash()
        if admin.phone_number_hash == current_admin_hash:
            return jsonify({
                'success': False,
                'error': 'Cannot deactivate your own account'
            }), 400
        
        admin.is_active = False
        admin.updated_at = datetime.utcnow()
        
        # Log action
        log = AuthLog(
            phone_number_hash=current_admin_hash,
            event_type='admin_deactivated',
            ip_address=request.remote_addr,
            success=True,
            details={'admin_id': admin_id}
        )
        db.session.add(log)
        db.session.commit()
        
        logger.info(f"Admin {admin_id} deactivated")
        return jsonify({'success': True, 'message': 'Admin deactivated'}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deactivating admin: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@whitelist_routes.route('/<int:admin_id>', methods=['DELETE'])
@auth_required
def delete_admin(admin_id):
    """
    Delete admin from whitelist.
    
    Note: This is a hard delete. Prefer using deactivate for safety.
    """
    try:
        admin = AdminWhitelist.query.get(admin_id)
        if not admin:
            return jsonify({'success': False, 'error': 'Admin not found'}), 404
        
        # Prevent self-deletion
        current_admin_hash = get_current_admin_phone_hash()
        if admin.phone_number_hash == current_admin_hash:
            return jsonify({
                'success': False,
                'error': 'Cannot delete your own account'
            }), 400
        
        # Log action before deletion
        log = AuthLog(
            phone_number_hash=current_admin_hash,
            event_type='admin_deleted',
            ip_address=request.remote_addr,
            success=True,
            details={'admin_id': admin_id}
        )
        db.session.add(log)
        
        # Delete admin
        db.session.delete(admin)
        db.session.commit()
        
        logger.info(f"Admin {admin_id} deleted")
        return jsonify({'success': True, 'message': 'Admin deleted'}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting admin: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
