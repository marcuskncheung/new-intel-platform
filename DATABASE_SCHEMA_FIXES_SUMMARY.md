# Database Schema Fixes Summary

## Overview
This document summarizes all database schema mismatches found and fixed during deployment.

## Issues Fixed

### 1. POIIntelligenceLink Schema Mismatch ✅
**Problem**: Model had columns that don't exist in database
- ❌ `created_by` 
- ❌ `updated_at`

**Actual Database Columns** (verified via `\d poi_intelligence_link`):
```
id, poi_id, case_profile_id, source_type, source_id, 
extraction_method, confidence_score, created_at
```

**Fix**: 
- Removed `created_by` and `updated_at` from model
- Added `extraction_method` column
- Updated all routes to use `extraction_method` instead of `created_by`

**Files Changed**:
- `models_poi_enhanced.py` - Fixed model definition
- `app1_production.py` - Updated WhatsApp and Patrol routes
- `alleged_person_automation.py` - Updated universal link creation

**Impact**: POI profiles can now be deleted, WhatsApp/Patrol links work correctly

---

### 2. POIAssessmentHistory Schema Mismatch ✅
**Problem**: Model defines many columns that don't exist in database

**Columns That Don't Exist**:
- ❌ `previous_risk_score`
- ❌ `new_risk_score`
- ❌ `assessment_reason`
- ❌ `assessment_notes`
- ❌ `supporting_evidence` (JSONB)
- ❌ `related_case_profiles` (JSONB)
- ❌ `trigger_source_type`
- ❌ `trigger_source_id`

**Columns That DO Exist**:
- ✅ `id`
- ✅ `poi_id`
- ✅ `assessed_by`
- ✅ `assessment_date`
- ✅ `previous_risk_level`
- ✅ `new_risk_level`

**Fix**:
- Commented out non-existent columns in model
- Disabled `assessment_history` relationship in `AllegedPersonProfile`
- Prevents cascade delete errors

**Files Changed**:
- `models_poi_enhanced.py` - Commented out columns and relationship

**Impact**: POI profiles can now be deleted without assessment_history errors

---

## Database Schema Verification Commands

Run these on your server to verify table structures:

```bash
# POI Intelligence Link table
sudo docker exec -i intelligence-db psql -U intelligence -d intelligence_db -c "\d poi_intelligence_link"

# POI Assessment History table
sudo docker exec -i intelligence-db psql -U intelligence -d intelligence_db -c "\d poi_assessment_history"

# Alleged Person Profile table
sudo docker exec -i intelligence-db psql -U intelligence -d intelligence_db -c "\d alleged_person_profile"

# List all tables
sudo docker exec -i intelligence-db psql -U intelligence -d intelligence_db -c "\dt"
```

---

## Recommended: Full Schema Migration

To properly implement all POI v2.0 features, you should run a complete database migration that creates all tables with correct schemas.

### Option 1: SQL Migration (Recommended)
```bash
# Create migration script
cat > /tmp/poi_v2_schema.sql << 'EOF'
-- Add missing columns to poi_assessment_history
ALTER TABLE poi_assessment_history 
ADD COLUMN IF NOT EXISTS previous_risk_score INTEGER,
ADD COLUMN IF NOT EXISTS new_risk_score INTEGER,
ADD COLUMN IF NOT EXISTS assessment_reason TEXT,
ADD COLUMN IF NOT EXISTS assessment_notes TEXT,
ADD COLUMN IF NOT EXISTS supporting_evidence JSONB,
ADD COLUMN IF NOT EXISTS related_case_profiles JSONB,
ADD COLUMN IF NOT EXISTS trigger_source_type VARCHAR(20),
ADD COLUMN IF NOT EXISTS trigger_source_id INTEGER;
EOF

# Run migration
docker cp /tmp/poi_v2_schema.sql intelligence-db:/tmp/
docker exec -i intelligence-db psql -U intelligence -d intelligence_db -f /tmp/poi_v2_schema.sql
```

### Option 2: Python Migration
Use the migration scripts in the repository:
- `migrate_poi_v2_python.py` (incomplete - placeholder)
- `migrations/01_poi_architecture_upgrade.sql` (if exists)

---

## Testing After Deployment

### Test POI Deletion:
1. Go to POI profile page
2. Click "Delete Profile"
3. Should succeed without errors ✅

### Test Intelligence Linking:
1. Create/edit WhatsApp assessment with alleged subject
2. Save
3. Check POI profile - should show WhatsApp intelligence ✅

4. Create/edit Online Patrol assessment with alleged subject
5. Save
6. Check POI profile - should show patrol intelligence ✅

---

## Commits

1. **022a53d** - Fix POIIntelligenceLink model schema and template URL errors
2. **18d501d** - Fix POI profile names not updating from ALL assessment edits
3. **3ea047a** - Fix POI deletion error due to POIAssessmentHistory schema mismatch

---

## Future Work

### High Priority:
- [ ] Run full schema migration to add missing poi_assessment_history columns
- [ ] Re-enable assessment_history relationship after migration
- [ ] Test risk assessment features

### Medium Priority:
- [ ] Verify all other table schemas match models
- [ ] Add database schema validation tests
- [ ] Document all database schema changes

### Low Priority:
- [ ] Consider using Alembic for future migrations
- [ ] Add schema version tracking
