#!/usr/bin/env python3
"""
Check database status - verify WhatsApp/Patrol entries and CaseProfile links
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app1_production import app, db, WhatsAppEntry, OnlinePatrolEntry, CaseProfile
from tabulate import tabulate

def check_database_status():
    """Check what's in the database"""
    with app.app_context():
        print("=" * 80)
        print("📊 DATABASE STATUS CHECK")
        print("=" * 80)
        
        # Check WhatsApp entries
        whatsapp_entries = WhatsAppEntry.query.all()
        print(f"\n📱 WhatsApp Entries: {len(whatsapp_entries)} total")
        
        if whatsapp_entries:
            whatsapp_data = []
            for w in whatsapp_entries:
                whatsapp_data.append([
                    w.id,
                    w.complaint_name or "N/A",
                    w.phone_number or "N/A",
                    w.received_time.strftime("%Y-%m-%d %H:%M") if w.received_time else "N/A",
                    w.caseprofile_id or "❌ NOT LINKED",
                    w.int_reference or "N/A"
                ])
            
            print(tabulate(
                whatsapp_data,
                headers=["ID", "Complaint Name", "Phone", "Received Time", "CaseProfile ID", "INT Ref"],
                tablefmt="grid"
            ))
        else:
            print("   ❌ NO WhatsApp entries found in database!")
        
        # Check Online Patrol entries
        patrol_entries = OnlinePatrolEntry.query.all()
        print(f"\n🔍 Online Patrol Entries: {len(patrol_entries)} total")
        
        if patrol_entries:
            patrol_data = []
            for p in patrol_entries:
                patrol_data.append([
                    p.id,
                    p.sender or "N/A",
                    p.source or "N/A",
                    p.complaint_time.strftime("%Y-%m-%d %H:%M") if p.complaint_time else "N/A",
                    p.caseprofile_id or "❌ NOT LINKED",
                    p.int_reference or "N/A"
                ])
            
            print(tabulate(
                patrol_data,
                headers=["ID", "Sender", "Source", "Complaint Time", "CaseProfile ID", "INT Ref"],
                tablefmt="grid"
            ))
        else:
            print("   ❌ NO Online Patrol entries found in database!")
        
        # Check CaseProfile entries
        case_profiles = CaseProfile.query.order_by(CaseProfile.index_order.asc()).all()
        print(f"\n🔗 CaseProfile Entries: {len(case_profiles)} total")
        
        if case_profiles:
            case_data = []
            for c in case_profiles:
                case_data.append([
                    c.id,
                    c.int_reference,
                    c.source_type,
                    c.date_of_receipt.strftime("%Y-%m-%d %H:%M") if c.date_of_receipt else "N/A",
                    c.email_id or "-",
                    c.whatsapp_id or "-",
                    c.patrol_id or "-",
                    c.created_by or "N/A"
                ])
            
            print(tabulate(
                case_data,
                headers=["ID", "INT Ref", "Source Type", "Receipt Date", "Email ID", "WhatsApp ID", "Patrol ID", "Created By"],
                tablefmt="grid"
            ))
        else:
            print("   ℹ️  NO CaseProfile entries yet")
        
        # Analysis
        print("\n" + "=" * 80)
        print("📈 ANALYSIS")
        print("=" * 80)
        
        unlinked_whatsapp = WhatsAppEntry.query.filter(
            WhatsAppEntry.caseprofile_id == None
        ).count()
        
        unlinked_patrol = OnlinePatrolEntry.query.filter(
            OnlinePatrolEntry.caseprofile_id == None
        ).count()
        
        if unlinked_whatsapp > 0:
            print(f"⚠️  {unlinked_whatsapp} WhatsApp entries NOT linked to CaseProfile")
        else:
            print(f"✅ All WhatsApp entries are linked")
        
        if unlinked_patrol > 0:
            print(f"⚠️  {unlinked_patrol} Online Patrol entries NOT linked to CaseProfile")
        else:
            print(f"✅ All Online Patrol entries are linked")
        
        # Check for orphaned CaseProfiles
        orphaned_cases = CaseProfile.query.filter(
            CaseProfile.email_id == None,
            CaseProfile.whatsapp_id == None,
            CaseProfile.patrol_id == None
        ).all()
        
        if orphaned_cases:
            print(f"\n⚠️  {len(orphaned_cases)} CaseProfile entries have NO source records:")
            for case in orphaned_cases:
                print(f"   - {case.int_reference} (ID: {case.id}, Type: {case.source_type})")
        
        print("\n" + "=" * 80)
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if unlinked_whatsapp > 0 or unlinked_patrol > 0:
            print("   1. Run: python3 migrate_existing_entries_to_unified_int.py")
            print("   2. This will create CaseProfile entries for unlinked records")
        
        if orphaned_cases:
            print("   ⚠️  WARNING: Orphaned CaseProfile entries detected!")
            print("   These entries have INT numbers but no source record.")
            print("   This happens when:")
            print("   - CaseProfile was created but source record creation failed")
            print("   - Database inconsistency")
            print("   Recommended: Delete these orphaned entries manually")

if __name__ == '__main__':
    check_database_status()
