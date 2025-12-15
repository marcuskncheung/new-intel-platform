# Intelligence Platform Database Architecture

## Overview

The database has **19 tables** organized into clear categories:

---

## 🔵 CORE TABLES (Main Data)

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `email` | Email intelligence entries | id, subject, sender, alleged_subject_english, alleged_subject_chinese, alleged_nature |
| `whatsapp_entry` | WhatsApp message intel | id, contact_name, message_content, alleged_subject_english, alleged_subject_chinese |
| `online_patrol_entry` | Online discoveries | id, source, url, alleged_subject_english, alleged_subject_chinese, threats |
| `surveillance_entry` | Surveillance operations | id, operation_number, venue, targets |
| `received_by_hand` | Hand-delivered intel | id, source_name, alleged_subject_english, alleged_subject_chinese |

---

## 🟢 CASE MANAGEMENT

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `case_profile` | **Unified INT tracking** - Links all sources | id, int_reference, source_type, email_id, whatsapp_id, patrol_id, received_by_hand_id |

This is the **central table** that ties everything together with INT-XXXX-XXXX references.

**⚠️ IMPORTANT:** `case_profile` only stores **references**. All alleged person data is in the source tables.
Use the relationships (email, whatsapp, patrol, received_by_hand) to get actual data.

---

## 🟡 RELATIONSHIP TABLES (Many-to-Many)

| Table | Purpose |
|-------|---------|
| `email_alleged_subject` | Links emails → alleged persons |
| `whatsapp_alleged_subject` | Links WhatsApp → alleged persons |
| `online_patrol_alleged_subject` | Links Online Patrol → alleged persons |
| `received_by_hand_alleged_subject` | Links Received by Hand → alleged persons |
| `target` | Links surveillance → target persons |

---

## 🟠 ATTACHMENT/MEDIA TABLES

| Table | Purpose |
|-------|---------|
| `attachment` | Email attachments |
| `whatsapp_image` | WhatsApp images |
| `online_patrol_photo` | Online Patrol screenshots |
| `surveillance_photo` | Surveillance photos |
| `surveillance_document` | Surveillance documents |
| `received_by_hand_document` | Hand-delivered documents |

---

## ⚪ SYSTEM TABLES

| Table | Purpose |
|-------|---------|
| `audit_log` | Activity logging |
| `email_analysis_lock` | Prevents duplicate processing |

---

## Database Relationship Diagram

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                     CASE_PROFILE                            │
                    │  (Unified INT Reference - Links ALL Intelligence Sources)   │
                    │  int_reference: INT-2024-0001, source_type, source_id       │
                    └─────────────────────────────────────────────────────────────┘
                                              │
           ┌──────────────┬──────────────┬────┴────┬──────────────┬──────────────┐
           ▼              ▼              ▼         ▼              ▼              
    ┌──────────┐   ┌──────────────┐  ┌────────┐  ┌────────────┐  ┌─────────────┐
    │  EMAIL   │   │ WHATSAPP_    │  │ONLINE_ │  │SURVEILLANCE│  │RECEIVED_BY_ │
    │          │   │ ENTRY        │  │PATROL_ │  │_ENTRY      │  │HAND         │
    │          │   │              │  │ENTRY   │  │            │  │             │
    └────┬─────┘   └──────┬───────┘  └───┬────┘  └─────┬──────┘  └──────┬──────┘
         │                │              │             │                │
         ▼                ▼              ▼             ▼                ▼
    ┌──────────┐   ┌──────────────┐  ┌────────┐  ┌──────────┐   ┌─────────────┐
    │ATTACHMENT│   │WHATSAPP_     │  │ONLINE_ │  │SURVEILL- │   │RECEIVED_BY_ │
    │          │   │IMAGE         │  │PATROL_ │  │ANCE_PHOTO│   │HAND_DOCUMENT│
    └──────────┘   └──────────────┘  │PHOTO   │  │SURVEILL- │   └─────────────┘
                                     └────────┘  │ANCE_DOC  │
         │                │              │       └──────────┘         │
         ▼                ▼              ▼             │              ▼
    ┌──────────┐   ┌──────────────┐  ┌────────┐       ▼        ┌─────────────┐
    │EMAIL_    │   │WHATSAPP_     │  │ONLINE_ │  ┌────────┐   │RECEIVED_BY_ │
    │ALLEGED_  │   │ALLEGED_      │  │PATROL_ │  │TARGET  │   │HAND_ALLEGED_│
    │SUBJECT   │   │SUBJECT       │  │ALLEGED_│  └────────┘   │SUBJECT      │
    └──────────┘   └──────────────┘  │SUBJECT │               └─────────────┘
                                     └────────┘
```

---

## Quick Reference

### To find intel on a person:
1. Check `case_profile` by `alleged_person`
2. Follow `source_type` + `source_id` to the source table

### To see all INT entries:
1. Query `case_profile` - it has ALL INT references

### Source Types in case_profile:
- `email` → links to `email.id`
- `whatsapp` → links to `whatsapp_entry.id`  
- `patrol` → links to `online_patrol_entry.id`
- `surveillance` → links to `surveillance_entry.id`
- `received_by_hand` → links to `received_by_hand.id`

---

## Tables That Can Be Ignored (Internal Use)

- `email_analysis_lock` - just prevents duplicate AI processing
- `audit_log` - just activity logs

---

## Summary

**5 Main Source Tables** (where intel comes from):
- email, whatsapp_entry, online_patrol_entry, surveillance_entry, received_by_hand

**1 Central Tracking Table**:
- case_profile (has all INT-XXXX-XXXX references)

**6 Media/Attachment Tables** (files linked to sources)

**5 Alleged Subject Tables** (person links)

**2 System Tables** (logging)

= **19 Total Tables**
