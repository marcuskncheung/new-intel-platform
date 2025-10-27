# 🚀 Ready-to-Run Commands for Your Server

**Server:** saiuapp11  
**User:** pam-du-uat-ai  
**Database User:** intelligence  
**Database Name:** intelligence_db  

---

## ✅ **Step 1: Create Backup (DO THIS FIRST!)**

```bash
# Create backup with correct username
docker exec intelligence-db pg_dump -U intelligence intelligence_db > /tmp/backup_before_cleanup_$(date +%Y%m%d_%H%M%S).sql

# Check backup was created and see size
ls -lh /tmp/backup_*.sql | tail -1

# If size looks good (should be > 1MB), copy to safe location
mkdir -p ~/backups
cp /tmp/backup_*.sql ~/backups/
```

**Expected output:**
```
-rw-r--r-- 1 pam-du-uat-ai pam-du-uat-ai 5.2M Oct 27 14:30 /tmp/backup_before_cleanup_20251027_143015.sql
```

✅ If you see a file with size > 1MB, backup is successful!

---

## 🔍 **Step 2: Preview What Will Be Cleaned**

```bash
# Quick check of your data
docker exec -i intelligence-db psql -U intelligence intelligence_db <<'EOF'
-- Total case profiles
SELECT COUNT(*) as total_case_profiles FROM case_profile;

-- By creator
SELECT 
    COALESCE(created_by, 'NULL') as creator,
    COUNT(*) as count
FROM case_profile
GROUP BY created_by
ORDER BY COUNT(*) DESC;

-- By date
SELECT 
    DATE(created_at) as date,
    COUNT(*) as count
FROM case_profile
GROUP BY DATE(created_at)
ORDER BY date DESC
LIMIT 10;

-- Check what will be deleted (preview)
SELECT COUNT(*) as will_be_deleted
FROM case_profile
WHERE (created_by IN ('MIGRATION', 'SYSTEM', 'AI_AUTO') OR created_by IS NULL)
  AND created_at < '2025-01-01';
EOF
```

**Review the output** - make sure you're comfortable with what will be deleted!

---

## 🧹 **Step 3: Run Cleanup (After Reviewing Preview)**

```bash
# Create the cleanup script
cat > cleanup_old_migration_data.sql <<'EOF'
-- ============================================
-- CLEANUP OLD MIGRATION DATA
-- For saiuapp11 intelligence platform
-- ============================================

\echo '=== STEP 0: PREVIEW ==='
SELECT COUNT(*) as total_to_archive
FROM case_profile
WHERE (created_by IN ('MIGRATION', 'SYSTEM', 'AI_AUTO') OR created_by IS NULL)
  AND created_at < '2025-01-01';

\echo '\n=== Showing first 10 records to be archived ==='
SELECT id, int_reference, source_type, created_at, created_by
FROM case_profile
WHERE (created_by IN ('MIGRATION', 'SYSTEM', 'AI_AUTO') OR created_by IS NULL)
  AND created_at < '2025-01-01'
ORDER BY id
LIMIT 10;

\echo '\n=== Press Ctrl+C to cancel, or press Enter to continue ==='
\prompt 'Type YES to continue: ' confirm

-- Step 1: Create archive
\echo '\n=== STEP 1: Creating archive table ==='
DROP TABLE IF EXISTS case_profile_migration_archive CASCADE;

CREATE TABLE case_profile_migration_archive AS
SELECT * FROM case_profile
WHERE (created_by IN ('MIGRATION', 'SYSTEM', 'AI_AUTO') OR created_by IS NULL)
  AND created_at < '2025-01-01';

ALTER TABLE case_profile_migration_archive 
ADD COLUMN archived_at TIMESTAMP DEFAULT NOW(),
ADD COLUMN archived_reason TEXT DEFAULT 'Old migration data - replaced with manual case grouping';

SELECT COUNT(*) as archived_count FROM case_profile_migration_archive;

-- Step 2: Unlink emails
\echo '\n=== STEP 2: Unlinking emails from old CaseProfiles ==='
UPDATE email
SET caseprofile_id = NULL, email_id = NULL
WHERE caseprofile_id IN (
    SELECT id FROM case_profile_migration_archive
);

SELECT COUNT(*) as unlinked_emails FROM email WHERE caseprofile_id IS NULL;

-- Step 3: Delete old records
\echo '\n=== STEP 3: Deleting old migration records ==='
DELETE FROM case_profile
WHERE id IN (SELECT id FROM case_profile_migration_archive);

-- Step 4: Show results
\echo '\n=== STEP 4: Results ==='
SELECT COUNT(*) as remaining_case_profiles FROM case_profile;
SELECT COUNT(*) as archived_records FROM case_profile_migration_archive;
SELECT COUNT(*) as emails_without_int FROM email WHERE caseprofile_id IS NULL;

\echo '\n=== CLEANUP COMPLETE! ==='
\echo 'Next: Go to https://10.96.135.11/int_source and manually assign INT numbers to emails'
EOF

# Run the cleanup script
docker exec -i intelligence-db psql -U intelligence intelligence_db < cleanup_old_migration_data.sql
```

