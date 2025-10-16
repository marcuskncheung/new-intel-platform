-- =====================================================
-- POI ARCHITECTURE UPGRADE MIGRATION
-- Version: 2.0
-- Date: 2024
-- Description: Comprehensive POI tracking system with
--              universal source linking and automation
-- =====================================================

-- Start transaction
BEGIN;

-- =====================================================
-- STEP 1: Enhance alleged_person_profile FIRST
-- (Must happen before creating foreign key references)
-- =====================================================

RAISE NOTICE '=== STEP 1: Enhancing alleged_person_profile table ===';

-- Add new columns to alleged_person_profile
ALTER TABLE alleged_person_profile 
    -- Add POI ID if not exists
    ADD COLUMN IF NOT EXISTS poi_id VARCHAR(20),
    
    -- Identity enhancements
    ADD COLUMN IF NOT EXISTS name_normalized VARCHAR(200),
    ADD COLUMN IF NOT EXISTS aliases JSONB,
    ADD COLUMN IF NOT EXISTS phone_numbers JSONB,
    ADD COLUMN IF NOT EXISTS email_addresses JSONB,
    ADD COLUMN IF NOT EXISTS whatsapp_numbers JSONB,
    ADD COLUMN IF NOT EXISTS addresses JSONB,
    ADD COLUMN IF NOT EXISTS employment_history JSONB,
    
    -- Assessment & Risk
    ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20),
    ADD COLUMN IF NOT EXISTS risk_score INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS threat_classification JSONB,
    ADD COLUMN IF NOT EXISTS watchlist_status VARCHAR(50),
    ADD COLUMN IF NOT EXISTS priority_level INTEGER DEFAULT 3,
    ADD COLUMN IF NOT EXISTS assessment_notes TEXT,
    
    -- Statistics (auto-updated by triggers)
    ADD COLUMN IF NOT EXISTS total_mentions INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS email_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS whatsapp_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS patrol_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS surveillance_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS case_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS first_mentioned_date TIMESTAMP,
    ADD COLUMN IF NOT EXISTS last_mentioned_date TIMESTAMP,
    ADD COLUMN IF NOT EXISTS last_activity_date TIMESTAMP,
    
    -- Misconduct tracking
    ADD COLUMN IF NOT EXISTS proven_violations JSONB,
    ADD COLUMN IF NOT EXISTS investigation_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS substantiated_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS unsubstantiated_count INTEGER DEFAULT 0,
    
    -- Relationship mapping
    ADD COLUMN IF NOT EXISTS associated_pois JSONB,
    ADD COLUMN IF NOT EXISTS organization_links JSONB,
    ADD COLUMN IF NOT EXISTS network_centrality FLOAT,
    
    -- AI/Automation metadata
    ADD COLUMN IF NOT EXISTS deduplication_group_id VARCHAR(50),
    ADD COLUMN IF NOT EXISTS merge_confidence FLOAT,
    ADD COLUMN IF NOT EXISTS auto_enriched BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS last_enrichment_date TIMESTAMP,
    ADD COLUMN IF NOT EXISTS data_sources JSONB,
    
    -- Status & Control
    ADD COLUMN IF NOT EXISTS merged_into_poi_id VARCHAR(20),
    ADD COLUMN IF NOT EXISTS is_high_priority BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS requires_approval BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS approved_by VARCHAR(100),
    ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS last_reviewed_date TIMESTAMP;

-- =====================================================
-- STEP 2: Generate POI-IDs for existing profiles
-- =====================================================

RAISE NOTICE '=== STEP 2: Generating POI-IDs for existing profiles ===';

-- Generate POI-IDs for existing profiles without them
DO $$
DECLARE
    next_poi_number INTEGER;
    profile_record RECORD;
    generated_count INTEGER := 0;
