-- Migration: POI v2.0 Schema Upgrade
-- Adds new columns to alleged_person_profile table for enhanced POI tracking
-- Run this on PostgreSQL database

BEGIN;

-- Add identity columns
ALTER TABLE alleged_person_profile 
ADD COLUMN IF NOT EXISTS name_normalized VARCHAR(200),
ADD COLUMN IF NOT EXISTS aliases JSONB,
ADD COLUMN IF NOT EXISTS date_of_birth DATE,
ADD COLUMN IF NOT EXISTS identification_number VARCHAR(50);

-- Add contact information columns
ALTER TABLE alleged_person_profile
ADD COLUMN IF NOT EXISTS phone_numbers JSONB,
ADD COLUMN IF NOT EXISTS email_addresses JSONB,
ADD COLUMN IF NOT EXISTS whatsapp_numbers JSONB,
ADD COLUMN IF NOT EXISTS addresses JSONB;

-- Add professional information columns
ALTER TABLE alleged_person_profile
ADD COLUMN IF NOT EXISTS agent_number VARCHAR(50),
ADD COLUMN IF NOT EXISTS license_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS license_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS company_code VARCHAR(50),
ADD COLUMN IF NOT EXISTS role VARCHAR(100),
ADD COLUMN IF NOT EXISTS employment_history JSONB;

-- Add assessment & risk scoring columns
ALTER TABLE alleged_person_profile
ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20),
ADD COLUMN IF NOT EXISTS risk_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS threat_classification JSONB,
ADD COLUMN IF NOT EXISTS watchlist_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS priority_level INTEGER DEFAULT 3,
ADD COLUMN IF NOT EXISTS assessment_notes TEXT;

-- Add intelligence statistics columns
ALTER TABLE alleged_person_profile
ADD COLUMN IF NOT EXISTS total_mentions INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS email_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS whatsapp_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS patrol_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS surveillance_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS case_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS first_mentioned_date TIMESTAMP,
ADD COLUMN IF NOT EXISTS last_mentioned_date TIMESTAMP,
ADD COLUMN IF NOT EXISTS last_activity_date TIMESTAMP;

-- Add misconduct tracking columns
ALTER TABLE alleged_person_profile
ADD COLUMN IF NOT EXISTS alleged_misconducts JSONB,
ADD COLUMN IF NOT EXISTS proven_violations JSONB,
ADD COLUMN IF NOT EXISTS investigation_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS substantiated_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS unsubstantiated_count INTEGER DEFAULT 0;

-- Add relationship mapping columns
ALTER TABLE alleged_person_profile
ADD COLUMN IF NOT EXISTS associated_pois JSONB,
ADD COLUMN IF NOT EXISTS organization_links JSONB,
ADD COLUMN IF NOT EXISTS network_centrality FLOAT;

-- Add AI/automation metadata columns
ALTER TABLE alleged_person_profile
ADD COLUMN IF NOT EXISTS deduplication_group_id VARCHAR(50),
ADD COLUMN IF NOT EXISTS merge_confidence FLOAT,
ADD COLUMN IF NOT EXISTS auto_enriched BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS last_enrichment_date TIMESTAMP,
ADD COLUMN IF NOT EXISTS data_sources JSONB;

-- Add status & control columns
ALTER TABLE alleged_person_profile
ADD COLUMN IF NOT EXISTS merged_into_poi_id VARCHAR(20),
ADD COLUMN IF NOT EXISTS is_high_priority BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS requires_approval BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS approved_by VARCHAR(100),
ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;

-- Add audit trail columns (if they don't exist)
ALTER TABLE alleged_person_profile
ADD COLUMN IF NOT EXISTS created_by VARCHAR(100),
ADD COLUMN IF NOT EXISTS updated_by VARCHAR(100),
ADD COLUMN IF NOT EXISTS last_reviewed_date TIMESTAMP;

-- Create indexes for new columns
CREATE INDEX IF NOT EXISTS idx_poi_name_normalized ON alleged_person_profile(name_normalized);
CREATE INDEX IF NOT EXISTS idx_poi_risk_level ON alleged_person_profile(risk_level);
CREATE INDEX IF NOT EXISTS idx_poi_last_activity ON alleged_person_profile(last_activity_date);

-- Add foreign key constraint for self-referencing merge
ALTER TABLE alleged_person_profile
DROP CONSTRAINT IF EXISTS fk_merged_into_poi;

ALTER TABLE alleged_person_profile
ADD CONSTRAINT fk_merged_into_poi 
FOREIGN KEY (merged_into_poi_id) 
REFERENCES alleged_person_profile(poi_id);

COMMIT;

-- Verify migration
SELECT 
    'Migration completed successfully. New columns added to alleged_person_profile table.' AS status,
    COUNT(*) AS total_profiles
FROM alleged_person_profile;
