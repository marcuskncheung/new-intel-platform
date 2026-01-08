# blueprints/tools.py
# Utility Tools routes - video downloads, debug tools, chart testing

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, Response, send_file
from flask_login import login_required, current_user
import os
import io
import subprocess
import tempfile
from datetime import datetime
from functools import wraps

tools_bp = Blueprint('tools', __name__)


# ==================== VIDEO DOWNLOAD TOOLS ====================

@tools_bp.route('/api/download-video', methods=['POST'])
@login_required
def download_video():
    """Download video from URL using yt-dlp"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        # Create temp directory for download
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, '%(title)s.%(ext)s')
        
        # Use yt-dlp to download
        result = subprocess.run([
            'yt-dlp',
            '-o', output_path,
            '--format', 'best',
            url
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            return jsonify({'success': False, 'error': result.stderr}), 500
        
        # Find downloaded file
        files = os.listdir(temp_dir)
        if files:
            file_path = os.path.join(temp_dir, files[0])
            return jsonify({
                'success': True,
                'filename': files[0],
                'temp_path': file_path
            })
        
        return jsonify({'success': False, 'error': 'No file downloaded'}), 500
        
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Download timed out'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tools_bp.route('/api/download-video-file/<path:filename>')
@login_required
def download_video_file(filename):
    """Serve downloaded video file"""
    try:
        temp_path = request.args.get('path')
        if temp_path and os.path.exists(temp_path):
            return send_file(
                temp_path,
                as_attachment=True,
                download_name=filename
            )
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== DEBUG TOOLS ====================

@tools_bp.route('/debug/session')
@login_required
def debug_session():
    """Debug session information"""
    from flask import session
    from extensions import db
    
    session_data = dict(session)
    # Remove sensitive data
    if 'csrf_token' in session_data:
        session_data['csrf_token'] = '[REDACTED]'
    
    return jsonify({
        'user': current_user.username if current_user.is_authenticated else None,
        'session_keys': list(session_data.keys()),
        'authenticated': current_user.is_authenticated
    })


@tools_bp.route('/debug/database')
@login_required
def debug_database():
    """Debug database connection status"""
    from extensions import db
    
    try:
        # Test database connection
        result = db.session.execute(db.text('SELECT 1')).fetchone()
        
        return jsonify({
            'status': 'connected',
            'test_query': 'passed'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@tools_bp.route('/debug/config')
@login_required
def debug_config():
    """Debug configuration (non-sensitive)"""
    from flask import current_app
    
    safe_config = {
        'DEBUG': current_app.config.get('DEBUG'),
        'TESTING': current_app.config.get('TESTING'),
        'ENV': current_app.config.get('ENV'),
        'DATABASE_TYPE': 'PostgreSQL' if 'postgresql' in current_app.config.get('SQLALCHEMY_DATABASE_URI', '') else 'SQLite'
    }
    
    return jsonify(safe_config)


# ==================== CHART TESTING ====================

@tools_bp.route('/chart-test')
@login_required
def chart_test():
    """Chart testing page"""
    return render_template('chart_test.html')


@tools_bp.route('/chart-data')
@login_required
def chart_data():
    """Get chart data for testing"""
    from extensions import db
    from models import CaseProfile, AllegedSubjectProfile, EmailIntel
    
    try:
        # Sample analytics data
        data = {
            'cases': {
                'total': CaseProfile.query.count(),
                'active': CaseProfile.query.filter_by(status='active').count(),
                'closed': CaseProfile.query.filter_by(status='closed').count()
            },
            'subjects': {
                'total': AllegedSubjectProfile.query.count()
            },
            'intel': {
                'emails': EmailIntel.query.count()
            }
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== MIGRATION TOOLS ====================

@tools_bp.route('/migrate-images-to-db')
@login_required
def migrate_images_to_db():
    """Migrate images from filesystem to database"""
    from extensions import db
    
    # This is an admin-only operation
    if not current_user.username == 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('main.index'))
    
    migrated = 0
    errors = []
    
    try:
        # Migration logic would go here
        # For now, return status
        return jsonify({
            'status': 'complete',
            'migrated': migrated,
            'errors': errors
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== BULK OPERATIONS ====================

@tools_bp.route('/bulk-update-status', methods=['POST'])
@login_required
def bulk_update_status():
    """Bulk update status for multiple entries"""
    try:
        data = request.get_json()
        entry_type = data.get('type')
        entry_ids = data.get('ids', [])
        new_status = data.get('status')
        
        if not entry_type or not entry_ids or not new_status:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        from extensions import db
        
        # Get appropriate model
        model_map = {
            'email': 'EmailIntel',
            'whatsapp': 'WhatsAppEntry',
            'patrol': 'OnlinePatrolEntry',
            'surveillance': 'SurveillanceEntry'
        }
        
        if entry_type not in model_map:
            return jsonify({'success': False, 'error': 'Invalid entry type'}), 400
        
        # Import model dynamically
        from models import EmailIntel, WhatsAppEntry, OnlinePatrolEntry, SurveillanceEntry
        model_classes = {
            'email': EmailIntel,
            'whatsapp': WhatsAppEntry,
            'patrol': OnlinePatrolEntry,
            'surveillance': SurveillanceEntry
        }
        
        model = model_classes[entry_type]
        updated = 0
        
        for entry_id in entry_ids:
            entry = model.query.get(entry_id)
            if entry and hasattr(entry, 'status'):
                entry.status = new_status
                updated += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'updated': updated
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@tools_bp.route('/bulk-delete', methods=['POST'])
@login_required
def bulk_delete():
    """Bulk delete multiple entries"""
    try:
        data = request.get_json()
        entry_type = data.get('type')
        entry_ids = data.get('ids', [])
        
        if not entry_type or not entry_ids:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        from extensions import db
        from models import EmailIntel, WhatsAppEntry, OnlinePatrolEntry, SurveillanceEntry
        
        model_classes = {
            'email': EmailIntel,
            'whatsapp': WhatsAppEntry,
            'patrol': OnlinePatrolEntry,
            'surveillance': SurveillanceEntry
        }
        
        if entry_type not in model_classes:
            return jsonify({'success': False, 'error': 'Invalid entry type'}), 400
        
        model = model_classes[entry_type]
        deleted = 0
        
        for entry_id in entry_ids:
            entry = model.query.get(entry_id)
            if entry:
                db.session.delete(entry)
                deleted += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'deleted': deleted
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
