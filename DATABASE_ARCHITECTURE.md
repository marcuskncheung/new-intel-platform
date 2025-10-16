# 🎯 Enhanced Intelligence Platform Database Architecture

## Overview

This document describes the comprehensive Person of Interest (POI) tracking system with automated extraction, assessment, and cross-source intelligence linking.

**Version**: 2.0 - Comprehensive POI Architecture  
**Last Updated**: 2025-10-16  
**Database**: PostgreSQL 15.14 (Production)

---

## 🔑 Core Design Principles

1. **Universal POI Linking**: Track POIs across ALL intelligence sources (Email, WhatsApp, Online Patrol, Surveillance)
2. **Automated Extraction**: AI-powered entity extraction with confidence scoring
3. **Deduplication**: Intelligent matching to prevent duplicate POI profiles
4. **Assessment Tracking**: Complete audit trail of risk assessments and changes
5. **Quality Control**: Review workflow for low-confidence extractions

---

## 📊 Database Schema

### 1. **ALLEGED_PERSON_PROFILE** (Enhanced POI Master Table)

**Purpose**: Central repository for all Person of Interest profiles with comprehensive tracking

```python
class AllegedPersonProfile(db.Model):
    """
    Enhanced POI profile with assessment tracking and cross-source statistics
    """
    __tablename__ = 'alleged_person_profile'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    poi_id = db.Column(db.String(20), unique=True, nullable=False)  # POI-001, POI-002...
    
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
    last_activity_date = db.Column(db.DateTime)
    
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
```

**Key Indexes**:
- `poi_id` (unique)
- `name_normalized` (for fuzzy matching)
- `license_number` (for deduplication)
- `risk_level` (for filtering)
- `status` (active/archived)
- `last_activity_date` (for sorting)

---

### 2. **POI_INTELLIGENCE_LINK** (Universal Linking Table)

**Purpose**: Links POIs to ANY intelligence source with extraction metadata

**Replaces**: `EMAIL_ALLEGED_PERSON_LINK` (old single-source system)

```python
class POIIntelligenceLink(db.Model):
    """
    Universal linking table connecting POIs to all intelligence sources
    with extraction metadata and quality control
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
```

**Key Features**:
- **Polymorphic linking**: Works with any source type
- **Confidence scoring**: Track extraction quality
- **Review workflow**: Flag low-confidence for manual check
- **Context preservation**: Store where/how POI was mentioned

---

### 3. **POI_EXTRACTION_QUEUE** (Automation Queue)

**Purpose**: Manages automated POI extraction jobs with retry logic

```python
class POIExtractionQueue(db.Model):
    """
    Queue for automated POI extraction jobs
    Processes intelligence sources to extract and link POIs
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
```

**Workflow**:
1. New intelligence arrives → Auto-queued
2. Worker picks up job → Extracts entities
3. Matches against existing POIs → Links or creates new
4. Low confidence → Flags for review

---

### 4. **POI_ASSESSMENT_HISTORY** (Audit Trail)

**Purpose**: Tracks all changes to POI risk assessments

```python
class POIAssessmentHistory(db.Model):
    """
    Audit trail for POI risk assessments
    Tracks who changed what and why
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
```

**Use Cases**:
- Track risk escalation over time
- Audit trail for compliance
- Analyze assessment patterns
- Support investigations with historical context

---

## 🔄 Data Flow: Automated POI Extraction Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│              AUTOMATED POI EXTRACTION PIPELINE               │
└─────────────────────────────────────────────────────────────┘

1. 📥 Intelligence Input (Email/WhatsApp/Patrol)
         │
         ▼
