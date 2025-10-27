# 🔄 Migration Cleanup Guide: Old INT System → New CaseProfile System

## 🎯 **Your Situation:**

### **OLD SYSTEM (Wrong Approach):**
```
Migration script auto-assigned INT numbers to every email:
- Email #1 → INT-001 (random assignment)
- Email #2 → INT-002 (random assignment)
- Email #3 → INT-003 (random assignment)
- Created 200+ CaseProfile records (one per email)
- No grouping by actual case content
```

### **NEW SYSTEM (Correct Approach):**
```
Manual assignment based on ACTUAL case content:
- Email #191 + Email #205 + WhatsApp #42 → INT-001 (same person, same complaint)
- Email #193 + Patrol #18 → INT-002 (same case)
- Each INT number represents a REAL investigation case
```

### **PROBLEM:**
```
case_profile table now contains:
- 200+ old records (auto-assigned, meaningless)
- Mixed with new records (manually assigned, meaningful)
- Can't tell which is which!
```

---

## ✅ **SOLUTION: Clean Up Old Migration Data**

### **Step 1: Identify Old vs New Records**

**Query to see what you have:**
```sql
-- Check all case profiles with their creation dates
SELECT 
    id,
    int_reference,
    source_type,
    created_at,
    created_by,
    (SELECT COUNT(*) FROM email WHERE caseprofile_id = cp.id) as email_count,
    (SELECT COUNT(*) FROM whats_app_entry WHERE caseprofile_id = cp.id) as whatsapp_count,
    (SELECT COUNT(*) FROM online_patrol_entry WHERE caseprofile_id = cp.id) as patrol_count
FROM case_profile cp
ORDER BY id;
```

**Look for patterns:**
```sql
-- Old migration records typically have:
-- 1. created_by = 'MIGRATION' or 'SYSTEM' or 'AI_AUTO'
-- 2. One source only (email_count=1, whatsapp_count=0, patrol_count=0)
-- 3. Created on same date (bulk migration)
-- 4. Sequential INT references (INT-001, INT-002, INT-003...)

-- New manual records typically have:
-- 1. created_by = actual username (marcus, kitty, etc.)
-- 2. Multiple sources possible (email_count≥1, might have whatsapp/patrol)
-- 3. Created on different dates (as cases come in)
-- 4. Non-sequential INT references based on case importance
```

---

### **Step 2: Backup Your Database First! ⚠️**

```bash
# SSH to your server (or if already logged in, continue)

# Create backup with correct username 'intelligence'
docker exec intelligence-db pg_dump -U intelligence intelligence_db > /tmp/backup_before_cleanup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup exists and check size
ls -lh /tmp/backup_before_cleanup*.sql

# Copy backup to safe location (optional but recommended)
cp /tmp/backup_before_cleanup*.sql /home/pam-du-uat-ai/backups/
```

---

### **Step 3: Identify Old Migration Records**

**Conservative approach (check before deleting):**

```sql
-- Find likely migration records
SELECT 
    id,
    int_reference,
    source_type,
    created_at,
    created_by,
    email_id,
    whatsapp_id,
    patrol_id
FROM case_profile
WHERE 
    -- Created by migration script
    (created_by IN ('MIGRATION', 'SYSTEM', 'AI_AUTO') OR created_by IS NULL)
    AND 
    -- Created before you started using new system
    created_at < '2025-01-01'  -- Adjust this date!
    AND
    -- Only has one source (not manually grouped)
    (
        (email_id IS NOT NULL AND whatsapp_id IS NULL AND patrol_id IS NULL) OR
        (email_id IS NULL AND whatsapp_id IS NOT NULL AND patrol_id IS NULL) OR
        (email_id IS NULL AND whatsapp_id IS NULL AND patrol_id IS NOT NULL)
    )
ORDER BY id;

-- Count them
SELECT COUNT(*) as old_migration_records
FROM case_profile
WHERE 
    (created_by IN ('MIGRATION', 'SYSTEM', 'AI_AUTO') OR created_by IS NULL)
    AND created_at < '2025-01-01';
```

