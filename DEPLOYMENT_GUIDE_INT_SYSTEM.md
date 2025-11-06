# 🚀 Unified INT Reference System - Deployment Guide

## ✅ What Has Been Completed

### Phase 1: Backend Implementation ✅
- ✅ Enhanced `/api/int_references/search` to search across ALL sources
- ✅ Added `/api/int_references/list` endpoint for autocomplete
- ✅ Created reusable INT reference component
- ✅ Committed to GitHub (commits: 5386d44, 9745c0c)

### Phase 2: Template Updates ✅  
- ✅ **Email**: Already had full INT system (Next + Search buttons)
- ✅ **WhatsApp**: Updated with unified component (Next + Search buttons)
- ✅ **Online Patrol**: Updated with unified component (Next + Search buttons)
- ⏳ **Surveillance**: Not yet updated (if surveillance detail page exists)

### Phase 3: Main Table Display ⏳
- ✅ **Email table**: Shows INT Reference column
- ⏳ **WhatsApp table**: INT Reference column needs to be added
- ⏳ **Patrol table**: INT Reference column needs to be added
- ⏳ **Surveillance table**: INT Reference column needs to be added

---

## 🚀 Deployment Steps

### Step 1: Deploy to Server

```bash
# SSH into server
ssh pam-du-uat-ai@10.96.135.11

# Navigate to project directory
cd /home/pam-du-uat-ai

# Pull latest code
git pull origin main

# Verify what was pulled
git log --oneline -3
# Should show:
# 9745c0c ✨ Apply unified INT reference component to WhatsApp and Patrol templates
# 5386d44 🔗 Implement unified INT reference system across all sources
# 020e29a 🔧 Add missing view_patrol_photo route

# Restart Flask application
sudo docker compose restart intelligence-app

# Check application logs
sudo docker compose logs -f intelligence-app
# Press Ctrl+C to exit logs when you see "Running on http://0.0.0.0:8080"

# Verify nginx is still running (should already be running from 413 fix)
sudo docker compose ps | grep nginx
```

---

## ✅ Testing Checklist

### Test 1: Email INT System (Should Still Work)
1. Navigate to https://10.96.135.11/int_source
2. Click on any email to open detail page
3. ✅ Verify INT Reference section shows with Next and Search buttons
4. Click **Next** button → Should show next available INT (e.g., INT-006)
5. Click **Search** button → Enter "test" → Should show matching INT cases
6. Click **Assign** button → Should save successfully

### Test 2: WhatsApp INT System (Newly Updated)
1. Navigate to https://10.96.135.11/int_source
2. Scroll to WhatsApp section
3. Click on any WhatsApp entry
4. ✅ Verify INT Reference section shows:
   - Source ID: WHATSAPP-{id} (read-only)
   - Case INT Reference input field
   - **Next** button (NEW!)
   - **Search** button (NEW!)
   - **Assign Case** button
5. Click **Next** → Should populate with next INT (e.g., INT-006)
6. Click **Search** → Enter a person name → Should find matches across Email/WhatsApp/Patrol
7. Assign an INT → Verify it saves

### Test 3: Online Patrol INT System (Newly Updated)
1. Navigate to https://10.96.135.11/int_source
2. Scroll to Online Patrol section
3. Click on entry #2 (the one that had 413 error - now fixed!)
4. ✅ Verify INT Reference section shows:
   - Source ID: PATROL-2 (read-only)
   - Case INT Reference input field
   - **Next** button (NEW!)
   - **Search** button (NEW!)
   - **Assign Case** button
5. ✅ Verify photos display correctly (413 fix)
6. Click **Next** → Should populate with next INT
7. Click **Search** → Should search across all sources
8. Assign an INT → Verify it saves