BEGIN
    -- Get the next available POI number
    SELECT COALESCE(MAX(CAST(SUBSTRING(poi_id FROM 5) AS INTEGER)), 0) + 1 
    INTO next_poi_number
    FROM alleged_person_profile 
    WHERE poi_id IS NOT NULL AND poi_id ~ '^POI-[0-9]+$';
    
    RAISE NOTICE 'Starting POI-ID generation from POI-%', LPAD(next_poi_number::TEXT, 3, '0');
    
    -- Assign POI-IDs to profiles without them
    FOR profile_record IN 
        SELECT id, name_english, name_chinese FROM alleged_person_profile WHERE poi_id IS NULL ORDER BY id
    LOOP
        UPDATE alleged_person_profile 
        SET poi_id = 'POI-' || LPAD(next_poi_number::TEXT, 3, '0')
        WHERE id = profile_record.id;
        
        generated_count := generated_count + 1;
        next_poi_number := next_poi_number + 1;
    END LOOP;
    
    RAISE NOTICE 'Generated % POI-IDs for existing profiles', generated_count;
END $$;

-- Make poi_id NOT NULL and UNIQUE after migration
ALTER TABLE alleged_person_profile 
    ALTER COLUMN poi_id SET NOT NULL;

-- Add unique constraint
ALTER TABLE alleged_person_profile
    DROP CONSTRAINT IF EXISTS unique_poi_id,
    ADD CONSTRAINT unique_poi_id UNIQUE (poi_id);

-- Create normalized names for existing profiles
UPDATE alleged_person_profile
SET name_normalized = LOWER(REPLACE(COALESCE(name_english, name_chinese, ''), ' ', ''))
WHERE name_normalized IS NULL;

-- Create indexes on new columns
CREATE INDEX IF NOT EXISTS idx_poi_id ON alleged_person_profile(poi_id);
CREATE INDEX IF NOT EXISTS idx_poi_name_normalized ON alleged_person_profile(name_normalized);
CREATE INDEX IF NOT EXISTS idx_poi_risk_level ON alleged_person_profile(risk_level);
CREATE INDEX IF NOT EXISTS idx_poi_status ON alleged_person_profile(status);
CREATE INDEX IF NOT EXISTS idx_poi_last_activity ON alleged_person_profile(last_activity_date);

-- Add foreign key for merged_into (self-referencing)
ALTER TABLE alleged_person_profile
    DROP CONSTRAINT IF EXISTS fk_merged_into_poi,
    ADD CONSTRAINT fk_merged_into_poi 
        FOREIGN KEY (merged_into_poi_id) 
        REFERENCES alleged_person_profile(poi_id);

RAISE NOTICE '=== alleged_person_profile enhancement complete ===';

-- =====================================================
-- STEP 3: Create New Tables (NOW with valid FK references)
-- =====================================================

RAISE NOTICE '=== STEP 3: Creating new POI system tables ===';

-- -----------------------------------------------------
-- Table: poi_intelligence_link (Universal Linking)
-- Replaces: email_alleged_person_link
-- Purpose: Link POIs to ANY intelligence source
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS poi_intelligence_link (
    id SERIAL PRIMARY KEY,
    
    -- Link References
    poi_id VARCHAR(20) NOT NULL,
    case_profile_id INTEGER NOT NULL,
    
    -- Source Reference (Polymorphic)
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('EMAIL', 'WHATSAPP', 'PATROL', 'SURVEILLANCE')),
    source_id INTEGER NOT NULL,
    source_table VARCHAR(50),
    
    -- Extraction Metadata
    extraction_method VARCHAR(20) CHECK (extraction_method IN ('MANUAL', 'AI', 'REGEX', 'NER')),
    extraction_tool VARCHAR(50),
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extracted_by_user VARCHAR(100),
    validation_status VARCHAR(20) DEFAULT 'PENDING' CHECK (validation_status IN ('PENDING', 'VERIFIED', 'REJECTED')),
    
    -- Context Information
    mention_context TEXT,
    role_in_case VARCHAR(50),
    mention_count INTEGER DEFAULT 1,
    is_primary_subject BOOLEAN DEFAULT FALSE,
    
    -- Quality Assurance
    verified_by VARCHAR(100),
    verified_at TIMESTAMP,
    verification_notes TEXT,
    needs_review BOOLEAN DEFAULT FALSE,
    
    -- Audit Trail
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys (NOW alleged_person_profile.poi_id exists!)
    FOREIGN KEY (poi_id) REFERENCES alleged_person_profile(poi_id) ON DELETE CASCADE,
    FOREIGN KEY (case_profile_id) REFERENCES case_profile(id) ON DELETE CASCADE,
    
    -- Unique Constraint
    CONSTRAINT unique_poi_source UNIQUE (poi_id, source_type, source_id)
);

