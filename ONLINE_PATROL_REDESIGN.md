# 📱 ONLINE PATROL MODULE REDESIGN - IMPLEMENTATION COMPLETE

## Overview
Comprehensive redesign of the Online Patrol module to meet professional intelligence gathering standards for tracking suspicious online posts from social media platforms (IG, WeChat, Facebook, forums, etc.).

---

## ✅ Completed Changes

### 1. **Database Model Redesign** (`app1_production.py`)

#### New Professional Fields:
| Field | Type | Purpose |
|-------|------|---------|
| `discovered_by` | VARCHAR(255) | Intelligence team member who found the post |
| `discovery_time` | TIMESTAMP | When we logged/discovered it in our system |
| `source_time` | TIMESTAMP | When the online post was originally created/published |

#### Photo Upload Support:
- Created `OnlinePatrolPhoto` table model
- Stores photos/screenshots of suspicious posts
- Fields: `id`, `online_patrol_id`, `filename`, `image_data` (BYTEA), `uploaded_at`, `uploaded_by`, `caption`
- Relationship: `photos = db.relationship('OnlinePatrolPhoto', ...)`

#### Legacy Fields Retained:
- `sender` → DEPRECATED, use `discovered_by` instead
- `complaint_time` → DEPRECATED, use `source_time` or `discovery_time`
- `status` → DEPRECATED, use assessment fields instead

### 2. **UI Redesign** (`templates/int_source.html`)

#### New Column Structure:
| Column | Display | Description |
|--------|---------|-------------|
| **Source ID** | `PATROL-{id}` | Unique identifier badge |
| **INT Reference** | `INT-YYYY-NNNN` | Linked case profile reference (clickable) |
| **Platform/Source** | Badge | IG, WeChat, Facebook, Forum, etc. |
| **Post Time** | DateTime | When the original post was created |
| **Discovered By** | Name | Intel team member who found it |
| **Discovery Time** | DateTime | When we logged it |
| **Photos** | Count badge | Number of uploaded photos |
| **Score & Action** | Combined | Score badge + View/Delete buttons |

#### Improvements:
- ✅ Combined "Score" and "Action" columns for streamlined review
- ✅ Photo count indicator with icon
- ✅ Professional badge styling for scores (color-coded by severity)
- ✅ INT Reference clickable link to case details
- ✅ Backward compatibility with legacy data

### 3. **Migration Script** (`migrate_online_patrol_redesign.py`)

#### Migration Process:
```bash
# Run migration BEFORE restarting containers
python migrate_online_patrol_redesign.py
```

#### What it does:
1. ✅ Adds new columns: `discovered_by`, `discovery_time`, `source_time`
2. ✅ Migrates data: `sender` → `discovered_by`, `complaint_time` → `discovery_time` & `source_time`
3. ✅ Creates `online_patrol_photo` table with indexes
4. ✅ Preserves all existing data
5. ✅ Keeps legacy columns for backward compatibility

---

## 🎯 Key Features

### Photo Upload Capability
```python
# Model relationship
entry.photos  # Access all photos for an entry
photo.image_data  # Binary photo data stored in database
photo.caption  # Optional photo description
```

### Professional Intelligence Recording
**Use Case**: Intelligence team logs suspicious agent misconduct found on social media

**Example Entry**:
- **Platform**: Instagram
- **Post Time**: 2025-10-27 15:30 (when agent posted)
- **Discovered By**: Officer Chan
- **Discovery Time**: 2025-10-28 09:15 (when we found it)
- **Photos**: 2 screenshots attached
- **Score**: 8/10 (Source: 4/5, Content: 4/5)

### Allegation Standards Alignment
The Online Patrol module now uses the same allegation categorization as complaint emails:
- `alleged_nature` → JSON array of allegation types
- `allegation_summary` → Detailed summary
- `alleged_subject_english` & `alleged_subject_chinese` → Standardized name fields
- `license_numbers_json` → Agent/Broker license tracking

---

## 📊 Benefits

