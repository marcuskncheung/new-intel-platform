#!/usr/bin/env python3
"""
Diagnose INT reference system issues
Shows which emails have INT numbers but aren't linked to CaseProfile
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app1_production import app, db, Email, CaseProfile, WhatsAppEntry, OnlinePatrolEntry

def diagnose():
    """Check INT reference system status"""
    with app.app_context():
        print("=" * 80)
        print("🔍 DIAGNOSING INT REFERENCE SYSTEM")
        print("=" * 80)
        
        # 1. Check Email table
        print("\n📧 EMAIL TABLE ANALYSIS:")
        print("-" * 80)
        
        total_emails = Email.query.count()
        emails_with_old_int = Email.query.filter(Email.int_reference_number != None).count()
        emails_with_caseprofile = Email.query.filter(Email.caseprofile_id != None).count()
        emails_with_both = Email.query.filter(
            Email.int_reference_number != None,
            Email.caseprofile_id != None
        ).count()
        emails_with_old_only = Email.query.filter(
            Email.int_reference_number != None,
            Email.caseprofile_id == None
        ).count()
        
        print(f"  Total Emails: {total_emails}")
        print(f"  ├─ With OLD int_reference_number: {emails_with_old_int}")
        print(f"  ├─ With NEW caseprofile_id link: {emails_with_caseprofile}")
        print(f"  ├─ With BOTH (migrated): {emails_with_both}")
        print(f"  └─ With OLD ONLY (needs migration): {emails_with_old_only}")
        
        # 2. Check CaseProfile table
        print("\n🔗 CASEPROFILE TABLE ANALYSIS:")
        print("-" * 80)
        
        total_profiles = CaseProfile.query.count()
        profiles_email = CaseProfile.query.filter(CaseProfile.email_id != None).count()
        profiles_whatsapp = CaseProfile.query.filter(CaseProfile.whatsapp_id != None).count()
        profiles_patrol = CaseProfile.query.filter(CaseProfile.patrol_id != None).count()
        
        print(f"  Total CaseProfiles: {total_profiles}")
        print(f"  ├─ Linked to Email: {profiles_email}")
        print(f"  ├─ Linked to WhatsApp: {profiles_whatsapp}")
        print(f"  └─ Linked to Patrol: {profiles_patrol}")
        
        # 3. Check WhatsApp table
        print("\n📱 WHATSAPP TABLE ANALYSIS:")
        print("-" * 80)
        
        total_whatsapp = WhatsAppEntry.query.count()
        whatsapp_with_caseprofile = WhatsAppEntry.query.filter(
            WhatsAppEntry.caseprofile_id != None
        ).count()
        
        print(f"  Total WhatsApp Entries: {total_whatsapp}")
        print(f"  ├─ With caseprofile_id link: {whatsapp_with_caseprofile}")
        print(f"  └─ Without link (orphaned): {total_whatsapp - whatsapp_with_caseprofile}")
        
        # 4. Check Online Patrol table
        print("\n🔍 ONLINE PATROL TABLE ANALYSIS:")
        print("-" * 80)
        
        total_patrol = OnlinePatrolEntry.query.count()
        patrol_with_caseprofile = OnlinePatrolEntry.query.filter(
            OnlinePatrolEntry.caseprofile_id != None
        ).count()
        
        print(f"  Total Patrol Entries: {total_patrol}")
        print(f"  ├─ With caseprofile_id link: {patrol_with_caseprofile}")
        print(f"  └─ Without link (orphaned): {total_patrol - patrol_with_caseprofile}")
        
        # 5. Show examples of problematic emails
        if emails_with_old_only > 0:
            print("\n⚠️  EMAILS WITH OLD INT SYSTEM (need migration):")
            print("-" * 80)
            
            problem_emails = Email.query.filter(
                Email.int_reference_number != None,
                Email.caseprofile_id == None
            ).limit(5).all()
            
            for email in problem_emails:
                print(f"  ID: {email.id:4d} | INT: {email.int_reference_number:8s} | "
                      f"Subject: {(email.subject or 'No subject')[:40]}...")
        
        # 6. Check for orphaned CaseProfiles
        print("\n🔍 ORPHANED CASEPROFILES (no source link):")
        print("-" * 80)
        
        orphaned = CaseProfile.query.filter(
            CaseProfile.email_id == None,
            CaseProfile.whatsapp_id == None,
            CaseProfile.patrol_id == None
        ).count()
        
        print(f"  Orphaned CaseProfiles: {orphaned}")
        
        if orphaned > 0:
            orphaned_list = CaseProfile.query.filter(
                CaseProfile.email_id == None,
                CaseProfile.whatsapp_id == None,
                CaseProfile.patrol_id == None
            ).limit(5).all()
            
            for cp in orphaned_list:
                print(f"  ID: {cp.id:4d} | INT: {cp.int_reference:8s} | "
                      f"Type: {cp.source_type} | Date: {cp.date_of_receipt}")
        
        # 7. Summary and recommendations
        print("\n" + "=" * 80)
        print("📊 SUMMARY:")
        print("=" * 80)
        
        if emails_with_old_only > 0:
            print(f"\n⚠️  ISSUE FOUND: {emails_with_old_only} emails use OLD INT system")
            print("   These emails have int_reference_number but no caseprofile_id")
            print("\n💡 SOLUTION: Run migration script to create CaseProfile entries")
            print("   Script: python3 migrate_old_int_to_caseprofile.py")
        
        if total_whatsapp > whatsapp_with_caseprofile:
            print(f"\n⚠️  ISSUE FOUND: {total_whatsapp - whatsapp_with_caseprofile} WhatsApp entries not linked")
            print("   These entries don't have CaseProfile links")
            print("\n💡 SOLUTION: Check add_whatsapp() route - should auto-create CaseProfile")
        
        if total_patrol > patrol_with_caseprofile:
            print(f"\n⚠️  ISSUE FOUND: {total_patrol - patrol_with_caseprofile} Patrol entries not linked")
            print("   These entries don't have CaseProfile links")
            print("\n💡 SOLUTION: Check add_online_patrol() route - should auto-create CaseProfile")
        
        if orphaned > 0:
            print(f"\n⚠️  ISSUE FOUND: {orphaned} orphaned CaseProfile entries")
            print("   These have no source (email/whatsapp/patrol) linked")
            print("\n💡 SOLUTION: These may be safe to delete or need manual review")
        
        if (emails_with_old_only == 0 and 
            total_whatsapp == whatsapp_with_caseprofile and 
            total_patrol == patrol_with_caseprofile and 
            orphaned == 0):
            print("\n✅ ALL GOOD! INT reference system is working correctly")
            print("   All sources are properly linked to CaseProfile")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    diagnose()
