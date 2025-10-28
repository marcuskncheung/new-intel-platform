-- Fix missing received_by_hand_id column in case_profile table
-- Run this on the server to fix the database error

-- Check if the column exists first
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'case_profile' 
                   AND column_name = 'received_by_hand_id') THEN
        -- Add the missing column
        ALTER TABLE case_profile 
        ADD COLUMN received_by_hand_id INTEGER 
        REFERENCES received_by_hand_entry(id);
        
        -- Create index for performance
        CREATE INDEX idx_case_profile_received_by_hand_id 
        ON case_profile(received_by_hand_id);
        
        RAISE NOTICE 'Successfully added received_by_hand_id column to case_profile table';
    ELSE
        RAISE NOTICE 'Column received_by_hand_id already exists in case_profile table';
    END IF;
END $$;
