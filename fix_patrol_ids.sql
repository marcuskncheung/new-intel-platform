-- Fix Online Patrol IDs to start from 1
-- This script renumbers existing patrol entries and resets the auto-increment sequence

BEGIN;

-- Create a temporary table to store the mapping
CREATE TEMP TABLE patrol_id_mapping AS
SELECT 
    id as old_id,
    ROW_NUMBER() OVER (ORDER BY id) as new_id
FROM online_patrol_entry
ORDER BY id;

-- Show what will be changed
SELECT 
    old_id as "Current ID",
    new_id as "New ID",
    'PATROL-' || old_id as "Current Display",
    'PATROL-' || new_id as "New Display"
FROM patrol_id_mapping;

-- Update foreign key references in case_profile table first
UPDATE case_profile 
SET patrol_id = mapping.new_id
FROM patrol_id_mapping mapping
WHERE case_profile.patrol_id = mapping.old_id;

-- Create new table with correct IDs
CREATE TABLE online_patrol_entry_new (LIKE online_patrol_entry INCLUDING ALL);

-- Copy data with new IDs
INSERT INTO online_patrol_entry_new
SELECT 
    mapping.new_id as id,
    ope.complaint_name,
    ope.contact_number,
    ope.alleged_person,
    ope.alleged_type,
    ope.alleged_nature,
    ope.source,
    ope.details,
    ope.source_reliability,
    ope.content_validity,
    ope.preparer,
    ope.complaint_time,
    ope.source_time,
    ope.discovery_time,
    ope.discoverer_name,
    ope.reviewer_name,
    ope.reviewer_comment,
    ope.caseprofile_id,
    ope.received_time
FROM online_patrol_entry ope
JOIN patrol_id_mapping mapping ON ope.id = mapping.old_id
ORDER BY mapping.new_id;

-- Drop old table and rename new one
DROP TABLE online_patrol_entry CASCADE;
ALTER TABLE online_patrol_entry_new RENAME TO online_patrol_entry;

-- Reset the sequence to start from the highest ID + 1
SELECT setval('online_patrol_entry_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM online_patrol_entry), false);

-- Verify the changes
SELECT 
    id,
    'PATROL-' || id as display_id,
    complaint_name,
    alleged_person,
    source_time
FROM online_patrol_entry
ORDER BY id;

COMMIT;

-- Show final status
SELECT 
    'Total patrol entries' as status,
    COUNT(*) as count
FROM online_patrol_entry
UNION ALL
SELECT 
    'Next ID will be',
    last_value
FROM online_patrol_entry_id_seq;
