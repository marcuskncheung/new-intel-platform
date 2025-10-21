# POI Refresh Troubleshooting Guide

## Issue Reported

After clicking "Refresh POI" button:
1. ✅ New POI profiles are created
2. ❌ When viewing POI profile, **NO source is shown** (no email, no WhatsApp, nothing)
3. ❌ Some POIs have **mismatched English/Chinese names** (e.g., company name paired with person name)

## Root Causes

### Issue 1: Source Links Not Created
**OLD CODE:**
```python
# Only created link if email had case_profile_id
if result.get('poi_id') and email.caseprofile_id:
    create_link()
```

**PROBLEM:** If email doesn't have a case assigned yet, NO link was created!

**FIX (Commit fca7ff1):**
```python
# Always create link if POI exists
if result.get('poi_id'):
    create_link(case_profile_id=email.caseprofile_id or None)
```

### Issue 2: Duplicate POIs Created
**OLD CODE:**
```python
for email in all_emails:
    create_poi()  # Creates POI but doesn't commit
# db.session.commit()  # Only commits at the end
```

**PROBLEM:** 
- Email 1: "John Chan" → Creates POI-001 (not committed)
- Email 2: "John Chan" → Can't find POI-001 → Creates POI-002 ❌ DUPLICATE!

**FIX (Commit fca7ff1):**
```python
for email in all_emails:
    create_poi()
    db.session.commit()  # Commit after EACH email
```

### Issue 3: Name Pairing Mismatch

**DATABASE STRUCTURE:**
```
alleged_subject_english: "PersonA, PersonB, PersonC"
alleged_subject_chinese: "人物甲, 人物乙, 人物丙"
```

**CURRENT PAIRING (Index-based):**
```python
Index 0: PersonA + 人物甲 ✅
Index 1: PersonB + 人物乙 ✅
Index 2: PersonC + 人物丙 ✅
```

**PROBLEM SCENARIO:**
```
User inputs:
alleged_subject_english: "Bay Insurance Brokers Limited, John Chan"
alleged_subject_chinese: "灣區保險經紀有限公司, 湾区保险经纪有限公司, 陈伟"
                         (Company traditional, Company simplified, Person)

Current pairing (WRONG!):
Index 0: "Bay Insurance..." + "灣區保險..." ✅ Correct
Index 1: "John Chan" + "湾区保险..." ❌ WRONG! (Person paired with company)
Index 2: None + "陈伟" ❌ WRONG! (Chinese name with no English)
```

**FIX (Commit 7ca430c):**
Added warning logs:
```
[POI REFRESH] ⚠️ WARNING: Email 123 has 2 English names but 3 Chinese names!
[POI REFRESH] ⚠️ Names will be paired by position - THIS MAY CREATE INCORRECT POI PROFILES!
[POI REFRESH] ⚠️ Please review Email 123 assessment and ensure names are in matching order!
```

## How to Debug

### Step 1: Deploy Latest Code
```bash
ssh saiuapp11
cd /path/to/new-intel-platform
git pull origin main
docker-compose restart
```

### Step 2: Click "Refresh POI" Button
Watch the console/logs for these messages:

**GOOD LOGS (Working correctly):**
```
[POI REFRESH] 🔍 Checking if link exists for POI-042 → EMAIL-123
[POI REFRESH] ➕ Creating new link: POI-042 ← EMAIL-123
[POI REFRESH] ✅ Source link created: POI-042 ← EMAIL-123
```

**WARNING LOGS (Need attention):**
```
[POI REFRESH] ⚠️ WARNING: Email 123 has 2 English names but 3 Chinese names!
[POI REFRESH] ⚠️ English: ['Bay Insurance Brokers Limited', 'John Chan']
[POI REFRESH] ⚠️ Chinese: ['灣區保險經紀有限公司', '湾区保险经纪有限公司', '陈伟']
[POI REFRESH] ⚠️ Names will be paired by position - THIS MAY CREATE INCORRECT POI PROFILES!
```

**ERROR LOGS (Critical):**
```
[POI REFRESH] ⚠️ WARNING: No POI ID returned from create_or_update!
```

### Step 3: Check POI Dashboard
After refresh:
1. Go to POI list
2. Click on any POI profile
3. Scroll down to "Intelligence Sources" section
4. You should see which emails/WhatsApp/patrol entries mention this person

## Fixing Name Pairing Issues

### Example of GOOD Assessment Input:
```
English Names: "John Chan, Peter Wong, Bay Insurance Brokers Limited"
Chinese Names: "陈伟, 黄伟强, 灣區保險經紀有限公司"

Result:
POI-001: John Chan (陈伟) ✅
POI-002: Peter Wong (黄伟强) ✅
POI-003: Bay Insurance Brokers Limited (灣區保險經紀有限公司) ✅
```

