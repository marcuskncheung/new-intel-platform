# 🚀 Deployment Guide: Unified INT-### Reference System

## Overview
This guide covers deploying the unified INT-### reference system to production.

## Prerequisites
- ✅ Code pushed to GitHub (main branch)
- ✅ SSH access to production server (10.96.135.11)
- ✅ Docker installed on server
- ✅ Database backup completed

## Deployment Steps

### Step 1: Connect to Production Server
```bash
ssh root@10.96.135.11
```

### Step 2: Navigate to Application Directory
```bash
cd /root/intelligence-app
```

### Step 3: Backup Current Database
```bash
# Create backup directory if it doesn't exist
mkdir -p backups

# Backup SQLite database
cp instance/users.db backups/users_backup_$(date +%Y%m%d_%H%M%S).db

# Verify backup
ls -lh backups/
```

### Step 4: Pull Latest Code from GitHub
```bash
# Pull latest changes
git pull origin main

# Verify you got the latest commits
git log --oneline -5
```

Expected commits:
- ✅ UI: Remove checkbox columns from WhatsApp and Online Patrol tables
- ✅ PHASE 1: Unified INT Reference System - Database Schema
- ✅ DOCUMENTATION: Unified INT-### Reference System Architecture
- ✅ FEATURE: Hong Kong timezone (HKT/UTC+8) for all date displays

### Step 5: Stop Running Containers
```bash
docker-compose down
```

### Step 6: Rebuild Docker Image (if needed)
```bash
# Only needed if Dockerfile or requirements changed
docker-compose build
```

### Step 7: Run Database Migration Script
```bash
# Option A: Run migration inside Docker container
docker-compose run --rm intelligence-app python3 migrate_add_int_reference.py

# Option B: Run migration directly (if Python installed on host)
python3 migrate_add_int_reference.py
```

Expected output:
```
============================================================
  INT Reference Number Migration
  Auto-generate INT-001, INT-002... for all emails
============================================================

🔄 Starting INT Reference Number migration...
📊 Database: sqlite:///instance/users.db
✅ Connected to database
📋 Existing email table columns: XX

📝 Adding new columns...
  ✅ Added column: caseprofile_id

🔍 Creating indexes...
  ✅ Created indexes

✅ Migration completed successfully!
```

### Step 8: Restart Application
```bash
docker-compose up -d
```

### Step 9: Verify Deployment
```bash
# Check containers are running
docker-compose ps

# Check application logs
docker-compose logs -f intelligence-app

# Check for errors
docker-compose logs intelligence-app | grep -i error
```

### Step 10: Test in Browser
1. Open browser: `http://10.96.135.11:5000`
2. Login with credentials
3. Navigate to INT Source page
4. Verify:
   - ✅ Email table shows INT-### references
   - ✅ WhatsApp table shows INT-### references (or WT-### fallback)
   - ✅ Online Patrol table shows INT-### references (or OP-### fallback)
   - ✅ No checkboxes in WhatsApp/Patrol tables
   - ✅ All dates display in Hong Kong time

## Troubleshooting

### Issue: Migration fails with "column already exists"
**Solution:** This is normal if migration ran before. Check if columns exist:
```bash
sqlite3 instance/users.db "PRAGMA table_info(email);" | grep caseprofile_id
sqlite3 instance/users.db "PRAGMA table_info(whats_app_entry);" | grep caseprofile_id
sqlite3 instance/users.db "PRAGMA table_info(online_patrol_entry);" | grep caseprofile_id
```

### Issue: Application won't start
**Solution:** Check logs for errors:
```bash
docker-compose logs intelligence-app | tail -50
```

Common issues:
- Missing `pytz` package → Run: `docker-compose run --rm intelligence-app pip install pytz`
- Database locked → Stop all containers: `docker-compose down`
- Port already in use → Check: `netstat -tulpn | grep 5000`

### Issue: INT references not showing
**Solution:** Check if migration ran successfully:
```bash
sqlite3 instance/users.db "SELECT COUNT(*) FROM email WHERE int_reference_number IS NOT NULL;"
```

If count is 0, re-run migration:
```bash
docker-compose run --rm intelligence-app python3 migrate_add_int_reference.py
```

### Issue: WhatsApp/Patrol entries have no INT reference
**Expected behavior:** Initial deployment shows fallback (WT-###, OP-###)
**Why:** Unified INT system needs Phase 2 implementation to auto-generate INT references for WhatsApp/Patrol on creation

**Workaround:** New entries created after Phase 2 deployment will automatically get INT references

## Rollback Procedure (If Needed)

### Emergency Rollback
```bash
# Stop application
docker-compose down

# Restore backup database
cp backups/users_backup_YYYYMMDD_HHMMSS.db instance/users.db

# Revert code
git reset --hard HEAD~3  # Go back 3 commits

# Restart
docker-compose up -d
```

## Post-Deployment Verification Checklist

- [ ] Application accessible via browser
- [ ] Users can login successfully
- [ ] Email table shows INT-### references
- [ ] WhatsApp table displays (with INT or WT fallback)
- [ ] Online Patrol table displays (with INT or OP fallback)
- [ ] No checkboxes in WhatsApp/Patrol tables
- [ ] Dates display in Hong Kong timezone
- [ ] Email detail pages work
- [ ] WhatsApp detail pages work
- [ ] Online Patrol detail pages work
- [ ] Profile pages work correctly
- [ ] No console errors in browser F12 devtools

## Next Steps (Phase 2 - Optional)

Phase 2 will implement auto-generation of unified INT references for WhatsApp and Online Patrol entries:

1. Update `add_whatsapp` route to call `create_unified_intelligence_entry()`
2. Update `add_online_patrol` route to call `create_unified_intelligence_entry()`
3. Update edit handlers to maintain INT references
4. Test cross-source deduplication

**Estimated time for Phase 2:** 2-3 hours

## Support

If you encounter issues:
1. Check application logs: `docker-compose logs -f`
2. Check database: `sqlite3 instance/users.db`
3. Restore from backup if needed
4. Contact system administrator

---

**Deployment Date:** _____________  
**Deployed By:** _____________  
**Verification Completed:** ☐ Yes ☐ No  
**Issues Encountered:** _____________
