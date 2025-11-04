# 🚀 DEPLOYMENT: WhatsApp/Patrol Name Pairing Fix

## 📋 What This Fixes

**CRITICAL BUG**: WhatsApp and Online Patrol alleged subjects were stored as comma-separated strings, causing wrong English-Chinese name pairing in POI profiles.

**Example of Bug**:
- Input: "LEUNG TAI LIN, CHIEN" + "梁大連, 錢某某"
- Wrong Output: "LEUNG TAI LIN (錢某某)" or "CHIEN (梁大連)"
- Correct Output: "LEUNG TAI LIN (梁大連)" and "CHIEN (錢某某)"

**Root Cause**: System didn't know which English name pairs with which Chinese name.

**Solution**: New relational tables (`whatsapp_alleged_subject`, `online_patrol_alleged_subject`) with `sequence_order` to guarantee correct pairing (mimics Email system).

---

## 🔧 Deployment Steps

### Step 1: Pull Latest Code

```bash
cd /path/to/new-intel-platform-main
git pull origin main
```

### Step 2: Restart Docker Containers

```bash
# Stop containers
docker-compose down

# Rebuild and start (this will pick up new code)
docker-compose up -d --build
```

### Step 3: Create New Database Tables

**Option A: Run Script Inside Container**

```bash
# Enter the Flask container
docker exec -it <flask-container-name> bash

# Run the table creation script
python3 create_alleged_subject_tables.py

# Exit container
exit
```

**Option B: Run via Docker Exec (One Command)**

```bash
docker exec <flask-container-name> python3 create_alleged_subject_tables.py
```

**Expected Output**:
```
================================================================================
🔍 CHECKING ALLEGED SUBJECT TABLES
================================================================================
⚠️  Table 'whatsapp_alleged_subject' does NOT exist - will create
⚠️  Table 'online_patrol_alleged_subject' does NOT exist - will create

================================================================================
🔨 CREATING MISSING TABLES
================================================================================
✅ Database tables created successfully!

📋 VERIFICATION:
✅ whatsapp_alleged_subject: id, whatsapp_id, english_name, chinese_name, license_type, license_number, sequence_order
✅ online_patrol_alleged_subject: id, patrol_id, english_name, chinese_name, license_type, license_number, sequence_order

================================================================================
✅ SETUP COMPLETE - New relational tables ready for English-Chinese name pairing!
================================================================================
```

### Step 4: Verify Deployment

1. **Check Container Logs**:
   ```bash
   docker logs <flask-container-name> --tail 50
   ```

2. **Test WhatsApp Entry**:
   - Go to WhatsApp entry edit page
   - Add alleged person: English="LEUNG TAI LIN" Chinese="梁大連"
   - Add another: English="CHIEN" Chinese="錢某某"
   - Save and refresh POI profiles
   - Verify correct pairing in POI profiles

3. **Check Database**:
   ```bash
   docker exec -it <postgres-container-name> psql -U <db-user> -d <db-name>
   
   # Check table exists
   \dt whatsapp_alleged_subject
   \dt online_patrol_alleged_subject
   
   # Check data
   SELECT * FROM whatsapp_alleged_subject LIMIT 5;
   SELECT * FROM online_patrol_alleged_subject LIMIT 5;
   ```

---

## 📊 What Changed

### New Database Tables

**`whatsapp_alleged_subject`**:
- `id` (Primary Key)
- `whatsapp_id` (Foreign Key → whatsapp_entry.id)
- `english_name` (TEXT)
- `chinese_name` (TEXT)
- `license_type` (VARCHAR 64)
- `license_number` (VARCHAR 64)
- `sequence_order` (INTEGER) ← **CRITICAL**: Guarantees pairing
- **Constraint**: At least one name (English or Chinese) must be provided
- **Unique**: (whatsapp_id, sequence_order)

**`online_patrol_alleged_subject`**:
- Same structure but links to `online_patrol_entry.id`

### Code Changes

1. **app1_production.py**:
   - Added `WhatsAppAllegedSubject` model (lines 1100-1124)
   - Added `OnlinePatrolAllegedSubject` model (lines 1126-1150)
   - Updated `int_source_whatsapp_update_assessment()` to save to new table
   - Updated `add_whatsapp()` to save to new table
   - Updated `int_source_patrol_update_assessment()` to save to new table
   - **Backward compatibility**: Old comma-separated columns still populated

2. **alleged_person_automation.py**:
   - Enhanced company name detection (15+ indicators)
   - Tightened subset matching rules
   - Returns 0.0 similarity if one is company, one is person

---

## ⚠️ Important Notes

### Backward Compatibility

- **Old entries**: Will continue using comma-separated fields (may have wrong pairing)
- **New entries**: Will use relational tables (guaranteed correct pairing)
- **Recommendation**: Re-edit important old entries to migrate data to new tables

### Migration Path

**Option 1: Gradual Migration** (Recommended)
- New entries automatically use new tables
- Edit old entries manually when needed
- Old entries fall back to comma-separated fields

**Option 2: Bulk Migration** (Future)
- Create migration script to copy data from old columns to new tables
- Would need to guess pairing based on index (may not be accurate)
- Not recommended due to uncertainty

### Legacy Fields

These fields are kept for backward compatibility:
- `whatsapp_entry.alleged_subject_english`
- `whatsapp_entry.alleged_subject_chinese`
- `online_patrol_entry.alleged_subject_english`
- `online_patrol_entry.alleged_subject_chinese`

Can be removed after validation period (e.g., 3 months).

---

## 🐛 Rollback Plan

If issues arise:

```bash
# Rollback code
git revert HEAD
docker-compose down
docker-compose up -d --build

# Drop new tables (if needed)
docker exec -it <postgres-container-name> psql -U <db-user> -d <db-name>
DROP TABLE IF EXISTS whatsapp_alleged_subject;
DROP TABLE IF EXISTS online_patrol_alleged_subject;
```

---

## ✅ Success Criteria

1. ✅ New tables created in PostgreSQL
2. ✅ WhatsApp entries save to `whatsapp_alleged_subject` table
3. ✅ Online Patrol entries save to `online_patrol_alleged_subject` table
4. ✅ POI profiles show correct English-Chinese pairing
5. ✅ No "LEUNG TAI LIN (錢某某)" mismatches
6. ✅ Company names no longer match personal names

---

## 📞 Support

If deployment issues occur:
1. Check container logs: `docker logs <flask-container-name>`
2. Check PostgreSQL connection: `docker exec <postgres-container-name> pg_isready`
3. Verify table creation: Run Step 3 again
4. Test with sample WhatsApp entry

**Contact**: System Administrator
