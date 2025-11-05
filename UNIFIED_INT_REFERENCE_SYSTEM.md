# 🔗 Unified INT Reference System

## Overview
This document describes the unified INT reference system that works across all intelligence sources:
- **EMAIL** - Email intelligence
- **WHATSAPP** - WhatsApp reports
- **PATROL** - Online patrol entries
- **SURVEILLANCE** - Surveillance operations

## System Architecture

### 1. Database Structure
```
CaseProfile (Central INT Registry)
├── int_reference: "INT-001", "INT-002", etc.
├── email_id: Link to Email table
├── whatsapp_id: Link to WhatsAppEntry table
├── patrol_id: Link to OnlinePatrolEntry table
└── surveillance_id: Link to SurveillanceEntry table
```

### 2. INT Reference Assignment

Each source can be assigned to a CaseProfile with an INT reference number.

**Assignment Flow:**
1. **Auto-assign**: System automatically assigns next INT when source is created
2. **Manual assign**: User can search and assign to existing INT
3. **New INT**: User can get next available INT number

### 3. Cross-Source Search

The search function searches across ALL sources:
- Email: alleged_subject_english, alleged_subject_chinese, alleged_nature, subject
- WhatsApp: alleged_person, alleged_type, details
- Online Patrol: alleged_person, alleged_nature, details
- Surveillance: targets, details_of_finding

### 4. UI Components

Each source detail page has:
- **Source ID**: Read-only unique identifier (e.g., EMAIL-123, WHATSAPP-45)
- **Case INT Reference**: Editable field with:
  - 🔍 **Search** button: Find existing INT by keywords
  - ➕ **Next** button: Get next available INT number
  - 💾 **Assign** button: Save the INT assignment

## Implementation

### API Endpoints

#### Get Next Available INT
```
GET /api/int_references/next_available
Response: { "success": true, "next_int_reference": "INT-005", "next_number": 5 }
```

#### Search INT References
```
GET /api/int_references/search?q=keyword
Response: { 
  "success": true, 
  "results": [
    {
      "int_reference": "INT-003",
      "total_sources": 5,
      "source_types": ["EMAIL", "WHATSAPP", "PATROL"],
      "match_reason": "Person: John Doe",
      "date_created": "2025-11-01"
    }
  ]
}
```

#### Update INT Reference
```
POST /whatsapp/<entry_id>/update_int_reference
POST /online_patrol/<entry_id>/update_int_reference
POST /surveillance/<entry_id>/update_int_reference
Data: { "int_reference_number": "INT-003" }
```

## Benefits

1. **Unified Tracking**: Track all sources related to a case under one INT number
2. **Cross-Source Intelligence**: Search finds related intelligence across all sources
3. **Consistency**: Same interface for all intelligence types
4. **Scalability**: Easy to add new source types in the future
5. **Audit Trail**: Track when and how INT assignments are made

## Migration Notes

- No database migration needed (CaseProfile table already has all foreign keys)
- Only frontend templates need updating to add INT reference UI
- Backend routes already support INT assignment for all sources
