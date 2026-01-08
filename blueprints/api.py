# blueprints/api.py
# REST API routes
# Migrated from app1_production.py

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.email import Email
from models.whatsapp import WhatsAppEntry
from models.patrol import OnlinePatrolEntry
from models.surveillance import SurveillanceEntry
from models.received_by_hand import ReceivedByHandEntry
from models.case import CaseProfile
from models.user import FeatureSettings
from sqlalchemy import or_
from utils.helpers import get_hk_time

# Create blueprint
api_bp = Blueprint('api', __name__)


@api_bp.route('/global-search')
@login_required
def global_search():
    """
    🔍 Global Search API
    Search across all intelligence sources
    """
    try:
        query = request.args.get('q', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({
                'success': False,
                'error': 'Search query must be at least 2 characters'
            }), 400
        
        results = {
            'emails': [],
            'whatsapp': [],
            'patrol': [],
            'surveillance': [],
            'received_by_hand': [],
            'poi': []
        }
        
        # Search emails
        emails = Email.query.filter(
            or_(
                Email.subject.ilike(f'%{query}%'),
                Email.body.ilike(f'%{query}%'),
                Email.sender.ilike(f'%{query}%'),
                Email.alleged_subject.ilike(f'%{query}%')
            )
        ).limit(20).all()
        
        results['emails'] = [{
            'id': e.id,
            'subject': e.subject,
            'sender': e.sender,
            'received': str(e.received) if e.received else None,
            'type': 'email'
        } for e in emails]
        
        # Search WhatsApp
        whatsapp = WhatsAppEntry.query.filter(
            or_(
                WhatsAppEntry.alleged_subject.ilike(f'%{query}%'),
                WhatsAppEntry.details.ilike(f'%{query}%'),
                WhatsAppEntry.intel_summary.ilike(f'%{query}%')
            )
        ).limit(20).all()
        
        results['whatsapp'] = [{
            'id': w.id,
            'alleged_subject': w.alleged_subject,
            'alleged_type': w.alleged_type,
            'type': 'whatsapp'
        } for w in whatsapp]
        
        # Search Patrol
        patrol = OnlinePatrolEntry.query.filter(
            or_(
                OnlinePatrolEntry.platform.ilike(f'%{query}%'),
                OnlinePatrolEntry.url.ilike(f'%{query}%'),
                OnlinePatrolEntry.alleged_subject.ilike(f'%{query}%'),
                OnlinePatrolEntry.details.ilike(f'%{query}%')
            )
        ).limit(20).all()
        
        results['patrol'] = [{
            'id': p.id,
            'platform': p.platform,
            'alleged_subject': p.alleged_subject,
            'type': 'patrol'
        } for p in patrol]
        
        # Search Surveillance
        surveillance = SurveillanceEntry.query.filter(
            or_(
                SurveillanceEntry.target_name.ilike(f'%{query}%'),
                SurveillanceEntry.target_location.ilike(f'%{query}%'),
                SurveillanceEntry.details.ilike(f'%{query}%')
            )
        ).limit(20).all()
        
        results['surveillance'] = [{
            'id': s.id,
            'target_name': s.target_name,
            'operation_type': s.operation_type,
            'type': 'surveillance'
        } for s in surveillance]
        
        # Search Received By Hand
        rbh = ReceivedByHandEntry.query.filter(
            or_(
                ReceivedByHandEntry.received_from.ilike(f'%{query}%'),
                ReceivedByHandEntry.alleged_subject.ilike(f'%{query}%'),
                ReceivedByHandEntry.details.ilike(f'%{query}%')
            )
        ).limit(20).all()
        
        results['received_by_hand'] = [{
            'id': r.id,
            'received_from': r.received_from,
            'alleged_subject': r.alleged_subject,
            'type': 'received_by_hand'
        } for r in rbh]
        
        # Search POI
        try:
            from models_poi_enhanced import AllegedPersonProfile
            poi = AllegedPersonProfile.query.filter(
                or_(
                    AllegedPersonProfile.english_name.ilike(f'%{query}%'),
                    AllegedPersonProfile.chinese_name.ilike(f'%{query}%'),
                    AllegedPersonProfile.license_number.ilike(f'%{query}%')
                )
            ).limit(20).all()
            
            results['poi'] = [{
                'id': p.id,
                'poi_id': p.poi_id,
                'english_name': p.english_name,
                'chinese_name': p.chinese_name,
                'type': 'poi'
            } for p in poi]
        except Exception:
            pass
        
        # Calculate total
        total = sum(len(v) for v in results.values())
        
        return jsonify({
            'success': True,
            'query': query,
            'total': total,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/debug/db-status')
@login_required
def debug_db_status():
    """
    🔧 Database Status API
    """
    try:
        from sqlalchemy import text
        
        # Check connection
        result = db.session.execute(text("SELECT 1")).scalar()
        
        # Get counts
        counts = {
            'emails': Email.query.count(),
            'whatsapp': WhatsAppEntry.query.count(),
            'patrol': OnlinePatrolEntry.query.count(),
            'surveillance': SurveillanceEntry.query.count(),
            'received_by_hand': ReceivedByHandEntry.query.count(),
            'case_profiles': CaseProfile.query.count()
        }
        
        return jsonify({
            'success': True,
            'connected': result == 1,
            'counts': counts,
            'database_url': str(db.engine.url)[:50] + '...'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/features/check/<feature_key>')
@login_required
def api_feature_check(feature_key):
    """
    🔒 Check Feature Visibility
    """
    try:
        setting = FeatureSettings.query.filter_by(feature_key=feature_key).first()
        
        if not setting:
            return jsonify({'visible': True, 'enabled': True})
        
        visible = setting.is_enabled
        
        if setting.admin_only and visible:
            if hasattr(current_user, 'is_admin'):
                visible = current_user.is_admin() if callable(current_user.is_admin) else current_user.is_admin
            else:
                visible = False
        
        return jsonify({
            'visible': visible,
            'enabled': setting.is_enabled,
            'admin_only': setting.admin_only
        })
        
    except Exception as e:
        return jsonify({'visible': True, 'error': str(e)})


@api_bp.route('/bulk-assign-case', methods=['POST'])
@login_required
def bulk_assign_case():
    """
    📦 Bulk Assign Case Numbers
    """
    try:
        data = request.get_json()
        email_ids = data.get('email_ids', [])
        case_number = data.get('case_number', '').strip()
        
        if not email_ids:
            return jsonify({'success': False, 'error': 'No emails selected'}), 400
        
        if not case_number:
            return jsonify({'success': False, 'error': 'Case number required'}), 400
        
        updated = 0
        for email_id in email_ids:
            email = Email.query.get(email_id)
            if email:
                email.case_number = case_number
                email.case_assigned_by = current_user.username
                email.case_assigned_at = get_hk_time()
                updated += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Assigned {updated} emails to case {case_number}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/clean-duplicates', methods=['POST'])
@login_required
def clean_duplicates():
    """
    🧹 Clean Duplicate Emails
    """
    try:
        from sqlalchemy import func
        
        # Find duplicates by entry_id
        duplicates = db.session.query(
            Email.entry_id,
            func.count(Email.id).label('count')
        ).group_by(Email.entry_id).having(func.count(Email.id) > 1).all()
        
        removed = 0
        for entry_id, count in duplicates:
            # Keep first, delete rest
            emails = Email.query.filter_by(entry_id=entry_id).order_by(Email.id).all()
            for email in emails[1:]:
                db.session.delete(email)
                removed += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Removed {removed} duplicate emails'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
