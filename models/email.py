# models/email.py
# Email-related database models

from datetime import datetime
import pytz
from extensions import db

HK_TZ = pytz.timezone('Asia/Hong_Kong')

def get_hk_time():
    return datetime.now(HK_TZ)


class Email(db.Model):
    """Enhanced Email model with encryption for sensitive data"""
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.String(255), unique=True, nullable=False)
    sender = db.Column(db.String(255))
    recipients = db.Column(db.String(1024))
    subject = db.Column(db.String(255))
    received = db.Column(db.String(64))
    body = db.Column(db.Text)
    source_reliability = db.Column(db.Integer)
    content_validity = db.Column(db.Integer)
    intelligence_case_opened = db.Column(db.Boolean, default=False)
    assessment_updated_at = db.Column(db.DateTime, default=get_hk_time)
    alleged_subject = db.Column(db.Text)
    alleged_subject_english = db.Column(db.Text)
    alleged_subject_chinese = db.Column(db.Text)
    alleged_nature = db.Column(db.Text)
    allegation_summary = db.Column(db.Text)
    ai_analysis_summary = db.Column(db.Text)
    license_number = db.Column(db.String(255))
    license_numbers_json = db.Column(db.Text)
    intermediary_types_json = db.Column(db.Text)
    preparer = db.Column(db.String(255))
    reviewer_name = db.Column(db.String(255))
    reviewer_comment = db.Column(db.Text)
    reviewer_decision = db.Column(db.String(16))
    status = db.Column(db.String(32), default='Pending')
    
    # Case Management Fields
    case_number = db.Column(db.String(50), nullable=True, index=True)
    case_assigned_by = db.Column(db.String(100), nullable=True)
    case_assigned_at = db.Column(db.DateTime, nullable=True)
    
    # Source Classification Fields
    source_category = db.Column(db.String(20), nullable=True)
    internal_source_type = db.Column(db.String(50), nullable=True)
    internal_source_other = db.Column(db.String(255), nullable=True)
    external_source_type = db.Column(db.String(50), nullable=True)
    external_regulator = db.Column(db.String(50), nullable=True)
    external_law_enforcement = db.Column(db.String(50), nullable=True)
    external_source_other = db.Column(db.String(255), nullable=True)
    
    # Intelligence Reference Number
    int_reference_number = db.Column(db.String(20), nullable=True, index=True)
    int_reference_order = db.Column(db.Integer, nullable=True, index=True)
    int_reference_manual = db.Column(db.Boolean, default=False)
    int_reference_updated_at = db.Column(db.DateTime, nullable=True)
    int_reference_updated_by = db.Column(db.String(100), nullable=True)
    
    # UNIFIED INT REFERENCE SYSTEM: Link to CaseProfile
    caseprofile_id = db.Column(db.Integer, db.ForeignKey('case_profile.id'), nullable=True, index=True)
    
    # Encryption flags
    is_body_encrypted = db.Column(db.Boolean, default=False)
    is_subject_encrypted = db.Column(db.Boolean, default=False)
    is_sensitive_encrypted = db.Column(db.Boolean, default=False)
    
    # Relationships
    attachments = db.relationship('Attachment', backref='email', lazy=True, cascade='all, delete-orphan')
    caseprofile = db.relationship('CaseProfile', foreign_keys=[caseprofile_id], backref='emails', lazy=True)
    
    @property
    def related_case_emails(self):
        if self.case_number:
            return Email.query.filter(
                Email.case_number == self.case_number,
                Email.id != self.id
            ).order_by(Email.received.asc()).all()
        return []
    
    @property
    def case_email_count(self):
        if self.case_number:
            return Email.query.filter(Email.case_number == self.case_number).count()
        return 1
    
    @property
    def is_case_master(self):
        if self.case_number:
            first_email = Email.query.filter(
                Email.case_number == self.case_number
            ).order_by(Email.received.asc()).first()
            return first_email and first_email.id == self.id
        return False
    
    @property
    def case_status_badge(self):
        if self.case_number:
            return {'type': 'success', 'text': f'Case {self.case_number}', 'count': self.case_email_count}
        return {'type': 'warning', 'text': 'No Case Assigned', 'count': 1}
    
    def encrypt_sensitive_fields(self):
        """Encrypt sensitive fields for secure storage"""
        try:
            from security_module import encrypt_field, SECURITY_MODULE_AVAILABLE
            if not SECURITY_MODULE_AVAILABLE:
                return
        except ImportError:
            return
        
        if self.alleged_subject and not self.is_sensitive_encrypted:
            self.alleged_subject = encrypt_field(self.alleged_subject)
        if self.alleged_nature and not self.is_sensitive_encrypted:
            self.alleged_nature = encrypt_field(self.alleged_nature)
        if self.allegation_summary and not self.is_sensitive_encrypted:
            self.allegation_summary = encrypt_field(self.allegation_summary)
        if self.ai_analysis_summary and not self.is_sensitive_encrypted:
            self.ai_analysis_summary = encrypt_field(self.ai_analysis_summary)
        if self.license_number and not self.is_sensitive_encrypted:
            self.license_number = encrypt_field(self.license_number)
        if self.reviewer_comment and not self.is_sensitive_encrypted:
            self.reviewer_comment = encrypt_field(self.reviewer_comment)
        
        self.is_sensitive_encrypted = True
        
        if self.should_encrypt_content():
            if self.body and not self.is_body_encrypted:
                self.body = encrypt_field(self.body)
                self.is_body_encrypted = True
            if self.subject and not self.is_subject_encrypted:
                self.subject = encrypt_field(self.subject)
                self.is_subject_encrypted = True
    
    def should_encrypt_content(self):
        sensitive_keywords = [
            'confidential', 'classified', 'sensitive', 'personal data',
            'investigation', 'surveillance', 'intelligence', 'suspect',
            'criminal', 'allegation', 'complaint', 'fraud', 'misconduct'
        ]
        content_to_check = f"{self.subject or ''} {self.body or ''}".lower()
        return any(keyword in content_to_check for keyword in sensitive_keywords)
    
    def get_decrypted_field(self, field_name):
        try:
            from security_module import decrypt_field, SECURITY_MODULE_AVAILABLE
            if not SECURITY_MODULE_AVAILABLE:
                return getattr(self, field_name, None)
        except ImportError:
            return getattr(self, field_name, None)
        
        field_value = getattr(self, field_name, None)
        if not field_value:
            return None
        
        is_encrypted = False
        if field_name in ['alleged_subject', 'alleged_nature', 'license_number', 'reviewer_comment']:
            is_encrypted = self.is_sensitive_encrypted
        elif field_name == 'body':
            is_encrypted = self.is_body_encrypted
        elif field_name == 'subject':
            is_encrypted = self.is_subject_encrypted
        
        if is_encrypted:
            return decrypt_field(field_value)
        return field_value
    
    def to_dict_secure(self, decrypt_sensitive=False):
        data = {
            'id': self.id,
            'entry_id': self.entry_id,
            'sender': self.sender,
            'recipients': self.recipients,
            'received': self.received,
            'source_reliability': self.source_reliability,
            'content_validity': self.content_validity,
            'intelligence_case_opened': self.intelligence_case_opened,
            'assessment_updated_at': self.assessment_updated_at.isoformat() if self.assessment_updated_at else None,
            'preparer': self.preparer,
            'reviewer_name': self.reviewer_name,
            'reviewer_decision': self.reviewer_decision,
            'status': self.status,
        }
        
        if decrypt_sensitive:
            data.update({
                'subject': self.get_decrypted_field('subject'),
                'body': self.get_decrypted_field('body'),
                'alleged_subject': self.get_decrypted_field('alleged_subject'),
                'alleged_nature': self.get_decrypted_field('alleged_nature'),
                'license_number': self.get_decrypted_field('license_number'),
                'reviewer_comment': self.get_decrypted_field('reviewer_comment'),
            })
        else:
            data.update({
                'subject': '[ENCRYPTED]' if self.is_subject_encrypted else self.subject,
                'body': '[ENCRYPTED - SENSITIVE CONTENT]' if self.is_body_encrypted else (self.body[:100] + '...' if self.body and len(self.body) > 100 else self.body),
                'alleged_subject': '[ENCRYPTED]' if self.is_sensitive_encrypted else self.alleged_subject,
                'alleged_nature': '[ENCRYPTED]' if self.is_sensitive_encrypted else self.alleged_nature,
                'license_number': '[ENCRYPTED]' if self.is_sensitive_encrypted else self.license_number,
                'reviewer_comment': '[ENCRYPTED]' if self.is_sensitive_encrypted else self.reviewer_comment,
            })
        
        return data


