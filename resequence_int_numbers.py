#!/usr/bin/env python3
"""
Re-sequence all existing INT numbers in chronological order

This script will:
1. Fetch all CaseProfile entries
2. Sort them by date_of_receipt
3. Renumber them as INT-001, INT-002, INT-003... in chronological order
4. Update the database

Run this ONCE after deploying the chronological INT fix
"""
import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app1_production import app, db, CaseProfile
from tabulate import tabulate

def resequence_all_int_references():
    """Re-sequence all INT references in chronological order"""
    with app.app_context():
        try:
            # Fetch all CaseProfiles ordered by receipt date
            profiles = CaseProfile.query.order_by(
                CaseProfile.date_of_receipt.asc()
            ).all()
            
            if not profiles:
                print("✅ No CaseProfile entries found. Nothing to re-sequence.")
                return
            
            print(f"\n📊 Found {len(profiles)} CaseProfile entries")
            print("=" * 80)
            
            # Show current state
            print("\n🔍 CURRENT STATE (before re-sequencing):")
            current_data = []
            for p in profiles:
                current_data.append([
                    p.index,
                    p.index_order,
                    p.source_type,
                    p.date_of_receipt.strftime("%Y-%m-%d %H:%M") if p.date_of_receipt else "N/A",
                    f"E:{p.email_id}" if p.email_id else
                    f"W:{p.whatsapp_id}" if p.whatsapp_id else
                    f"P:{p.patrol_id}" if p.patrol_id else "None"
                ])
            print(tabulate(current_data, headers=["Current INT", "Order", "Type", "Receipt Date", "Source"], tablefmt="grid"))
            
            # Check if already in correct order
            needs_resequencing = False
            for i, p in enumerate(profiles, start=1):
                expected_index = f"INT-{i:03d}"
                if p.index != expected_index or p.index_order != i:
                    needs_resequencing = True
                    break
            
            if not needs_resequencing:
                print("\n✅ All INT references are already in correct chronological order!")
                return
            
            print("\n⚠️  Some INT references are out of chronological order!")
            print("\n🔄 RE-SEQUENCING to chronological order...")
            
            # Re-sequence
            changes = []
            for i, profile in enumerate(profiles, start=1):
                old_index = profile.index
                old_order = profile.index_order
                
                new_index = f"INT-{i:03d}"
                new_order = i
                
                if old_index != new_index or old_order != new_order:
                    profile.index = new_index
                    profile.index_order = new_order
                    changes.append([
                        old_index,
                        new_index,
                        profile.source_type,
                        profile.date_of_receipt.strftime("%Y-%m-%d %H:%M") if profile.date_of_receipt else "N/A"
                    ])
            
            if changes:
                print(f"\n📝 Changes to be made ({len(changes)} entries):")
                print(tabulate(changes, headers=["Old INT", "New INT", "Type", "Receipt Date"], tablefmt="grid"))
                
                # Confirm before committing
                response = input("\n⚠️  Proceed with re-sequencing? (yes/no): ").strip().lower()
                if response != 'yes':
                    print("❌ Aborted. No changes made.")
                    return
                
                # Commit changes
                db.session.commit()
                print(f"\n✅ Successfully re-sequenced {len(changes)} INT references!")
                
                # Show final state
                print("\n📊 FINAL STATE (after re-sequencing):")
                final_data = []
                for i, p in enumerate(profiles, start=1):
                    final_data.append([
                        p.index,
                        p.index_order,
                        p.source_type,
                        p.date_of_receipt.strftime("%Y-%m-%d %H:%M") if p.date_of_receipt else "N/A"
                    ])
                print(tabulate(final_data, headers=["INT Ref", "Order", "Type", "Receipt Date"], tablefmt="grid"))
                
            else:
                print("\n✅ No changes needed!")
                
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error during re-sequencing: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    print("=" * 80)
    print("🔄 INT REFERENCE RE-SEQUENCING TOOL")
    print("=" * 80)
    print("\nThis will re-order all INT references chronologically by receipt date.")
    print("Example: If INT-180 has date 2024-01-01 and INT-002 has date 2024-02-01,")
    print("         they will be swapped to maintain chronological order.\n")
    
    resequence_all_int_references()
