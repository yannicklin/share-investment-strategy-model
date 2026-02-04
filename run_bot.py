"""
ASX Bot Trading System - Application Entry Point

This is the Flask application entry point for the bot automation version.

Usage:
    Development:
        python run_bot.py
    
    Production (Fly.io):
        gunicorn -b 0.0.0.0:8080 run_bot:app

Environment Variables Required:
    - DATABASE_URL: PostgreSQL connection string (Supabase)
    - CRON_TOKEN: Bearer token for GitHub Actions authentication
    - BACKUP_ENCRYPTION_KEY: AES-256 key for database backups
    - SENDGRID_API_KEY: Email notification API key (optional)
    - TELNYX_API_KEY: SMS notification API key (optional)
"""

from app.bot import create_app, db

# Create Flask app
app = create_app()

# Create database tables (if they don't exist)
with app.app_context():
    db.create_all()
    print("✅ Database tables created/verified")

if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=True
    )
