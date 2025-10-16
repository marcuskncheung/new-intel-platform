#!/usr/bin/env python3
"""
🔗 Unified INT-### Reference System Migration Script

This script migrates the database to support the unified INT reference system
that indexes ALL intelligence sources (Email, WhatsApp, Online Patrol).

⚠️ BACKUP YOUR DATABASE BEFORE RUNNING THIS SCRIPT!

Usage:
    python3 migrate_unified_int_system.py

What it does:
    1. Adds new columns to CaseProfile table
    2. Adds caseprofile_id columns to Email, WhatsAppEntry, OnlinePatrolEntry
    3. Migrates existing Email INT references to CaseProfile
    4. Creates CaseProfile entries for WhatsApp and Patrol records
    5. Links all source records to their CaseProfile
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app1_production import app, db, Email, WhatsAppEntry, OnlinePatrolEntry, CaseProfile
from app1_production import create_unified_intelligence_entry, get_hk_time
from sqlalchemy import inspect, text
from datetime import datetime

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def add_column_if_not_exists(table_name, column_name, column_type):
    """Add column to table if it doesn't exist"""
    if not check_column_exists(table_name, column_name):
        try:
            with db.engine.connect() as conn:
                conn.execute(text(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}'))
                conn.commit()
            print(f"  ✅ Added column '{column_name}' to '{table_name}'")
            return True
        except Exception as e:
            print(f"  ⚠️  Error adding column '{column_name}' to '{table_name}': {e}")
            return False
    else:
        print(f"  ℹ️  Column '{column_name}' already exists in '{table_name}'")
        return False

def migrate_to_unified_int_system():
    """
    Main migration function for unified INT system
    """
    print("\n" + "="*70)
    print("🔗 UNIFIED INT-### REFERENCE SYSTEM MIGRATION")
    print("="*70)
    
    with app.app_context():
        try:
            # Step 1: Update CaseProfile table
            print("\n📋 STEP 1: Updating CaseProfile table...")
            add_column_if_not_exists('case_profile', 'index_order', 'INTEGER')
            add_column_if_not_exists('case_profile', 'email_id', 'INTEGER')
            add_column_if_not_exists('case_profile', 'whatsapp_id', 'INTEGER')
            add_column_if_not_exists('case_profile', 'patrol_id', 'INTEGER')
            add_column_if_not_exists('case_profile', 'created_at', 'DATETIME')
            add_column_if_not_exists('case_profile', 'updated_at', 'DATETIME')
            add_column_if_not_exists('case_profile', 'created_by', 'VARCHAR(100)')
            add_column_if_not_exists('case_profile', 'similarity_checked', 'BOOLEAN DEFAULT 0')
            add_column_if_not_exists('case_profile', 'duplicate_of_id', 'INTEGER')
            
            # Convert date_of_receipt from VARCHAR to DATETIME (if needed)
            if check_column_exists('case_profile', 'date_of_receipt'):
                print("  ℹ️  date_of_receipt column exists (may need type conversion)")
            
            # Step 2: Add caseprofile_id to source tables
            print("\n📧 STEP 2: Updating Email table...")
            add_column_if_not_exists('email', 'caseprofile_id', 'INTEGER')
            
            print("\n💬 STEP 3: Updating WhatsAppEntry table...")
            add_column_if_not_exists('whats_app_entry', 'caseprofile_id', 'INTEGER')
            
            print("\n🌐 STEP 4: Updating OnlinePatrolEntry table...")
            add_column_if_not_exists('online_patrol_entry', 'caseprofile_id', 'INTEGER')
            
            # Step 3: Migrate existing Email INT references
            print("\n📨 STEP 5: Migrating existing Email INT references...")
            emails_with_int = Email.query.filter(
                Email.int_reference_number.isnot(None)
            ).all()
            
            migrated_emails = 0
            for email in emails_with_int:
                # Check if already migrated
                if email.caseprofile_id:
                    continue
                
                try:
                    # Parse received date
                    if isinstance(email.received, str):
                        try:
                            date_of_receipt = datetime.strptime(email.received[:19], '%Y-%m-%d %H:%M:%S')
                        except:
                            date_of_receipt = get_hk_time()
                    else:
                        date_of_receipt = email.received or get_hk_time()
                    
                    # Create CaseProfile for each email
                    case = CaseProfile(
                        index=email.int_reference_number,
                        index_order=email.int_reference_order or 0,
                        date_of_receipt=date_of_receipt,
                        source_type="EMAIL",
                        email_id=email.id,
                        created_by="MIGRATION",
                        created_at=get_hk_time(),
                        updated_at=get_hk_time(),
                        alleged_subject_en=email.alleged_subject_english,
                        alleged_subject_cn=email.alleged_subject_chinese,
                        description_of_incident=email.allegation_summary
                    )
                    db.session.add(case)
                    db.session.flush()
                    
                    # Link email back
                    email.caseprofile_id = case.id
                    migrated_emails += 1
                    
                    if migrated_emails % 10 == 0:
                        print(f"  ⏳ Migrated {migrated_emails} emails...")
                        
                except Exception as e:
                    print(f"  ⚠️  Error migrating email {email.id}: {e}")
                    continue
            
            db.session.commit()
            print(f"  ✅ Migrated {migrated_emails} Email INT references to CaseProfile")
            
            # Step 4: Create INT references for WhatsApp entries
            print("\n💬 STEP 6: Creating INT references for WhatsApp entries...")
            whatsapp_entries = WhatsAppEntry.query.filter(
                WhatsAppEntry.caseprofile_id.is_(None)
            ).all()
            
            migrated_whatsapp = 0
            for entry in whatsapp_entries:
                try:
                    case = create_unified_intelligence_entry(
                        source_record=entry,
                        source_type="WHATSAPP",
                        created_by="MIGRATION"
                    )
                    if case:
                        migrated_whatsapp += 1
                        if migrated_whatsapp % 10 == 0:
                            print(f"  ⏳ Created {migrated_whatsapp} WhatsApp INT references...")
                except Exception as e:
                    print(f"  ⚠️  Error creating INT for WhatsApp entry {entry.id}: {e}")
                    continue
            
            db.session.commit()
            print(f"  ✅ Created {migrated_whatsapp} WhatsApp INT references")
            
            # Step 5: Create INT references for Online Patrol entries
            print("\n🌐 STEP 7: Creating INT references for Online Patrol entries...")
            patrol_entries = OnlinePatrolEntry.query.filter(
                OnlinePatrolEntry.caseprofile_id.is_(None)
            ).all()
            
            migrated_patrol = 0
            for entry in patrol_entries:
                try:
                    case = create_unified_intelligence_entry(
                        source_record=entry,
                        source_type="PATROL",
                        created_by="MIGRATION"
                    )
                    if case:
                        migrated_patrol += 1
                        if migrated_patrol % 10 == 0:
                            print(f"  ⏳ Created {migrated_patrol} Patrol INT references...")
                except Exception as e:
                    print(f"  ⚠️  Error creating INT for Patrol entry {entry.id}: {e}")
                    continue
            
            db.session.commit()
            print(f"  ✅ Created {migrated_patrol} Online Patrol INT references")
            
            # Step 6: Summary
            print("\n" + "="*70)
            print("✅ MIGRATION COMPLETE!")
            print("="*70)
            print(f"\n📊 Summary:")
            print(f"  • Email INT references migrated: {migrated_emails}")
            print(f"  • WhatsApp INT references created: {migrated_whatsapp}")
            print(f"  • Online Patrol INT references created: {migrated_patrol}")
            print(f"  • Total unified INT references: {migrated_emails + migrated_whatsapp + migrated_patrol}")
            
            # Verify
            total_cases = CaseProfile.query.count()
            email_cases = CaseProfile.query.filter_by(source_type='EMAIL').count()
            whatsapp_cases = CaseProfile.query.filter_by(source_type='WHATSAPP').count()
            patrol_cases = CaseProfile.query.filter_by(source_type='PATROL').count()
            
            print(f"\n🔍 Verification:")
            print(f"  • Total CaseProfile records: {total_cases}")
            print(f"  • EMAIL source type: {email_cases}")
            print(f"  • WHATSAPP source type: {whatsapp_cases}")
            print(f"  • PATROL source type: {patrol_cases}")
            
            if total_cases == email_cases + whatsapp_cases + patrol_cases:
                print(f"\n  ✅ All source records properly categorized!")
            else:
                print(f"\n  ⚠️  Mismatch detected - some records may need manual review")
            
            print("\n" + "="*70)
            print("🎉 Unified INT-### Reference System is now active!")
            print("="*70)
            print("\nNext steps:")
            print("  1. Test the system by creating new Email/WhatsApp/Patrol entries")
            print("  2. Verify INT references appear correctly in the UI")
            print("  3. Check cross-source deduplication works")
            print("  4. Update dashboard queries to use CaseProfile counts")
            print()
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ MIGRATION FAILED: {e}")
            import traceback
            traceback.print_exc()
            print("\n⚠️  Database rolled back. Please review errors and try again.")
            sys.exit(1)

if __name__ == "__main__":
    print("\n⚠️  WARNING: This script will modify your database schema.")
    print("   Make sure you have a backup before proceeding!")
    
    response = input("\n   Continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        migrate_to_unified_int_system()
    else:
        print("\n❌ Migration cancelled.")
        sys.exit(0)
