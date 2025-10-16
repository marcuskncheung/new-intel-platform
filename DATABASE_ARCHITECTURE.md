# 🏗️ Intelligence Platform Database Architecture

## 📊 Database Schema Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE PLATFORM DATABASE ARCHITECTURE               │
│                          PostgreSQL 15.14 (Production)                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                        🔗 UNIFIED INT REFERENCE SYSTEM                        │
│                              (Central Registry)                               │
└──────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────────┐
                              │   CASE_PROFILE      │
                              │  (INT-### System)   │
                              ├─────────────────────┤
                              │ 🔑 id               │
                              │ 📋 int_reference    │ ← INT-001, INT-002...
                              │ 📊 index_order      │ ← 1, 2, 3...
                              │ 📅 date_of_receipt  │
                              │ 🏷️  source_type     │ ← EMAIL/WHATSAPP/PATROL
                              │                     │
                              │ Foreign Keys:       │
                              │ ├─ email_id         │
                              │ ├─ whatsapp_id      │
                              │ └─ patrol_id        │
                              │                     │
                              │ 📝 case_status      │
                              │ 📝 case_number      │
                              │ 👤 alleged_subject  │
                              │ ⚠️  misconduct_type │
                              └─────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼

        ┌───────────────────┐  ┌──────────────────┐  ┌────────────────────┐
        │      EMAIL        │  │   WHATSAPP_ENTRY │  │ ONLINE_PATROL_ENTRY│
        ├───────────────────┤  ├──────────────────┤  ├────────────────────┤
        │ 🔑 id             │  │ 🔑 id            │  │ 🔑 id              │
        │ 📧 entry_id       │  │ 📱 phone_number  │  │ 🔍 sender          │
        │ 👤 sender         │  │ 👤 complaint_name│  │ 🌐 source          │
        │ 👥 recipients     │  │ 👤 alleged_person│  │ 📅 complaint_time  │
        │ 📝 subject        │  │ 📝 details       │  │ 📝 details         │
        │ 📅 received       │  │ 📅 received_time │  │ ✅ status          │
        │ 📄 body           │  │ ⚠️  alleged_type │  │                    │
        │                   │  │ 📊 source        │  │ 🔗 caseprofile_id  │
        │ 📊 Assessment:    │  │                  │  │                    │
        │ ├─ reliability    │  │ 🔗 caseprofile_id│  │ 📊 reliability     │
        │ ├─ validity       │  │                  │  │ 📊 validity        │
        │ └─ case_opened    │  │ 📊 reliability   │  └────────────────────┘
        │                   │  │ 📊 validity      │           │
        │ 🔗 caseprofile_id │  └──────────────────┘           │
        │                   │           │                     │
        │ 📎 Legacy INT:    │           │                     │
        │ ├─ int_ref_number │           │                     │
        │ └─ int_ref_order  │           │                     │
        └───────────────────┘           │                     │
                │                       │                     │
                │                       ▼                     ▼
                │              ┌──────────────────┐  ┌──────────────┐
                │              │ WHATSAPP_IMAGE   │  │   (No images)│
                │              ├──────────────────┤  └──────────────┘
                │              │ 🔑 id            │
                │              │ 🔗 whatsapp_id   │
                │              │ 📁 filename      │
                │              │ 💾 image_data    │
                │              └──────────────────┘
                │
                ▼
        ┌───────────────────┐
        │   ATTACHMENT      │
        ├───────────────────┤
        │ 🔑 id             │
        │ 🔗 email_id       │
        │ 📁 filename       │
        │ 💾 file_data      │
        └───────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                     👤 ALLEGED PERSON TRACKING SYSTEM                         │
│                        (POI-### System - Separate)                            │
└──────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────────┐
                    │   ALLEGED_PERSON_PROFILE        │
                    │    (POI-### System)             │
                    ├─────────────────────────────────┤
                    │ 🔑 id                           │
                    │ 🏷️  poi_id                      │ ← POI-001, POI-002...
                    │ 👤 name_english                 │
                    │ 👤 name_chinese                 │
                    │ 🔤 name_normalized              │
                    │                                 │
                    │ 💼 Professional Info:           │
                    │ ├─ agent_number                 │
                    │ ├─ license_number               │
                    │ ├─ company                      │
                    │ └─ role                         │
                    │                                 │
                    │ 📊 Statistics:                  │
                    │ ├─ email_count                  │
                    │ ├─ first_mentioned_date         │
                    │ └─ last_mentioned_date          │
                    │                                 │
                    │ ✅ status (ACTIVE/MERGED)       │
                    └─────────────────────────────────┘
                                  │
                                  │ Many-to-Many
                                  ▼
                    ┌─────────────────────────────────┐
                    │ EMAIL_ALLEGED_PERSON_LINK       │
                    ├─────────────────────────────────┤
                    │ 🔑 id                           │
                    │ 🔗 email_id                     │
                    │ 🔗 alleged_person_id            │
                    │ 📊 confidence (AI score)        │
                    │ 👤 created_by                   │
                    └─────────────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────────┐
                    │         EMAIL (link)            │
                    └─────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                      🔍 SURVEILLANCE & OPERATIONS                             │
└──────────────────────────────────────────────────────────────────────────────┘

        ┌────────────────────────┐
        │  SURVEILLANCE_ENTRY    │
        ├────────────────────────┤
        │ 🔑 id                  │
        │ 🔢 operation_number    │
        │ 🏢 operation_type      │ ← Mystery Shopping / Surveillance
        │ 📅 date                │
        │ 📍 venue               │
        │ 📝 details_of_finding  │
        │ 👤 conducted_by        │ ← PI / IA staff
        │ 📊 source_reliability  │
        └────────────────────────┘
                    │
                    │ One-to-Many
                    ▼
        ┌────────────────────────┐
        │       TARGET           │
        ├────────────────────────┤
        │ 🔑 id                  │
        │ 🔗 surveillance_entry_id│
        │ 👤 name                │
        │ 🎫 license_type        │ ← Agent/Broker/N/A
        │ 🔢 license_number      │
        │ 📊 content_validity    │
        └────────────────────────┘

        ┌────────────────────────┐      ┌────────────────────────┐
        │  SURVEILLANCE_PHOTO    │      │ SURVEILLANCE_DOCUMENT  │
        ├────────────────────────┤      ├────────────────────────┤
        │ 🔑 id                  │      │ 🔑 id                  │
        │ 🔗 surveillance_id     │      │ 🔗 surveillance_id     │
        │ 📁 filename            │      │ 📁 filename            │
        │ 💾 image_data          │      │ 📂 filepath            │
        │ 📅 uploaded_at         │      └────────────────────────┘
        └────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                        🔐 SECURITY & AUDIT SYSTEM                             │
└──────────────────────────────────────────────────────────────────────────────┘

        ┌────────────────────────┐              ┌────────────────────────┐
        │        USER            │              │  EMAIL_ANALYSIS_LOCK   │
        ├────────────────────────┤              ├────────────────────────┤
        │ 🔑 id                  │              │ 🔑 email_id            │
        │ 👤 username            │              │ 👤 locked_by           │
        │ 🔒 password (hashed)   │              │ 📅 locked_at           │
        │ 🎭 role (admin/user)   │              │ ⏰ expires_at          │
        │ 📅 created_at          │              └────────────────────────┘
        │ 📅 last_login          │
        │ ✅ is_active           │
        └────────────────────────┘

        ┌─────────────────────────────────────────┐
        │           AUDIT_LOG                     │
        ├─────────────────────────────────────────┤
        │ 🔑 id                                   │
        │ 👤 user_id                              │
        │ 👤 username                             │
        │ 🎬 action                               │
        │ 📦 resource_type                        │
        │ 🆔 resource_id                          │
        │ 🔐 details (encrypted)                  │
        │ 🌐 ip_address                           │
        │ 💻 user_agent                           │
        │ 📅 timestamp                            │
        │ 🔑 session_id                           │
        │ ⚠️  severity (info/warning/critical)    │
        └─────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                          📊 DATA FLOW DIAGRAM                                 │
└──────────────────────────────────────────────────────────────────────────────┘

    📧 Email Import          📱 WhatsApp Entry        🔍 Patrol Entry
         │                          │                       │
         ▼                          ▼                       ▼
    ┌─────────┐              ┌─────────┐             ┌─────────┐
    │  EMAIL  │              │WHATSAPP │             │ PATROL  │
    └─────────┘              └─────────┘             └─────────┘
         │                          │                       │
         └──────────────────────────┼───────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  create_unified_intelligence  │
                    │      _entry()                 │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   generate_next_int_id()      │
                    │   - Chronological ordering    │
                    │   - Auto renumber if needed   │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      CASE_PROFILE             │
                    │    INT-### assigned!          │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  Link back to source record   │
                    │  source.caseprofile_id = id   │
                    └───────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                        🔢 INT REFERENCE NUMBER SYSTEMS                        │
└──────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────┐
    │  NEW UNIFIED SYSTEM (via CaseProfile)                           │
    ├─────────────────────────────────────────────────────────────────┤
    │  INT-001 → Email (email_id=42)                                  │
    │  INT-002 → WhatsApp (whatsapp_id=1)                             │
    │  INT-003 → Patrol (patrol_id=1)                                 │
    │  INT-004 → Email (email_id=43)                                  │
    │  INT-005 → WhatsApp (whatsapp_id=2)                             │
    │  ...                                                             │
    │                                                                  │
    │  ✅ Unified tracking across all intelligence sources            │
    │  ✅ Chronological based on receipt date                         │
    │  ✅ Auto-renumbers when inserting older items                   │
    └─────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────┐
    │  OLD SYSTEM (direct in Email table) - DEPRECATED                │
    ├─────────────────────────────────────────────────────────────────┤
    │  Email.int_reference_number = "INT-139"                         │
    │  Email.int_reference_order = 139                                │
    │                                                                  │
    │  ⚠️  Being migrated to CaseProfile system                       │
    │  ⚠️  182 emails need migration                                  │
    └─────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────┐
    │  ALLEGED PERSON SYSTEM (separate POI tracking)                  │
    ├─────────────────────────────────────────────────────────────────┤
    │  POI-001 → Person Profile (John Doe)                            │
    │  POI-002 → Person Profile (張三)                                 │
    │  POI-003 → Person Profile (Mary Smith)                          │
    │  ...                                                             │
    │                                                                  │
    │  ✅ Tracks persons across multiple intelligence items           │
    │  ✅ Links to emails via EMAIL_ALLEGED_PERSON_LINK               │
    └─────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                          🔐 ENCRYPTION & SECURITY                             │
└──────────────────────────────────────────────────────────────────────────────┘

    Encrypted Fields (using cryptography module):
    
    📧 EMAIL:
       ├─ alleged_subject       (PII - encrypted)
       ├─ alleged_nature        (sensitive content)
       ├─ allegation_summary    (detailed allegations)
       ├─ license_number        (sensitive identifier)
       ├─ reviewer_comment      (assessment details)
       └─ body (if contains sensitive keywords)
    
    🔐 AUDIT_LOG:
       └─ details (all audit details encrypted)
    
    Encryption Flags:
       ├─ is_body_encrypted
       ├─ is_subject_encrypted
       └─ is_sensitive_encrypted


┌──────────────────────────────────────────────────────────────────────────────┐
│                         📈 CURRENT DATABASE STATUS                            │
└──────────────────────────────────────────────────────────────────────────────┘

    📊 Statistics (as of latest diagnostic):
    
    ┌────────────────────────────────────┬──────────┬──────────────┐
    │ Table                              │ Records  │ Status       │
    ├────────────────────────────────────┼──────────┼──────────────┤
    │ EMAIL                              │    182   │ ⚠️ Migration │
    │ CASE_PROFILE                       │      3   │ ✅ Active    │
    │ WHATSAPP_ENTRY                     │      2   │ ✅ Linked    │
    │ ONLINE_PATROL_ENTRY                │      1   │ ✅ Linked    │
    │ ALLEGED_PERSON_PROFILE             │     ?    │ ✅ Active    │
    │ EMAIL_ALLEGED_PERSON_LINK          │     ?    │ ✅ Active    │
    │ USER                               │     ?    │ ✅ Active    │
    │ AUDIT_LOG                          │     ?    │ ✅ Active    │
    └────────────────────────────────────┴──────────┴──────────────┘
    
    ⚠️  PENDING MIGRATION:
       • 182 emails have old INT system (int_reference_number)
       • 0 emails linked to CaseProfile (caseprofile_id)
       • Need to run: migrate_old_int_to_caseprofile.py


┌──────────────────────────────────────────────────────────────────────────────┐
│                            🔧 KEY CONSTRAINTS                                 │
└──────────────────────────────────────────────────────────────────────────────┘

    UNIQUE Constraints:
    ├─ case_profile.int_reference         (e.g., INT-001)
    ├─ case_profile.index_order           (e.g., 1, 2, 3...)
    ├─ case_profile.email_id              (one-to-one)
    ├─ case_profile.whatsapp_id           (one-to-one)
    ├─ case_profile.patrol_id             (one-to-one)
    ├─ alleged_person_profile.poi_id      (e.g., POI-001)
    ├─ email.entry_id                     (unique identifier)
    └─ user.username                      (unique login)
    
    FOREIGN Keys:
    ├─ email.caseprofile_id → case_profile.id
    ├─ whatsapp_entry.caseprofile_id → case_profile.id
    ├─ online_patrol_entry.caseprofile_id → case_profile.id
    ├─ case_profile.email_id → email.id
    ├─ case_profile.whatsapp_id → whatsapp_entry.id
    ├─ case_profile.patrol_id → online_patrol_entry.id
    ├─ attachment.email_id → email.id
    ├─ whatsapp_image.whatsapp_id → whatsapp_entry.id
    ├─ email_alleged_person_link.email_id → email.id
    ├─ email_alleged_person_link.alleged_person_id → alleged_person_profile.id
    └─ audit_log.user_id → user.id


┌──────────────────────────────────────────────────────────────────────────────┐
│                         🎯 DESIGN PATTERNS & FEATURES                         │
└──────────────────────────────────────────────────────────────────────────────┘

    ✅ Unified Intelligence Reference System
       • Central CaseProfile table for all intelligence sources
       • Chronological INT-### numbering with auto-renumbering
       • Single source of truth for intelligence tracking
    
    ✅ Bidirectional Relationships
       • Source → CaseProfile (via caseprofile_id)
       • CaseProfile → Source (via email_id/whatsapp_id/patrol_id)
    
    ✅ Property-Based Access
       • email.int_reference → property → case_profile.int_reference
       • Transparent access to unified INT numbers
    
    ✅ Security & Audit
       • Field-level encryption for sensitive data
       • Comprehensive audit trail with encrypted details
       • Race condition protection (EmailAnalysisLock)
    
    ✅ Person Tracking
       • Separate POI-### system for alleged persons
       • Many-to-many links to emails
       • AI confidence scoring
    
    ✅ Case Management
       • Human-assigned case numbers (C2025-001)
       • Related email grouping
       • Case status tracking
