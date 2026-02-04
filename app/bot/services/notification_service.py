"""
Notification Service - Email & SMS delivery

Supports:
- SendGrid email (FREE 100/day)
- Telnyx SMS ($0.02/message)
- Telegram Bot API (FREE alternative)
"""

import os
import logging

logger = logging.getLogger(__name__)


def send_email(subject, body):
    """
    Send email via SendGrid
    
    Args:
        subject: Email subject line
        body: Email body text
    """
    # TODO: Implement SendGrid integration
    # For now, just log
    logger.info(f"[EMAIL] Subject: {subject}")
    logger.info(f"[EMAIL] Body: {body}")
    
    # MOCKUP: Replace with actual SendGrid API call
    # import sendgrid
    # from sendgrid.helpers.mail import Mail
    # 
    # sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    # message = Mail(
    #     from_email='bot@asx-trader.com',
    #     to_emails=os.environ.get('NOTIFICATION_EMAIL'),
    #     subject=subject,
    #     plain_text_content=body
    # )
    # response = sg.send(message)
    # logger.info(f"Email sent: {response.status_code}")


def send_sms(message):
    """
    Send SMS via Telnyx
    
    Args:
        message: SMS message text (max 160 chars)
    """
    # TODO: Implement Telnyx integration
    # For now, just log
    logger.info(f"[SMS] Message: {message}")
    
    # MOCKUP: Replace with actual Telnyx API call
    # import telnyx
    # 
    # telnyx.api_key = os.environ.get('TELNYX_API_KEY')
    # telnyx.Message.create(
    #     from_="ASX-BOT",  # Alphanumeric sender ID
    #     to=os.environ.get('NOTIFICATION_PHONE'),
    #     text=message
    # )
    # logger.info("SMS sent successfully")


def send_telegram(message):
    """
    Send Telegram message (FREE alternative to SMS)
    
    Args:
        message: Message text
    """
    # TODO: Implement Telegram Bot API
    # For now, just log
    logger.info(f"[TELEGRAM] Message: {message}")
    
    # MOCKUP: Replace with actual Telegram API call
    # import requests
    # 
    # bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    # chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    # 
    # url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    # requests.post(url, json={
    #     'chat_id': chat_id,
    #     'text': message,
    #     'parse_mode': 'Markdown'
    # })
    # logger.info("Telegram message sent")