**Result example:**
```
id  | int_reference | created_at          | created_by
----|---------------|---------------------|------------
1   | INT-001       | 2024-10-15 10:00:00 | MIGRATION
2   | INT-002       | 2024-10-15 10:00:01 | MIGRATION
3   | INT-003       | 2024-10-15 10:00:02 | MIGRATION
... (200 more rows)
203 | INT-203       | 2024-10-15 10:03:23 | MIGRATION

Total: 203 old migration records
```

---

### **Step 4: Archive Old Records (Don't Delete Yet!)**

```sql
-- Create archive table
CREATE TABLE case_profile_migration_archive AS
SELECT * FROM case_profile
WHERE 
    (created_by IN ('MIGRATION', 'SYSTEM', 'AI_AUTO') OR created_by IS NULL)
    AND created_at < '2025-01-01';

-- Verify archive
SELECT COUNT(*) FROM case_profile_migration_archive;

-- Add metadata to archive
ALTER TABLE case_profile_migration_archive 
ADD COLUMN archived_at TIMESTAMP DEFAULT NOW(),
ADD COLUMN archived_reason TEXT DEFAULT 'Old migration data - replaced with manual assignment system';
```

---

### **Step 5: Unlink Emails from Old CaseProfiles**

```sql
-- Before deletion, unlink all emails that point to old case_profiles
-- This prevents breaking foreign key constraints

UPDATE email e
SET 
    caseprofile_id = NULL,
    email_id = NULL
WHERE caseprofile_id IN (
    SELECT id FROM case_profile
    WHERE 
        (created_by IN ('MIGRATION', 'SYSTEM', 'AI_AUTO') OR created_by IS NULL)
        AND created_at < '2025-01-01'
);

-- Check how many emails were unlinked
SELECT COUNT(*) as unlinked_emails
FROM email
WHERE caseprofile_id IS NULL;
```

**⚠️ IMPORTANT:** After this step, those emails will have **NO INT reference** until you manually assign them!

---

### **Step 6: Delete Old Migration Records**

```sql
-- Now safe to delete old records
DELETE FROM case_profile
WHERE 
    (created_by IN ('MIGRATION', 'SYSTEM', 'AI_AUTO') OR created_by IS NULL)
    AND created_at < '2025-01-01';

-- Verify deletion
SELECT COUNT(*) as remaining_records FROM case_profile;

-- Should only see your manually created records
SELECT * FROM case_profile ORDER BY id;
```

---

### **Step 7: Reset ID Sequence (Optional)**

**If you want future IDs to start from a lower number:**

```sql
-- Find current max ID
SELECT MAX(id) FROM case_profile;
-- Let's say it returns: 217

-- Check for manually created records
SELECT id, int_reference, created_at, created_by 
FROM case_profile 
ORDER BY id;
-- Let's say you only have 15 real records (ids: 205-217, 220, 225...)

-- DO NOT reset if you have any active records!
-- But if you deleted everything and want fresh start:

-- Option A: Keep current sequence (RECOMMENDED)
-- Just let it continue from 218, 219, 220...
-- This is safer and maintains audit trail

-- Option B: Reset sequence (RISKY - only if table is empty or you know what you're doing)
SELECT setval('case_profile_id_seq', (SELECT MAX(id) FROM case_profile));
-- This sets next ID to max_id + 1
```

---

### **Step 8: Manually Re-assign INT References**

**Now you need to manually assign INT references to emails that lost their link:**

```sql
-- Find emails without INT reference
SELECT 
    id,
    entry_id,
    subject,
    sender,
    received,
    caseprofile_id
FROM email
WHERE caseprofile_id IS NULL
ORDER BY received DESC;

-- For each email, go to the web interface and assign proper INT number
-- Group emails about the same case together
```

**Web Interface Steps:**
1. Go to https://10.96.135.11/int_source
2. Click on each email
3. Assign INT reference based on case content:
   - Same person + same complaint = Same INT number
   - Different person or different issue = Different INT number
4. System will automatically create CaseProfile or reuse existing one

---

## 📊 **COMPLETE CLEANUP SCRIPT**

**Save this as `cleanup_old_migration_data.sql`:**