-- Indexes for poi_intelligence_link
CREATE INDEX idx_poi_link_poi_id ON poi_intelligence_link(poi_id);
CREATE INDEX idx_poi_link_case_profile ON poi_intelligence_link(case_profile_id);
CREATE INDEX idx_poi_link_source ON poi_intelligence_link(source_type, source_id);
CREATE INDEX idx_poi_link_validation ON poi_intelligence_link(validation_status);
CREATE INDEX idx_poi_link_review ON poi_intelligence_link(needs_review);

COMMENT ON TABLE poi_intelligence_link IS 'Universal POI-to-intelligence linking table supporting all source types';
COMMENT ON COLUMN poi_intelligence_link.source_type IS 'Type of intelligence source: EMAIL/WHATSAPP/PATROL/SURVEILLANCE';
COMMENT ON COLUMN poi_intelligence_link.extraction_method IS 'How POI was extracted: MANUAL/AI/REGEX/NER';
COMMENT ON COLUMN poi_intelligence_link.confidence_score IS 'AI extraction confidence (0.0-1.0)';

-- -----------------------------------------------------
-- Table: poi_extraction_queue (Automation Queue)
-- Purpose: Manage automated POI extraction jobs
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS poi_extraction_queue (
    id SERIAL PRIMARY KEY,
    
    -- Job References
    case_profile_id INTEGER NOT NULL,
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('EMAIL', 'WHATSAPP', 'PATROL', 'SURVEILLANCE')),
    source_id INTEGER NOT NULL,
    
    -- Processing Status
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETE', 'FAILED', 'NEEDS_REVIEW')),
    priority INTEGER DEFAULT 3 CHECK (priority >= 1 AND priority <= 5),
    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_started_at TIMESTAMP,
    completed_at TIMESTAMP,
    assigned_to VARCHAR(100),
    
    -- Extraction Results
    extracted_entities JSONB,
    extraction_method VARCHAR(50),
    extraction_confidence FLOAT CHECK (extraction_confidence >= 0 AND extraction_confidence <= 1),
    entities_found_count INTEGER DEFAULT 0,
    matched_existing_pois JSONB,
    
    -- Quality Check
    requires_manual_review BOOLEAN DEFAULT FALSE,
    review_reason VARCHAR(200),
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    
    -- Error Handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    last_error_at TIMESTAMP,
    max_retries INTEGER DEFAULT 3,
    
    -- Foreign Keys
    FOREIGN KEY (case_profile_id) REFERENCES case_profile(id) ON DELETE CASCADE,
    
    -- Unique Constraint
    CONSTRAINT unique_extraction_source UNIQUE (source_type, source_id)
);

-- Indexes for poi_extraction_queue
CREATE INDEX idx_extraction_queue_status ON poi_extraction_queue(status);
CREATE INDEX idx_extraction_queue_priority ON poi_extraction_queue(priority);
CREATE INDEX idx_extraction_queue_queued ON poi_extraction_queue(queued_at);
CREATE INDEX idx_extraction_queue_review ON poi_extraction_queue(requires_manual_review);
CREATE INDEX idx_extraction_queue_case ON poi_extraction_queue(case_profile_id);

