# models/case.py
# Case Profile database model

from datetime import datetime
import pytz
from extensions import db

HK_TZ = pytz.timezone('Asia/Hong_Kong')

def get_hk_time():
    return datetime.now(HK_TZ)


class CaseProfile(db.Model):
    """
    🔗 UNIFIED INT-### REFERENCE SYSTEM
    Central intelligence item registry - links ALL sources (Email, WhatsApp, Patrol, Received by Hand)
    """
    __tablename__ = "case_profile"
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Unified INT Reference System
    int_reference = db.Column(db.String(20), unique=True, nullable=False, index=True)
    index_order = db.Column(db.Integer, unique=True, nullable=False, index=True)
    
    # Source Classification
    date_of_receipt = db.Column(db.DateTime, nullable=False, index=True)
    source_type = db.Column(db.String(30), nullable=False, index=True)
    
    # Source Foreign Keys (one-to-one relationship)
    email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=True, unique=True)
    whatsapp_id = db.Column(db.Integer, db.ForeignKey('whats_app_entry.id'), nullable=True, unique=True)
    patrol_id = db.Column(db.Integer, db.ForeignKey('online_patrol_entry.id'), nullable=True, unique=True)
    received_by_hand_id = db.Column(db.Integer, db.ForeignKey('received_by_hand_entry.id'), nullable=True, unique=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=get_hk_time)
    updated_at = db.Column(db.DateTime, default=get_hk_time, onupdate=get_hk_time)
    created_by = db.Column(db.String(100))
    
    # Relationships - using string references to avoid circular imports
    email = db.relationship('Email', backref='case_profile', foreign_keys=[email_id], uselist=False)
    whatsapp = db.relationship('WhatsAppEntry', backref='case_profile', foreign_keys=[whatsapp_id], uselist=False)
    patrol = db.relationship('OnlinePatrolEntry', backref='case_profile', foreign_keys=[patrol_id], uselist=False)
    received_by_hand = db.relationship('ReceivedByHandEntry', backref='case_profile', foreign_keys=[received_by_hand_id], uselist=False)
    
    def __repr__(self):
        return f'<CaseProfile {self.int_reference} ({self.source_type})>'
