-- Migration: Change alleged_nature column from VARCHAR(255) to TEXT
-- This fixes the error: "value too long for type character varying(255)"

BEGIN;

-- Check current column type
SELECT 
    column_name, 
    data_type, 
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'email' 
AND column_name = 'alleged_nature';

-- Change column type to TEXT
ALTER TABLE email 
ALTER COLUMN alleged_nature TYPE TEXT;

-- Verify the change
SELECT 
    column_name, 
    data_type
FROM information_schema.columns 
WHERE table_name = 'email' 
AND column_name = 'alleged_nature';

COMMIT;
