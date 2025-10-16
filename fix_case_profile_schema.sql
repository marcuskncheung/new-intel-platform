-- ========================================
-- FIX: Add missing reverse foreign keys to case_profile
-- ========================================
-- This completes the Stage 1 migration for unified INT system
-- Run this on production PostgreSQL database

-- Step 1: Add missing columns
ALTER TABLE case_profile ADD COLUMN IF NOT EXISTS email_id INTEGER;
ALTER TABLE case_profile ADD COLUMN IF NOT EXISTS whatsapp_id INTEGER;
ALTER TABLE case_profile ADD COLUMN IF NOT EXISTS patrol_id INTEGER;

-- Step 2: Add foreign key constraints
ALTER TABLE case_profile 
    ADD CONSTRAINT IF NOT EXISTS fk_case_profile_email 
    FOREIGN KEY (email_id) REFERENCES email(id) ON DELETE SET NULL;

ALTER TABLE case_profile 
    ADD CONSTRAINT IF NOT EXISTS fk_case_profile_whatsapp 
    FOREIGN KEY (whatsapp_id) REFERENCES whats_app_entry(id) ON DELETE SET NULL;

ALTER TABLE case_profile 
    ADD CONSTRAINT IF NOT EXISTS fk_case_profile_patrol 
    FOREIGN KEY (patrol_id) REFERENCES online_patrol_entry(id) ON DELETE SET NULL;

-- Step 3: Add performance indexes
CREATE INDEX IF NOT EXISTS idx_case_profile_email ON case_profile(email_id);
CREATE INDEX IF NOT EXISTS idx_case_profile_whatsapp ON case_profile(whatsapp_id);
CREATE INDEX IF NOT EXISTS idx_case_profile_patrol ON case_profile(patrol_id);

-- Step 4: Verify the changes
\d case_profile

-- Expected output: Should show email_id, whatsapp_id, patrol_id columns with foreign keys
