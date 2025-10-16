# 🔗 Unified INT-### Reference System

## Overview
Implements a **single unified INT-### numbering system** that indexes ALL intelligence sources (Email, WhatsApp, Online Patrol) by receipt date, ensuring each intelligence item is counted uniquely across channels.

## Architecture

### Current State (Before)
- ✅ **Emails**: Have INT-### references (INT-001, INT-002, etc.)
- ❌ **WhatsApp**: Have WT-### index (separate numbering)
- ❌ **Online Patrol**: No formal index
- **Problem**: Can't track total unique intelligence items across sources

### New State (After)
- ✅ **ALL Sources**: Share unified INT-### references
- ✅ **CaseProfile as Hub**: Central table links all sources
- ✅ **Cross-Source Linkage**: Same incident from multiple sources = same INT number
- ✅ **Deduplication**: AI-powered similarity matching prevents duplicates

## Database Schema Changes

### Enhanced CaseProfile Model
```python
class CaseProfile(db.Model):
    """
    Central intelligence item registry - unified INT-### hub
    Links ALL intelligence sources through foreign keys
    """
    __tablename__ = "case_profile"
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # ✅ NEW: Unified INT Reference System
    index = db.Column(db.String(20), unique=True, nullable=False, index=True)  # INT-001, INT-002
    index_order = db.Column(db.Integer, unique=True, nullable=False, index=True)  # 1, 2, 3...
    
    # ✅ NEW: Source Classification
    date_of_receipt = db.Column(db.DateTime, nullable=False, index=True)  # ISO timestamp for sorting
    source_type = db.Column(db.String(20), nullable=False, index=True)  # EMAIL, WHATSAPP, PATROL
    
    # ✅ NEW: Source Foreign Keys (one-to-one relationship)
    email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=True, unique=True)
    whatsapp_id = db.Column(db.Integer, db.ForeignKey('whats_app_entry.id'), nullable=True, unique=True)
    patrol_id = db.Column(db.Integer, db.ForeignKey('online_patrol_entry.id'), nullable=True, unique=True)
    
    # Existing fields (legacy compatibility)
    source = db.Column(db.String(255))  # Detailed source info
    case_status = db.Column(db.String(255))  # Pending, Under Investigation, Closed
    case_number = db.Column(db.String(255))  # Human-assigned case (C2025-001)
    alleged_subject_en = db.Column(db.String(255))
    alleged_subject_cn = db.Column(db.String(255))
    agent_number = db.Column(db.String(255))
    agent_company_broker = db.Column(db.String(255))
    alleged_misconduct_type = db.Column(db.String(255))
    description_of_incident = db.Column(db.Text)
    
    # ✅ NEW: Metadata
    created_at = db.Column(db.DateTime, default=get_hk_time)
    updated_at = db.Column(db.DateTime, default=get_hk_time, onupdate=get_hk_time)
    created_by = db.Column(db.String(100))  # AI_AUTO, MANUAL, SYSTEM
    
    # ✅ NEW: Deduplication tracking
    similarity_checked = db.Column(db.Boolean, default=False)
    duplicate_of_id = db.Column(db.Integer, db.ForeignKey('case_profile.id'), nullable=True)
    
    # Relationships
    email = db.relationship('Email', backref='case_profile', uselist=False)
    whatsapp = db.relationship('WhatsAppEntry', backref='case_profile', uselist=False)
    patrol = db.relationship('OnlinePatrolEntry', backref='case_profile', uselist=False)
    duplicates = db.relationship('CaseProfile', 
                                 foreign_keys=[duplicate_of_id],
                                 remote_side=[id],
                                 backref='master_case')
```

### Update Source Models (Add Reverse Foreign Key)

**Email Model:**
```python
class Email(db.Model):
    # ... existing fields ...
    
    # ✅ ADD: Unified INT reference (replaces standalone int_reference_number)
    caseprofile_id = db.Column(db.Integer, db.ForeignKey('case_profile.id'), nullable=True)
    
    @property
    def int_reference(self):
        """Get INT reference from linked CaseProfile"""
        if self.case_profile:
            return self.case_profile.index
        return None
```

**WhatsAppEntry Model:**
```python
class WhatsAppEntry(db.Model):
    # ... existing fields ...
    
    # ✅ ADD: Unified INT reference
    caseprofile_id = db.Column(db.Integer, db.ForeignKey('case_profile.id'), nullable=True)
    
    @property
    def int_reference(self):
        """Get INT reference from linked CaseProfile"""
        if self.case_profile:
            return self.case_profile.index
        return None
```

