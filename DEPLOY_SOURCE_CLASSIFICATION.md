# 🚀 Deployment Guide: Source Classification Feature

## Overview
This guide explains how to deploy the new **Source Classification** feature to the production server running in Docker.

## What's New?
The email assessment form now includes a comprehensive source classification system:

### Internal Sources
- 📊 Market Conduct Supervision Team
- 📞 Complaint Team  
- 🔹 Other Internal Department (with text field to specify)

### External Sources
- **Regulators**: SFC, HKMA, MPFA, Other (specify)
- **Law Enforcement**: Hong Kong Police, ICAC, Customs, Other (specify)
- **Insurance Industry**
- **Other External Source** (with text field to specify)

---

## 📋 Pre-Deployment Checklist

- [x] Code committed to GitHub (commit: 1336bf4)
- [x] Migration script created (`migrate_add_source_classification.py`)
- [x] Database model updated (7 new columns in Email table)
- [x] Assessment handler updated to save source classification
- [x] UI updated with cascading dropdowns

---

## 🚀 Deployment Steps

### Step 1: Access Production Server
```bash
ssh user@your-server-ip
cd /var/www/new-intel-platform
```

### Step 2: Pull Latest Code
```bash
sudo git pull origin main
```

**Expected output:**
```
remote: Enumerating objects: 11, done.
remote: Counting objects: 100% (11/11), done.
remote: Compressing objects: 100% (7/7), done.
remote: Total 7 (delta 4), reused 0 (delta 0)
Unpacking objects: 100% (7/7), done.
From https://github.com/marcuskncheung/new-intel-platform
   d1bff65..1336bf4  main       -> origin/main
Updating d1bff65..1336bf4
Fast-forward
 app1_production.py                        |  42 +++-
 migrate_add_source_classification.py      | 126 +++++++++++
 templates/int_source_email_detail.html    | 180 ++++++++++++++-
 3 files changed, 346 insertions(+), 2 deletions(-)
 create mode 100644 migrate_add_source_classification.py
```

### Step 3: Run Database Migration Inside Docker

**Option A: Using Docker Exec (Recommended)**
```bash
# Run migration inside the intelligence-app container
sudo docker exec -it intelligence-app python /app/migrate_add_source_classification.py
```

**Option B: Using Docker Compose**
```bash
# Run migration using docker-compose
sudo docker-compose exec intelligence-app python migrate_add_source_classification.py
```

**Expected output:**
```
================================================================================
📊 EMAIL SOURCE CLASSIFICATION MIGRATION
================================================================================

➕ Adding column: source_category (VARCHAR(20))
✅ Column 'source_category' added successfully
➕ Adding column: internal_source_type (VARCHAR(50))
✅ Column 'internal_source_type' added successfully
➕ Adding column: internal_source_other (VARCHAR(255))
✅ Column 'internal_source_other' added successfully
➕ Adding column: external_source_type (VARCHAR(50))
✅ Column 'external_source_type' added successfully
➕ Adding column: external_regulator (VARCHAR(50))
✅ Column 'external_regulator' added successfully
➕ Adding column: external_law_enforcement (VARCHAR(50))
✅ Column 'external_law_enforcement' added successfully
➕ Adding column: external_source_other (VARCHAR(255))
✅ Column 'external_source_other' added successfully

================================================================================
✅ MIGRATION COMPLETE
   • Columns added: 7
   • Columns skipped (already exist): 0
================================================================================

📋 SOURCE CATEGORY OPTIONS:

INTERNAL:
  1. Market Conduct Supervision Team
  2. Complaint Team
  3. Other Internal Department (specify)

EXTERNAL:
  A. Regulators:
     - SFC (Securities and Futures Commission)
     - HKMA (Hong Kong Monetary Authority)
     - MPFA (Mandatory Provident Fund Schemes Authority)
     - Other Regulator (specify)

  B. Law Enforcement:
     - Hong Kong Police Force
     - ICAC (Independent Commission Against Corruption)
     - Customs and Excise Department
     - Other Law Enforcement (specify)

  C. Insurance Industry
  D. Other External Source (specify)

================================================================================
```

### Step 4: Restart Docker Containers
```bash
# Restart the application to load new code
sudo docker-compose restart intelligence-app

# Verify containers are running
sudo docker-compose ps
```

**Expected output:**
```
Name                     Command               State           Ports
-----------------------------------------------------------------------------
intelligence-app         python app1_production.py        Up      0.0.0.0:8080->8080/tcp
intelligence-nginx       nginx -g daemon off;             Up      0.0.0.0:443->443/tcp, 0.0.0.0:80->80/tcp
postgres-db              docker-entrypoint.sh postgres    Up      5432/tcp
```

### Step 5: Verify Deployment

1. **Check Application Logs:**
   ```bash
   sudo docker-compose logs -f intelligence-app --tail=50
   ```

2. **Verify Database Columns:**
   ```bash
   sudo docker exec -it postgres-db psql -U intelligence -d intelligence_db -c "\d email"
   ```
   
   Look for the new columns:
   - `source_category`
   - `internal_source_type`
   - `internal_source_other`
   - `external_source_type`
   - `external_regulator`
   - `external_law_enforcement`
   - `external_source_other`

3. **Test in Browser:**
   - Go to any email assessment page
   - Look for the new "Source Category" dropdown
   - Select "Internal" - verify internal fields appear
   - Select "External" - verify external fields appear
   - Test cascading dropdowns work correctly

---

## 🔧 Troubleshooting

