# blueprints/received_by_hand_intel.py
# Received By Hand Intelligence routes
# Migrated from app1_production.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from flask_login import login_required, current_user
from extensions import db
from models.received_by_hand import ReceivedByHandEntry, ReceivedByHandDocument
from models.case import CaseProfile
from models.user import AuditLog
from services.received_by_hand_service import (
    get_all_received_by_hand_entries,
    get_received_by_hand_by_id,
    create_received_by_hand_entry,
    delete_received_by_hand_entry,
    update_received_by_hand_assessment
)
from utils.helpers import get_hk_time
import io

# Create blueprint
received_by_hand_intel_bp = Blueprint('received_by_hand_intel', __name__)


@received_by_hand_intel_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_received_by_hand():
    """
    📝 Add New Received By Hand Entry
    """
    if request.method == 'POST':
        data = {
            'received_from': request.form.get('received_from'),
            'received_date': request.form.get('received_date'),
            'alleged_subject': request.form.get('alleged_subject'),
            'alleged_nature': request.form.get('alleged_nature'),
            'source_reliability': request.form.get('source_reliability'),
            'content_validity': request.form.get('content_validity'),
            'intel_summary': request.form.get('intel_summary'),
            'details': request.form.get('details')
        }
        
        documents = request.files.getlist('documents')
        
        success, message, entry = create_received_by_hand_entry(data, documents, current_user)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('received_by_hand_intel.received_by_hand_detail', entry_id=entry.id))
        else:
            flash(message, 'danger')
    
    return render_template('add_received_by_hand.html')


@received_by_hand_intel_bp.route('/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def received_by_hand_detail(entry_id):
    """
    📝 Received By Hand Entry Detail View
    """
    entry = get_received_by_hand_by_id(entry_id)
    
    if request.method == 'POST':
        data = request.form.to_dict()
        success, message, updated_entry = update_received_by_hand_assessment(entry_id, data, current_user)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
        
        return redirect(url_for('received_by_hand_intel.received_by_hand_detail', entry_id=entry_id))
    
    # Get documents
    documents = ReceivedByHandDocument.query.filter_by(received_by_hand_id=entry_id).all()
    
    # Get case profile if linked
    case_profile = None
    if entry.caseprofile_id:
        case_profile = CaseProfile.query.get(entry.caseprofile_id)
    
    return render_template(
        'received_by_hand_detail.html',
        entry=entry,
        documents=documents,
        case_profile=case_profile
    )


@received_by_hand_intel_bp.route('/<int:entry_id>/update_assessment', methods=['POST'])
@login_required
def update_assessment(entry_id):
    """
    📝 Update Received By Hand Assessment (AJAX)
    """
    try:
        data = request.get_json() or request.form.to_dict()
        success, message, entry = update_received_by_hand_assessment(entry_id, data, current_user)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@received_by_hand_intel_bp.route('/<int:entry_id>/delete', methods=['POST'])
@login_required
def delete_received_by_hand(entry_id):
    """
    🗑️ Delete Received By Hand Entry
    """
    success, message = delete_received_by_hand_entry(entry_id, current_user)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('email_intel.int_source'))


@received_by_hand_intel_bp.route('/document/<int:document_id>')
@login_required
def view_document(document_id):
    """
    📄 View/Download Document
    """
    document = ReceivedByHandDocument.query.get_or_404(document_id)
    
    if document.data:
        response = make_response(document.data)
        response.headers['Content-Type'] = document.content_type or 'application/octet-stream'
        response.headers['Content-Disposition'] = f'inline; filename="{document.filename}"'
        return response
    else:
        flash('Document data not found', 'warning')
        return redirect(url_for('received_by_hand_intel.received_by_hand_detail', entry_id=document.received_by_hand_id))


@received_by_hand_intel_bp.route('/document/<int:document_id>/delete', methods=['POST'])
@login_required
def delete_document(document_id):
    """
    🗑️ Delete Document
    """
    document = ReceivedByHandDocument.query.get_or_404(document_id)
    entry_id = document.received_by_hand_id
    
    try:
        db.session.delete(document)
        db.session.commit()
        flash('Document deleted', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting document: {str(e)}', 'danger')
    
    return redirect(url_for('received_by_hand_intel.received_by_hand_detail', entry_id=entry_id))


@received_by_hand_intel_bp.route('/<int:entry_id>/update_int_reference', methods=['POST'])
@login_required
def update_int_reference(entry_id):
    """
    🔗 Update Received By Hand INT Reference
    """
    try:
        entry = ReceivedByHandEntry.query.get_or_404(entry_id)
        
        int_reference = request.form.get('int_reference', '').strip()
        
        if int_reference:
            case = CaseProfile.query.filter_by(int_reference=int_reference).first()
            if not case:
                case = CaseProfile(int_reference=int_reference)
                db.session.add(case)
                db.session.flush()
            
            entry.caseprofile_id = case.id
        else:
            entry.caseprofile_id = None
        
        entry.int_reference_updated_at = get_hk_time()
        entry.int_reference_updated_by = current_user.username
        
        db.session.commit()
        
        flash(f'INT Reference updated to {int_reference}' if int_reference else 'INT Reference cleared', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating INT reference: {str(e)}', 'danger')
    
    return redirect(url_for('received_by_hand_intel.received_by_hand_detail', entry_id=entry_id))
