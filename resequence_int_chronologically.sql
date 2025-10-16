-- ========================================
-- CHRONOLOGICAL INT RE-SEQUENCING (SQL Version)
-- ========================================
-- This script re-sequences all INT references in chronological order
-- Run this on production PostgreSQL database

-- Step 1: Backup current state
CREATE TABLE IF NOT EXISTS case_profile_backup_before_resequence AS 
SELECT * FROM case_profile;

SELECT 'Backup created with ' || COUNT(*) || ' records' as backup_status
FROM case_profile_backup_before_resequence;

-- Step 2: Show current out-of-order entries
SELECT 
    index as current_int,
    index_order,
    source_type,
    date_of_receipt,
    CASE 
        WHEN email_id IS NOT NULL THEN CONCAT('Email:', email_id)
        WHEN whatsapp_id IS NOT NULL THEN CONCAT('WhatsApp:', whatsapp_id)
        WHEN patrol_id IS NOT NULL THEN CONCAT('Patrol:', patrol_id)
        ELSE 'Unknown'
    END as source_record
FROM case_profile
ORDER BY date_of_receipt ASC;

-- Step 3: Create temporary table with correct chronological order
CREATE TEMP TABLE resequenced_case_profile AS
SELECT 
    id,
    'INT-' || LPAD(ROW_NUMBER() OVER (ORDER BY date_of_receipt ASC)::text, 3, '0') as new_index,
    ROW_NUMBER() OVER (ORDER BY date_of_receipt ASC) as new_index_order,
    date_of_receipt,
    source_type,
    index as old_index,
    index_order as old_index_order
FROM case_profile
ORDER BY date_of_receipt ASC;

-- Step 4: Show what will change
SELECT 
    old_index as "Old INT",
    new_index as "New INT",
    source_type as "Type",
    TO_CHAR(date_of_receipt, 'YYYY-MM-DD HH24:MI') as "Receipt Date"
FROM resequenced_case_profile
WHERE old_index != new_index
ORDER BY date_of_receipt ASC;

-- Step 5: Apply the changes (UNCOMMENT TO EXECUTE)
/*
UPDATE case_profile
SET 
    index = r.new_index,
    index_order = r.new_index_order
FROM resequenced_case_profile r
WHERE case_profile.id = r.id;

SELECT 'Re-sequencing complete! Updated ' || COUNT(*) || ' records' as status
FROM resequenced_case_profile
WHERE old_index != new_index;
*/

-- Step 6: Verify final state (run after uncommenting Step 5)
/*
SELECT 
    index as int_ref,
    index_order,
    source_type,
    TO_CHAR(date_of_receipt, 'YYYY-MM-DD HH24:MI') as receipt_date,
    CASE 
        WHEN email_id IS NOT NULL THEN CONCAT('Email:', email_id)
        WHEN whatsapp_id IS NOT NULL THEN CONCAT('WhatsApp:', whatsapp_id)
        WHEN patrol_id IS NOT NULL THEN CONCAT('Patrol:', patrol_id)
    END as source
FROM case_profile
ORDER BY date_of_receipt ASC;
*/

-- ========================================
-- INSTRUCTIONS:
-- ========================================
-- 1. Run Steps 1-4 to see what will change
-- 2. Review the output carefully
-- 3. If correct, uncomment Step 5 and run it
-- 4. Run Step 6 to verify
-- 5. If something goes wrong, restore from backup:
--    INSERT INTO case_profile SELECT * FROM case_profile_backup_before_resequence;
