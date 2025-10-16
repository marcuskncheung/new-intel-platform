# 🗄️ POI v2.0 Migration Options

**Status**: POI v1.0 currently deployed, v2.0 migration ready  
**Date**: 2025-10-17

---

## ⚠️ IMPORTANT: Do NOT Run Migrations Yet

Your current system runs **POI v1.0** which works perfectly.  
Migrations are for **future POI v2.0 upgrade** only.

---

## 📋 Current Deployment (Use This)

### ✅ For POI v1.0 (Current System):

```bash
# On Linux server - this is all you need
docker compose exec web python3 -c "from app1_production import app, db; with app.app_context(): db.create_all()"
```

**This automatically creates all tables from your current Python models.**

---

## 🔄 Future Migration Options (POI v2.0)

When you implement POI v2.0 code, choose ONE migration method:

### Option 1: Python Migration (Recommended ⭐)

**File**: `migrate_poi_v2_python.py`

**Advantages**:
- ✅ Pre-flight safety checks
- ✅ Interactive confirmation
- ✅ Automatic rollback on errors  
- ✅ Validates code readiness
- ✅ Detailed logging
- ✅ Idempotent (safe to re-run)

**Usage**:
```bash
# After deploying POI v2.0 code
docker compose exec web python3 migrate_poi_v2_python.py
```

---

### Option 2: SQL Migration (Traditional)

**File**: `migrations/01_poi_architecture_upgrade.sql`

**Advantages**:
- ✅ Complete and tested
- ✅ 790 lines fully automated
- ✅ Standard SQL approach

**Usage**:
```bash
# After deploying POI v2.0 code
docker compose exec db psql -U postgres -d intelligence_db < migrations/01_poi_architecture_upgrade.sql
```

---

## 📊 What Gets Created (POI v2.0)

### New Tables:

1. **poi_intelligence_link**
   - Universal POI linking (Email/WhatsApp/Patrol/Surveillance)
   - Confidence scoring
   - Validation workflow

2. **poi_extraction_queue**  
   - Automated extraction jobs
   - Priority queue
   - Retry logic

3. **poi_assessment_history**
   - Risk assessment changes
   - Audit trail
   - Historical tracking

### Enhanced Fields (alleged_person_profile):

Adds 35+ new columns:
- Identity: `name_normalized`, `aliases`, `phone_numbers`, `email_addresses`
- Assessment: `risk_level`, `risk_score`, `threat_classification`
- Statistics: `whatsapp_count`, `patrol_count`, `surveillance_count`
- Relationships: `associated_pois`, `organization_links`
- And more...

---

## 🔧 Migration Prerequisites

Before running ANY migration:

1. ✅ **Update Python Code**
   - Add POI v2.0 models to `app1_production.py`
   - Add `POIIntelligenceLink`, `POIExtractionQueue`, `POIAssessmentHistory` classes
   - Update `AllegedPersonProfile` with new fields

2. ✅ **Create Backup**
   ```bash
   docker compose exec db pg_dump -U postgres intelligence_db > backup_$(date +%Y%m%d).sql
   ```

3. ✅ **Test Code**
   - Verify POI v2.0 code works in development
   - Test new features
   - Ensure no errors

4. ✅ **Plan Downtime**
   - Notify users
   - Schedule maintenance window
   - Prepare rollback plan

---

## 🔄 Rollback Options

### Python Rollback:

```bash
# Use rollback script (if you created one)
docker compose exec web python3 rollback_poi_v2.py
```

### SQL Rollback:

```bash
# Use SQL rollback file
docker compose exec db psql -U postgres -d intelligence_db < migrations/01_poi_architecture_rollback.sql
```

### Backup Restore:

```bash
# Restore from backup (safest)
docker compose down
docker compose up -d db
sleep 10
docker compose exec -T db psql -U postgres -d intelligence_db < backup_YYYYMMDD.sql
docker compose up -d
```

---

## 🎯 Decision Guide

### Use Python Migration If:
- ✅ You want interactive safety checks
- ✅ You prefer detailed logging
- ✅ You want automatic error handling
- ✅ You're less experienced with raw SQL

### Use SQL Migration If:
- ✅ You're comfortable with PostgreSQL
- ✅ You want traditional approach
- ✅ You need complete control
- ✅ You prefer battle-tested SQL

### Use Neither If:
- ❌ POI v2.0 code is NOT deployed yet
- ❌ You haven't updated Python models
- ❌ You don't have a backup
- ❌ Current POI v1.0 system meets your needs

---

## 📋 Migration Comparison

| Feature | Python Script | SQL File | db.create_all() |
|---------|--------------|----------|-----------------|
| **Safety Checks** | ✅ Yes | ❌ No | ⚠️ Basic |
| **User Prompts** | ✅ Yes | ❌ No | ❌ No |
| **Auto Rollback** | ✅ Yes | ❌ No | ❌ No |
| **Code Validation** | ✅ Yes | ❌ No | ✅ Yes |
| **Data Migration** | ✅ Automated | ✅ Automated | ❌ No |
| **Idempotent** | ✅ Yes | ⚠️ Partial | ✅ Yes |
| **Use Case** | POI v2.0 Upgrade | POI v2.0 Upgrade | Initial Setup |

---

## ✅ Current Recommendation

### For Now (POI v1.0):
```bash
# ✅ Use this - simple and works
docker compose exec web python3 -c "from app1_production import app, db; with app.app_context(): db.create_all()"
```

### For Later (POI v2.0):
```bash
# ✅ After code update, use Python migration
docker compose exec web python3 migrate_poi_v2_python.py

# Or SQL migration
docker compose exec db psql -U postgres -d intelligence_db < migrations/01_poi_architecture_upgrade.sql
```

---

## 📞 Support

If unsure which option to choose:
1. Stick with POI v1.0 (current system works great)
2. Plan POI v2.0 implementation carefully
3. Use Python migration for safety
4. Keep backup handy for rollback

---

**Summary**: Your current system doesn't need migration. When you implement POI v2.0, use Python migration for safety or SQL for traditional approach.
