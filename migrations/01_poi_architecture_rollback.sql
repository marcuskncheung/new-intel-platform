-- =====================================================
-- POI ARCHITECTURE ROLLBACK SCRIPT
-- Version: 2.0
-- Description: Safely rollback POI architecture upgrade
-- =====================================================

-- Start transaction
BEGIN;

RAISE NOTICE 'Starting POI Architecture Rollback...';

-- =====================================================
-- STEP 1: Drop Triggers
-- =====================================================

RAISE NOTICE 'Dropping triggers...';

DROP TRIGGER IF EXISTS trigger_queue_email_extraction ON email;
DROP TRIGGER IF EXISTS trigger_queue_whatsapp_extraction ON whatsapp_entry;
DROP TRIGGER IF EXISTS trigger_update_poi_stats ON poi_intelligence_link;
DROP TRIGGER IF EXISTS trigger_record_assessment ON alleged_person_profile;

-- =====================================================
-- STEP 2: Drop Functions
-- =====================================================

RAISE NOTICE 'Dropping functions...';

DROP FUNCTION IF EXISTS auto_queue_poi_extraction() CASCADE;
DROP FUNCTION IF EXISTS update_poi_statistics() CASCADE;
DROP FUNCTION IF EXISTS record_poi_assessment_change() CASCADE;
DROP FUNCTION IF EXISTS get_poi_network(VARCHAR) CASCADE;

-- =====================================================
-- STEP 3: Drop Views
-- =====================================================

RAISE NOTICE 'Dropping views...';

DROP VIEW IF EXISTS v_poi_dashboard CASCADE;
DROP VIEW IF EXISTS v_extraction_queue_status CASCADE;

-- =====================================================
-- STEP 4: Backup Data Before Removal
-- =====================================================

RAISE NOTICE 'Creating backup tables...';

-- Backup POI intelligence links (in case we need to restore)
CREATE TABLE IF NOT EXISTS backup_poi_intelligence_link AS
SELECT * FROM poi_intelligence_link;

-- Backup extraction queue
CREATE TABLE IF NOT EXISTS backup_poi_extraction_queue AS
SELECT * FROM poi_extraction_queue;

-- Backup assessment history
CREATE TABLE IF NOT EXISTS backup_poi_assessment_history AS
SELECT * FROM poi_assessment_history;

-- Backup enhanced profile data
CREATE TABLE IF NOT EXISTS backup_alleged_person_profile_enhanced AS
SELECT 
    id,
    poi_id,
    name_normalized,
    aliases,
    phone_numbers,
    email_addresses,
    whatsapp_numbers,
    addresses,
    employment_history,
    risk_level,
    risk_score,
    threat_classification,
    watchlist_status,
    priority_level,
    assessment_notes,
    total_mentions,
    email_count,
    whatsapp_count,
    patrol_count,
    surveillance_count,
    case_count,
    first_mentioned_date,
    last_mentioned_date,
    last_activity_date,
    proven_violations,
    investigation_count,
    substantiated_count,
    unsubstantiated_count,
    associated_pois,
    organization_links,
    network_centrality,
    deduplication_group_id,
    merge_confidence,
    auto_enriched,
    last_enrichment_date,
    data_sources,
    merged_into_poi_id,
    is_high_priority,
    requires_approval,
    approved_by,
    approved_at,
    last_reviewed_date
FROM alleged_person_profile
WHERE poi_id IS NOT NULL;

RAISE NOTICE 'Backup tables created successfully';

-- =====================================================
-- STEP 5: Drop New Tables
-- =====================================================

RAISE NOTICE 'Dropping new tables...';

DROP TABLE IF EXISTS poi_assessment_history CASCADE;
DROP TABLE IF EXISTS poi_extraction_queue CASCADE;
DROP TABLE IF EXISTS poi_intelligence_link CASCADE;

-- =====================================================
-- STEP 6: Remove New Columns from alleged_person_profile
-- =====================================================

RAISE NOTICE 'Removing enhanced columns from alleged_person_profile...';

-- Drop foreign key constraint first
ALTER TABLE alleged_person_profile
    DROP CONSTRAINT IF EXISTS fk_merged_into_poi;

-- Drop indexes
DROP INDEX IF EXISTS idx_poi_id;
DROP INDEX IF EXISTS idx_poi_name_normalized;
DROP INDEX IF EXISTS idx_poi_risk_level;
DROP INDEX IF EXISTS idx_poi_status;
DROP INDEX IF EXISTS idx_poi_last_activity;