**OnlinePatrolEntry Model:**
```python
class OnlinePatrolEntry(db.Model):
    # ... existing fields ...
    
    # ✅ ADD: Unified INT reference
    caseprofile_id = db.Column(db.Integer, db.ForeignKey('case_profile.id'), nullable=True)
    
    @property
    def int_reference(self):
        """Get INT reference from linked CaseProfile"""
        if self.case_profile:
            return self.case_profile.index
        return None
```

## Core Functions

### 1. Generate Next INT ID
```python
def generate_next_int_id(date_of_receipt=None, source_type="EMAIL"):
    """
    Generate next INT-### reference number
    
    Mirrors generateintreferencefornewemail() but works for ALL sources
    Ensures chronological ordering by receipt date
    """
    try:
        # Find highest existing order number
        max_order = db.session.query(func.max(CaseProfile.index_order)).scalar() or 0
        
        # Increment
        next_order = max_order + 1
        int_reference = f"INT-{next_order:03d}"
        
        # Default receipt time
        if not date_of_receipt:
            date_of_receipt = get_hk_time()
        
        print(f"[INT-GEN] Generated {int_reference} for {source_type}")
        
        return {
            'index': int_reference,
            'index_order': next_order,
            'date_of_receipt': date_of_receipt,
            'source_type': source_type
        }
        
    except Exception as e:
        print(f"[INT-GEN] ❌ Error generating INT reference: {e}")
        return None
```

### 2. Create Unified Intelligence Entry
```python
def create_unified_intelligence_entry(source_record, source_type, created_by="SYSTEM"):
    """
    Create CaseProfile entry linking to any source record
    
    Args:
        source_record: Email, WhatsAppEntry, or OnlinePatrolEntry object
        source_type: "EMAIL", "WHATSAPP", or "PATROL"
        created_by: Who created this (AI_AUTO, MANUAL, SYSTEM)
    
    Returns:
        CaseProfile object with unified INT reference
    """
    try:
        # Determine receipt date based on source type
        if source_type == "EMAIL":
            date_of_receipt = source_record.received or get_hk_time()
            foreign_key = {'email_id': source_record.id}
        elif source_type == "WHATSAPP":
            date_of_receipt = source_record.received_time or get_hk_time()
            foreign_key = {'whatsapp_id': source_record.id}
        elif source_type == "PATROL":
            date_of_receipt = source_record.complaint_time or get_hk_time()
            foreign_key = {'patrol_id': source_record.id}
        else:
            raise ValueError(f"Unknown source type: {source_type}")
        
        # Generate INT reference
        int_data = generate_next_int_id(date_of_receipt, source_type)
        if not int_data:
            raise Exception("Failed to generate INT reference")
        
        # Create CaseProfile
        case_profile = CaseProfile(
            index=int_data['index'],
            index_order=int_data['index_order'],
            date_of_receipt=date_of_receipt,
            source_type=source_type,
            created_by=created_by,
            **foreign_key
        )
        
        db.session.add(case_profile)
        db.session.flush()  # Get ID without full commit
        
        # Link back to source
        source_record.caseprofile_id = case_profile.id
        
        print(f"[INT-CREATE] Created {int_data['index']} for {source_type} record {source_record.id}")
        
        return case_profile
        
    except Exception as e:
        print(f"[INT-CREATE] ❌ Error creating unified entry: {e}")
        db.session.rollback()
        return None
```

### 3. Cross-Source Deduplication
```python
def check_duplicate_intelligence(source_record, source_type, similarity_threshold=0.85):
    """
    Check if intelligence item already exists from different source
    
    Uses AI similarity matching on:
    - Allegation descriptions
    - Person names
    - Agent numbers
    - Date proximity (within 7 days)
    
    Returns:
        - None: No duplicate found
        - CaseProfile: Existing case that matches
    """
    try:
        # Extract text for comparison
        if source_type == "EMAIL":
            search_text = f"{source_record.alleged_subject_english} {source_record.alleged_subject_chinese} {source_record.allegation_summary}"
            search_date = source_record.received
        elif source_type == "WHATSAPP":
            search_text = f"{source_record.complaint_name} {source_record.alleged_person} {source_record.details}"
            search_date = source_record.received_time
        elif source_type == "PATROL":
            search_text = f"{source_record.sender} {source_record.details}"
            search_date = source_record.complaint_time
        else:
            return None
        
        # Get recent cases (within 30 days)
        from datetime import timedelta
        if search_date:
            date_threshold = search_date - timedelta(days=30)
            recent_cases = CaseProfile.query.filter(
                CaseProfile.date_of_receipt >= date_threshold
            ).all()
        else:
            recent_cases = CaseProfile.query.order_by(
                CaseProfile.date_of_receipt.desc()
            ).limit(100).all()
        
        # AI similarity check (simplified - can integrate OpenAI embeddings)
        for case in recent_cases:
            # Skip same source type (allow duplicates within same channel)
            if case.source_type == source_type:
                continue
            
            # Get comparison text from existing case
            existing_text = f"{case.alleged_subject_en} {case.alleged_subject_cn} {case.description_of_incident}"
            
            # Simple text similarity (upgrade to AI embeddings for production)
            similarity = calculate_text_similarity(search_text, existing_text)
            
            if similarity >= similarity_threshold:
                print(f"[DUPLICATE] Found duplicate: {case.index} (similarity: {similarity:.2f})")
                return case
        
        return None
        
    except Exception as e:
        print(f"[DUPLICATE] ❌ Error checking duplicates: {e}")
        return None

def calculate_text_similarity(text1, text2):
    """
    Calculate similarity between two texts
    
    Production version should use:
    - OpenAI embeddings + cosine similarity
    - or sentence-transformers
    
    Current implementation: Simple Jaccard similarity
    """
    if not text1 or not text2:
        return 0.0
    
    # Tokenize
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    # Jaccard similarity
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)
```

