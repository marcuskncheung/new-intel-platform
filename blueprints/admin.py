# blueprints/admin.py
# Admin routes: dashboard, users, features, logs, database

import os
import sys
import time
import threading
import csv
from io import StringIO
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from blueprints import admin_bp
from extensions import db
from models.user import User, AuditLog, FeatureSettings
from utils.decorators import admin_required
from utils.helpers import get_hk_time

# Try to import psutil for system info
try:
    import psutil
except ImportError:
    psutil = None

PAGINATION_SIZE = 50


@admin_bp.route("")
@admin_bp.route("/dashboard")
@login_required
@admin_required
def admin_dashboard():
    """Admin Dashboard with system stats"""
    # Import models inside function to avoid circular imports
    from models import (
        Email, WhatsAppEntry, OnlinePatrolEntry, SurveillanceEntry,
        ReceivedByHandEntry, CaseProfile, Attachment
    )
    
    # Try to import POI models
    try:
        from models_poi_enhanced import AllegedPersonProfile, POIIntelligenceLink
    except ImportError:
        AllegedPersonProfile = None
        POIIntelligenceLink = None
    
    # Get user stats
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admin_users = User.query.filter_by(role='admin').count()
    
    # Get database statistics
    poi_count = AllegedPersonProfile.query.count() if AllegedPersonProfile else 0
    email_count = Email.query.count()
    whatsapp_count = WhatsAppEntry.query.count()
    rbh_count = ReceivedByHandEntry.query.count()
    patrol_count = OnlinePatrolEntry.query.count()
    surveillance_count = SurveillanceEntry.query.count()
    
    total_intel = email_count + whatsapp_count + rbh_count + patrol_count + surveillance_count
    
    db_stats = {
        'poi_count': poi_count,
        'email_count': email_count,
        'whatsapp_count': whatsapp_count,
        'rbh_count': rbh_count,
        'patrol_count': patrol_count,
        'surveillance_count': surveillance_count,
        'total_intel': total_intel
    }
    
    # Get recent activity
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    # Get system info
    import platform
    system_info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
    }
    
    if psutil:
        try:
            system_info.update({
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent if platform.system() != 'Windows' else psutil.disk_usage('C:\\').percent
            })
        except Exception:
            system_info.update({
                'cpu_percent': 'N/A',
                'memory_percent': 'N/A', 
                'disk_percent': 'N/A'
            })
    else:
        system_info.update({
            'cpu_percent': 'N/A (psutil not installed)',
            'memory_percent': 'N/A (psutil not installed)',
            'disk_percent': 'N/A (psutil not installed)'
        })
    
    AuditLog.log_action('Admin dashboard accessed', None, current_user)
    
    return render_template('admin_dashboard.html', 
                         total_users=total_users,
                         active_users=active_users, 
                         admin_users=admin_users,
                         db_stats=db_stats,
                         recent_logs=recent_logs,
                         system_info=system_info)


