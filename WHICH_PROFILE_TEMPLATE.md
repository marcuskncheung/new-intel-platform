# 📋 Which Profile Template Are You Using?

## Summary: **YOU ARE USING `poi_profile_detail.html`** ✅

---

## The Confusion Explained

You have **TWO different profile systems** that got mixed up:

### System 1: POI Profile System (NEW - POI-001, POI-002, etc.)
- **Route**: `/alleged_subject_profile/<poi_id>` (e.g., `/alleged_subject_profile/POI-035`)
- **Template**: `poi_profile_detail.html` ✅ (39,880 bytes - **THIS IS THE CORRECT ONE**)
- **Backend**: `alleged_subject_profile_detail()` function at line 1657
- **Features**: 
  - ✅ Uses POI-XXX identifiers
  - ✅ Shows related emails with INT references
  - ✅ Has manual link/unlink functionality (JUST ADDED)
  - ✅ Modern design with gradients
  - ✅ This is what your screenshot shows

### System 2: Old Profile System (OLD - uses numeric IDs)
- **Route**: `/alleged_subject_profiles/<int:profile_id>` (e.g., `/alleged_subject_profiles/105`)
- **Template**: `profile_detail.html` ✅ (35,600 bytes - older version)
- **Backend**: Anonymous function at line 2840
- **Features**:
  - Uses numeric profile IDs (105, 106, etc.)
  - Different URL pattern
  - Older design
  - You probably don't use this anymore

---

## What Just Happened

1. **I edited `poi_profile_detail.html`** ✅ - This is correct!
2. **I added these features**:
   - INT Reference column (leftmost)
   - "Link Email Manually" button
   - "Unlink" button for each row
   - Modal for linking emails
   - JavaScript for validation
3. **I added backend APIs**:
   - `/api/check_email_exists`
   - `/api/link_email_to_profile`
   - `/api/unlink_email_from_profile`
4. **I fixed the route** to use correct template name

---

## Files Modified (Ready to Commit)

```
✅ templates/poi_profile_detail.html    - Frontend UI with link/unlink
✅ app1_production.py                   - Backend APIs + fixed route
```

---

## How to Access Your POI Profile Page

When you click on a profile from the Alleged Subject List, you go to:

```
URL: https://10.96.135.11/alleged_subject_profile/POI-035
Template Used: poi_profile_detail.html
What You See: 
  - POI-035 header
  - YAN LINUN / 日琳琳
  - Agent: N/A
  - Table with allegations
  - INT references (INT-XXX)
  - Link Email button (NEW!)
  - Unlink buttons (NEW!)
```

---

## The Other Template (`profile_detail.html`)

This is probably **not used** in your current system. It's an older template that uses numeric IDs instead of POI-XXX format. You can ignore it or delete it later.

---

## Ready to Deploy

All changes are in `poi_profile_detail.html` and `app1_production.py`. These are the correct files for your POI profile system!

```bash
# Commit and push
git add templates/poi_profile_detail.html app1_production.py
git commit -m "FEATURE: Manual email link/unlink for POI profiles"
git push origin main

# Deploy
ssh root@10.96.135.11
cd /root/intelligence-app
git pull origin main
docker-compose restart intelligence-app
```

---

## Summary

✅ **You're using**: `poi_profile_detail.html` (POI-035, POI-036, etc.)  
❌ **You're NOT using**: `profile_detail.html` (old numeric IDs)  
✅ **I edited the correct file**: YES!  
✅ **Ready to deploy**: YES!