COMMENT ON TABLE poi_extraction_queue IS 'Queue for automated POI extraction jobs with priority and retry logic';
COMMENT ON COLUMN poi_extraction_queue.extracted_entities IS 'Raw AI extraction results as JSON array';
COMMENT ON COLUMN poi_extraction_queue.requires_manual_review IS 'Flag indicating human review needed';

-- -----------------------------------------------------
-- Table: poi_assessment_history (Audit Trail)
-- Purpose: Track all POI risk assessment changes
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS poi_assessment_history (
    id SERIAL PRIMARY KEY,
    
    -- Assessment References
    poi_id VARCHAR(20) NOT NULL,
    assessed_by VARCHAR(100) NOT NULL,
    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Assessment Changes
    previous_risk_level VARCHAR(20),
    new_risk_level VARCHAR(20),
    previous_risk_score INTEGER,
    new_risk_score INTEGER,
    assessment_reason TEXT,
    supporting_evidence JSONB,
    assessment_notes TEXT,
    
    -- Related Intelligence
    related_case_profiles JSONB,
    trigger_source_type VARCHAR(20),
    trigger_source_id INTEGER,
    
    -- Foreign Keys
    FOREIGN KEY (poi_id) REFERENCES alleged_person_profile(poi_id) ON DELETE CASCADE
);

-- Indexes for poi_assessment_history
CREATE INDEX idx_assessment_history_poi ON poi_assessment_history(poi_id);
CREATE INDEX idx_assessment_history_date ON poi_assessment_history(assessment_date);
CREATE INDEX idx_assessment_history_assessor ON poi_assessment_history(assessed_by);

COMMENT ON TABLE poi_assessment_history IS 'Complete audit trail of POI risk assessment changes';
COMMENT ON COLUMN poi_assessment_history.supporting_evidence IS 'Array of case references supporting assessment change';

-- =====================================================
-- STEP 2: Enhance Existing Tables
-- =====================================================

-- Add new columns to alleged_person_profile
ALTER TABLE alleged_person_profile 
    -- Add POI ID if not exists
    ADD COLUMN IF NOT EXISTS poi_id VARCHAR(20) UNIQUE,
    
    -- Identity enhancements
    ADD COLUMN IF NOT EXISTS name_normalized VARCHAR(200),
    ADD COLUMN IF NOT EXISTS aliases JSONB,
    ADD COLUMN IF NOT EXISTS phone_numbers JSONB,
    ADD COLUMN IF NOT EXISTS email_addresses JSONB,
    ADD COLUMN IF NOT EXISTS whatsapp_numbers JSONB,
    ADD COLUMN IF NOT EXISTS addresses JSONB,
    ADD COLUMN IF NOT EXISTS employment_history JSONB,
    
    -- Assessment & Risk
    ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20),
    ADD COLUMN IF NOT EXISTS risk_score INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS threat_classification JSONB,
    ADD COLUMN IF NOT EXISTS watchlist_status VARCHAR(50),
    ADD COLUMN IF NOT EXISTS priority_level INTEGER DEFAULT 3,
    ADD COLUMN IF NOT EXISTS assessment_notes TEXT,
    
    -- Statistics (auto-updated by triggers)
    ADD COLUMN IF NOT EXISTS total_mentions INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS email_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS whatsapp_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS patrol_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS surveillance_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS case_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS first_mentioned_date TIMESTAMP,
    ADD COLUMN IF NOT EXISTS last_mentioned_date TIMESTAMP,
    ADD COLUMN IF NOT EXISTS last_activity_date TIMESTAMP,
    
    -- Misconduct tracking
    ADD COLUMN IF NOT EXISTS proven_violations JSONB,
    ADD COLUMN IF NOT EXISTS investigation_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS substantiated_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS unsubstantiated_count INTEGER DEFAULT 0,
    
    -- Relationship mapping
    ADD COLUMN IF NOT EXISTS associated_pois JSONB,
    ADD COLUMN IF NOT EXISTS organization_links JSONB,
    ADD COLUMN IF NOT EXISTS network_centrality FLOAT,
    
    -- AI/Automation metadata
    ADD COLUMN IF NOT EXISTS deduplication_group_id VARCHAR(50),
    ADD COLUMN IF NOT EXISTS merge_confidence FLOAT,
    ADD COLUMN IF NOT EXISTS auto_enriched BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS last_enrichment_date TIMESTAMP,
    ADD COLUMN IF NOT EXISTS data_sources JSONB,
    
    -- Status & Control
    ADD COLUMN IF NOT EXISTS merged_into_poi_id VARCHAR(20),
    ADD COLUMN IF NOT EXISTS is_high_priority BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS requires_approval BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS approved_by VARCHAR(100),
    ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS last_reviewed_date TIMESTAMP;

