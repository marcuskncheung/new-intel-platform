# services/received_by_hand_service.py
# Received By Hand Intelligence Business Logic

from datetime import datetime
import pytz
from extensions import db

HK_TZ = pytz.timezone('Asia/Hong_Kong')

def get_hk_time():
    return datetime.now(HK_TZ)


def get_all_received_by_hand_entries():
    """Get all Received By Hand entries sorted by ID (newest first)"""
    from models.received_by_hand import ReceivedByHandEntry
    return ReceivedByHandEntry.query.order_by(ReceivedByHandEntry.id.desc()).all()


def get_received_by_hand_by_id(entry_id):
    """Get a single received by hand entry by ID"""
    from models.received_by_hand import ReceivedByHandEntry
    return ReceivedByHandEntry.query.get_or_404(entry_id)


def create_received_by_hand_entry(data, documents, user):
    """Create a new Received By Hand entry"""
    from models.received_by_hand import ReceivedByHandEntry, ReceivedByHandDocument
    from models.user import AuditLog
    
    try:
        entry = ReceivedByHandEntry(
            received_from=data.get('received_from'),
            received_date=data.get('received_date'),
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
        
        # Process documents
        if documents:
            for doc in documents:
                if doc and doc.filename:
                    document = ReceivedByHandDocument(
                        received_by_hand_id=entry.id,
                        filename=doc.filename,
                        data=doc.read(),
                        content_type=doc.content_type
                    )
                    db.session.add(document)
        
        db.session.commit()
        
        try:
            AuditLog.log_action("create_received_by_hand", "received_by_hand", str(entry.id),
                {"received_from": entry.received_from, "created_by": user.username}, user, "info")
        except Exception:
            pass
        
        return True, "Received by hand entry created", entry
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error creating entry: {str(e)}", None


def delete_received_by_hand_entry(entry_id, user):
    """Delete a Received By Hand entry"""
    from models.received_by_hand import ReceivedByHandEntry, ReceivedByHandDocument
    from models.user import AuditLog
    
    try:
        entry = ReceivedByHandEntry.query.get(entry_id)
        if not entry:
            return False, "Entry not found"
        
        received_from = entry.received_from
        ReceivedByHandDocument.query.filter_by(received_by_hand_id=entry_id).delete()
        db.session.delete(entry)
        db.session.commit()
        
        try:
            AuditLog.log_action("delete_received_by_hand", "received_by_hand", str(entry_id),
                {"received_from": received_from, "deleted_by": user.username}, user, "warning")
        except Exception:
            pass
        
        return True, "Received by hand entry deleted"
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error deleting entry: {str(e)}"


def update_received_by_hand_assessment(entry_id, data, user):
    """Update received by hand assessment"""
    from models.received_by_hand import ReceivedByHandEntry
    
    try:
        entry = ReceivedByHandEntry.query.get(entry_id)
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
        if 'received_from' in data:
            entry.received_from = data['received_from']
        if 'alleged_subject' in data:
            entry.alleged_subject = data['alleged_subject']
        if 'alleged_nature' in data:
            entry.alleged_nature = data['alleged_nature']
        
        entry.updated_at = get_hk_time()
        db.session.commit()
        
        return True, "Assessment updated", entry
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error updating: {str(e)}", None
