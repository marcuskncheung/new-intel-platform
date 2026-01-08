# blueprints/ai.py
# AI Analysis routes
# Migrated from app1_production.py

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models.email import Email, EmailAnalysisLock
from models.user import AuditLog
from utils.helpers import get_hk_time

# Create blueprint
ai_bp = Blueprint('ai', __name__)

# Try to import AI module
try:
    from intelligence_ai import intelligence_ai
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


@ai_bp.route('/models')
@login_required
def api_ai_list_models():
    """
    🤖 List Available AI Models
    """
    try:
        if not AI_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'AI module not available'
            }), 503
        
        models = intelligence_ai.get_available_models()
        return jsonify({
            'success': True,
            'models': models
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/models/current')
@login_required
def api_ai_get_current_model():
    """
    🤖 Get Current AI Model
    """
    try:
        if not AI_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'AI module not available'
            }), 503
        
        current_model = intelligence_ai.get_current_model()
        return jsonify({
            'success': True,
            'model': current_model
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/models/set', methods=['POST'])
@login_required
def api_ai_set_model():
    """
    🤖 Set AI Model
    """
    try:
        if not AI_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'AI module not available'
            }), 503
        
        data = request.get_json()
        model_name = data.get('model')
        
        if not model_name:
            return jsonify({'success': False, 'error': 'Model name required'}), 400
        
        success = intelligence_ai.set_model(model_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Model set to {model_name}'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to set model'}), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/status')
@login_required
def api_ai_status():
    """
    🤖 Get AI Module Status
    """
    return jsonify({
        'success': True,
        'available': AI_AVAILABLE,
        'status': 'operational' if AI_AVAILABLE else 'unavailable'
    })


@ai_bp.route('/comprehensive-analyze/<int:email_id>', methods=['POST'])
@login_required
def ai_comprehensive_analyze_email(email_id):
    """
    🧠 Run Comprehensive AI Analysis on Email
    """
    try:
        if not AI_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'AI module not available'
            }), 503
        
        email = Email.query.get_or_404(email_id)
        
        # Check for analysis lock
        lock = EmailAnalysisLock.query.filter_by(email_id=email_id).first()
        if lock and lock.is_locked:
            return jsonify({
                'success': False,
                'error': 'Analysis already in progress',
                'locked_by': lock.locked_by
            }), 409
        
        # Create or update lock
        if not lock:
            lock = EmailAnalysisLock(
                email_id=email_id,
                locked_by=current_user.username,
                locked_at=get_hk_time(),
                is_locked=True
            )
            db.session.add(lock)
        else:
            lock.locked_by = current_user.username
            lock.locked_at = get_hk_time()
            lock.is_locked = True
        
        db.session.commit()
        
        try:
            # Run AI analysis
            content = f"Subject: {email.subject}\n\n{email.body}"
            result = intelligence_ai.analyze_email(content)
            
            # Update email with results
            if result.get('success'):
                email.ai_analysis_summary = result.get('summary')
                email.alleged_subject = result.get('alleged_subject', email.alleged_subject)
                email.alleged_nature = result.get('alleged_nature', email.alleged_nature)
                db.session.commit()
            
            # Release lock
            lock.is_locked = False
            lock.completed_at = get_hk_time()
            db.session.commit()
            
            # Audit log
            try:
                AuditLog.log_action("ai_analysis", "email", str(email_id),
                    {"status": "success", "analyzed_by": current_user.username}, current_user, "info")
            except Exception:
                pass
            
            return jsonify({
                'success': True,
                'result': result
            })
            
        except Exception as analysis_error:
            # Release lock on error
            lock.is_locked = False
            lock.error = str(analysis_error)
            db.session.commit()
            raise analysis_error
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@ai_bp.route('/email-analysis-status')
@login_required
def ai_email_analysis_status():
    """
    📊 Get Email Analysis Status
    """
    try:
        # Get counts
        total_emails = Email.query.count()
        analyzed = Email.query.filter(Email.ai_analysis_summary.isnot(None)).count()
        pending = total_emails - analyzed
        
        # Get currently locked emails
        locked = EmailAnalysisLock.query.filter_by(is_locked=True).all()
        
        return jsonify({
            'success': True,
            'status': {
                'total': total_emails,
                'analyzed': analyzed,
                'pending': pending,
                'in_progress': len(locked)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
