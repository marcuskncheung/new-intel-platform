#!/usr/bin/env python3
"""
Add missing received_by_hand_id column to case_profile table
This fixes the error: column case_profile.received_by_hand_id does not exist
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app1_production import db
import psycopg2
from secure_config_loader import load_config

def add_received_by_hand_column():
    """Add the missing received_by_hand_id column to case_profile table"""
    
    config = load_config()
    
    # Connect directly to PostgreSQL
    conn = psycopg2.connect(
        host=config['host'],
        database=config['database'], 
        user=config['user'],
        password=config['password'],
        port=config.get('port', 5432)
    )
    
    cursor = conn.cursor()
    
    try:
        print("🔍 Checking if received_by_hand_id column exists...")
        
        # Check if column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'case_profile' 
            AND column_name = 'received_by_hand_id'
        """)
        
        exists = cursor.fetchone()
        
        if exists:
            print("✅ Column received_by_hand_id already exists in case_profile table")
            return
        
        print("❌ Column received_by_hand_id does not exist. Adding it now...")
        
        # Add the missing column
        cursor.execute("""
            ALTER TABLE case_profile 
            ADD COLUMN received_by_hand_id INTEGER 
            REFERENCES received_by_hand_entry(id)
        """)
        
        # Create index for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_case_profile_received_by_hand_id 
            ON case_profile(received_by_hand_id)
        """)
        
        conn.commit()
        print("✅ Successfully added received_by_hand_id column to case_profile table")
        
        # Verify the column was added
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'case_profile' 
            AND column_name = 'received_by_hand_id'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"✅ Verification: Column {result[0]} ({result[1]}, nullable: {result[2]}) exists")
        else:
            print("❌ Verification failed: Column not found after creation")
            
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("🚀 Starting migration to add received_by_hand_id column...")
    add_received_by_hand_column()
    print("🎉 Migration completed successfully!")