-- Create indexes on new columns
CREATE INDEX IF NOT EXISTS idx_poi_id ON alleged_person_profile(poi_id);
CREATE INDEX IF NOT EXISTS idx_poi_name_normalized ON alleged_person_profile(name_normalized);
CREATE INDEX IF NOT EXISTS idx_poi_risk_level ON alleged_person_profile(risk_level);
CREATE INDEX IF NOT EXISTS idx_poi_status ON alleged_person_profile(status);
CREATE INDEX IF NOT EXISTS idx_poi_last_activity ON alleged_person_profile(last_activity_date);

-- Add foreign key for merged_into
ALTER TABLE alleged_person_profile
    DROP CONSTRAINT IF EXISTS fk_merged_into_poi,
    ADD CONSTRAINT fk_merged_into_poi 
        FOREIGN KEY (merged_into_poi_id) 
        REFERENCES alleged_person_profile(poi_id);

-- =====================================================
-- STEP 4: Migrate Existing Email-POI Links
-- =====================================================

RAISE NOTICE '=== STEP 4: Migrating existing email_alleged_person_link data ===';

-- Migrate email_alleged_person_link to poi_intelligence_link
-- This preserves all existing POI-to-email relationships
INSERT INTO poi_intelligence_link (
    poi_id,
    case_profile_id,
    source_type,
    source_id,
    source_table,
    extraction_method,
    extraction_timestamp,
    validation_status,
    created_at
)
SELECT 
    app.poi_id,
    e.case_profile_id,
    'EMAIL' as source_type,
    eapl.email_id as source_id,
    'email' as source_table,
    'MANUAL' as extraction_method,
    COALESCE(eapl.created_at, CURRENT_TIMESTAMP) as extraction_timestamp,
    'VERIFIED' as validation_status,
    COALESCE(eapl.created_at, CURRENT_TIMESTAMP) as created_at
FROM email_alleged_person_link eapl
JOIN alleged_person_profile app ON eapl.alleged_person_id = app.id
JOIN email e ON eapl.email_id = e.id
WHERE NOT EXISTS (
    SELECT 1 FROM poi_intelligence_link pil 
    WHERE pil.poi_id = app.poi_id 
    AND pil.source_type = 'EMAIL' 
    AND pil.source_id = eapl.email_id
);

-- Log migration results
DO $$
DECLARE
    migrated_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO migrated_count
    FROM poi_intelligence_link
    WHERE source_type = 'EMAIL';
    
    RAISE NOTICE 'Migrated % email-POI links to new system', migrated_count;
END $$;

-- Update statistics in alleged_person_profile based on migrated data
RAISE NOTICE 'Updating POI statistics...';

