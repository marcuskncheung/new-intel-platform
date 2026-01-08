# blueprints/email_intel.py
# Email Intelligence routes
# Migrated from app1_production.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from flask_login import login_required, current_user
from extensions import db
from models.email import Email, Attachment, EmailAnalysisLock
from models.whatsapp import WhatsAppEntry
from models.patrol import OnlinePatrolEntry
from models.surveillance import SurveillanceEntry
from models.received_by_hand import ReceivedByHandEntry
from models.case import CaseProfile
from models.user import AuditLog
from services.email_service import (
    get_all_emails_sorted,
    get_email_by_id,
    delete_email_by_id,
    update_email_assessment,
    get_analytics_data,
    get_unique_int_references
)
from utils.helpers import get_hk_time
import io
import base64
import mimetypes

# Create blueprint
email_intel_bp = Blueprint('email_intel', __name__)


@email_intel_bp.route('')
@email_intel_bp.route('/')
@login_required
def int_source():
    """
    📧 INT SOURCE - Main Intelligence Inbox View
    Shows all intelligence sources in tabs: Email, WhatsApp, Patrol, Surveillance, Received by Hand
    """
    import os
    print("[DEBUG] Email Intel Blueprint - int_source route")
    
    # Get all emails sorted
    emails = get_all_emails_sorted()
    print(f"[DEBUG] Final emails count: {len(emails)}")
    
    # Get other intelligence sources
    whatsapp_data = WhatsAppEntry.query.order_by(WhatsAppEntry.id.desc()).all()
    online_patrol_data = OnlinePatrolEntry.query.order_by(OnlinePatrolEntry.id.desc()).all()
    surveillance_data = SurveillanceEntry.query.order_by(SurveillanceEntry.id.desc()).all()
    received_by_hand_data = ReceivedByHandEntry.query.order_by(ReceivedByHandEntry.id.desc()).all()
    
    # Build analytics data
    analytics = get_analytics_data(emails, whatsapp_data, surveillance_data)
    
    # Get unique INT references
    unique_int_references = get_unique_int_references()
    
    return render_template(
        "int_source.html",
        op_type_labels=analytics['op_type_labels'],
        op_type_values=analytics['op_type_values'],
        status_labels=analytics['status_labels'],
        status_values=analytics['status_values'],
        wa_type_labels=analytics['wa_type_labels'],
        wa_type_values=analytics['wa_type_values'],
        inbox_status_labels=analytics['inbox_status_labels'],
        inbox_status_values=analytics['inbox_status_values'],
        emails=emails,
        whatsapp_data=whatsapp_data,
        online_patrol_data=online_patrol_data,
        surveillance_data=surveillance_data,
        received_by_hand_data=received_by_hand_data,
        unique_int_references=unique_int_references
    )


@email_intel_bp.route('/email/<int:email_id>', methods=['GET', 'POST'])
@login_required
def email_detail(email_id):
    """
    📧 Email Detail View
    Shows email content, attachments, AI analysis, and allows assessment updates
    """
    email = get_email_by_id(email_id)
    
    if request.method == 'POST':
        # Handle assessment update
        data = {
            'source_reliability': request.form.get('source_reliability', type=int),
            'content_validity': request.form.get('content_validity', type=int),
            'preparer': request.form.get('preparer'),
            'reviewer_name': request.form.get('reviewer_name'),
            'reviewer_comment': request.form.get('reviewer_comment'),
            'reviewer_decision': request.form.get('reviewer_decision'),
            'status': request.form.get('status')
        }
        
        # Clean up None values
        data = {k: v for k, v in data.items() if v is not None}
        
        success, message, updated_email = update_email_assessment(email_id, data, current_user)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('email_intel.email_detail', email_id=email_id))
        else:
            flash(message, 'danger')
    
    # Get attachments
    attachments = Attachment.query.filter_by(email_id=email_id).all()
    
    # Get case profile if linked
    case_profile = None
    if email.caseprofile_id:
        case_profile = CaseProfile.query.get(email.caseprofile_id)
    
    return render_template(
        'email_detail.html',
        email=email,
        attachments=attachments,
        case_profile=case_profile
    )


@email_intel_bp.route('/email/<int:email_id>/update_assessment', methods=['POST'])
@login_required
def update_assessment(email_id):
    """
    📝 Update Email Assessment (AJAX)
    """
    try:
        data = request.get_json() or request.form.to_dict()
        
        success, message, email = update_email_assessment(email_id, data, current_user)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@email_intel_bp.route('/delete/<int:email_id>', methods=['POST'])
@login_required
def delete_email(email_id):
    """
    🗑️ Delete Email
    """
    success, message = delete_email_by_id(email_id, current_user)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('email_intel.int_source'))


@email_intel_bp.route('/download_attachment/<int:att_id>')
@login_required
def download_attachment(att_id):
    """
    📎 Download Email Attachment
    """
    attachment = Attachment.query.get_or_404(att_id)
    
    # Log download
    try:
        AuditLog.log_action(
            action="download_attachment",
            resource_type="attachment",
            resource_id=str(att_id),
            details={"filename": attachment.filename, "email_id": attachment.email_id},
            user=current_user,
            severity="info"
        )
    except Exception:
        pass
    
    if attachment.data:
        return send_file(
            io.BytesIO(attachment.data),
            download_name=attachment.filename,
            as_attachment=True,
            mimetype=attachment.content_type or 'application/octet-stream'
        )
    else:
        flash('Attachment data not found', 'warning')
        return redirect(url_for('email_intel.email_detail', email_id=attachment.email_id))


@email_intel_bp.route('/view_attachment/<int:att_id>')
@login_required
def view_attachment(att_id):
    """
    👁️ View Email Attachment (inline)
    """
    attachment = Attachment.query.get_or_404(att_id)
    
    if attachment.data:
        response = make_response(attachment.data)
        response.headers['Content-Type'] = attachment.content_type or 'application/octet-stream'
        response.headers['Content-Disposition'] = f'inline; filename="{attachment.filename}"'
        return response
    else:
        flash('Attachment data not found', 'warning')
        return redirect(url_for('email_intel.email_detail', email_id=attachment.email_id))


@email_intel_bp.route('/email/<int:email_id>/update_int_reference', methods=['POST'])
@login_required
def update_int_reference(email_id):
    """
    🔗 Update Email INT Reference
    Links email to a CaseProfile (INT number)
    """
    try:
        email = Email.query.get_or_404(email_id)
        
        int_reference = request.form.get('int_reference', '').strip()
        
        if int_reference:
            # Find or create CaseProfile
            case = CaseProfile.query.filter_by(int_reference=int_reference).first()
            if not case:
                case = CaseProfile(int_reference=int_reference)
                db.session.add(case)
                db.session.flush()
            
            email.caseprofile_id = case.id
        else:
            email.caseprofile_id = None
        
        email.int_reference_updated_at = get_hk_time()
        email.int_reference_updated_by = current_user.username
        
        db.session.commit()
        
        flash(f'INT Reference updated to {int_reference}' if int_reference else 'INT Reference cleared', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating INT reference: {str(e)}', 'danger')
    
    return redirect(url_for('email_intel.email_detail', email_id=email_id))


# Additional routes to be migrated from app1_production.py:
# - /assign-case-number/<int:email_id>
# - /int_source/embedded_attachment_viewer/<int:att_id>
# - /process-exchange-inbox
# - /api/refresh-emails
# - bulk operations
