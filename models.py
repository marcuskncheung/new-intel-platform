# models.py
# Database Models for Intelligence Platform
# Separated from app for modular Blueprint architecture

from datetime import datetime
import json
from flask_login import UserMixin
from extensions import db, HK_TZ

# ========================================
# 🇭🇰 HONG KONG TIMEZONE UTILITIES
# ========================================

def get_hk_time():
    """🇭🇰 Get current Hong Kong time (timezone-aware)"""
    from datetime import datetime
    import pytz
    return datetime.now(HK_TZ)


# ========================================
# Security Module Compatibility
# ========================================
# These will be overridden when security module is available
SECURITY_MODULE_AVAILABLE = False

def encrypt_field(value):
    """Placeholder for field encryption"""
    return value

def decrypt_field(value):
    """Placeholder for field decryption"""
    return value

try:
    from security_module import encrypt_field, decrypt_field, init_security
    SECURITY_MODULE_AVAILABLE = True
except ImportError:
    pass


# ========================================
# USER MODEL
# ========================================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'
    created_at = db.Column(db.DateTime, default=get_hk_time)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    def is_admin(self):
        return self.role == 'admin'


# ========================================
# AUDIT LOG MODEL
# ========================================

class AuditLog(db.Model):
    """Enhanced audit log with encryption and comprehensive tracking"""
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    username = db.Column(db.String(80))
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(200))
    resource_id = db.Column(db.String(100))
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=get_hk_time)
    session_id = db.Column(db.String(200))
    severity = db.Column(db.String(20), default='info')
    
    @staticmethod
    def log_action(action, resource_type=None, resource_id=None, details=None, user=None, severity='info'):
        """Enhanced audit logging with encryption and proper Flask context handling"""
        try:
            from flask import request, session as flask_session, has_request_context, has_app_context
            
            if not has_app_context():
                print(f"⚠️ Audit log skipped - no app context: {action}")
                return
            
            encrypted_details = None
            if details:
                if isinstance(details, dict):
                    details = json.dumps(details)
                details_str = str(details)
                if len(details_str) > 5000:
                    details_str = details_str[:4900] + "...[truncated]"
                
                if SECURITY_MODULE_AVAILABLE:
                    encrypted_details = encrypt_field(details_str)
                else:
                    encrypted_details = details_str
            
            username_val = (user.username if user else 'Anonymous')[:80] if user and user.username else 'Anonymous'
            action_val = action[:100] if action else ''
            resource_type_val = resource_type[:200] if resource_type else None
            resource_id_val = str(resource_id)[:100] if resource_id else None
            ip_address_val = (request.remote_addr if has_request_context() and request else None)
            if ip_address_val and len(ip_address_val) > 45:
                ip_address_val = ip_address_val[:45]
            user_agent_val = (request.headers.get('User-Agent', '') if has_request_context() and request else '')[:500]
            session_id_val = (flask_session.get('_id', 'unknown') if has_request_context() and flask_session else 'unknown')[:200]
            severity_val = severity[:20] if severity else 'info'
            
            log_entry = AuditLog(
                user_id=user.id if user else None,
                username=username_val,
                action=action_val,
                resource_type=resource_type_val,
                resource_id=resource_id_val,
                details=encrypted_details,
                ip_address=ip_address_val,
                user_agent=user_agent_val,
                session_id=session_id_val,
                severity=severity_val
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as e:
            print(f"⚠️ Audit log error: {e}")
            try:
                db.session.rollback()
            except Exception:
                pass
    
    def get_decrypted_details(self):
        """Get decrypted details for authorized viewing"""
        if not self.details:
            return None
        if SECURITY_MODULE_AVAILABLE:
            return decrypt_field(self.details)
        return self.details
    
    def to_dict(self):
        """Convert audit log to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.get_decrypted_details(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'session_id': self.session_id,
            'severity': self.severity
        }


# ========================================
# FEATURE SETTINGS MODEL
# ========================================

class FeatureSettings(db.Model):
    """Admin-controlled feature visibility settings"""
    __tablename__ = 'feature_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    feature_key = db.Column(db.String(100), unique=True, nullable=False)
    feature_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_enabled = db.Column(db.Boolean, default=True)
    admin_only = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=get_hk_time, onupdate=get_hk_time)
    updated_by = db.Column(db.String(100))
    
    DEFAULT_FEATURES = [
        {'feature_key': 'ai_analysis', 'feature_name': 'AI Analysis (Email)', 'description': 'AI-powered analysis for emails', 'is_enabled': True, 'admin_only': True},
        {'feature_key': 'ai_status_button', 'feature_name': 'AI Status Button', 'description': 'Button to check AI analysis status', 'is_enabled': True, 'admin_only': True},
        {'feature_key': 'rebuild_poi_list', 'feature_name': 'Rebuild POI List', 'description': 'Button to rebuild POI list', 'is_enabled': True, 'admin_only': True},
        {'feature_key': 'surveillance_tab', 'feature_name': 'Surveillance Tab', 'description': 'Surveillance Operation tab', 'is_enabled': True, 'admin_only': False},
        {'feature_key': 'database_admin', 'feature_name': 'Database Overview', 'description': 'Database management access', 'is_enabled': True, 'admin_only': True},
    ]
    
    @classmethod
    def get_setting(cls, feature_key):
        return cls.query.filter_by(feature_key=feature_key).first()
    
    @classmethod
    def is_feature_visible(cls, feature_key, user=None):
        setting = cls.get_setting(feature_key)
        if not setting:
            return True
        if not setting.is_enabled:
            return False
        if setting.admin_only:
            if user and hasattr(user, 'is_admin'):
                return user.is_admin() if callable(user.is_admin) else user.is_admin
            return False
        return True
    
    @classmethod
    def initialize_defaults(cls):
        for feature in cls.DEFAULT_FEATURES:
            existing = cls.query.filter_by(feature_key=feature['feature_key']).first()
            if not existing:
                new_setting = cls(
                    feature_key=feature['feature_key'],
                    feature_name=feature['feature_name'],
                    description=feature['description'],
                    is_enabled=feature['is_enabled'],
                    admin_only=feature['admin_only'],
                    updated_by='system'
                )
                db.session.add(new_setting)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ Error initializing feature settings: {e}")


# ========================================
# CASE PROFILE MODEL (Unified INT Reference System)
# ========================================

class CaseProfile(db.Model):
    """🔗 UNIFIED INT-### REFERENCE SYSTEM - Central intelligence item registry"""
    __tablename__ = "case_profile"
    
    id = db.Column(db.Integer, primary_key=True)
    int_reference = db.Column(db.String(20), unique=True, nullable=False, index=True)
    index_order = db.Column(db.Integer, unique=True, nullable=False, index=True)
    date_of_receipt = db.Column(db.DateTime, nullable=False, index=True)
    source_type = db.Column(db.String(30), nullable=False, index=True)
    
    email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=True, unique=True)
    whatsapp_id = db.Column(db.Integer, db.ForeignKey('whats_app_entry.id'), nullable=True, unique=True)
    patrol_id = db.Column(db.Integer, db.ForeignKey('online_patrol_entry.id'), nullable=True, unique=True)
    received_by_hand_id = db.Column(db.Integer, db.ForeignKey('received_by_hand_entry.id'), nullable=True, unique=True)
    
    created_at = db.Column(db.DateTime, default=get_hk_time)
    updated_at = db.Column(db.DateTime, default=get_hk_time, onupdate=get_hk_time)
    created_by = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<CaseProfile {self.int_reference} ({self.source_type})>'


