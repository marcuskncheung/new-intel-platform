# Fix: POI Profile Name Not Updating from Assessment Edits

## Problem
When editing alleged person names in assessment forms (e.g., changing "Mandy" to "Peter"), the POI profile names were not being updated. This affected:
- ❌ Email assessments
- ❌ WhatsApp assessments  
- ❌ Online Patrol assessments

## Root Cause
The automation functions used `update_mode="merge"` by default, which only adds missing fields but doesn't overwrite existing ones.

**Old Logic (merge mode):**
```python
if name_english and not profile.name_english:  # Only if empty
    profile.name_english = name_english.strip()
```

This means if the profile already had a name, it would NOT be updated even if the user changed it in the form.

## Solution
1. **Added `update_mode` parameter** to `process_manual_input()` function
2. **Set default to `"overwrite"`** for manual edits (user intent is to update)
3. **Implemented overwrite logic** that updates names even if they exist
4. **Applied to all assessment routes**: Email, WhatsApp, and Online Patrol
5. **Fixed POIIntelligenceLink bug**: Removed `created_by` field (doesn't exist in database)

**New Logic (overwrite mode):**
```python
if update_mode == "overwrite":
    if name_english and name_english.strip() != profile.name_english:
        old_name = profile.name_english
        profile.name_english = name_english.strip()
        updated_fields.append('name_english')
        print(f"Updated English name: '{old_name}' → '{name_english}'")
```

## Files Changed

### 1. **alleged_person_automation.py** (lines 526-340)
   - Added `update_mode` parameter to `process_manual_input()` with default `"overwrite"`
   - Implemented separate logic for overwrite vs merge modes
   - Overwrite mode: Updates names even if they exist (for manual corrections)
   - Merge mode: Only fills in missing fields (for AI automation)

### 2. **app1_production.py**
   
   **Email Assessment Route** (line ~7461):
   ```python
   result = process_manual_input(
       db, AllegedPersonProfile, EmailAllegedPersonLink,
       email_id=email.id,
       alleged_subject_english=english_name,
       alleged_subject_chinese=chinese_name,
       additional_info=person_additional_info,
       update_mode="overwrite"  # ✅ Allow updating existing POI names
   )
   ```
   
   **WhatsApp Assessment Route** (line ~7103):
   ```python
   result = create_or_update_alleged_person_profile(
       db, AllegedPersonProfile, EmailAllegedPersonLink,
       name_english=english_name if english_name else None,
       name_chinese=chinese_name if chinese_name else None,
       email_id=None,
       source="WHATSAPP",
       update_mode="overwrite",  # ✅ Allow updating existing POI names
       additional_info=person_info
   )
   ```
   
   **Online Patrol Assessment Route** (line ~7269):
   ```python
   result = create_or_update_alleged_person_profile(
       db, AllegedPersonProfile, EmailAllegedPersonLink,
       name_english=english_name if english_name else None,
       name_chinese=chinese_name if chinese_name else None,
       email_id=None,
       source="PATROL",
       update_mode="overwrite",  # ✅ Allow updating existing POI names
       additional_info=person_info
   )
   ```
   
   **POIIntelligenceLink Fixes** (WhatsApp & Patrol routes):
   ```python
   # OLD (caused errors):
   universal_link = POIIntelligenceLink(
       poi_id=result['profile_id'],
       source_type='WHATSAPP',
       source_id=entry.id,
       case_profile_id=entry.caseprofile_id,
       confidence_score=0.90,
       created_by=f"USER-{current_user.username}"  # ❌ Column doesn't exist
   )
   
   # NEW (fixed):
   universal_link = POIIntelligenceLink(
       poi_id=result['profile_id'],
       source_type='WHATSAPP',
       source_id=entry.id,
       case_profile_id=entry.caseprofile_id,
       confidence_score=0.90,
       extraction_method='MANUAL'  # ✅ Correct column
   )
   ```

### 3. **models_poi_enhanced.py** (line ~193)
   - Removed `created_by` column from POIIntelligenceLink model
   - Removed `updated_at` column from POIIntelligenceLink model
   - Added `extraction_method` column to match database schema

## Testing Steps

### Test Email Assessment:
1. Create a POI profile (e.g., "Mandy Chan 陳美芬")
2. Go to email assessment that references this profile
3. Change name from "Mandy Chan" to "Peter Wong"
4. Change Chinese from "陳美芬" to "王彼得"
5. Save assessment
6. Go to POI profile - should show "Peter Wong 王彼得" ✅

### Test WhatsApp Assessment:
1. Open WhatsApp entry linked to a POI
2. Edit alleged subject name in assessment form
3. Save
4. Verify POI profile updated ✅

### Test Online Patrol Assessment:
1. Open patrol entry linked to a POI
2. Edit alleged subject name in assessment form
3. Save
4. Verify POI profile updated ✅

## Update Modes Explained
- **`merge`** (AI automation): Only fill in missing fields, don't overwrite
  - Use case: AI extracts data automatically, shouldn't override manual corrections
- **`overwrite`** (manual edit): Update fields even if they exist
  - Use case: User manually corrects a name, want the change to apply
- **`skip_if_exists`**: Don't update anything, just link to existing profile
  - Use case: Simple linking without modifications

## Impact
- ✅ Email assessments can now update POI names
- ✅ WhatsApp assessments can now update POI names
- ✅ Online Patrol assessments can now update POI names
- ✅ Manual name corrections work as expected across all intelligence types
- ✅ AI automation still uses merge mode (safe, non-destructive)
- ✅ POIIntelligenceLink creation no longer crashes
- ✅ Backward compatible with existing code

## Database Schema Alignment
Fixed POIIntelligenceLink model to match actual database:
- ❌ Removed: `created_by`, `updated_at`
- ✅ Added: `extraction_method`
- ✅ Kept: `id`, `poi_id`, `case_profile_id`, `source_type`, `source_id`, `confidence_score`, `created_at`
