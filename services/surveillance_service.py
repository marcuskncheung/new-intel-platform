# services/surveillance_service.py
# Surveillance Intelligence Business Logic

from datetime import datetime
import pytz
from extensions import db

HK_TZ = pytz.timezone('Asia/Hong_Kong')

def get_hk_time():
    return datetime.now(HK_TZ)


def get_all_surveillance_entries():
    """Get all Surveillance entries sorted by ID (newest first)"""
    from models.surveillance import SurveillanceEntry
    return SurveillanceEntry.query.order_by(SurveillanceEntry.id.desc()).all()


def get_surveillance_by_id(entry_id):
    """Get a single surveillance entry by ID"""
    from models.surveillance import SurveillanceEntry
    return SurveillanceEntry.query.get_or_404(entry_id)


def create_surveillance_entry(data, user):
    """Create a new Surveillance entry"""
    from models.surveillance import SurveillanceEntry
    from models.user import AuditLog
    
    try:
        entry = SurveillanceEntry(
            operation_type=data.get('operation_type', 'Surveillance'),
            target_name=data.get('target_name'),
            target_location=data.get('target_location'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            source_reliability=int(data['source_reliability']) if data.get('source_reliability') else None,
            content_validity=int(data['content_validity']) if data.get('content_validity') else None,
            intel_summary=data.get('intel_summary'),
            details=data.get('details'),
            preparer=user.username,
            created_at=get_hk_time()
        )
        
        db.session.add(entry)
        db.session.commit()
        
        try:
            AuditLog.log_action("create_surveillance", "surveillance", str(entry.id),
                {"operation_type": entry.operation_type, "created_by": user.username}, user, "info")
        except Exception:
            pass
        
        return True, "Surveillance entry created", entry
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error creating entry: {str(e)}", None


def delete_surveillance_entry(entry_id, user):
    """Delete a Surveillance entry"""
    from models.surveillance import SurveillanceEntry
    from models.user import AuditLog
    
    try:
        entry = SurveillanceEntry.query.get(entry_id)
        if not entry:
            return False, "Entry not found"
        
        operation_type = entry.operation_type
        db.session.delete(entry)
        db.session.commit()
        
        try:
            AuditLog.log_action("delete_surveillance", "surveillance", str(entry_id),
                {"operation_type": operation_type, "deleted_by": user.username}, user, "warning")
        except Exception:
            pass
        
        return True, "Surveillance entry deleted"
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error deleting entry: {str(e)}"


def update_surveillance_assessment(entry_id, data, user):
    """Update surveillance assessment"""
    from models.surveillance import SurveillanceEntry
    
    try:
        entry = SurveillanceEntry.query.get(entry_id)
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
        if 'operation_type' in data:
            entry.operation_type = data['operation_type']
        if 'target_name' in data:
            entry.target_name = data['target_name']
        if 'target_location' in data:
            entry.target_location = data['target_location']
        
        entry.updated_at = get_hk_time()
        db.session.commit()
        
        return True, "Assessment updated", entry
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error updating: {str(e)}", None