UPDATE alleged_person_profile app
SET 
    email_count = (
        SELECT COUNT(*) 
        FROM poi_intelligence_link pil 
        WHERE pil.poi_id = app.poi_id AND pil.source_type = 'EMAIL'
    ),
    total_mentions = (
        SELECT COUNT(*) 
        FROM poi_intelligence_link pil 
        WHERE pil.poi_id = app.poi_id
    ),
    first_mentioned_date = (
        SELECT MIN(pil.created_at) 
        FROM poi_intelligence_link pil 
        WHERE pil.poi_id = app.poi_id
    ),
    last_mentioned_date = (
        SELECT MAX(pil.created_at) 
        FROM poi_intelligence_link pil 
        WHERE pil.poi_id = app.poi_id
    ),
    last_activity_date = (
        SELECT MAX(pil.created_at) 
        FROM poi_intelligence_link pil 
        WHERE pil.poi_id = app.poi_id
    ),
    case_count = (
        SELECT COUNT(DISTINCT pil.case_profile_id) 
        FROM poi_intelligence_link pil 
        WHERE pil.poi_id = app.poi_id
    );

-- Log statistics update
DO $$
DECLARE
    updated_profiles INTEGER;
    total_links INTEGER;
BEGIN
    SELECT COUNT(*) INTO updated_profiles
    FROM alleged_person_profile
    WHERE total_mentions > 0;
    
    SELECT COUNT(*) INTO total_links
    FROM poi_intelligence_link;
    
    RAISE NOTICE 'Updated statistics for % POI profiles', updated_profiles;
    RAISE NOTICE 'Total intelligence links: %', total_links;
END $$;

-- Optional: Keep email_alleged_person_link for backwards compatibility
-- or drop it after verifying migration
-- UNCOMMENT BELOW TO REMOVE OLD TABLE:
-- DROP TABLE IF EXISTS email_alleged_person_link CASCADE;
-- RAISE NOTICE 'Dropped old email_alleged_person_link table';

RAISE NOTICE '=== Data migration complete ===';

-- =====================================================
-- STEP 5: Create Database Triggers
-- =====================================================

RAISE NOTICE '=== STEP 5: Creating database triggers ===';