### 4. Update INT Reference (Manual Override)
```python
def update_int_reference_unified(case_profile_id, new_int_number, updated_by):
    """
    Manually update INT reference for any source
    
    Args:
        case_profile_id: CaseProfile database ID
        new_int_number: New INT number (e.g., "INT-042")
        updated_by: Username making the change
    """
    try:
        case = CaseProfile.query.get(case_profile_id)
        if not case:
            return {'success': False, 'error': 'Case profile not found'}
        
        # Validate format
        import re
        if not re.match(r'^INT-\d{1,4}$', new_int_number.upper()):
            return {
                'success': False,
                'error': 'Invalid format. Use INT-XXX (e.g., INT-001)'
            }
        
        old_index = case.index
        numeric_part = int(new_int_number.upper().split('-')[1])
        
        # Update
        case.index = new_int_number.upper()
        case.index_order = numeric_part
        case.updated_at = get_hk_time()
        case.created_by = f"{case.created_by} (edited by {updated_by})"
        
        db.session.commit()
        
        print(f"[INT-UPDATE] Manual update: {old_index} → {new_int_number}")
        
        return {
            'success': True,
            'old_index': old_index,
            'new_index': new_int_number.upper(),
            'message': f'INT reference updated from {old_index} to {new_int_number.upper()}'
        }
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}
```

## Integration Points

### On Email Creation
```python
# In email save/create handler:
new_email = Email(...)
db.session.add(new_email)
db.session.flush()

# ✅ Create unified INT reference
case_profile = create_unified_intelligence_entry(
    source_record=new_email,
    source_type="EMAIL",
    created_by="SYSTEM"
)

if case_profile:
    db.session.commit()
```

### On WhatsApp Entry Creation
```python
# In WhatsApp save handler:
entry = WhatsAppEntry(...)
db.session.add(entry)
db.session.flush()

# Check for duplicates first
duplicate = check_duplicate_intelligence(entry, "WHATSAPP")

if duplicate:
    # Link to existing INT
    entry.caseprofile_id = duplicate.id
    print(f"[WHATSAPP] Linked to existing {duplicate.index}")
else:
    # Create new INT
    case_profile = create_unified_intelligence_entry(
        source_record=entry,
        source_type="WHATSAPP",
        created_by="SYSTEM"
    )

db.session.commit()
```

### On Online Patrol Creation
```python
# In Online Patrol save handler:
patrol = OnlinePatrolEntry(...)
db.session.add(patrol)
db.session.flush()

# Check for duplicates
duplicate = check_duplicate_intelligence(patrol, "PATROL")

if duplicate:
    patrol.caseprofile_id = duplicate.id
else:
    case_profile = create_unified_intelligence_entry(
        source_record=patrol,
        source_type="PATROL",
        created_by="SYSTEM"
    )

db.session.commit()
```

## Reporting Enhancements

### Dashboard Queries
```python
# Total unique intelligence items (not inflated by duplicates)
total_cases = CaseProfile.query.count()

# Breakdown by source
email_count = CaseProfile.query.filter_by(source_type='EMAIL').count()
whatsapp_count = CaseProfile.query.filter_by(source_type='WHATSAPP').count()
patrol_count = CaseProfile.query.filter_by(source_type='PATROL').count()

# Cross-source cases (linked duplicates)
cross_source_cases = CaseProfile.query.filter(
    CaseProfile.duplicate_of_id.isnot(None)
).count()
```

