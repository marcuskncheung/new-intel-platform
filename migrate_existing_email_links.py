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
        
        # Update POI statistics (only update columns that exist)
        print()
        print("📊 Updating POI statistics...")
        
        # Check which columns exist
        result = db.session.execute(db.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'alleged_person_profile' 
            AND column_name IN ('email_count', 'total_mentions', 'case_count', 'whatsapp_count', 'patrol_count', 'surveillance_count')
        """))
        existing_columns = [row[0] for row in result.fetchall()]
        print(f"📋 Found POI columns: {', '.join(existing_columns)}")
        
        if 'email_count' in existing_columns:
            # Update email_count (this column exists in v1.0)
            db.session.execute(db.text("""
                UPDATE alleged_person_profile ap
                SET email_count = (
                    SELECT COUNT(*) 
                    FROM poi_intelligence_link 
                    WHERE poi_id = ap.poi_id AND source_type = 'EMAIL'
                )
                WHERE poi_id IS NOT NULL
            """))
            db.session.commit()
            print("✅ email_count updated")
        
        if 'total_mentions' in existing_columns:
            # Update total_mentions (POI v2.0 column)
            db.session.execute(db.text("""
                UPDATE alleged_person_profile ap
                SET total_mentions = (
                    SELECT COUNT(*) 
                    FROM poi_intelligence_link 
                    WHERE poi_id = ap.poi_id
                )
                WHERE poi_id IS NOT NULL
            """))
            db.session.commit()
            print("✅ total_mentions updated")
        
        if 'case_count' in existing_columns:
            # Update case_count (POI v2.0 column)
            db.session.execute(db.text("""
                UPDATE alleged_person_profile ap
                SET case_count = (
                    SELECT COUNT(DISTINCT case_profile_id) 
                    FROM poi_intelligence_link 
                    WHERE poi_id = ap.poi_id
                )
                WHERE poi_id IS NOT NULL
            """))
            db.session.commit()
            print("✅ case_count updated")
        
        if not existing_columns:
            print("⚠️  No statistics columns found to update")
        
        print("✅ POI statistics update completed")
        
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
    try:
        db.session.rollback()
    except:
        pass  # Ignore rollback errors if outside app context
    sys.exit(1)
