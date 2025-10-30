-- Comprehensive fix: Renumber all WhatsApp entries to start from 1
-- This fixes the foreign key constraint issue by updating related tables at the right time
BEGIN;

-- Create backup first
CREATE TABLE IF NOT EXISTS whats_app_entry_backup_v3 AS SELECT * FROM whats_app_entry;

-- Show current state
SELECT 'BEFORE:' as status, id, complaint_name, received_time FROM whats_app_entry ORDER BY received_time, id;

-- Create a mapping of old IDs to new IDs (ordered by received_time)
CREATE TEMP TABLE id_mapping AS
SELECT
    id as old_id,
    ROW_NUMBER() OVER (ORDER BY received_time, id) as new_id
FROM whats_app_entry;

-- Show the mapping
SELECT 'MAPPING:' as info, old_id as current_id, new_id as will_become FROM id_mapping ORDER BY new_id;

-- STEP 1: First shift all IDs in MAIN table by +10000 to avoid conflicts
UPDATE whats_app_entry SET id = id + 10000;

-- STEP 2: Update related tables to use the shifted IDs (+10000)
-- This prevents foreign key violations
UPDATE whats_app_image wi
SET whatsapp_id = wi.whatsapp_id + 10000
WHERE whatsapp_id IN (SELECT old_id FROM id_mapping);

UPDATE case_profile cp
SET whatsapp_id = cp.whatsapp_id + 10000
WHERE whatsapp_id IN (SELECT old_id FROM id_mapping);

-- STEP 3: Now update MAIN table to the final new IDs
UPDATE whats_app_entry we
SET id = (SELECT new_id FROM id_mapping WHERE old_id = we.id - 10000);

-- STEP 4: Update related tables to match the new IDs
UPDATE whats_app_image wi
SET whatsapp_id = (SELECT new_id FROM id_mapping WHERE old_id + 10000 = wi.whatsapp_id);

UPDATE case_profile cp
SET whatsapp_id = (SELECT new_id FROM id_mapping WHERE old_id + 10000 = cp.whatsapp_id);

-- Handle poi_intelligence_link if source_id is stored as varchar
UPDATE poi_intelligence_link pil
SET source_id = (SELECT new_id::varchar FROM id_mapping WHERE (old_id + 10000)::varchar = pil.source_id)
WHERE source_type = 'WHATSAPP';

-- Reset the sequence to continue from the highest ID + 1
SELECT setval('whats_app_entry_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM whats_app_entry), false);

-- Show final state
SELECT 'AFTER:' as status, id, complaint_name, received_time FROM whats_app_entry ORDER BY id;
SELECT 'Next WhatsApp ID will be:' as info, nextval('whats_app_entry_id_seq') as next_id;
-- Put the sequence back to the correct position
SELECT setval('whats_app_entry_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM whats_app_entry), false);

-- Verify related tables were updated
SELECT 'whats_app_image references:' as table_name, whatsapp_id FROM whats_app_image ORDER BY whatsapp_id;
SELECT 'case_profile references:' as table_name, whatsapp_id FROM case_profile WHERE whatsapp_id IS NOT NULL ORDER BY whatsapp_id;
SELECT 'poi_intelligence_link references:' as table_name, source_id FROM poi_intelligence_link WHERE source_type = 'WHATSAPP' ORDER BY source_id;

COMMIT;
