# 🚀 DEPLOYMENT CHECKLIST - Alleged Subject Pairing Fix

## ✅ Pre-Deployment Verification

- [x] Code committed to Git
- [x] Documentation created (`ALLEGED_SUBJECT_PAIRING_FIX.md`)
- [x] All 4 relational tables implemented:
  - [x] EmailAllegedSubject (already working)
  - [x] WhatsAppAllegedSubject
  - [x] OnlinePatrolAllegedSubject  
  - [x] ReceivedByHandAllegedSubject
- [x] Backward compatibility maintained (legacy columns preserved)
- [x] Company name detection added (15+ indicators)
- [x] Subset matching tightened (2+ words, length ratio ≤2x)

---

## 📋 Deployment Steps

### **Step 1: Pull Latest Code**

```bash
ssh user@your-server
cd /path/to/new-intel-platform
git pull origin main
```

**Expected output**:
```
Updating cdb8f34..b7e0ced
Fast-forward
 ALLEGED_SUBJECT_PAIRING_FIX.md | 374 ++++++++++++++++++++
 app1_production.py             |  32 +-
 alleged_person_automation.py   |  28 +-
```

### **Step 2: Create Database Tables**

**Option A: Inside Docker Container (Recommended)**

```bash
docker exec -it new-intel-platform-web-1 python3 -c "
from app1_production import app, db
app.app_context().push()
db.create_all()
print('✅ New tables created successfully!')
"
```

**Option B: Direct on Server**

```bash
cd /path/to/new-intel-platform
python3 -c "
from app1_production import app, db
app.app_context().push()
db.create_all()
print('✅ New tables created successfully!')
"
```

**Expected tables created**:
- `whatsapp_alleged_subjects`
- `online_patrol_alleged_subjects`
- `received_by_hand_alleged_subjects`

### **Step 3: Restart Application**

```bash
# If using Docker Compose
docker-compose restart web

# Or if using systemd
sudo systemctl restart intel-platform

# Or if using supervisor
sudo supervisorctl restart intel-platform
```

### **Step 4: Verify Deployment**

#### **A. Check Application Logs**

```bash
# Docker logs
docker logs new-intel-platform-web-1 --tail=100

# Look for:
# ✅ Database tables created
# ✅ Alleged Person Automation System loaded
# ✅ No errors during startup
```

#### **B. Verify Database Tables**

```bash
# PostgreSQL
docker exec -it new-intel-platform-db-1 psql -U postgres -d intelligence_db -c "
SELECT table_name 
FROM information_schema.tables 
WHERE table_name LIKE '%alleged_subjects'
ORDER BY table_name;
"
```

**Expected output**:
```
          table_name          
------------------------------
 email_alleged_subjects
 online_patrol_alleged_subjects
 received_by_hand_alleged_subjects
 whatsapp_alleged_subjects
(4 rows)
```

#### **C. Check Table Structure**

```sql
\d whatsapp_alleged_subjects

-- Expected columns:
-- id, whatsapp_id, english_name, chinese_name, 
-- license_type, license_number, sequence_order, created_at
```

---

## 🧪 Testing Checklist

### **Test 1: WhatsApp Entry with Multiple Alleged Subjects**

1. Navigate to WhatsApp Intelligence Source
2. Create or edit an entry with 2 alleged subjects:
   - Person 1: English="LEUNG TAI LIN", Chinese="梁大連"
   - Person 2: English="CHIEN WAI MAN", Chinese="錢偉文"
3. Save entry
4. **Expected**: Database should have 2 rows in `whatsapp_alleged_subjects`:
   ```sql
   SELECT * FROM whatsapp_alleged_subjects WHERE whatsapp_id = [entry_id];
   -- Row 1: sequence_order=0, english_name='LEUNG TAI LIN', chinese_name='梁大連'
   -- Row 2: sequence_order=1, english_name='CHIEN WAI MAN', chinese_name='錢偉文'
   ```

### **Test 2: POI Profile Creation with Correct Pairing**

1. After saving WhatsApp entry, go to "Alleged Subject List"
2. **Expected**: Two POI profiles created:
   - POI-XXX: LEUNG TAI LIN (梁大連) ✅
   - POI-YYY: CHIEN WAI MAN (錢偉文) ✅
3. **NOT Expected**:
   - POI-XXX: LEUNG TAI LIN (錢偉文) ❌
   - POI-YYY: CHIEN WAI MAN (梁大連) ❌

### **Test 3: Company Name Detection**

1. Create WhatsApp entry with:
   - Person 1: "LEUNG TAI LIN" (person)
   - Person 2: "LEUNG INSURANCE LIMITED" (company)
2. Refresh POI profiles
3. **Expected**: Only 1 POI profile created (for person)
4. **NOT Expected**: POI matching person with company name

