# blueprints/poi.py
# POI (Person of Interest) / Alleged Subject routes
# Migrated from app1_production.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.user import AuditLog
from services.poi_service import (
    get_all_alleged_profiles,
    get_profile_by_id,
    get_profile_by_poi_id,
    create_manual_profile,
    update_profile,
    delete_profile,
    get_linked_intelligence
)
from utils.helpers import get_hk_time

# Create blueprint
poi_bp = Blueprint('poi', __name__)


@poi_bp.route('/list')
@poi_bp.route('/alleged_subject_list')
@login_required
def alleged_subject_list():
    """
    👥 POI List - All Alleged Person Profiles
    """
    profiles = get_all_alleged_profiles()
    return render_template('alleged_subject_list.html', profiles=profiles)


@poi_bp.route('/profiles')
@login_required
def alleged_subject_profiles():
    """
    👥 Enhanced POI Profiles View
    """
    profiles = get_all_alleged_profiles()
    return render_template('alleged_subject_profiles.html', profiles=profiles)


@poi_bp.route('/profile/<poi_id>')
@login_required
def alleged_subject_profile(poi_id):
    """
    👤 View Single POI Profile by POI ID
    """
    profile = get_profile_by_poi_id(poi_id)
    linked = get_linked_intelligence(profile)
    
    return render_template(
        'alleged_subject_profile.html',
        profile=profile,
        linked_emails=linked['emails'],
        linked_whatsapp=linked['whatsapp'],
        linked_patrol=linked['patrol'],
        linked_surveillance=linked['surveillance'],
        linked_received_by_hand=linked['received_by_hand']
    )


@poi_bp.route('/profile/<poi_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_alleged_subject_profile(poi_id):
    """
    ✏️ Edit POI Profile
    """
    profile = get_profile_by_poi_id(poi_id)
    
    if request.method == 'POST':
        data = request.form.to_dict()
        success, message, updated_profile = update_profile(profile.id, data, current_user)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('poi.alleged_subject_profile', poi_id=poi_id))
        else:
            flash(message, 'danger')
    
    return render_template('edit_alleged_subject_profile.html', profile=profile)


@poi_bp.route('/profile/<int:profile_id>/view')
@login_required
def view_alleged_person_profile(profile_id):
    """
    👤 View POI Profile by Database ID
    """
    profile = get_profile_by_id(profile_id)
    linked = get_linked_intelligence(profile)
    
    return render_template(
        'alleged_person_profile.html',
        profile=profile,
        linked_emails=linked['emails'],
        linked_whatsapp=linked['whatsapp'],
        linked_patrol=linked['patrol'],
        linked_surveillance=linked['surveillance'],
        linked_received_by_hand=linked['received_by_hand']
    )


@poi_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_alleged_person_profile():
    """
    ➕ Create New POI Profile
    """
    if request.method == 'POST':
        data = {
            'english_name': request.form.get('english_name'),
            'chinese_name': request.form.get('chinese_name'),
            'license_number': request.form.get('license_number'),
            'alleged_nature': request.form.get('alleged_nature'),
            'notes': request.form.get('notes')
        }
        
        success, message, profile = create_manual_profile(data, current_user)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('poi.alleged_subject_profile', poi_id=profile.poi_id))
        else:
            flash(message, 'danger')
    
    return render_template('create_alleged_person_profile.html')


@poi_bp.route('/create_manual', methods=['POST'])
@login_required
def create_manual_poi_profile():
    """
    ➕ Create POI Profile (AJAX)
    """
    try:
        data = request.get_json() or request.form.to_dict()
        success, message, profile = create_manual_profile(data, current_user)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'poi_id': profile.poi_id,
                'profile_id': profile.id
            })
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@poi_bp.route('/delete/<int:profile_id>', methods=['POST'])
@login_required
def delete_alleged_person_profile(profile_id):
    """
    🗑️ Delete POI Profile
    """
    success, message = delete_profile(profile_id, current_user)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('poi.alleged_subject_list'))


@poi_bp.route('/profiles/refresh', methods=['POST'])
@login_required
def refresh_profiles():
    """
    🔄 Refresh POI Profiles
    """
    try:
        # Import automation functions
        from alleged_person_automation import auto_resequence_poi_ids
        
        count = auto_resequence_poi_ids()
        flash(f'Refreshed and resequenced {count} profiles', 'success')
        
    except ImportError:
        flash('Automation module not available', 'warning')
    except Exception as e:
        flash(f'Error refreshing profiles: {str(e)}', 'danger')
    
    return redirect(url_for('poi.alleged_subject_profiles'))


@poi_bp.route('/profiles/find_duplicates', methods=['GET', 'POST'])
@login_required
def find_duplicates():
    """
    🔍 Find Duplicate POI Profiles
    """
    duplicates = []
    
    if request.method == 'POST':
        try:
            from models_poi_enhanced import AllegedPersonProfile
            from alleged_person_automation import calculate_name_similarity
            
            profiles = AllegedPersonProfile.query.all()
            
            for i, p1 in enumerate(profiles):
                for p2 in profiles[i+1:]:
                    # Check English name similarity
                    if p1.english_name and p2.english_name:
                        sim = calculate_name_similarity(p1.english_name, p2.english_name)
                        if sim > 0.8:
                            duplicates.append({
                                'profile1': p1,
                                'profile2': p2,
                                'similarity': sim,
                                'match_field': 'english_name'
                            })
                    
                    # Check Chinese name similarity
                    if p1.chinese_name and p2.chinese_name and p1.chinese_name == p2.chinese_name:
                        duplicates.append({
                            'profile1': p1,
                            'profile2': p2,
                            'similarity': 1.0,
                            'match_field': 'chinese_name'
                        })
                        
        except Exception as e:
            flash(f'Error finding duplicates: {str(e)}', 'danger')
    
    return render_template('find_duplicates.html', duplicates=duplicates)


@poi_bp.route('/profiles/merge', methods=['POST'])
@login_required
def merge_profiles():
    """
    🔗 Merge Two POI Profiles
    """
    try:
        primary_id = request.form.get('primary_id', type=int)
        secondary_id = request.form.get('secondary_id', type=int)
        
        if not primary_id or not secondary_id:
            flash('Please select both profiles to merge', 'warning')
            return redirect(url_for('poi.find_duplicates'))
        
        from models_poi_enhanced import AllegedPersonProfile
        
        primary = AllegedPersonProfile.query.get(primary_id)
        secondary = AllegedPersonProfile.query.get(secondary_id)
        
        if not primary or not secondary:
            flash('One or both profiles not found', 'danger')
            return redirect(url_for('poi.find_duplicates'))
        
        # Merge secondary into primary
        # Transfer any missing data from secondary to primary
        if not primary.chinese_name and secondary.chinese_name:
            primary.chinese_name = secondary.chinese_name
        if not primary.license_number and secondary.license_number:
            primary.license_number = secondary.license_number
        if not primary.notes and secondary.notes:
            primary.notes = secondary.notes
        
        # TODO: Transfer linked intelligence entries
        
        # Delete secondary profile
        db.session.delete(secondary)
        db.session.commit()
        
        flash(f'Merged {secondary.poi_id} into {primary.poi_id}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error merging profiles: {str(e)}', 'danger')
    
    return redirect(url_for('poi.alleged_subject_profiles'))
