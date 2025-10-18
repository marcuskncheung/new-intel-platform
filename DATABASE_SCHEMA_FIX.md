# Database Schema Mismatch Fix

**Date:** 2025-10-19  
**Issue:** POI Intelligence Link table had severe schema mismatch between model definition and actual database

---

## 🐛 Problem Summary

The `POIIntelligenceLink` model defined 20+ columns but the PostgreSQL database only had 8 columns, causing SQL errors:

```
ERROR: column poi_intelligence_link.extraction_tool does not exist
ERROR: column poi_intelligence_link.source_table does not exist
```

This prevented:
- ❌ Smart redirect to POI profiles after saving
- ❌ Creating universal links between POIs and intelligence sources
- ❌ POI profile updates from intelligence assessments

---

## ✅ Changes Made

### 1. **models_poi_enhanced.py** - POIIntelligenceLink Model

**Removed 15 non-existent columns:**
- `source_table`
- `extraction_method`
- `extraction_tool`
- `extraction_timestamp`
- `extracted_by_user`
- `validation_status`
- `mention_context`
- `role_in_case`
- `mention_count`
- `is_primary_subject`
- `verified_by`
- `verified_at`
- `verification_notes`
- `needs_review`

**Kept only existing columns:**
- `id` (Primary Key)
- `poi_id` (Foreign Key → AllegedPersonProfile)
- `case_profile_id` (Foreign Key → CaseProfile, nullable)
- `source_type` (EMAIL/WHATSAPP/PATROL/SURVEILLANCE)
- `source_id` (ID of the intelligence entry)
- `confidence_score` (0.0-1.0)
- `created_by` (Username)
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

**Updated `to_dict()` method:**
- Removed references to deleted columns
- Now only serializes existing fields

---

### 2. **app1_production.py** - Constructor Calls

**Fixed 5 POIIntelligenceLink() instantiations:**

**Lines:** 5516, 5675, 5771, 6116, 6786

**Before:**
```python
POIIntelligenceLink(
    poi_id=result['profile_id'],
    source_type='WHATSAPP',
    source_id=entry.id,
    case_id=entry.caseprofile_id,  # ❌ Wrong field name
    confidence_score=0.90,
    extraction_method='AUTOMATION',  # ❌ Column doesn't exist
    created_by=f"USER-{current_user.username}"
)
```

**After:**
```python
POIIntelligenceLink(
    poi_id=result['profile_id'],
    source_type='WHATSAPP',
    source_id=entry.id,
    case_profile_id=entry.caseprofile_id,  # ✅ Correct
    confidence_score=0.90,
    created_by=f"USER-{current_user.username}"
)
```

---

### 3. **app1_production.py** - SQL Queries

**Line ~2163:** Removed `extraction_method` from SELECT statement

**Before:**
```sql
SELECT 
    pil.source_id,
    pil.confidence_score,
    pil.created_at as link_created_at,
    pil.extraction_method,  -- ❌ Column doesn't exist
    ...
```

**After:**
```sql
SELECT 
    pil.source_id,
    pil.confidence_score,
    pil.created_at as link_created_at,
    ...
```

---

### 4. **app1_production.py** - Display Dictionaries

**Lines ~2193, 2224, 2247, 2268, 2288:** Removed `extraction_method` from `intel_data` dictionaries

**Before:**
```python
intel_data = {
    'link_id': link.link_id,
    'source_type': link.source_type,
    'confidence': link.confidence_score,
    'extraction_method': link.extraction_method,  # ❌ Doesn't exist
    'case_name': link.case_name,
    ...
}
```

**After:**
```python
intel_data = {
    'link_id': link.link_id,
    'source_type': link.source_type,
    'confidence': link.confidence_score,
    'case_name': link.case_name,
    ...
}
```

---

### 5. **UI Updates - Remove agent_number Display**

**Files modified:**
- `templates/poi_profile_detail.html`
- `templates/int_source.html`

**Removed:**
- Badge showing agent number in header
- Agent Number row in profile details table
- Agent Number in modal popup details

**Now shows only:**
- License Number ✅
- Company
- Role
- Names (English/Chinese)

---

## 🧪 Testing Checklist

### Test 1: Email Assessment Update
1. Go to Email Intelligence → Select an email
2. Click "Review Assessment Details"
3. Change alleged person's license number (e.g., IH1412 → IH1413)
4. Click Save

**Expected:**
- ✅ Redirects to POI profile page (not alleged_subject_list)
- ✅ POI profile shows updated license number
- ✅ No SQL errors in console
- ✅ Console logs: `[ALLEGED PERSON AUTOMATION] ✅ Found existing profile: POI-XXX`

### Test 2: WhatsApp/Patrol/Surveillance
1. Edit assessment details in each intelligence type
2. Save changes

**Expected:**
- ✅ Smart redirect to POI profile if linked
- ✅ No database errors

### Test 3: POI Profile Display
1. Navigate to POI profile page
2. Check displayed fields

**Expected:**
- ✅ License Number visible
- ❌ Agent Number NOT visible
- ✅ Names, Company, Role visible
- ✅ Clean layout without gaps

---

## 📊 Database Schema Reference

### Actual PostgreSQL Schema (poi_intelligence_link table)

```sql
CREATE TABLE poi_intelligence_link (
    id SERIAL PRIMARY KEY,
    poi_id INTEGER NOT NULL REFERENCES alleged_person_profile(id),
    case_profile_id INTEGER REFERENCES case_profile(id),
    source_type VARCHAR(20) NOT NULL,  -- EMAIL/WHATSAPP/PATROL/SURVEILLANCE
    source_id INTEGER NOT NULL,
    confidence_score FLOAT DEFAULT 0.0,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🚀 Deployment

Once tested, commit and deploy:

```bash
cd /Users/kinnamcheung/Downloads/new-intel-platform-main-2

git add models_poi_enhanced.py app1_production.py templates/poi_profile_detail.html templates/int_source.html
git commit -m "Fix POIIntelligenceLink database schema mismatch + remove agent_number from UI

- Removed 15 non-existent columns from POIIntelligenceLink model
- Fixed constructor calls to use case_profile_id instead of case_id
- Removed extraction_method parameter (column doesn't exist)
- Updated SQL queries to exclude non-existent fields
- Removed agent_number from POI profile display (user request)
- Now shows only license_number, company, role in profiles"

git push origin main
```

Wait for GitHub Actions, then deploy:

```bash
sudo docker compose pull
sudo docker compose up -d
```

---

## 📝 Notes

- **Database not migrated:** The model was designed for future expansion but the production database was never updated
- **Data preserved:** No data loss - all existing POI links remain intact
- **Backward compatible:** Old email_alleged_person_link table still works (POI v1.0 fallback)
- **Future enhancement:** If needed, columns can be added via migration later

---

## 🔗 Related Files

- Smart redirect feature: `SMART_REDIRECT_FEATURE.md`
- POI merge logic: `alleged_person_automation.py` lines 275-397
- Database architecture: `DATABASE_ARCHITECTURE.md`
