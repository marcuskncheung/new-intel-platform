# models/received_by_hand.py
# Received By Hand-related database models

from datetime import datetime
import pytz
from extensions import db

HK_TZ = pytz.timezone('Asia/Hong_Kong')

def get_hk_time():
    return datetime.now(HK_TZ)


class ReceivedByHandEntry(db.Model):
    """📝 RECEIVED BY HAND INTELLIGENCE ENTRY"""
    __tablename__ = 'received_by_hand_entry'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    received_time = db.Column(db.DateTime, default=get_hk_time)
    complaint_name = db.Column(db.String(255))
    contact_number = db.Column(db.String(64))
    alleged_person = db.Column(db.String(255))
    alleged_type = db.Column(db.String(255))
    source = db.Column(db.String(255))
    details = db.Column(db.Text)
    
    # Assessment fields
    source_reliability = db.Column(db.Integer)
    content_validity = db.Column(db.Integer)
    assessment_updated_at = db.Column(db.DateTime, default=get_hk_time)
    preparer = db.Column(db.String(255))
    reviewer_name = db.Column(db.String(255))
    reviewer_comment = db.Column(db.Text)
    reviewer_decision = db.Column(db.String(16))
    intelligence_case_opened = db.Column(db.Boolean, default=False)
    
    # Standardized Assessment Fields
    alleged_subject_english = db.Column(db.Text)
    alleged_subject_chinese = db.Column(db.Text)
    alleged_nature = db.Column(db.Text)
    allegation_summary = db.Column(db.Text)
    license_numbers_json = db.Column(db.Text)
    intermediary_types_json = db.Column(db.Text)
    license_number = db.Column(db.String(64))
    
    # UNIFIED INT REFERENCE SYSTEM: Link to CaseProfile
    caseprofile_id = db.Column(db.Integer, db.ForeignKey('case_profile.id'), nullable=True, index=True)
    
    # Relationships
    documents = db.relationship('ReceivedByHandDocument', backref='entry', lazy=True, cascade="all, delete-orphan")
    
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
    """Relational table for Received By Hand alleged subjects."""
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
