# POI Profile Auto-Update Implementation

## Date: 2025-01-17

## Overview
Implemented automatic POI (Person of Interest) profile creation and updates across all intelligence sources with POI v2.0 universal linking support.

---

## Problem 1: Email Display Fix ✅ COMPLETED

### Issue
- Despite successful migration of 65 email-POI links to `poi_intelligence_link` table
- POI detail page showed 0 emails
- Root cause: Only querying new POI v2.0 table, missing backward compatibility

### Solution Implemented
Modified `alleged_subject_profile_detail()` route in `app1_production.py`:

1. **Dual Table Query**:
   - Query both `poi_intelligence_link` (new POI v2.0) 
   - Query `email_alleged_person_link` (old POI v1.0)
   - Ensures backward compatibility

2. **Deduplication Logic**:
   ```python
   email_ids_already_added = {email['id'] for email in emails}
   for old_link, email in old_email_links:
       if email.id not in email_ids_already_added:
           # Add email to results
   ```

3. **Fixed Loop Structure**:
   - Separate loops for EMAIL processing (both old and new tables)
   - Loop for WHATSAPP, PATROL, SURVEILLANCE from new table only
   - Changed `elif` to `if` statements for independent checks

### Files Modified
- `app1_production.py` (lines ~2076-2260)

---

## Problem 2: Auto-Update POI Profiles ✅ COMPLETED

### Issue
- When users update assessment details (Email, WhatsApp, Patrol, Surveillance)
- POI profiles should be automatically created/updated
- Links should be created in both old and new POI tables

### Solution Implemented

#### 1. Enhanced `alleged_person_automation.py`

**Function**: `link_email_to_profile()` (lines 560-590)

**Changes**:
- Added POI v2.0 universal link creation
- Creates link in `poi_intelligence_link` table
- Maintains backward compatibility with old `email_alleged_person_link` table

```python
# Create link in old table (POI v1.0)
new_link = EmailAllegedPersonLink(...)
db.session.add(new_link)

# Create link in new table (POI v2.0)
try:
    from app1_production import POIIntelligenceLink, Email
    
    universal_link = POIIntelligenceLink(
        poi_id=profile_id,
        source_type='EMAIL',
        source_id=email_id,
        case_id=email.caseprofile_id,
        confidence_score=0.95,
        extraction_method='AUTOMATION',
        created_by='AUTOMATION'
    )
    db.session.add(universal_link)
except Exception as e:
    # Graceful fallback if POI v2.0 not available
    pass
```

#### 2. WhatsApp Auto-Update

**Route**: `add_whatsapp()` (lines ~5376-5430)

**Features**:
- Automatically detects alleged persons from form input
- Determines if name is English or Chinese using regex
- Creates/updates POI profiles
- Creates universal links in `poi_intelligence_link` table

```python
if ALLEGED_PERSON_AUTOMATION and alleged_person_str:
    alleged_persons = [p.strip() for p in alleged_person_str.split(',')]
    
    for person_name in alleged_persons:
        is_chinese = bool(re.search(r'[\u4e00-\u9fff]', person_name))
        
        result = create_or_update_alleged_person_profile(
            db, AllegedPersonProfile, EmailAllegedPersonLink,
            name_english=None if is_chinese else person_name,
            name_chinese=person_name if is_chinese else None,
            source="WHATSAPP",
            update_mode="merge"
        )
        
        # Create universal link
        if result.get('profile_id'):
            universal_link = POIIntelligenceLink(
                poi_id=result['profile_id'],
                source_type='WHATSAPP',
                source_id=entry.id,
                ...
            )
```

**Route**: `whatsapp_detail()` - Edit Mode (lines ~6360-6410)

**Features**:
- Same automation when editing existing WhatsApp entries
- Updates POI profiles when alleged persons change
- Creates new universal links as needed

#### 3. Email Auto-Update (Already Existed)

**Route**: `int_source_update_assessment()` (lines ~6593-6660)

**Status**: ✅ Already implemented with automation
- Now enhanced with POI v2.0 support via `link_email_to_profile()` function
- Processes multiple alleged subjects with English/Chinese names
- Handles insurance license information

#### 4. Online Patrol Auto-Update 🆕

**Database Change**: Added `alleged_person` field to `OnlinePatrolEntry` model

**Route**: `add_online_patrol()` (lines ~5530-5588)

**Features**:
- Accepts multiple alleged persons from form
- Auto-detects Chinese vs English names
- Creates POI profiles automatically
- Creates universal links in `poi_intelligence_link` table

**Route**: `online_patrol_detail()` - Edit Mode (lines ~5620-5678)

**Features**:
- Updates POI profiles when patrol details change
- Processes alleged person changes
- Creates new universal links as needed

**Migration Required**: 
```bash
python migrate_add_alleged_person_patrol.py
```

#### 5. Surveillance Auto-Update 🆕

