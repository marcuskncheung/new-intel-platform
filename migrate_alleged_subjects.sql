-- ============================================================================
-- ALLEGED SUBJECT RELATIONAL TABLES MIGRATION
-- ============================================================================
-- Creates 3 tables to guarantee correct English-Chinese name pairing:
-- 1. whatsapp_alleged_subjects
-- 2. online_patrol_alleged_subjects
-- 3. received_by_hand_alleged_subjects
--
-- Usage (inside PostgreSQL Docker container):
--   psql -U postgres -d intelligence_db -f migrate_alleged_subjects.sql
-- ============================================================================

\echo ''
\echo '============================================================================'
\echo 'ALLEGED SUBJECT TABLES MIGRATION'
\echo '============================================================================'
\echo ''

-- Check current state
\echo 'Current tables with "alleged_subjects" in name:'
SELECT table_name 
FROM information_schema.tables 
WHERE table_name LIKE '%alleged_subjects' 
ORDER BY table_name;

\echo ''
\echo 'Creating tables...'
\echo ''

-- ============================================================================
-- TABLE 1: WhatsApp Alleged Subjects
-- ============================================================================
\echo '1. Creating whatsapp_alleged_subjects...'

CREATE TABLE IF NOT EXISTS whatsapp_alleged_subjects (
    id SERIAL PRIMARY KEY,
    whatsapp_id INTEGER NOT NULL,
    english_name VARCHAR(255),
    chinese_name VARCHAR(255),
    is_insurance_intermediary BOOLEAN DEFAULT FALSE,
    license_type VARCHAR(100),
    license_number VARCHAR(100),
    sequence_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key with CASCADE delete
    CONSTRAINT fk_whatsapp_alleged_whatsapp
        FOREIGN KEY (whatsapp_id) 
        REFERENCES whatsapp_entry(id) 
        ON DELETE CASCADE,
    
    -- At least one name must be provided
    CONSTRAINT check_whatsapp_has_name 
        CHECK (english_name IS NOT NULL OR chinese_name IS NOT NULL),
    
    -- Unique combination of whatsapp_id and sequence_order
    CONSTRAINT unique_whatsapp_subject 
        UNIQUE (whatsapp_id, sequence_order)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_whatsapp_alleged_subjects_whatsapp_id 
    ON whatsapp_alleged_subjects(whatsapp_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_alleged_subjects_english 
    ON whatsapp_alleged_subjects(english_name);
CREATE INDEX IF NOT EXISTS idx_whatsapp_alleged_subjects_chinese 
    ON whatsapp_alleged_subjects(chinese_name);

\echo '   ✓ whatsapp_alleged_subjects created'

-- ============================================================================
-- TABLE 2: Online Patrol Alleged Subjects
-- ============================================================================
\echo '2. Creating online_patrol_alleged_subjects...'

CREATE TABLE IF NOT EXISTS online_patrol_alleged_subjects (
    id SERIAL PRIMARY KEY,
    patrol_id INTEGER NOT NULL,
    english_name VARCHAR(255),
    chinese_name VARCHAR(255),
    is_insurance_intermediary BOOLEAN DEFAULT FALSE,
    license_type VARCHAR(100),
    license_number VARCHAR(100),
    sequence_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key with CASCADE delete
    CONSTRAINT fk_patrol_alleged_patrol
        FOREIGN KEY (patrol_id) 
        REFERENCES online_patrol_entry(id) 
        ON DELETE CASCADE,
    
    -- At least one name must be provided
    CONSTRAINT check_patrol_has_name 
        CHECK (english_name IS NOT NULL OR chinese_name IS NOT NULL),
    
    -- Unique combination of patrol_id and sequence_order
    CONSTRAINT unique_patrol_subject 
        UNIQUE (patrol_id, sequence_order)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_patrol_alleged_subjects_patrol_id 
    ON online_patrol_alleged_subjects(patrol_id);
CREATE INDEX IF NOT EXISTS idx_patrol_alleged_subjects_english 
    ON online_patrol_alleged_subjects(english_name);
CREATE INDEX IF NOT EXISTS idx_patrol_alleged_subjects_chinese 
    ON online_patrol_alleged_subjects(chinese_name);

\echo '   ✓ online_patrol_alleged_subjects created'

-- ============================================================================
-- TABLE 3: Received By Hand Alleged Subjects
-- ============================================================================
\echo '3. Creating received_by_hand_alleged_subjects...'

CREATE TABLE IF NOT EXISTS received_by_hand_alleged_subjects (
    id SERIAL PRIMARY KEY,
    received_by_hand_id INTEGER NOT NULL,
    english_name VARCHAR(255),
    chinese_name VARCHAR(255),
    is_insurance_intermediary BOOLEAN DEFAULT FALSE,
    license_type VARCHAR(100),
    license_number VARCHAR(100),
    sequence_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key with CASCADE delete
    CONSTRAINT fk_rbh_alleged_rbh
        FOREIGN KEY (received_by_hand_id) 
        REFERENCES received_by_hand_entry(id) 
        ON DELETE CASCADE,
    
    -- At least one name must be provided
    CONSTRAINT check_rbh_has_name 
        CHECK (english_name IS NOT NULL OR chinese_name IS NOT NULL),
    
    -- Unique combination of received_by_hand_id and sequence_order
    CONSTRAINT unique_rbh_subject 
        UNIQUE (received_by_hand_id, sequence_order)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_rbh_alleged_subjects_rbh_id 
    ON received_by_hand_alleged_subjects(received_by_hand_id);
CREATE INDEX IF NOT EXISTS idx_rbh_alleged_subjects_english 
    ON received_by_hand_alleged_subjects(english_name);
CREATE INDEX IF NOT EXISTS idx_rbh_alleged_subjects_chinese 
    ON received_by_hand_alleged_subjects(chinese_name);

\echo '   ✓ received_by_hand_alleged_subjects created'

-- ============================================================================
-- VERIFICATION
-- ============================================================================
\echo ''
\echo '============================================================================'
\echo 'VERIFICATION'
\echo '============================================================================'
\echo ''

\echo 'All tables with "alleged_subjects" in name:'
SELECT table_name 
FROM information_schema.tables 
WHERE table_name LIKE '%alleged_subjects' 
ORDER BY table_name;

\echo ''
\echo '============================================================================'
\echo 'TABLE STRUCTURES'
\echo '============================================================================'

\echo ''
\echo 'WhatsApp Alleged Subjects:'
\d whatsapp_alleged_subjects

\echo ''
\echo 'Online Patrol Alleged Subjects:'
\d online_patrol_alleged_subjects

\echo ''
\echo 'Received By Hand Alleged Subjects:'
\d received_by_hand_alleged_subjects

\echo ''
\echo '============================================================================'
\echo '✅ MIGRATION COMPLETE!'
\echo '============================================================================'
\echo ''
\echo 'Next steps:'
\echo '1. Restart your application: docker-compose restart web'
\echo '2. Test by creating entries with multiple alleged subjects'
\echo '3. Verify data is saved correctly in the new tables'
\echo ''