-- Remove new columns (keep only original schema)
ALTER TABLE alleged_person_profile 
    DROP COLUMN IF EXISTS poi_id,
    DROP COLUMN IF EXISTS name_normalized,
    DROP COLUMN IF EXISTS aliases,
    DROP COLUMN IF EXISTS phone_numbers,
    DROP COLUMN IF EXISTS email_addresses,
    DROP COLUMN IF EXISTS whatsapp_numbers,
    DROP COLUMN IF EXISTS addresses,
    DROP COLUMN IF EXISTS employment_history,
    DROP COLUMN IF EXISTS risk_level,
    DROP COLUMN IF EXISTS risk_score,
    DROP COLUMN IF EXISTS threat_classification,
    DROP COLUMN IF EXISTS watchlist_status,
    DROP COLUMN IF EXISTS priority_level,
    DROP COLUMN IF EXISTS assessment_notes,
    DROP COLUMN IF EXISTS total_mentions,
    DROP COLUMN IF EXISTS email_count,
    DROP COLUMN IF EXISTS whatsapp_count,
    DROP COLUMN IF EXISTS patrol_count,
    DROP COLUMN IF EXISTS surveillance_count,
    DROP COLUMN IF EXISTS case_count,
    DROP COLUMN IF EXISTS first_mentioned_date,
    DROP COLUMN IF EXISTS last_mentioned_date,
    DROP COLUMN IF EXISTS last_activity_date,
    DROP COLUMN IF EXISTS proven_violations,
    DROP COLUMN IF EXISTS investigation_count,
    DROP COLUMN IF EXISTS substantiated_count,
    DROP COLUMN IF EXISTS unsubstantiated_count,
    DROP COLUMN IF EXISTS associated_pois,
    DROP COLUMN IF EXISTS organization_links,
    DROP COLUMN IF EXISTS network_centrality,
    DROP COLUMN IF EXISTS deduplication_group_id,
    DROP COLUMN IF EXISTS merge_confidence,
    DROP COLUMN IF EXISTS auto_enriched,
    DROP COLUMN IF EXISTS last_enrichment_date,
    DROP COLUMN IF EXISTS data_sources,
    DROP COLUMN IF EXISTS merged_into_poi_id,
    DROP COLUMN IF EXISTS is_high_priority,
    DROP COLUMN IF EXISTS requires_approval,
    DROP COLUMN IF EXISTS approved_by,
    DROP COLUMN IF EXISTS approved_at,
    DROP COLUMN IF EXISTS last_reviewed_date;

RAISE NOTICE 'Enhanced columns removed from alleged_person_profile';

-- =====================================================
-- STEP 7: Restore Old Linking System (Optional)
-- =====================================================

-- Note: email_alleged_person_link should still exist
-- If it was dropped, you can restore from backup_poi_intelligence_link

-- Check if email_alleged_person_link still exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'email_alleged_person_link'
    ) THEN
        RAISE NOTICE 'Recreating email_alleged_person_link from backup...';
        
        -- Recreate the old linking table structure
        CREATE TABLE email_alleged_person_link (
            id SERIAL PRIMARY KEY,
            email_id INTEGER NOT NULL,
            alleged_person_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email_id) REFERENCES email(id) ON DELETE CASCADE,
            FOREIGN KEY (alleged_person_id) REFERENCES alleged_person_profile(id) ON DELETE CASCADE,
            UNIQUE (email_id, alleged_person_id)
        );
        
        -- Restore data from backup if available
        INSERT INTO email_alleged_person_link (email_id, alleged_person_id, created_at)
        SELECT 
            bpil.source_id as email_id,
            app.id as alleged_person_id,
            bpil.created_at
        FROM backup_poi_intelligence_link bpil
        JOIN backup_alleged_person_profile_enhanced bapp ON bpil.poi_id = bapp.poi_id
        JOIN alleged_person_profile app ON bapp.id = app.id
        WHERE bpil.source_type = 'EMAIL'
        ON CONFLICT (email_id, alleged_person_id) DO NOTHING;
        
        RAISE NOTICE 'email_alleged_person_link restored';
    ELSE
        RAISE NOTICE 'email_alleged_person_link already exists, skipping restoration';
    END IF;
END $$;

-- =====================================================
-- STEP 8: Verification
-- =====================================================

RAISE NOTICE 'Verifying rollback...';

-- Check that new tables are gone
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_name IN ('poi_intelligence_link', 'poi_extraction_queue', 'poi_assessment_history');
    
    IF table_count > 0 THEN
        RAISE WARNING 'Some POI tables still exist! Rollback may be incomplete.';
    ELSE
        RAISE NOTICE 'All POI tables successfully removed';
    END IF;
END $$;

-- Check that backup tables exist
DO $$
DECLARE
    backup_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO backup_count
    FROM information_schema.tables
    WHERE table_name LIKE 'backup_%';
    
    RAISE NOTICE 'Created % backup tables', backup_count;
END $$;

-- =====================================================
-- COMMIT TRANSACTION
-- =====================================================

COMMIT;

RAISE NOTICE '==============================================';
RAISE NOTICE 'POI Architecture Rollback Complete!';
RAISE NOTICE '==============================================';
RAISE NOTICE 'Backup tables created:';
RAISE NOTICE '  - backup_poi_intelligence_link';
RAISE NOTICE '  - backup_poi_extraction_queue';
RAISE NOTICE '  - backup_poi_assessment_history';
RAISE NOTICE '  - backup_alleged_person_profile_enhanced';
RAISE NOTICE '';
RAISE NOTICE 'Keep backup tables for recovery purposes.';
RAISE NOTICE 'Drop them manually after verification:';
RAISE NOTICE '  DROP TABLE backup_poi_intelligence_link;';
RAISE NOTICE '  DROP TABLE backup_poi_extraction_queue;';
RAISE NOTICE '  DROP TABLE backup_poi_assessment_history;';
RAISE NOTICE '  DROP TABLE backup_alleged_person_profile_enhanced;';
RAISE NOTICE '==============================================';

-- =====================================================
-- Post-Rollback Verification Queries
-- =====================================================

-- List remaining tables
SELECT tablename, schemaname
FROM pg_tables
WHERE schemaname = 'public'
AND (tablename LIKE '%poi%' OR tablename LIKE '%backup%')
ORDER BY tablename;

-- Check alleged_person_profile columns
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'alleged_person_profile'
ORDER BY ordinal_position;
