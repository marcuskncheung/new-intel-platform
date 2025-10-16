#!/usr/bin/env python3
"""
Fix the 3 remaining emails with conflicting INT numbers
Renumbers them to the next available INT numbers
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app1_production import app, db, Email, CaseProfile
from datetime import datetime

def fix_remaining_emails():
    """Fix the 3 emails with conflicting INT numbers"""
    with app.app_context():
        print("=" * 80)
        print("🔧 FIXING REMAINING 3 EMAILS WITH CONFLICTING INT NUMBERS")
        print("=" * 80)
        
        # Find emails still not migrated
        unmigrated = Email.query.filter(
            Email.int_reference_number != None,
            Email.caseprofile_id == None
        ).all()
        
        if not unmigrated:
            print("\n✅ All emails are already migrated!")
            return
        
        print(f"\n📊 Found {len(unmigrated)} emails to fix:")
        for email in unmigrated:
            print(f"  • Email ID {email.id}: {email.int_reference_number} - {email.subject[:50]}...")
        
        # Find the highest existing INT number
        max_case_profile = CaseProfile.query.order_by(
            CaseProfile.index_order.desc()
        ).first()
        
        next_order = max_case_profile.index_order + 1 if max_case_profile else 1
        
        print(f"\n📈 Next available INT number: INT-{next_order:03d}")
        print("\n⚠️  This will renumber these 3 emails to avoid conflicts")
        
        response = input("\nProceed with renumbering? (yes/no): ").strip().lower()
        if response != 'yes':
            print("❌ Cancelled")
            return
        
        print("\n🔄 Renumbering emails...")
        
        fixed = 0
        for email in unmigrated:
            try:
                # Parse received date
                received_date = None
                if email.received:
                    try:
                        received_date = datetime.strptime(email.received, '%Y-%m-%d %H:%M:%S')
                    except:
                        try:
                            received_date = datetime.strptime(email.received, '%Y-%m-%d %H:%M')
                        except:
                            received_date = datetime.now()
                else:
                    received_date = datetime.now()
                
                # Assign new INT number
                new_int_ref = f"INT-{next_order:03d}"
                old_int_ref = email.int_reference_number
                
                # Create CaseProfile
                case_profile = CaseProfile(
                    int_reference=new_int_ref,
                    index_order=next_order,
                    date_of_receipt=received_date,
                    source_type='EMAIL',
                    email_id=email.id,
                    source=f'Email from {email.sender or "Unknown"}',
                    case_status='Pending',
                    alleged_subject_en=email.alleged_subject_english,
                    alleged_subject_cn=email.alleged_subject_chinese,
                    alleged_misconduct_type=email.alleged_nature,
                    description_of_incident=email.allegation_summary,
                    created_by='RENUMBER_SCRIPT',
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                db.session.add(case_profile)
                db.session.flush()
                
                # Link email to CaseProfile
                email.caseprofile_id = case_profile.id
                
                # Update email's INT number to new one
                email.int_reference_number = new_int_ref
                email.int_reference_order = next_order
                
                db.session.commit()
                
                print(f"  ✅ Email {email.id}: {old_int_ref} → {new_int_ref}")
                
                next_order += 1
                fixed += 1
                
            except Exception as e:
                print(f"  ❌ Error fixing email {email.id}: {e}")
                db.session.rollback()
        
        print("\n" + "=" * 80)
        print(f"✅ Fixed {fixed} emails!")
        print("=" * 80)
        
        # Verify
        print("\n🔍 Verifying...")
        still_unmigrated = Email.query.filter(
            Email.int_reference_number != None,
            Email.caseprofile_id == None
        ).count()
        
        total_linked = Email.query.filter(
            Email.caseprofile_id != None
        ).count()
        
        total_caseprofiles = CaseProfile.query.count()
        
        print(f"  Emails still unmigrated: {still_unmigrated}")
        print(f"  Emails linked to CaseProfile: {total_linked}")
        print(f"  Total CaseProfile entries: {total_caseprofiles}")
        
        if still_unmigrated == 0:
            print("\n🎉 ALL EMAILS SUCCESSFULLY MIGRATED!")
            print("\n📝 Next steps:")
            print("   1. Restart application: docker-compose restart web")
            print("   2. Check /int_source page")
            print("   3. Verify INT references display correctly")
        else:
            print(f"\n⚠️  {still_unmigrated} emails still need attention")

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("FIX REMAINING EMAILS WITH CONFLICTING INT NUMBERS")
    print("=" * 80 + "\n")
    fix_remaining_emails()
    print("\n" + "=" * 80)
    print("✅ COMPLETE")
    print("=" * 80 + "\n")
