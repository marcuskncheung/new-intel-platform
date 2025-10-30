# POI Duplicate Finder & Merger Feature

## 🎯 What's New

### 1️⃣ **POI Number Display on List Page**
- **Before**: Only showed name "Marcus Cheung (張三)"
- **After**: Shows **POI-070** badge next to name

**Visual:**
```
┌─────────────────────────────────┐
│ Marcus Cheung           POI-070 │  ← Badge shows POI number
│ 張三                            │
│                                 │
│ [View]  [Delete]                │
└─────────────────────────────────┘
```

---

### 2️⃣ **Find & Merge Duplicates Button**
New button added to the POI list page toolbar:

```
[+ New POI Profile] [🔍 Find & Merge Duplicates] [🔄 Refresh All Sources]
```

---

## 🔍 How Duplicate Detection Works

### Smart Matching Algorithm:
1. **English Names** (Fuzzy Matching)
   - "John Smith" ↔ "Smith John" → **90% match** ✅
   - "Marcus Cheung" ↔ "Marcus K Cheung" → **85% match** ✅
   - "John Doe" ↔ "Jane Doe" → **40% match** ❌

2. **Chinese Names** (Exact/Partial Matching)
   - "張偉" ↔ "張偉" → **100% match** ✅
   - "張偉" ↔ "張偉強" → **90% match** ✅
   - "張偉" ↔ "李明" → **0% match** ❌

3. **License Numbers** (Exact Match)
   - Same license number → **100% match** ✅ (highest priority)

4. **Threshold**: ≥ **85% similarity** = potential duplicate

---

## 📋 Usage Workflow

### Step 1: Click "Find & Merge Duplicates"
**Page:** Alleged Subject List
**Action:** Click the yellow warning button

### Step 2: Start Scanning
**System scans all active POI profiles**
- Compares every profile with every other profile
- Groups duplicates together
- Shows similarity percentage

**Example Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Found 3 Potential Duplicate Groups
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Duplicate Group 1                        [90% Match]
┌─────────────────────┬─────────────────────┐
│ POI-010 [KEEP]      │ POI-037 [MERGE]     │
│ CHEUNG KIN          │ CHEUNG KIN NAM      │
│ 張健                │ 張健南              │
│ License: A123456    │ License: A123456    │
│ Emails: 5           │ Emails: 3           │
│ WhatsApp: 2         │ WhatsApp: 1         │
└─────────────────────┴─────────────────────┘
[Merge Into POI-010]  [Skip This Group]

Duplicate Group 2                        [100% Match]
┌─────────────────────┬─────────────────────┐
│ POI-019 [KEEP]      │ POI-058 [MERGE]     │
│ John Smith          │ Smith John          │
│ License: B789012    │ License: B789012    │
│ Emails: 8           │ Emails: 2           │
└─────────────────────┴─────────────────────┘
[Merge Into POI-019]  [Skip This Group]
```

### Step 3: Review & Merge
**For each duplicate group:**
1. **Review** the profiles side-by-side
2. **Check** if they're really the same person
3. **Click "Merge"** to consolidate
4. **Or "Skip"** if they're different people

### Step 4: Merge Execution
**What happens when you click "Merge Into POI-010":**
```
Before:
  POI-010: 5 emails, 2 WhatsApp
  POI-037: 3 emails, 1 WhatsApp
  
After:
  POI-010: 8 emails, 3 WhatsApp  ← All links transferred
  POI-037: [MERGED] status       ← Marked as duplicate
```

**Merge Process:**
1. ✅ Transfer all intelligence links (email, WhatsApp, patrol)
2. ✅ Merge missing information (if master lacks data)
3. ✅ Mark duplicate as "MERGED" status
4. ✅ Update master profile counts
5. ✅ Keep oldest POI as master (smaller number)

---

## 🛡️ Safety Features

### 1. Manual Review Required
- ❌ **NO automatic merging**
- ✅ You must click "Merge" button for each group
- ✅ Confirmation dialog before merging

### 2. Master Selection
- Always keeps the **oldest** POI (lowest number)
- Example: POI-010 (created Jan 1) + POI-037 (created Jan 15)
  - → Keeps POI-010 as master

### 3. Data Preservation
- Original emails remain in the database
- Only POI profile records are merged
- Intelligence links are transferred, not deleted

### 4. Audit Trail
- Duplicate profiles marked with "MERGED" status
- Notes field records: "Merged into POI-010 on 2025-10-20 12:34"
- Can track merge history

---

## 📊 Example Scenarios

### Scenario 1: Different Name Orders
```
Input:
  POI-025: "Marcus Cheung" (張三)
  POI-073: "Cheung Marcus" (張三)
  
Detection: 90% English name match + 100% Chinese match
Action: System flags as duplicate
Result: Merge into POI-025
```

### Scenario 2: Full Name vs Short Name
```
Input:
  POI-015: "CHEUNG KIN" (張健)
  POI-042: "CHEUNG KIN NAM" (張健南)
  
Detection: 85% English match + 90% Chinese match
Action: System flags as duplicate
Result: Merge into POI-015
```

### Scenario 3: Same License Number
```
Input:
  POI-008: "John DOE" / License: A123456
  POI-061: "John Doe Jr." / License: A123456
  
Detection: 100% license match (overrides name)
Action: System flags as duplicate
Result: Merge into POI-008
```

### Scenario 4: NOT Duplicates
```
Input:
  POI-005: "John Smith" (張偉)
  POI-009: "Jane Smith" (李明)
  
Detection: 40% English match + 0% Chinese match
Action: NOT flagged (below 85% threshold)
Result: No action
```

---

## 🚀 Deployment

### Production Server Steps:
```bash
cd /home/pam-du-uat-ai
git pull origin main
sudo docker restart intelligence-app
sudo docker logs -f intelligence-app
```

### Commits Included:
- `bf60aec` - Fixed POI ID type mismatch in link creation
- `106f883` - Added duplicate finder and merger feature

---

## 🎨 UI Features

### Alleged Subject List Page
**New Elements:**
1. POI number badge (blue, top-right of card)
2. "Find & Merge Duplicates" button (yellow warning color)

### Find Duplicates Page
**Features:**
1. Scan button to start detection
2. Duplicate groups with similarity scores
3. Side-by-side profile comparison
4. Color coding (green = keep, gray = merge)
5. Merge confirmation dialogs

---

## 💡 Tips

1. **Run periodically**: After importing batches of emails
2. **Review carefully**: Not all high-similarity matches are duplicates
3. **Skip if unsure**: Better to have duplicates than wrong merges
4. **Check counts**: If a POI has many links, be extra careful
5. **Name variations**: Chinese names with different characters might be different people

---

## ⚙️ Technical Details

### Routes Added:
- `GET/POST /alleged_subject_profiles/find_duplicates`
- `POST /alleged_subject_profiles/merge`

### Templates:
- `templates/find_duplicate_poi.html` (new)
- `templates/alleged_subject_list.html` (updated)

### Database Changes:
- None (uses existing POI profile schema)
- Status field: Added "MERGED" status value
- Notes field: Stores merge audit info

### Functions Used:
- `calculate_name_similarity()` from `alleged_person_automation.py`
- Existing POIIntelligenceLink and EmailAllegedPersonLink models

---

## ✅ Success!

**You now have:**
1. ✅ POI numbers displayed on all profile cards
2. ✅ Duplicate detection with smart name matching
3. ✅ Safe manual merge workflow
4. ✅ Full audit trail of merges

**Ready to use!** 🎉