-- Trigger: Auto-queue POI extraction on new intelligence
CREATE OR REPLACE FUNCTION auto_queue_poi_extraction()
RETURNS TRIGGER AS $$
BEGIN
    -- Determine source type and ID based on table
    INSERT INTO poi_extraction_queue (
        case_profile_id,
        source_type,
        source_id,
        priority,
        queued_at
    ) VALUES (
        NEW.case_profile_id,
        CASE 
            WHEN TG_TABLE_NAME = 'email' THEN 'EMAIL'
            WHEN TG_TABLE_NAME = 'whatsapp_entry' THEN 'WHATSAPP'
            WHEN TG_TABLE_NAME = 'online_patrol_entry' THEN 'PATROL'
            WHEN TG_TABLE_NAME = 'surveillance_entry' THEN 'SURVEILLANCE'
        END,
        NEW.id,
        3, -- default priority
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (source_type, source_id) DO NOTHING;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers on intelligence tables
DROP TRIGGER IF EXISTS trigger_queue_email_extraction ON email;
CREATE TRIGGER trigger_queue_email_extraction
    AFTER INSERT ON email
    FOR EACH ROW
    EXECUTE FUNCTION auto_queue_poi_extraction();

DROP TRIGGER IF EXISTS trigger_queue_whatsapp_extraction ON whatsapp_entry;
CREATE TRIGGER trigger_queue_whatsapp_extraction
    AFTER INSERT ON whatsapp_entry
    FOR EACH ROW
    EXECUTE FUNCTION auto_queue_poi_extraction();

-- Trigger: Update POI statistics on new links
CREATE OR REPLACE FUNCTION update_poi_statistics()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE alleged_person_profile
        SET 
            total_mentions = total_mentions + 1,
            email_count = CASE WHEN NEW.source_type = 'EMAIL' THEN email_count + 1 ELSE email_count END,
            whatsapp_count = CASE WHEN NEW.source_type = 'WHATSAPP' THEN whatsapp_count + 1 ELSE whatsapp_count END,
            patrol_count = CASE WHEN NEW.source_type = 'PATROL' THEN patrol_count + 1 ELSE patrol_count END,
            surveillance_count = CASE WHEN NEW.source_type = 'SURVEILLANCE' THEN surveillance_count + 1 ELSE surveillance_count END,
            case_count = (
                SELECT COUNT(DISTINCT case_profile_id) 
                FROM poi_intelligence_link 
                WHERE poi_id = NEW.poi_id
            ),
            last_mentioned_date = CURRENT_TIMESTAMP,
            first_mentioned_date = COALESCE(first_mentioned_date, CURRENT_TIMESTAMP),
            last_activity_date = CURRENT_TIMESTAMP
        WHERE poi_id = NEW.poi_id;
        
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE alleged_person_profile
        SET 
            total_mentions = GREATEST(total_mentions - 1, 0),
            email_count = CASE WHEN OLD.source_type = 'EMAIL' THEN GREATEST(email_count - 1, 0) ELSE email_count END,
            whatsapp_count = CASE WHEN OLD.source_type = 'WHATSAPP' THEN GREATEST(whatsapp_count - 1, 0) ELSE whatsapp_count END,
            patrol_count = CASE WHEN OLD.source_type = 'PATROL' THEN GREATEST(patrol_count - 1, 0) ELSE patrol_count END,
            surveillance_count = CASE WHEN OLD.source_type = 'SURVEILLANCE' THEN GREATEST(surveillance_count - 1, 0) ELSE surveillance_count END,
            case_count = (
                SELECT COUNT(DISTINCT case_profile_id) 
                FROM poi_intelligence_link 
                WHERE poi_id = OLD.poi_id
            )
        WHERE poi_id = OLD.poi_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_poi_stats ON poi_intelligence_link;
CREATE TRIGGER trigger_update_poi_stats
    AFTER INSERT OR DELETE ON poi_intelligence_link
    FOR EACH ROW
    EXECUTE FUNCTION update_poi_statistics();

-- Trigger: Record assessment changes in history
CREATE OR REPLACE FUNCTION record_poi_assessment_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Only record if risk level or score changed
    IF (OLD.risk_level IS DISTINCT FROM NEW.risk_level) OR 
       (OLD.risk_score IS DISTINCT FROM NEW.risk_score) THEN
        
        INSERT INTO poi_assessment_history (
            poi_id,
            assessed_by,
            assessment_date,
            previous_risk_level,
            new_risk_level,
            previous_risk_score,
            new_risk_score,
            assessment_reason
        ) VALUES (
            NEW.poi_id,
            NEW.updated_by,
            CURRENT_TIMESTAMP,
            OLD.risk_level,
            NEW.risk_level,
            OLD.risk_score,
            NEW.risk_score,
            'Risk assessment updated'
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_record_assessment ON alleged_person_profile;
CREATE TRIGGER trigger_record_assessment
    AFTER UPDATE ON alleged_person_profile
    FOR EACH ROW
    WHEN (OLD.risk_level IS DISTINCT FROM NEW.risk_level OR OLD.risk_score IS DISTINCT FROM NEW.risk_score)
    EXECUTE FUNCTION record_poi_assessment_change();

-- =====================================================
-- STEP 6: Create Useful Views
-- =====================================================

RAISE NOTICE '=== STEP 6: Creating dashboard views ===';

-- View: POI Summary Dashboard
CREATE OR REPLACE VIEW v_poi_dashboard AS
SELECT 
    app.poi_id,
    app.name_english,
    app.name_chinese,
    app.license_number,
    app.company,
    app.risk_level,
    app.risk_score,
    app.watchlist_status,
    app.total_mentions,
    app.email_count,
    app.whatsapp_count,
    app.patrol_count,
    app.surveillance_count,
    app.case_count,
    app.last_activity_date,
    app.status,
    COUNT(DISTINCT pil.case_profile_id) as linked_cases,
    MAX(pil.created_at) as last_linked_date
FROM alleged_person_profile app
LEFT JOIN poi_intelligence_link pil ON app.poi_id = pil.poi_id
GROUP BY app.poi_id, app.name_english, app.name_chinese, app.license_number, 
         app.company, app.risk_level, app.risk_score, app.watchlist_status,
         app.total_mentions, app.email_count, app.whatsapp_count, 
         app.patrol_count, app.surveillance_count, app.case_count,
         app.last_activity_date, app.status;

-- View: Extraction Queue Status
CREATE OR REPLACE VIEW v_extraction_queue_status AS
SELECT 
    status,
    COUNT(*) as job_count,
    AVG(CASE 
        WHEN completed_at IS NOT NULL AND processing_started_at IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (completed_at - processing_started_at))
        ELSE NULL 
    END) as avg_processing_seconds,
    COUNT(CASE WHEN requires_manual_review THEN 1 END) as needs_review_count
FROM poi_extraction_queue
GROUP BY status;

-- =====================================================
-- STEP 7: Create Helper Functions
-- =====================================================

RAISE NOTICE '=== STEP 7: Creating helper functions ===';

-- Function: Get POI network (associated POIs)
CREATE OR REPLACE FUNCTION get_poi_network(target_poi_id VARCHAR)
RETURNS TABLE (
    related_poi_id VARCHAR,
    relationship_strength INTEGER,
    shared_cases INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pil2.poi_id as related_poi_id,
        COUNT(*) as relationship_strength,
        COUNT(DISTINCT pil2.case_profile_id) as shared_cases
    FROM poi_intelligence_link pil1
    JOIN poi_intelligence_link pil2 ON pil1.case_profile_id = pil2.case_profile_id
    WHERE pil1.poi_id = target_poi_id 
    AND pil2.poi_id != target_poi_id
    GROUP BY pil2.poi_id
    ORDER BY relationship_strength DESC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- STEP 8: Grant Permissions
-- =====================================================

RAISE NOTICE '=== STEP 8: Granting database permissions ===';

-- Grant permissions to application user (adjust username as needed)
GRANT SELECT, INSERT, UPDATE, DELETE ON poi_intelligence_link TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON poi_extraction_queue TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON poi_assessment_history TO postgres;
GRANT SELECT, UPDATE ON alleged_person_profile TO postgres;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- =====================================================
-- COMMIT TRANSACTION
-- =====================================================

COMMIT;

-- =====================================================
-- Verification Queries
-- =====================================================

-- Check table creation
SELECT 
    tablename,
    schemaname
FROM pg_tables
WHERE tablename IN ('poi_intelligence_link', 'poi_extraction_queue', 'poi_assessment_history')
ORDER BY tablename;

-- Check new columns in alleged_person_profile
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'alleged_person_profile'
AND column_name IN ('poi_id', 'risk_level', 'risk_score', 'total_mentions')
ORDER BY column_name;

-- Check triggers
SELECT 
    trigger_name,
    event_object_table,
    action_timing,
    event_manipulation
FROM information_schema.triggers
WHERE trigger_name LIKE '%poi%'
ORDER BY trigger_name;

-- Summary statistics
SELECT 
    'POI Profiles' as entity,
    COUNT(*) as count
FROM alleged_person_profile
UNION ALL
SELECT 
    'Intelligence Links' as entity,
    COUNT(*) as count
FROM poi_intelligence_link
UNION ALL
SELECT 
    'Extraction Queue' as entity,
    COUNT(*) as count
FROM poi_extraction_queue
UNION ALL
SELECT 
    'Assessment History' as entity,
    COUNT(*) as count
FROM poi_assessment_history;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================
-- Next Steps:
-- 1. Update Flask models to match new schema
-- 2. Create POI extraction worker service
-- 3. Update UI to display new POI features
-- 4. Test extraction queue processing
-- 5. Configure scheduled jobs for queue processing
-- =====================================================
