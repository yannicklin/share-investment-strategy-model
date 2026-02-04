"""
Admin UI Routes - Custom Dashboard for Thread 2

Provides meaningful, purpose-built UI for:
- Dashboard overview (status cards, recent signals, job logs)
- Trading profile management (create/edit/delete strategies)
- Signal history viewer
- Job execution logs
- Manual signal trigger
- Backup management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import date, datetime, timedelta
from app.bot import db
from app.bot.models.database import Signal, ConfigProfile, JobLog
from app.bot.services.signal_engine import generate_daily_signals
import logging

admin_ui_bp = Blueprint('admin_ui', __name__, url_prefix='/admin')
logger = logging.getLogger(__name__)


@admin_ui_bp.route('/')
@admin_ui_bp.route('/dashboard')
def dashboard():
    """Dashboard overview with status cards and recent activity"""
    
    # Today's signal
    today_signal = Signal.query.filter_by(date=date.today()).first()
    
    # Last job execution
    last_job = JobLog.query.order_by(JobLog.created_at.desc()).first()
    
    # Profile count
    profile_count = ConfigProfile.query.count()
    
    # Recent signals (last 7 days)
    seven_days_ago = date.today() - timedelta(days=7)
    recent_signals = Signal.query.filter(
        Signal.date >= seven_days_ago
    ).order_by(Signal.date.desc()).limit(10).all()
    
    # Recent job logs (last 20)
    recent_logs = JobLog.query.order_by(
        JobLog.created_at.desc()
    ).limit(20).all()
    
    return render_template(
        'dashboard.html',
        today_signal=today_signal,
        last_job=last_job,
        profile_count=profile_count,
        recent_signals=recent_signals,
        recent_logs=recent_logs
    )


@admin_ui_bp.route('/config/profiles')
def config_profiles():
    """List all trading strategy profiles"""
    profiles = ConfigProfile.query.order_by(ConfigProfile.created_at.desc()).all()
    return render_template('config_profiles.html', profiles=profiles)


@admin_ui_bp.route('/config/profiles/new', methods=['GET', 'POST'])
def create_profile():
    """Create new trading profile"""
    if request.method == 'POST':
        try:
            # Parse form data
            stocks = request.form.get('stocks', '').split(',')
            stocks = [s.strip().upper() for s in stocks if s.strip()]
            
            profile = ConfigProfile(
                name=request.form['name'],
                stocks=stocks,
                holding_period=int(request.form['holding_period']),
                hurdle_rate=float(request.form['hurdle_rate']) / 100.0,  # Convert % to decimal
                max_position_size=float(request.form['max_position_size']),
                stop_loss=float(request.form.get('stop_loss', 0)) / 100.0 if request.form.get('stop_loss') else None
            )
            
            db.session.add(profile)
            db.session.commit()
            
            flash(f'Profile "{profile.name}" created successfully', 'success')
            return redirect(url_for('admin_ui.config_profiles'))
            
        except Exception as e:
            logger.error(f"Failed to create profile: {str(e)}", exc_info=True)
            flash(f'Error creating profile: {str(e)}', 'error')
    
    return render_template('profile_form.html', profile=None, action='Create')


@admin_ui_bp.route('/config/profiles/<int:id>/edit', methods=['GET', 'POST'])
def edit_profile(id):
    """Edit existing trading profile"""
    profile = ConfigProfile.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Parse form data
            stocks = request.form.get('stocks', '').split(',')
            stocks = [s.strip().upper() for s in stocks if s.strip()]
            
            profile.name = request.form['name']
            profile.stocks = stocks
            profile.holding_period = int(request.form['holding_period'])
            profile.hurdle_rate = float(request.form['hurdle_rate']) / 100.0
            profile.max_position_size = float(request.form['max_position_size'])
            profile.stop_loss = float(request.form.get('stop_loss', 0)) / 100.0 if request.form.get('stop_loss') else None
            profile.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash(f'Profile "{profile.name}" updated successfully', 'success')
            return redirect(url_for('admin_ui.config_profiles'))
            
        except Exception as e:
            logger.error(f"Failed to update profile: {str(e)}", exc_info=True)
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('profile_form.html', profile=profile, action='Edit')


@admin_ui_bp.route('/config/profiles/<int:id>/delete', methods=['POST'])
def delete_profile(id):
    """Delete trading profile"""
    profile = ConfigProfile.query.get_or_404(id)
    name = profile.name
    
    try:
        db.session.delete(profile)
        db.session.commit()
        flash(f'Profile "{name}" deleted successfully', 'success')
    except Exception as e:
        logger.error(f"Failed to delete profile: {str(e)}", exc_info=True)
        flash(f'Error deleting profile: {str(e)}', 'error')
    
    return redirect(url_for('admin_ui.config_profiles'))


@admin_ui_bp.route('/signals')
def signals():
    """View signal history with filters"""
    # TODO: Implement signal viewer with date range filter
    signals = Signal.query.order_by(Signal.date.desc()).limit(100).all()
    return render_template('signals.html', signals=signals)


@admin_ui_bp.route('/logs')
def job_logs():
    """View job execution logs"""
    # TODO: Implement log viewer with status filter
    logs = JobLog.query.order_by(JobLog.created_at.desc()).limit(100).all()
    return render_template('job_logs.html', logs=logs)


@admin_ui_bp.route('/trigger/manual', methods=['POST'])
def manual_trigger():
    """Manually trigger daily signal generation"""
    try:
        logger.info("Manual signal trigger requested from admin UI")
        result = generate_daily_signals()
        
        if result['already_calculated']:
            flash('Signal already calculated today. Check dashboard for results.', 'info')
        else:
            flash(f'Signal generated: {result["signal"]} ({result["confidence"]:.0%} confidence)', 'success')
            
        if result['already_sent']:
            flash('Notifications already sent today.', 'info')
        else:
            flash('Notifications sent successfully.', 'success')
            
    except Exception as e:
        logger.error(f"Manual trigger failed: {str(e)}", exc_info=True)
        flash(f'Error triggering signals: {str(e)}', 'error')
    
    return redirect(url_for('admin_ui.dashboard'))