```sql
-- ============================================
-- CLEANUP OLD MIGRATION DATA
-- Run this on your PostgreSQL database
-- ============================================

-- Step 0: Verify what will be affected
\echo '=== PREVIEW: Records to be archived ==='
SELECT COUNT(*) as total_to_archive
FROM case_profile
WHERE 
    (created_by IN ('MIGRATION', 'SYSTEM', 'AI_AUTO') OR created_by IS NULL)
    AND created_at < '2025-01-01';  -- ADJUST THIS DATE!

\echo '\n=== PREVIEW: Emails that will lose INT reference ==='
SELECT COUNT(*) as emails_to_unlink
FROM email
WHERE caseprofile_id IN (
    SELECT id FROM case_profile
    WHERE 
        (created_by IN ('MIGRATION', 'SYSTEM', 'AI_AUTO') OR created_by IS NULL)
        AND created_at < '2025-01-01'
);

\echo '\n=== PREVIEW: Current CaseProfile records ==='
SELECT 
    id,
    int_reference,
    source_type,
    created_at,
    created_by
FROM case_profile
ORDER BY id
LIMIT 20;

-- Pause here and review the output!
-- If everything looks correct, continue:

\prompt 'Do you want to continue with cleanup? (yes/no): ' continue_cleanup

-- Step 1: Create archive table
\echo '\n=== Step 1: Creating archive table ==='
DROP TABLE IF EXISTS case_profile_migration_archive CASCADE;

CREATE TABLE case_profile_migration_archive AS
SELECT * FROM case_profile
WHERE 
    (created_by IN ('MIGRATION', 'SYSTEM', 'AI_AUTO') OR created_by IS NULL)
    AND created_at < '2025-01-01';

ALTER TABLE case_profile_migration_archive 
ADD COLUMN archived_at TIMESTAMP DEFAULT NOW(),
ADD COLUMN archived_reason TEXT DEFAULT 'Old migration data - replaced with manual case grouping system';

\echo 'Archive table created with records:'
SELECT COUNT(*) FROM case_profile_migration_archive;

-- Step 2: Unlink emails
\echo '\n=== Step 2: Unlinking emails from old CaseProfiles ==='
UPDATE email e
SET 
    caseprofile_id = NULL,
    email_id = NULL
WHERE caseprofile_id IN (
    SELECT id FROM case_profile
    WHERE 
        (created_by IN ('MIGRATION', 'SYSTEM', 'AI_AUTO') OR created_by IS NULL)
        AND created_at < '2025-01-01'
);

\echo 'Emails unlinked:'
SELECT COUNT(*) as unlinked_emails FROM email WHERE caseprofile_id IS NULL;

-- Step 3: Delete old migration records
\echo '\n=== Step 3: Deleting old migration records ==='
DELETE FROM case_profile
WHERE 
    (created_by IN ('MIGRATION', 'SYSTEM', 'AI_AUTO') OR created_by IS NULL)
    AND created_at < '2025-01-01';

\echo 'Deletion complete. Remaining CaseProfile records:'
SELECT COUNT(*) FROM case_profile;

-- Step 4: Show what remains
\echo '\n=== Step 4: Remaining CaseProfile records ==='
SELECT 
    id,
    int_reference,
    source_type,
    created_at,
    created_by,
    (SELECT COUNT(*) FROM email WHERE caseprofile_id = cp.id) as linked_emails
FROM case_profile cp
ORDER BY id;

\echo '\n=== CLEANUP COMPLETE ==='
\echo 'Next steps:'
\echo '1. Review remaining case_profile records above'
\echo '2. Check case_profile_migration_archive table for archived data'
\echo '3. Manually re-assign INT references to unlinked emails via web interface'
\echo '4. Verify everything works correctly'
```

**Run it:**
```bash
# On your server (already logged in as pam-du-uat-ai@saiuapp11)

# Copy the script to server
nano cleanup_old_migration_data.sql
# Paste the SQL above, save and exit (Ctrl+X, Y, Enter)

# Run it with correct username 'intelligence' (will prompt for confirmation)
docker exec -i intelligence-db psql -U intelligence intelligence_db < cleanup_old_migration_data.sql
```

---

## 🔍 **VERIFICATION QUERIES**

**After cleanup, run these to verify everything is correct:**

