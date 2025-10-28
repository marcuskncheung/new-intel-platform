#!/usr/bin/env python3
"""
Quick fix for missing received_by_hand_id column
Run this on the server to fix the database error
"""

import os
import sys
import psycopg2

def fix_database():
    """Fix the missing received_by_hand_id column"""
    
    # Get database connection from environment variables (Docker setup)
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'intelligence-db'),
        'database': os.getenv('POSTGRES_DB', 'intelligence_db'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'port': int(os.getenv('POSTGRES_PORT', 5432))
    }
    
    print("🔧 Connecting to database...")
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'case_profile' 
            AND column_name = 'received_by_hand_id'
        """)
        
        exists = cursor.fetchone()
        
        if exists:
            print("✅ Column received_by_hand_id already exists")
        else:
            print("❌ Column missing. Adding now...")
            
            # Add the missing column
            cursor.execute("""
                ALTER TABLE case_profile 
                ADD COLUMN received_by_hand_id INTEGER 
                REFERENCES received_by_hand_entry(id)
            """)
            
            # Create index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_case_profile_received_by_hand_id 
                ON case_profile(received_by_hand_id)
            """)
            
            conn.commit()
            print("✅ Successfully added received_by_hand_id column")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
    
    return True

if __name__ == "__main__":
    print("🚀 Fixing database schema...")
    if fix_database():
        print("🎉 Database fix completed!")
    else:
        print("💥 Database fix failed!")
        sys.exit(1)
