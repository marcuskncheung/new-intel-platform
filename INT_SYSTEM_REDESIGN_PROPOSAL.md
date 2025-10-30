if# 🔗 INT Reference System Redesign Proposal

## Current Problem

### Issue 1: WhatsApp generates INT-184 when latest email is INT-182
- WhatsApp creates independent sequence instead of unified chronological system
- Renumbering logic happens BEFORE new entry is added to database
- Race condition causes incorrect INT assignment

### Issue 2: Automatic renumbering may not be desired
- If older email arrives after newer WhatsApp, should INT numbers change?
- Current system tries to maintain chronological order automatically
- But this may disrupt existing case references

## Proposed Solution: Two-Tier Reference System

### Tier 1: **Source-Specific IDs** (Auto-generated, Never Change)
```
EMAIL-001, EMAIL-002, EMAIL-003...
WHATSAPP-001, WHATSAPP-002...
PATROL-001, PATROL-002...
SURVEILLANCE-001, SURVEILLANCE-002...
```

**Purpose:** Unique identifier for each intelligence item
**Display:** Show in intelligence source list (INT Source page)
**Benefits:**
- Each source has own sequence (no conflicts)
- Never changes once assigned
- Easy to reference individual items

### Tier 2: **Case INT Numbers** (Manual Grouping)
```
INT-001, INT-002, INT-003...
```

**Purpose:** Group related intelligence across sources into cases
**Assignment:** Manual (officer reviews and assigns)
**Display:** Show in Case Profile list
**Benefits:**
- Officer decides which items belong to same case
- Can link EMAIL-045 + WHATSAPP-023 + PATROL-012 → INT-007
- Reflects actual investigation workflow
- No automatic renumbering

## Implementation Changes

### 1. Display Changes

**INT Source Page** (Email/WhatsApp/Patrol tabs):
```
Current: Shows "INT-182" for email
Proposed: Shows "EMAIL-182" or just the email ID

Each row shows:
- Source ID: EMAIL-182
- Case INT: INT-007 (if assigned) or [Assign to Case]
- Subject/Details
- Alleged Person
```

### 2. Case Profile Page:
```
Shows: INT-007

Linked Intelligence:
- EMAIL-045 (received 2025-10-15)
- EMAIL-067 (received 2025-10-18)
- WHATSAPP-023 (received 2025-10-19)
- PATROL-012 (received 2025-10-20)

All about same person/allegation
```

### 3. Workflow:
1. Email arrives → Auto-assigned EMAIL-182
2. Officer reviews → Recognizes it matches existing case
3. Officer clicks "Assign to Case INT-007"
4. EMAIL-182 now linked to INT-007
5. Case INT-007 shows all linked sources

## Code Changes Required

### A. Remove automatic INT chronological insertion
- Keep source-specific sequences (EMAIL-001, WHATSAPP-001)
- Remove automatic CaseProfile creation on intelligence entry
- Case INT assigned manually by officer

### B. Add manual case assignment UI
- Button in email detail: "Assign to Case"
- Modal: Search existing cases or create new INT
- Link intelligence item to case

### C. Update display logic
- INT Source page: Show source IDs (EMAIL-XXX)
- Case Profile page: Show case INT (INT-XXX) with linked sources
- POI Profile page: Show both source IDs and case INTs

## Migration Strategy

### Option A: Keep current system (auto chronological)
**Fix bugs:**
- Fix renumbering race condition
- Ensure WhatsApp/Patrol use same sequence as Email
- Make chronological insertion work correctly

**Pros:** Less work, maintains current workflow
**Cons:** Renumbering disrupts references, complexity

### Option B: Switch to manual case grouping
**Changes:**
- Remove automatic CaseProfile creation
- Add manual assignment interface
- Keep source-specific IDs

**Pros:** Clearer workflow, no renumbering issues, matches investigation process
**Cons:** More work initially, officers must manually assign cases

## Recommendation

**Implement Option B** (Manual Case Grouping)

**Rationale:**
1. Matches real-world investigation workflow
2. Officers need to review before grouping anyway
3. Avoids complex automatic renumbering bugs
4. Each source has stable ID that never changes
5. Case INT truly represents a "case" not just chronological order

**Immediate Actions:**
1. Keep source IDs stable (EMAIL-182 stays EMAIL-182)
2. Display source IDs in INT Source page
3. Make Case INT (INT-XXX) manual assignment
4. Add "Assign to Case" button in intelligence details
5. Case Profile shows all linked sources

## Question for User

Which approach do you prefer?

**A. Fix automatic chronological system:**
- INT-001, INT-002, INT-003 in date order across all sources
- Automatic renumbering when older items arrive
- One unified sequence

**B. Separate source IDs + manual case grouping:**
- EMAIL-182, WHATSAPP-023, PATROL-012 (source-specific)
- INT-007 (manually assigned case number for related items)
- Two-tier system

My recommendation is **Option B** because it:
- Reflects how officers actually work (review then group)
- Avoids renumbering bugs
- Clearer separation of "intelligence item" vs "case"