### Test 4: Cross-Source Search (New Feature!)
1. Go to any Email detail page
2. Click **Search** button
3. Enter a person name that appears in multiple sources (e.g., from online patrol entry #2)
4. ✅ Verify search results show:
   - INT reference number
   - Source types (Email, WhatsApp, Patrol mix)
   - Total source count
   - Match reason
   - Date created
5. Click on a result → Should populate the INT field

### Test 5: Autocomplete Feature (New!)
1. Go to any WhatsApp or Patrol detail page
2. Start typing in the INT Reference field (e.g., type "INT-")
3. ✅ Verify autocomplete dropdown appears showing all existing INT references
4. Select one from dropdown → Should populate field

---

## 📋 Known Limitations

### Main Table Columns Still Missing INT Reference

**Affected Tables:**
- WhatsApp table in `/int_source` page
- Online Patrol table in `/int_source` page
- Surveillance table in `/int_source` page

**Impact:**
- Users can assign INT references in detail pages
- INT references are saved to database correctly
- But INT references don't show in main table list views yet

**Workaround:**
- Click into individual entries to see their INT references
- INT system fully functional, just not visible in table overview

**Next Phase:**
This will be addressed in a future update to add INT Reference column to all main tables.

---

## 🔍 Troubleshooting

### Issue 1: "Next" Button Doesn't Work
**Symptom**: Click Next button, nothing happens
**Diagnosis**:
```bash
# Check browser console for errors (F12 → Console tab)
# Should see API call to /api/int_references/next_available
```
**Solution**:
```bash
# Verify Flask app restarted successfully
sudo docker compose logs intelligence-app | grep "Running on"

# Check if API endpoint exists
sudo docker compose exec intelligence-app grep -n "next_available" app1_production.py
# Should show line with @app.route("/api/int_references/next_available")
```

### Issue 2: "Search" Button Returns No Results
**Symptom**: Search returns empty even though data exists
**Diagnosis**:
```bash
# Check if CaseProfile table has data
sudo docker compose exec intelligence-db psql -U intelligence_user -d intelligence_db -c "SELECT COUNT(*) FROM case_profile;"

# Check browser console for API errors
```
**Solution**:
- Ensure data exists in CaseProfile table with int_reference values
- Check API logs: `sudo docker compose logs intelligence-app | grep "INT API"`

### Issue 3: 413 Error Returns
**Symptom**: Online patrol save fails with 413 error again
**Diagnosis**:
```bash
# Check nginx config inside container
docker exec intelligence-nginx cat /etc/nginx/nginx.conf | grep "client_max_body_size"
# Should show: client_max_body_size 100M;
```
**Solution**: See previous 413 fix documentation

### Issue 4: Component Doesn't Display
**Symptom**: INT reference section missing or shows error
**Diagnosis**:
```bash
# Check if component file exists
sudo docker compose exec intelligence-app ls -la templates/components/
# Should show: int_reference_component.html

# Check Flask logs for template errors
sudo docker compose logs intelligence-app | grep -i "template\|jinja"
```
**Solution**:
```bash
# Re-pull code
git pull origin main

# Force restart
sudo docker compose down
sudo docker compose up -d
```

---

## 📊 Success Metrics

After deployment, verify these metrics:

1. ✅ **Email INT System**: Still works (no regressions)
2. ✅ **WhatsApp INT System**: Now has Next + Search buttons
3. ✅ **Patrol INT System**: Now has Next + Search buttons
4. ✅ **Cross-Source Search**: Finds matches in Email + WhatsApp + Patrol
5. ✅ **Autocomplete**: Shows all existing INT references
6. ✅ **413 Error Fixed**: Online patrol photos upload successfully

---

## 🎯 Next Steps (Future Enhancements)

### Phase 3: Add INT Column to Main Tables
**Files to Update:**
- `templates/int_source.html` - WhatsApp table section
- `templates/int_source.html` - Online Patrol table section
- `templates/int_source.html` - Surveillance table section

**Change Required:**
Add INT Reference column to table headers and data rows:
```html
<!-- In WhatsApp table -->
<th>INT Reference</th>
...
<td>{{ entry.case_profile.int_reference if entry.case_profile else '-' }}</td>
```

### Phase 4: Surveillance Template (If Exists)
- Check if surveillance detail template needs INT component
- Apply same pattern as WhatsApp/Patrol

### Phase 5: Enhanced Search Features
- Add filters: Search by date range, source type, reliability score
- Add sorting: Sort results by date, source count, relevance
- Add bulk operations: Assign multiple sources to same INT

---

## 📝 Deployment Checklist

Before deploying:
- [x] Backend API endpoints tested locally
- [x] Component template created
- [x] Email template verified (no regressions)
- [x] WhatsApp template updated with component
- [x] Patrol template updated with component
- [x] Code committed to GitHub
- [x] Code pushed to origin/main

After deploying:
- [ ] SSH into server
- [ ] Git pull latest code
- [ ] Restart intelligence-app container
- [ ] Test Email INT system (regression check)
- [ ] Test WhatsApp INT system with new buttons
- [ ] Test Patrol INT system with new buttons
- [ ] Test cross-source search functionality
- [ ] Test autocomplete feature
- [ ] Verify no errors in Flask logs
- [ ] Update team on new features

---

## 💡 User Training Notes

**New Features to Communicate:**

1. **Next Button**
   - Automatically gets next available INT number
   - No need to manually count or check existing numbers
   - Ensures sequential numbering

2. **Search Button**
   - Search for existing cases by person name, nature, or keyword
   - Finds matches across Email, WhatsApp, Online Patrol
   - Shows source types and total linked sources
   - Prevents duplicate case creation

3. **Autocomplete**
   - Type "INT-" to see all existing references
   - Quick way to link to existing cases
   - Shows source count for each INT

4. **Consistent Interface**
   - Same INT assignment workflow across all sources
   - Learn once, use everywhere
   - Email, WhatsApp, Patrol all work the same way

---

## 🏁 Completion Status

**Current State: 90% Complete**

✅ Backend fully implemented
✅ Email INT system working
✅ WhatsApp INT system updated
✅ Patrol INT system updated
⏳ Main table columns need INT display
⏳ Surveillance template (if needed)

**Estimated Time to 100%**: 1-2 hours to add INT columns to main tables

---

## 📧 Support

If issues arise after deployment:
1. Check this guide's Troubleshooting section
2. Review Flask logs: `sudo docker compose logs intelligence-app`
3. Review nginx logs: `sudo docker compose logs intelligence-nginx`
4. Check browser console (F12) for JavaScript errors
5. Verify database connectivity: `sudo docker compose ps`

---

**Deployment Date**: November 5, 2025
**Last Updated**: November 5, 2025
**Version**: 2.0 - Unified INT Reference System
