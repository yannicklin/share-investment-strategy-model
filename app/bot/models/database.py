"""
Database Models - PostgreSQL Schema

Implements the database schema defined in:
bot_trading_system_requirements.md Section 2.4.1

Tables:
- signals: Daily signal archive (BUY/SELL/HOLD)
- config_profiles: Trading strategy configurations (SENSITIVE)
- api_credentials: Broker/notification API keys (SENSITIVE, encrypted)
- job_logs: Execution history
"""

from app.bot import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY

class Signal(db.Model):
    """Daily signal archive with idempotency support"""
    __tablename__ = 'signals'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    ticker = db.Column(db.String(20), nullable=False)
    signal = db.Column(db.String(10), nullable=False)  # BUY/SELL/HOLD
    confidence = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    job_type = db.Column(db.String(20), nullable=False)  # 'daily' or 'on-demand'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime, nullable=True)  # NULL if notifications not sent
    
    __table_args__ = (
        db.UniqueConstraint('date', 'ticker', 'job_type', name='uq_signal_date_ticker'),
    )
    
    def __repr__(self):
        return f'<Signal {self.date} {self.ticker} {self.signal} ({self.confidence:.2%})>'


class ConfigProfile(db.Model):
    """Trading strategy configurations (SENSITIVE DATA)"""
    __tablename__ = 'config_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    stocks = db.Column(ARRAY(db.String), nullable=False)  # ["BHP.AX", "RIO.AX"]
    holding_period = db.Column(db.Integer, nullable=False)  # Days
    hurdle_rate = db.Column(db.Float, nullable=False)  # Minimum return threshold
    max_position_size = db.Column(db.Float, nullable=False)  # AUD
    stop_loss = db.Column(db.Float, nullable=True)  # Optional
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ConfigProfile {self.name} ({len(self.stocks)} stocks)>'


class ApiCredential(db.Model):
    """Broker/notification API keys (SENSITIVE DATA, encrypted at rest)"""
    __tablename__ = 'api_credentials'
    
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(50), nullable=False)  # 'telnyx', 'sendgrid', 'broker'
    credential_type = db.Column(db.String(20), nullable=False)  # 'api_key', 'token', 'secret'
    encrypted_value = db.Column(db.Text, nullable=False)  # AES-256 encrypted
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ApiCredential {self.service} ({self.credential_type})>'


class JobLog(db.Model):
    """Execution history for monitoring and debugging"""
    __tablename__ = 'job_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_type = db.Column(db.String(50), nullable=False)  # 'daily-signals', 'weekly-retrain'
    status = db.Column(db.String(20), nullable=False)  # 'success', 'failure'
    duration_seconds = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<JobLog {self.job_type} {self.status} @ {self.created_at}>'
