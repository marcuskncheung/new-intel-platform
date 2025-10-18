# Template Alignment Plan: WhatsApp & Online Patrol → Email

**Date:** 2025-10-19  
**Goal:** Align WhatsApp and Online Patrol detail pages with Email detail page structure

---

## 📋 Email Detail Page Structure (Reference)

### **Section Order:**

1. **Header**
   - Email subject
   - Sender & received date
   - Action buttons (AI Analysis, Back to Inbox)

2. **AI Details Section** (if exists)
   - Comprehensive AI analysis report
   - Shows when AI has processed the email

3. **📌 Case Reference Number** (INT-XXX)
   - Editable INT reference number field
   - Save button
   - Manual/auto assignment status

4. **📧 Email Content**
   - Thread blocks (current email + previous threads)
   - Expandable/collapsible sections
   - Styled with left border

5. **📎 Attachments** (if exists)
   - List of attachments
   - View & Download buttons

6. **🤖 AI Analysis Results** (if exists)
   - Alleged subjects
   - Allegation type
   - Source reliability & content validity scores

7. **📝 Assessment Details Form**
   - Date & Preparer
   - **Alleged Subjects** with:
     * English Name field
     * Chinese Name field
     * Insurance intermediary checkbox
     * License type dropdown (Agent/Broker/Other)
     * License number field
     * Add/Remove person buttons
   - Allegation Type & Nature
   - Allegation Summary (detailed description)
   - Source Reliability (1-5)
   - Content Validity (1-5)
   - Reviewer section (Name, Comment, Decision)
   - Save Assessment button

---

## 🎯 WhatsApp Required Changes

### **Current Structure:**
- Basic complaint info editing
- Simple alleged_person field (comma-separated names)
- No case reference number
- No detailed assessment form

### **Required Changes:**

1. ✅ **Add Case Reference Number Section** (after header)
   - INT reference number field
   - Save button
   - Same styling as email

2. ✅ **Move WhatsApp Content Section** (after case reference)
   - Contact information
   - Message details
   - Keep existing structure

3. ✅ **Add/Keep Images Section** (after content)
   - Display uploaded images
   - Same as current attachments display

4. ✅ **Replace Simple Alleged Person Field with Detailed Form**
   - English name field
   - Chinese name field
   - Insurance intermediary checkbox
   - License type (Agent/Broker/Other)
   - License number field
   - Add/Remove person buttons
   - Match email template structure exactly

5. ✅ **Add Full Assessment Details Section**
   - Preparer dropdown
   - Allegation Type & Nature
   - Allegation Summary
   - Source Reliability (1-5)
   - Content Validity (1-5)
   - Reviewer section
   - Save Assessment button

---

## 🎯 Online Patrol Required Changes

### **Current Structure:**
- Basic patrol info editing
- Simple alleged_person field (comma-separated names)
- No case reference number
- Basic assessment (reliability & validity only)

### **Required Changes:**

1. ✅ **Add Case Reference Number Section** (after header)
   - INT reference number field
   - Save button
   - Same styling as email

2. ✅ **Keep Online Patrol Details Section** (after case reference)
   - Sender, source, status
   - Complaint time
   - Details/Synopsis
   - Keep existing structure

3. ✅ **Add Photos Section** (if upload feature exists)
   - Display uploaded photos from creation
   - Similar to WhatsApp images display

4. ✅ **Replace Simple Alleged Person Field with Detailed Form**
   - English name field
   - Chinese name field
   - Insurance intermediary checkbox
   - License type (Agent/Broker/Other)
   - License number field
   - Add/Remove person buttons
   - Match email template structure exactly

5. ✅ **Upgrade Assessment Details Section**
   - Keep existing: Source Reliability, Content Validity
   - **Add new fields:**
     * Preparer dropdown
     * Allegation Type & Nature
     * Allegation Summary (detailed description)
     * Reviewer section (Name, Comment, Decision)
   - Save Assessment button

---

## 🔧 Implementation Steps

### **Phase 1: WhatsApp Template**

1. Read current `whatsapp_detail_test.html`
2. Create backup copy
3. Restructure sections:
   - Add Case Reference Number section (copy from email template)
   - Keep WhatsApp content section
   - Keep images display
   - Replace alleged_person field with detailed form (copy from email)
   - Add full assessment section (copy from email)
4. Update JavaScript functions for add/remove persons
5. Test with existing WhatsApp entries

### **Phase 2: Online Patrol Template**

1. Read current `int_source_online_patrol_edit.html`
2. Create backup copy
3. Restructure sections:
   - Add Case Reference Number section
   - Keep patrol details section
   - Add photos display (if applicable)
   - Replace alleged_person field with detailed form
   - Upgrade assessment section
4. Update JavaScript functions
5. Test with existing patrol entries

### **Phase 3: Backend Route Updates**

**WhatsApp Route (`whatsapp_detail`):**
- ✅ Already has POI automation
- ✅ Already has smart redirect
- ⏸️ Need to handle new form fields:
  * `alleged_subjects_en[]`
  * `alleged_subjects_cn[]`
  * `license_numbers[]`
  * `intermediary_type[]`
  * `allegation_summary`
  * `reviewer_name`, `reviewer_comment`, `reviewer_decision`

**Online Patrol Route (`online_patrol_detail`):**
- ✅ Already has POI automation
- ✅ Already has smart redirect
- ⏸️ Need to handle new form fields (same as WhatsApp)

### **Phase 4: Database Schema Check**

Check if WhatsApp and OnlinePatrolEntry models have these fields:
- `allegation_summary` (TEXT)
- `reviewer_name` (VARCHAR)
- `reviewer_comment` (TEXT)
- `reviewer_decision` (VARCHAR)
- `license_numbers_json` (TEXT/JSON)
- `intermediary_types_json` (TEXT/JSON)
- `alleged_subject_english` (TEXT)
- `alleged_subject_chinese` (TEXT)

**If missing:** Need to add migration or update model definitions.

---

## 📝 Code Reuse Strategy

### **JavaScript Functions to Copy:**

From `int_source_email_detail.html`:
```javascript
function toggleInsuranceFields(checkbox)
function addAllegedSubject()
function removeAllegedSubject(button)
```

### **HTML Sections to Copy:**

1. **Case Reference Number Section** (lines ~60-110 in email template)
2. **Alleged Subjects Form Section** (lines ~295-450 in email template)
3. **Assessment Form Table** (lines ~260-700 in email template)

### **CSS Styles to Maintain:**

- Same card borders and colors
- Same form styling
- Same button styles
- Same badge styles for scores

---

## ✅ Success Criteria

After implementation, WhatsApp and Online Patrol should:

1. ✅ Have same visual layout as Email detail page
2. ✅ Allow detailed alleged person editing with license numbers
3. ✅ Have full assessment form (preparer, reliability, validity, reviewer)
4. ✅ Show case reference number prominently
5. ✅ Process POI automation with license info
6. ✅ Smart redirect to POI profiles after save
7. ✅ Maintain backward compatibility with old data

---

## 🚨 Important Notes

- Keep all existing functionality (don't break current features)
- Ensure backward compatibility (old entries without new fields should still work)
- Test POI automation with new detailed fields
- Verify smart redirect still works after changes
- Check that license numbers are properly saved and displayed