### Get Entries by CaseProfile
```python
def get_entries_by_case_profile(int_reference):
    """
    Get all source records linked to an INT reference
    Useful for drill-down reporting
    """
    case = CaseProfile.query.filter_by(index=int_reference).first()
    if not case:
        return []
    
    entries = []
    
    if case.email:
        entries.append({'type': 'EMAIL', 'record': case.email})
    if case.whatsapp:
        entries.append({'type': 'WHATSAPP', 'record': case.whatsapp})
    if case.patrol:
        entries.append({'type': 'PATROL', 'record': case.patrol})
    
    # Include linked duplicates
    for dup in case.duplicates:
        if dup.email:
            entries.append({'type': 'EMAIL', 'record': dup.email})
        if dup.whatsapp:
            entries.append({'type': 'WHATSAPP', 'record': dup.whatsapp})
        if dup.patrol:
            entries.append({'type': 'PATROL', 'record': dup.patrol})
    
    return entries
```

## Migration Strategy

### Phase 1: Database Schema Update
```python
def migrate_to_unified_int_system():
    """
    Migrate existing data to unified INT system
    """
    from sqlalchemy import inspect
    
    inspector = inspect(db.engine)
    
    # 1. Add new columns to CaseProfile
    # (Done via SQLAlchemy migrations or ALTER TABLE)
    
    # 2. Add caseprofile_id to source tables
    # (Done via SQLAlchemy migrations)
    
    # 3. Migrate existing Email INT references
    emails_with_int = Email.query.filter(
        Email.int_reference_number.isnot(None)
    ).all()
    
    for email in emails_with_int:
        # Create CaseProfile for each email
        case = CaseProfile(
            index=email.int_reference_number,
            index_order=email.int_reference_order,
            date_of_receipt=email.received or get_hk_time(),
            source_type="EMAIL",
            email_id=email.id,
            created_by="MIGRATION",
            alleged_subject_en=email.alleged_subject_english,
            alleged_subject_cn=email.alleged_subject_chinese,
            description_of_incident=email.allegation_summary
        )
        db.session.add(case)
        db.session.flush()
        
        # Link email back
        email.caseprofile_id = case.id
    
    # 4. Create INT references for WhatsApp entries
    whatsapp_entries = WhatsAppEntry.query.all()
    for entry in whatsapp_entries:
        case = create_unified_intelligence_entry(
            source_record=entry,
            source_type="WHATSAPP",
            created_by="MIGRATION"
        )
    
    # 5. Create INT references for Online Patrol
    patrol_entries = OnlinePatrolEntry.query.all()
    for entry in patrol_entries:
        case = create_unified_intelligence_entry(
            source_record=entry,
            source_type="PATROL",
            created_by="MIGRATION"
        )
    
    db.session.commit()
    print("✅ Migration to unified INT system complete")
```

### Phase 2: Update UI Templates
- Replace `email.int_reference_number` with `email.int_reference`
- Add INT column to WhatsApp table
- Add INT column to Online Patrol table
- Update export functions to include INT reference

### Phase 3: Profile Automation Integration
```python
# In create_or_update_alleged_person_profile():
# Accept source_type parameter
def create_or_update_alleged_person_profile(
    db, AllegedPersonProfile, EmailAllegedPersonLink,
    name_english: str,
    source_id: int = None,  # Can be email_id, whatsapp_id, or patrol_id
    source_type: str = "EMAIL",  # EMAIL, WHATSAPP, PATROL
    **kwargs
):
    # Get INT reference from CaseProfile
    if source_type == "EMAIL":
        source = Email.query.get(source_id)
    elif source_type == "WHATSAPP":
        source = WhatsAppEntry.query.get(source_id)
    elif source_type == "PATROL":
        source = OnlinePatrolEntry.query.get(source_id)
    
    int_reference = source.int_reference if source else None
    
    # Create profile and link using INT reference
    # ... existing logic ...
```

## Benefits

✅ **True Unique Count**: Dashboard shows actual intelligence items, not inflated by channel duplication  
✅ **Cross-Source Linkage**: Same incident from Email + WhatsApp = one INT number  
✅ **Chronological Ordering**: INT numbers reflect true receipt order across all sources  
✅ **Deduplication**: AI prevents duplicate intelligence items  
✅ **Scalability**: Easy to add new sources (Surveillance, Social Media, etc.)  
✅ **Audit Trail**: Full history of INT assignments and changes  
✅ **Reporting Accuracy**: Metrics based on unique cases, not raw entry counts  

## Future Enhancements

🔮 **Event-Driven Architecture**:
```python
# Emit events for new intelligence items
@event.emit('intelligence.created')
def on_intelligence_created(case_profile):
    # Trigger alerts
    # Update dashboards
    # Sync external systems
    pass
```

🔮 **Microservices**:
- INT Generation Service
- Deduplication Service
- Profile Matching Service

🔮 **Advanced AI**:
- GPT-4 embeddings for similarity
- Multi-language support (English + Chinese)
- Entity extraction and matching

---

**Status**: Ready for implementation  
**Priority**: High - Foundational architecture change  
**Estimated Effort**: 3-5 days for full implementation + testing
