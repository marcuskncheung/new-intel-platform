#!/usr/bin/env python3
"""
Migrate existing WhatsApp and Online Patrol entries to Unified INT system

This script:
1. Finds all WhatsApp entries without caseprofile_id
2. Finds all Online Patrol entries without caseprofile_id
3. Creates CaseProfile entries for each with proper INT references
4. Links them back to their source records

Run this ONCE after deploying the unified INT system
"""
import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app1_production import app, db, WhatsAppEntry, OnlinePatrolEntry, CaseProfile, create_unified_intelligence_entry
from tabulate import tabulate

def migrate_existing_entries():
    """Migrate all existing WhatsApp and Online Patrol entries to unified INT system"""
    with app.app_context():
        try:
            print("=" * 80)
            print("🔄 UNIFIED INT MIGRATION: Link Existing Entries")
            print("=" * 80)
            
            # Find WhatsApp entries without CaseProfile
            unlinked_whatsapp = WhatsAppEntry.query.filter(
                WhatsAppEntry.caseprofile_id == None
            ).order_by(WhatsAppEntry.received_time.asc()).all()
            
            # Find Online Patrol entries without CaseProfile
            unlinked_patrol = OnlinePatrolEntry.query.filter(
                OnlinePatrolEntry.caseprofile_id == None
            ).order_by(OnlinePatrolEntry.complaint_time.asc()).all()
            
            print(f"\n📊 Found:")
            print(f"   - {len(unlinked_whatsapp)} WhatsApp entries without INT references")
            print(f"   - {len(unlinked_patrol)} Online Patrol entries without INT references")
            
            if not unlinked_whatsapp and not unlinked_patrol:
                print("\n✅ All entries are already linked! Nothing to migrate.")
                return
            
            print("\n⚠️  This will create CaseProfile entries for all unlinked records.")
            print("   INT numbers will be assigned chronologically by receipt date.")
            
            response = input("\nProceed with migration? (yes/no): ").strip().lower()
            if response != 'yes':
                print("❌ Aborted. No changes made.")
                return
            
            created_profiles = []
            
            # Migrate WhatsApp entries
            print("\n🔄 Migrating WhatsApp entries...")
            for entry in unlinked_whatsapp:
                try:
                    case_profile = create_unified_intelligence_entry(
                        source_record=entry,
                        source_type="WHATSAPP",
                        created_by="MIGRATION_SCRIPT"
                    )
                    
                    if case_profile:
                        created_profiles.append([
                            case_profile.index,
                            "WHATSAPP",
                            entry.id,
                            entry.received_time.strftime("%Y-%m-%d %H:%M") if entry.received_time else "N/A",
                            entry.complaint_name or "N/A"
                        ])
                        print(f"   ✅ Created {case_profile.index} for WhatsApp entry {entry.id}")
                    else:
                        print(f"   ❌ Failed to create CaseProfile for WhatsApp entry {entry.id}")
                        
                except Exception as e:
                    print(f"   ❌ Error migrating WhatsApp entry {entry.id}: {e}")
                    continue
            
            # Migrate Online Patrol entries
            print("\n🔄 Migrating Online Patrol entries...")
            for entry in unlinked_patrol:
                try:
                    case_profile = create_unified_intelligence_entry(
                        source_record=entry,
                        source_type="PATROL",
                        created_by="MIGRATION_SCRIPT"
                    )
                    
                    if case_profile:
                        created_profiles.append([
                            case_profile.index,
                            "PATROL",
                            entry.id,
                            entry.complaint_time.strftime("%Y-%m-%d %H:%M") if entry.complaint_time else "N/A",
                            entry.sender or "N/A"
                        ])
                        print(f"   ✅ Created {case_profile.index} for Online Patrol entry {entry.id}")
                    else:
                        print(f"   ❌ Failed to create CaseProfile for Online Patrol entry {entry.id}")
                        
                except Exception as e:
                    print(f"   ❌ Error migrating Online Patrol entry {entry.id}: {e}")
                    continue
            
            # Commit all changes
            try:
                db.session.commit()
                print(f"\n✅ Successfully migrated {len(created_profiles)} entries!")
                
                # Show summary
                if created_profiles:
                    print("\n📊 MIGRATION SUMMARY:")
                    print(tabulate(
                        created_profiles,
                        headers=["INT Ref", "Type", "Source ID", "Date", "Name"],
                        tablefmt="grid"
                    ))
                
                # Show statistics
                print("\n📈 STATISTICS:")
                print(f"   - Total CaseProfiles: {CaseProfile.query.count()}")
                print(f"   - WhatsApp linked: {WhatsAppEntry.query.filter(WhatsAppEntry.caseprofile_id != None).count()}")
                print(f"   - Online Patrol linked: {OnlinePatrolEntry.query.filter(OnlinePatrolEntry.caseprofile_id != None).count()}")
                
                print("\n✅ Migration complete! INT references will now display on /int_source page.")
                
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Error committing changes: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
                
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    migrate_existing_entries()
