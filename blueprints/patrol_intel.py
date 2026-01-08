# blueprints/patrol_intel.py
# Online Patrol Intelligence routes
# Migrated from app1_production.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from flask_login import login_required, current_user
from extensions import db
from models.patrol import OnlinePatrolEntry, OnlinePatrolPhoto
from models.case import CaseProfile
from models.user import AuditLog
from services.patrol_service import (
    get_all_patrol_entries,
    get_patrol_by_id,
    create_patrol_entry,
    delete_patrol_entry,
    update_patrol_assessment
)
from utils.helpers import get_hk_time
import io

# Create blueprint
patrol_intel_bp = Blueprint('patrol_intel', __name__)


@patrol_intel_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_patrol():
    """
    🔍 Add New Online Patrol Entry
    """
    if request.method == 'POST':
        data = {
            'platform': request.form.get('platform'),
            'url': request.form.get('url'),
            'alleged_subject': request.form.get('alleged_subject'),
            'alleged_nature': request.form.get('alleged_nature'),
            'source_reliability': request.form.get('source_reliability'),
            'content_validity': request.form.get('content_validity'),
            'intel_summary': request.form.get('intel_summary'),
            'details': request.form.get('details')
        }
        
        files = request.files.getlist('photos')
        
        success, message, entry = create_patrol_entry(data, files, current_user)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('patrol_intel.patrol_detail', entry_id=entry.id))
        else:
            flash(message, 'danger')
    
    return render_template('add_online_patrol.html')


@patrol_intel_bp.route('/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def patrol_detail(entry_id):
    """
    🔍 Online Patrol Entry Detail View
    """
    entry = get_patrol_by_id(entry_id)
    
    if request.method == 'POST':
        data = request.form.to_dict()
        success, message, updated_entry = update_patrol_assessment(entry_id, data, current_user)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
        
        return redirect(url_for('patrol_intel.patrol_detail', entry_id=entry_id))
    
    # Get photos
    photos = OnlinePatrolPhoto.query.filter_by(online_patrol_id=entry_id).all()
    
    # Get case profile if linked
    case_profile = None
    if entry.caseprofile_id:
        case_profile = CaseProfile.query.get(entry.caseprofile_id)
    
    return render_template(
        'online_patrol_detail.html',
        entry=entry,
        photos=photos,
        case_profile=case_profile
    )


@patrol_intel_bp.route('/<int:entry_id>/update_assessment', methods=['POST'])
@login_required
def update_assessment(entry_id):
    """
    📝 Update Patrol Assessment (AJAX)
    """
    try:
        data = request.get_json() or request.form.to_dict()
        success, message, entry = update_patrol_assessment(entry_id, data, current_user)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@patrol_intel_bp.route('/<int:entry_id>/delete', methods=['POST'])
@login_required
def delete_patrol(entry_id):
    """
    🗑️ Delete Online Patrol Entry
    """
    success, message = delete_patrol_entry(entry_id, current_user)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('email_intel.int_source'))


@patrol_intel_bp.route('/photo/<int:photo_id>')
@login_required
def view_photo(photo_id):
    """
    🖼️ View Online Patrol Photo
    """
    photo = OnlinePatrolPhoto.query.get_or_404(photo_id)
    
    if photo.data:
        response = make_response(photo.data)
        response.headers['Content-Type'] = photo.content_type or 'image/jpeg'
        response.headers['Content-Disposition'] = f'inline; filename="{photo.filename}"'
        return response
    else:
        flash('Photo data not found', 'warning')
        return redirect(url_for('patrol_intel.patrol_detail', entry_id=photo.online_patrol_id))


@patrol_intel_bp.route('/photo/<int:photo_id>/delete', methods=['POST'])
@login_required
def delete_photo(photo_id):
    """
    🗑️ Delete Online Patrol Photo
    """
    photo = OnlinePatrolPhoto.query.get_or_404(photo_id)
    entry_id = photo.online_patrol_id
    
    try:
        db.session.delete(photo)
        db.session.commit()
        flash('Photo deleted', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting photo: {str(e)}', 'danger')
    
    return redirect(url_for('patrol_intel.patrol_detail', entry_id=entry_id))


@patrol_intel_bp.route('/<int:entry_id>/update_int_reference', methods=['POST'])
@login_required
def update_int_reference(entry_id):
    """
    🔗 Update Patrol INT Reference
    """
    try:
        entry = OnlinePatrolEntry.query.get_or_404(entry_id)
        
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
    
    return redirect(url_for('patrol_intel.patrol_detail', entry_id=entry_id))


# ==================== ADDITIONAL ROUTES ====================

@patrol_intel_bp.route('/update_patrol_details/<int:entry_id>', methods=['POST'])
@login_required
def update_patrol_details(entry_id):
    """
    📝 Update Patrol Entry Details
    """
    try:
        entry = OnlinePatrolEntry.query.get_or_404(entry_id)
        
        # Update fields from form
        entry.title = request.form.get('title', entry.title)
        entry.platform = request.form.get('platform', entry.platform)
        entry.link = request.form.get('link', entry.link)
        entry.account_id = request.form.get('account_id', entry.account_id)
        entry.account_name = request.form.get('account_name', entry.account_name)
        entry.notes = request.form.get('notes', entry.notes)
        
        db.session.commit()
        flash('Details updated successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating details: {str(e)}', 'danger')
    
    return redirect(url_for('patrol_intel.patrol_detail', entry_id=entry_id))


@patrol_intel_bp.route('/delete_patrol_file/<int:file_id>', methods=['POST'])
@login_required
def delete_patrol_file(file_id):
    """
    🗑️ Delete Patrol File/Photo
    """
    from models.patrol import OnlinePatrolFile
    
    try:
        file = OnlinePatrolFile.query.get_or_404(file_id)
        entry_id = file.online_patrol_id
        
        db.session.delete(file)
        db.session.commit()
        flash('File deleted', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting file: {str(e)}', 'danger')
        entry_id = request.form.get('entry_id', 1)
    
    return redirect(url_for('patrol_intel.patrol_detail', entry_id=entry_id))