---

## ✅ **Step 4: Verify Cleanup Worked**

```bash
# Check results
docker exec -i intelligence-db psql -U intelligence intelligence_db <<'EOF'
-- Should show reduced count
SELECT COUNT(*) as remaining_case_profiles FROM case_profile;

-- Should show archived count
SELECT COUNT(*) as archived_records FROM case_profile_migration_archive;

-- Show what's left
SELECT id, int_reference, source_type, created_at, created_by
FROM case_profile
ORDER BY id;

-- Emails without INT (will need manual assignment)
SELECT COUNT(*) as emails_without_int FROM email WHERE caseprofile_id IS NULL;
EOF
```

---

## 🔄 **Step 5: Manually Re-assign INT References**

Now go to your web interface and assign INT numbers:

1. **Open:** https://10.96.135.11/int_source
2. **Click:** Each email without INT reference
3. **Assign:** INT number based on case content
   - Same person + same issue = Same INT ✅
   - Different case = Different INT ✅

**Query to see emails needing INT:**
```bash
docker exec -i intelligence-db psql -U intelligence intelligence_db <<'EOF'
SELECT id, entry_id, subject, sender, received
FROM email
WHERE caseprofile_id IS NULL
ORDER BY received DESC
LIMIT 20;
EOF
```

---

## 🆘 **Emergency: Restore Backup**

If something goes wrong:

```bash
# Find your backup
ls -lh /tmp/backup_*.sql ~/backups/backup_*.sql

# Restore (replace FILENAME with actual backup name)
docker exec -i intelligence-db psql -U intelligence intelligence_db < /tmp/backup_before_cleanup_YYYYMMDD_HHMMSS.sql

# Verify restoration
docker exec -i intelligence-db psql -U intelligence intelligence_db -c "SELECT COUNT(*) FROM case_profile;"
```

---

## 📊 **Useful Monitoring Queries**

**Check progress of INT assignment:**
```bash
docker exec -i intelligence-db psql -U intelligence intelligence_db <<'EOF'
SELECT 
    COUNT(*) as total_emails,
    COUNT(caseprofile_id) as with_int,
    COUNT(*) - COUNT(caseprofile_id) as without_int,
    ROUND(100.0 * COUNT(caseprofile_id) / COUNT(*), 1) as percent_assigned
FROM email;
EOF
```

**See all active case profiles:**
```bash
docker exec -i intelligence-db psql -U intelligence intelligence_db <<'EOF'
SELECT 
    cp.id,
    cp.int_reference,
    cp.created_at,
    cp.created_by,
    COUNT(e.id) as email_count,
    COUNT(w.id) as whatsapp_count,
    COUNT(p.id) as patrol_count
FROM case_profile cp
LEFT JOIN email e ON e.caseprofile_id = cp.id
LEFT JOIN whats_app_entry w ON w.caseprofile_id = cp.id
LEFT JOIN online_patrol_entry p ON p.caseprofile_id = cp.id
GROUP BY cp.id, cp.int_reference, cp.created_at, cp.created_by
ORDER BY cp.id;
EOF
```

---

## 🎯 **Summary**

1. ✅ **Backup** (Step 1) - CRITICAL!
2. 🔍 **Preview** (Step 2) - See what will change
3. 🧹 **Cleanup** (Step 3) - Remove old data
4. ✅ **Verify** (Step 4) - Check it worked
5. ✍️ **Re-assign** (Step 5) - Manual INT assignment
6. 🎉 **Done!** - Clean database with meaningful INT references

---

## 💡 **Tips**

- **Backup size:** Should be 1-10 MB depending on data
- **Cleanup time:** Takes 30-60 seconds
- **Re-assignment:** Budget 5-10 minutes per 20 emails
- **Peak hours:** Avoid 9am-5pm when users are active
- **Test first:** If nervous, ask me to create a test query first

Good luck! 🚀
