"""
Enhanced POI (Person of Interest) System Models
Version 2.0 - Comprehensive Architecture

This module contains the enhanced database models for the POI tracking system:
- AllegedPersonProfile (Enhanced with assessment tracking)
- POIIntelligenceLink (Universal cross-source linking)
- POIExtractionQueue (Automation queue)
- POIAssessmentHistory (Audit trail)

IMPORTANT: This module uses factory pattern for late binding.
Call init_models(db) after Flask app initialization to create the model classes.

Build: 2025-10-17T14:30 - Factory pattern implementation
"""

from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

# Global references to model classes (set by init_models())
AllegedPersonProfile = None
POIIntelligenceLink = None
EmailAllegedPersonLink = None
POIExtractionQueue = None
POIAssessmentHistory = None

def init_models(db_instance):
    """
    Initialize POI models with the provided db instance.
    
    Args:
        db_instance: Flask-SQLAlchemy db object
        
    Returns:
        dict: Dictionary containing all model classes
    """
    global AllegedPersonProfile, POIIntelligenceLink, EmailAllegedPersonLink
    global POIExtractionQueue, POIAssessmentHistory
    
    class _AllegedPersonProfile(db_instance.Model):
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
        id = db_instance.Column(db_instance.Integer, primary_key=True)
        poi_id = db_instance.Column(db_instance.String(20), unique=True, nullable=False, index=True)  # POI-001, POI-002...
        
        # Identity Information
        name_english = db_instance.Column(db_instance.String(200))
        name_chinese = db_instance.Column(db_instance.String(200))
        name_normalized = db_instance.Column(db_instance.String(200), index=True)  # Lowercase, no spaces for matching
        aliases = db_instance.Column(JSONB)  # Array of alternative names
        date_of_birth = db_instance.Column(db_instance.Date)
        identification_number = db_instance.Column(db_instance.String(50))  # Encrypted HKID/Passport
        
        # Contact Information
        phone_numbers = db_instance.Column(JSONB)  # Array: ["+85212345678", ...]
        email_addresses = db_instance.Column(JSONB)  # Array: ["person@example.com", ...]
        whatsapp_numbers = db_instance.Column(JSONB)  # Array of WhatsApp contact numbers
        addresses = db_instance.Column(JSONB)  # Array of address objects
        
        # Professional Information
        agent_number = db_instance.Column(db_instance.String(50))
        license_number = db_instance.Column(db_instance.String(100), index=True)
        license_type = db_instance.Column(db_instance.String(50))  # AGENT/BROKER/BOTH/NONE
        license_status = db_instance.Column(db_instance.String(50))  # ACTIVE/SUSPENDED/REVOKED
        company = db_instance.Column(db_instance.String(200))
        company_code = db_instance.Column(db_instance.String(50))
        role = db_instance.Column(db_instance.String(100))
        employment_history = db_instance.Column(JSONB)  # Array of employment records
        
        # Assessment & Risk Scoring
        risk_level = db_instance.Column(db_instance.String(20), index=True)  # LOW/MEDIUM/HIGH/CRITICAL
        risk_score = db_instance.Column(db_instance.Integer, default=0)  # 0-100
        threat_classification = db_instance.Column(JSONB)  # Array: ["FRAUD", "MISREPRESENTATION", ...]
        watchlist_status = db_instance.Column(db_instance.String(50))  # ACTIVE/MONITORING/CLEARED
        priority_level = db_instance.Column(db_instance.Integer, default=3)  # 1-5 (1=highest)
        assessment_notes = db_instance.Column(db_instance.Text)  # Encrypted sensitive notes
        
        # Intelligence Statistics (Auto-updated by triggers)
        total_mentions = db_instance.Column(db_instance.Integer, default=0)
        email_count = db_instance.Column(db_instance.Integer, default=0)
        whatsapp_count = db_instance.Column(db_instance.Integer, default=0)
        patrol_count = db_instance.Column(db_instance.Integer, default=0)
        surveillance_count = db_instance.Column(db_instance.Integer, default=0)
        case_count = db_instance.Column(db_instance.Integer, default=0)
        first_mentioned_date = db_instance.Column(db_instance.DateTime)
        last_mentioned_date = db_instance.Column(db_instance.DateTime)
        last_activity_date = db_instance.Column(db_instance.DateTime, index=True)
        
        # Misconduct Tracking
        alleged_misconducts = db_instance.Column(JSONB)  # Array of allegation types
        proven_violations = db_instance.Column(JSONB)  # Array of substantiated violations
        investigation_count = db_instance.Column(db_instance.Integer, default=0)
        substantiated_count = db_instance.Column(db_instance.Integer, default=0)
        unsubstantiated_count = db_instance.Column(db_instance.Integer, default=0)
        
        # Relationship Mapping
        associated_pois = db_instance.Column(JSONB)  # Array of related POI-IDs
        organization_links = db_instance.Column(JSONB)  # Companies/groups involved with
        network_centrality = db_instance.Column(db_instance.Float)  # Graph analysis score (0.0-1.0)
        
        # AI/Automation Metadata
        deduplication_group_id = db_instance.Column(db_instance.String(50))  # For merged entities
        merge_confidence = db_instance.Column(db_instance.Float)  # Similarity score if merged
        auto_enriched = db_instance.Column(db_instance.Boolean, default=False)
        last_enrichment_date = db_instance.Column(db_instance.DateTime)
        data_sources = db_instance.Column(JSONB)  # Array: ["EMAIL-123", "WHATSAPP-45", ...]
        
        # Status & Control
        status = db_instance.Column(db_instance.String(20), default='ACTIVE', index=True)  # ACTIVE/MERGED/ARCHIVED
        merged_into_poi_id = db_instance.Column(db_instance.String(20), db_instance.ForeignKey('alleged_person_profile.poi_id'))
        is_high_priority = db_instance.Column(db_instance.Boolean, default=False)
        requires_approval = db_instance.Column(db_instance.Boolean, default=False)
        approved_by = db_instance.Column(db_instance.String(100))
        approved_at = db_instance.Column(db_instance.DateTime)
        
        # Audit Trail
        created_by = db_instance.Column(db_instance.String(100))
        created_at = db_instance.Column(db_instance.DateTime, default=datetime.utcnow)
        updated_by = db_instance.Column(db_instance.String(100))
        updated_at = db_instance.Column(db_instance.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        last_reviewed_date = db_instance.Column(db_instance.DateTime)
        
        # Relationships
        intelligence_links = db_instance.relationship('_POIIntelligenceLink', backref='poi_profile', lazy='dynamic', cascade='all, delete-orphan')
        # TEMPORARILY DISABLED: assessment_history relationship causes errors because table schema doesn't match model
        # Re-enable once poi_assessment_history table is properly created with all columns
        # assessment_history = db_instance.relationship('_POIAssessmentHistory', backref='poi_profile', lazy='dynamic', cascade='all, delete-orphan')
        
        def __repr__(self):
            return f'<POI {self.poi_id}: {self.name_english or self.name_chinese}>'
        
        def to_dict(self):
            """Convert to dictionary for JSON serialization"""
            return {
                'id': self.id,  # ✅ CRITICAL: Add database ID for merge logic
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


    class _POIIntelligenceLink(db_instance.Model):
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
        id = db_instance.Column(db_instance.Integer, primary_key=True)
        
        # Link References
        poi_id = db_instance.Column(db_instance.String(20), db_instance.ForeignKey('alleged_person_profile.poi_id', ondelete='CASCADE'), nullable=False, index=True)
        case_profile_id = db_instance.Column(db_instance.Integer, db_instance.ForeignKey('case_profile.id', ondelete='CASCADE'), nullable=False, index=True)
        
        # Source Reference (Polymorphic)
        source_type = db_instance.Column(db_instance.String(20), nullable=False, index=True)  # EMAIL/WHATSAPP/PATROL/SURVEILLANCE
        source_id = db_instance.Column(db_instance.Integer, nullable=False, index=True)  # ID of the source record
        
        # Extraction metadata
        extraction_method = db_instance.Column(db_instance.String(20))  # Method used to extract the link
        
        # Metadata columns - ONLY columns that exist in actual database schema
        # Actual database has: id, poi_id, case_profile_id, source_type, source_id, 
        # extraction_method, confidence_score, created_at
        # NOTE: created_by and updated_at DO NOT EXIST in database - removed to prevent errors
        
        confidence_score = db_instance.Column(db_instance.Float)  # 0.0-1.0
        created_at = db_instance.Column(db_instance.DateTime, default=datetime.utcnow)
        
        # Unique constraint: one POI per source record
        __table_args__ = (
            db_instance.UniqueConstraint('poi_id', 'source_type', 'source_id', name='unique_poi_source'),
            db_instance.Index('idx_poi_link_source', 'source_type', 'source_id'),
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
                'confidence_score': self.confidence_score,
                'extraction_method': self.extraction_method,
                # 'created_by': self.created_by,  # Column removed from model - see line 193
                'created_at': self.created_at.isoformat() if self.created_at else None
            }


    class _POIExtractionQueue(db_instance.Model):
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
        id = db_instance.Column(db_instance.Integer, primary_key=True)
        
        # Job References
        case_profile_id = db_instance.Column(db_instance.Integer, db_instance.ForeignKey('case_profile.id', ondelete='CASCADE'), nullable=False)
        source_type = db_instance.Column(db_instance.String(20), nullable=False)  # EMAIL/WHATSAPP/PATROL/SURVEILLANCE
        source_id = db_instance.Column(db_instance.Integer, nullable=False)
        
        # Processing Status
        status = db_instance.Column(db_instance.String(20), default='PENDING', index=True)  # PENDING/PROCESSING/COMPLETE/FAILED/NEEDS_REVIEW
        priority = db_instance.Column(db_instance.Integer, default=3, index=True)  # 1-5 (1=highest)
        queued_at = db_instance.Column(db_instance.DateTime, default=datetime.utcnow, index=True)
        processing_started_at = db_instance.Column(db_instance.DateTime)
        completed_at = db_instance.Column(db_instance.DateTime)
        assigned_to = db_instance.Column(db_instance.String(100))  # Worker ID/Username
        
        # Extraction Results
        extracted_entities = db_instance.Column(JSONB)  # Raw AI output: [{name, confidence, context}, ...]
        extraction_method = db_instance.Column(db_instance.String(50))  # AI model/tool used
        extraction_confidence = db_instance.Column(db_instance.Float)  # Average confidence score
        entities_found_count = db_instance.Column(db_instance.Integer, default=0)
        matched_existing_pois = db_instance.Column(JSONB)  # Array of POI-IDs matched
        
        # Quality Check
        requires_manual_review = db_instance.Column(db_instance.Boolean, default=False, index=True)
        review_reason = db_instance.Column(db_instance.String(200))  # "Low confidence", "Conflict", etc.
        reviewed_by = db_instance.Column(db_instance.String(100))
        reviewed_at = db_instance.Column(db_instance.DateTime)
        review_notes = db_instance.Column(db_instance.Text)
        
        # Error Handling
        error_message = db_instance.Column(db_instance.Text)
        retry_count = db_instance.Column(db_instance.Integer, default=0)
        last_error_at = db_instance.Column(db_instance.DateTime)
        max_retries = db_instance.Column(db_instance.Integer, default=3)
        
        # Unique constraint: one extraction job per source
        __table_args__ = (
            db_instance.UniqueConstraint('source_type', 'source_id', name='unique_extraction_source'),
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


    class _POIAssessmentHistory(db_instance.Model):
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
        id = db_instance.Column(db_instance.Integer, primary_key=True)
        
        # Assessment References
        poi_id = db_instance.Column(db_instance.String(20), db_instance.ForeignKey('alleged_person_profile.poi_id', ondelete='CASCADE'), nullable=False, index=True)
        assessed_by = db_instance.Column(db_instance.String(100), nullable=False)
        assessment_date = db_instance.Column(db_instance.DateTime, default=datetime.utcnow, index=True)
        
        # Assessment Changes
        # NOTE: Commented out columns that don't exist in database yet
        # Uncomment when poi_assessment_history table is properly created
        previous_risk_level = db_instance.Column(db_instance.String(20))
        new_risk_level = db_instance.Column(db_instance.String(20))
        # previous_risk_score = db_instance.Column(db_instance.Integer)  # ❌ Not in DB
        # new_risk_score = db_instance.Column(db_instance.Integer)  # ❌ Not in DB
        # assessment_reason = db_instance.Column(db_instance.Text)  # ❌ Not in DB
        # supporting_evidence = db_instance.Column(JSONB)  # ❌ Not in DB
        # assessment_notes = db_instance.Column(db_instance.Text)  # ❌ Not in DB
        
        # Related Intelligence
        # related_case_profiles = db_instance.Column(JSONB)  # ❌ Not in DB
        # trigger_source_type = db_instance.Column(db_instance.String(20))  # ❌ Not in DB
        # trigger_source_id = db_instance.Column(db_instance.Integer)  # ❌ Not in DB
        
        def __repr__(self):
            return f'<Assessment {self.poi_id}: {self.previous_risk_level}→{self.new_risk_level}>'
        
        def to_dict(self):
            """Convert to dictionary for JSON serialization"""
            # NOTE: Only include columns that exist in database
            # Columns like previous_risk_score, new_risk_score, assessment_reason
            # are commented out in model definition (see lines 316-327)
            return {
                'id': self.id,
                'poi_id': self.poi_id,
                'assessed_by': self.assessed_by,
                'assessment_date': self.assessment_date.isoformat() if self.assessment_date else None,
                'previous_risk_level': self.previous_risk_level,
                'new_risk_level': self.new_risk_level
                # 'previous_risk_score': self.previous_risk_score,  # ❌ Not in DB
                # 'new_risk_score': self.new_risk_score,            # ❌ Not in DB
                # 'assessment_reason': self.assessment_reason       # ❌ Not in DB
            }


    # ✅ BACKWARD COMPATIBILITY: Legacy Email-POI linking table
    class _EmailAllegedPersonLink(db_instance.Model):
        """
        Many-to-many relationship between emails and alleged persons (POI v1.0 compatibility)
        
        NOTE: This is the legacy linking table. New code should use POIIntelligenceLink.
        This is kept for backward compatibility with existing code that queries this table.
        """
        __tablename__ = 'email_alleged_person_link'
        
        id = db_instance.Column(db_instance.Integer, primary_key=True)
        email_id = db_instance.Column(db_instance.Integer, db_instance.ForeignKey('email.id'), nullable=False)
        alleged_person_id = db_instance.Column(db_instance.Integer, db_instance.ForeignKey('alleged_person_profile.id'), nullable=False)
        
        # Link metadata
        created_at = db_instance.Column(db_instance.DateTime, nullable=False, default=datetime.utcnow)
        created_by = db_instance.Column(db_instance.String(100))  # AI_ANALYSIS, MANUAL_INPUT
        confidence = db_instance.Column(db_instance.Float)  # AI confidence score (0.0 to 1.0)
        
        # Relationships - using direct class references (not strings) since classes are in same file
        # Note: Email is in app1_production.py, so we use string reference
        email = db_instance.relationship('Email', backref='alleged_person_links')
        alleged_person = db_instance.relationship('_AllegedPersonProfile', backref='email_links')
        
        # Ensure unique email-person combinations
        __table_args__ = (db_instance.UniqueConstraint('email_id', 'alleged_person_id', name='unique_email_person_link'),)
        
        def __repr__(self):
            return f'<EmailAllegedPersonLink email_id={self.email_id} person_id={self.alleged_person_id}>'

    
    # Set global references
    AllegedPersonProfile = _AllegedPersonProfile
    POIIntelligenceLink = _POIIntelligenceLink
    EmailAllegedPersonLink = _EmailAllegedPersonLink
    POIExtractionQueue = _POIExtractionQueue
    POIAssessmentHistory = _POIAssessmentHistory
    
    print(f"[POI MODELS] ✅ Factory init_models() completed successfully")
    print(f"[POI MODELS] 📦 Created classes: {AllegedPersonProfile.__name__}, {POIIntelligenceLink.__name__}, {EmailAllegedPersonLink.__name__}")
    
    return {
        'AllegedPersonProfile': AllegedPersonProfile,
        'POIIntelligenceLink': POIIntelligenceLink,
        'EmailAllegedPersonLink': EmailAllegedPersonLink,
        'POIExtractionQueue': POIExtractionQueue,
        'POIAssessmentHistory': POIAssessmentHistory
    }
