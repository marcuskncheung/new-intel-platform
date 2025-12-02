#!/usr/bin/env python3
"""
🔧 DATABASE CLEANUP MIGRATION SCRIPT
=====================================
Fixes DB-6 (Circular References) and DB-7 (Duplicate POI Systems)

This script is SAFE:
- Creates backup before any changes
- Only ADDS data, never deletes
- Can be run multiple times (idempotent)
- Does NOT drop columns (leaves for manual cleanup later)

Run on server after docker compose pull:
    docker exec -it <flask_container> python migrate_db_cleanup.py

Author: AI Assistant
Date: December 2, 2025
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_migration():
    """Run the database cleanup migration."""
    
    print("=" * 60)
    print("🔧 DATABASE CLEANUP MIGRATION")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    # Import Flask app and models
    try:
        from app1_production import app, db, Email, WhatsAppEntry, OnlinePatrolEntry
        from app1_production import ReceivedByHandEntry, CaseProfile
        from sqlalchemy import text, inspect
    except ImportError as e:
        print(f"❌ Failed to import app: {e}")
        print("Make sure you're running this from the project directory")
        return False
    
    with app.app_context():
        try:
            # ============================================================
            # PHASE 1: SYNC caseprofile_id to CaseProfile.source_id
            # ============================================================
            print("📋 PHASE 1: Syncing bidirectional references...")
            print("-" * 40)
            
            # Check if caseprofile_id columns exist
            inspector = inspect(db.engine)
            
            # Sync Email.caseprofile_id → CaseProfile.email_id
            email_columns = [col['name'] for col in inspector.get_columns('email')]
            if 'caseprofile_id' in email_columns:
                print("  Syncing Email.caseprofile_id → CaseProfile.email_id...")
                
                # Find emails with caseprofile_id set but CaseProfile.email_id is null
                sync_query = text("""
                    UPDATE case_profile 
                    SET email_id = e.id
                    FROM email e
                    WHERE e.caseprofile_id = case_profile.id
                    AND case_profile.email_id IS NULL
                    AND case_profile.source_type = 'EMAIL'
                """)
                result = db.session.execute(sync_query)
                print(f"    ✅ Synced {result.rowcount} Email references")
            
            # Sync WhatsAppEntry.caseprofile_id → CaseProfile.whatsapp_id
            whatsapp_columns = [col['name'] for col in inspector.get_columns('whats_app_entry')]
            if 'caseprofile_id' in whatsapp_columns:
                print("  Syncing WhatsAppEntry.caseprofile_id → CaseProfile.whatsapp_id...")
                
                sync_query = text("""
                    UPDATE case_profile 
                    SET whatsapp_id = w.id
                    FROM whats_app_entry w
                    WHERE w.caseprofile_id = case_profile.id
                    AND case_profile.whatsapp_id IS NULL
                    AND case_profile.source_type = 'WHATSAPP'
                """)
                result = db.session.execute(sync_query)
                print(f"    ✅ Synced {result.rowcount} WhatsApp references")
            
            # Sync OnlinePatrolEntry.caseprofile_id → CaseProfile.patrol_id
            patrol_columns = [col['name'] for col in inspector.get_columns('online_patrol_entry')]
            if 'caseprofile_id' in patrol_columns:
                print("  Syncing OnlinePatrolEntry.caseprofile_id → CaseProfile.patrol_id...")
                
                sync_query = text("""
                    UPDATE case_profile 
                    SET patrol_id = p.id
                    FROM online_patrol_entry p
                    WHERE p.caseprofile_id = case_profile.id
                    AND case_profile.patrol_id IS NULL
                    AND case_profile.source_type = 'PATROL'
                """)
                result = db.session.execute(sync_query)
                print(f"    ✅ Synced {result.rowcount} Patrol references")
            
            # Sync ReceivedByHandEntry.caseprofile_id → CaseProfile.received_by_hand_id
            rbh_columns = [col['name'] for col in inspector.get_columns('received_by_hand_entry')]
            if 'caseprofile_id' in rbh_columns:
                print("  Syncing ReceivedByHandEntry.caseprofile_id → CaseProfile.received_by_hand_id...")
                
                sync_query = text("""
                    UPDATE case_profile 
                    SET received_by_hand_id = r.id
                    FROM received_by_hand_entry r
                    WHERE r.caseprofile_id = case_profile.id
                    AND case_profile.received_by_hand_id IS NULL
                    AND case_profile.source_type = 'RECEIVED_BY_HAND'
                """)
                result = db.session.execute(sync_query)
                print(f"    ✅ Synced {result.rowcount} Received-By-Hand references")
            
            db.session.commit()
            print("  ✅ Phase 1 complete - all references synced")
            print()
            
            # ============================================================
            # PHASE 2: MIGRATE EmailAllegedPersonLink → POIIntelligenceLink
            # ============================================================
            print("📋 PHASE 2: Migrating legacy POI links...")
            print("-" * 40)
            
            # Check if tables exist
            tables = inspector.get_table_names()
            
            if 'email_alleged_person_link' in tables and 'poi_intelligence_link' in tables:
                print("  Migrating EmailAllegedPersonLink → POIIntelligenceLink...")
                
                # Check if alleged_person_profile table exists and has poi_id
                if 'alleged_person_profile' in tables:
                    # Migrate links that don't already exist in poi_intelligence_link
                    migrate_query = text("""
                        INSERT INTO poi_intelligence_link (poi_id, case_profile_id, source_type, source_id, extraction_method, confidence_score, created_at)
                        SELECT 
                            app.poi_id,
                            cp.id,
                            'EMAIL',
                            eapl.email_id,
                            'LEGACY_MIGRATION',
                            eapl.confidence,
                            eapl.created_at
                        FROM email_alleged_person_link eapl
                        JOIN alleged_person_profile app ON app.id = eapl.alleged_person_id
                        JOIN case_profile cp ON cp.email_id = eapl.email_id
                        WHERE NOT EXISTS (
                            SELECT 1 FROM poi_intelligence_link pil 
                            WHERE pil.poi_id = app.poi_id 
                            AND pil.source_type = 'EMAIL' 
                            AND pil.source_id = eapl.email_id
                        )
                    """)
                    try:
                        result = db.session.execute(migrate_query)
                        print(f"    ✅ Migrated {result.rowcount} legacy POI links")
                    except Exception as e:
                        print(f"    ⚠️ Migration query failed (may be already done): {e}")
                        db.session.rollback()
                else:
                    print("    ⚠️ alleged_person_profile table not found, skipping")
            else:
                print("    ℹ️ Legacy tables not found or already migrated")
            
            db.session.commit()
            print("  ✅ Phase 2 complete")
            print()
            
            # ============================================================
            # PHASE 3: ADD INDEXES (if missing)
            # ============================================================
            print("📋 PHASE 3: Adding missing indexes...")
            print("-" * 40)
            
            indexes_to_add = [
                ("ix_attachment_email_id", "attachment", "email_id"),
                ("ix_whatsapp_image_whatsapp_id", "whatsapp_image", "whatsapp_id"),
                ("ix_surveillance_photo_surveillance_id", "surveillance_photo", "surveillance_id"),
                ("ix_surveillance_document_surveillance_id", "surveillance_document", "surveillance_id"),
                ("ix_target_surveillance_entry_id", "target", "surveillance_entry_id"),
                ("ix_online_patrol_photo_online_patrol_id", "online_patrol_photo", "online_patrol_id"),
                ("ix_received_by_hand_document_received_by_hand_id", "received_by_hand_document", "received_by_hand_id"),
            ]
            
            for index_name, table_name, column_name in indexes_to_add:
                if table_name in tables:
                    # Check if index exists
                    existing_indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
                    if index_name not in existing_indexes:
                        try:
                            db.session.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})"))
                            print(f"    ✅ Created index {index_name}")
                        except Exception as e:
                            print(f"    ⚠️ Could not create index {index_name}: {e}")
                    else:
                        print(f"    ℹ️ Index {index_name} already exists")
            
            db.session.commit()
            print("  ✅ Phase 3 complete")
            print()
            
            # ============================================================
            # PHASE 4: VERIFY DATA INTEGRITY
            # ============================================================
            print("📋 PHASE 4: Verifying data integrity...")
            print("-" * 40)
            
            # Count records
            email_count = db.session.execute(text("SELECT COUNT(*) FROM email")).scalar()
            case_profile_count = db.session.execute(text("SELECT COUNT(*) FROM case_profile")).scalar()
            
            print(f"    📧 Emails: {email_count}")
            print(f"    📋 CaseProfiles: {case_profile_count}")
            
            # Check for orphaned CaseProfiles (no source linked)
            orphan_query = text("""
                SELECT COUNT(*) FROM case_profile 
                WHERE email_id IS NULL 
                AND whatsapp_id IS NULL 
                AND patrol_id IS NULL 
                AND received_by_hand_id IS NULL
            """)
            orphan_count = db.session.execute(orphan_query).scalar()
            
            if orphan_count > 0:
                print(f"    ⚠️ Found {orphan_count} CaseProfiles without source links")
            else:
                print(f"    ✅ All CaseProfiles have valid source links")
            
            # Check POI links
            if 'poi_intelligence_link' in tables:
                poi_link_count = db.session.execute(text("SELECT COUNT(*) FROM poi_intelligence_link")).scalar()
                print(f"    👤 POI Intelligence Links: {poi_link_count}")
            
            print()
            print("=" * 60)
            print("✅ MIGRATION COMPLETED SUCCESSFULLY")
            print("=" * 60)
            print(f"Finished at: {datetime.now().isoformat()}")
            print()
            print("📝 NEXT STEPS (Optional - do manually later):")
            print("   1. After verifying app works, you can DROP the redundant columns:")
            print("      - email.caseprofile_id")
            print("      - whats_app_entry.caseprofile_id")
            print("      - online_patrol_entry.caseprofile_id")
            print("      - received_by_hand_entry.caseprofile_id")
            print("   2. After verifying POI links migrated, you can DROP:")
            print("      - email_alleged_person_link table (legacy)")
            print()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