### **Test 4: Online Patrol**

Repeat Test 1-2 for Online Patrol entries

### **Test 5: Received By Hand**

Repeat Test 1-2 for Received By Hand entries

---

## 🔍 Monitoring

### **Check Application Logs for Automation**

```bash
# Look for POI automation logs
docker logs new-intel-platform-web-1 -f | grep "AUTOMATION"

# Expected log patterns:
# [WHATSAPP AUTOMATION] 🚀 Auto-updating POI profiles for WhatsApp {id}
# [POI RELINK] 🧹 Removing old POI links for WHATSAPP-{id}
# [POI RELINK] ✅ Old links removed, creating new links based on updated names
# [WHATSAPP AUTOMATION] ✅ Created universal link for POI {poi_id}
```

### **Monitor Database Activity**

```sql
-- Check recent alleged subject records
SELECT 
    'whatsapp' as source,
    COUNT(*) as total_subjects,
    COUNT(DISTINCT whatsapp_id) as entries_with_subjects,
    MAX(created_at) as last_created
FROM whatsapp_alleged_subjects
UNION ALL
SELECT 
    'patrol' as source,
    COUNT(*) as total_subjects,
    COUNT(DISTINCT patrol_id) as entries_with_subjects,
    MAX(created_at) as last_created
FROM online_patrol_alleged_subjects
UNION ALL
SELECT 
    'received_by_hand' as source,
    COUNT(*) as total_subjects,
    COUNT(DISTINCT received_by_hand_id) as entries_with_subjects,
    MAX(created_at) as last_created
FROM received_by_hand_alleged_subjects;
```

---

## ⚠️ Rollback Plan

If issues occur:

### **Option 1: Rollback Code**

```bash
cd /path/to/new-intel-platform
git reset --hard cdb8f34  # Previous commit
docker-compose restart web
```

### **Option 2: Keep Code, Remove Tables**

```sql
-- Drop new tables (data loss!)
DROP TABLE IF EXISTS whatsapp_alleged_subjects CASCADE;
DROP TABLE IF EXISTS online_patrol_alleged_subjects CASCADE;
DROP TABLE IF EXISTS received_by_hand_alleged_subjects CASCADE;
```

**Note**: Legacy comma-separated columns still exist, so old functionality will work.

---

## 📊 Success Criteria

- [ ] All 4 tables created successfully
- [ ] Application starts without errors
- [ ] WhatsApp entries save to relational table
- [ ] Online Patrol entries save to relational table
- [ ] Received By Hand entries save to relational table
- [ ] POI profiles created with correct English-Chinese pairing
- [ ] No company names matched with personal names
- [ ] No errors in application logs
- [ ] UI displays alleged subjects correctly

---

## 🆘 Troubleshooting

### **Issue: Tables not created**

**Symptom**: Error "table whatsapp_alleged_subjects does not exist"

**Solution**:
```bash
docker exec -it new-intel-platform-web-1 python3 -c "
from app1_production import app, db
app.app_context().push()
db.create_all()
"
```

### **Issue: POI profiles still have wrong pairing**

**Symptom**: POI shows "LEUNG TAI LIN (錢偉文)" instead of "LEUNG TAI LIN (梁大連)"

**Diagnosis**:
1. Check if data is in relational table:
   ```sql
   SELECT * FROM whatsapp_alleged_subjects WHERE whatsapp_id = [id];
   ```
2. Check POI automation logs for errors
3. Verify `sequence_order` is sequential (0, 1, 2...)

**Solution**: Re-edit the entry and save to migrate data

### **Issue: Legacy columns not populated**

**Symptom**: Old code breaks because `alleged_subject_english` is NULL

**Diagnosis**: Check if backward compatibility code is running

**Solution**: Code should populate both new tables AND legacy columns. Check lines ~8530, ~8757, ~9095 in app1_production.py

---

## 📝 Post-Deployment Actions

1. **Monitor for 24 hours**: Watch logs for any errors
2. **Test with real data**: Create multiple entries with various name combinations
3. **User communication**: Inform team about the fix
4. **Documentation update**: Update user manual if needed
5. **Performance check**: Monitor query performance on new tables
6. **Index optimization**: Add indexes if queries are slow

---

## 📞 Support

**Issues?** Check:
- Application logs: `docker logs new-intel-platform-web-1`
- Database logs: `docker logs new-intel-platform-db-1`
- GitHub Issues: [repo]/issues

**Contact**:
- Email: [your-email]
- Slack: [your-channel]

---

**Deployment Date**: _____________
**Deployed By**: _____________
**Verified By**: _____________
**Status**: ⏳ PENDING / ✅ COMPLETE / ❌ ROLLED BACK