### For Intelligence Team:
1. **Clear Timeline**: Distinguish between when content was created vs. when we discovered it
2. **Photo Evidence**: Upload and store screenshots of suspicious posts
3. **Better Tracking**: Know who discovered what and when
4. **Consistent Standards**: Same allegation types as email complaints

### For Management:
1. **Professional Reports**: Clear, well-structured data
2. **Photo Documentation**: Visual evidence attached to cases
3. **Audit Trail**: Full tracking of discovery and assessment
4. **Integrated System**: Seamless with INT Reference system

### For System:
1. **Backward Compatible**: Old data still accessible
2. **Scalable**: Photo storage in database (no file system issues)
3. **Consistent Schema**: Aligned with other intelligence sources
4. **Future-Proof**: Easy to add more fields as needed

---

## 🚀 Deployment Instructions

### Step 1: Run Migration
```bash
cd /Users/iapanel/Downloads/new-intel-platform-main
python migrate_online_patrol_redesign.py
```

### Step 2: Commit Changes
```bash
git add app1_production.py templates/int_source.html migrate_online_patrol_redesign.py
git commit -m "Redesign Online Patrol module - Professional structure + Photo upload"
git push origin main
```

### Step 3: Restart Docker
```bash
docker-compose down
docker-compose up -d --build
```

### Step 4: Verify
1. Navigate to INT Source → Online Patrol tab
2. Check new columns display correctly
3. Test creating new entry with photos
4. Verify legacy data displays properly

---

## 📝 TODO: Forms & Routes Update

### Still Needed:
1. **Update `add_online_patrol` route** to handle new fields:
   - Add `discovered_by`, `discovery_time`, `source_time` form fields
   - Add photo upload handling

2. **Update `online_patrol_detail` template** to:
   - Display new fields professionally
   - Show uploaded photos
   - Allow photo upload/delete

3. **Update `online_patrol_export` route** to:
   - Include new columns in Excel export
   - Include photo count/list

4. **Create photo upload/view routes**:
   - `/online_patrol/<id>/upload_photo` (POST)
   - `/online_patrol/photo/<id>` (GET - view photo)
   - `/online_patrol/photo/<id>/delete` (POST)

---

## 🔧 Technical Details

### Database Schema Changes:
```sql
-- New columns added
ALTER TABLE online_patrol_entry ADD COLUMN discovered_by VARCHAR(255);
ALTER TABLE online_patrol_entry ADD COLUMN discovery_time TIMESTAMP;
ALTER TABLE online_patrol_entry ADD COLUMN source_time TIMESTAMP;

-- New table created
CREATE TABLE online_patrol_photo (
    id SERIAL PRIMARY KEY,
    online_patrol_id INTEGER NOT NULL REFERENCES online_patrol_entry(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    image_data BYTEA NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by VARCHAR(255),
    caption TEXT
);

CREATE INDEX idx_online_patrol_photo_patrol_id ON online_patrol_photo(online_patrol_id);
```

### Model Changes:
```python
class OnlinePatrolEntry(db.Model):
    # New professional fields
    discovered_by = db.Column(db.String(255))
    discovery_time = db.Column(db.DateTime, default=get_hk_time)
    source_time = db.Column(db.DateTime)
    
    # Photo relationship
    photos = db.relationship('OnlinePatrolPhoto', backref='patrol_entry', 
                            lazy=True, cascade="all, delete-orphan")
```

---

## ✨ Success Criteria

- [x] Database model updated with new fields
- [x] Migration script created and tested
- [x] UI template updated with new columns
- [x] Photo upload table created
- [x] Backward compatibility maintained
- [ ] Forms updated (add/edit entry)
- [ ] Photo upload functionality implemented
- [ ] Export updated with new fields
- [ ] User testing completed

---

## 📞 Support

For questions or issues:
1. Check migration output for errors
2. Verify database schema with: `\d online_patrol_entry` in psql
3. Check Flask logs for any template errors
4. Test with small dataset first

---

**Status**: ✅ Core structure complete, forms/routes update needed
**Date**: October 28, 2025
**Version**: 1.0.0
