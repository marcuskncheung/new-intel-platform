#!/usr/bin/env python3
"""
Database schema fix for audit_log table
Fixes the details column from VARCHAR(100) to TEXT to prevent truncation errors
"""

import psycopg2
import os
from datetime import datetime

def fix_audit_log_schema():
    """Fix the audit_log table schema to use TEXT for details column"""
    
    # Database connection parameters
    db_config = {
        'host': 'postgres-db',
        'port': 5432,
        'database': 'intelligence_db',
        'user': 'intelligence',
        'password': 'SecureIntelDB2024!'
    }
    
    try:
        print(f"[{datetime.now()}] Connecting to PostgreSQL database...")
        
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        print(f"[{datetime.now()}] Checking current audit_log table schema...")
        
        # Check current column type
        cursor.execute("""
            SELECT data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'audit_log' AND column_name = 'details'
        """)
        
        result = cursor.fetchone()
        if result:
            data_type, max_length = result
            print(f"[{datetime.now()}] Current details column: {data_type}({max_length})")
            
            if data_type == 'character varying' and max_length == 100:
                print(f"[{datetime.now()}] ❌ Found problematic VARCHAR(100) column")
                print(f"[{datetime.now()}] 🔧 Fixing to TEXT...")
                
                # Alter the column to TEXT
                cursor.execute("ALTER TABLE audit_log ALTER COLUMN details TYPE TEXT")
                conn.commit()
                
                print(f"[{datetime.now()}] ✅ Successfully changed details column to TEXT")
                
                # Verify the change
                cursor.execute("""
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'audit_log' AND column_name = 'details'
                """)
                
                new_type = cursor.fetchone()[0]
                print(f"[{datetime.now()}] ✅ Verified: details column is now {new_type}")
                
            elif data_type == 'text':
                print(f"[{datetime.now()}] ✅ Details column is already TEXT - no fix needed")
            else:
                print(f"[{datetime.now()}] ⚠️ Unexpected column type: {data_type}")
        else:
            print(f"[{datetime.now()}] ❌ audit_log table or details column not found")
            
        cursor.close()
        conn.close()
        print(f"[{datetime.now()}] Database connection closed")
        
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error fixing audit log schema: {e}")
        return False
        
    return True

if __name__ == "__main__":
    print("=== Audit Log Schema Fix ===")
    success = fix_audit_log_schema()
    
    if success:
        print("✅ Audit log schema fix completed successfully")
    else:
        print("❌ Audit log schema fix failed")