### Example of BAD Assessment Input:
```
English Names: "John Chan, Bay Insurance Brokers Limited"
Chinese Names: "陈伟, 灣區保險, 湾区保险"

Result:
POI-001: John Chan (陈伟) ✅ Correct
POI-002: Bay Insurance... (灣區保險) ❌ Missing company suffix
POI-003: ??? (湾区保险) ❌ No English name
```

### How to Fix:
1. Look for warning logs showing name count mismatches
2. Go to that email's assessment
3. Ensure English and Chinese names are in the **same order**
4. Ensure **same number** of English and Chinese names
5. Click "Save Assessment"
6. Click "Refresh POI" again to regenerate correct POIs

## Technical Details

### POI Link Creation Flow

**Assessment Save (Manual):**
```
1. User edits Email 123 assessment
2. User enters "John Chan (陈伟)"
3. User clicks "Save Assessment"
4. app1_production.py line 8137-8197:
   - Deletes ALL old POI links for Email 123
   - Creates POI-042 for "John Chan (陈伟)"
   - Creates link: POI-042 ← EMAIL-123 (with email_id=123)
   - Creates POIIntelligenceLink: POI-042 ← EMAIL-123
5. When viewing POI-042, Email 123 is shown ✅
```

**Refresh POI (Automated):**
```
1. User clicks "Refresh POI" button
2. poi_refresh_system.py scans all emails
3. For each email with alleged persons:
   - Deletes ALL old POI links
   - Reads current alleged_subject_english and alleged_subject_chinese
   - Splits by comma to get individual names
   - Pairs names by index position
   - Creates/finds POI profile (with email_id=None to avoid wrong linking)
   - Creates POIIntelligenceLink separately
4. Commits after each email (prevents duplicates)
```

### Database Tables

**POIIntelligenceLink (Universal):**
```sql
poi_id: "POI-042"
source_type: "EMAIL"
source_id: 123
case_profile_id: 456 (or NULL)
confidence_score: 0.95
extraction_method: "REFRESH" or "AUTOMATION"
```

This table links POI profiles to their intelligence sources.

## Current Status (2025-10-21 08:04 HKT)

**🔴 ROOT CAUSE FOUND!**

**Error from production logs:**
```
psycopg2.errors.NotNullViolation: null value in column "case_profile_id" 
of relation "poi_intelligence_link" violates not-null constraint

DETAIL: Failing row contains (178, POI-001, null, EMAIL, 2, REFRESH, 0.95, ...).
```

**THE PROBLEM:**
Database schema requires `case_profile_id` to be NOT NULL, but refresh code tries to insert NULL (because not all emails have cases assigned yet).

**THE FIX:**
Run this SQL command to make `case_profile_id` nullable:

```bash
docker exec -i intelligence-db psql -U postgres -d intelligence_system << 'EOF'
ALTER TABLE poi_intelligence_link 
ALTER COLUMN case_profile_id DROP NOT NULL;
EOF
```

**WHY THIS WORKS:**
- ✅ Code already handles NULL case_profile_id (commit fca7ff1)
- ✅ Error handling catches the violation (commit fb8010f)
- ⏳ **Database schema needs to allow NULL** (THIS FIX)

After running the SQL fix, click "Refresh POI" again - it will work!

---

## Commits

| Commit | Date | Description | Status |
|--------|------|-------------|--------|
| `1a19f49` | 2025-01-17 | Fixed dual-name matching logic | ✅ Deployed |
| `fca7ff1` | 2025-01-17 | Fixed source link creation + duplicate POIs | ✅ Deployed |
| `7ca430c` | 2025-01-17 | Added enhanced logging | ✅ Deployed |
| `fb8010f` | 2025-01-17 | Added error handling for link creation | ✅ Deployed |
| **SQL FIX** | **2025-10-21** | **Make case_profile_id nullable** | ⏳ **RUN THIS NOW!** |

## Next Steps

1. ✅ ~~Deploy code (commits above)~~ - DONE
2. ✅ ~~Click "Refresh POI" and watch logs~~ - DONE  
3. ✅ ~~Look for error messages~~ - **FOUND THE BUG!**
4. ⏳ **RUN SQL FIX** (see above)
5. ⏳ Click "Refresh POI" again - should work now!
6. ⏳ Verify POI-082 shows correct sources

---

**Date**: 2025-10-21  
**Priority**: 🔴 **CRITICAL** - Schema fix ready to deploy  
**Status**: 🎯 **ROOT CAUSE IDENTIFIED** - Run SQL fix to resolve
