"""
Enhanced POI (Person of Interest) System Models
Version 2.0 - Comprehensive Architecture

This module contains the enhanced database models for the POI tracking system:
- AllegedPersonProfile (Enhanced with assessment tracking)
- POIIntelligenceLink (Universal cross-source linking)
- POIExtractionQueue (Automation queue)
- POIAssessmentHistory (Audit trail)
"""

from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

# Get db reference - this must be called AFTER app1_production has initialized db
_db = None

def _get_db():
    global _db
    if _db is None:
        from app1_production import db as app_db
        _db = app_db
    return _db

# Make db available at module level for backward compatibility
class _LazyDB:
    def __getattr__(self, name):
        return getattr(_get_db(), name)

db = _LazyDB()


class AllegedPersonProfile(db.Model):
    """
    Enhanced POI profile with comprehensive tracking and assessment
    
    Key Features:
    - Cross-source statistics (email, whatsapp, patrol, surveillance)
    - Risk assessment and scoring
    - Automated deduplication support
    - Complete audit trail
    """
    __tablename__ = 'alleged_person_profile'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    poi_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # POI-001, POI-002...
    
    # Identity Information
    name_english = db.Column(db.String(200))
    name_chinese = db.Column(db.String(200))
    name_normalized = db.Column(db.String(200), index=True)  # Lowercase, no spaces for matching
    aliases = db.Column(JSONB)  # Array of alternative names
    date_of_birth = db.Column(db.Date)
    identification_number = db.Column(db.String(50))  # Encrypted HKID/Passport
    
    # Contact Information
    phone_numbers = db.Column(JSONB)  # Array: ["+85212345678", ...]
    email_addresses = db.Column(JSONB)  # Array: ["person@example.com", ...]
    whatsapp_numbers = db.Column(JSONB)  # Array of WhatsApp contact numbers
    addresses = db.Column(JSONB)  # Array of address objects
    
    # Professional Information
    agent_number = db.Column(db.String(50))
    license_number = db.Column(db.String(100), index=True)
    license_type = db.Column(db.String(50))  # AGENT/BROKER/BOTH/NONE
    license_status = db.Column(db.String(50))  # ACTIVE/SUSPENDED/REVOKED
    company = db.Column(db.String(200))
    company_code = db.Column(db.String(50))
    role = db.Column(db.String(100))
    employment_history = db.Column(JSONB)  # Array of employment records
    
    # Assessment & Risk Scoring
    risk_level = db.Column(db.String(20), index=True)  # LOW/MEDIUM/HIGH/CRITICAL
    risk_score = db.Column(db.Integer, default=0)  # 0-100
    threat_classification = db.Column(JSONB)  # Array: ["FRAUD", "MISREPRESENTATION", ...]
    watchlist_status = db.Column(db.String(50))  # ACTIVE/MONITORING/CLEARED
    priority_level = db.Column(db.Integer, default=3)  # 1-5 (1=highest)
    assessment_notes = db.Column(db.Text)  # Encrypted sensitive notes
    
    # Intelligence Statistics (Auto-updated by triggers)
    total_mentions = db.Column(db.Integer, default=0)
    email_count = db.Column(db.Integer, default=0)
    whatsapp_count = db.Column(db.Integer, default=0)
    patrol_count = db.Column(db.Integer, default=0)
    surveillance_count = db.Column(db.Integer, default=0)
    case_count = db.Column(db.Integer, default=0)
    first_mentioned_date = db.Column(db.DateTime)
    last_mentioned_date = db.Column(db.DateTime)
    last_activity_date = db.Column(db.DateTime, index=True)
    
    # Misconduct Tracking
    alleged_misconducts = db.Column(JSONB)  # Array of allegation types
    proven_violations = db.Column(JSONB)  # Array of substantiated violations
    investigation_count = db.Column(db.Integer, default=0)
    substantiated_count = db.Column(db.Integer, default=0)
    unsubstantiated_count = db.Column(db.Integer, default=0)
    
    # Relationship Mapping
    associated_pois = db.Column(JSONB)  # Array of related POI-IDs
    organization_links = db.Column(JSONB)  # Companies/groups involved with
    network_centrality = db.Column(db.Float)  # Graph analysis score (0.0-1.0)
    
    # AI/Automation Metadata
    deduplication_group_id = db.Column(db.String(50))  # For merged entities
    merge_confidence = db.Column(db.Float)  # Similarity score if merged
    auto_enriched = db.Column(db.Boolean, default=False)
    last_enrichment_date = db.Column(db.DateTime)
    data_sources = db.Column(JSONB)  # Array: ["EMAIL-123", "WHATSAPP-45", ...]
    
    # Status & Control
    status = db.Column(db.String(20), default='ACTIVE', index=True)  # ACTIVE/MERGED/ARCHIVED
    merged_into_poi_id = db.Column(db.String(20), db.ForeignKey('alleged_person_profile.poi_id'))
    is_high_priority = db.Column(db.Boolean, default=False)
    requires_approval = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.String(100))
    approved_at = db.Column(db.DateTime)
    
    # Audit Trail
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by = db.Column(db.String(100))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_reviewed_date = db.Column(db.DateTime)
    
    # Relationships
    intelligence_links = db.relationship('POIIntelligenceLink', backref='poi_profile', lazy='dynamic', cascade='all, delete-orphan')
    assessment_history = db.relationship('POIAssessmentHistory', backref='poi_profile', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<POI {self.poi_id}: {self.name_english or self.name_chinese}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'poi_id': self.poi_id,
            'name_english': self.name_english,
            'name_chinese': self.name_chinese,
            'license_number': self.license_number,
            'company': self.company,
            'risk_level': self.risk_level,
            'risk_score': self.risk_score,
            'total_mentions': self.total_mentions,
            'email_count': self.email_count,
            'whatsapp_count': self.whatsapp_count,
            'patrol_count': self.patrol_count,
            'status': self.status,
            'last_activity_date': self.last_activity_date.isoformat() if self.last_activity_date else None
        }


