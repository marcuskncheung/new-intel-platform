-- Simple SQL fix to run directly in the database container
-- No Python, no passwords, just pure SQL

\echo '🚀 Checking and fixing received_by_hand_id column...'

-- Check if column exists and add if missing
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'case_profile' 
        AND column_name = 'received_by_hand_id'
    ) THEN
        -- Add the missing column
        ALTER TABLE case_profile 
        ADD COLUMN received_by_hand_id INTEGER 
        REFERENCES received_by_hand_entry(id);
        
        -- Create index for performance
        CREATE INDEX idx_case_profile_received_by_hand_id 
        ON case_profile(received_by_hand_id);
        
        RAISE NOTICE '✅ Successfully added received_by_hand_id column';
    ELSE
        RAISE NOTICE '✅ Column received_by_hand_id already exists';
    END IF;
END $$;

\echo '🎉 Database fix completed!'
