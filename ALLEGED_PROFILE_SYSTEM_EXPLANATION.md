# Alleged Subject Profile System - Complete Explanation

## 📋 Current System Status

### ✅ What Already EXISTS and WORKS:

1. **Automated Profile Creation from AI Analysis**
   - When AI analyzes an email (INT-003, INT-010, etc.), it extracts alleged person names
   - System automatically creates or updates profiles in `alleged_person_profile` table
   - Smart name matching prevents duplicates (Chan Tai Man = Tai Man Chan)
   - Profiles get unique POI IDs (POI-001, POI-002, etc.)

2. **Smart Duplicate Prevention**
   - Uses fuzzy matching for English names (handles: John Smith = JOHN SMITH = john smith)
   - Uses strict matching for Chinese names (陳大文 = 陳大文 exactly)
   - Similarity threshold of 85% to catch variations (Chan Tai Man ≈ Tai Man Chan)
   - Combines multiple signals: name + license number + company

3. **Profile Linking**
   - Each profile is linked to all emails that mention that person
   - Relationship stored in `email_alleged_person_link` table
   - One profile → many emails (INT-003, INT-010, INT-045 all reference same person)

### ⚠️ What's MISSING (Needs to be Built):

1. **Backfill Existing Data**
   - Your existing emails (INT-003, INT-010, etc.) were created BEFORE the automation
   - They have `alleged_subject_english` and `alleged_subject_chinese` fields populated
   - But profiles were NEVER created because automation runs during AI analysis
   - **Solution**: Run migration script to create profiles for all existing data

2. **Manual Assessment Profile Creation**
   - Currently profiles are auto-created during AI analysis
   - When users manually assess emails and enter alleged person names, profiles should also be created
   - **Solution**: Hook into the email assessment save function

3. **Profile View Enhancement**
   - Profile detail page needs to show full allegation text (currently truncated)
   - **Solution**: Add "View Full Details" modal/expandable section

---

## 🔄 How It SHOULD Work (Complete Flow):

### Scenario 1: AI Analysis
```
User clicks "AI Analysis" on INT-003
↓
AI finds: "Chan Tai Man (陳大文), License #123456"
↓
System saves to email table:
  - alleged_subject_english = "Chan Tai Man"
  - alleged_subject_chinese = "陳大文"
  - license_numbers_json = ["123456"]
↓
🤖 AUTO-CREATION:
  - Search for existing profile matching "Chan Tai Man" or "陳大文"
  - If NOT found: Create POI-001 with name + license
  - If FOUND: Link INT-003 to existing POI-001
  - Create link: email_alleged_person_link (INT-003 → POI-001)
```

### Scenario 2: Manual Assessment
```
User opens INT-010 email detail page
↓
User enters in form:
  - Alleged Subject: "Tai Man Chan (陳大文)"
  - License: "123456"
  - Summary: "Rebate allegation from client"
↓
User clicks "Save Assessment"
↓
🤖 AUTO-CREATION (Should happen but doesn't yet):
  - Parse names: "Tai Man Chan" and "陳大文"
  - Smart match finds POI-001 (Chan Tai Man = Tai Man Chan, 95% similar)
  - Link INT-010 to POI-001
  - Update POI-001: Add INT-010 to allegations count
```

### Scenario 3: Viewing Profile
```
User opens "Alleged Subject Profiles" page
↓
Sees: POI-001 - Chan Tai Man (陳大文)
  - Total Allegations: 2 (INT-003, INT-010)
  - Risk Score: 85/100
  - License: 123456
  - Status: Under Investigation
↓
User clicks on POI-001
↓
Profile Detail Page shows:
  ✅ All linked emails (INT-003, INT-010)
  ✅ Timeline of allegations
  ✅ Source breakdown (Email, WhatsApp, etc.)
  ✅ Full allegation text (with "View More" button if truncated)
```

---

## 🎯 Smart Duplicate Prevention Examples

### Name Variations (All matched as SAME person):
```
English Names:
✓ Chan Tai Man
✓ Tai Man Chan
✓ CHAN TAI MAN
✓ Chan Tai-Man
✓ Mr. Chan Tai Man
✓ Chan T.M.

Chinese Names (Strict):
✓ 陳大文
✗ 陈大文 (Simplified vs Traditional - requires special handling)
✗ 陳文大 (Different character order - NOT same person)

License Numbers (Exact Match):
✓ E-123456
✓ E-123456 (case-insensitive)
✗ E-123457 (Different number)
```

### Matching Logic Priority:
```
1. EXACT LICENSE MATCH (100% confidence)
   If license numbers match → Same person (even if names different)
   
2. BOTH NAMES MATCH (95% confidence)
   English: Chan Tai Man = Tai Man Chan (similarity 0.90)
   Chinese: 陳大文 = 陳大文 (exact match 1.00)
   → Same person
   
3. ONE NAME MATCHES (85% confidence)
   English: Chan Tai Man = CHAN TAI MAN (similarity 1.00)
   Chinese: None provided
   → Likely same person
   
4. COMPANY + NAME (75% confidence)
   English: Chan Tai Man = Chan T.M. (similarity 0.85)
   Company: ABC Realty = ABC Realty (exact match)
   → Probably same person
```

---

## 🔧 What Needs to Be Fixed

