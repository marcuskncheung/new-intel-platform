#!/usr/bin/env python3
"""
Fix Patrol ID Sequence - Change PATROL-2 to PATROL-1 and reset auto-increment

This script:
1. Updates the ID of existing patrol entry from 2 to 1
2. Resets the auto-increment sequence to start from 2
3. Updates any foreign key references (caseprofile_id in CaseProfile table)
"""

import sys
from flask import Flask
from sqlalchemy import text, inspect
from app1_production import app, db, OnlinePatrolEntry, CaseProfile

def fix_patrol_id_sequence():
    """Fix the patrol ID sequence and update existing entry"""
    
    with app.app_context():
        try:
            print("=" * 60)
            print("PATROL ID SEQUENCE FIX")
            print("=" * 60)
            
            # Check if PATROL-1 exists
            patrol_1 = db.session.execute(
                text("SELECT * FROM online_patrol_entry WHERE id = 1")
            ).fetchone()
            
            if patrol_1:
                print("✅ PATROL-1 already exists (ID=1)")
                print("   No changes needed.")
                return
            
            # Check if PATROL-2 exists
            patrol_2 = db.session.execute(
                text("SELECT * FROM online_patrol_entry WHERE id = 2")
            ).fetchone()
            
            if not patrol_2:
                print("❌ No PATROL entry found with ID=2")
                print("   Nothing to fix.")
                return
            
            print(f"Found entry: PATROL-2 (ID=2)")
            
            # Step 1: Check for any CaseProfile entries referencing patrol_id=2
            case_profiles_with_patrol_2 = db.session.execute(
                text("SELECT id, int_reference FROM case_profile WHERE patrol_id = 2")
            ).fetchall()
            
            if case_profiles_with_patrol_2:
                print(f"\n📋 Found {len(case_profiles_with_patrol_2)} CaseProfile(s) referencing patrol_id=2:")
                for cp in case_profiles_with_patrol_2:
                    print(f"   - CaseProfile ID={cp[0]}, INT={cp[1]}")
            
            # Step 2: Update the patrol entry ID from 2 to 1
            print("\n🔄 Updating patrol entry ID: 2 → 1...")
            
            # Temporarily disable foreign key constraints (SQLite specific)
            db.session.execute(text("PRAGMA foreign_keys = OFF"))
            
            # Update patrol entry ID
            db.session.execute(
                text("UPDATE online_patrol_entry SET id = 1 WHERE id = 2")
            )
            
            # Update CaseProfile references
            if case_profiles_with_patrol_2:
                print(f"🔄 Updating CaseProfile references: patrol_id 2 → 1...")
                db.session.execute(
                    text("UPDATE case_profile SET patrol_id = 1 WHERE patrol_id = 2")
                )
            
            # Re-enable foreign key constraints
            db.session.execute(text("PRAGMA foreign_keys = ON"))
            
            # Step 3: Reset the auto-increment sequence
            print("🔄 Resetting auto-increment sequence to start from 2...")
            
            # SQLite: Update sqlite_sequence table
            db.session.execute(
                text("UPDATE sqlite_sequence SET seq = 1 WHERE name = 'online_patrol_entry'")
            )
            
            # Commit all changes
            db.session.commit()
            
            print("\n" + "=" * 60)
            print("✅ SUCCESS! Patrol ID sequence fixed:")
            print("   - Existing entry now shows as PATROL-1")
            print("   - Next new entry will be PATROL-2")
            print("   - CaseProfile references updated")
            print("=" * 60)
            
            # Verify the changes
            print("\n🔍 Verification:")
            patrol_1_verify = db.session.execute(
                text("SELECT id, source, alleged_person FROM online_patrol_entry WHERE id = 1")
            ).fetchone()
            
            if patrol_1_verify:
                print(f"✅ PATROL-1 exists:")
                print(f"   ID: {patrol_1_verify[0]}")
                print(f"   Source: {patrol_1_verify[1]}")
                print(f"   Alleged Person: {patrol_1_verify[2]}")
            
            current_seq = db.session.execute(
                text("SELECT seq FROM sqlite_sequence WHERE name = 'online_patrol_entry'")
            ).scalar()
            print(f"✅ Auto-increment sequence: {current_seq}")
            print(f"   Next entry will be PATROL-{current_seq + 1}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    print("\n⚠️  WARNING: This script will modify the database!")
    print("   - Change PATROL-2 to PATROL-1")
    print("   - Reset auto-increment sequence")
    print("   - Update CaseProfile references")
    
    response = input("\nDo you want to continue? (yes/no): ").strip().lower()
    
    if response == "yes":
        fix_patrol_id_sequence()
    else:
        print("❌ Operation cancelled.")
        sys.exit(0)
