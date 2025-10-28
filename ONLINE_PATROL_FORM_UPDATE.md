# 📋 Online Patrol Entry Form - Complete Update

## ✅ What Was Updated

### 1. **Form Template** (`int_source_online_patrol_edit.html`)

#### New Professional Structure:
- **Discovery Information Section**
  - Platform/Source (dropdown: Instagram, WeChat, Facebook, Twitter/X, Forum, Website, Other)
  - Post Time (when post was created/published)
  - Discovery Time (when we logged it)
  - Discovered By (team member name)
  - Post Details/Description

#### Photo Upload Section:
- Multiple file upload (JPEG, PNG, PDF)
- Real-time photo preview
- Remove photo functionality
- Stores as binary data (BYTEA) in PostgreSQL

#### Alleged Person Section:
- Dynamic multi-input fields
- Add/remove person functionality
- Comma-separated storage for POI automation

#### Alleged Nature Section:
- Multi-select allegation categories (aligned with Email complaint standards)
- Searchable dropdown with categories:
  - AMLO Breaches
  - MPF Violations
  - CPD Non-Compliance
  - Miscellaneous Cases
- JSON array storage for multiple allegations

#### Assessment Section:
- Source Reliability (1-5 scale)
- Content Validity (1-5 scale)
- Reviewer Name (required)
- Reviewer Comment (required)

### 2. **Backend Route** (`add_online_patrol` in `app1_production.py`)

#### New Field Handling:
```python
# Professional fields
discovered_by = request.form.get("discovered_by")
discovery_time = request.form.get("discovery_time")
source_time = request.form.get("source_time")

# Alleged nature (JSON array)
alleged_nature = request.form.get("alleged_nature", "[]")

# Alleged persons (multiple)
alleged_person = request.form.getlist("alleged_person[]")

# Photo uploads
photos = request.files.getlist('photos[]')
```

#### Photo Processing:
- Reads photo binary data
- Creates `OnlinePatrolPhoto` entries
- Links to patrol entry via `online_patrol_id`
- Stores in database as BYTEA

#### POI Automation:
- Auto-creates profiles for alleged persons
- Links to universal POI system
- Creates cross-source connections

### 3. **Database Migration** (`migrate_online_patrol_redesign.py`)

#### New Columns Added:
- `discovered_by` (VARCHAR 255)
- `discovery_time` (TIMESTAMP)
- `source_time` (TIMESTAMP)
- `alleged_nature` (TEXT - JSON array)
- `alleged_subject_english` (TEXT)
- `alleged_subject_chinese` (TEXT)
- `allegation_summary` (TEXT)
- `license_numbers_json` (TEXT)
- `intermediary_types_json` (TEXT)

#### New Table Created:
- `online_patrol_photo`
  - id (SERIAL PRIMARY KEY)
  - online_patrol_id (FOREIGN KEY)
  - filename (VARCHAR 255)
  - image_data (BYTEA) - Binary photo storage
  - uploaded_at (TIMESTAMP)
  - uploaded_by (VARCHAR 255)
  - caption (TEXT)

## 🚀 Deployment Steps

### Step 1: Run Database Migration
```bash
python migrate_online_patrol_redesign.py
```

Expected output:
```
🚀 ONLINE PATROL MODULE REDESIGN - DATABASE MIGRATION
======================================================================

📋 STEP 1: Adding new columns to online_patrol_entry table...
   ➕ Adding column 'discovered_by'...
   ✅ Column 'discovered_by' added successfully
   ➕ Adding column 'discovery_time'...
   ✅ Column 'discovery_time' added successfully
   ...

📦 STEP 2: Migrating data from old columns to new columns...
   🔄 Copying 'sender' → 'discovered_by'...
   ✅ Updated X rows with discovered_by
   ...

📸 STEP 3: Creating OnlinePatrolPhoto table...
   ➕ Creating online_patrol_photo table...
   ✅ Table 'online_patrol_photo' created successfully
   ...
```

### Step 2: Restart Docker Containers
```bash
docker-compose down
docker-compose up -d --build
```

### Step 3: Test Create Entry
1. Navigate to INT Source → Online Patrol tab
2. Click "Create Entry" button
3. Fill in required fields:
   - Platform/Source (required)
   - Post Time (required)
   - Discovery Time (required)
   - Discovered By (required)
   - Source Reliability (required)
   - Content Validity (required)
   - Reviewer Name (required)
   - Reviewer Comment (required)
