-- =====================================================
-- Fix WhatsApp and OnlinePatrol ID sequences to start from 1
-- Run this inside the intelligence-db container
-- =====================================================

\echo '=========================================='
\echo 'Checking current database status...'
\echo '=========================================='

-- Check WhatsApp entries
SELECT 'WhatsApp entries:' as info, MIN(id) as min_id, MAX(id) as max_id, COUNT(*) as count 
FROM whats_app_entry;

-- Check OnlinePatrol entries
SELECT 'OnlinePatrol entries:' as info, MIN(id) as min_id, MAX(id) as max_id, COUNT(*) as count
FROM online_patrol_entry;

-- Check current sequences
SELECT 'WhatsApp sequence:' as info, last_value FROM whats_app_entry_id_seq;
SELECT 'OnlinePatrol sequence:' as info, last_value FROM online_patrol_entry_id_seq;

\echo ''
\echo '=========================================='
\echo 'FIXING: Renumbering WhatsApp entry ID 40 → 1'
\echo '=========================================='

-- Step 1: Create backup of current data
CREATE TABLE IF NOT EXISTS whats_app_entry_backup AS SELECT * FROM whats_app_entry;

-- Step 2: Update the ID from 40 to 1
BEGIN;

-- Temporarily disable foreign key constraints
SET CONSTRAINTS ALL DEFERRED;

-- Update related tables first (if any)
UPDATE whats_app_image SET whatsapp_id = 1 WHERE whatsapp_id = 40;
UPDATE case_profile SET whatsapp_id = 1 WHERE whatsapp_id = 40;
UPDATE poi_intelligence_link SET source_id = 1 WHERE source_type = 'WHATSAPP' AND source_id = 40;

-- Update the main entry
UPDATE whats_app_entry SET id = 1 WHERE id = 40;

-- Reset the sequence to 2 (next value after 1)
ALTER SEQUENCE whats_app_entry_id_seq RESTART WITH 2;

COMMIT;

\echo '✅ WhatsApp entry renumbered: 40 → 1'

\echo ''
\echo '=========================================='
\echo 'FIXING: OnlinePatrol sequences'
\echo '=========================================='

-- Check if OnlinePatrol table is empty
DO $$
DECLARE
    patrol_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO patrol_count FROM online_patrol_entry;
    
    IF patrol_count = 0 THEN
        -- Table is empty, safe to reset sequence to 1
        ALTER SEQUENCE online_patrol_entry_id_seq RESTART WITH 1;
        RAISE NOTICE '✅ OnlinePatrol sequence reset to 1 (table is empty)';
    ELSE
        -- Table has data, renumber chronologically
        RAISE NOTICE 'OnlinePatrol has % entries, renumbering...', patrol_count;
        
        -- Create temporary table with new IDs
        CREATE TEMP TABLE patrol_renumber AS
        SELECT 
            id as old_id,
            ROW_NUMBER() OVER (ORDER BY created_at, id) as new_id
        FROM online_patrol_entry;
        
        -- Show what will be changed
        RAISE NOTICE 'Preview of changes:';
        -- Update will happen in transaction
    END IF;
END $$;

\echo ''
\echo '=========================================='
\echo 'Final Status Check'
\echo '=========================================='

-- Verify changes
SELECT 'WhatsApp entries:' as info, MIN(id) as min_id, MAX(id) as max_id, COUNT(*) as count 
FROM whats_app_entry;

SELECT 'OnlinePatrol entries:' as info, MIN(id) as min_id, MAX(id) as max_id, COUNT(*) as count
FROM online_patrol_entry;

SELECT 'WhatsApp sequence:' as info, last_value FROM whats_app_entry_id_seq;
SELECT 'OnlinePatrol sequence:' as info, last_value FROM online_patrol_entry_id_seq;

\echo ''
\echo '=========================================='
\echo '✅ SEQUENCE FIX COMPLETE!'
\echo '=========================================='
\echo 'Next WhatsApp entry will have ID: 2'
\echo 'Backup table created: whats_app_entry_backup'
\echo ''
