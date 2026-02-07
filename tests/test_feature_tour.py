import pytest
import os
from datetime import date
from unittest.mock import patch, MagicMock

# Force SQLite for testing BEFORE importing app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.bot import create_app, db
from app.bot.shared.models import Signal, ConfigProfile, JobLog


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = create_app("testing")
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SECRET_KEY"] = "test-secret"

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


def test_complete_feature_simulation(client, app):
    """
    SIMULATION: Complete user journey in Market-Isolated Architecture.
    """
    test_phone = "+61400000000"
    market = "ASX"

    # Bypass auth_required decorator
    with (
        patch(
            "app.bot.api.auth_routes.verification_service.verify_code", return_value=(True, "OK")
        ),
        patch(
            "app.bot.api.auth_middleware.session_service.validate_session",
            return_value={"phone_hash": "test", "expires_at": date.today()},
        ),
    ):
        # 1. Login simulation
        client.post("/api/admin/auth/verify-code", json={"phone": test_phone, "code": "123456"})

        # 2. CREATE TRADING PROFILE
        resp = client.post(
            "/admin/config/profiles/new",
            data={
                "name": "Test Strategy",
                "stocks": "BHP.AX, RIO.AX",
                "holding_period": "30",
                "hurdle_rate": "10.0",
                "max_position_size": "1000",
                "stop_loss": "5",
            },
            follow_redirects=True,
        )

        assert resp.status_code == 200

        # 3. VERIFY IN DB (Market Isolation Check)
        with app.app_context():
            profile = ConfigProfile.query.filter_by(market=market, name="Test Strategy").first()
            assert profile is not None
            assert "BHP.AX" in profile.stocks

        # 4. TRIGGER SIGNALS
        with patch("app.bot.api.admin_ui_routes.generate_daily_signals") as mock_gen:
            mock_gen.return_value = {
                "already_calculated": False,
                "already_sent": False,
                "signal": "BUY",
                "confidence": 0.8,
                "trigger_type": "manual",
            }
            resp = client.post("/admin/trigger/manual", follow_redirects=True)
            assert resp.status_code == 200

        # 5. CHECK LOGS
        with app.app_context():
            log = JobLog(market=market, job_type="test-job", status="success")
            db.session.add(log)
            db.session.commit()

            resp = client.get("/admin/logs")
            assert b"success" in resp.data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
