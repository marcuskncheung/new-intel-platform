#!/usr/bin/env python3
"""
Migrate old emails with int_reference_number to new CaseProfile system

This script:
1. Finds emails with int_reference_number but no caseprofile_id
2. Creates CaseProfile entries for each email
3. Links emails to their CaseProfile
4. Preserves the original INT numbers and order
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app1_production import app, db, Email, CaseProfile
from datetime import datetime
from sqlalchemy import text

def migrate_emails():
    """Migrate old emails to CaseProfile system"""
    with app.app_context():
        print("=" * 80)
        print("🔄 MIGRATING EMAILS TO CASEPROFILE SYSTEM")
        print("=" * 80)
        
        # Find emails that need migration
        emails_to_migrate = Email.query.filter(
            Email.int_reference_number != None,
            Email.caseprofile_id == None
        ).order_by(Email.int_reference_order.asc()).all()
        
        total = len(emails_to_migrate)
        
        if total == 0:
            print("\n✅ No emails need migration!")
            print("   All emails are already linked to CaseProfile")
            return
        
        print(f"\n📊 Found {total} emails to migrate")
        print("-" * 80)
        
        # Confirm before proceeding
        print("\n⚠️  This will create CaseProfile entries for all emails")
        print("   and link them to preserve INT reference numbers")
        
        response = input("\nProceed with migration? (yes/no): ").strip().lower()
        if response != 'yes':
            print("❌ Migration cancelled")
            return
        
        print("\n🔄 Starting migration...")
        print("-" * 80)
        
        migrated = 0
        errors = 0
        
        for i, email in enumerate(emails_to_migrate, 1):
            try:
                # Parse received date
                received_date = None
                if email.received:
                    try:
                        # Try parsing the date string
                        received_date = datetime.strptime(email.received, '%Y-%m-%d %H:%M:%S')
                    except:
                        try:
                            received_date = datetime.strptime(email.received, '%Y-%m-%d %H:%M')
                        except:
                            # Use current time as fallback
                            received_date = datetime.now()
                else:
                    received_date = datetime.now()
                
                # Extract INT number (e.g., "INT-139" -> 139)
                int_number = email.int_reference_number
                int_order = email.int_reference_order
                
                if not int_order:
                    # Extract order from INT reference
                    try:
                        int_order = int(int_number.split('-')[1])
                    except:
                        int_order = i
                
                # Create CaseProfile entry
                case_profile = CaseProfile(
                    int_reference=int_number,
                    index_order=int_order,
                    date_of_receipt=received_date,
                    source_type='EMAIL',
                    email_id=email.id,
                    source=f'Email from {email.sender or "Unknown"}',
                    case_status='Pending',
                    alleged_subject_en=email.alleged_subject_english,
                    alleged_subject_cn=email.alleged_subject_chinese,
                    alleged_misconduct_type=email.alleged_nature,
                    description_of_incident=email.allegation_summary,
                    created_by='MIGRATION_SCRIPT',
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                db.session.add(case_profile)
                db.session.flush()  # Get case_profile.id
                
                # Link email to CaseProfile
                email.caseprofile_id = case_profile.id
                
                db.session.commit()
                
                migrated += 1
                
                if i % 10 == 0 or i == total:
                    print(f"  Progress: {i}/{total} ({migrated} migrated, {errors} errors)")
                
            except Exception as e:
                errors += 1
                print(f"\n  ❌ Error migrating email ID {email.id} ({int_number}): {e}")
                db.session.rollback()
                continue
        
        print("\n" + "=" * 80)
        print("📊 MIGRATION RESULTS:")
        print("=" * 80)
        print(f"  Total emails processed: {total}")
        print(f"  ✅ Successfully migrated: {migrated}")
        print(f"  ❌ Errors: {errors}")
        
        if migrated > 0:
            print("\n✅ Migration completed successfully!")
            print("\n📝 Next steps:")
            print("   1. Verify migration: python3 diagnose_int_references.py")
            print("   2. Restart application: docker-compose restart web")
            print("   3. Check /int_source page to verify INT references display")
        
        # Verify migration
        print("\n🔍 Verifying migration...")
        still_unmigrated = Email.query.filter(
            Email.int_reference_number != None,
            Email.caseprofile_id == None
        ).count()
        
        newly_linked = Email.query.filter(
            Email.caseprofile_id != None
        ).count()
        
        total_caseprofiles = CaseProfile.query.count()
        
        print(f"  Emails still unmigrated: {still_unmigrated}")
        print(f"  Emails now linked to CaseProfile: {newly_linked}")
        print(f"  Total CaseProfile entries: {total_caseprofiles}")
        
        if still_unmigrated == 0:
            print("\n✅ ALL EMAILS SUCCESSFULLY MIGRATED!")
        else:
            print(f"\n⚠️  {still_unmigrated} emails still need migration")

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("EMAIL TO CASEPROFILE MIGRATION SCRIPT")
    print("=" * 80 + "\n")
    migrate_emails()
    print("\n" + "=" * 80)
    print("✅ SCRIPT COMPLETE")
    print("=" * 80 + "\n")
