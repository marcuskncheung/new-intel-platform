# services/patrol_service.py
# Online Patrol Intelligence Business Logic

from datetime import datetime
import pytz
from extensions import db

HK_TZ = pytz.timezone('Asia/Hong_Kong')

def get_hk_time():
    return datetime.now(HK_TZ)


def get_all_patrol_entries():
    """Get all Online Patrol entries sorted by ID (newest first)"""
    from models.patrol import OnlinePatrolEntry
    return OnlinePatrolEntry.query.order_by(OnlinePatrolEntry.id.desc()).all()


def get_patrol_by_id(entry_id):
    """Get a single patrol entry by ID"""
    from models.patrol import OnlinePatrolEntry
    return OnlinePatrolEntry.query.get_or_404(entry_id)


def create_patrol_entry(data, files, user):
    """Create a new Online Patrol entry"""
    from models.patrol import OnlinePatrolEntry, OnlinePatrolPhoto
    from models.user import AuditLog
    
    try:
        entry = OnlinePatrolEntry(
            platform=data.get('platform'),
            url=data.get('url'),
            alleged_subject=data.get('alleged_subject'),
            alleged_nature=data.get('alleged_nature'),
            source_reliability=int(data['source_reliability']) if data.get('source_reliability') else None,
            content_validity=int(data['content_validity']) if data.get('content_validity') else None,
            intel_summary=data.get('intel_summary'),
            details=data.get('details'),
            preparer=user.username,
            created_at=get_hk_time()
        )
        
        db.session.add(entry)
        db.session.flush()
        
        # Process photos/files
        if files:
            for f in files:
                if f and f.filename:
                    photo = OnlinePatrolPhoto(
                        online_patrol_id=entry.id,
                        filename=f.filename,
                        data=f.read(),
                        content_type=f.content_type
                    )
                    db.session.add(photo)
        
        db.session.commit()
        
        try:
            AuditLog.log_action("create_patrol", "patrol", str(entry.id),
                {"platform": entry.platform, "created_by": user.username}, user, "info")
        except Exception:
            pass
        
        return True, "Online patrol entry created", entry
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error creating entry: {str(e)}", None


def delete_patrol_entry(entry_id, user):
    """Delete an Online Patrol entry"""
    from models.patrol import OnlinePatrolEntry, OnlinePatrolPhoto
    from models.user import AuditLog
    
    try:
        entry = OnlinePatrolEntry.query.get(entry_id)
        if not entry:
            return False, "Entry not found"
        
        platform = entry.platform
        OnlinePatrolPhoto.query.filter_by(online_patrol_id=entry_id).delete()
        db.session.delete(entry)
        db.session.commit()
        
        try:
            AuditLog.log_action("delete_patrol", "patrol", str(entry_id),
                {"platform": platform, "deleted_by": user.username}, user, "warning")
        except Exception:
            pass
        
        return True, "Online patrol entry deleted"
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error deleting entry: {str(e)}"


def update_patrol_assessment(entry_id, data, user):
    """Update patrol assessment"""
    from models.patrol import OnlinePatrolEntry
    
    try:
        entry = OnlinePatrolEntry.query.get(entry_id)
        if not entry:
            return False, "Entry not found", None
        
        if 'source_reliability' in data and data['source_reliability']:
            entry.source_reliability = int(data['source_reliability'])
        if 'content_validity' in data and data['content_validity']:
            entry.content_validity = int(data['content_validity'])
        if 'intel_summary' in data:
            entry.intel_summary = data['intel_summary']
        if 'details' in data:
            entry.details = data['details']
        if 'platform' in data:
            entry.platform = data['platform']
        if 'url' in data:
            entry.url = data['url']
        
        entry.updated_at = get_hk_time()
        db.session.commit()
        
        return True, "Assessment updated", entry
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error updating: {str(e)}", None