```sql
-- 1. Check CaseProfile table
SELECT 
    COUNT(*) as total_case_profiles,
    COUNT(DISTINCT int_reference) as unique_int_refs,
    MIN(created_at) as oldest_date,
    MAX(created_at) as newest_date
FROM case_profile;

-- 2. Check emails without INT reference
SELECT 
    COUNT(*) as emails_without_int,
    (SELECT COUNT(*) FROM email) as total_emails,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM email), 2) as percentage_unlinked
FROM email 
WHERE caseprofile_id IS NULL;

-- 3. Check archive table
SELECT 
    COUNT(*) as archived_records,
    MIN(created_at) as oldest_archived,
    MAX(created_at) as newest_archived
FROM case_profile_migration_archive;

-- 4. Verify no broken foreign keys
SELECT 
    e.id,
    e.caseprofile_id,
    cp.id as cp_exists
FROM email e
LEFT JOIN case_profile cp ON e.caseprofile_id = cp.id
WHERE e.caseprofile_id IS NOT NULL 
  AND cp.id IS NULL;
-- Should return 0 rows!
```

---

## 📋 **SUMMARY OF CHANGES**

### **Before Cleanup:**
```
case_profile table:
- 217 records (200 from migration, 17 manual)
- Mixed old auto-assigned + new manual records
- Confusing to manage

email table:
- All emails linked to auto-assigned CaseProfiles
- One email = One INT number (wrong!)
```

### **After Cleanup:**
```
case_profile table:
- ~17 records (only manually created ones)
- Clean, meaningful INT references
- Each INT = actual investigation case

case_profile_migration_archive table:
- 200 archived old records (safe backup)
- Can restore if needed

email table:
- Unlinked from old CaseProfiles
- Ready for manual INT assignment
- Multiple emails can share INT number (correct!)
```

---

## ⚠️ **IMPORTANT WARNINGS**

1. **ALWAYS BACKUP FIRST** 🔒
   - Full database dump before ANY deletion
   - Test on development server first if possible

2. **ADJUST DATES CAREFULLY** 📅
   - Change `created_at < '2025-01-01'` to your actual migration date
   - Don't accidentally delete manually created records!

3. **CHECK created_by VALUES** 👤
   - Your migration script might use different values
   - Check actual values: `SELECT DISTINCT created_by FROM case_profile;`

4. **MANUAL RE-ASSIGNMENT REQUIRED** ✍️
   - After cleanup, emails have NO INT reference
   - You MUST manually assign INT numbers via web interface
   - Plan time to do this properly

5. **DON'T RUN IN PRODUCTION DURING BUSINESS HOURS** ⏰
   - Run during maintenance window
   - Users will see emails without INT references during re-assignment

---

## 🎯 **RECOMMENDED APPROACH**

**Option A: Clean Slate (If you haven't assigned many manual INTs yet)**
```
1. Backup database
2. Run cleanup script
3. All emails lose INT reference
4. Manually re-assign all INT references properly
5. Going forward, use manual assignment only
```

**Option B: Gradual Migration (If you have important manual assignments)**
```
1. Backup database
2. Identify old migration records (created_at < your_migration_date)
3. Archive old records only
4. Keep manually assigned records
5. Re-assign INT to emails that lost links
6. Going forward, use manual assignment only
```

**Option C: Keep Everything (Safest but messy)**
```
1. Don't delete anything
2. Just start using manual assignment for new cases
3. Old auto-assigned INT numbers stay but unused
4. System works but case_profile table has junk data
5. Accept high ID numbers (217, 218, 219...)
```

---

## 💡 **BEST PRACTICE GOING FORWARD**

**Manual INT Assignment Rules:**
1. **Same Case = Same INT**
   - Email about Agent X rebating → INT-001
   - Follow-up email about Agent X → INT-001 (reuse!)
   - WhatsApp complaint about Agent X → INT-001 (group!)

2. **Different Case = Different INT**
   - Email about Agent Y churning → INT-002
   - Email about Agent Z fraud → INT-003

3. **Document Your System**
   - Keep a log: INT-001 = Agent X rebating case
   - Use case description field in CaseProfile
   - Train team on grouping logic

---

## 📞 **NEED HELP?**

If you're unsure about any step:
1. Run the PREVIEW queries first (Step 0)
2. Check what will be deleted
3. Make sure you have backup
4. Start with archiving, not deletion
5. Test on one email first

**Recovery if something goes wrong:**
```bash
# Restore from backup (replace XXXXXX with your actual backup filename)
docker exec -i intelligence-db psql -U intelligence intelligence_db < /tmp/backup_before_cleanup_XXXXXX.sql
```

Good luck! 🚀