# ========================================
# EMAIL MODELS
# ========================================

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
    
    # Link to CaseProfile
    caseprofile_id = db.Column(db.Integer, db.ForeignKey('case_profile.id'), nullable=True, index=True)
    
    # Encryption flags
    is_body_encrypted = db.Column(db.Boolean, default=False)
    is_subject_encrypted = db.Column(db.Boolean, default=False)
    is_sensitive_encrypted = db.Column(db.Boolean, default=False)
    
    # Relationships
    attachments = db.relationship('Attachment', backref='email', lazy=True, cascade='all, delete-orphan')
    caseprofile = db.relationship('CaseProfile', foreign_keys=[caseprofile_id], backref='emails', lazy=True)


class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=True)
    file_data = db.Column(db.LargeBinary, nullable=True)


class EmailAllegedSubject(db.Model):
    """Relational table for email alleged subjects"""
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


# ========================================
# WHATSAPP MODELS
# ========================================

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
    
    alleged_subject_english = db.Column(db.Text)
    alleged_subject_chinese = db.Column(db.Text)
    alleged_nature = db.Column(db.Text)
    allegation_summary = db.Column(db.Text)
    license_numbers_json = db.Column(db.Text)
    intermediary_types_json = db.Column(db.Text)
    license_number = db.Column(db.String(64))
    
    caseprofile_id = db.Column(db.Integer, db.ForeignKey('case_profile.id'), nullable=True, index=True)
    
    images = db.relationship('WhatsAppImage', backref='entry', lazy=True, cascade="all, delete-orphan")
    
    @property
    def int_reference(self):
        if self.caseprofile_id:
            case = db.session.get(CaseProfile, self.caseprofile_id)
            return case.int_reference if case else None
        return None


class WhatsAppImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    whatsapp_id = db.Column(db.Integer, db.ForeignKey('whats_app_entry.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=True)
    image_data = db.Column(db.LargeBinary, nullable=True)


class WhatsAppAllegedSubject(db.Model):
    """Relational table for WhatsApp alleged subjects"""
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


# ========================================
# ONLINE PATROL MODELS
# ========================================

class OnlinePatrolEntry(db.Model):
    """Online Patrol Intelligence Entry"""
    __tablename__ = 'online_patrol_entry'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    source = db.Column(db.String(255))
    source_time = db.Column(db.DateTime)
    discovered_by = db.Column(db.String(255))
    discovery_time = db.Column(db.DateTime, default=get_hk_time)
    sender = db.Column(db.String(255))
    complaint_time = db.Column(db.DateTime)
    status = db.Column(db.String(64))
    details = db.Column(db.Text)
    threats = db.Column(db.Text)
    alleged_person = db.Column(db.String(255))
    
    source_reliability = db.Column(db.Integer)
    content_validity = db.Column(db.Integer)
    assessment_updated_at = db.Column(db.DateTime, default=get_hk_time)
    
    alleged_subject_english = db.Column(db.Text)
    alleged_subject_chinese = db.Column(db.Text)
    alleged_nature = db.Column(db.Text)
    allegation_summary = db.Column(db.Text)
    license_numbers_json = db.Column(db.Text)
    intermediary_types_json = db.Column(db.Text)
    license_number = db.Column(db.String(64))
    
    preparer = db.Column(db.String(255))
    reviewer_name = db.Column(db.String(255))
    reviewer_comment = db.Column(db.Text)
    reviewer_decision = db.Column(db.String(16))
    intelligence_case_opened = db.Column(db.Boolean, default=False)
    
    caseprofile_id = db.Column(db.Integer, db.ForeignKey('case_profile.id'), nullable=True, index=True)
    
    photos = db.relationship('OnlinePatrolPhoto', backref='patrol_entry', lazy=True, cascade="all, delete-orphan")
    
    @property
    def int_reference(self):
        if self.caseprofile_id:
            case = db.session.get(CaseProfile, self.caseprofile_id)
            return case.int_reference if case else None
        return None


class OnlinePatrolPhoto(db.Model):
    """Online Patrol Photo Storage"""
    __tablename__ = 'online_patrol_photo'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    online_patrol_id = db.Column(db.Integer, db.ForeignKey('online_patrol_entry.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    image_data = db.Column(db.LargeBinary, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=get_hk_time)
    uploaded_by = db.Column(db.String(255))
    caption = db.Column(db.Text)


class OnlinePatrolAllegedSubject(db.Model):
    """Relational table for Online Patrol alleged subjects"""
    __tablename__ = 'online_patrol_alleged_subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    patrol_id = db.Column(db.Integer, db.ForeignKey('online_patrol_entry.id', ondelete='CASCADE'), nullable=False)
    english_name = db.Column(db.String(255), nullable=True)
    chinese_name = db.Column(db.String(255), nullable=True)
    is_insurance_intermediary = db.Column(db.Boolean, default=False)
    license_type = db.Column(db.String(100), nullable=True)
    license_number = db.Column(db.String(100), nullable=True)
    sequence_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.CheckConstraint('english_name IS NOT NULL OR chinese_name IS NOT NULL', name='check_patrol_has_name'),
        db.UniqueConstraint('patrol_id', 'sequence_order', name='unique_patrol_subject'),
        db.Index('idx_patrol_alleged_subjects_patrol_id', 'patrol_id'),
        db.Index('idx_patrol_alleged_subjects_english', 'english_name'),
        db.Index('idx_patrol_alleged_subjects_chinese', 'chinese_name'),
    )


# ========================================
# SURVEILLANCE MODELS
# ========================================

class SurveillanceEntry(db.Model):
    __tablename__ = 'surveillance_entry'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    operation_number = db.Column(db.String(64))
    operation_type = db.Column(db.String(64))
    date = db.Column(db.Date)
    venue = db.Column(db.String(255))
    details_of_finding = db.Column(db.Text)
    conducted_by = db.Column(db.String(32))
    
    operation_finding = db.Column(db.Text)
    has_adverse_finding = db.Column(db.Boolean, default=False)
    adverse_finding_details = db.Column(db.Text)
    observation_notes = db.Column(db.Text)
    
    preparer = db.Column(db.String(255))
    reviewer_name = db.Column(db.String(255))
    reviewer_comment = db.Column(db.Text)
    reviewer_decision = db.Column(db.String(16))
    assessment_updated_at = db.Column(db.DateTime, default=get_hk_time)
    
    targets = db.relationship('Target', backref='surveillance_entry', cascade='all, delete-orphan')
    
    caseprofile_id = db.Column(db.Integer, db.ForeignKey('case_profile.id'), nullable=True, index=True)
    
    @property
    def int_reference(self):
        if self.caseprofile_id:
            case = db.session.get(CaseProfile, self.caseprofile_id)
            return case.int_reference if case else None
        return None


class Target(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    surveillance_entry_id = db.Column(db.Integer, db.ForeignKey('surveillance_entry.id'), nullable=False)
    license_type = db.Column(db.String(50))
    license_number = db.Column(db.String(64))
    content_validity = db.Column(db.Integer)
    assessment_updated_at = db.Column(db.DateTime, default=get_hk_time)


class SurveillancePhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    surveillance_id = db.Column(db.Integer, db.ForeignKey('surveillance_entry.id'), nullable=False)
    filename = db.Column(db.String(255))
    image_data = db.Column(db.LargeBinary)
    uploaded_at = db.Column(db.DateTime, default=get_hk_time)


class SurveillanceDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    surveillance_id = db.Column(db.Integer, db.ForeignKey('surveillance_entry.id'), nullable=False)
    filename = db.Column(db.String(255))
    filepath = db.Column(db.String(512))


# ========================================
# RECEIVED BY HAND MODELS
# ========================================

class ReceivedByHandEntry(db.Model):
    """Received By Hand Intelligence Entry"""
    __tablename__ = 'received_by_hand_entry'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    received_time = db.Column(db.DateTime, default=get_hk_time)
    complaint_name = db.Column(db.String(255))
    contact_number = db.Column(db.String(64))
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
    
    alleged_subject_english = db.Column(db.Text)
    alleged_subject_chinese = db.Column(db.Text)
    alleged_nature = db.Column(db.Text)
    allegation_summary = db.Column(db.Text)
    license_numbers_json = db.Column(db.Text)
    intermediary_types_json = db.Column(db.Text)
    license_number = db.Column(db.String(64))
    
    caseprofile_id = db.Column(db.Integer, db.ForeignKey('case_profile.id'), nullable=True, index=True)
    
    documents = db.relationship('ReceivedByHandDocument', backref='entry', lazy=True, cascade="all, delete-orphan")
    
    @property
    def int_reference(self):
        if self.caseprofile_id:
            case = db.session.get(CaseProfile, self.caseprofile_id)
            return case.int_reference if case else None
        return None


class ReceivedByHandDocument(db.Model):
    """Documents attached to received-by-hand entries"""
    __tablename__ = 'received_by_hand_document'
    
    id = db.Column(db.Integer, primary_key=True)
    received_by_hand_id = db.Column(db.Integer, db.ForeignKey('received_by_hand_entry.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_data = db.Column(db.LargeBinary, nullable=False)
    file_type = db.Column(db.String(50))
    uploaded_at = db.Column(db.DateTime, default=get_hk_time)


class ReceivedByHandAllegedSubject(db.Model):
    """Relational table for Received By Hand alleged subjects"""
    __tablename__ = 'received_by_hand_alleged_subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    received_by_hand_id = db.Column(db.Integer, db.ForeignKey('received_by_hand_entry.id', ondelete='CASCADE'), nullable=False)
    english_name = db.Column(db.String(255), nullable=True)
    chinese_name = db.Column(db.String(255), nullable=True)
    is_insurance_intermediary = db.Column(db.Boolean, default=False)
    license_type = db.Column(db.String(100), nullable=True)
    license_number = db.Column(db.String(100), nullable=True)
    sequence_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=get_hk_time)
    
    __table_args__ = (
        db.CheckConstraint('english_name IS NOT NULL OR chinese_name IS NOT NULL', name='check_rbh_has_name'),
        db.UniqueConstraint('received_by_hand_id', 'sequence_order', name='unique_rbh_subject'),
        db.Index('idx_rbh_alleged_subjects_rbh_id', 'received_by_hand_id'),
        db.Index('idx_rbh_alleged_subjects_english', 'english_name'),
        db.Index('idx_rbh_alleged_subjects_chinese', 'chinese_name'),
    )


# ========================================
# POI / ALLEGED PERSON MODELS
# ========================================
# Note: Additional POI models are in models_poi_enhanced.py
# Import them after db initialization to avoid circular imports


# ========================================
# HELPER FUNCTION
# ========================================

def can_see_feature(feature_key):
    """Template helper to check if current user can see a feature"""
    from flask_login import current_user
    return FeatureSettings.is_feature_visible(feature_key, current_user if current_user.is_authenticated else None)
