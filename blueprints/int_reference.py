# blueprints/int_reference.py
# INT Reference System routes
# Migrated from app1_production.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.case import CaseProfile
from models.email import Email
from models.whatsapp import WhatsAppEntry
from models.patrol import OnlinePatrolEntry
from models.surveillance import SurveillanceEntry
from models.received_by_hand import ReceivedByHandEntry
from models.user import AuditLog
from utils.helpers import get_hk_time
from sqlalchemy import func

# Create blueprint
int_reference_bp = Blueprint('int_reference', __name__)


@int_reference_bp.route('/next_available')
@login_required
def get_next_available_int():
    """
    🔢 Get Next Available INT Reference Number
    Returns the next INT-XXX number
    """
    try:
        # Get highest INT number
        last_case = CaseProfile.query.filter(
            CaseProfile.int_reference.like('INT-%')
        ).order_by(CaseProfile.int_reference.desc()).first()
        
        if last_case and last_case.int_reference:
            try:
                last_num = int(last_case.int_reference.replace('INT-', ''))
                next_num = last_num + 1
            except ValueError:
                next_num = CaseProfile.query.count() + 1
        else:
            next_num = 1
        
        next_reference = f"INT-{next_num:03d}"
        
        return jsonify({
            'success': True,
            'next_reference': next_reference
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@int_reference_bp.route('/list')
@login_required
def list_int_references():
    """
    📋 List All INT References
    """
    try:
        cases = CaseProfile.query.filter(
            CaseProfile.int_reference.isnot(None)
        ).order_by(CaseProfile.int_reference.desc()).all()
        
        references = []
        for case in cases:
            # Count linked intelligence
            email_count = Email.query.filter_by(caseprofile_id=case.id).count()
            whatsapp_count = WhatsAppEntry.query.filter_by(caseprofile_id=case.id).count()
            patrol_count = OnlinePatrolEntry.query.filter_by(caseprofile_id=case.id).count()
            surveillance_count = SurveillanceEntry.query.filter_by(caseprofile_id=case.id).count()
            rbh_count = ReceivedByHandEntry.query.filter_by(caseprofile_id=case.id).count()
            
            references.append({
                'id': case.id,
                'int_reference': case.int_reference,
                'email_count': email_count,
                'whatsapp_count': whatsapp_count,
                'patrol_count': patrol_count,
                'surveillance_count': surveillance_count,
                'received_by_hand_count': rbh_count,
                'total_count': email_count + whatsapp_count + patrol_count + surveillance_count + rbh_count
            })
        
        return jsonify({
            'success': True,
            'references': references
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@int_reference_bp.route('/search')
@login_required
def search_int_references():
    """
    🔍 Search INT References
    """
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'success': True, 'references': []})
        
        cases = CaseProfile.query.filter(
            CaseProfile.int_reference.ilike(f'%{query}%')
        ).order_by(CaseProfile.int_reference.desc()).limit(20).all()
        
        references = [{'id': c.id, 'int_reference': c.int_reference} for c in cases]
        
        return jsonify({
            'success': True,
            'references': references
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@int_reference_bp.route('/detail/<int_reference>')
@login_required
def int_reference_detail(int_reference):
    """
    📄 INT Reference Detail View
    Shows all intelligence linked to this INT reference
    """
    case = CaseProfile.query.filter_by(int_reference=int_reference).first_or_404()
    
    # Get linked intelligence
    emails = Email.query.filter_by(caseprofile_id=case.id).order_by(Email.received.desc()).all()
    whatsapp = WhatsAppEntry.query.filter_by(caseprofile_id=case.id).all()
    patrol = OnlinePatrolEntry.query.filter_by(caseprofile_id=case.id).all()
    surveillance = SurveillanceEntry.query.filter_by(caseprofile_id=case.id).all()
    received_by_hand = ReceivedByHandEntry.query.filter_by(caseprofile_id=case.id).all()
    
    return render_template(
        'int_reference_detail.html',
        case=case,
        int_reference=int_reference,
        emails=emails,
        whatsapp=whatsapp,
        patrol=patrol,
        surveillance=surveillance,
        received_by_hand=received_by_hand
    )


@int_reference_bp.route('/<int_number>/emails')
@login_required
def get_int_reference_emails(int_number):
    """
    📧 Get Emails for INT Reference
    """
    try:
        case = CaseProfile.query.filter_by(int_reference=int_number).first()
        
        if not case:
            return jsonify({'success': False, 'error': 'INT reference not found'}), 404
        
        emails = Email.query.filter_by(caseprofile_id=case.id).all()
        
        email_list = [{
            'id': e.id,
            'subject': e.subject,
            'sender': e.sender,
            'received': e.received,
            'status': e.status
        } for e in emails]
        
        return jsonify({
            'success': True,
            'int_reference': int_number,
            'emails': email_list
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@int_reference_bp.route('/reorder_all', methods=['POST'])
@login_required
def reorder_all_int_references():
    """
    🔄 Reorder All INT References Chronologically
    """
    try:
        from utils.decorators import admin_required
        
        # Get all case profiles with INT references
        cases = CaseProfile.query.filter(
            CaseProfile.int_reference.isnot(None)
        ).all()
        
        # Sort by creation date
        cases.sort(key=lambda c: c.created_at or get_hk_time())
        
        # Reassign INT numbers
        for i, case in enumerate(cases, 1):
            case.int_reference = f"INT-{i:03d}"
        
        db.session.commit()
        
        flash(f'Reordered {len(cases)} INT references', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error reordering: {str(e)}', 'danger')
    
    return redirect(url_for('int_reference.list_int_references'))


@int_reference_bp.route('/<int_number>/emails')
@login_required
def get_emails_by_int_reference(int_number):
    """
    📧 Get All Emails Linked to a Specific INT Reference
    """
    try:
        int_reference = f"INT-{int_number:03d}" if isinstance(int_number, int) else int_number
        
        # Find emails with this INT reference
        emails = Email.query.filter(
            Email.unified_int_reference == int_reference
        ).order_by(Email.received.desc()).all()
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                'success': True,
                'int_reference': int_reference,
                'count': len(emails),
                'emails': [{
                    'id': e.id,
                    'subject': e.subject,
                    'sender': e.sender,
                    'received': e.received.isoformat() if e.received else None
                } for e in emails]
            })
        
        return render_template('int_reference_emails.html',
                             int_reference=int_reference,
                             emails=emails)
        
    except Exception as e:
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Error loading emails: {str(e)}', 'danger')
        return redirect(url_for('int_reference.list_int_references'))