class POIIntelligenceLink(db.Model):
    """
    Universal linking table connecting POIs to all intelligence sources
    Replaces the old EMAIL_ALLEGED_PERSON_LINK with polymorphic linking
    
    Key Features:
    - Links POIs to ANY source (EMAIL/WHATSAPP/PATROL/SURVEILLANCE)
    - Extraction metadata (method, tool, confidence)
    - Quality control (validation status, review flags)
    - Context preservation
    """
    __tablename__ = 'poi_intelligence_link'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Link References
    poi_id = db.Column(db.String(20), db.ForeignKey('alleged_person_profile.poi_id', ondelete='CASCADE'), nullable=False, index=True)
    case_profile_id = db.Column(db.Integer, db.ForeignKey('case_profile.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Source Reference (Polymorphic)
    source_type = db.Column(db.String(20), nullable=False, index=True)  # EMAIL/WHATSAPP/PATROL/SURVEILLANCE
    source_id = db.Column(db.Integer, nullable=False, index=True)  # ID of the source record
    source_table = db.Column(db.String(50))  # Table name: email/whatsapp_entry/online_patrol_entry
    
    # Extraction Metadata
    extraction_method = db.Column(db.String(20))  # MANUAL/AI/REGEX/NER
    extraction_tool = db.Column(db.String(50))  # GPT4/CLAUDE/SPACY/MANUAL
    confidence_score = db.Column(db.Float)  # 0.0-1.0
    extraction_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    extracted_by_user = db.Column(db.String(100))  # NULL if automated
    validation_status = db.Column(db.String(20), default='PENDING', index=True)  # PENDING/VERIFIED/REJECTED
    
    # Context Information
    mention_context = db.Column(db.Text)  # Text snippet where POI mentioned
    role_in_case = db.Column(db.String(50))  # COMPLAINANT/SUBJECT/WITNESS/OTHER
    mention_count = db.Column(db.Integer, default=1)
    is_primary_subject = db.Column(db.Boolean, default=False)
    
    # Quality Assurance
    verified_by = db.Column(db.String(100))
    verified_at = db.Column(db.DateTime)
    verification_notes = db.Column(db.Text)
    needs_review = db.Column(db.Boolean, default=False, index=True)
    
    # Audit Trail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: one POI per source record
    __table_args__ = (
        db.UniqueConstraint('poi_id', 'source_type', 'source_id', name='unique_poi_source'),
        db.Index('idx_poi_link_source', 'source_type', 'source_id'),
    )
    
    def __repr__(self):
        return f'<POILink {self.poi_id} → {self.source_type}-{self.source_id}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'poi_id': self.poi_id,
            'case_profile_id': self.case_profile_id,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'extraction_method': self.extraction_method,
            'confidence_score': self.confidence_score,
            'validation_status': self.validation_status,
            'role_in_case': self.role_in_case,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class POIExtractionQueue(db.Model):
    """
    Queue for automated POI extraction jobs
    Processes intelligence sources to extract and link POIs
    
    Key Features:
    - Priority-based processing
    - Retry logic for failed jobs
    - Quality control flags
    - Result storage
    """
    __tablename__ = 'poi_extraction_queue'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Job References
    case_profile_id = db.Column(db.Integer, db.ForeignKey('case_profile.id', ondelete='CASCADE'), nullable=False)
    source_type = db.Column(db.String(20), nullable=False)  # EMAIL/WHATSAPP/PATROL/SURVEILLANCE
    source_id = db.Column(db.Integer, nullable=False)
    
    # Processing Status
    status = db.Column(db.String(20), default='PENDING', index=True)  # PENDING/PROCESSING/COMPLETE/FAILED/NEEDS_REVIEW
    priority = db.Column(db.Integer, default=3, index=True)  # 1-5 (1=highest)
    queued_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    processing_started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    assigned_to = db.Column(db.String(100))  # Worker ID/Username
    
    # Extraction Results
    extracted_entities = db.Column(JSONB)  # Raw AI output: [{name, confidence, context}, ...]
    extraction_method = db.Column(db.String(50))  # AI model/tool used
    extraction_confidence = db.Column(db.Float)  # Average confidence score
    entities_found_count = db.Column(db.Integer, default=0)
    matched_existing_pois = db.Column(JSONB)  # Array of POI-IDs matched
    
    # Quality Check
    requires_manual_review = db.Column(db.Boolean, default=False, index=True)
    review_reason = db.Column(db.String(200))  # "Low confidence", "Conflict", etc.
    reviewed_by = db.Column(db.String(100))
    reviewed_at = db.Column(db.DateTime)
    review_notes = db.Column(db.Text)
    
    # Error Handling
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    last_error_at = db.Column(db.DateTime)
    max_retries = db.Column(db.Integer, default=3)
    
    # Unique constraint: one extraction job per source
    __table_args__ = (
        db.UniqueConstraint('source_type', 'source_id', name='unique_extraction_source'),
    )
    
    def __repr__(self):
        return f'<ExtractionJob {self.id}: {self.source_type}-{self.source_id} [{self.status}]>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'case_profile_id': self.case_profile_id,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'status': self.status,
            'priority': self.priority,
            'entities_found_count': self.entities_found_count,
            'requires_manual_review': self.requires_manual_review,
            'queued_at': self.queued_at.isoformat() if self.queued_at else None
        }


class POIAssessmentHistory(db.Model):
    """
    Audit trail for POI risk assessments
    Tracks who changed what and why
    
    Key Features:
    - Complete change history
    - Supporting evidence links
    - Trigger source tracking
    """
    __tablename__ = 'poi_assessment_history'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Assessment References
    poi_id = db.Column(db.String(20), db.ForeignKey('alleged_person_profile.poi_id', ondelete='CASCADE'), nullable=False, index=True)
    assessed_by = db.Column(db.String(100), nullable=False)
    assessment_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Assessment Changes
    previous_risk_level = db.Column(db.String(20))
    new_risk_level = db.Column(db.String(20))
    previous_risk_score = db.Column(db.Integer)
    new_risk_score = db.Column(db.Integer)
    assessment_reason = db.Column(db.Text)  # Why changed
    supporting_evidence = db.Column(JSONB)  # Array of case references
    assessment_notes = db.Column(db.Text)  # Encrypted
    
    # Related Intelligence
    related_case_profiles = db.Column(JSONB)  # Array of INT-### references
    trigger_source_type = db.Column(db.String(20))  # What prompted reassessment
    trigger_source_id = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<Assessment {self.poi_id}: {self.previous_risk_level}→{self.new_risk_level}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'poi_id': self.poi_id,
            'assessed_by': self.assessed_by,
            'assessment_date': self.assessment_date.isoformat() if self.assessment_date else None,
            'previous_risk_level': self.previous_risk_level,
            'new_risk_level': self.new_risk_level,
            'previous_risk_score': self.previous_risk_score,
            'new_risk_score': self.new_risk_score,
            'assessment_reason': self.assessment_reason
        }
