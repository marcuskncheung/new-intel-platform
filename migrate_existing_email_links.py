#!/usr/bin/env python3
"""
Migrate Existing Email-POI Links to POI v2.0 Universal Table

This script migrates data from email_alleged_person_link to poi_intelligence_link
without disrupting existing functionality.

Usage:
    docker compose exec intelligence-platform python3 migrate_existing_email_links.py
"""

from app1_production import app, db
import sys

print("=" * 70)
print("📦 Migrating Email-POI Links to Universal POI v2.0 Table")
print("=" * 70)
print()

try:
    with app.app_context():
        # Check if tables exist
        result = db.session.execute(db.text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name IN ('email_alleged_person_link', 'poi_intelligence_link')
        """))
        table_count = result.scalar()
        
        if table_count != 2:
            print("❌ Required tables not found")
            print("   Make sure both tables exist")
            sys.exit(1)
        
        print("✅ Tables verified")
        print()
        
        # Count existing links in old table
        result = db.session.execute(db.text("""
            SELECT COUNT(*) FROM email_alleged_person_link
        """))
        old_count = result.scalar()
        print(f"📊 Found {old_count} links in email_alleged_person_link")
        
        # Count existing links in new table
        result = db.session.execute(db.text("""
            SELECT COUNT(*) FROM poi_intelligence_link WHERE source_type = 'EMAIL'
        """))
        new_count = result.scalar()
        print(f"📊 Found {new_count} email links already in poi_intelligence_link")
        print()
        
        if old_count == 0:
            print("⚠️  No links to migrate")
            sys.exit(0)
        
        # Migrate links
        print("🔄 Migrating links...")
        result = db.session.execute(db.text("""
            INSERT INTO poi_intelligence_link (
                poi_id, 
                case_profile_id, 
                source_type, 
                source_id,
                extraction_method, 
                confidence_score, 
                created_at
            )
            SELECT 
                ap.poi_id,
                e.caseprofile_id,
                'EMAIL' as source_type,
                eapl.email_id as source_id,
                CASE 
                    WHEN eapl.created_by = 'AI_ANALYSIS' THEN 'AI'
                    WHEN eapl.created_by = 'MANUAL_INPUT' THEN 'MANUAL'
                    ELSE 'MANUAL'
                END as extraction_method,
                COALESCE(eapl.confidence, 1.0) as confidence_score,
                COALESCE(eapl.created_at, CURRENT_TIMESTAMP) as created_at
            FROM email_alleged_person_link eapl
            JOIN alleged_person_profile ap ON eapl.alleged_person_id = ap.id
            JOIN email e ON eapl.email_id = e.id
            WHERE e.caseprofile_id IS NOT NULL
              AND ap.poi_id IS NOT NULL
            ON CONFLICT (poi_id, source_type, source_id) DO NOTHING
        """))
        
        migrated = result.rowcount
        db.session.commit()
        
        print(f"✅ Migrated {migrated} email-POI links")
        print()
        
        # Verify migration
        result = db.session.execute(db.text("""
            SELECT COUNT(*) FROM poi_intelligence_link WHERE source_type = 'EMAIL'
        """))
        final_count = result.scalar()
        print(f"📊 Total email links in poi_intelligence_link: {final_count}")
        
        # Update POI statistics
        print()
        print("📊 Updating POI statistics...")
        db.session.execute(db.text("""
            UPDATE alleged_person_profile ap
            SET 
                email_count = (
                    SELECT COUNT(*) 
                    FROM poi_intelligence_link 
                    WHERE poi_id = ap.poi_id AND source_type = 'EMAIL'
                ),
                total_mentions = (
                    SELECT COUNT(*) 
                    FROM poi_intelligence_link 
                    WHERE poi_id = ap.poi_id
                ),
                case_count = (
                    SELECT COUNT(DISTINCT case_profile_id) 
                    FROM poi_intelligence_link 
                    WHERE poi_id = ap.poi_id
                )
            WHERE poi_id IS NOT NULL
        """))
        db.session.commit()
        print("✅ POI statistics updated")
        
        print()
        print("=" * 70)
        print("✅ MIGRATION COMPLETE!")
        print("=" * 70)
        print()
        print("📋 Summary:")
        print(f"  • Old table links: {old_count}")
        print(f"  • Migrated: {migrated}")
        print(f"  • Total in new table: {final_count}")
        print()
        print("⚠️  Note: Keep email_alleged_person_link table for now")
        print("   It won't interfere with the new system")
        print()

except Exception as e:
    print()
    print("❌ ERROR during migration:")
    print(f"   {str(e)}")
    print()
    db.session.rollback()
    sys.exit(1)