2. 🤖 Trigger: create_unified_intelligence_entry()
         │
         ├─→ Create CASE_PROFILE (INT-### assigned)
         │
         └─→ Queue POI Extraction
                  │
                  ▼
3. 🔍 AI Entity Extraction Worker
         │
         ├─→ Named Entity Recognition (NER)
         ├─→ Extract: Names, License Numbers, Companies
         ├─→ Confidence Scoring
         └─→ Context Analysis
                  │
                  ▼
4. 🎯 POI Matching & Deduplication
         │
         ├─→ Search existing POI profiles
         ├─→ Fuzzy matching (name normalization)
         ├─→ Check: phone, email, license number
         ├─→ Calculate similarity scores
         │
         ├─→ MATCH FOUND?
         │    │
         │    ├─→ YES: Link to existing POI
         │    │         (update statistics)
         │    │
         │    └─→ NO:  Create new POI profile
         │              (generate POI-###)
         │
         ▼
5. 💾 Create POI_INTELLIGENCE_LINK
         │
         ├─→ Link POI ←→ CASE_PROFILE
         ├─→ Store extraction metadata
         ├─→ Set confidence score
         └─→ Flag for review if low confidence
                  │
                  ▼
6. 📊 Assessment Auto-Population
         │
         ├─→ Extract alleged misconduct type
         ├─→ Update POI statistics
         ├─→ Calculate risk score (if rules defined)
         └─→ Update ALLEGED_PERSON_PROFILE
                  │
                  ▼
7. ✅ Quality Control
         │
         ├─→ High confidence (>0.85): Auto-approve
         ├─→ Medium (0.60-0.85): Flag for review
         └─→ Low (<0.60): Require manual verification
                  │
                  ▼
8. 📋 Update Alleged Subject List
         │
         └─→ POI profile appears in dashboard
             with assessment details
```

---

## 🗄️ Database Relationships

```
                    ┌─────────────────────┐
                    │   CASE_PROFILE      │
                    │   (INT-### System)  │
                    └──────────┬──────────┘
                               │
                               │ One-to-Many
                               ▼
        ┌──────────────────────────────────────────┐
        │      POI_INTELLIGENCE_LINK               │
        │  Links POI to ANY intelligence source    │
        └──────────────┬───────────────────────────┘
                       │
                       │ Many-to-One
                       ▼
        ┌──────────────────────────────────────────┐
        │     ALLEGED_PERSON_PROFILE               │
        │          (POI-### System)                 │
        └──────────────┬───────────────────────────┘
                       │
                       ├─→ One-to-Many → POI_ASSESSMENT_HISTORY
                       │
                       └─→ Self-Reference → Merged POIs
                       
        ┌──────────────────────────────────────────┐
        │      POI_EXTRACTION_QUEUE                │
        │   (Automated extraction jobs)             │
        └──────────────────────────────────────────┘
```

---

## 🚀 Implementation Phases

### Phase 1: Database Schema (Week 1)

**Tasks**:
1. Create migration script for new tables
2. Add new columns to `alleged_person_profile`
3. Create `poi_intelligence_link` table
4. Create `poi_extraction_queue` table
5. Create `poi_assessment_history` table
6. Add database triggers for auto-updates

**Deliverables**:
- `migrations/add_poi_comprehensive_system.py`
- Database backup before migration
- Rollback script

---

### Phase 2: Data Migration (Week 1-2)

**Tasks**:
1. Migrate existing `EMAIL_ALLEGED_PERSON_LINK` data
2. Populate `poi_intelligence_link` from legacy links
3. Generate initial POI statistics
4. Validate data integrity

**SQL Migration Script**:
```sql
-- Migrate EMAIL_ALLEGED_PERSON_LINK → POI_INTELLIGENCE_LINK
INSERT INTO poi_intelligence_link (
    poi_id, case_profile_id, source_type, source_id, 
    extraction_method, confidence_score, extraction_timestamp,
    validation_status
)
SELECT 
    ap.poi_id,
    e.caseprofile_id,
    'EMAIL' as source_type,
    eapl.email_id as source_id,
    'MANUAL' as extraction_method,
    COALESCE(eapl.confidence, 1.0) as confidence_score,
    NOW() as extraction_timestamp,
    'VERIFIED' as validation_status
FROM email_alleged_person_link eapl
JOIN alleged_person_profile ap ON eapl.alleged_person_id = ap.id
JOIN email e ON eapl.email_id = e.id
WHERE e.caseprofile_id IS NOT NULL;
```

---

### Phase 3: Core Functions (Week 2)

**Tasks**:
1. Implement POI extraction worker
2. Build fuzzy matching algorithm
3. Create deduplication logic
4. Implement confidence scoring
5. Build review dashboard

**Key Functions**:
```python
def extract_pois_from_intelligence(case_profile_id, source_type, source_id):
    """Extract POIs from intelligence source using NER"""
    pass

def find_matching_poi(name, license_number=None, phone=None):
    """Find existing POI by fuzzy matching"""
    pass

def create_or_link_poi(extracted_entity, case_profile_id, source_info):
    """Create new POI or link to existing"""
    pass

def calculate_risk_score(poi_id):
    """Calculate risk score based on intelligence patterns"""
    pass
```

---

### Phase 4: UI Development (Week 3-4)

**Tasks**:
1. Enhanced POI profile page with statistics
2. Review dashboard for low-confidence extractions
3. Assessment history visualization
4. Risk scoring interface
5. POI network visualization

**UI Components**:
- POI detail page with cross-source intelligence
- Assessment timeline
- Related POIs graph
- Risk score calculator
- Manual extraction form

---

### Phase 5: Testing & Deployment (Week 4)

**Tasks**:
1. Unit tests for extraction logic
2. Integration tests for end-to-end flow
3. Performance testing with large datasets
4. User acceptance testing
5. Production deployment

---

## 📈 Key Benefits

✅ **Universal POI tracking** across all intelligence sources (not just email)

✅ **Automated extraction** with confidence scoring and validation workflow

✅ **Rich assessment data** with risk scoring and historical tracking

✅ **Deduplication support** to unify multiple mentions of same person

✅ **Quality control** with review flags for low-confidence extractions

✅ **Audit trail** for all POI assessments and updates

✅ **Scalable architecture** supporting future intelligence sources (surveillance, etc.)

✅ **Compliance ready** with full audit logging and encryption support

---

## 🔧 Database Triggers & Functions

### Trigger 1: Auto-queue POI extraction on new intelligence

```sql
CREATE OR REPLACE FUNCTION auto_queue_poi_extraction()
RETURNS TRIGGER AS $$
BEGIN
    -- Queue extraction job for new intelligence
    INSERT INTO poi_extraction_queue (
        case_profile_id,
        source_type,
        source_id,
        status,
        priority
    ) VALUES (
        NEW.id,
        NEW.source_type,
        COALESCE(NEW.email_id, NEW.whatsapp_id, NEW.patrol_id),
        'PENDING',
        CASE 
            WHEN NEW.source_type = 'WHATSAPP' THEN 1  -- Highest priority
            WHEN NEW.source_type = 'EMAIL' THEN 2
            WHEN NEW.source_type = 'PATROL' THEN 3
            ELSE 4
        END
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_queue_poi_extraction
    AFTER INSERT ON case_profile
    FOR EACH ROW
    EXECUTE FUNCTION auto_queue_poi_extraction();
```

### Trigger 2: Update POI statistics on new link

```sql
CREATE OR REPLACE FUNCTION update_poi_statistics()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE alleged_person_profile
    SET 
        total_mentions = total_mentions + 1,
        email_count = email_count + CASE WHEN NEW.source_type = 'EMAIL' THEN 1 ELSE 0 END,
        whatsapp_count = whatsapp_count + CASE WHEN NEW.source_type = 'WHATSAPP' THEN 1 ELSE 0 END,
        patrol_count = patrol_count + CASE WHEN NEW.source_type = 'PATROL' THEN 1 ELSE 0 END,
        surveillance_count = surveillance_count + CASE WHEN NEW.source_type = 'SURVEILLANCE' THEN 1 ELSE 0 END,
        last_mentioned_date = NOW(),
        last_activity_date = NOW(),
        updated_at = NOW()
    WHERE poi_id = NEW.poi_id;
    
    -- Update case count if new case
    UPDATE alleged_person_profile ap
    SET case_count = (
        SELECT COUNT(DISTINCT case_profile_id) 
        FROM poi_intelligence_link 
        WHERE poi_id = NEW.poi_id
    )
    WHERE ap.poi_id = NEW.poi_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_poi_statistics
    AFTER INSERT ON poi_intelligence_link
    FOR EACH ROW
    EXECUTE FUNCTION update_poi_statistics();
```

### Trigger 3: Log assessment changes

```sql
CREATE OR REPLACE FUNCTION log_poi_assessment_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Log risk level/score changes
    IF (OLD.risk_level IS DISTINCT FROM NEW.risk_level) OR 
       (OLD.risk_score IS DISTINCT FROM NEW.risk_score) THEN
        INSERT INTO poi_assessment_history (
            poi_id,
            assessed_by,
            previous_risk_level,
            new_risk_level,
            previous_risk_score,
            new_risk_score,
            assessment_date
        ) VALUES (
            NEW.poi_id,
            NEW.updated_by,
            OLD.risk_level,
            NEW.risk_level,
            OLD.risk_score,
            NEW.risk_score,
            NOW()
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_poi_assessment_change
    AFTER UPDATE ON alleged_person_profile
    FOR EACH ROW
    EXECUTE FUNCTION log_poi_assessment_change();
```

---

## 📝 Implementation Notes

### Security Considerations
- **Encryption**: All sensitive data (ID numbers, assessment notes) encrypted at application level
- **Access Control**: Row-level security for multi-user scenarios
- **Audit Logging**: All POI access logged with user ID and timestamp
- **Data Retention**: Archived POIs retained for 7 years per compliance

### Performance Optimization
- **Indexes**: Strategic indexes on frequently queried fields
- **Caching**: Redis cache for frequently accessed POI profiles
- **Batch Processing**: Queue workers process in batches of 50
- **Asynchronous**: Long-running extractions run in background

### Scalability
- **Partitioning**: Consider table partitioning for `poi_assessment_history` by year
- **Archive Strategy**: Move inactive POIs to archive table after 2 years
- **Read Replicas**: Use PostgreSQL read replicas for reporting queries

---

## 🎓 Usage Examples

### Example 1: Manual POI Creation

```python
# Create new POI profile manually
new_poi = AllegedPersonProfile(
    poi_id=generate_next_poi_id(),  # POI-042
    name_english="John Doe",
    name_normalized="johndoe",
    license_number="A123456",
    license_type="AGENT",
    license_status="ACTIVE",
    company="ABC Insurance",
    risk_level="MEDIUM",
    risk_score=50,
    created_by="admin@example.com"
)
db.session.add(new_poi)
db.session.commit()
```

### Example 2: Link POI to Intelligence

```python
# Link POI to email intelligence
link = POIIntelligenceLink(
    poi_id="POI-042",
    case_profile_id=case_profile.id,
    source_type="EMAIL",
    source_id=email.id,
    source_table="email",
    extraction_method="MANUAL",
    confidence_score=1.0,
    role_in_case="SUBJECT",
    is_primary_subject=True,
    validation_status="VERIFIED"
)
db.session.add(link)
db.session.commit()
```

### Example 3: Query POI Cross-Source Intelligence

```python
# Get all intelligence linked to a POI
poi = AllegedPersonProfile.query.filter_by(poi_id="POI-042").first()

# Get all linked intelligence with sources
intelligence = db.session.query(
    POIIntelligenceLink, CaseProfile
).join(
    CaseProfile, POIIntelligenceLink.case_profile_id == CaseProfile.id
).filter(
    POIIntelligenceLink.poi_id == poi.poi_id
).order_by(
    CaseProfile.date_of_receipt.desc()
).all()

# Statistics
print(f"Total mentions: {poi.total_mentions}")
print(f"Email: {poi.email_count}, WhatsApp: {poi.whatsapp_count}, Patrol: {poi.patrol_count}")
```

---

## 📚 Next Steps

1. **Review and approve** this architecture document
2. **Create detailed technical specifications** for each phase
3. **Set up development environment** with test database
4. **Begin Phase 1** implementation (database schema)
5. **Schedule weekly progress reviews**

---

**Document Status**: ✅ Ready for Review  
**Estimated Implementation Time**: 4-6 weeks  
**Priority**: HIGH - Foundational for future enhancements
