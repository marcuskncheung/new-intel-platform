#!/usr/bin/env python3
"""
🔄 ONLINE PATROL MODULE REDESIGN - DATABASE MIGRATION
=====================================================
Adds new professional columns to OnlinePatrolEntry table:
- discovered_by: Intelligence team member who found the post
- discovery_time: When we logged/discovered it  
- source_time: When the online post was originally created
- Creates OnlinePatrolPhoto table for photo uploads

MIGRATION STRATEGY:
1. Add new columns (discovered_by, discovery_time, source_time)
2. Migrate data from old columns (sender → discovered_by, complaint_time → discovery_time)
3. Create OnlinePatrolPhoto table
4. Keep legacy columns (sender, complaint_time, status) for backward compatibility

Run this BEFORE restarting the application.
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app1_production import app, db
from sqlalchemy import text, inspect

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception as e:
        print(f"⚠️  Error checking column: {e}")
        return False

def check_table_exists(table_name):
    """Check if a table exists"""
    try:
        inspector = inspect(db.engine)
        return table_name in inspector.get_table_names()
    except Exception as e:
        print(f"⚠️  Error checking table: {e}")
        return False

def migrate_online_patrol_redesign():
    """Execute the Online Patrol redesign migration"""
    
    print("=" * 70)
    print("🚀 ONLINE PATROL MODULE REDESIGN - DATABASE MIGRATION")
    print("=" * 70)
    print()
    
    with app.app_context():
        try:
            # ============================================================
            # STEP 1: Add new columns to online_patrol_entry
            # ============================================================
            print("📋 STEP 1: Adding new columns to online_patrol_entry table...")
            print()
            
            new_columns = {
                'discovered_by': "ALTER TABLE online_patrol_entry ADD COLUMN discovered_by VARCHAR(255)",
                'discovery_time': "ALTER TABLE online_patrol_entry ADD COLUMN discovery_time TIMESTAMP",
                'source_time': "ALTER TABLE online_patrol_entry ADD COLUMN source_time TIMESTAMP"
            }
            
            for col_name, sql in new_columns.items():
                if not check_column_exists('online_patrol_entry', col_name):
                    print(f"   ➕ Adding column '{col_name}'...")
                    db.session.execute(text(sql))
                    db.session.commit()
                    print(f"   ✅ Column '{col_name}' added successfully")
                else:
                    print(f"   ⏭️  Column '{col_name}' already exists, skipping")
            
            print()
            
            # ============================================================
            # STEP 2: Migrate existing data
            # ============================================================
            print("📦 STEP 2: Migrating data from old columns to new columns...")
            print()
            
            # Copy sender → discovered_by
            print("   🔄 Copying 'sender' → 'discovered_by'...")
            db.session.execute(text("""
                UPDATE online_patrol_entry 
                SET discovered_by = sender 
                WHERE discovered_by IS NULL AND sender IS NOT NULL
            """))
            rows_updated = db.session.execute(text("""
                SELECT COUNT(*) FROM online_patrol_entry 
                WHERE discovered_by IS NOT NULL
            """)).scalar()
            print(f"   ✅ Updated {rows_updated} rows with discovered_by")
            
            # Copy complaint_time → discovery_time AND source_time (for now)
            print("   🔄 Copying 'complaint_time' → 'discovery_time' and 'source_time'...")
            db.session.execute(text("""
                UPDATE online_patrol_entry 
                SET discovery_time = complaint_time,
                    source_time = complaint_time
                WHERE complaint_time IS NOT NULL
            """))
            rows_updated = db.session.execute(text("""
                SELECT COUNT(*) FROM online_patrol_entry 
                WHERE discovery_time IS NOT NULL
            """)).scalar()
            print(f"   ✅ Updated {rows_updated} rows with discovery_time and source_time")
            
            db.session.commit()
            print()
            
            # ============================================================
            # STEP 3: Create OnlinePatrolPhoto table
            # ============================================================
            print("📸 STEP 3: Creating OnlinePatrolPhoto table...")
            print()
            
            if not check_table_exists('online_patrol_photo'):
                create_table_sql = """
                CREATE TABLE online_patrol_photo (
                    id SERIAL PRIMARY KEY,
                    online_patrol_id INTEGER NOT NULL REFERENCES online_patrol_entry(id) ON DELETE CASCADE,
                    filename VARCHAR(255) NOT NULL,
                    image_data BYTEA NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    uploaded_by VARCHAR(255),
                    caption TEXT
                )
                """
                print("   ➕ Creating online_patrol_photo table...")
                db.session.execute(text(create_table_sql))
                
                # Create index for faster lookups
                db.session.execute(text("""
                    CREATE INDEX idx_online_patrol_photo_patrol_id 
                    ON online_patrol_photo(online_patrol_id)
                """))
                
                db.session.commit()
                print("   ✅ Table 'online_patrol_photo' created successfully")
                print("   ✅ Index 'idx_online_patrol_photo_patrol_id' created")
            else:
                print("   ⏭️  Table 'online_patrol_photo' already exists, skipping")
            
            print()
            
            # ============================================================
            # STEP 4: Verification
            # ============================================================
            print("🔍 STEP 4: Verifying migration...")
            print()
            
            # Count online patrol entries
            total_entries = db.session.execute(text("""
                SELECT COUNT(*) FROM online_patrol_entry
            """)).scalar()
            
            entries_with_new_fields = db.session.execute(text("""
                SELECT COUNT(*) FROM online_patrol_entry 
                WHERE discovered_by IS NOT NULL OR discovery_time IS NOT NULL
            """)).scalar()
            
            print(f"   📊 Total Online Patrol entries: {total_entries}")
            print(f"   📊 Entries with new fields populated: {entries_with_new_fields}")
            
            if check_table_exists('online_patrol_photo'):
                photo_count = db.session.execute(text("""
                    SELECT COUNT(*) FROM online_patrol_photo
                """)).scalar()
                print(f"   📊 Total Online Patrol photos: {photo_count}")
            
            print()
            
            # ============================================================
            # SUCCESS!
            # ============================================================
            print("=" * 70)
            print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 70)
            print()
            print("📝 SUMMARY:")
            print(f"   • Added 3 new columns to online_patrol_entry table")
            print(f"   • Migrated data from old columns to new columns")
            print(f"   • Created online_patrol_photo table for photo uploads")
            print(f"   • Legacy columns (sender, complaint_time, status) retained for compatibility")
            print()
            print("🎯 NEXT STEPS:")
            print("   1. Restart the Docker containers: docker-compose restart")
            print("   2. Test the Online Patrol module with new fields")
            print("   3. Upload test photos to verify photo upload functionality")
            print("   4. After validation, consider removing legacy columns in future release")
            print()
            
        except Exception as e:
            print()
            print("=" * 70)
            print("❌ MIGRATION FAILED!")
            print("=" * 70)
            print(f"Error: {str(e)}")
            print()
            import traceback
            traceback.print_exc()
            print()
            print("💡 TIP: Check the error message above and ensure:")
            print("   • PostgreSQL database is running")
            print("   • Database connection is working")
            print("   • You have sufficient permissions")
            print()
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    migrate_online_patrol_redesign()
