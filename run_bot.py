"""
AI Trading Bot System - Application Entry Point (Multi-Market Architecture)

This is the Flask application entry point for the bot automation version.
Supports multiple markets (ASX, USA, TWN) with market-specific configurations.

Usage:
    Development:
        python run_bot.py
    
    Production (Koyeb):
        gunicorn -b 0.0.0.0:8080 run_bot:app

Environment Variables Required:
    - DATABASE_URL: PostgreSQL connection string (Supabase Free)
    - CRON_TOKEN: Bearer token for GitHub Actions authentication
    - R2_ACCESS_KEY: Cloudflare R2 access key (backups)
    - R2_SECRET_KEY: Cloudflare R2 secret key (backups)
    - R2_ACCOUNT_ID: Cloudflare R2 account ID
    - TELEGRAM_BOT_TOKEN: Telegram notification token (optional)
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
