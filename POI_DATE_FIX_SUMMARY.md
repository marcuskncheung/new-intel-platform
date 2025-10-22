# POI Profile Date Fix Summary

## 🐛 Problem Fixed

**Issue**: POI profiles were using the **current date** (when the POI was created) instead of the **intelligence source date** (when the email was received).

**Impact**: 
- POI profiles showed wrong "First Mentioned" dates
- Made it look like person was first mentioned today, not when email arrived
- Historical tracking was inaccurate

## ✅ Solution Implemented

### Changes Made:

**1. Updated `alleged_person_automation.py`:**

**Added `source_date` parameter to functions:**
```python
def create_or_update_alleged_person_profile(
    ...
    source_date: datetime = None  # NEW PARAMETER
)

def process_manual_input(
    ...
    source_date: datetime = None  # NEW PARAMETER
)
```

**Updated POI creation logic:**
```python
# OLD CODE (WRONG):
first_mentioned_date=datetime.now(timezone.utc)  # Always used current date

# NEW CODE (CORRECT):
if source_date:  # Use email received date if provided
    first_mentioned = source_date
elif email_id:
    first_mentioned = datetime.now(timezone.utc)  # Fallback to current
else:
    first_mentioned = None
```

**2. Updated `app1_production.py`:**

**Pass email received date when creating POI:**
```python
result = process_manual_input(
    db, AllegedPersonProfile, EmailAllegedPersonLink,
    email_id=email.id,
    alleged_subject_english=english_name,
    alleged_subject_chinese=chinese_name,
    additional_info=person_additional_info,
    update_mode="overwrite",
    source_date=email.received  # ✅ NOW PASSES EMAIL RECEIVED DATE
)
```

## 📊 Before vs After

### Before Fix:
```
Email Received: 2025-01-15
POI Created: 2025-10-22 (today)
POI First Mentioned Date: 2025-10-22 ❌ WRONG!
```

### After Fix:
```
Email Received: 2025-01-15
POI Created: 2025-10-22 (today)
POI First Mentioned Date: 2025-01-15 ✅ CORRECT!
```

## 🎯 What This Affects

### Email-based POIs:
- ✅ Uses `email.received` date
- Shows when person was ACTUALLY first mentioned in intelligence

### WhatsApp/Patrol/Surveillance POIs:
- Will use their respective source dates when implemented
- Framework now supports passing source_date for all intelligence types

### Manually Created POIs:
- If no source date available, uses current date (as before)
- Ensures no null dates in database

## 🔄 Deployment

After deploying to server:
```bash
cd /path/to/new-intel-platform
git pull
docker-compose restart
```

### Testing:
1. Create new assessment with alleged person
2. Save assessment
3. Check POI profile
4. **Expected**: "First Mentioned" date = Email received date
5. **Previous**: "First Mentioned" date = Today's date

## 📝 Notes

**For Existing POI Profiles:**
- Already created POIs will keep their current dates
- Only NEW POIs created after this fix will have correct dates
- Consider running a migration script if historical accuracy is critical

**For Future Enhancements:**
- Can extend to WhatsApp messages (use message date)
- Can extend to Online Patrol (use patrol date)
- Can extend to Surveillance (use operation date)

**Database Fields Affected:**
- `alleged_person_profile.first_mentioned_date`
- `alleged_person_profile.last_mentioned_date`

## ✅ Status

- ✅ Code updated
- ✅ Committed to git
- ✅ Pushed to GitHub
- ⏳ Awaiting deployment to server
- ⏳ Awaiting user testing

---

*Last Updated: October 22, 2025*
*Status: ✅ Fixed and Ready for Deployment*
