# 🔧 CODE UPDATE GUIDE - Option A (Full Migration)

**Strategy:** Use new table ONLY, keep old columns for safety (don't delete)

---

## 📋 FILES TO UPDATE

### 1. Add Model (REQUIRED FIRST)
**File:** `app1_production.py` or create separate `models.py`  
**Action:** Add `EmailAllegedSubject` model from `email_alleged_subject_model.py`

```python
# Add near other model definitions (around line 100-500)
from email_alleged_subject_model import EmailAllegedSubject, save_email_alleged_subjects, get_email_alleged_subjects
```

---

### 2. Update Assessment Save (app1_production.py)
**Location:** Lines ~8037-8195  
**Route:** `/email/<int:email_id>/assessment` (POST)

**CURRENT CODE (to replace):**
```python
# Update email with processed subjects - Store separately
email.alleged_subject_english = ', '.join(processed_english) if processed_english else None
email.alleged_subject_chinese = ', '.join(processed_chinese) if processed_chinese else None
```

**NEW CODE:**
```python
# Delete old alleged subjects
EmailAllegedSubject.query.filter_by(email_id=email.id).delete()

# Save to new relational table
for i in range(len(processed_english) or len(processed_chinese)):
    english = processed_english[i] if i < len(processed_english) else None
    chinese = processed_chinese[i] if i < len(processed_chinese) else None
    license_num = license_info[i] if i < len(license_info) else None
    license_type = intermediary_info[i] if i < len(intermediary_info) else None
    
    # Skip if both names empty
    if not english and not chinese:
        continue
    
    subject = EmailAllegedSubject(
        email_id=email.id,
        english_name=english,
        chinese_name=chinese,
        is_insurance_intermediary=bool(license_num),
        license_type=license_type,
        license_number=license_num,
        sequence_order=i + 1
    )
    db.session.add(subject)

# Keep old columns for backward compatibility (optional - for safety)
email.alleged_subject_english = ', '.join(processed_english) if processed_english else None
email.alleged_subject_chinese = ', '.join(processed_chinese) if processed_chinese else None
```

---

### 3. Update POI Refresh (poi_refresh_system.py)
**Location:** Lines ~77-107  
**Function:** `refresh_poi_from_all_sources()`

**CURRENT CODE (to replace):**
```python
# Parse alleged subjects
english_text = email.alleged_subject_english or ""
chinese_text = email.alleged_subject_chinese or ""

# Split by comma
english_names = [n.strip() for n in english_text.split(',') if n.strip()]
chinese_names = [n.strip() for n in chinese_text.split(',') if n.strip()]
```

**NEW CODE:**
```python
# Read from new relational table
from email_alleged_subject_model import EmailAllegedSubject

alleged_subjects = EmailAllegedSubject.query.filter_by(
    email_id=email.id
).order_by(EmailAllegedSubject.sequence_order).all()

if not alleged_subjects:
    print(f"[POI REFRESH] ℹ️ Email {email.id} has no alleged subjects")
    continue

# Process each subject (guaranteed correct pairing!)
for subject in alleged_subjects:
    english_name = subject.english_name or ""
    chinese_name = subject.chinese_name or ""
    
    # Skip if both empty
    if not english_name and not chinese_name:
        continue
    
    print(f"[POI REFRESH] Processing: {english_name} | {chinese_name}")
    
    # Create/update POI
    result = create_or_update_alleged_person_profile(
        db=db,
        AllegedPersonProfile=AllegedPersonProfile,
        name_english=english_name,
        name_chinese=chinese_name,
        email_id=None,  # Don't link to avoid cross-contamination
        additional_info={
            'agent_number': subject.license_number,
            'role': subject.license_type
        }
    )
    
    # Create POI link
    if result.get('poi_id'):
        # ... existing link creation code ...
```

---

## 🔍 TESTING CHECKLIST

After making changes:

### Test 1: Save New Assessment
1. Go to an email
2. Add alleged subjects:
   - English: "Test Person"
   - Chinese: "测试人"
3. Save assessment
4. Check database:
```sql
SELECT * FROM email_alleged_subjects WHERE email_id = <email_id>;
```
Expected: 1 row with correct names

### Test 2: Update Existing Assessment
1. Open email with alleged subjects
2. Modify names
3. Save
4. Check database - should see updated names

### Test 3: POI Refresh
1. Click "Refresh POI" button
2. Watch logs:
```
[POI REFRESH] Processing: Test Person | 测试人
[POI REFRESH] ✅ Source link created: POI-XXX ← EMAIL-YYY
```
3. Check POI profile - should show email source

### Test 4: Multiple Persons
1. Add 3 alleged subjects
2. Save
3. Verify sequence_order: 1, 2, 3
4. POI refresh should create 3 POIs

### Test 5: Name Mismatch Prevention
1. Try to add:
   - 2 English names
   - 3 Chinese names
2. System should pair by index (like before)
3. **Future enhancement:** Add UI validation

---

## 🚨 ROLLBACK PLAN

If issues found:

### Quick Rollback (Revert code changes)
```bash
git revert <commit_hash>
git push origin main
docker-compose restart
```

Old columns still have data, so system works immediately!

### Full Rollback (Remove new table)
```sql
DROP TABLE email_alleged_subjects;
```

Then revert code changes.

---

## ✅ DEPLOYMENT STEPS

1. **Commit model:**
```bash
git add email_alleged_subject_model.py
git commit -m "Add EmailAllegedSubject model"
git push origin main
```

2. **Update app1_production.py** (assessment save)

3. **Update poi_refresh_system.py** (POI refresh)

4. **Test locally first** (if possible)

5. **Deploy to production:**
```bash
ssh saiuapp11
cd /path/to/new-intel-platform
git pull origin main
docker-compose restart
```

6. **Monitor logs** for errors

7. **Test manually** (checklist above)

---

## 📊 BENEFITS

### Before:
- ❌ "John, Peter" + "陈,黄,王" = Wrong pairings
- ❌ Hard to query specific person
- ❌ POI refresh creates incorrect profiles

### After:
- ✅ Each person separate row = Guaranteed correct pairing
- ✅ Easy queries: `WHERE english_name = 'John'`
- ✅ POI refresh always accurate
- ✅ Can update single person without affecting others
- ✅ Old columns kept for safety

---

**Next:** Make the code changes step by step!
