"""
AI Trading Bot System - Multi-Market Signal Generator with Idempotent Notifications

Delegates to market-specific services (ASX/USA/TWN) for AI-powered signal generation.
Handles Telegram notification sending with idempotency tracking.

Flow:
1. Market service generates signals using consensus models (if not already done today)
2. Check if notifications already sent for this market/date
3. Send via Telegram Bot API (first time only)

Benefits:
- No duplicate signals (database UNIQUE constraint on market/date/ticker)
- No duplicate notifications (sent_at timestamp check)
- Market isolation enforced via .for_market() query helper

Author: Yannick
Copyright (c) 2026 Yannick
"""

from datetime import date, datetime
from app.bot.shared.models import Signal, JobLog, db
from app.bot.services.notification_service import notify_signals
import logging

logger = logging.getLogger(__name__)


def generate_daily_signals(market="ASX"):
    """
    Generate daily signals for specified market

    Args:
        market: 'ASX', 'USA', or 'TWN'

    Returns:
        dict: {
            'market': str,
            'already_calculated': bool,
            'signals_generated': int,
            'notifications_sent': bool
        }
    """
    today = date.today()
    start_time = datetime.utcnow()

    try:
        # Get market-specific service
        service = _get_market_service(market)

        if service is None:
            return {"error": f"Market {market} not supported", "market": market}

        # STEP 1: Generate signals (market-specific logic)
        result = service.generate_daily_signals()

        # STEP 2: Send notifications for unsent signals
        unsent_signals = Signal.for_market(market).filter_by(date=today, sent_at=None).all()

        notifications_sent = False

        if unsent_signals:
            logger.info(f"{market}: Sending notifications for {len(unsent_signals)} signals")

            # Send via configured channels
            notify_results = notify_signals(unsent_signals)

            # Mark signals as sent if any channel succeeded
            if any(notify_results.values()):
                for signal in unsent_signals:
                    signal.sent_at = datetime.utcnow()
                db.session.commit()
                notifications_sent = True
                logger.info(f"{market}: Notifications sent via {notify_results}")
            else:
                logger.warning(f"{market}: All notification channels failed")
        else:
            logger.info(f"{market}: No new signals to notify")

        # Return consolidated result
        return {
            "market": market,
            "already_calculated": result.get("already_calculated", False),
            "signals_generated": result.get("signals_generated", 0),
            "notifications_sent": notifications_sent,
            "errors": result.get("errors", []),
        }

    except Exception as e:
        logger.error(f"{market}: Signal generation failed: {str(e)}", exc_info=True)

        # Log failure
        job_log = JobLog(
            market=market,
            job_type="daily-signal",
            status="failure",
            error_message=str(e),
            duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
        )
        db.session.add(job_log)
        db.session.commit()

        return {"market": market, "error": str(e)}


def _get_market_service(market):
    """
    Get market-specific signal service

    Args:
        market: 'ASX', 'USA', or 'TWN'

    Returns:
        Market-specific service instance or None
    """
    if market == "ASX":
        from app.bot.markets.asx.signal_service import ASXSignalService

        return ASXSignalService()
    elif market == "USA":
        # Future implementation
        logger.warning("USA market not yet implemented")
        return None
    elif market == "TWN":
        # Future implementation
        logger.warning("TWN market not yet implemented")
        return None
    else:
        logger.error(f"Unknown market: {market}")
        return None


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
    return {"ticker": "BHP.AX", "signal": "BUY", "confidence": 0.82}
