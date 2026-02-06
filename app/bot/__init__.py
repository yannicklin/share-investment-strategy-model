"""
AI Trading Bot System - Flask Application Factory (Multi-Market Architecture)

This module implements the bot automation version of the multi-market AI trading system.
Unlike the interactive dashboard (main branch), this bot is designed for:
- Scheduled cron execution (GitHub Actions triggers)
- Multi-market support (ASX, USA, TWN)
- Dual-trigger reliability (08:00 + 10:00 AEST daily)
- Idempotent signal generation (no duplicate signals/notifications)
- Market-isolated database architecture (PostgreSQL via Supabase)
- Automated backups to Cloudflare R2

See: bot_trading_system_requirements.md for detailed specifications
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

# Initialize extensions
db = SQLAlchemy()

def create_app(config_name='production'):
    """
    Flask application factory
    
    Args:
        config_name: 'production', 'development', or 'testing'
        
    Returns:
        Configured Flask app instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'postgresql://user:pass@localhost/asx_bot'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['CRON_TOKEN'] = os.environ.get('CRON_TOKEN')
    app.config['BACKUP_ENCRYPTION_KEY'] = os.environ.get('BACKUP_ENCRYPTION_KEY')
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # PRIVACY: Block all search engines and AI crawlers
    @app.after_request
    def add_privacy_headers(response):
        """
        Add HTTP headers to prevent indexing by:
        - Traditional search engines (Google, Bing, Yahoo, Baidu, Yandex)
        - AI crawlers (ChatGPT, Claude, Perplexity, Google Extended)
        - Archive services (Internet Archive, Wayback Machine)
        
        Context: This is a PRIVATE family-only trading bot.
        No public discovery allowed via search or AI training data.
        """
        response.headers['X-Robots-Tag'] = 'noindex, nofollow, noarchive, nosnippet, noimageindex'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response
    
    # Register blueprints
    from app.bot.api.cron_routes import cron_bp
    from app.bot.api.admin_ui_routes import admin_ui_bp
    from app.bot.api.auth_routes import auth_routes
    from app.bot.api.whitelist_routes import whitelist_routes
    
    app.register_blueprint(cron_bp)
    app.register_blueprint(admin_ui_bp)
    app.register_blueprint(auth_routes)
    app.register_blueprint(whitelist_routes)
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'asx-bot'}, 200
    
    # Robots.txt endpoint (block all crawlers)
    @app.route('/robots.txt')
    def robots():
        return app.send_static_file('robots.txt')
    
    return app