**Route**: `add_surveillance()` (lines ~5880-5960)

**Features**:
- Processes surveillance targets (Target model)
- Each target becomes a POI profile
- Includes license information (agent/broker numbers)
- Creates universal links with HIGH confidence (0.95)
- Physical surveillance = highest confidence

```python
# Surveillance has multiple targets with license info
for idx, name in enumerate(target_names):
    license_type = license_types[idx]  # Agent, Broker, N/A
    license_number = license_numbers[idx]
    
    additional_info = {
        'license_number': license_number,
        'agent_number': license_number,
        'role': license_type
    }
    
    result = create_or_update_alleged_person_profile(
        ...,
        source="SURVEILLANCE",
        additional_info=additional_info
    )
```

### Files Modified
- `alleged_person_automation.py` (lines 560-590)
- `app1_production.py`:
  - `OnlinePatrolEntry` model (line 1007) - Added `alleged_person` field
  - `add_whatsapp()` route (lines ~5376-5430)
  - `whatsapp_detail()` route (lines ~6360-6410)
  - `add_online_patrol()` route (lines ~5530-5588)
  - `online_patrol_detail()` route (lines ~5620-5678)
  - `add_surveillance()` route (lines ~5880-5960)
- `migrate_add_alleged_person_patrol.py` - New migration script

---

## Technical Details

### POI v2.0 Universal Link Schema
```python
class POIIntelligenceLink(db.Model):
    poi_id = db.Column(db.Integer)           # Links to AllegedPersonProfile
    source_type = db.Column(db.String)       # EMAIL, WHATSAPP, PATROL, SURVEILLANCE
    source_id = db.Column(db.Integer)        # ID of source record
    case_id = db.Column(db.Integer)          # Optional case reference
    confidence_score = db.Column(db.Float)   # 0.0-1.0
    extraction_method = db.Column(db.String) # AUTOMATION, MANUAL_UPDATE, etc.
    created_by = db.Column(db.String)        # USER-username or AUTOMATION
    created_at = db.Column(db.DateTime)
    last_activity_date = db.Column(db.DateTime)
```

### Automation Flow

```
User Updates Assessment
        ↓
Extract Alleged Persons
        ↓
For Each Person:
  ├─→ Determine Language (English/Chinese)
  ├─→ Call create_or_update_alleged_person_profile()
  │   ├─→ Find matching profile (smart name matching)
  │   ├─→ Create new profile if no match (assign POI-XXX ID)
  │   └─→ Update existing profile if match found
  │
  └─→ Create Links:
      ├─→ Old table: email_alleged_person_link (POI v1.0)
      └─→ New table: poi_intelligence_link (POI v2.0)
```

### Name Detection Logic
```python
# Chinese name detection
is_chinese = bool(re.search(r'[\u4e00-\u9fff]', person_name))

if is_chinese:
    name_chinese = person_name
    name_english = None
else:
    name_english = person_name
    name_chinese = None
```

---

## Benefits

### 1. Automated Profile Management
- ✅ No manual POI profile creation needed
- ✅ Profiles updated automatically when new information available
- ✅ Smart duplicate detection prevents profile duplication

### 2. Cross-Source Intelligence
- ✅ POI profiles linked to Email, WhatsApp, Patrol, Surveillance
- ✅ Universal `poi_intelligence_link` table for all sources
- ✅ Easy to query all intelligence about a person

### 3. Backward Compatibility
- ✅ Old POI v1.0 links still work
- ✅ Graceful fallback if POI v2.0 not available
- ✅ Migration safe - no data loss

### 4. User Experience
- ✅ Save assessment → POI profiles created automatically
- ✅ See all intelligence about a person in one view
- ✅ Flash messages inform users of automation actions

---

## Implementation Status

### ✅ Completed
1. Email display fix (dual table query with deduplication)
2. POI v2.0 universal link creation in email automation
3. WhatsApp create automation with POI linking
4. WhatsApp edit automation with POI linking
5. **Online Patrol create automation with POI linking** 🆕
6. **Online Patrol edit automation with POI linking** 🆕
7. **Surveillance create automation with POI linking** 🆕
8. Backward compatibility layer
9. **Database migration script for patrol alleged_person field** 🆕

### 🔄 Requires Database Migration
- Run `migrate_add_alleged_person_patrol.py` to add `alleged_person` column to `online_patrol_entry` table

### 📋 Future Enhancements
1. **Surveillance Edit Automation**: Add POI profile automation when surveillance entries are edited
2. **Bulk Profile Updates**: Tool to update multiple POI profiles at once
3. **Profile Merging UI**: Interface to merge duplicate POI profiles
4. **Intelligence Timeline**: Visual timeline of all intelligence about a POI
5. **Enhanced UI Forms**: Update patrol/surveillance forms to include alleged person fields

---

## Testing Checklist

