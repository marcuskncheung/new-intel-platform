# 🚨 EMERGENCY FIX: Stage 1 Migration Not Complete

## Problem
The database migration from Stage 1 was not fully executed. The `case_profile` table is missing the new foreign key columns:
- `email_id`
- `whatsapp_id` 
- `patrol_id`

## Error Message
```
column "email_id" of relation "case_profile" does not exist
```

## Solution: Re-run Stage 1 Migration

### Step 1: SSH into Production Server
```bash
ssh user@your-server
cd /path/to/intelligence-platform
```

### Step 2: Run Migration Script
```bash
# Execute the migration
docker-compose exec intelligence-app python3 migrate_unified_int_postgres.py
```

### Step 3: Verify Migration Success
Look for output like:
```
✅ Phase 1: Added columns to case_profile
✅ Phase 2: Added caseprofile_id to source tables
✅ Phase 3: Created foreign key constraints
✅ Phase 4: Created performance indexes
✅ Migration completed successfully!
```

### Step 4: Restart Application
```bash
docker-compose restart intelligence-app
```

### Step 5: Test
1. Create a new WhatsApp entry
2. Should see: `[UNIFIED INT] WhatsApp entry X linked to INT-XXX`
3. No more "column does not exist" errors

## If Migration Script Fails

Run SQL directly:

```bash
docker-compose exec intelligence-db psql -U intelligence_user -d intelligence_db
```

Then paste:

```sql
-- Phase 1: Add columns to case_profile
ALTER TABLE case_profile ADD COLUMN IF NOT EXISTS email_id INTEGER;
ALTER TABLE case_profile ADD COLUMN IF NOT EXISTS whatsapp_id INTEGER;
ALTER TABLE case_profile ADD COLUMN IF NOT EXISTS patrol_id INTEGER;

-- Phase 2: Already done (caseprofile_id columns exist)

-- Phase 3: Add foreign key constraints
ALTER TABLE case_profile ADD CONSTRAINT IF NOT EXISTS fk_case_profile_email 
    FOREIGN KEY (email_id) REFERENCES email(id);
    
ALTER TABLE case_profile ADD CONSTRAINT IF NOT EXISTS fk_case_profile_whatsapp 
    FOREIGN KEY (whatsapp_id) REFERENCES whats_app_entry(id);
    
ALTER TABLE case_profile ADD CONSTRAINT IF NOT EXISTS fk_case_profile_patrol 
    FOREIGN KEY (patrol_id) REFERENCES online_patrol_entry(id);

-- Phase 4: Add indexes
CREATE INDEX IF NOT EXISTS idx_case_profile_email ON case_profile(email_id);
CREATE INDEX IF NOT EXISTS idx_case_profile_whatsapp ON case_profile(whatsapp_id);
CREATE INDEX IF NOT EXISTS idx_case_profile_patrol ON case_profile(patrol_id);

-- Exit
\q
```

## Verification Query

After migration, verify columns exist:

```bash
docker-compose exec intelligence-db psql -U intelligence_user -d intelligence_db -c "\d case_profile"
```

Should show:
```
email_id     | integer |
whatsapp_id  | integer |
patrol_id    | integer |
```

## Why This Happened

The previous migration run may have been interrupted or only partially completed. The Stage 1 migration has two parts:

1. **Reverse direction** (✅ DONE): Add `caseprofile_id` to source tables
2. **Forward direction** (❌ MISSING): Add `email_id`, `whatsapp_id`, `patrol_id` to case_profile

You need to complete part 2.

---

**After fixing, Stage 2 will work correctly!**