### Issue: Migration Script Not Found
**Error:** `python: can't open file 'migrate_add_source_classification.py'`

**Solution:**
```bash
# Check if file exists
sudo docker exec -it intelligence-app ls -la /app/migrate_add_source_classification.py

# If not found, code not pulled properly
cd /var/www/new-intel-platform
sudo git pull
sudo docker-compose restart intelligence-app
```

### Issue: Columns Already Exist
**Error:** `column "source_category" of relation "email" already exists`

**Solution:**
This is normal if migration was run before. The script will skip existing columns and continue.

### Issue: Permission Denied
**Error:** `Permission denied: '/app/migrate_add_source_classification.py'`

**Solution:**
```bash
# Make script executable
sudo docker exec -it intelligence-app chmod +x /app/migrate_add_source_classification.py
```

### Issue: Database Connection Error
**Error:** `could not connect to server: Connection refused`

**Solution:**
```bash
# Check if postgres container is running
sudo docker-compose ps postgres-db

# If not running, start it
sudo docker-compose up -d postgres-db

# Wait a few seconds, then retry migration
```

### Issue: Application Not Loading New Code
**Symptom:** Source classification fields not appearing in UI

**Solution:**
```bash
# Force rebuild and restart
sudo docker-compose down
sudo docker-compose up -d --build

# Or clear browser cache and hard refresh (Ctrl+Shift+R)
```

---

## 🧪 Testing Checklist

After deployment, test the following:

- [ ] Email assessment page loads without errors
- [ ] Source Category dropdown appears
- [ ] Selecting "Internal" shows internal source options
- [ ] Selecting "External" shows external source options
- [ ] Regulator dropdown shows SFC, HKMA, MPFA, Other
- [ ] Law Enforcement dropdown shows Police, ICAC, Customs, Other
- [ ] "Other" options show text input fields
- [ ] Saving assessment with source classification works
- [ ] Source classification displays correctly on email details page
- [ ] Existing emails without source classification still work

---

## 📊 Database Schema Changes

### New Columns Added to `email` Table

| Column Name | Type | Nullable | Description |
|-------------|------|----------|-------------|
| `source_category` | VARCHAR(20) | Yes | 'INTERNAL' or 'EXTERNAL' |
| `internal_source_type` | VARCHAR(50) | Yes | Internal department type |
| `internal_source_other` | VARCHAR(255) | Yes | Free text for other internal |
| `external_source_type` | VARCHAR(50) | Yes | External source type |
| `external_regulator` | VARCHAR(50) | Yes | Specific regulator |
| `external_law_enforcement` | VARCHAR(50) | Yes | Specific law enforcement |
| `external_source_other` | VARCHAR(255) | Yes | Free text for other external |

### SQL to Manually Verify
```sql
-- Check if columns exist
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'email' 
AND column_name IN (
    'source_category',
    'internal_source_type',
    'internal_source_other',
    'external_source_type',
    'external_regulator',
    'external_law_enforcement',
    'external_source_other'
);

-- Check if any data has been entered
SELECT 
    COUNT(*) as total_emails,
    COUNT(source_category) as with_source_category,
    COUNT(CASE WHEN source_category = 'INTERNAL' THEN 1 END) as internal_sources,
    COUNT(CASE WHEN source_category = 'EXTERNAL' THEN 1 END) as external_sources
FROM email;
```

---

## 🔄 Rollback Plan (If Needed)

If issues arise and you need to rollback:

```bash
# 1. Revert to previous commit
cd /var/www/new-intel-platform
sudo git revert HEAD
sudo git push

# 2. Restart containers
sudo docker-compose restart intelligence-app

# 3. Optionally remove columns (NOT recommended - data loss!)
sudo docker exec -it postgres-db psql -U intelligence -d intelligence_db -c "
ALTER TABLE email 
DROP COLUMN IF EXISTS source_category,
DROP COLUMN IF EXISTS internal_source_type,
DROP COLUMN IF EXISTS internal_source_other,
DROP COLUMN IF EXISTS external_source_type,
DROP COLUMN IF EXISTS external_regulator,
DROP COLUMN IF EXISTS external_law_enforcement,
DROP COLUMN IF EXISTS external_source_other;
"
```

⚠️ **Warning:** Removing columns will permanently delete all source classification data!

---

## 📝 Post-Deployment Notes

### For Users
- New source classification is **optional** for now
- Existing emails don't need to be updated
- Start using source classification for new assessments
- Boss can filter/report by source category later

### For Administrators
- Monitor database performance after migration
- Watch application logs for any errors
- Consider adding database indexes if filtering by source becomes slow:
  ```sql
  CREATE INDEX idx_email_source_category ON email(source_category);
  CREATE INDEX idx_email_external_source ON email(external_source_type);
  ```

---

## 🎯 Next Steps

After successful deployment:

1. **Train Users:** Show team members the new source classification feature
2. **Update Documentation:** Add source classification to user manual
3. **Create Reports:** Build analytics to show intelligence by source
4. **Extend Feature:** Consider adding source classification to WhatsApp, Online Patrol, etc.

---

## 📞 Support

If you encounter issues:
1. Check application logs: `sudo docker-compose logs intelligence-app`
2. Check database logs: `sudo docker-compose logs postgres-db`
3. Review this deployment guide
4. Contact development team with specific error messages

---

**Deployment Date:** November 5, 2025  
**Version:** 1.0.0  
**Commit:** 1336bf4  
**Feature:** Source Classification for Email Intelligence
