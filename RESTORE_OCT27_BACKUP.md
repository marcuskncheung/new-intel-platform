# 🔄 RESTORE DATABASE - Oct 27, 2025 Backup

**Backup File:** `/tmp/backup_before_cleanup_20251027_121324.sql` (869MB)  
**Created:** Oct 27, 2025 at 12:13 PM  
**Contains:** All your manual INT assignments from today!

---

## 🚀 **RESTORE COMMANDS - Copy & Paste:**

```bash
# Step 1: Stop the application
cd /app
docker-compose stop web
```

Wait for "done", then:

```bash
# Step 2: Drop and recreate database
docker exec -i intelligence-db psql -U intelligence postgres <<'EOF'
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'intelligence_db' AND pid <> pg_backend_pid();
DROP DATABASE intelligence_db;
CREATE DATABASE intelligence_db OWNER intelligence;
EOF
```

Should see:
```
DROP DATABASE
CREATE DATABASE
```

Then:

```bash
# Step 3: Restore from TODAY's backup (will take ~2 minutes for 869MB)
docker exec -i intelligence-db psql -U intelligence intelligence_db < /tmp/backup_before_cleanup_20251027_121324.sql
```

You'll see lots of SQL statements scrolling by - this is normal! Wait for it to finish.

Finally:

```bash
# Step 4: Verify restore
docker exec -i intelligence-db psql -U intelligence intelligence_db <<'EOF'
SELECT COUNT(*) as total_case_profiles FROM case_profile;
SELECT COUNT(*) as emails_with_int FROM email WHERE caseprofile_id IS NOT NULL;

-- Show INT numbers with multiple emails (your manual work!)
SELECT 
    cp.int_reference,
    COUNT(e.id) as email_count
FROM case_profile cp
INNER JOIN email e ON e.caseprofile_id = cp.id
GROUP BY cp.int_reference
HAVING COUNT(e.id) > 1
ORDER BY COUNT(e.id) DESC, cp.int_reference
LIMIT 10;
EOF
```

Then:

```bash
# Step 5: Restart application
docker-compose start web
docker-compose ps
```

---

## ✅ **Expected Results:**

After restore, you should see:
- `total_case_profiles`: ~183 (or similar)
- `emails_with_int`: Should show your manual assignments
- **INT numbers with 2+ emails**: Your manual groupings! ✅

---

## 🎯 **After Restore:**

Once verified, we can then:
1. ✅ Identify which INT numbers have multiple emails (manual work)
2. ✅ Keep those
3. ✅ Delete INT numbers with only 1 email (migration junk)
4. ✅ Fix the code bug so future assignments show your username

---

## ⏱️ **Time Required:** 3-5 minutes total

Ready to start? Copy-paste the commands above! 🚀
