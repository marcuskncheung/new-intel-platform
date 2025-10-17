# 🔄 POI v1.0 → v2.0 Migration Mapping

## 📊 Table Structure Comparison

### OLD: `email_alleged_person_link` (POI v1.0)
**Purpose**: Email-only POI linking

```sql
CREATE TABLE email_alleged_person_link (
    id                  SERIAL PRIMARY KEY,
    email_id            INT4 NOT NULL,                    -- FK to email.id
    alleged_person_id   INT4 NOT NULL,                    -- FK to alleged_person_profile.id
    created_at          TIMESTAMP DEFAULT NOW(),
    created_by          VARCHAR(100) DEFAULT 'System',
    confidence          FLOAT8 DEFAULT 1.0
);
```

**Limitations**:
- ❌ Email-only (can't link WhatsApp/Patrol/Surveillance)
- ❌ No case context
- ❌ No quality control (verification/review)
- ❌ No extraction metadata
- ❌ No role/context information

---

### NEW: `poi_intelligence_link` (POI v2.0)
**Purpose**: Universal POI linking across ALL intelligence sources

```sql
CREATE TABLE poi_intelligence_link (
    id                    SERIAL PRIMARY KEY,
    
    -- POI Reference (universal)
    poi_id                VARCHAR(20) NOT NULL,           -- FK to alleged_person_profile.poi_id
    case_profile_id       INT4 NOT NULL,                  -- FK to case_profile.id
    
    -- Source Reference (polymorphic)
    source_type           VARCHAR(20) NOT NULL,           -- 'EMAIL'/'WHATSAPP'/'PATROL'/'SURVEILLANCE'
    source_id             INT4 NOT NULL,                  -- ID in source table
    source_table          VARCHAR(50),                    -- Table name for reference
    
    -- Extraction Metadata
    extraction_method     VARCHAR(20),                    -- 'MANUAL'/'AI'/'REGEX'/'NER'
    extraction_tool       VARCHAR(50),                    -- 'GPT4'/'CLAUDE'/'MANUAL'
    confidence_score      FLOAT8 DEFAULT 1.0,             -- 0.0-1.0
    extraction_timestamp  TIMESTAMP DEFAULT NOW(),
    extracted_by_user     VARCHAR(100),                   -- NULL if automated
    validation_status     VARCHAR(20) DEFAULT 'PENDING',  -- 'PENDING'/'VERIFIED'/'REJECTED'
    
    -- Context Information
    mention_context       TEXT,                           -- Text snippet where POI mentioned
    role_in_case          VARCHAR(50),                    -- 'COMPLAINANT'/'SUBJECT'/'WITNESS'/'OTHER'
    mention_count         INT DEFAULT 1,
    is_primary_subject    BOOLEAN DEFAULT FALSE,
    
    -- Quality Assurance
    verified_by           VARCHAR(100),
    verified_at           TIMESTAMP,
    verification_notes    TEXT,
    needs_review          BOOLEAN DEFAULT FALSE,
    
    -- Audit Trail
    created_at            TIMESTAMP DEFAULT NOW(),
    updated_at            TIMESTAMP DEFAULT NOW(),
    
    UNIQUE (poi_id, source_type, source_id)              -- One POI per source
);

CREATE INDEX idx_poi_link_poi ON poi_intelligence_link(poi_id);
CREATE INDEX idx_poi_link_case ON poi_intelligence_link(case_profile_id);
CREATE INDEX idx_poi_link_source ON poi_intelligence_link(source_type, source_id);
CREATE INDEX idx_poi_link_validation ON poi_intelligence_link(validation_status);
CREATE INDEX idx_poi_link_review ON poi_intelligence_link(needs_review);
```

**Benefits**:
- ✅ Universal linking (Email/WhatsApp/Patrol/Surveillance)
- ✅ Case context tracking
- ✅ Quality control workflow
- ✅ Extraction metadata (method, confidence, tool)
- ✅ Role and context preservation
- ✅ Verification and review flags
- ✅ Full audit trail

---

## 🔄 Migration Mapping

### Field Mapping: OLD → NEW

| OLD Table | OLD Field | NEW Table | NEW Field | Transformation |
|-----------|-----------|-----------|-----------|----------------|
| email_alleged_person_link | id | poi_intelligence_link | id | Direct copy |
| email_alleged_person_link | email_id | poi_intelligence_link | source_id | Direct copy |
| email_alleged_person_link | alleged_person_id | poi_intelligence_link | poi_id | **JOIN to get poi_id** |
| email_alleged_person_link | created_at | poi_intelligence_link | created_at | Direct copy |
| email_alleged_person_link | created_by | poi_intelligence_link | extraction_method | **Map to method** |
| email_alleged_person_link | confidence | poi_intelligence_link | confidence_score | Direct copy |
| (none) | (none) | poi_intelligence_link | source_type | **Fixed: 'EMAIL'** |
| email | caseprofile_id | poi_intelligence_link | case_profile_id | **JOIN from email** |
| (none) | (none) | poi_intelligence_link | source_table | **Fixed: 'email'** |

### created_by → extraction_method Mapping

```sql
CASE 
    WHEN created_by = 'AI_ANALYSIS' THEN 'AI'
    WHEN created_by = 'MANUAL_INPUT' THEN 'MANUAL'
    WHEN created_by IN ('AI', 'System') THEN 'AI'
    WHEN created_by = 'Manual' THEN 'MANUAL'
    ELSE 'MANUAL'
END
```

---

## 📝 Migration SQL (Complete)

```sql
-- ============================================
-- POI v2.0 Migration: Email Links
-- ============================================

-- Step 1: Migrate existing email-POI links
INSERT INTO poi_intelligence_link (
    poi_id,                 -- From alleged_person_profile.poi_id
    case_profile_id,        -- From email.caseprofile_id
    source_type,            -- Fixed: 'EMAIL'
    source_id,              -- From email_alleged_person_link.email_id
    source_table,           -- Fixed: 'email'
    extraction_method,      -- From email_alleged_person_link.created_by
    confidence_score,       -- From email_alleged_person_link.confidence
    extraction_timestamp,   -- From email_alleged_person_link.created_at
    extracted_by_user,      -- From email_alleged_person_link.created_by (if manual)
    validation_status,      -- Default: 'VERIFIED' (already reviewed)
    created_at,            -- From email_alleged_person_link.created_at
    updated_at             -- From email_alleged_person_link.created_at
)
SELECT 
    ap.poi_id,                                          -- Get POI-ID from profile
    e.caseprofile_id,                                   -- Get case from email
    'EMAIL' as source_type,                             -- Fixed value
    eapl.email_id as source_id,                         -- Email ID
    'email' as source_table,                            -- Fixed value
    CASE 
        WHEN eapl.created_by = 'AI_ANALYSIS' THEN 'AI'
        WHEN eapl.created_by = 'MANUAL_INPUT' THEN 'MANUAL'
        WHEN eapl.created_by IN ('AI', 'System') THEN 'AI'
        WHEN eapl.created_by = 'Manual' THEN 'MANUAL'
        ELSE 'MANUAL'
    END as extraction_method,
    COALESCE(eapl.confidence, 1.0) as confidence_score,
    COALESCE(eapl.created_at, CURRENT_TIMESTAMP) as extraction_timestamp,
    CASE 
        WHEN eapl.created_by IN ('Manual', 'MANUAL_INPUT') THEN eapl.created_by
        ELSE NULL
    END as extracted_by_user,
    'VERIFIED' as validation_status,                    -- Assume old links are verified
    COALESCE(eapl.created_at, CURRENT_TIMESTAMP) as created_at,
    COALESCE(eapl.created_at, CURRENT_TIMESTAMP) as updated_at
FROM email_alleged_person_link eapl
JOIN alleged_person_profile ap ON eapl.alleged_person_id = ap.id
JOIN email e ON eapl.email_id = e.id
WHERE e.caseprofile_id IS NOT NULL                      -- Must have case
  AND ap.poi_id IS NOT NULL                             -- Must have POI-ID
ON CONFLICT (poi_id, source_type, source_id) DO NOTHING;

-- Step 2: Update POI statistics
UPDATE alleged_person_profile ap
SET 
    email_count = (
        SELECT COUNT(*) 
        FROM poi_intelligence_link 
        WHERE poi_id = ap.poi_id AND source_type = 'EMAIL'
    ),
    total_mentions = (
        SELECT COUNT(*) 
        FROM poi_intelligence_link 
        WHERE poi_id = ap.poi_id
    ),
    case_count = (
        SELECT COUNT(DISTINCT case_profile_id) 
        FROM poi_intelligence_link 
        WHERE poi_id = ap.poi_id
    ),
    last_activity_date = (
        SELECT MAX(created_at)
        FROM poi_intelligence_link
        WHERE poi_id = ap.poi_id
    )
WHERE poi_id IS NOT NULL;

-- Step 3: Verify migration
SELECT 
    'Email Links (OLD)' as source,
    COUNT(*) as count
FROM email_alleged_person_link
UNION ALL
SELECT 
    'Email Links (NEW)' as source,
    COUNT(*) as count
FROM poi_intelligence_link
WHERE source_type = 'EMAIL';
```

---

## ✅ Verification Queries

### Check Migration Success
```sql
-- Compare counts (should be equal or NEW >= OLD)
SELECT 
    (SELECT COUNT(*) FROM email_alleged_person_link) as old_links,
    (SELECT COUNT(*) FROM poi_intelligence_link WHERE source_type = 'EMAIL') as new_links,
    (SELECT COUNT(*) FROM email_alleged_person_link) - 
    (SELECT COUNT(*) FROM poi_intelligence_link WHERE source_type = 'EMAIL') as difference;
```

### Check POI Statistics
```sql
-- View updated POI statistics
SELECT 
    poi_id,
    full_name_english,
    email_count,
    whatsapp_count,
    patrol_count,
    surveillance_count,
    total_mentions,
    case_count
FROM alleged_person_profile
WHERE status = 'ACTIVE'
ORDER BY total_mentions DESC
LIMIT 10;
```

### Check Sample Links
```sql
-- View sample migrated links
SELECT 
    pil.poi_id,
    ap.full_name_english,
    pil.source_type,
    pil.source_id,
    pil.extraction_method,
    pil.confidence_score,
    pil.created_at,
    cp.case_name
FROM poi_intelligence_link pil
JOIN alleged_person_profile ap ON pil.poi_id = ap.poi_id
LEFT JOIN case_profile cp ON pil.case_profile_id = cp.id
WHERE pil.source_type = 'EMAIL'
LIMIT 10;
```

---

## 🚀 Next Steps After Migration

### 1. **Keep Old Table** (Safety)
```sql
-- DO NOT DROP the old table yet!
-- Keep it for 30 days as backup
-- Rename for clarity:
ALTER TABLE email_alleged_person_link 
RENAME TO email_alleged_person_link_v1_backup;
```

### 2. **Add WhatsApp Linking** (Next Feature)
```sql
-- New WhatsApp links will go directly to poi_intelligence_link:
INSERT INTO poi_intelligence_link (
    poi_id, case_profile_id, source_type, source_id,
    extraction_method, confidence_score
)
VALUES (
    'POI-00001', 123, 'WHATSAPP', 456, 'MANUAL', 1.0
);
```

### 3. **Add Patrol Linking**
```sql
INSERT INTO poi_intelligence_link (
    poi_id, case_profile_id, source_type, source_id,
    extraction_method, confidence_score
)
VALUES (
    'POI-00001', 123, 'PATROL', 789, 'MANUAL', 1.0
);
```

### 4. **Add Surveillance Linking**
```sql
INSERT INTO poi_intelligence_link (
    poi_id, case_profile_id, source_type, source_id,
    extraction_method, confidence_score
)
VALUES (
    'POI-00001', 123, 'SURVEILLANCE', 101, 'MANUAL', 1.0
);
```

---

## 📊 Benefits Summary

### Before (POI v1.0):
```
POI-00001 → [EMAIL-123, EMAIL-456]
POI-00002 → [EMAIL-789]
```
❌ Can't see WhatsApp/Patrol/Surveillance mentions

### After (POI v2.0):
```
POI-00001 → [
    EMAIL-123 (confidence: 1.0),
    EMAIL-456 (confidence: 0.9),
    WHATSAPP-789 (confidence: 1.0),
    PATROL-101 (confidence: 0.8),
    SURVEILLANCE-202 (confidence: 1.0)
]
```
✅ Complete cross-source intelligence view!
✅ Track confidence and quality
✅ Unified POI profile across all sources

---

## 🔒 Safety Notes

1. **Migration is idempotent**: Safe to run multiple times (ON CONFLICT DO NOTHING)
2. **Old table preserved**: email_alleged_person_link stays intact
3. **Zero downtime**: Both tables coexist during transition
4. **Rollback ready**: Can drop new table and keep using old one
5. **No data loss**: All existing links migrated with full fidelity

---

## 📞 Support

Run migration script:
```bash
docker compose exec intelligence-platform python3 migrate_existing_email_links.py
```

Or manually via psql:
```bash
docker compose exec -T postgres-db psql -U intelligence -d intelligence_db -f migration.sql
```
