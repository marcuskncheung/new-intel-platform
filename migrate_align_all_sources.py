"""
Database Migration: Align All Intelligence Sources with Email Assessment Structure

Purpose: Standardize assessment fields across Email, WhatsApp, Patrol, and Surveillance
Date: 2025-01-17

Fields to Add:
- alleged_person (multiple names)
- alleged_subject_english (for POI matching)
- alleged_subject_chinese (for POI matching)
- alleged_nature (type of allegation)
- allegation_summary (detailed summary)
- license_numbers_json (multiple license numbers)
- intermediary_types_json (Agent/Broker types)
- license_number (single license for backward compatibility)
"""

import psycopg2
from psycopg2 import sql
import sys

def migrate_align_assessment_fields():
    """Add standardized assessment fields to all intelligence sources"""
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host="postgres-db",
            database="intelligence_db",
            user="intelligence",
            password="SecureIntelDB2024!"
        )
        
        cur = conn.cursor()
        
        print("=" * 80)
        print("STANDARDIZING ASSESSMENT FIELDS ACROSS ALL INTELLIGENCE SOURCES")
        print("=" * 80)
        
        # ========================================================================
        # WHATSAPP ENTRY - Add missing fields
        # ========================================================================
        print("\n[1/3] WhatsApp Entry - Adding standardized fields...")
        
        whatsapp_fields = [
            ("alleged_subject_english", "TEXT"),
            ("alleged_subject_chinese", "TEXT"),
            ("alleged_nature", "TEXT"),
            ("allegation_summary", "TEXT"),
            ("license_numbers_json", "TEXT"),
            ("intermediary_types_json", "TEXT"),
            ("license_number", "VARCHAR(64)")
        ]
        
        for field_name, field_type in whatsapp_fields:
            try:
                # Check if column exists
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='whats_app_entry' 
                    AND column_name=%s
                """, (field_name,))
                
                if cur.fetchone():
                    print(f"  ✓ {field_name} already exists")
                else:
                    cur.execute(sql.SQL("""
                        ALTER TABLE whats_app_entry 
                        ADD COLUMN {} {}
                    """).format(
                        sql.Identifier(field_name),
                        sql.SQL(field_type)
                    ))
                    conn.commit()
                    print(f"  ✅ Added {field_name} ({field_type})")
            except Exception as e:
                conn.rollback()
                print(f"  ⚠️  Error adding {field_name}: {e}")
        
        # ========================================================================
        # ONLINE PATROL ENTRY - Add missing fields
        # ========================================================================
        print("\n[2/3] Online Patrol Entry - Adding standardized fields...")
        
        patrol_fields = [
            ("alleged_person", "VARCHAR(255)"),  # Already added, but check
            ("alleged_subject_english", "TEXT"),
            ("alleged_subject_chinese", "TEXT"),
            ("alleged_nature", "TEXT"),
            ("allegation_summary", "TEXT"),
            ("license_numbers_json", "TEXT"),
            ("intermediary_types_json", "TEXT"),
            ("license_number", "VARCHAR(64)"),
            ("preparer", "VARCHAR(255)"),
            ("reviewer_name", "VARCHAR(255)"),
            ("reviewer_comment", "TEXT"),
            ("reviewer_decision", "VARCHAR(16)"),
            ("intelligence_case_opened", "BOOLEAN DEFAULT FALSE")
        ]
        
        for field_name, field_type in patrol_fields:
            try:
                # Check if column exists
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='online_patrol_entry' 
                    AND column_name=%s
                """, (field_name,))
                
                if cur.fetchone():
                    print(f"  ✓ {field_name} already exists")
                else:
                    cur.execute(sql.SQL("""
                        ALTER TABLE online_patrol_entry 
                        ADD COLUMN {} {}
                    """).format(
                        sql.Identifier(field_name),
                        sql.SQL(field_type)
                    ))
                    conn.commit()
                    print(f"  ✅ Added {field_name} ({field_type})")
            except Exception as e:
                conn.rollback()
                print(f"  ⚠️  Error adding {field_name}: {e}")
        
        # ========================================================================
        # SURVEILLANCE ENTRY - Add missing fields
        # ========================================================================
        print("\n[3/3] Surveillance Entry - Adding standardized fields...")
        
        surveillance_fields = [
            ("alleged_nature", "TEXT"),
            ("allegation_summary", "TEXT"),
            ("preparer", "VARCHAR(255)"),
            ("reviewer_name", "VARCHAR(255)"),
            ("reviewer_comment", "TEXT"),
            ("reviewer_decision", "VARCHAR(16)"),
            ("intelligence_case_opened", "BOOLEAN DEFAULT FALSE"),
            ("assessment_updated_at", "TIMESTAMP")
        ]
        
        for field_name, field_type in surveillance_fields:
            try:
                # Check if column exists
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='surveillance_entry' 
                    AND column_name=%s
                """, (field_name,))
                
                if cur.fetchone():
                    print(f"  ✓ {field_name} already exists")
                else:
                    cur.execute(sql.SQL("""
                        ALTER TABLE surveillance_entry 
                        ADD COLUMN {} {}
                    """).format(
                        sql.Identifier(field_name),
                        sql.SQL(field_type)
                    ))
                    conn.commit()
                    print(f"  ✅ Added {field_name} ({field_type})")
            except Exception as e:
                conn.rollback()
                print(f"  ⚠️  Error adding {field_name}: {e}")
        
        # ========================================================================
        # VERIFICATION
        # ========================================================================
        print("\n" + "=" * 80)
        print("VERIFICATION - Checking all tables...")
        print("=" * 80)
        
        tables = ['email', 'whats_app_entry', 'online_patrol_entry', 'surveillance_entry']
        
        for table in tables:
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name=%s
                AND column_name IN (
                    'alleged_subject_english',
                    'alleged_subject_chinese',
                    'alleged_nature',
                    'allegation_summary',
                    'license_number',
                    'preparer',
                    'reviewer_name',
                    'assessment_updated_at'
                )
                ORDER BY column_name
            """, (table,))
            
            fields = [row[0] for row in cur.fetchall()]
            print(f"\n{table.upper()}:")
            print(f"  Standard fields present: {len(fields)}/8")
            if fields:
                for field in fields:
                    print(f"    ✓ {field}")
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False

if __name__ == "__main__":
    print("\n🔧 DATABASE SCHEMA ALIGNMENT TOOL")
    print("This will standardize assessment fields across all intelligence sources")
    print("to match the Email assessment structure.\n")
    
    response = input("Proceed with migration? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        success = migrate_align_assessment_fields()
        
        if success:
            print("\n📋 NEXT STEPS:")
            print("1. Update Python models in app1_production.py")
            print("2. Update HTML forms for WhatsApp/Patrol/Surveillance")
            print("3. Restart application: docker-compose restart intelligence-app")
            print("4. Test assessment workflows for all sources")
        else:
            print("\n❌ Migration failed. Please check error messages above.")
            sys.exit(1)
    else:
        print("Migration cancelled.")
        sys.exit(0)
