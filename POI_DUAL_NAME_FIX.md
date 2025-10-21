# POI Dual-Name Matching Fix

## Problem Report

**User Issue**: "Peter Chan (陈伟)" and "Peter Chang (张明)" were incorrectly linking to the same POI profile after updating the assessment.

## Root Cause Analysis

### The Bug (Line 232 in `alleged_person_automation.py`)

**OLD LOGIC (BROKEN)**:
```python
elif eng_similarity >= 0.80 or chi_similarity >= 0.80:
    # ❌ BUG: Using OR logic - if EITHER name matches, treat as same person
    overall_similarity = max(eng_similarity, chi_similarity) * 0.9
```

**What Happened**:
1. Existing POI-042: "Peter Chan (陈伟)"
2. User corrects assessment to: "Peter Chan (张明)" (different person!)
3. System calculates:
   - English similarity: "Peter Chan" vs "Peter Chan" = 1.0 ✅
   - Chinese similarity: "张明" vs "陈伟" = 0.0 ❌
4. **BUG**: `eng_similarity >= 0.80` is TRUE → `overall = max(1.0, 0.0) * 0.9 = 0.9` → Links to POI-042 ❌
5. Result: Two different people incorrectly merged into one POI!

## The Fix

### NEW LOGIC (Commit 1a19f49)

```python
if name_english and name_chinese and profile.name_english and profile.name_chinese:
    # When BOTH names are provided, REQUIRE BOTH to match!
    
    if eng_similarity >= 0.80 and chi_similarity >= 0.80:
        # ✅ Both names match well - definitely same person
        overall_similarity = 1.0
    
    elif eng_similarity >= 0.95 and chi_similarity >= 0.50:
        # 🤔 English near-perfect, Chinese partial - could be name variation
        # Example: "Cao Yue (曹越)" vs "Cao Yue Spero (曹越Spero)"
        overall_similarity = 0.90
    
    else:
        # 🚨 CRITICAL: Use MINIMUM score to prevent false matches
        # If one name doesn't match, they're different people!
        overall_similarity = min(eng_similarity, chi_similarity)
```

## Test Results

| Scenario | English Sim | Chinese Sim | Overall | Result |
|----------|-------------|-------------|---------|--------|
| Peter Chan (陈伟) vs Peter Chan (陈伟) | 1.000 | 1.000 | 1.000 | ✅ Same person |
| Peter Chan (张明) vs Peter Chan (陈伟) | 1.000 | 0.000 | **0.000** | ❌ **Different people** |
| Cao Yue (曹越) vs Cao Yue Spero (曹越) | 0.950 | 0.950 | 1.000 | ✅ Same person (name variation) |
| John Smith vs John William Smith | 0.950 | N/A | 0.950 | ✅ Same person (single-name) |

## Impact

### Before Fix
- ❌ Same English name + different Chinese name → Incorrectly merged
- ❌ Users couldn't correct name mistakes without manual intervention
- ❌ POI dashboard showed wrong people linked together

### After Fix
- ✅ Requires BOTH names to match when both provided
- ✅ Users can correct names and POIs stay separate
- ✅ Still allows legitimate variations (Cao Yue vs Cao Yue Spero)
- ✅ Prevents false positives while catching true duplicates

## How to Test in Production

1. **Test Case 1: Different People (Should NOT merge)**
   ```
   Assessment 1: Peter Chan (陈伟)
   Assessment 2: Peter Chan (张明)
   
   Expected: Two separate POI profiles
   ```

2. **Test Case 2: Same Person with Variation (Should merge)**
   ```
   Assessment 1: Cao Yue (曹越)
   Assessment 2: Cao Yue Spero (曹越)
   
   Expected: One POI profile
   ```

3. **Test Case 3: Name Correction (Should create new POI)**
   ```
   Step 1: Save "Peter Chan (陈伟)" → Creates POI-042
   Step 2: Edit to "Peter Chan (张明)" and save
   Expected: 
   - POI-042 has 0 emails (old link deleted)
   - New POI-043 created for "Peter Chan (张明)"
   ```

## Related Fixes in Same Commit

This commit also includes:

1. **Email Linking Fix** (poi_refresh_system.py)
   - Fixed refresh passing `email_id` causing cross-contamination
   - Changed to `email_id=None` to prevent wrong links

2. **Enhanced Auto-Merge**
   - Subset detection: "Cao Yue" ⊆ "Cao Yue Spero" → 0.95 match
   - Chinese suffix handling: "曹越" vs "曹越Spero" → 0.95 match
   - Lowered threshold from 0.85 to 0.80

## Deployment Instructions

```bash
# 1. Pull latest code
cd /path/to/new-intel-platform
git pull origin main

# 2. Verify commit is present
git log --oneline -1
# Should show: 1a19f49 🚨 CRITICAL FIXES: POI dual-name matching...

# 3. Restart application
docker-compose restart

# 4. Test with scenarios above
```

## Database Impact

**No database migration needed** - This is a pure logic fix in the matching algorithm.

Existing POI profiles with incorrect merges will:
- ✅ Stay as-is (no automatic cleanup)
- ✅ Users can fix using "Find Duplicates" → "Un-merge" feature
- ✅ New assessments will correctly create separate POIs

## Monitoring

After deployment, check logs for:
- `[PROFILE MATCHING] ❌ Different people (dual-name mismatch)` - Shows when system correctly rejects false matches
- `[POI RELINK] 🧹 Removing old POI links` - Shows when assessment saves clean up old links

---

**Date**: 2025-01-17  
**Commit**: 1a19f49  
**Files Changed**: `alleged_person_automation.py`, `poi_refresh_system.py`  
**Priority**: 🚨 CRITICAL - Fixes data integrity issue
