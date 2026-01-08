# services/poi_service.py
# POI (Person of Interest) / Alleged Subject Business Logic

from datetime import datetime
import pytz
from extensions import db

HK_TZ = pytz.timezone('Asia/Hong_Kong')

def get_hk_time():
    return datetime.now(HK_TZ)


def get_all_alleged_profiles():
    """Get all alleged person profiles"""
    try:
        from models_poi_enhanced import AllegedPersonProfile
        return AllegedPersonProfile.query.order_by(AllegedPersonProfile.poi_id.desc()).all()
    except Exception:
        return []


def get_profile_by_id(profile_id):
    """Get profile by database ID"""
    from models_poi_enhanced import AllegedPersonProfile
    return AllegedPersonProfile.query.get_or_404(profile_id)


def get_profile_by_poi_id(poi_id):
    """Get profile by POI ID (e.g., POI-001)"""
    from models_poi_enhanced import AllegedPersonProfile
    return AllegedPersonProfile.query.filter_by(poi_id=poi_id).first_or_404()


def create_manual_profile(data, user):
    """
    Create a new alleged person profile manually
    Returns: (success, message, profile)
    """
    from models_poi_enhanced import AllegedPersonProfile
    from models.user import AuditLog
    
    try:
        # Generate next POI ID
        last_profile = AllegedPersonProfile.query.order_by(AllegedPersonProfile.id.desc()).first()
        if last_profile and last_profile.poi_id:
            try:
                last_num = int(last_profile.poi_id.replace('POI-', ''))
                next_poi_id = f"POI-{last_num + 1:03d}"
            except ValueError:
                next_poi_id = f"POI-{AllegedPersonProfile.query.count() + 1:03d}"
        else:
            next_poi_id = "POI-001"
        
        profile = AllegedPersonProfile(
            poi_id=next_poi_id,
            english_name=data.get('english_name'),
            chinese_name=data.get('chinese_name'),
            license_number=data.get('license_number'),
            alleged_nature=data.get('alleged_nature'),
            notes=data.get('notes'),
            created_at=get_hk_time(),
            created_by=user.username
        )
        
        db.session.add(profile)
        db.session.commit()
        
        try:
            AuditLog.log_action("create_poi_profile", "poi", next_poi_id,
                {"english_name": profile.english_name, "created_by": user.username}, user, "info")
        except Exception:
            pass
        
        return True, f"Profile {next_poi_id} created successfully", profile
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error creating profile: {str(e)}", None


def update_profile(profile_id, data, user):
    """Update an existing profile"""
    from models_poi_enhanced import AllegedPersonProfile
    from models.user import AuditLog
    
    try:
        profile = AllegedPersonProfile.query.get(profile_id)
        if not profile:
            return False, "Profile not found", None
        
        # Update fields
        if 'english_name' in data:
            profile.english_name = data['english_name']
        if 'chinese_name' in data:
            profile.chinese_name = data['chinese_name']
        if 'license_number' in data:
            profile.license_number = data['license_number']
        if 'alleged_nature' in data:
            profile.alleged_nature = data['alleged_nature']
        if 'notes' in data:
            profile.notes = data['notes']
        if 'status' in data:
            profile.status = data['status']
        
        profile.updated_at = get_hk_time()
        profile.updated_by = user.username
        
        db.session.commit()
        
        try:
            AuditLog.log_action("update_poi_profile", "poi", profile.poi_id,
                {"updated_by": user.username}, user, "info")
        except Exception:
            pass
        
        return True, "Profile updated successfully", profile
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error updating profile: {str(e)}", None


def delete_profile(profile_id, user):
    """Delete a profile"""
    from models_poi_enhanced import AllegedPersonProfile
    from models.user import AuditLog
    
    try:
        profile = AllegedPersonProfile.query.get(profile_id)
        if not profile:
            return False, "Profile not found"
        
        poi_id = profile.poi_id
        db.session.delete(profile)
        db.session.commit()
        
        try:
            AuditLog.log_action("delete_poi_profile", "poi", poi_id,
                {"deleted_by": user.username}, user, "warning")
        except Exception:
            pass
        
        return True, f"Profile {poi_id} deleted successfully"
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error deleting profile: {str(e)}"


def get_linked_intelligence(profile):
    """Get all intelligence entries linked to a profile"""
    from models.email import Email, EmailAllegedSubject
    from models.whatsapp import WhatsAppEntry, WhatsAppAllegedSubject
    from models.patrol import OnlinePatrolEntry, OnlinePatrolAllegedSubject
    from models.surveillance import SurveillanceEntry
    from models.received_by_hand import ReceivedByHandEntry, ReceivedByHandAllegedSubject
    
    linked = {
        'emails': [],
        'whatsapp': [],
        'patrol': [],
        'surveillance': [],
        'received_by_hand': []
    }
    
    try:
        # Get linked emails
        email_links = EmailAllegedSubject.query.filter_by(alleged_profile_id=profile.id).all()
        for link in email_links:
            email = Email.query.get(link.email_id)
            if email:
                linked['emails'].append(email)
        
        # Get linked WhatsApp entries
        wa_links = WhatsAppAllegedSubject.query.filter_by(alleged_profile_id=profile.id).all()
        for link in wa_links:
            entry = WhatsAppEntry.query.get(link.whatsapp_entry_id)
            if entry:
                linked['whatsapp'].append(entry)
        
        # Get linked patrol entries
        patrol_links = OnlinePatrolAllegedSubject.query.filter_by(alleged_profile_id=profile.id).all()
        for link in patrol_links:
            entry = OnlinePatrolEntry.query.get(link.online_patrol_id)
            if entry:
                linked['patrol'].append(entry)
        
        # Get linked received by hand entries
        rbh_links = ReceivedByHandAllegedSubject.query.filter_by(alleged_profile_id=profile.id).all()
        for link in rbh_links:
            entry = ReceivedByHandEntry.query.get(link.received_by_hand_id)
            if entry:
                linked['received_by_hand'].append(entry)
                
    except Exception as e:
        print(f"[POI SERVICE] Error getting linked intel: {e}")
    
    return linked
