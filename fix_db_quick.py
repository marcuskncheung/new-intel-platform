#!/usr/bin/env python3
"""
Quick fix for missing received_by_hand_id column
Run this on the server to fix the database error
Uses the existing Flask app infrastructure - no separate password needed!
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app and db - this uses the existing configuration
from app1_production import app, db

def fix_database():
    """Fix the missing received_by_hand_id column using Flask app context"""
    
    print("🔧 Using Flask app database connection...")
    
    with app.app_context():
        try:
            # Check if column exists using SQLAlchemy
            result = db.engine.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'case_profile' 
                AND column_name = 'received_by_hand_id'
            """)
            
            exists = result.fetchone()
            
            if exists:
                print("✅ Column received_by_hand_id already exists")
            else:
                print("❌ Column missing. Adding now...")
                
                # Add the missing column using SQLAlchemy
                db.engine.execute("""
                    ALTER TABLE case_profile 
                    ADD COLUMN received_by_hand_id INTEGER 
                    REFERENCES received_by_hand_entry(id)
                """)
                
                # Create index
                db.engine.execute("""
                    CREATE INDEX IF NOT EXISTS idx_case_profile_received_by_hand_id 
                    ON case_profile(received_by_hand_id)
                """)
                
                print("✅ Successfully added received_by_hand_id column")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("🚀 Fixing database schema...")
    if fix_database():
        print("🎉 Database fix completed!")
    else:
        print("💥 Database fix failed!")
        sys.exit(1)
