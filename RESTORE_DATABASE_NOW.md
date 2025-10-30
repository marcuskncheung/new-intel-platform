# 🆘 EMERGENCY DATABASE RESTORE

**Backup File:** `backup_20251017.sql` (846MB, from Oct 17, 2025)

---

## ⚡ **STEP 1: Stop the Application**

```bash
cd /app
docker-compose stop web
```

**Expected output:**
```
Stopping new-intel-platform-main-web-1 ... done
```

---

## ⚡ **STEP 2: Drop Current Database**

```bash
docker exec -i intelligence-db psql -U intelligence postgres <<'EOF'
-- Terminate all connections to the database
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'intelligence_db' AND pid <> pg_backend_pid();

-- Drop the database
DROP DATABASE intelligence_db;

-- Recreate empty database
CREATE DATABASE intelligence_db OWNER intelligence;
EOF
```

**Expected output:**
```
pg_terminate_backend
----------------------
(0 rows)

DROP DATABASE
CREATE DATABASE
```

---

## ⚡ **STEP 3: Restore from Backup**

```bash
# Restore the backup (this will take 30-60 seconds for 846MB)
docker exec -i intelligence-db psql -U intelligence intelligence_db < backup_20251017.sql
```

**Expected output:** Lots of `CREATE TABLE`, `ALTER TABLE`, `COPY` statements scrolling by

---

## ⚡ **STEP 4: Verify Restore**

```bash
docker exec -i intelligence-db psql -U intelligence intelligence_db <<'EOF'
-- Check case_profile count
SELECT COUNT(*) as total_case_profiles FROM case_profile;

-- Check emails with INT numbers
SELECT COUNT(*) as emails_with_int FROM email WHERE caseprofile_id IS NOT NULL;

-- Show recent case profiles
SELECT id, int_reference, source_type, created_at, created_by
FROM case_profile
ORDER BY id DESC
LIMIT 10;
EOF
```

**Expected output:**
```
total_case_profiles: ~183
emails_with_int: Should show your manual assignments
```

---

## ⚡ **STEP 5: Restart Application**

```bash
cd /app
docker-compose start web

# Wait 5 seconds for app to start
sleep 5

# Check it's running
docker-compose ps
```

**Expected output:**
```
NAME                               STATUS
intelligence-db                    Up
new-intel-platform-main-web-1      Up
```

---

## ✅ **STEP 6: Test Web Interface**

Open browser: https://10.96.135.11/int_source

Check:
- ✅ Emails show INT numbers
- ✅ Can view email details
- ✅ Can update INT references

---

## 🎯 **Summary**

This restores your database to Oct 17, 2025 state with all your manual INT number groupings intact!

**Time required:** ~2-3 minutes total

---

## 🆘 **If Something Goes Wrong**

**Error: "database is being accessed by other users"**
```bash
# Force close all connections
docker-compose stop web
docker exec -i intelligence-db psql -U intelligence postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'intelligence_db';"
# Then retry DROP DATABASE
```

**Error: "permission denied"**
```bash
# Use postgres superuser
docker exec -i intelligence-db psql -U postgres postgres -c "DROP DATABASE intelligence_db;"
docker exec -i intelligence-db psql -U postgres postgres -c "CREATE DATABASE intelligence_db OWNER intelligence;"
```

**Restore hangs/takes too long:**
```bash
# Kill restore process
Ctrl+C
# Check database size
docker exec -i intelligence-db psql -U intelligence intelligence_db -c "\l+"
```

---

## 📊 **After Restore - Next Steps**

Once restored, we can:
1. ✅ Check which INT assignments you had
2. ✅ Identify which are migration junk vs your manual work
3. ✅ Create a BETTER cleanup that preserves your manual assignments
4. ✅ Only delete the auto-assigned migration data

**Don't panic!** Your backup has everything. We'll restore it and do this right! 🚀
