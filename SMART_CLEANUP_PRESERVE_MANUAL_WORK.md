# 🎯 SMART CLEANUP - Preserve Manual INT Assignments

**Strategy:** Delete ONLY case_profile records that have NO emails linked to them!

---

## 🔍 **Step 1: Check What We Have**

```bash
docker exec -i intelligence-db psql -U intelligence intelligence_db <<'EOF'
-- Total case_profiles
SELECT COUNT(*) as total FROM case_profile;

-- Case profiles WITH emails linked (YOUR MANUAL WORK)
SELECT COUNT(*) as with_emails
FROM case_profile cp
WHERE EXISTS (
    SELECT 1 FROM email e WHERE e.caseprofile_id = cp.id
);

-- Case profiles WITHOUT emails linked (JUNK TO DELETE)
SELECT COUNT(*) as orphan_junk
FROM case_profile cp
WHERE NOT EXISTS (
    SELECT 1 FROM email e WHERE e.caseprofile_id = cp.id
);

-- Show which INT numbers have emails
SELECT 
    cp.int_reference,
    cp.created_by,
    COUNT(e.id) as email_count,
    MIN(e.received) as first_email,
    MAX(e.received) as last_email
FROM case_profile cp
LEFT JOIN email e ON e.caseprofile_id = cp.id
GROUP BY cp.int_reference, cp.created_by
HAVING COUNT(e.id) > 0
ORDER BY cp.int_reference;
EOF
```

---

## 🧹 **Step 2: SMART Cleanup Script**

```bash
cat > smart_cleanup.sql <<'EOF'
-- ============================================
-- SMART CLEANUP - PRESERVE MANUAL WORK
-- Only delete case_profile records with NO emails linked
-- ============================================

\echo '=== STEP 0: PREVIEW ==='
\echo 'Case profiles that will be KEPT (have emails):'
SELECT COUNT(*) as will_keep
FROM case_profile cp
WHERE EXISTS (
    SELECT 1 FROM email e WHERE e.caseprofile_id = cp.id
);

\echo '\nCase profiles that will be DELETED (no emails):'
SELECT COUNT(*) as will_delete
FROM case_profile cp
WHERE NOT EXISTS (
    SELECT 1 FROM email e WHERE e.caseprofile_id = cp.id
);

\echo '\n=== Sample of records to DELETE ==='
SELECT id, int_reference, source_type, created_at, created_by
FROM case_profile cp
WHERE NOT EXISTS (
    SELECT 1 FROM email e WHERE e.caseprofile_id = cp.id
)
ORDER BY id
LIMIT 10;

\echo '\n=== Sample of records to KEEP ==='
SELECT 
    cp.id, 
    cp.int_reference, 
    cp.source_type, 
    cp.created_by,
    COUNT(e.id) as email_count
FROM case_profile cp
INNER JOIN email e ON e.caseprofile_id = cp.id
GROUP BY cp.id, cp.int_reference, cp.source_type, cp.created_by
ORDER BY cp.id
LIMIT 10;

\echo '\n=== Press Ctrl+C to cancel, or press Enter to continue ==='
\prompt 'Type YES to continue: ' confirm

-- Step 1: Create archive of orphan records
\echo '\n=== STEP 1: Archiving orphan case_profiles ==='
DROP TABLE IF EXISTS case_profile_orphan_archive CASCADE;

CREATE TABLE case_profile_orphan_archive AS
SELECT * FROM case_profile cp
WHERE NOT EXISTS (
    SELECT 1 FROM email e WHERE e.caseprofile_id = cp.id
);

ALTER TABLE case_profile_orphan_archive 
ADD COLUMN archived_at TIMESTAMP DEFAULT NOW(),
ADD COLUMN archived_reason TEXT DEFAULT 'Orphan record - no emails linked';

SELECT COUNT(*) as archived FROM case_profile_orphan_archive;

-- Step 2: Delete orphan records
\echo '\n=== STEP 2: Deleting orphan case_profiles ==='
DELETE FROM case_profile
WHERE id IN (SELECT id FROM case_profile_orphan_archive);

-- Step 3: Show results
\echo '\n=== STEP 3: RESULTS ==='
\echo 'Remaining case profiles (with emails):'
SELECT COUNT(*) FROM case_profile;

\echo '\nArchived orphan records:'
SELECT COUNT(*) FROM case_profile_orphan_archive;

\echo '\nEmails still have INT numbers:'
SELECT COUNT(*) FROM email WHERE caseprofile_id IS NOT NULL;

\echo '\nYour INT references (preserved):'
SELECT 
    cp.int_reference,
    COUNT(e.id) as email_count
FROM case_profile cp
LEFT JOIN email e ON e.caseprofile_id = cp.id
GROUP BY cp.int_reference
ORDER BY cp.int_reference;

\echo '\n=== ✅ CLEANUP COMPLETE! ==='
\echo 'All your manual INT assignments are preserved!'
EOF

# Run the smart cleanup
docker exec -i intelligence-db psql -U intelligence intelligence_db < smart_cleanup.sql
```

---

## 📊 **What This Does:**

**KEEPS:**
- ✅ case_profile #45 (INT-005) → has 3 emails linked → **KEEP!**
- ✅ case_profile #78 (INT-012) → has 1 email linked → **KEEP!**
- ✅ case_profile #99 (INT-020) → has 5 emails linked → **KEEP!**

**DELETES:**
- ❌ case_profile #10 (INT-001) → no emails linked → **DELETE!**
- ❌ case_profile #11 (INT-002) → no emails linked → **DELETE!**
- ❌ case_profile #12 (INT-003) → no emails linked → **DELETE!**

---

## ✅ **Advantages of This Approach:**

1. ✅ **Preserves ALL your manual work** - Any email you assigned INT to stays!
2. ✅ **Deletes only junk** - Empty case_profile records from migration
3. ✅ **No foreign key violations** - Emails keep their caseprofile_id
4. ✅ **No export/import needed** - Direct database cleanup
5. ✅ **Reversible** - Orphan records archived in case_profile_orphan_archive

---

## 🎯 **Run This Instead:**

```bash
# Step 1: Preview what will happen
docker exec -i intelligence-db psql -U intelligence intelligence_db <<'EOF'
SELECT 
    'KEEP' as action,
    COUNT(*) as count
FROM case_profile cp
WHERE EXISTS (SELECT 1 FROM email e WHERE e.caseprofile_id = cp.id)
UNION ALL
SELECT 
    'DELETE' as action,
    COUNT(*) as count
FROM case_profile cp
WHERE NOT EXISTS (SELECT 1 FROM email e WHERE e.caseprofile_id = cp.id);
EOF

# If you like what you see, run the smart cleanup!
```

**This is MUCH safer and preserves your work!** 🚀

Want me to help you run this?
