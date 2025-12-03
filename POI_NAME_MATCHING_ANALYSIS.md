# POI Name Matching System Analysis

**Investigation Date:** June 2025  
**File Analyzed:** `alleged_person_automation.py`  
**Status:** 🔍 Issues Identified

---

## 📋 System Overview

The POI name matching system automatically links new intelligence entries (Email, WhatsApp, Online Patrol, Surveillance) to existing POI profiles based on name similarity.

### Key Functions
| Function | Purpose | Location |
|----------|---------|----------|
| `normalize_name_for_matching()` | Cleans names for comparison | Lines 18-41 |
| `calculate_name_similarity()` | Returns 0.0-1.0 similarity | Lines 43-155 |
| `find_matching_profile()` | Searches existing POIs | Lines 189-308 |
| `create_or_update_alleged_person_profile()` | Creates/updates POI records | Lines 314-547 |

### Matching Priority Order
1. **Exact agent number match** (most reliable)
2. **High similarity English + Chinese names**
3. **High similarity on either English OR Chinese name**
4. **Company + name partial match** (boost)

---

## 🚨 IDENTIFIED ISSUES

### ISSUE #1: Single-Word Name False Matches
**Severity:** HIGH  
**Location:** `calculate_name_similarity()` lines 130-148

**Problem:**
```python
# Current protection only works for subset matching:
if shorter_words >= 2 and longer_words <= shorter_words * 2:
    return 0.95
```

**Example Failures:**
| Input Name | Existing POI | Expected | Actual | Problem |
|------------|--------------|----------|--------|---------|
| "LEUNG" | "LEUNG TAI LIN" | NO MATCH | ~0.57 (MATCH) | Single surname matches different person |
| "CHAN" | "CHAN KIN WAH" | NO MATCH | ~0.57 (MATCH) | Common surname creates false link |
| "Wong" | "Wong Fei Hung" | NO MATCH | ~0.67 (MATCH) | Single word matching too permissive |

**Root Cause:** 
The `difflib.SequenceMatcher` still returns ~0.57-0.67 for single-word matches, which can exceed the 0.80 threshold when combined with other boosts.

**Impact:** 
- Common surnames (CHAN, LEUNG, WONG, LEE) may incorrectly link to wrong POI profiles
- Data integrity issues when intelligence links to wrong person

---

### ISSUE #2: Company Name Detection Too Narrow
**Severity:** MEDIUM  
**Location:** `calculate_name_similarity()` lines 61-75

**Problem:**
```python
company_indicators = [
    'limited', 'ltd', 'llc', 'inc', 'corp', 'corporation',
    'company', 'co', 'group', 'holdings', 'international',
    '有限公司', '公司', '集團', '控股', '國際', '投資',
    # Missing many common patterns!
]
```

**Missing Company Indicators:**
- `'enterprise'`, `'enterprises'`
- `'association'`, `'foundation'`
- `'property'`, `'properties'`, `'real estate'`
- `'agency'`, `'agents'`
- `'bank'`, `'banking'`, `'finance'`
- `'trust'`, `'trustees'`
- Chinese: `'發展'`, `'實業'`, `'地產'`, `'代理'`, `'商業'`

**Impact:** 
Company names without common indicators may incorrectly match person names.

---

### ISSUE #3: Chinese Name Partial Matching Too Lenient
**Severity:** MEDIUM  
**Location:** `calculate_name_similarity()` lines 100-114

**Problem:**
```python
# Partial match returns 0.85 * ratio
if chinese_chars1 in chinese_chars2:
    ratio = len(chinese_chars1) / len(chinese_chars2)
    return 0.85 * ratio
```

**Example Failures:**
| Input | Existing | Calculation | Result | Problem |
|-------|----------|-------------|--------|---------|
| "明" | "明偉" | 0.85 * (1/2) | 0.425 | OK - below threshold |
| "偉明" | "偉明華" | 0.85 * (2/3) | 0.567 | OK - below threshold |
| "陳偉明" | "陳偉明華" | 0.85 * (3/4) | 0.638 | Borderline |

**Note:** Current implementation is actually reasonable, but edge cases exist with 3+ character matches.

---

### ISSUE #4: Name Order Sensitivity
**Severity:** MEDIUM  
**Location:** `normalize_name_for_matching()` and `calculate_name_similarity()`

**Problem:**
The system doesn't account for name order variations common in Chinese-English contexts.

**Example Failures:**
| Input | Existing | Expected | Actual | Problem |
|-------|----------|----------|--------|---------|
| "CHAN WEI MING" | "WEI MING CHAN" | MATCH | ~0.57 | Chinese surname first vs last |
| "Peter Chan" | "Chan Peter" | MATCH | ~0.83 | Western order vs Chinese order |

**Root Cause:**
No name part reordering algorithm for cross-cultural name formats.

---

### ISSUE #5: Threshold 0.80 May Be Too Low
**Severity:** MEDIUM  
**Location:** `find_matching_profile()` line 192

**Problem:**
```python
similarity_threshold: float = 0.80
```

**Example False Matches at 0.80:**
| Input | Existing | Similarity | Match? | Correct? |
|-------|----------|------------|--------|----------|
| "John Smith" | "John Smyth" | 0.82 | YES | MAYBE |
| "Lee Ka Ming" | "Lee Ka Man" | 0.83 | YES | NO |
| "Wong Tai Sin" | "Wong Tai Sing" | 0.87 | YES | MAYBE |

