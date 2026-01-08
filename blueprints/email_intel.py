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


# ==================== ALIAS ROUTES FOR TEMPLATE COMPATIBILITY ====================

@email_intel_bp.route('/list')
@login_required
def list_int_source_email():
    """Alias for int_source for template compatibility"""
    return redirect(url_for('email_intel.int_source'))


@email_intel_bp.route('/master_export')
@login_required
def int_source_master_export():
    """Alias for export.master_export for template compatibility"""
    return redirect(url_for('export.master_export'))


@email_intel_bp.route('/ai_grouped_export/excel')
@login_required
def int_source_ai_grouped_excel_export():
    """Alias for AI grouped export - redirect to export blueprint"""
    return redirect(url_for('export.master_export'))


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


# ==================== LEGACY ROUTES ====================

@email_intel_bp.route('/create', methods=['GET', 'POST'])
@login_required
def legacy_create():
    """
    DEPRECATED: Legacy create route.
    CaseProfile entries are now created automatically.
    """
    flash("CaseProfile entries are created automatically when you add intelligence from Email, WhatsApp, Online Patrol, or Received by Hand sources.", "info")
    return redirect(url_for("email_intel.int_source"))


@email_intel_bp.route('/delete/<int:idx>', methods=['POST'])
@login_required
def legacy_delete(idx):
    """DEPRECATED: Legacy delete route for CaseProfile"""
    cp = CaseProfile.query.get_or_404(idx)
    db.session.delete(cp)
    db.session.commit()
    flash("Profile deleted", "info")
    return redirect(url_for("poi.alleged_subject_list"))


@email_intel_bp.route('/details/<int:idx>', methods=['GET', 'POST'])
@login_required
def legacy_details(idx):
    """
    DEPRECATED: Legacy details page for CaseProfile.
    Redirects to the appropriate source detail page.
    """
    cp = CaseProfile.query.get_or_404(idx)
    
    # Redirect to the appropriate source detail page
    if cp.source_type == 'EMAIL' and cp.email_id:
        return redirect(url_for('email_intel.email_detail', email_id=cp.email_id))
    elif cp.source_type == 'WHATSAPP' and cp.whatsapp_id:
        return redirect(url_for('whatsapp_intel.whatsapp_detail', entry_id=cp.whatsapp_id))
    elif cp.source_type == 'PATROL' and cp.patrol_id:
        return redirect(url_for('patrol_intel.online_patrol_detail', entry_id=cp.patrol_id))
    elif cp.source_type == 'RECEIVED_BY_HAND' and cp.received_by_hand_id:
        return redirect(url_for('received_by_hand_intel.received_by_hand_detail', entry_id=cp.received_by_hand_id))
    else:
        # Fallback: redirect to INT reference detail
        flash(f"Redirecting to INT Reference {cp.int_reference}", "info")
        return redirect(url_for('int_reference.int_reference_detail', int_reference=cp.int_reference))


# ==================== ADDITIONAL ROUTES ====================

@email_intel_bp.route('/embedded_attachment_viewer/<int:att_id>')
@login_required
def embedded_attachment_viewer(att_id):
    """View attachment in embedded viewer"""
    try:
        attachment = Attachment.query.get_or_404(att_id)
        
        # Determine content type
        content_type = attachment.content_type or 'application/octet-stream'
        
        return render_template('embedded_attachment.html',
                             attachment=attachment,
                             content_type=content_type)
    except Exception as e:
        flash(f'Error loading attachment: {str(e)}', 'danger')
        return redirect(url_for('email_intel.int_source'))