4. Upload photos (optional)
5. Add alleged persons (optional)
6. Select alleged nature categories (optional)
7. Click Save

### Step 4: Verify Photo Storage
Check database:
```sql
-- View photo entries
SELECT id, online_patrol_id, filename, length(image_data) as size_bytes, uploaded_at 
FROM online_patrol_photo;

-- Verify patrol entries with photos
SELECT op.id, op.discovered_by, COUNT(opp.id) as photo_count
FROM online_patrol_entry op
LEFT JOIN online_patrol_photo opp ON opp.online_patrol_id = op.id
GROUP BY op.id, op.discovered_by;
```

## 📊 Feature Comparison

| Feature | Old Form | New Form |
|---------|----------|----------|
| Fields | Sender, Complaint Time, Status | Discovered By, Discovery Time, Source Time, Platform |
| Photo Upload | ❌ None | ✅ Multiple files (JPEG, PNG, PDF) |
| Photo Storage | N/A | ✅ Binary (BYTEA) in database |
| Alleged Person | ❌ Manual text | ✅ Dynamic multi-input with add/remove |
| Alleged Nature | ❌ None | ✅ Multi-select with searchable categories |
| Assessment | Basic | ✅ Full assessment aligned with Email standards |
| POI Automation | ❌ Limited | ✅ Auto-creates profiles with universal links |
| INT Reference | ✅ Auto-generated | ✅ Auto-generated (unified system) |

## 🎯 Benefits

### For Intelligence Team:
1. **Professional Structure** - Aligned with law enforcement intelligence standards
2. **Photo Evidence** - Upload screenshots of suspicious posts directly
3. **Multi-Allegation Support** - Select multiple violation categories per entry
4. **Better Tracking** - Distinguish between post time vs discovery time
5. **POI Integration** - Auto-links to person-of-interest profiles

### For Data Quality:
1. **Standardized Fields** - Consistent with Email and WhatsApp complaint forms
2. **Required Fields** - Ensures complete data entry
3. **Validation** - Prevents incomplete submissions
4. **Binary Storage** - Efficient photo storage (no filesystem dependencies)

### For System Integration:
1. **Unified INT References** - Same system across all intelligence sources
2. **Cross-Source Linking** - POI profiles connect Email, WhatsApp, Patrol, etc.
3. **Assessment Scoring** - Consistent 1-10 scale across all sources
4. **Export Ready** - All data structured for reporting

## 🔍 Testing Checklist

- [ ] Create entry with all required fields
- [ ] Upload single photo (JPEG)
- [ ] Upload multiple photos (JPEG + PNG)
- [ ] Upload PDF document
- [ ] Add multiple alleged persons
- [ ] Select multiple alleged nature categories
- [ ] Verify INT reference auto-generated
- [ ] Check photo count badge in table
- [ ] Verify POI profile auto-created
- [ ] Test backward compatibility (existing entries display correctly)
- [ ] Export to Excel includes new fields

## 📝 Notes

### Backward Compatibility:
- Old fields (sender, complaint_time, status) are **preserved** in database
- Migration script copies data: sender → discovered_by, complaint_time → discovery_time
- Table display uses new fields with fallback to old fields
- No existing data is lost

### Photo Storage:
- Photos stored as BYTEA (binary) in PostgreSQL
- Similar to WhatsAppImage pattern (proven working)
- No filesystem storage needed (Docker-friendly)
- Supports JPEG, PNG, PDF formats

### Alleged Nature:
- Uses same multi-select component as Email complaints
- JSON array storage for flexibility
- Searchable categories for fast selection
- Supports multiple selections per entry

## 🚨 Important

**MUST run migration script BEFORE restarting Docker!**

If you restart without migration:
- Application will crash trying to access non-existent columns
- Error: `column "discovered_by" does not exist`

Migration script is idempotent (safe to run multiple times).

## 📚 Related Files

- `templates/int_source_online_patrol_edit.html` - Form template
- `app1_production.py` (lines 6718-6860) - Create entry route
- `migrate_online_patrol_redesign.py` - Database migration script
- `templates/alleged_nature_multi_select.html` - Reusable allegation component
- `templates/alleged_nature_multi_select_js.html` - JavaScript for multi-select

## ✅ Status

**Implementation: COMPLETE**
**Migration Script: READY**
**Testing: PENDING**
**Deployment: READY**

---

**Last Updated:** October 28, 2025
**Author:** GitHub Copilot
**Version:** 2.0 (Professional Redesign)
