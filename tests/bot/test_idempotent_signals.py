"""
Test Suite for Idempotent Signal Generation

Tests the dual-trigger reliability pattern:
1. First trigger (08:00): Calculate + send notifications
2. Second trigger (10:00): Skip if already done

Validates:
- No duplicate signals (database constraint)
- No duplicate notifications (sent_at check)
- Correct idempotency flags in response
"""

import pytest
from datetime import date
from app.bot import create_app, db
from app.bot.models import Signal, JobLog
from app.bot.services.signal_engine import generate_daily_signals


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = create_app("testing")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestIdempotentSignalGeneration:
    """Test dual-trigger reliability"""

    def test_first_trigger_creates_signal(self, app):
        """First trigger should calculate signal and send notifications"""
        with app.app_context():
            # Act: Run signal generation (first trigger)
            result = generate_daily_signals()

            # Assert: Signal created in database
            signal = Signal.for_market("ASX").filter_by(date=date.today()).first()
            assert signal is not None
            assert signal.signal in ["BUY", "SELL", "HOLD"]
            assert 0.0 <= signal.confidence <= 1.0
            assert signal.sent_at is not None  # Notification sent

            # Assert: Correct idempotency flags
            assert result["already_calculated"] is False
            assert result["already_sent"] is False
            assert result["trigger_type"] == "first"

            # Assert: Job logged
            log = JobLog.query.filter_by(job_type="daily-signals").first()
            assert log is not None
            assert log.status == "success"

    def test_second_trigger_skips_calculation(self, app):
        """Second trigger should skip if signal already exists"""
        with app.app_context():
            # Arrange: Run first trigger
            first_result = generate_daily_signals()
            first_signal_id = Signal.for_market("ASX").filter_by(date=date.today()).first().id

            # Act: Run second trigger (simulate 10:00 AEST call)
            second_result = generate_daily_signals()

            # Assert: No new signal created (same ID)
            signal = Signal.for_market("ASX").filter_by(date=date.today()).first()
            assert signal.id == first_signal_id

            # Assert: Correct idempotency flags
            assert second_result["already_calculated"] is True
            assert second_result["already_sent"] is True
            assert second_result["trigger_type"] == "second_redundancy"

            # Assert: Only one signal in database
            signal_count = Signal.for_market("ASX").filter_by(date=date.today()).count()
            assert signal_count == 1

    def test_database_prevents_duplicate_signals(self, app):
        """Database constraint should prevent duplicate signals"""
        with app.app_context():
            today = date.today()

            # Arrange: Create first signal
            signal1 = Signal(
                market="ASX",
                date=today,
                ticker="BHP.AX",
                signal="BUY",
                confidence=0.85,
                job_type="daily",
            )
            db.session.add(signal1)
            db.session.commit()

            # Act: Try to create duplicate signal
            signal2 = Signal(
                market="ASX",
                date=today,
                ticker="BHP.AX",  # Same ticker
                signal="SELL",  # Different signal
                confidence=0.90,
                job_type="daily",  # Same job_type
            )
            db.session.add(signal2)

            # Assert: Database raises IntegrityError
            with pytest.raises(Exception):  # SQLAlchemy IntegrityError
                db.session.commit()

    def test_notification_sent_only_once(self, app):
        """Notifications should only be sent on first trigger"""
        with app.app_context():
            # Act: First trigger
            first_result = generate_daily_signals()
            signal_after_first = Signal.for_market("ASX").filter_by(date=date.today()).first()
            first_sent_at = signal_after_first.sent_at

            # Act: Second trigger
            second_result = generate_daily_signals()
            signal_after_second = Signal.for_market("ASX").filter_by(date=date.today()).first()
            second_sent_at = signal_after_second.sent_at

            # Assert: sent_at timestamp unchanged (no duplicate notifications)
            assert first_sent_at == second_sent_at
            assert second_result["already_sent"] is True


class TestCronEndpoints:
    """Test Flask API endpoints"""

    def test_health_check(self, client):
        """Health endpoint should return 200"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json["status"] == "healthy"

    def test_daily_signals_requires_auth(self, client):
        """Cron endpoint should require CRON_TOKEN"""
        response = client.post("/cron/daily-signals")
        assert response.status_code == 401
        assert "Unauthorized" in response.json["error"]

    def test_daily_signals_with_valid_token(self, client, app):
        """Cron endpoint should work with valid token"""
        app.config["CRON_TOKEN"] = "test-token-123"

        response = client.post(
            "/cron/daily-signals", headers={"Authorization": "Bearer test-token-123"}
        )

        assert response.status_code == 200
        assert "signal" in response.json
        assert "already_calculated" in response.json


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
