# 🎯 CORRECTED Cleanup Commands for YOUR Server

**Your Actual Data:**
- Total: 183 case profiles
- Old migration: 179 (MIGRATION_SCRIPT) + 3 (RENUMBER_SCRIPT) = **182 to delete**
- Manual: 1 (USER-kinnamcheung) = **KEEP**
- Migration date: Oct 16, 2025

---

## ✅ **CORRECTED Step 2: Preview (Use This Instead)**

```bash
# Preview with CORRECT creator names
docker exec -i intelligence-db psql -U intelligence intelligence_db <<'EOF'
-- Check what will be deleted (CORRECTED QUERY)
SELECT COUNT(*) as will_be_deleted
FROM case_profile
WHERE created_by IN ('MIGRATION_SCRIPT', 'RENUMBER_SCRIPT')
   OR created_at < '2025-10-20';  -- Before your manual record

-- Show sample of what will be deleted
SELECT id, int_reference, source_type, created_at, created_by
FROM case_profile
WHERE created_by IN ('MIGRATION_SCRIPT', 'RENUMBER_SCRIPT')
   OR created_at < '2025-10-20'
ORDER BY id
LIMIT 10;

-- Show what will be KEPT
SELECT id, int_reference, source_type, created_at, created_by
FROM case_profile
WHERE created_by NOT IN ('MIGRATION_SCRIPT', 'RENUMBER_SCRIPT')
  AND created_at >= '2025-10-20';
EOF
```

**Expected result:** `will_be_deleted: 182`

---

## 🧹 **CORRECTED Step 3: Run Cleanup (Use This Instead)**

```bash
# Create CORRECTED cleanup script
cat > cleanup_old_migration_data.sql <<'EOF'
-- ============================================
-- CORRECTED CLEANUP FOR YOUR SERVER
-- Targets: MIGRATION_SCRIPT and RENUMBER_SCRIPT
-- ============================================

\echo '=== STEP 0: PREVIEW (CORRECTED) ==='
SELECT COUNT(*) as total_to_archive
FROM case_profile
WHERE created_by IN ('MIGRATION_SCRIPT', 'RENUMBER_SCRIPT');

\echo '\n=== Records to DELETE ==='
SELECT id, int_reference, source_type, created_at, created_by
FROM case_profile
WHERE created_by IN ('MIGRATION_SCRIPT', 'RENUMBER_SCRIPT')
ORDER BY id
LIMIT 10;

\echo '\n=== Records to KEEP ==='
SELECT id, int_reference, source_type, created_at, created_by
FROM case_profile
WHERE created_by NOT IN ('MIGRATION_SCRIPT', 'RENUMBER_SCRIPT');

\echo '\n=== Press Ctrl+C to cancel, or press Enter to continue ==='
\prompt 'Type YES to continue with cleanup: ' confirm

-- Step 1: Create archive
\echo '\n=== STEP 1: Creating archive table ==='
DROP TABLE IF EXISTS case_profile_migration_archive CASCADE;

CREATE TABLE case_profile_migration_archive AS
SELECT * FROM case_profile
WHERE created_by IN ('MIGRATION_SCRIPT', 'RENUMBER_SCRIPT');

ALTER TABLE case_profile_migration_archive 
ADD COLUMN archived_at TIMESTAMP DEFAULT NOW(),
ADD COLUMN archived_reason TEXT DEFAULT 'Old migration data - removed Oct 27, 2025';

\echo 'Archive created:'
SELECT COUNT(*) as archived_count FROM case_profile_migration_archive;

-- Step 2: Unlink emails
\echo '\n=== STEP 2: Unlinking emails from old CaseProfiles ==='
UPDATE email
SET caseprofile_id = NULL, email_id = NULL
WHERE caseprofile_id IN (
    SELECT id FROM case_profile_migration_archive
);

\echo 'Emails unlinked:'
SELECT COUNT(*) as unlinked_emails FROM email WHERE caseprofile_id IS NULL;

-- Step 3: Delete old records
\echo '\n=== STEP 3: Deleting 182 old migration records ==='
DELETE FROM case_profile
WHERE id IN (SELECT id FROM case_profile_migration_archive);

-- Step 4: Show results
\echo '\n=== STEP 4: RESULTS ==='
\echo 'Remaining case profiles (should be 1):'
SELECT COUNT(*) as remaining_case_profiles FROM case_profile;

\echo '\nArchived records (should be 182):'
SELECT COUNT(*) as archived_records FROM case_profile_migration_archive;

\echo '\nWhat is left (should be your 1 manual record):'
SELECT id, int_reference, source_type, created_at, created_by
FROM case_profile;

\echo '\nEmails without INT (will need manual re-assignment):'
SELECT COUNT(*) as emails_without_int FROM email WHERE caseprofile_id IS NULL;

\echo '\n=== ✅ CLEANUP COMPLETE! ==='
\echo 'Next steps:'
\echo '1. Verify the 1 remaining case_profile is your manual record'
\echo '2. Go to https://10.96.135.11/int_source'
\echo '3. Manually assign INT numbers to emails based on actual cases'
EOF

# Run the CORRECTED cleanup script
docker exec -i intelligence-db psql -U intelligence intelligence_db < cleanup_old_migration_data.sql
```

---

## 📊 **Expected Results After Cleanup:**

**Before:**
```
case_profile: 183 records
- 182 from migration scripts (JUNK)
- 1 manual (GOOD)
```

**After:**
```
case_profile: 1 record (only your manual one)
case_profile_migration_archive: 182 archived records
email: Many without caseprofile_id (need re-assignment)
```

---

## ✅ **Step 4: Verify (After Cleanup)**

```bash
# Check results
docker exec -i intelligence-db psql -U intelligence intelligence_db <<'EOF'
-- Should show 1 remaining
SELECT COUNT(*) as remaining FROM case_profile;

-- Should show 182 archived
SELECT COUNT(*) as archived FROM case_profile_migration_archive;

-- Show the 1 record that remains
SELECT * FROM case_profile;

-- How many emails need INT assignment
SELECT COUNT(*) as emails_without_int FROM email WHERE caseprofile_id IS NULL;

-- Show first 10 emails needing INT
SELECT id, entry_id, subject, sender, received
FROM email
WHERE caseprofile_id IS NULL
ORDER BY received DESC
LIMIT 10;
EOF
```

---

## 🎯 **Quick Summary - What Changed:**

**OLD QUERY (Wrong):**
```sql
WHERE created_by IN ('MIGRATION', 'SYSTEM', 'AI_AUTO')
```
❌ This matched 0 records because your creator is `MIGRATION_SCRIPT`

**NEW QUERY (Correct):**
```sql
WHERE created_by IN ('MIGRATION_SCRIPT', 'RENUMBER_SCRIPT')
```
✅ This matches 182 records (all the old junk)

---

## 🚀 **Run This Now:**

```bash
# 1. Preview with CORRECT query
docker exec -i intelligence-db psql -U intelligence intelligence_db <<'EOF'
SELECT COUNT(*) as will_be_deleted
FROM case_profile
WHERE created_by IN ('MIGRATION_SCRIPT', 'RENUMBER_SCRIPT');
EOF

# Should show: will_be_deleted: 182
# If yes, proceed with cleanup script above!
```

**After cleanup, you'll need to manually assign INT numbers to ~180 emails via the web interface!**

Would you like me to create a helper script to make INT assignment faster? 😊
