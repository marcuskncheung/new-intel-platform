# 📖 Intelligence Platform - User Manual

> **Version:** 2.0 | **Last Updated:** December 2025  
> A comprehensive guide to help you navigate and use the Intelligence Platform effectively.

---

## 📑 Table of Contents

1. [Getting Started](#1-getting-started)
2. [Dashboard Overview](#2-dashboard-overview)
3. [Intelligence Sources](#3-intelligence-sources)
4. [POI (Person of Interest) Management](#4-poi-person-of-interest-management)
5. [Case Management](#5-case-management)
6. [Global Search](#6-global-search)
7. [Reports & Analytics](#7-reports--analytics)
8. [Admin Functions](#8-admin-functions)
9. [Tips & Shortcuts](#9-tips--shortcuts)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Getting Started

### 🔐 Logging In

1. Open your web browser and navigate to the platform URL
2. Enter your **Username** and **Password**
3. Click **Login**
4. You will be redirected to the **Dashboard**

> 💡 **Tip:** Contact your administrator if you forget your password.

### 🏠 First Time Navigation

After logging in, you'll see the main navigation bar at the top with these sections:

| Menu Item | Description |
|-----------|-------------|
| 📊 Dashboard | Platform overview and statistics |
| 📧 INT Source | All intelligence sources (Email, WhatsApp, etc.) |
| 👤 POI Profiles | Person of Interest management |
| 📁 Cases | Case file management |
| 🔍 Global Search | Search across all data |

---

## 2. Dashboard Overview

The Dashboard is your home base - it shows a quick overview of the entire platform.

### 📈 Statistics Cards

At the top, you'll see quick stats:

- **Total POIs** - Number of Persons of Interest
- **Total Cases** - Number of open case files
- **Email Intelligence** - Count of email entries
- **WhatsApp Intelligence** - Count of WhatsApp entries
- **Online Patrol** - Count of patrol findings
- **Received by Hand** - Count of manual entries

### 📋 Recent Activity

Below the stats, you'll see recent intelligence entries from all sources.

---

## 3. Intelligence Sources

### 📧 Email Intelligence

**To view email intelligence:**
1. Click **INT Source** → **Email**
2. Browse the list of imported emails
3. Click on any email to view details

**Email Details Page shows:**
- Subject, sender, date received
- Email body content
- Attachments (if any)
- Linked POIs (Alleged Subjects)
- INT Reference number

### 💬 WhatsApp Intelligence

**To add WhatsApp intelligence:**
1. Click **INT Source** → **WhatsApp**
2. Click **+ Add New Entry**
3. Fill in the form:
   - Received Time
   - Content/Summary
   - Attach screenshots if needed
4. Click **Save**

### 🌐 Online Patrol

**To add patrol findings:**
1. Click **INT Source** → **Online Patrol**
2. Click **+ Add New Entry**
3. Enter:
   - Discovery Time
   - Platform (Facebook, Instagram, etc.)
   - URL/Link
   - Content summary
   - Screenshots
4. Click **Save**

### 📬 Received by Hand

**For physical documents or verbal reports:**
1. Click **INT Source** → **Received by Hand**
2. Click **+ Add New Entry**
3. Enter:
   - Received Date
   - Source/From whom
   - Content description
   - Scan/upload documents
4. Click **Save**

---

## 4. POI (Person of Interest) Management

### 👥 Viewing POI List

1. Click **POI Profiles** in the navigation
2. You'll see all Persons of Interest as cards

**Each card shows:**
- Name (English & Chinese)
- POI ID (e.g., POI-001)
- Number of linked cases
- Risk level badge (Low/Medium/High/Critical)
- Status (Active/Inactive)

### 🔍 Filtering POIs

Use the filter buttons at the top:

| Filter | Shows |
|--------|-------|
| **All** | All POI profiles |
| **High Risk** | POIs with 3+ cases |
| **Active** | Only active POIs |

### 📊 Sorting POIs

Click the **Sort** dropdown to sort by:
- Recent Activity
- Name (A-Z)
- Most Cases

### 👤 Viewing POI Details

Click on any POI card to see the full profile:

**Profile Header:**
- Name, POI ID, Status
- Company, License Number, Role

**Cases Section (Purple Bar):**
- Total number of INT cases
- List of INT reference numbers

**Risk Assessment Gauge:**
- Visual indicator of risk level
- Based on number of cases

**Intelligence Timeline:**
- All intelligence linked to this POI
- Tabs to filter by source (Email, WhatsApp, Patrol, etc.)

### ✏️ Editing a POI

1. Open the POI profile
2. Click **Edit Profile** in Quick Actions
3. Update the information
4. Click **Save**

### 🔄 Rebuilding POI List (Admin)

If POIs seem out of sync:
1. Go to POI Profiles list
2. Click **Rebuild POI List** (Admin only)
3. Confirm the action
4. Wait for the process to complete

---

## 5. Case Management

### 📁 What is an INT Reference?

Each intelligence entry can be assigned an **INT Reference** number (e.g., `INT-2025-001`). This groups related intelligence together into a "case".

### 🔢 Assigning INT References

When viewing any intelligence entry:
1. Look for the **INT Reference** field
2. Click to assign or change the reference
3. Enter the INT number (e.g., `INT-2025-001`)
4. Click **Save**

### 📋 Viewing Cases

1. Click **Cases** in navigation
2. See all case profiles
3. Click any case to view:
   - All linked intelligence
   - All linked POIs
   - Case timeline

---

## 6. Global Search

### 🔍 How to Search

1. Click **Global Search** in navigation (or press `/`)
2. Type your search term
3. Press **Enter** or click **Search**

### 🎯 Search Tips

| Search For | Example |
|------------|---------|
| Person name | `John Chan` |
| Company | `ABC Insurance` |
| INT Reference | `INT-2025-001` |
| License number | `FA12345` |
| Keywords | `fraud complaint` |

### 📂 Search Results

Results are grouped by source:
- 📧 Email matches
- 💬 WhatsApp matches
- 🌐 Online Patrol matches
- 📬 Received by Hand matches
- 👤 POI matches

Click any result to view the full details.

---

## 7. Reports & Analytics

### 📊 Dashboard Statistics

The Dashboard automatically shows:
- Total counts for each source
- Recent activity feed
- Quick access links

### 🖨️ Printing Reports

**To print a POI profile:**
1. Open the POI profile
2. Click **Print Report** in Quick Actions
3. Use your browser's print function

---

## 8. Admin Functions

> ⚠️ **Note:** These features require admin privileges.

### 👤 User Management

1. Click your profile icon → **Admin**
2. Go to **User Management**
3. Add, edit, or deactivate users

### 🔄 Rebuild POI List

If POIs need to be refreshed:
1. Go to **POI Profiles**
2. Click **Rebuild POI List**
3. This will:
   - Scan all intelligence sources
   - Update POI counts
   - Fix any misaligned data

### 📋 Audit Logs

View system activity:
1. Go to **Admin** → **Audit Logs**
2. See login history, changes, deletions

---

## 9. Tips & Shortcuts

### ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `/` | Open Global Search |
| `Esc` | Close modal/dialog |

### 💡 Best Practices

1. **Always assign INT references** - This keeps intelligence organized
2. **Link POIs promptly** - Connect alleged subjects to intelligence as you add it
3. **Use consistent naming** - `CHAN Tai Man` not `Chan, Tai Man`
4. **Add screenshots** - Visual evidence is valuable for Online Patrol entries
5. **Regular backups** - Contact admin for backup schedules

### 🔢 Understanding Risk Levels

| Level | Cases | Meaning |
|-------|-------|---------|
| 🟢 **LOW** | 0-1 | Minimal concern |
| 🟡 **MEDIUM** | 2 | Moderate concern |
| 🔴 **HIGH** | 3-4 | Significant concern |
| ⚫ **CRITICAL** | 5+ | Urgent attention needed |

---

## 10. Troubleshooting

### ❌ Common Issues

#### "Page not loading"
- Check your internet connection
- Try refreshing the page (F5)
- Clear browser cache

#### "Cannot see POI details"
- Make sure you're logged in
- Check if the POI exists
- Contact admin if persists

#### "Search returns no results"
- Try different keywords
- Check spelling
- Use partial names

#### "Cannot edit entry"
- Check if you have permission
- Make sure no one else is editing
- Refresh the page

### 📞 Getting Help

If you encounter issues:
1. Note the error message
2. Take a screenshot
3. Contact your system administrator
4. Provide:
   - What you were trying to do
   - What happened
   - The error message (if any)

---

## 📝 Quick Reference Card

### Navigation
```
Dashboard       → Platform overview
INT Source      → All intelligence entries
POI Profiles    → Person of Interest list
Cases           → Case file management
Global Search   → Search everything
```

### Adding Intelligence
```
1. Go to INT Source
2. Select source type (Email/WhatsApp/Patrol/By Hand)
3. Click "+ Add New"
4. Fill in details
5. Save
```

### Finding a POI
```
1. Go to POI Profiles
2. Use search box OR
3. Use filter pills (All/High Risk/Active)
4. Click POI card to view details
```

### Linking Intelligence to POI
```
1. Open intelligence entry
2. Find "Alleged Subjects" section
3. Add/link person names
4. Save
```

---

## 📌 Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | Dec 2025 | Added POI redesign, Risk Assessment, Quick Actions |
| 1.5 | Nov 2025 | Added Rebuild POI feature |
| 1.0 | Oct 2025 | Initial release |

---

> 📧 **Support:** Contact your system administrator for assistance.  
> 🔒 **Security:** Never share your login credentials with others.

---

*© 2025 Intelligence Platform. All rights reserved.*
