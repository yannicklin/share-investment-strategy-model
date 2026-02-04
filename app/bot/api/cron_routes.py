"""
Cron Routes - GitHub Actions triggered endpoints

Implements the Flask API endpoints documented in:
infrastructure_comparison.md Section 6.3

Endpoints:
- POST /cron/daily-signals: Dual-trigger daily signal generation
- POST /cron/weekly-retrain: Weekly model retraining + backup

Security: Bearer token authentication (CRON_TOKEN)
"""

from flask import Blueprint, request, jsonify, current_app
from app.bot.services.signal_engine import generate_daily_signals
import logging

cron_bp = Blueprint('cron', __name__, url_prefix='/cron')
logger = logging.getLogger(__name__)


def verify_cron_token():
    """
    Verify CRON_TOKEN from Authorization header
    
    Returns:
        bool: True if token valid, False otherwise
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return False
    
    token = auth_header.split('Bearer ')[1]
    expected_token = current_app.config.get('CRON_TOKEN')
    
    return token == expected_token


@cron_bp.route('/daily-signals', methods=['POST'])
def trigger_daily_signals():
    """
    Daily signal generation endpoint (idempotent)
    
    Called by GitHub Actions:
    - First trigger: 08:00 AEST (22:00 UTC previous day)
    - Second trigger: 10:00 AEST (00:00 UTC)
    
    Returns:
        JSON response with signal data and idempotency status
    """
    if not verify_cron_token():
        logger.warning("Unauthorized cron request - invalid token")
        return jsonify({'error': 'Unauthorized'}), 401
    
    logger.info("Daily signals trigger received")
    
    try:
        result = generate_daily_signals()
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Daily signals failed: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@cron_bp.route('/weekly-retrain', methods=['POST'])
def trigger_weekly_retrain():
    """
    Weekly model retraining endpoint
    
    Called by GitHub Actions:
    - Schedule: Saturday 02:00 AEST (Friday 16:00 UTC)
    
    Returns:
        JSON response with training results
    """
    if not verify_cron_token():
        logger.warning("Unauthorized cron request - invalid token")
        return jsonify({'error': 'Unauthorized'}), 401
    
    logger.info("Weekly retrain trigger received")
    
    # TODO: Implement model retraining logic
    # For now, return mockup response
    return jsonify({
        'status': 'success',
        'message': 'Model retraining not yet implemented',
        'models_trained': 0,
        'duration_minutes': 0
    }), 200