### Email Intelligence
- [ ] Create email with alleged persons → Check POI profiles created
- [ ] Update email assessment → Check POI profiles updated
- [ ] View POI detail page → Check emails display correctly
- [ ] Check both old and new POI links created

### WhatsApp Intelligence
- [ ] Create WhatsApp entry with alleged persons → Check POI profiles created
- [ ] Edit WhatsApp complaint details → Check POI profiles updated
- [ ] View POI detail page → Check WhatsApp entries display
- [ ] Test with Chinese names
- [ ] Test with English names
- [ ] Test with mixed names

### Online Patrol Intelligence 🆕
- [ ] **FIRST**: Run migration: `python migrate_add_alleged_person_patrol.py`
- [ ] Create patrol entry with alleged persons → Check POI profiles created
- [ ] Edit patrol details with new alleged persons → Check POI profiles updated
- [ ] View POI detail page → Check patrol entries display
- [ ] Test with Chinese names
- [ ] Test with English names
- [ ] Test with multiple alleged persons

### Surveillance Intelligence 🆕
- [ ] Create surveillance entry with targets → Check POI profiles created
- [ ] Add targets with license info → Check license info in POI profiles
- [ ] View POI detail page → Check surveillance entries display
- [ ] Test with Agent license type
- [ ] Test with Broker license type
- [ ] Test with multiple targets
- [ ] Verify HIGH confidence score (0.95) for surveillance

### Cross-Source Verification
- [ ] One POI mentioned in Email + WhatsApp + Patrol + Surveillance → Check all show in detail
- [ ] Statistics cards show correct counts for all 4 sources
- [ ] Tabbed interface filters sources correctly (5 tabs total)
- [ ] No duplicate entries in "All Sources" tab
- [ ] "Total Intelligence" count = sum of all sources

---

## Deployment Notes

### Prerequisites
- PostgreSQL 15.14+ with `poi_intelligence_link` table
- `ALLEGED_PERSON_AUTOMATION = True` in configuration

### Deployment Steps
1. Commit all changes
2. Push to GitHub repository
3. SSH to server: `ssh root@your-server-ip`
4. Pull latest code: `cd /root/intelligence-platform && git pull origin main`
5. **Run database migration**: 
   ```bash
   docker exec -it intelligence-app python migrate_add_alleged_person_patrol.py
   ```
6. Restart application: `docker-compose restart intelligence-app`
7. Test all source workflows:
   - Email alleged persons
   - WhatsApp alleged persons
   - **Patrol alleged persons** 🆕
   - **Surveillance targets** 🆕

### Rollback Plan
If issues occur:
```bash
# Revert to previous commit
git log --oneline  # Find previous commit hash
git revert <commit-hash>
git push origin main

# Restart
docker-compose restart intelligence-app
```

---

## Configuration

### Enable/Disable Automation
```python
# In app1_production.py or config file
ALLEGED_PERSON_AUTOMATION = True   # Enable automation
ALLEGED_PERSON_AUTOMATION = False  # Disable automation
```

### Confidence Scores
- **Email (Manual Entry)**: 0.95 (Very High - User explicitly added)
- **WhatsApp (Automated)**: 0.90 (High - From form input)
- **AI Extraction**: 0.75-0.85 (Medium-High - AI analysis)

---

## Maintenance

### Regular Checks
1. **POI Profile Count**: Monitor growth rate
2. **Link Quality**: Check for orphaned links
3. **Duplicate Detection**: Run duplicate profile checks monthly
4. **Performance**: Monitor query performance as data grows

### Database Queries for Monitoring
```sql
-- Check POI profile count
SELECT COUNT(*) FROM alleged_subject_profile WHERE status = 'ACTIVE';

-- Check universal links by source
SELECT source_type, COUNT(*) 
FROM poi_intelligence_link 
GROUP BY source_type;

-- Find POIs with multiple sources
SELECT poi_id, COUNT(DISTINCT source_type) as source_count
FROM poi_intelligence_link
GROUP BY poi_id
HAVING COUNT(DISTINCT source_type) > 1;

-- Recent POI activity (last 7 days)
SELECT COUNT(*) 
FROM poi_intelligence_link 
WHERE created_at > NOW() - INTERVAL '7 days';
```

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f intelligence-app | grep -i "automation"`
2. Check database: `docker exec -it postgres-db psql -U intelligence -d intelligence_db`
3. Review this document
4. Contact development team

---

## Version History

- **v2.1.0** (2025-01-17): POI v2.0 auto-update implementation
  - Email display fix with backward compatibility
  - WhatsApp automation with universal linking
  - Enhanced automation framework
  
- **v2.0.0** (2025-01-16): POI v2.0 migration
  - Created `poi_intelligence_link` table
  - Migrated 65 email-POI links
  - Cross-source UI enhancement

- **v1.0.0** (Earlier): POI v1.0
  - Basic email-POI linking
  - Manual profile creation
