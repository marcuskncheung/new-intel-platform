#!/usr/bin/env python3
"""
Migration script to change alleged_nature column from VARCHAR(255) to TEXT
in the Email table to support longer JSON arrays.

This fixes the error:
  psycopg2.errors.StringDataRightTruncation: value too long for type character varying(255)
"""

import os
import sys

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://intel_user:intel_password@localhost:5432/intelligence_db')

def run_migration():
    """Run the migration to change alleged_nature to TEXT"""
    import psycopg2
    
    print("=" * 60)
    print("Migration: Change alleged_nature column to TEXT")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check current column type
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'email' AND column_name = 'alleged_nature'
        """)
        result = cursor.fetchone()
        
        if result:
            col_name, data_type, max_length = result
            print(f"Current column type: {data_type}")
            if max_length:
                print(f"Current max length: {max_length}")
            
            if data_type == 'character varying':
                print("\n🔄 Altering column to TEXT...")
                cursor.execute("""
                    ALTER TABLE email 
                    ALTER COLUMN alleged_nature TYPE TEXT
                """)
                print("✅ Column altered successfully!")
            else:
                print(f"✅ Column is already TEXT type, no migration needed.")
        else:
            print("⚠️ Column 'alleged_nature' not found in 'email' table")
        
        # Also check and fix other tables that might have this issue
        tables_to_check = [
            ('whatsapp_entry', 'alleged_nature'),
            ('online_patrol_entry', 'alleged_nature'),
            ('surveillance_entry', 'alleged_nature'),
            ('received_by_hand', 'alleged_nature'),
        ]
        
        for table_name, column_name in tables_to_check:
            cursor.execute("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
            """, (table_name, column_name))
            result = cursor.fetchone()
            
            if result:
                col_name, data_type, max_length = result
                if data_type == 'character varying':
                    print(f"\n🔄 Altering {table_name}.{column_name} to TEXT...")
                    cursor.execute(f"""
                        ALTER TABLE {table_name} 
                        ALTER COLUMN {column_name} TYPE TEXT
                    """)
                    print(f"✅ {table_name}.{column_name} altered successfully!")
                else:
                    print(f"✅ {table_name}.{column_name} is already TEXT type")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_migration()
