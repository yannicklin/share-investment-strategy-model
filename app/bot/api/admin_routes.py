"""Admin Routes API"""

from app.bot.api.cron_routes import cron_bp

admin_bp = None  # Placeholder for admin blueprint

__all__ = ['cron_bp', 'admin_bp']
