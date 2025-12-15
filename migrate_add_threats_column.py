#!/usr/bin/env python3
"""
Migration script to add new columns that exist in models but not in database.

Adds:
- online_patrol_entry.threats (Text) - For tracking threats from online patrol
"""

import os
import sys

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://intel_user:intel_password@localhost:5432/intelligence_db')

def run_migration():
    """Add missing columns to database tables"""
    import psycopg2
    
    print("=" * 60)
    print("Migration: Add missing columns to database")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if threats column exists in online_patrol_entry
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'online_patrol_entry' AND column_name = 'threats'
        """)
        result = cursor.fetchone()
        
        if not result:
            print("\n🔄 Adding 'threats' column to online_patrol_entry...")
            cursor.execute("""
                ALTER TABLE online_patrol_entry 
                ADD COLUMN threats TEXT
            """)
            print("✅ Added 'threats' column to online_patrol_entry")
        else:
            print("✅ 'threats' column already exists in online_patrol_entry")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("Migration completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_migration()