class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=True)
    file_data = db.Column(db.LargeBinary, nullable=True)


class EmailAllegedSubject(db.Model):
    """Relational table for email alleged subjects."""
    __tablename__ = 'email_alleged_subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email.id', ondelete='CASCADE'), nullable=False)
    english_name = db.Column(db.String(255), nullable=True)
    chinese_name = db.Column(db.String(255), nullable=True)
    is_insurance_intermediary = db.Column(db.Boolean, default=False)
    license_type = db.Column(db.String(100), nullable=True)
    license_number = db.Column(db.String(100), nullable=True)
    sequence_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.CheckConstraint('english_name IS NOT NULL OR chinese_name IS NOT NULL', name='check_has_name'),
        db.UniqueConstraint('email_id', 'sequence_order', name='unique_email_subject'),
        db.Index('idx_email_alleged_subjects_email_id', 'email_id'),
        db.Index('idx_email_alleged_subjects_english', 'english_name'),
        db.Index('idx_email_alleged_subjects_chinese', 'chinese_name'),
    )


class EmailAnalysisLock(db.Model):
    """Race condition protection for AI analysis"""
    __tablename__ = 'email_analysis_lock'
    email_id = db.Column(db.Integer, primary_key=True)
    locked_by = db.Column(db.String(100), nullable=False)
    locked_at = db.Column(db.DateTime, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f'<EmailAnalysisLock email_id={self.email_id} locked_by={self.locked_by}>'
