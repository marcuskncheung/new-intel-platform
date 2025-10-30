# POI Refresh System Bug Fix

## Issue Description
**Error:** `null value in column "case_profile_id" of relation "poi_intelligence_link" violates not-null constraint`

**Impact:** POI refresh functionality was completely broken - clicking the "Refresh" button on POI profiles caused database constraint violations.

## Root Cause
The `poi_refresh_system.py` was creating `POIIntelligenceLink` entries for all sources (Email, WhatsApp, Online Patrol, Surveillance), but:

1. **Database Schema Requirement:** The `poi_intelligence_link.case_profile_id` column is defined as `NOT NULL`
2. **Data Reality:** Many emails, WhatsApp entries, and patrol entries don't have an assigned `case_profile_id` (it's `None`)
3. **Code Bug:** The refresh system was attempting to create links even when `case_profile_id` was `None`

## Solution Applied

### Email, WhatsApp, and Patrol Sources
**Before:**
```python
# Create universal link
if result.get('poi_id'):
    new_link = POIIntelligenceLink(
        poi_id=result['poi_id'],
        source_type='EMAIL',
        source_id=email.id,
        case_profile_id=email.caseprofile_id,  # ❌ Can be None!
        confidence_score=0.95,
        extraction_method='REFRESH'
    )
```

**After:**
```python
# Create universal link (only if case_profile_id exists)
if result.get('poi_id') and email.caseprofile_id:  # ✅ Check for None
    new_link = POIIntelligenceLink(
        poi_id=result['poi_id'],
        source_type='EMAIL',
        source_id=email.id,
        case_profile_id=email.caseprofile_id,  # Now guaranteed to be not None
        confidence_score=0.95,
        extraction_method='REFRESH'
    )
```

**Changes:**
- Line 78: Added `and email.caseprofile_id` check
- Line 131: Added `and entry.caseprofile_id` check (WhatsApp)
- Line 184: Added `and entry.caseprofile_id` check (Patrol)

### Surveillance Source
**Before:**
```python
new_link = POIIntelligenceLink(
    poi_id=result['poi_id'],
    source_type='SURVEILLANCE',
    source_id=target.surveillance_entry_id,
    case_profile_id=None,  # ❌ Explicitly None!
    confidence_score=0.95,
    extraction_method='REFRESH'
)
```

**After:**
```python
# Note: Surveillance entries don't have case_profile_id, 
# so we skip creating POIIntelligenceLink for surveillance sources
```

**Reason:** The `SurveillanceEntry` and `Target` models don't have a `caseprofile_id` field at all, so we cannot create links for surveillance sources.

## Impact of Fix

### ✅ What Now Works
- POI refresh button no longer crashes
- Links are created ONLY for entries that have been assigned to a case profile
- System gracefully skips entries without case assignments

### ⚠️ Important Note
**POIIntelligenceLink entries will NOT be created for:**
1. Emails not assigned to a case profile
2. WhatsApp entries not assigned to a case profile  
3. Online Patrol entries not assigned to a case profile
4. **All surveillance entries** (don't have case_profile_id field)

This is correct behavior - the intelligence link system requires a case profile to properly track the relationship.

## Files Modified
- `poi_refresh_system.py` - Added validation checks to prevent NULL constraint violations

## Testing Recommendations
1. ✅ Click "Refresh" on POI profile page - should now work without errors
2. ✅ Verify POI profiles are updated from all sources
3. ✅ Check that links are created for entries WITH case assignments
4. ✅ Verify no errors for entries WITHOUT case assignments

## Related Features
This fix enables the new INT Suggestion System to work properly:
- `/int-statistics` - Shows unique allegations dashboard
- `/api/int-suggestions/*` - INT autocomplete and search APIs
- `int_suggestion_widget.html` - Smart INT assignment widget

## Deployment Status
✅ **Ready to push to repository**
- Critical bug fixed
- No blocking errors
- Code quality warnings are non-critical (style/complexity)
