"""
Notification Service - Multi-channel delivery

Supports:
- Telegram Bot API (FREE, recommended)
- SendGrid email (optional - 100/day free)
- SMS (optional - costs apply)
"""

import os
import logging
import requests

logger = logging.getLogger(__name__)


def send_telegram(message, parse_mode='Markdown'):
    """
    Send Telegram message via Bot API
    
    Args:
        message: Message text (supports Markdown formatting)
        parse_mode: 'Markdown' or 'HTML'
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        logger.warning("Telegram credentials not configured (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing)")
        logger.info(f"[TELEGRAM-MOCKUP] {message}")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        response = requests.post(url, json={
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode
        }, timeout=10)
        
        if response.status_code == 200:
            logger.info("Telegram message sent successfully")
            return True
        else:
            logger.error(f"Telegram API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Telegram send failed: {str(e)}")
        return False


def send_email(subject, body):
    """
    Send email via SendGrid (optional)
    
    Args:
        subject: Email subject line
        body: Email body text
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
    notification_email = os.environ.get('NOTIFICATION_EMAIL')
    
    if not sendgrid_api_key or not notification_email:
        logger.info(f"[EMAIL-DISABLED] {subject}: {body}")
        return False
    
    try:
        # Optional: Install sendgrid library
        # pip install sendgrid
        import sendgrid
        from sendgrid.helpers.mail import Mail
        
        sg = sendgrid.SendGridAPIClient(api_key=sendgrid_api_key)
        message = Mail(
            from_email='bot@asx-trader.com',
            to_emails=notification_email,
            subject=subject,
            plain_text_content=body
        )
        response = sg.send(message)
        logger.info(f"Email sent: {response.status_code}")
        return True
        
    except ImportError:
        logger.warning("SendGrid library not installed. Install: pip install sendgrid")
        return False
    except Exception as e:
        logger.error(f"Email send failed: {str(e)}")
        return False


def send_sms(message):
    """
    Send SMS via Telnyx (optional - costs $0.02/message)
    
    Args:
        message: SMS message text (max 160 chars)
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    telnyx_api_key = os.environ.get('TELNYX_API_KEY')
    notification_phone = os.environ.get('NOTIFICATION_PHONE')
    
    if not telnyx_api_key or not notification_phone:
        logger.info(f"[SMS-DISABLED] {message}")
        return False
    
    try:
        # Optional: Install telnyx library
        # pip install telnyx
        import telnyx
        
        telnyx.api_key = telnyx_api_key
        telnyx.Message.create(
            from_="ASX-BOT",
            to=notification_phone,
            text=message
        )
        logger.info("SMS sent successfully")
        return True
        
    except ImportError:
        logger.warning("Telnyx library not installed. Install: pip install telnyx")
        return False
    except Exception as e:
        logger.error(f"SMS send failed: {str(e)}")
        return False


def notify_signals(signals):
    """
    Send trading signal notifications via configured channels
    
    Args:
        signals: List of Signal objects
        
    Returns:
        dict: {'telegram': bool, 'email': bool, 'sms': bool}
    """
    if not signals:
        logger.info("No signals to notify")
        return {'telegram': False, 'email': False, 'sms': False}
    
    # Format message
    message = _format_signals_message(signals)
    
    # Send via all configured channels
    results = {
        'telegram': send_telegram(message),
        'email': send_email("ASX Trading Signals", message),
        'sms': send_sms(_format_sms_message(signals))  # Shorter version for SMS
    }
    
    logger.info(f"Notifications sent: {results}")
    return results


def _format_signals_message(signals):
    """Format signals for Telegram/Email (supports Markdown)"""
    lines = ["*ASX Trading Signals*\n"]
    
    for signal in signals:
        emoji = "🟢" if signal.signal == 'BUY' else "🔴" if signal.signal == 'SELL' else "⚪"
        lines.append(
            f"{emoji} *{signal.ticker}*: {signal.signal} "
            f"({signal.confidence:.0%} confidence)"
        )
    
    lines.append(f"\n_Generated: {signals[0].created_at.strftime('%Y-%m-%d %H:%M AEST')}_")
    return "\n".join(lines)


def _format_sms_message(signals):
    """Format signals for SMS (160 char limit)"""
    # Example: "ASX: BUY BHP (82%), SELL CBA (65%)"
    signal_parts = [
        f"{s.signal[:1]} {s.ticker} ({s.confidence:.0%})"
        for s in signals[:3]  # Max 3 signals to fit in SMS
    ]
    return f"ASX: {', '.join(signal_parts)}"

