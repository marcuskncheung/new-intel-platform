# models/surveillance.py
# Surveillance-related database models

from datetime import datetime
import pytz
from extensions import db

HK_TZ = pytz.timezone('Asia/Hong_Kong')

def get_hk_time():
    return datetime.now(HK_TZ)


class SurveillanceEntry(db.Model):
    __tablename__ = 'surveillance_entry'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    operation_number = db.Column(db.String(64))
    operation_type = db.Column(db.String(64))  # Mystery Shopping or Surveillance
    date = db.Column(db.Date)
    venue = db.Column(db.String(255))
    details_of_finding = db.Column(db.Text)
    conducted_by = db.Column(db.String(32))  # 'Private investigator' or 'IA staff'
    
    # Surveillance-Specific Assessment
    operation_finding = db.Column(db.Text)
    has_adverse_finding = db.Column(db.Boolean, default=False)
    adverse_finding_details = db.Column(db.Text)
    observation_notes = db.Column(db.Text)
    
    # Standard assessment fields
    preparer = db.Column(db.String(255))
    reviewer_name = db.Column(db.String(255))
    reviewer_comment = db.Column(db.Text)
    reviewer_decision = db.Column(db.String(16))
    assessment_updated_at = db.Column(db.DateTime, default=get_hk_time)
    
    # Relationships
    targets = db.relationship('Target', backref='surveillance_entry', cascade='all, delete-orphan')
    
    # UNIFIED INT REFERENCE SYSTEM: Link to CaseProfile
    caseprofile_id = db.Column(db.Integer, db.ForeignKey('case_profile.id'), nullable=True, index=True)
    
    @property
    def int_reference(self):
        """Get INT reference from linked CaseProfile"""
        if self.caseprofile_id:
            from models.case import CaseProfile
            case = db.session.get(CaseProfile, self.caseprofile_id)
            return case.int_reference if case else None
        return None


class Target(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    surveillance_entry_id = db.Column(db.Integer, db.ForeignKey('surveillance_entry.id'), nullable=False)
    
    # Licensing fields
    license_type = db.Column(db.String(50))  # 'Agent', 'Technical Representative', 'Insurer', 'Broker', 'Others'
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
