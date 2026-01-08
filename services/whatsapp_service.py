# services/whatsapp_service.py
# WhatsApp Intelligence Business Logic

from datetime import datetime
import pytz
from extensions import db

HK_TZ = pytz.timezone('Asia/Hong_Kong')

def get_hk_time():
    return datetime.now(HK_TZ)


def get_all_whatsapp_entries():
    """Get all WhatsApp entries sorted by ID (newest first)"""
    from models.whatsapp import WhatsAppEntry
    return WhatsAppEntry.query.order_by(WhatsAppEntry.id.desc()).all()


def get_whatsapp_by_id(entry_id):
    """Get a single WhatsApp entry by ID"""
    from models.whatsapp import WhatsAppEntry
    return WhatsAppEntry.query.get_or_404(entry_id)


def create_whatsapp_entry(data, images, user):
    """
    Create a new WhatsApp entry
    Returns: (success, message, entry)
    """
    from models.whatsapp import WhatsAppEntry, WhatsAppImage
    from models.user import AuditLog
    
    try:
        entry = WhatsAppEntry(
            alleged_type=data.get('alleged_type'),
            alleged_subject=data.get('alleged_subject'),
            alleged_nature=data.get('alleged_nature'),
            source_reliability=data.get('source_reliability', type=int) if data.get('source_reliability') else None,
            content_validity=data.get('content_validity', type=int) if data.get('content_validity') else None,
            intel_summary=data.get('intel_summary'),
            details=data.get('details'),
            preparer=user.username,
            created_at=get_hk_time()
        )
        
        db.session.add(entry)
        db.session.flush()
        
        # Process images
        if images:
            for img_file in images:
                if img_file and img_file.filename:
                    image = WhatsAppImage(
                        whatsapp_entry_id=entry.id,
                        filename=img_file.filename,
                        data=img_file.read(),
                        content_type=img_file.content_type
                    )
                    db.session.add(image)
        
        db.session.commit()
        
        # Audit log
        try:
            AuditLog.log_action(
                action="create_whatsapp",
                resource_type="whatsapp",
                resource_id=str(entry.id),
                details={"alleged_subject": entry.alleged_subject, "created_by": user.username},
                user=user,
                severity="info"
            )
        except Exception:
            pass
        
        return True, "WhatsApp entry created successfully", entry
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error creating entry: {str(e)}", None


def delete_whatsapp_entry(entry_id, user):
    """
    Delete a WhatsApp entry and its images
    Returns: (success, message)
    """
    from models.whatsapp import WhatsAppEntry, WhatsAppImage
    from models.user import AuditLog
    
    try:
        entry = WhatsAppEntry.query.get(entry_id)
        if not entry:
            return False, "Entry not found"
        
        subject = entry.alleged_subject
        
        # Delete images first
        WhatsAppImage.query.filter_by(whatsapp_entry_id=entry_id).delete()
        
        # Delete entry
        db.session.delete(entry)
        db.session.commit()
        
        # Audit log
        try:
            AuditLog.log_action(
                action="delete_whatsapp",
                resource_type="whatsapp",
                resource_id=str(entry_id),
                details={"alleged_subject": subject, "deleted_by": user.username if user else "system"},
                user=user,
                severity="warning"
            )
        except Exception:
            pass
        
        return True, f"WhatsApp entry deleted successfully"
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error deleting entry: {str(e)}"


def update_whatsapp_assessment(entry_id, data, user):
    """
    Update WhatsApp assessment
    Returns: (success, message, entry)
    """
    from models.whatsapp import WhatsAppEntry
    from models.user import AuditLog
    
    try:
        entry = WhatsAppEntry.query.get(entry_id)
        if not entry:
            return False, "Entry not found", None
        
        # Update fields
        if 'source_reliability' in data and data['source_reliability']:
            entry.source_reliability = int(data['source_reliability'])
        if 'content_validity' in data and data['content_validity']:
            entry.content_validity = int(data['content_validity'])
        if 'intel_summary' in data:
            entry.intel_summary = data['intel_summary']
        if 'details' in data:
            entry.details = data['details']
        if 'alleged_type' in data:
            entry.alleged_type = data['alleged_type']
        if 'alleged_subject' in data:
            entry.alleged_subject = data['alleged_subject']
        if 'alleged_nature' in data:
            entry.alleged_nature = data['alleged_nature']
        
        entry.updated_at = get_hk_time()
        
        db.session.commit()
        
        # Audit log
        try:
            AuditLog.log_action(
                action="update_whatsapp_assessment",
                resource_type="whatsapp",
                resource_id=str(entry_id),
                details={"updated_by": user.username if user else "system"},
                user=user,
                severity="info"
            )
        except Exception:
            pass
        
        return True, "Assessment updated", entry
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error updating: {str(e)}", None
