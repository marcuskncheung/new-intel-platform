# services/email_service.py
# Email Intelligence Business Logic
# Shared between app1_production.py and blueprints/email_intel.py

from datetime import datetime
import pytz
from sqlalchemy import text
from extensions import db

HK_TZ = pytz.timezone('Asia/Hong_Kong')


def get_hk_time():
    return datetime.now(HK_TZ)


def get_all_emails_sorted():
    """
    Get all emails sorted by received date (newest first)
    Returns: List of Email objects
    """
    from models.email import Email
    
    try:
        # Force session refresh
        db.session.expire_all()
        db.session.commit()
        
        # Use direct SQL to get IDs
        with db.engine.connect() as connection:
            email_ids_result = connection.execute(text("SELECT id FROM email ORDER BY id DESC"))
            email_ids = [row[0] for row in email_ids_result]
        
        if email_ids:
            emails = Email.query.filter(Email.id.in_(email_ids)).all()
        else:
            emails = []
        
        # Filter and sort
        emails = [e for e in emails if e is not None]
        
        def safe_sort_key(email):
            if email is None or not email.received:
                return datetime.min
            try:
                if isinstance(email.received, str):
                    return datetime.strptime(email.received, '%Y-%m-%d %H:%M:%S')
                return email.received
            except Exception:
                return datetime.min
        
        emails.sort(key=safe_sort_key, reverse=True)
        return emails
        
    except Exception as e:
        print(f"[EMAIL SERVICE] Error loading emails: {e}")
        return []


def get_email_by_id(email_id):
    """Get a single email by ID"""
    from models.email import Email
    return Email.query.get_or_404(email_id)


def delete_email_by_id(email_id, user):
    """
    Delete an email and its attachments
    Returns: (success, message)
    """
    from models.email import Email, Attachment
    from models.user import AuditLog
    
    try:
        email = Email.query.get(email_id)
        if not email:
            return False, "Email not found"
        
        subject = email.subject
        
        # Delete attachments first
        Attachment.query.filter_by(email_id=email_id).delete()
        
        # Delete the email
        db.session.delete(email)
        db.session.commit()
        
        # Audit log
        try:
            AuditLog.log_action(
                action="delete_email",
                resource_type="email",
                resource_id=str(email_id),
                details={"subject": subject, "deleted_by": user.username if user else "system"},
                user=user,
                severity="warning"
            )
        except Exception:
            pass
        
        return True, f"Email '{subject}' deleted successfully"
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error deleting email: {str(e)}"


def update_email_assessment(email_id, data, user):
    """
    Update email assessment (source reliability, content validity, etc.)
    Returns: (success, message, email)
    """
    from models.email import Email
    from models.user import AuditLog
    
    try:
        email = Email.query.get(email_id)
        if not email:
            return False, "Email not found", None
        
        old_values = {
            'source_reliability': email.source_reliability,
            'content_validity': email.content_validity,
            'preparer': email.preparer,
            'status': email.status
        }
        
        # Update fields
        if 'source_reliability' in data:
            email.source_reliability = data['source_reliability']
        if 'content_validity' in data:
            email.content_validity = data['content_validity']
        if 'preparer' in data:
            email.preparer = data['preparer']
        if 'reviewer_name' in data:
            email.reviewer_name = data['reviewer_name']
        if 'reviewer_comment' in data:
            email.reviewer_comment = data['reviewer_comment']
        if 'reviewer_decision' in data:
            email.reviewer_decision = data['reviewer_decision']
        if 'status' in data:
            email.status = data['status']
        if 'intelligence_case_opened' in data:
            email.intelligence_case_opened = data['intelligence_case_opened']
        
        email.assessment_updated_at = get_hk_time()
        
        db.session.commit()
        
        # Audit log
        try:
            AuditLog.log_action(
                action="update_email_assessment",
                resource_type="email",
                resource_id=str(email_id),
                details={
                    "old_values": old_values,
                    "new_values": data,
                    "updated_by": user.username if user else "system"
                },
                user=user,
                severity="info"
            )
        except Exception:
            pass
        
        return True, "Assessment updated", email
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error updating assessment: {str(e)}", None


def get_analytics_data(emails, whatsapp_data, surveillance_data):
    """
    Build analytics chart data for int_source view
    Returns: dict with chart data
    """
    from collections import Counter
    
    try:
        # Surveillance vs Mystery Shopping
        surv_counter = Counter((s.operation_type or "Unknown") for s in surveillance_data if s is not None)
        op_type_labels = ["Surveillance", "Mystery Shopping"]
        op_type_values = [
            surv_counter.get("Surveillance", 0),
            surv_counter.get("Mystery Shopping", 0)
        ]
        
        # WhatsApp by type
        wa_total_counter = Counter((w.alleged_type or "Unknown") for w in whatsapp_data if w is not None)
        new_wa_entries = [
            w for w in whatsapp_data
            if w is not None and (w.source_reliability is None or w.content_validity is None)
        ]
        wa_new_counter = Counter((w.alleged_type or "Unknown") for w in new_wa_entries if w is not None)
        
        wa_type_labels = [
            f"{label} ({wa_new_counter.get(label, 0)}/{wa_total_counter[label]})"
            for label in wa_total_counter.keys()
        ]
        wa_type_values = [wa_total_counter[label] for label in wa_total_counter.keys()]
        
        # Email new vs reviewed
        total_emails = len(emails)
        new_email_count = sum(
            1 for e in emails
            if e is not None and (e.source_reliability is None or e.content_validity is None)
        )
        inbox_status_labels = ["New", "Reviewed"]
        inbox_status_values = [new_email_count, total_emails - new_email_count]
        
        return {
            'op_type_labels': op_type_labels,
            'op_type_values': op_type_values,
            'wa_type_labels': wa_type_labels,
            'wa_type_values': wa_type_values,
            'inbox_status_labels': inbox_status_labels,
            'inbox_status_values': inbox_status_values,
            'status_labels': [],
            'status_values': []
        }
        
    except Exception as e:
        print(f"[EMAIL SERVICE] Error building analytics: {e}")
        return {
            'op_type_labels': [],
            'op_type_values': [],
            'wa_type_labels': [],
            'wa_type_values': [],
            'inbox_status_labels': [],
            'inbox_status_values': [],
            'status_labels': [],
            'status_values': []
        }


def get_unique_int_references():
    """Get unique INT references for filter dropdown"""
    from models.case import CaseProfile
    
    try:
        int_refs = db.session.query(CaseProfile.int_reference)\
            .filter(CaseProfile.int_reference.isnot(None))\
            .distinct().order_by(CaseProfile.int_reference).all()
        return [ref[0] for ref in int_refs if ref[0]]
    except Exception as e:
        print(f"[EMAIL SERVICE] Error loading INT references: {e}")
        return []
