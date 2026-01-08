# blueprints/surveillance_intel.py
# Surveillance Intelligence routes
# Migrated from app1_production.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.surveillance import SurveillanceEntry
from models.case import CaseProfile
from models.user import AuditLog
from services.surveillance_service import (
    get_all_surveillance_entries,
    get_surveillance_by_id,
    create_surveillance_entry,
    delete_surveillance_entry,
    update_surveillance_assessment
)
from utils.helpers import get_hk_time

# Create blueprint
surveillance_intel_bp = Blueprint('surveillance_intel', __name__)


# ==================== LIST ROUTE ====================

@surveillance_intel_bp.route('/')
@surveillance_intel_bp.route('/list')
@login_required
def surveillance_list():
    """List all surveillance entries - redirects to int_source with filter"""
    return redirect(url_for('email_intel.int_source', source_filter='surveillance'))


@surveillance_intel_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_surveillance():
    """
    🔭 Add New Surveillance Entry
    """
    if request.method == 'POST':
        data = {
            'operation_type': request.form.get('operation_type', 'Surveillance'),
            'target_name': request.form.get('target_name'),
            'target_location': request.form.get('target_location'),
            'start_date': request.form.get('start_date'),
            'end_date': request.form.get('end_date'),
            'source_reliability': request.form.get('source_reliability'),
            'content_validity': request.form.get('content_validity'),
            'intel_summary': request.form.get('intel_summary'),
            'details': request.form.get('details')
        }
        
        success, message, entry = create_surveillance_entry(data, current_user)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('surveillance_intel.surveillance_detail', entry_id=entry.id))
        else:
            flash(message, 'danger')
    
    return render_template('add_surveillance.html')


@surveillance_intel_bp.route('/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def surveillance_detail(entry_id):
    """
    🔭 Surveillance Entry Detail View
    """
    entry = get_surveillance_by_id(entry_id)
    
    if request.method == 'POST':
        data = request.form.to_dict()
        success, message, updated_entry = update_surveillance_assessment(entry_id, data, current_user)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
        
        return redirect(url_for('surveillance_intel.surveillance_detail', entry_id=entry_id))
    
    # Get case profile if linked
    case_profile = None
    if entry.caseprofile_id:
        case_profile = CaseProfile.query.get(entry.caseprofile_id)
    
    return render_template(
        'surveillance_detail.html',
        entry=entry,
        case_profile=case_profile
    )


@surveillance_intel_bp.route('/<int:entry_id>/update_assessment', methods=['POST'])
@login_required
def update_assessment(entry_id):
    """
    📝 Update Surveillance Assessment (AJAX)
    """
    try:
        data = request.get_json() or request.form.to_dict()
        success, message, entry = update_surveillance_assessment(entry_id, data, current_user)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@surveillance_intel_bp.route('/<int:entry_id>/delete', methods=['POST'])
@login_required
def delete_surveillance(entry_id):
    """
    🗑️ Delete Surveillance Entry
    """
    success, message = delete_surveillance_entry(entry_id, current_user)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('email_intel.int_source'))


@surveillance_intel_bp.route('/<int:entry_id>/update_int_reference', methods=['POST'])
@login_required
def update_int_reference(entry_id):
    """
    🔗 Update Surveillance INT Reference
    """
    try:
        entry = SurveillanceEntry.query.get_or_404(entry_id)
        
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
    
    return redirect(url_for('surveillance_intel.surveillance_detail', entry_id=entry_id))
