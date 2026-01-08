# models/whatsapp.py
# WhatsApp-related database models

from datetime import datetime
import pytz
from extensions import db

HK_TZ = pytz.timezone('Asia/Hong_Kong')

def get_hk_time():
    return datetime.now(HK_TZ)


class WhatsAppEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    received_time = db.Column(db.DateTime)
    complaint_name = db.Column(db.String(255))
    phone_number = db.Column(db.String(64))
    alleged_person = db.Column(db.String(255))
    alleged_type = db.Column(db.String(255))
    source = db.Column(db.String(255))
    details = db.Column(db.Text)
    source_reliability = db.Column(db.Integer)
    content_validity = db.Column(db.Integer)
    assessment_updated_at = db.Column(db.DateTime, default=get_hk_time)
    preparer = db.Column(db.String(255))
    reviewer_name = db.Column(db.String(255))
    reviewer_comment = db.Column(db.Text)
    reviewer_decision = db.Column(db.String(16))
    intelligence_case_opened = db.Column(db.Boolean, default=False)
    
    # Standardized assessment fields
    alleged_subject_english = db.Column(db.Text)
    alleged_subject_chinese = db.Column(db.Text)
    alleged_nature = db.Column(db.Text)
    allegation_summary = db.Column(db.Text)
    license_numbers_json = db.Column(db.Text)
    intermediary_types_json = db.Column(db.Text)
    license_number = db.Column(db.String(64))
    
    # UNIFIED INT REFERENCE SYSTEM: Link to CaseProfile
    caseprofile_id = db.Column(db.Integer, db.ForeignKey('case_profile.id'), nullable=True, index=True)
    
    images = db.relationship('WhatsAppImage', backref='entry', lazy=True, cascade="all, delete-orphan")
    
    @property
    def int_reference(self):
        """Get unified INT reference from CaseProfile"""
        if self.caseprofile_id:
            from models.case import CaseProfile
            case = db.session.get(CaseProfile, self.caseprofile_id)
            return case.int_reference if case else None
        return None
    
    @property
    def received_time_formatted(self):
        if not self.received_time:
            return ''
        
        if hasattr(self.received_time, 'strftime'):
            return self.received_time.strftime('%Y-%m-%d %H:%M')
        
        if isinstance(self.received_time, str):
            try:
                for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']:
                    try:
                        dt = datetime.strptime(self.received_time, fmt)
                        return dt.strftime('%Y-%m-%d %H:%M')
                    except ValueError:
                        continue
                return str(self.received_time)
            except Exception:
                return str(self.received_time)
        
        return str(self.received_time) if self.received_time else ''


class WhatsAppImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    whatsapp_id = db.Column(db.Integer, db.ForeignKey('whats_app_entry.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=True)
    image_data = db.Column(db.LargeBinary, nullable=True)


class WhatsAppAllegedSubject(db.Model):
    """Relational table for WhatsApp alleged subjects."""
    __tablename__ = 'whatsapp_alleged_subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    whatsapp_id = db.Column(db.Integer, db.ForeignKey('whats_app_entry.id', ondelete='CASCADE'), nullable=False)
    english_name = db.Column(db.String(255), nullable=True)
    chinese_name = db.Column(db.String(255), nullable=True)
    is_insurance_intermediary = db.Column(db.Boolean, default=False)
    license_type = db.Column(db.String(100), nullable=True)
    license_number = db.Column(db.String(100), nullable=True)
    sequence_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.CheckConstraint('english_name IS NOT NULL OR chinese_name IS NOT NULL', name='check_whatsapp_has_name'),
        db.UniqueConstraint('whatsapp_id', 'sequence_order', name='unique_whatsapp_subject'),
        db.Index('idx_whatsapp_alleged_subjects_whatsapp_id', 'whatsapp_id'),
        db.Index('idx_whatsapp_alleged_subjects_english', 'english_name'),
        db.Index('idx_whatsapp_alleged_subjects_chinese', 'chinese_name'),
    )