### 1. Backfill Existing Emails
**Problem**: Emails created before automation have no profiles
**Solution**: Run migration script

```python
# Script will:
1. Query all emails with alleged_subject_english or alleged_subject_chinese
2. For each email:
   - Parse names (handle comma-separated lists)
   - Check for existing profile using smart matching
   - Create new profile if not found
   - Link email to profile
3. Handle multiple persons per email (INT-003 mentions 3 people)
```

### 2. Add Profile Creation on Manual Assessment
**Problem**: Manual email assessment doesn't create profiles
**Solution**: Hook into the save assessment route

```python
# In int_source_email_detail POST handler:
if alleged_subject_english or alleged_subject_chinese:
    process_manual_input(
        db, AllegedPersonProfile, EmailAllegedPersonLink,
        email_id=email.id,
        alleged_subject_english=alleged_subject_english,
        alleged_subject_chinese=alleged_subject_chinese,
        additional_info={
            'agent_number': license_number,
            'company': company
        }
    )
```

### 3. Add "View Full Details" in Profile Page
**Problem**: Allegation descriptions truncated, can't see full text
**Solution**: Add modal popup

```html
<!-- In profile_detail.html -->
<td>
  {{ allegation.allegation_description[:100] }}
  {% if allegation.allegation_description|length > 100 %}
    <button class="btn btn-sm btn-link" 
            onclick="showFullDetails('{{ allegation.id }}')">
      View Full...
    </button>
  {% endif %}
</td>

<!-- Modal for full text -->
<div class="modal" id="fullDetailsModal">
  <div class="modal-body">
    <div id="fullDetailsContent"></div>
  </div>
</div>
```

---

## 📊 Database Schema

### Tables Involved:
```sql
-- Main profile table
CREATE TABLE alleged_person_profile (
    id INTEGER PRIMARY KEY,
    poi_id VARCHAR(20) UNIQUE,  -- POI-001, POI-002
    name_english VARCHAR(255),
    name_chinese VARCHAR(255),
    agent_number VARCHAR(50),
    company VARCHAR(255),
    risk_score FLOAT,
    total_allegations INTEGER,
    status VARCHAR(20),  -- ACTIVE, ARCHIVED
    created_at TIMESTAMP,
    created_by VARCHAR(100)
);

-- Email table (already has these fields)
CREATE TABLE email (
    id INTEGER PRIMARY KEY,
    int_reference_number VARCHAR(20),  -- INT-003
    alleged_subject_english VARCHAR(500),
    alleged_subject_chinese VARCHAR(500),
    license_numbers_json TEXT,
    -- ... other fields
);

-- Link table (connects emails to profiles)
CREATE TABLE email_alleged_person_link (
    id INTEGER PRIMARY KEY,
    email_id INTEGER REFERENCES email(id),
    alleged_person_id INTEGER REFERENCES alleged_person_profile(id),
    link_type VARCHAR(20),  -- PRIMARY, MENTIONED
    created_at TIMESTAMP
);
```

---

## 🚀 Implementation Steps

### Step 1: Deploy Migration Script (Priority 1)
```bash
# Create and run backfill script
python backfill_alleged_profiles.py

# This will:
# - Process all existing emails
# - Create profiles for historical data
# - Link emails to profiles
# - Print summary report
```

### Step 2: Add Manual Assessment Hook (Priority 2)
```python
# Modify app1_production.py int_source_email_detail()
# Add call to process_manual_input() when assessment saved
```

### Step 3: Enhance Profile View (Priority 3)
```html
# Update profile_detail.html
# Add modal for full allegation text
# Add click handler for "View Full" buttons
```

### Step 4: Test on Server
```bash
# Test scenarios:
1. Run AI analysis on new email → Profile created ✓
2. Manually assess email → Profile created ✓
3. Similar names detected → Linked to same profile ✓
4. View profile → Shows all linked emails ✓
5. Click "View Full" → Modal shows complete text ✓
```

---

## 💡 Advanced Features (Future Enhancements)

### 1. Merge Profiles
Allow admins to manually merge duplicate profiles if automation misses
```python
merge_profiles(poi_id_keep="POI-001", poi_id_merge="POI-015")
# Transfer all links from POI-015 to POI-001
# Archive POI-015
```

### 2. Profile Splitting
If one profile actually represents two different people
```python
split_profile(poi_id="POI-001", 
              email_ids_to_split=[45, 67, 89])
# Create new POI-020 
# Move specified emails to POI-020
```

### 3. AI-Powered Similarity Tuning
```python
# Current threshold: 85%
# Allow admins to adjust per use case:
similarity_threshold = {
    'english_name': 0.85,  # More flexible
    'chinese_name': 0.95,  # Strict
    'license': 1.00,       # Exact only
}
```

---

## ✅ Summary

**Good News**: The automation system is 90% complete!
- ✅ AI analysis already creates profiles
- ✅ Smart duplicate prevention works
- ✅ Profile linking implemented

**What's Needed**:
1. 🔧 Backfill script for existing data (1-2 hours)
2. 🔧 Hook manual assessment to profile creation (30 minutes)
3. 🎨 UI enhancement for full text view (1 hour)

**Total Time**: ~3-4 hours to complete system

**Result**: Fully automated alleged person profile management with intelligent duplicate prevention and comprehensive tracking across all intelligence sources.
