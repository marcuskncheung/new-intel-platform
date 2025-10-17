"""
Database Migration: Add alleged_person field to online_patrol_entry table

Purpose: Enable POI automation for Online Patrol entries
Date: 2025-01-17
"""

import psycopg2
from psycopg2 import sql

def migrate_add_alleged_person_to_patrol():
    """Add alleged_person column to online_patrol_entry table"""
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host="postgres-db",
            database="intelligence_db",
            user="intelligence",
            password="SecureIntelDB2024!"
        )
        
        cur = conn.cursor()
        
        print("[MIGRATION] Starting: Add alleged_person to online_patrol_entry")
        
        # Check if column already exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='online_patrol_entry' 
            AND column_name='alleged_person'
        """)
        
        if cur.fetchone():
            print("[MIGRATION] ℹ️  Column 'alleged_person' already exists in online_patrol_entry")
            cur.close()
            conn.close()
            return True
        
        # Add the column
        print("[MIGRATION] Adding 'alleged_person' column...")
        cur.execute("""
            ALTER TABLE online_patrol_entry 
            ADD COLUMN alleged_person VARCHAR(255);
        """)
        
        conn.commit()
        
        print("[MIGRATION] ✅ Successfully added 'alleged_person' column to online_patrol_entry")
        
        # Verify
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='online_patrol_entry' 
            AND column_name='alleged_person'
        """)
        
        result = cur.fetchone()
        if result:
            print(f"[MIGRATION] ✅ Verified: {result[0]} ({result[1]})")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"[MIGRATION] ❌ Error: {e}")
        if conn:
            conn.rollback()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add alleged_person to Online Patrol")
    print("=" * 60)
    
    success = migrate_add_alleged_person_to_patrol()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Restart application: docker-compose restart intelligence-app")
        print("2. Test creating/editing patrol entries with alleged persons")
        print("3. Verify POI profiles are created automatically")
    else:
        print("\n❌ Migration failed! Check error messages above.")
        print("\nTroubleshooting:")
        print("1. Verify database connection")
        print("2. Check if you're running from correct location")
        print("3. Ensure database user has ALTER TABLE permissions")