# ===== FEATURE VISIBILITY CONTROL ROUTES =====
@admin_bp.route("/features")
@login_required
def admin_features():
    """Admin page to control feature visibility"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.home'))
    
    FeatureSettings.initialize_defaults()
    features = FeatureSettings.query.order_by(FeatureSettings.feature_name).all()
    
    AuditLog.log_action('Admin feature settings accessed', 'feature_settings', None, None, current_user)
    
    return render_template('admin_features.html', features=features)


@admin_bp.route("/features/update", methods=["POST"])
@login_required
def admin_features_update():
    """Update feature visibility settings"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        feature_key = request.form.get('feature_key')
        action = request.form.get('action')
        
        setting = FeatureSettings.query.filter_by(feature_key=feature_key).first()
        if not setting:
            return jsonify({'success': False, 'error': 'Feature not found'}), 404
        
        if action == 'toggle_enabled':
            setting.is_enabled = not setting.is_enabled
        elif action == 'toggle_admin_only':
            setting.admin_only = not setting.admin_only
        else:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400
        
        setting.updated_by = current_user.username
        setting.updated_at = get_hk_time()
        
        db.session.commit()
        
        AuditLog.log_action(
            f'Feature setting changed: {feature_key} - {action}',
            'feature_settings',
            feature_key,
            f'is_enabled={setting.is_enabled}, admin_only={setting.admin_only}',
            current_user
        )
        
        return jsonify({
            'success': True,
            'is_enabled': setting.is_enabled,
            'admin_only': setting.admin_only,
            'message': f'Feature "{setting.feature_name}" updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ===== USER MANAGEMENT =====
@admin_bp.route("/users")
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    AuditLog.log_action('Admin users page accessed', None, current_user)
    return render_template('admin_users.html', users=users)


@admin_bp.route("/users/create", methods=["GET", "POST"])
@login_required
@admin_required
def admin_create_user():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")
        
        if not username or not password:
            flash("Username and password are required", "danger")
        elif User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
        else:
            new_user = User(
                username=username,
                password=generate_password_hash(password),
                role=role
            )
            db.session.add(new_user)
            db.session.commit()
            
            AuditLog.log_action('User created', f'Created user {username} with role {role}', current_user)
            flash(f"User '{username}' created successfully", "success")
            return redirect(url_for("admin.admin_users"))
    
    return render_template('admin_create_user.html')


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        role = request.form.get("role", "user")
        is_active = request.form.get("is_active") == "on"
        new_password = request.form.get("new_password", "").strip()
        
        if not username:
            flash("Username is required", "danger")
        elif username != user.username and User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
        else:
            old_values = f"username: {user.username}, role: {user.role}, active: {user.is_active}"
            
            user.username = username
            user.role = role
            user.is_active = is_active
            
            if new_password:
                user.password = generate_password_hash(new_password)
                AuditLog.log_action('User password changed', f'Password changed for user {username}', current_user)
            
            db.session.commit()
            
            new_values = f"username: {user.username}, role: {user.role}, active: {user.is_active}"
            AuditLog.log_action('User updated', f'User {user_id} updated. Old: {old_values} -> New: {new_values}', current_user)
            
            flash(f"User '{username}' updated successfully", "success")
            return redirect(url_for("admin.admin_users"))
    
    return render_template('admin_edit_user.html', user=user)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def admin_delete_user(user_id):
    if user_id == current_user.id:
        flash("You cannot delete your own account", "danger")
        return redirect(url_for("admin.admin_users"))
    
    user = User.query.get_or_404(user_id)
    username = user.username
    
    db.session.delete(user)
    db.session.commit()
    
    AuditLog.log_action('User deleted', f'Deleted user {username} (ID: {user_id})', current_user)
    flash(f"User '{username}' deleted successfully", "success")
    return redirect(url_for("admin.admin_users"))


# ===== DATABASE OVERVIEW =====
@admin_bp.route("/database")
@login_required
@admin_required
def admin_database():
    """Comprehensive database overview for admins"""
    from models import (
        Email, WhatsAppEntry, OnlinePatrolEntry, SurveillanceEntry,
        ReceivedByHandEntry, CaseProfile, Attachment
    )
    
    try:
        from models_poi_enhanced import AllegedPersonProfile, POIIntelligenceLink
    except ImportError:
        AllegedPersonProfile = None
        POIIntelligenceLink = None
    
    db_tables = []
    
    # POI Profiles
    if AllegedPersonProfile:
        poi_count = AllegedPersonProfile.query.count()
        db_tables.append({
            'name': 'POI Profiles',
            'icon': 'bi-person-badge-fill',
            'color': 'danger',
            'count': poi_count,
            'link': url_for('poi.alleged_subject_list')
        })
    
    # Email Records
    email_count = Email.query.count()
    db_tables.append({
        'name': 'Email Records',
        'icon': 'bi-envelope-fill',
        'color': 'info',
        'count': email_count,
        'link': url_for('email.list_int_source_email')
    })
    
    # WhatsApp Records
    whatsapp_count = WhatsAppEntry.query.count()
    db_tables.append({
        'name': 'WhatsApp Records',
        'icon': 'bi-chat-fill',
        'color': 'success',
        'count': whatsapp_count,
        'link': None  # Will be added when blueprint is created
    })
    
    # Received By Hand
    rbh_count = ReceivedByHandEntry.query.count()
    db_tables.append({
        'name': 'Received By Hand',
        'icon': 'bi-hand-index-fill',
        'color': 'warning',
        'count': rbh_count,
        'link': None
    })
    
    # Online Patrol
    patrol_count = OnlinePatrolEntry.query.count()
    db_tables.append({
        'name': 'Online Patrol',
        'icon': 'bi-globe',
        'color': 'primary',
        'count': patrol_count,
        'link': None
    })
    
    # Surveillance
    surveillance_count = SurveillanceEntry.query.count()
    db_tables.append({
        'name': 'Surveillance',
        'icon': 'bi-camera-video-fill',
        'color': 'secondary',
        'count': surveillance_count,
        'link': None
    })
    
    # Case Profiles
    case_count = CaseProfile.query.count()
    db_tables.append({
        'name': 'Case Profiles',
        'icon': 'bi-folder-fill',
        'color': 'dark',
        'count': case_count,
        'link': None
    })
    
    # Users
    user_count = User.query.count()
    db_tables.append({
        'name': 'Users',
        'icon': 'bi-people-fill',
        'color': 'primary',
        'count': user_count,
        'link': url_for('admin.admin_users')
    })
    
    # Audit Logs
    log_count = AuditLog.query.count()
    db_tables.append({
        'name': 'Audit Logs',
        'icon': 'bi-journal-text',
        'color': 'info',
        'count': log_count,
        'link': url_for('admin.admin_logs')
    })
    
    # POI Intelligence Links
    if POIIntelligenceLink:
        poi_link_count = POIIntelligenceLink.query.count()
        db_tables.append({
            'name': 'POI-Intel Links',
            'icon': 'bi-link-45deg',
            'color': 'warning',
            'count': poi_link_count,
            'link': None
        })
    
    # Attachments
    attachment_count = Attachment.query.count()
    db_tables.append({
        'name': 'Attachments',
        'icon': 'bi-paperclip',
        'color': 'secondary',
        'count': attachment_count,
        'link': None
    })
    
    AuditLog.log_action('Admin database overview accessed', None, current_user)
    
    return render_template('admin_database.html', db_tables=db_tables)


# ===== ACTIVITY LOGS =====
@admin_bp.route("/logs")
@login_required
@admin_required
def admin_logs():
    page = request.args.get('page', 1, type=int)
    
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=PAGINATION_SIZE, error_out=False)
    
    AuditLog.log_action('Admin logs accessed', f'Viewed page {page}', current_user)
    return render_template('admin_logs.html', logs=logs)


@admin_bp.route("/logs/export")
@login_required
@admin_required
def admin_logs_export():
    """Export admin logs to CSV"""
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'ID', 'Timestamp', 'User ID', 'Username', 'Action', 
        'Resource Type', 'Resource ID', 'Details', 'IP Address', 
        'User Agent', 'Session ID', 'Severity'
    ])
    
    for log in logs:
        details = log.get_decrypted_details() if hasattr(log, 'get_decrypted_details') else log.details
        writer.writerow([
            log.id,
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else '',
            log.user_id or '',
            log.username or '',
            log.action or '',
            getattr(log, 'resource_type', '') or '',
            getattr(log, 'resource_id', '') or '',
            details or '',
            log.ip_address or '',
            getattr(log, 'user_agent', '') or '',
            getattr(log, 'session_id', '') or '',
            getattr(log, 'severity', 'info') or ''
        ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=admin_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    AuditLog.log_action(
        action='admin_logs_export',
        resource_type='audit_trail',
        details={
            'exported_records': len(logs),
            'export_format': 'csv'
        },
        user=current_user,
        severity='info'
    )
    
    return response


# ===== SERVER MANAGEMENT =====
@admin_bp.route("/server/restart", methods=["POST"])
@login_required
@admin_required
def admin_restart_server():
    """Restart the Flask server - Admin only"""
    AuditLog.log_action('Server restart initiated', 'Admin initiated server restart', current_user)
    
    def restart():
        time.sleep(1)
        os.execv(sys.executable, ['python'] + sys.argv)
    
    thread = threading.Thread(target=restart)
    thread.daemon = True
    thread.start()
    
    flash("Server restart initiated. Please wait...", "info")
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/server/shutdown", methods=["POST"])
@login_required
@admin_required
def admin_shutdown_server():
    """Shutdown the Flask server - Admin only"""
    AuditLog.log_action('Server shutdown initiated', 'Admin initiated server shutdown', current_user)
    
    def shutdown():
        time.sleep(1)
        os._exit(0)
    
    thread = threading.Thread(target=shutdown)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Server shutting down...'})


# Legacy redirect routes
@admin_bp.route("/restart", methods=["POST"])
@login_required
@admin_required
def admin_restart():
    return redirect(url_for("admin.admin_restart_server"), code=307)


@admin_bp.route("/shutdown", methods=["POST"])
@login_required
@admin_required
def admin_shutdown():
    return redirect(url_for("admin.admin_shutdown_server"), code=307)
