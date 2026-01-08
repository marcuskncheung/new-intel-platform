# blueprints/whatsapp_intel.py
# WhatsApp Intelligence routes
# Migrated from app1_production.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from flask_login import login_required, current_user
from extensions import db
from models.whatsapp import WhatsAppEntry, WhatsAppImage
from models.case import CaseProfile
from models.user import AuditLog
from services.whatsapp_service import (
    get_all_whatsapp_entries,
    get_whatsapp_by_id,
    create_whatsapp_entry,
    delete_whatsapp_entry,
    update_whatsapp_assessment
)
from utils.helpers import get_hk_time
import io

# Create blueprint
whatsapp_intel_bp = Blueprint('whatsapp_intel', __name__)


@whatsapp_intel_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_whatsapp():
    """
    📱 Add New WhatsApp Entry
    """
    if request.method == 'POST':
        data = {
            'alleged_type': request.form.get('alleged_type'),
            'alleged_subject': request.form.get('alleged_subject'),
            'alleged_nature': request.form.get('alleged_nature'),
            'source_reliability': request.form.get('source_reliability'),
            'content_validity': request.form.get('content_validity'),
            'intel_summary': request.form.get('intel_summary'),
            'details': request.form.get('details')
        }
        
        images = request.files.getlist('images')
        
        success, message, entry = create_whatsapp_entry(data, images, current_user)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('whatsapp_intel.whatsapp_detail', entry_id=entry.id))
        else:
            flash(message, 'danger')
    
    return render_template('add_whatsapp.html')


@whatsapp_intel_bp.route('/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def whatsapp_detail(entry_id):
    """
    📱 WhatsApp Entry Detail View
    """
    entry = get_whatsapp_by_id(entry_id)
    
    if request.method == 'POST':
        data = request.form.to_dict()
        success, message, updated_entry = update_whatsapp_assessment(entry_id, data, current_user)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
        
        return redirect(url_for('whatsapp_intel.whatsapp_detail', entry_id=entry_id))
    
    # Get images
    images = WhatsAppImage.query.filter_by(whatsapp_entry_id=entry_id).all()
    
    # Get case profile if linked
    case_profile = None
    if entry.caseprofile_id:
        case_profile = CaseProfile.query.get(entry.caseprofile_id)
    
    return render_template(
        'whatsapp_detail.html',
        entry=entry,
        images=images,
        case_profile=case_profile
    )


@whatsapp_intel_bp.route('/<int:entry_id>/update_assessment', methods=['POST'])
@login_required
def update_assessment(entry_id):
    """
    📝 Update WhatsApp Assessment (AJAX)
    """
    try:
        data = request.get_json() or request.form.to_dict()
        success, message, entry = update_whatsapp_assessment(entry_id, data, current_user)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@whatsapp_intel_bp.route('/<int:entry_id>/delete', methods=['POST'])
@login_required
def delete_whatsapp(entry_id):
    """
    🗑️ Delete WhatsApp Entry
    """
    success, message = delete_whatsapp_entry(entry_id, current_user)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('email_intel.int_source'))


@whatsapp_intel_bp.route('/image/<int:image_id>')
@login_required
def view_image(image_id):
    """
    🖼️ View WhatsApp Image
    """
    image = WhatsAppImage.query.get_or_404(image_id)
    
    if image.data:
        response = make_response(image.data)
        response.headers['Content-Type'] = image.content_type or 'image/jpeg'
        response.headers['Content-Disposition'] = f'inline; filename="{image.filename}"'
        return response
    else:
        flash('Image data not found', 'warning')
        return redirect(url_for('whatsapp_intel.whatsapp_detail', entry_id=image.whatsapp_entry_id))


@whatsapp_intel_bp.route('/image/<int:image_id>/delete', methods=['POST'])
@login_required
def delete_image(image_id):
    """
    🗑️ Delete WhatsApp Image
    """
    image = WhatsAppImage.query.get_or_404(image_id)
    entry_id = image.whatsapp_entry_id
    
    try:
        db.session.delete(image)
        db.session.commit()
        flash('Image deleted', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting image: {str(e)}', 'danger')
    
    return redirect(url_for('whatsapp_intel.whatsapp_detail', entry_id=entry_id))


@whatsapp_intel_bp.route('/<int:entry_id>/update_int_reference', methods=['POST'])
@login_required
def update_int_reference(entry_id):
    """
    🔗 Update WhatsApp INT Reference
    """
    try:
        entry = WhatsAppEntry.query.get_or_404(entry_id)
        
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
    
    return redirect(url_for('whatsapp_intel.whatsapp_detail', entry_id=entry_id))


# ==================== ADDITIONAL ROUTES ====================

@whatsapp_intel_bp.route('/update_whatsapp_details/<int:entry_id>', methods=['POST'])
@login_required
def update_whatsapp_details(entry_id):
    """
    📝 Update WhatsApp Entry Details
    """
    try:
        entry = WhatsAppEntry.query.get_or_404(entry_id)
        
        # Update fields from form
        entry.contact_name = request.form.get('contact_name', entry.contact_name)
        entry.phone_number = request.form.get('phone_number', entry.phone_number)
        entry.message_content = request.form.get('message_content', entry.message_content)
        entry.notes = request.form.get('notes', entry.notes)
        
        db.session.commit()
        flash('Details updated successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating details: {str(e)}', 'danger')
    
    return redirect(url_for('whatsapp_intel.whatsapp_detail', entry_id=entry_id))


@whatsapp_intel_bp.route('/delete_whatsapp_file/<int:file_id>', methods=['POST'])
@login_required
def delete_whatsapp_file(file_id):
    """
    🗑️ Delete WhatsApp Image/File
    """
    from models.whatsapp import WhatsAppImage
    
    try:
        file = WhatsAppImage.query.get_or_404(file_id)
        entry_id = file.whatsapp_id
        
        db.session.delete(file)
        db.session.commit()
        flash('File deleted', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting file: {str(e)}', 'danger')
        entry_id = request.form.get('entry_id', 1)
    
    return redirect(url_for('whatsapp_intel.whatsapp_detail', entry_id=entry_id))
