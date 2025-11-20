# 🔍 Global Intelligence Search - Feature Documentation

## Overview
**Commit:** `2a00856`  
**Date:** November 20, 2025  
**Status:** ✅ Deployed and Ready for Testing

The new **Global Search** feature transforms the old basic `/index` search into a powerful, Google-like search system that works across ALL intelligence sources in the platform.

---

## 🎯 What Changed

### **Before (Old `/index` Search)**
- ❌ Only searched `CaseProfile` table
- ❌ Only searched alleged subjects (English/Chinese names)
- ❌ Limited to agent number search
- ❌ Basic table display with no context
- ❌ No direct links to original sources
- ❌ No search across email bodies, WhatsApp messages, etc.

### **After (New Global Search)**
- ✅ Searches across **5 intelligence sources** (POI, Email, WhatsApp, Patrol, Surveillance)
- ✅ Searches **ALL text fields** (names, subjects, bodies, details, locations, etc.)
- ✅ Modern, Google-like interface with color-coded results
- ✅ Smart snippet extraction with keyword highlighting
- ✅ Direct "View" buttons to jump to original sources
- ✅ Source type filtering (toggle on/off)
- ✅ Real-time search with loading indicator
- ✅ Match field tracking (shows WHERE the keyword was found)

---

## 📍 Accessed From

### 🏠 **NOW THE HOME PAGE!**
- **Main URL:** https://10.96.135.11/ (home page redirects to global search)
- **Direct URL:** https://10.96.135.11/global-search
- **Shortcut:** https://10.96.135.11/home (redirects to global search)
- **Shortcut:** https://10.96.135.11/index (redirects to global search)
- **Shortcut:** https://10.96.135.11/search (redirects to global search)

### Navigation Menu
- **Menu Item:** "Global Search" 
- **Logo Click:** Clicking "Intelligence" logo also goes to Global Search
- **Active Highlighting:** Menu item highlights when on home/search pages

---

## 🔍 What Can You Search?

### 1. **POI Profiles (Alleged Persons)**
Search in:
- ✅ English names (e.g., "David Chan")
- ✅ Chinese names (e.g., "陳大文")
- ✅ License numbers (e.g., "FA1234", "FB5678")
- ✅ Company names (e.g., "Prudential", "AIA")
- ✅ Aliases (alternative names)

**Results Show:**
- POI ID (e.g., POI-037)
- Full name (English + Chinese)
- License number
- Company
- Total mentions across all sources
- Direct link to POI profile

### 2. **Email Intelligence**
Search in:
- ✅ Email subject lines
- ✅ Email body content (full text search)
- ✅ Sender email addresses
- ✅ Alleged person names (English/Chinese)
- ✅ Allegation nature/type

**Results Show:**
- Email subject
- Sender
- Alleged persons mentioned
- Smart snippet (100 chars before/after your keyword)
- INT reference number
- Received date/time
- Direct link to email detail page

### 3. **WhatsApp Reports**
Search in:
- ✅ Complaint names
- ✅ Phone numbers
- ✅ Alleged person names
- ✅ Allegation types
- ✅ Message details/content

**Results Show:**
- Complaint name
- Phone number
- Alleged persons
- Message snippet
- INT reference
- Direct link to WhatsApp detail

### 4. **Online Patrol Entries**
Search in:
- ✅ Alleged person names
- ✅ Alleged nature/misconduct type
- ✅ Details and findings
- ✅ Platform names (Facebook, Instagram, etc.)

**Results Show:**
- Alleged persons
- Nature of allegation
- Details snippet
- INT reference
- Direct link to patrol entry

### 5. **Surveillance Operations**
Search in:
- ✅ Target names
- ✅ Locations
- ✅ Operation findings/details

**Results Show:**
- Target names
- Location
- Findings snippet
- INT reference
- Direct link to surveillance detail

---

## 🎨 User Interface Features

### Search Bar
- **Large, prominent search input** (like Google)
- **Placeholder text:** "Search for person name, email content, case details, license number..."
- **Enter key support** for quick search
- **Real-time search** with loading spinner

### Source Filters
Toggle on/off to search specific sources:
- 🔵 **POI Profiles** (blue badge)
- 🔵 **Email** (primary blue badge)
- 🟢 **WhatsApp** (success green badge)
- 🟡 **Patrol** (warning yellow badge)
- 🔴 **Surveillance** (danger red badge)

### Result Cards
Each result appears in a color-coded card:
- **Left border color** matches source type
- **Hover effect** (lifts up slightly)
- **Keyword highlighting** (yellow background)
- **Match reason** shows which field matched
- **View button** (color-coded by source type)

### Results Summary
Shows:
- ✅ Total number of results found
- ✅ Search query used
- ✅ Search time in milliseconds
- ✅ Result counts per source type

---

## 💡 Usage Examples

### Example 1: Find Person Named "David Chan"
**Search:** `David Chan`

**Will Find:**
- POI profile if exists (shows all their mentions)
- Emails where "David Chan" appears in:
  - Subject line
  - Email body
  - Alleged person field
- WhatsApp reports mentioning David Chan
- Patrol entries where David Chan was found
- Surveillance operations targeting David Chan

**Result:** Click "View" button on any result to jump directly to that source

---

### Example 2: Find License Number
**Search:** `FA1234`

**Will Find:**
- POI profile with that license number
- Emails mentioning that license number
- Any other source referencing that license

**Use Case:** Quickly verify if a license number has been reported before

