"""
Idempotent Signal Generator

Implements dual-trigger reliability pattern as documented in:
bot_trading_system_requirements.md Section 2.1.2

Flow:
1. First trigger (08:00 AEST): Calculate signal + send notifications
2. Second trigger (10:00 AEST): Check if already done, skip if yes

Benefits:
- No duplicate signals (database uniqueness constraint)
- No duplicate notifications (sent_at timestamp check)
- 99.9%+ reliability (catches GitHub Actions failures, cold start timeouts)
- Cost: ~$0.00001 when second trigger finds work already done
"""

from datetime import date, datetime
from app.bot import db
from app.bot.models import Signal, JobLog
from app.bot.services.notification_service import send_email, send_sms
import logging

logger = logging.getLogger(__name__)


def generate_daily_signals():
    """
    Idempotent daily signal generation
    
    Returns:
        dict: {
            'already_calculated': bool,
            'already_sent': bool,
            'signal': str,
            'confidence': float
        }
    """
    today = date.today()
    start_time = datetime.utcnow()
    
    try:
        # STEP 1: Check if signal already calculated today
        existing_signal = Signal.query.filter_by(
            date=today,
            job_type='daily'
        ).first()
        
        if not existing_signal:
            logger.info(f"[{today}] First trigger - calculating signal...")
            
            # Calculate signal (30 min job)
            # TODO: Replace with actual AI consensus logic
            signal_data = _run_ai_consensus()
            
            # Store in database
            new_signal = Signal(
                date=today,
                ticker=signal_data['ticker'],
                signal=signal_data['signal'],
                confidence=signal_data['confidence'],
                job_type='daily'
            )
            db.session.add(new_signal)
            db.session.commit()
            
            signal = new_signal
            already_calculated = False
            logger.info(f"[{today}] Signal calculated: {signal.signal} ({signal.confidence:.2%})")
        else:
            # Second trigger: Already exists, exit in 5 seconds
            signal = existing_signal
            already_calculated = True
            logger.info(f"[{today}] Second trigger - signal already calculated, skipping...")
        
        # STEP 2: Check if notification already sent today
        if not signal.sent_at:
            logger.info(f"[{today}] Sending notifications...")
            
            # Send email/SMS (first time only)
            send_email(
                subject=f"ASX Signal: {signal.signal} ({signal.confidence:.0%})",
                body=f"Today's signal for {signal.ticker}: {signal.signal}\nConfidence: {signal.confidence:.2%}"
            )
            send_sms(
                message=f"ASX: {signal.signal} {signal.ticker} {signal.confidence:.0%}"
            )
            
            # Mark as sent
            signal.sent_at = datetime.utcnow()
            db.session.commit()
            
            already_sent = False
            logger.info(f"[{today}] Notifications sent")
        else:
            # Notification already sent (second trigger or retry)
            already_sent = True
            logger.info(f"[{today}] Notifications already sent at {signal.sent_at}, skipping...")
        
        # Log successful execution
        duration = (datetime.utcnow() - start_time).total_seconds()
        log = JobLog(
            job_type='daily-signals',
            status='success',
            duration_seconds=int(duration)
        )
        db.session.add(log)
        db.session.commit()
        
        return {
            'status': 'success',
            'date': str(today),
            'signal': signal.signal,
            'ticker': signal.ticker,
            'confidence': signal.confidence,
            'already_calculated': already_calculated,
            'already_sent': already_sent,
            'trigger_type': 'first' if not already_calculated else 'second_redundancy'
        }
        
    except Exception as e:
        logger.error(f"[{today}] Signal generation failed: {str(e)}", exc_info=True)
        
        # Log failed execution
        duration = (datetime.utcnow() - start_time).total_seconds()
        log = JobLog(
            job_type='daily-signals',
            status='failure',
            duration_seconds=int(duration),
            error_message=str(e)
        )
        db.session.add(log)
        db.session.commit()
        
        raise


def _run_ai_consensus():
    """
    Run multi-model AI consensus (placeholder)
    
    TODO: Integrate with core/model_builder.py from main branch
    
    Returns:
        dict: {
            'ticker': str,
            'signal': str,  # BUY/SELL/HOLD
            'confidence': float  # 0.0 to 1.0
        }
    """
    # MOCKUP: Replace with actual model consensus logic
    return {
        'ticker': 'BHP.AX',
        'signal': 'BUY',
        'confidence': 0.82
    }
