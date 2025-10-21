-- Fix POI Intelligence Link Schema
-- Make case_profile_id nullable since not all intelligence sources have cases

ALTER TABLE poi_intelligence_link 
ALTER COLUMN case_profile_id DROP NOT NULL;

-- Verify the change
\d poi_intelligence_link
