-- Simple fix: Change the single WhatsApp entry from ID=41 to ID=1
-- Since there's only 1 entry, this is much simpler!

BEGIN;

-- Backup first
CREATE TABLE IF NOT EXISTS whatsapp_backup_simple AS SELECT * FROM whats_app_entry;

-- Show before
SELECT 'BEFORE:' as status, id, complaint_name, received_time FROM whats_app_entry;

-- Temporarily disable triggers to avoid foreign key issues
SET CONSTRAINTS ALL DEFERRED;

-- Update related tables first (if any references exist)
UPDATE whats_app_image SET whatsapp_id = 1 WHERE whatsapp_id = 41;
UPDATE case_profile SET whatsapp_id = 1 WHERE whatsapp_id = 41;
UPDATE poi_intelligence_link SET source_id = '1' WHERE source_type = 'WHATSAPP' AND source_id = '41';

-- Now update the main table
UPDATE whats_app_entry SET id = 1 WHERE id = 41;

-- Reset sequence to start from 2 (next entry will be ID=2)
SELECT setval('whats_app_entry_id_seq', 2, false);

-- Show after
SELECT 'AFTER:' as status, id, complaint_name, received_time FROM whats_app_entry;
SELECT 'Next ID will be:' as info, nextval('whats_app_entry_id_seq') as next_id;
SELECT setval('whats_app_entry_id_seq', 2, false); -- Reset back to 2

-- Verify related tables
SELECT 'case_profile references:' as table_name, whatsapp_id FROM case_profile WHERE whatsapp_id IS NOT NULL;
SELECT 'whats_app_image references:' as table_name, whatsapp_id FROM whats_app_image;

COMMIT;

SELECT '✅ Success! WhatsApp entry is now ID=1, next entry will be ID=2' as result;