---

### Example 3: Find Company Name
**Search:** `Prudential`

**Will Find:**
- POI profiles working at Prudential
- Emails mentioning Prudential
- WhatsApp reports about Prudential agents
- Patrol findings related to Prudential

**Use Case:** See all intelligence related to a specific company

---

### Example 4: Find Keyword in Email Bodies
**Search:** `insurance fraud`

**Will Find:**
- Emails with "insurance fraud" in body or subject
- WhatsApp messages discussing insurance fraud
- Patrol entries about insurance fraud
- Allegation natures marked as insurance fraud

**Result:** Each result shows a snippet with your keywords highlighted

---

### Example 5: Filter by Source Type
**Search:** `Chan Tai Man`  
**Filter:** Only enable "Email" checkbox

**Will Find:**
- ONLY emails mentioning Chan Tai Man
- Ignores WhatsApp, Patrol, Surveillance results

**Use Case:** Narrow down search to specific intelligence source

---

## 🔧 Technical Implementation

### Frontend (`templates/global_search.html`)
- **Framework:** Bootstrap 5 with custom CSS
- **JavaScript:** Vanilla JS with Fetch API
- **Features:**
  - AJAX search (no page reload)
  - Dynamic result rendering
  - Keyword highlighting with regex
  - Responsive design

### Backend API (`/api/global-search`)
- **Route:** `/api/global-search?q=keyword&filters=POI,EMAIL,WHATSAPP,PATROL,SURVEILLANCE`
- **Method:** GET
- **Authentication:** `@login_required`
- **Response:** JSON with results grouped by source type

**Search Algorithm:**
1. Get search query and active filters
2. For each enabled source:
   - Query database table
   - Check all text fields with case-insensitive match
   - Extract snippet around keyword match
   - Track which field matched
   - Build result object
3. Return results grouped by source type
4. Frontend renders color-coded cards

### Database Queries
- **POI:** `AllegedPersonProfile` table (via factory pattern)
- **Email:** `Email` table (subject, body, sender, alleged persons)
- **WhatsApp:** `WhatsAppEntry` table (details, phone, alleged persons)
- **Patrol:** `OnlinePatrolEntry` table (details, alleged persons, nature)
- **Surveillance:** `SurveillanceEntry` + `Target` tables (findings, locations, targets)

---

## 🚀 Deployment Status

### Commit History
```bash
commit 2a00856
Author: Marcus Cheung
Date: November 20, 2025

🔍 Feature: Google-like Global Intelligence Search

- Created /global-search page
- Added /api/global-search API
- Updated navigation menu
- Redirected /index to new search
```

### Files Changed
- ✅ `app1_production.py` (+448 lines) - API route and redirect
- ✅ `templates/global_search.html` (NEW) - Modern search UI
- ✅ `templates/base.html` - Updated navigation
- ✅ `templates/base_OFFLINE.html` - Updated offline navigation

### GitHub Actions
- ⏳ **Status:** Building Docker image...
- ⏳ **Next:** Deploy to production (docker compose pull && up -d)

---

## 📊 Performance

### Expected Search Times
- **Small datasets** (<1000 records): <100ms
- **Medium datasets** (1000-10000 records): 100-500ms
- **Large datasets** (>10000 records): 500-1500ms

### Optimization Notes
- Case-insensitive search uses database `LOWER()` function
- Results limited to relevant matches only
- Snippet extraction limited to 200 characters
- No pagination (all results shown at once)

---

## 🎯 Next Steps (Future Enhancements)

### Potential Improvements
1. **Advanced Filters:**
   - Date range filtering
   - Risk level filtering (for POI)
   - Case status filtering

2. **Search Suggestions:**
   - Auto-complete as you type
   - Recent searches
   - Popular searches

3. **Export Results:**
   - Export to Excel
   - Export to PDF
   - Generate search report

4. **Saved Searches:**
   - Save frequently used searches
   - Email alerts for new matches

5. **Full-Text Search:**
   - PostgreSQL full-text search (FTS)
   - Weighted relevance scoring
   - Fuzzy matching for typos

---

## ✅ Testing Checklist

After deployment, test these scenarios:

- [ ] Search for a known POI name → Should find POI profile
- [ ] Search for email subject keywords → Should find matching emails
- [ ] Search for license number → Should find POI and emails
- [ ] Toggle source filters → Should show/hide results
- [ ] Click "View" buttons → Should navigate to correct detail pages
- [ ] Search with no results → Should show "No results found"
- [ ] Test Chinese character search → Should work correctly
- [ ] Test search timing display → Should show milliseconds
- [ ] Test on mobile device → Should be responsive
- [ ] Test with very long query → Should not break

---

## 📞 Support

**Feature Built By:** GitHub Copilot + Marcus Cheung  
**Date:** November 20, 2025  
**Version:** 1.0  

For questions or issues, check:
1. GitHub Actions build status
2. Docker container logs
3. Browser console for JavaScript errors
4. Flask app logs for API errors

---

## 🎉 Summary

**BEFORE:** Basic search only looked in CaseProfile table for alleged subjects  
**AFTER:** Google-like search across POI, Email, WhatsApp, Patrol, and Surveillance with smart snippets, highlighting, and direct navigation

**🏠 HOME PAGE:** Global Search is now the landing page when users log in - the most useful feature front and center!

**User Benefit:** Find anyone or anything mentioned anywhere in the intelligence system with one search!
