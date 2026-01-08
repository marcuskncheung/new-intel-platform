# models/patrol.py
# Online Patrol-related database models

from datetime import datetime
import pytz
from extensions import db

HK_TZ = pytz.timezone('Asia/Hong_Kong')

def get_hk_time():
    return datetime.now(HK_TZ)


class OnlinePatrolEntry(db.Model):
    """📱 ONLINE PATROL INTELLIGENCE ENTRY"""
    __tablename__ = 'online_patrol_entry'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Core Fields
    source = db.Column(db.String(255))  # Platform: IG, WeChat, Facebook, Forum, etc.
    source_time = db.Column(db.DateTime)
    discovered_by = db.Column(db.String(255))
    discovery_time = db.Column(db.DateTime, default=get_hk_time)
    
    # Legacy Fields
    sender = db.Column(db.String(255))
    complaint_time = db.Column(db.DateTime)
    status = db.Column(db.String(64))
    
    # Content Details
    details = db.Column(db.Text)
    threats = db.Column(db.Text)
    alleged_person = db.Column(db.String(255))
    
    # Assessment Fields
    source_reliability = db.Column(db.Integer)
    content_validity = db.Column(db.Integer)
    assessment_updated_at = db.Column(db.DateTime, default=get_hk_time)
    
    # Standardized Assessment Fields
    alleged_subject_english = db.Column(db.Text)
    alleged_subject_chinese = db.Column(db.Text)
    alleged_nature = db.Column(db.Text)
    allegation_summary = db.Column(db.Text)
    license_numbers_json = db.Column(db.Text)
    intermediary_types_json = db.Column(db.Text)
    license_number = db.Column(db.String(64))
    
    # Reviewer Fields
    preparer = db.Column(db.String(255))
    reviewer_name = db.Column(db.String(255))
    reviewer_comment = db.Column(db.Text)
    reviewer_decision = db.Column(db.String(16))
    intelligence_case_opened = db.Column(db.Boolean, default=False)
    
    # UNIFIED INT REFERENCE SYSTEM: Link to CaseProfile
    caseprofile_id = db.Column(db.Integer, db.ForeignKey('case_profile.id'), nullable=True, index=True)
    
    # Photo Relationship
    photos = db.relationship('OnlinePatrolPhoto', backref='patrol_entry', lazy=True, cascade="all, delete-orphan")
    
    @property
    def int_reference(self):
        """Get unified INT reference from CaseProfile"""
        if self.caseprofile_id:
            from models.case import CaseProfile
            case = db.session.get(CaseProfile, self.caseprofile_id)
            return case.int_reference if case else None
        return None
    
    @property
    def combined_score(self):
        return (self.source_reliability or 0) + (self.content_validity or 0)


class OnlinePatrolPhoto(db.Model):
    """📸 ONLINE PATROL PHOTO STORAGE"""
    __tablename__ = 'online_patrol_photo'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    online_patrol_id = db.Column(db.Integer, db.ForeignKey('online_patrol_entry.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    image_data = db.Column(db.LargeBinary, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=get_hk_time)
    uploaded_by = db.Column(db.String(255))
    caption = db.Column(db.Text)


class OnlinePatrolAllegedSubject(db.Model):
    """Relational table for Online Patrol alleged subjects."""
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