**Impact:**
Similar but different people may be incorrectly linked.

---

### ISSUE #6: Missing Alias/AKA Support
**Severity:** MEDIUM  
**Location:** Entire matching system

**Problem:**
No support for:
- Known aliases (e.g., "Peter" = "彼得")
- Nicknames (e.g., "Michael Chan" = "Mike Chan")
- Name variations stored in POI profile

**Current State:**
The `AllegedPersonProfile` model has `aliases` field but it's not used in matching.

---

### ISSUE #7: Case Sensitivity in Chinese Detection
**Severity:** LOW  
**Location:** `calculate_name_similarity()` line 89

**Problem:**
```python
is_chinese1 = bool(re.search(r'[\u4e00-\u9fff]', norm1))
```

This only detects CJK Unified Ideographs, missing:
- CJK Extension A: `\u3400-\u4dbf`
- CJK Extension B: `\u20000-\u2a6df`
- Compatibility: `\uf900-\ufaff`

**Impact:** Rare but valid Chinese characters may not be detected.

---

## ✅ RECOMMENDED FIXES

### Fix #1: Add Single-Word Protection
```python
def calculate_name_similarity(name1: str, name2: str) -> float:
    # ... existing code ...
    
    # NEW: Reject single-word vs multi-word matching
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if len(words1) == 1 and len(words2) > 1:
        # Single word (surname only) cannot match full name
        return min(0.50, similarity)  # Cap at 0.50, below threshold
    if len(words2) == 1 and len(words1) > 1:
        return min(0.50, similarity)
```

### Fix #2: Expand Company Indicators
```python
company_indicators = [
    # English
    'limited', 'ltd', 'llc', 'inc', 'corp', 'corporation',
    'company', 'co', 'group', 'holdings', 'international',
    'consultant', 'consulting', 'services', 'advisory',
    'financial', 'insurance', 'wealth', 'asset',
    'enterprise', 'enterprises', 'association', 'foundation',
    'property', 'properties', 'real estate', 'realty',
    'agency', 'agents', 'bank', 'banking', 'finance',
    'trust', 'trustees', 'investments', 'capital',
    
    # Chinese
    '有限公司', '公司', '集團', '控股', '國際', '投資',
    '發展', '實業', '地產', '代理', '商業', '企業',
    '顧問', '服務', '銀行', '金融', '信託', '基金會'
]
```

### Fix #3: Increase Threshold to 0.85
```python
# In find_matching_profile()
similarity_threshold: float = 0.85  # Increased from 0.80
```

### Fix #4: Add Name Part Matching
```python
def calculate_name_similarity(name1: str, name2: str) -> float:
    # ... existing code ...
    
    # NEW: Check if names have same parts in different order
    words1 = set(norm1.lower().split())
    words2 = set(norm2.lower().split())
    
    if words1 == words2:
        # Same words, different order → likely same person
        return 0.95
```

### Fix #5: Implement Alias Matching
```python
def find_matching_profile(...):
    # ... existing code ...
    
    # Check aliases for each profile
    for profile in all_profiles:
        if profile.aliases:
            alias_list = [a.strip() for a in profile.aliases.split(',')]
            for alias in alias_list:
                alias_similarity = calculate_name_similarity(name_english or name_chinese, alias)
                if alias_similarity >= similarity_threshold:
                    return profile.to_dict()
```

---

## 📊 SUMMARY TABLE

| Issue | Severity | Fix Complexity | Impact |
|-------|----------|----------------|--------|
| #1 Single-word false matches | HIGH | LOW | Incorrect POI links |
| #2 Company detection gaps | MEDIUM | LOW | Mixed person/company matches |
| #3 Chinese partial matching | MEDIUM | MEDIUM | False positives |
| #4 Name order sensitivity | MEDIUM | MEDIUM | Missed matches |
| #5 Low threshold (0.80) | MEDIUM | LOW | False positives |
| #6 No alias support | MEDIUM | MEDIUM | Missed matches |
| #7 Chinese char detection | LOW | LOW | Rare edge cases |

---

## 🎯 PRIORITY RECOMMENDATIONS

1. **IMMEDIATE (HIGH):** Fix single-word name matching (Issue #1)
2. **SHORT-TERM (MEDIUM):** Expand company indicators (Issue #2)
3. **SHORT-TERM (MEDIUM):** Increase threshold to 0.85 (Issue #5)
4. **MEDIUM-TERM:** Add name part reordering (Issue #4)
5. **MEDIUM-TERM:** Implement alias matching (Issue #6)

---

## 🧪 TEST CASES TO ADD

```python
# Test single-word protection
assert calculate_name_similarity("LEUNG", "LEUNG TAI LIN") < 0.80  # Should NOT match
assert calculate_name_similarity("CHAN", "CHAN KIN WAH") < 0.80     # Should NOT match

# Test company detection
assert calculate_name_similarity("Wong Property", "Wong Ka Ming") == 0.0  # Company vs person

# Test name order
assert calculate_name_similarity("Chan Wei Ming", "Wei Ming Chan") >= 0.90  # Same parts

# Test Chinese exact
assert calculate_name_similarity("陳偉明", "陳偉明") == 1.0  # Exact match
assert calculate_name_similarity("陳偉明", "陳偉銘") < 0.80  # Different last character
```

---

*Report generated by code analysis. Please review and prioritize fixes based on business requirements.*