@email_intel_bp.route('/debug/attachment/<int:att_id>')
@login_required  
def debug_attachment(att_id):
    """Debug attachment information"""
    try:
        attachment = Attachment.query.get_or_404(att_id)
        
        return jsonify({
            'id': attachment.id,
            'email_id': attachment.email_id,
            'filename': attachment.filename,
            'content_type': attachment.content_type,
            'has_data': attachment.data is not None,
            'data_size': len(attachment.data) if attachment.data else 0,
            'file_path': getattr(attachment, 'file_path', None)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== EXCHANGE & REFRESH ROUTES ====================

@email_intel_bp.route('/process-exchange-inbox')
@login_required
def process_exchange_inbox():
    """
    📥 Process Exchange Inbox - Import emails from Exchange server
    """
    try:
        from fresh_ews_import import process_exchange_inbox as do_import
        
        result = do_import()
        flash(f'Processed {result.get("imported", 0)} emails', 'success')
        
    except ImportError:
        flash('Exchange import module not available', 'warning')
    except Exception as e:
        flash(f'Error processing inbox: {str(e)}', 'danger')
    
    return redirect(url_for('email_intel.int_source'))


@email_intel_bp.route('/api/refresh-emails', methods=['POST'])
@login_required
def refresh_emails():
    """
    🔄 Refresh Emails API - Re-fetch emails from Exchange
    """
    try:
        from fresh_ews_import import process_exchange_inbox as do_import
        
        result = do_import()
        
        return jsonify({
            'success': True,
            'imported': result.get('imported', 0),
            'message': f'Imported {result.get("imported", 0)} new emails'
        })
        
    except ImportError:
        return jsonify({'success': False, 'error': 'Exchange module not available'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@email_intel_bp.route('/assign-case-number/<int:email_id>', methods=['POST'])
@login_required
def assign_case_number(email_id):
    """
    📋 Assign Case Number to Email
    """
    try:
        email = Email.query.get_or_404(email_id)
        case_number = request.form.get('case_number', '').strip()
        
        if case_number:
            email.case_number = case_number
            db.session.commit()
            flash(f'Case number {case_number} assigned', 'success')
        else:
            flash('Please provide a case number', 'warning')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('email_intel.email_detail', email_id=email_id))


# ==================== BULK OPERATIONS ====================

@email_intel_bp.route('/bulk_mark-reviewed', methods=['POST'])
@login_required
def bulk_mark_reviewed():
    """Mark multiple emails as reviewed"""
    try:
        email_ids = request.form.getlist('email_ids[]') or request.json.get('email_ids', [])
        
        for email_id in email_ids:
            email = Email.query.get(email_id)
            if email:
                email.status = 'reviewed'
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'count': len(email_ids)})
        
        flash(f'Marked {len(email_ids)} emails as reviewed', 'success')
        return redirect(url_for('email_intel.int_source'))
        
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('email_intel.int_source'))


@email_intel_bp.route('/bulk_mark-pending', methods=['POST'])
@login_required
def bulk_mark_pending():
    """Mark multiple emails as pending"""
    try:
        email_ids = request.form.getlist('email_ids[]') or request.json.get('email_ids', [])
        
        for email_id in email_ids:
            email = Email.query.get(email_id)
            if email:
                email.status = 'pending'
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'count': len(email_ids)})
        
        flash(f'Marked {len(email_ids)} emails as pending', 'success')
        return redirect(url_for('email_intel.int_source'))
        
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('email_intel.int_source'))


@email_intel_bp.route('/bulk_open-case', methods=['POST'])
@login_required
def bulk_open_case():
    """Open case for multiple emails"""
    try:
        email_ids = request.form.getlist('email_ids[]') or request.json.get('email_ids', [])
        case_number = request.form.get('case_number') or request.json.get('case_number', '')
        
        for email_id in email_ids:
            email = Email.query.get(email_id)
            if email:
                email.case_number = case_number
                email.status = 'case_opened'
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'count': len(email_ids)})
        
        flash(f'Opened case for {len(email_ids)} emails', 'success')
        return redirect(url_for('email_intel.int_source'))
        
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('email_intel.int_source'))


@email_intel_bp.route('/bulk_export', methods=['POST'])
@login_required
def bulk_export():
    """Export multiple emails"""
    try:
        email_ids = request.form.getlist('email_ids[]') or request.json.get('email_ids', [])
        export_format = request.form.get('format', 'csv') or request.json.get('format', 'csv')
        
        emails = Email.query.filter(Email.id.in_(email_ids)).all()
        
        if export_format == 'csv':
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['ID', 'Subject', 'Sender', 'Received', 'Status'])
            
            for email in emails:
                writer.writerow([
                    email.id,
                    email.subject,
                    email.sender,
                    email.received.isoformat() if email.received else '',
                    email.status or ''
                ])
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = 'attachment; filename=emails_export.csv'
            return response
        
        return jsonify({'success': False, 'error': 'Unsupported format'}), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@email_intel_bp.route('/bulk_delete', methods=['POST'])
@login_required
def bulk_delete_emails():
    """Delete multiple emails"""
    try:
        email_ids = request.form.getlist('email_ids[]') or request.json.get('email_ids', [])
        
        deleted = 0
        for email_id in email_ids:
            email = Email.query.get(email_id)
            if email:
                db.session.delete(email)
                deleted += 1
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'deleted': deleted})
        
        flash(f'Deleted {deleted} emails', 'success')
        return redirect(url_for('email_intel.int_source'))
        
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('email_intel.int_source'))
