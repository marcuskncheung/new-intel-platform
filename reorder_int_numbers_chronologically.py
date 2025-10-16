#!/usr/bin/env python3
"""
Reorder ALL INT reference numbers chronologically by receipt date

This will:
1. Sort all CaseProfile entries by date_of_receipt (oldest first)
2. Renumber them INT-001, INT-002, INT-003... in chronological order
3. Update linked Email.int_reference_number to match
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app1_production import app, db, CaseProfile, Email
from sqlalchemy import text

def reorder_chronologically():
    """Reorder all INT numbers by receipt date"""
    with app.app_context():
        print("=" * 80)
        print("🔄 REORDERING INT NUMBERS CHRONOLOGICALLY")
        print("=" * 80)
        
        # Get ALL CaseProfiles sorted by receipt date
        all_profiles = CaseProfile.query.order_by(
            CaseProfile.date_of_receipt.asc()
        ).all()
        
        if not all_profiles:
            print("\n❌ No CaseProfile entries found!")
            return
        
        print(f"\n📊 Found {len(all_profiles)} CaseProfile entries")
        print("\n📅 Current order (by receipt date):")
        print("-" * 80)
        
        for i, cp in enumerate(all_profiles[:10], 1):
            date_str = cp.date_of_receipt.strftime('%Y-%m-%d %H:%M') if cp.date_of_receipt else 'Unknown'
            print(f"  {i:3d}. {cp.int_reference:8s} | {cp.source_type:8s} | {date_str}")
        
        if len(all_profiles) > 10:
            print(f"  ... ({len(all_profiles) - 10} more entries)")
        
        print("\n⚠️  This will renumber ALL entries chronologically:")
        print("   • Oldest receipt date → INT-001")
        print("   • Newest receipt date → INT-" + f"{len(all_profiles):03d}")
        print("   • Updates Email.int_reference_number to match")
        
        response = input("\nProceed with reordering? (yes/no): ").strip().lower()
        if response != 'yes':
            print("❌ Cancelled")
            return
        
        print("\n🔄 Reordering INT numbers...")
        print("-" * 80)
        
        updated = 0
        errors = 0
        
        # Temporarily disable unique constraint checks
        # We'll update in a transaction to avoid conflicts
        
        for new_order, case_profile in enumerate(all_profiles, 1):
            try:
                old_int_ref = case_profile.int_reference
                new_int_ref = f"INT-{new_order:03d}"
                
                # Skip if already correct
                if old_int_ref == new_int_ref:
                    continue
                
                # Update CaseProfile
                case_profile.int_reference = new_int_ref
                case_profile.index_order = new_order
                
                # Update linked Email if exists
                if case_profile.email_id:
                    email = Email.query.get(case_profile.email_id)
                    if email:
                        email.int_reference_number = new_int_ref
                        email.int_reference_order = new_order
                
                updated += 1
                
                if updated % 10 == 0 or new_order == len(all_profiles):
                    print(f"  Progress: {new_order}/{len(all_profiles)} ({updated} updated)")
                
            except Exception as e:
                errors += 1
                print(f"\n  ❌ Error updating {old_int_ref}: {str(e)[:80]}")
                continue
        
        # Commit all changes at once
        try:
            db.session.commit()
            print("\n✅ Successfully committed all changes!")
        except Exception as e:
            print(f"\n❌ Error committing changes: {e}")
            db.session.rollback()
            return
        
        print("\n" + "=" * 80)
        print("📊 REORDERING RESULTS:")
        print("=" * 80)
        print(f"  Total entries: {len(all_profiles)}")
        print(f"  ✅ Successfully updated: {updated}")
        print(f"  ❌ Errors: {errors}")
        
        # Show new order
        print("\n📅 NEW CHRONOLOGICAL ORDER:")
        print("-" * 80)
        
        refreshed_profiles = CaseProfile.query.order_by(
            CaseProfile.index_order.asc()
        ).limit(10).all()
        
        for cp in refreshed_profiles:
            date_str = cp.date_of_receipt.strftime('%Y-%m-%d %H:%M') if cp.date_of_receipt else 'Unknown'
            print(f"  {cp.int_reference:8s} | {cp.source_type:8s} | {date_str}")
        
        if len(all_profiles) > 10:
            print(f"  ... ({len(all_profiles) - 10} more entries)")
        
        print("\n✅ ALL INT NUMBERS NOW IN CHRONOLOGICAL ORDER!")
        print("\n📝 Next steps:")
        print("   1. Restart application: docker-compose restart web")
        print("   2. Check database - INT numbers should be chronological")
        print("   3. Check /int_source page - should display in correct order")

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CHRONOLOGICAL INT NUMBER REORDERING")
    print("=" * 80 + "\n")
    reorder_chronologically()
    print("\n" + "=" * 80)
    print("✅ COMPLETE")
    print("=" * 80 + "\n")
