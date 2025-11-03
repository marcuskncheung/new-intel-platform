#!/usr/bin/env python3
"""
Migration: Change alleged_nature column from VARCHAR(255) to TEXT
This fixes the error: "value too long for type character varying(255)"
when saving multiple allegation types that exceed 255 characters.
"""

import psycopg2
import os

def migrate_alleged_nature_to_text():
    """Change alleged_nature column to TEXT type"""
    
    # Get database connection details from environment
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'intelligence_db')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("=" * 60)
        print("Migration: Change alleged_nature to TEXT")
        print("=" * 60)
        
        # Check current column type
        cursor.execute("""
            SELECT 
                column_name, 
                data_type, 
                character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'email' 
            AND column_name = 'alleged_nature'
        """)
        
        result = cursor.fetchone()
        if result:
            col_name, data_type, max_length = result
            print(f"\n✓ Current column: {col_name}")
            print(f"  Type: {data_type}")
            print(f"  Max length: {max_length}")
        else:
            print("\n✗ Column 'alleged_nature' not found!")
            return False
        
        # Only migrate if it's not already TEXT
        if data_type == 'text':
            print("\n✓ Column is already TEXT type. No migration needed.")
            return True
        
        print(f"\n→ Changing from {data_type}({max_length}) to TEXT...")
        
        # Change column type to TEXT
        cursor.execute("""
            ALTER TABLE email 
            ALTER COLUMN alleged_nature TYPE TEXT
        """)
        
        # Verify the change
        cursor.execute("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'email' 
            AND column_name = 'alleged_nature'
        """)
        
        new_type = cursor.fetchone()[0]
        
        if new_type == 'text':
            print(f"✓ Column type changed to: {new_type}")
            conn.commit()
            print("\n✓ Migration completed successfully!")
            return True
        else:
            print(f"✗ Migration failed. Current type: {new_type}")
            conn.rollback()
            return False
            
    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("=" * 60)

if __name__ == "__main__":
    success = migrate_alleged_nature_to_text()
    exit(0 if success else 1)
