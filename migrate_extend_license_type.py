#!/usr/bin/env python3
"""
Migration Script: Extend target.license_type column to support new values

This updates the license_type column from VARCHAR(16) to VARCHAR(50)
to support the new options:
- Agent
- Technical Representative (24 characters - was too long for VARCHAR(16))
- Insurer
- Broker
- Others

Run this script ONCE after updating the application code.

Usage:
    python migrate_extend_license_type.py
"""

import os
import sys

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://intel_user:intel_password@localhost:5432/intelligence_db')

def run_migration():
    """Extend license_type column to VARCHAR(50)"""
    import psycopg2
    
    print("=" * 60)
    print("🔧 MIGRATION: Extend license_type column to VARCHAR(50)")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check current column type
        print("\n📋 Checking current column type...")
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'target' AND column_name = 'license_type'
        """)
        result = cursor.fetchone()
        
        if result:
            col_name, data_type, max_length = result
            print(f"   Current: {col_name} {data_type}({max_length})")
            
            if max_length and max_length >= 50:
                print("   ✅ Column is already VARCHAR(50) or larger, no change needed")
            else:
                # Alter the column
                print(f"\n🔄 Altering column from VARCHAR({max_length}) to VARCHAR(50)...")
                cursor.execute("""
                    ALTER TABLE target 
                    ALTER COLUMN license_type TYPE VARCHAR(50)
                """)
                conn.commit()
                print("   ✅ Column successfully altered to VARCHAR(50)")
        else:
            print("   ⚠️ Column 'license_type' not found in 'target' table")
            print("   The column may be created when the app starts")
        
        # Show current valid values
        print("\n📊 Current license_type values in database:")
        cursor.execute("""
            SELECT DISTINCT license_type, COUNT(*) as count
            FROM target
            WHERE license_type IS NOT NULL AND license_type != ''
            GROUP BY license_type
            ORDER BY count DESC
        """)
        rows = cursor.fetchall()
        if rows:
            for license_type, count in rows:
                print(f"   - {license_type}: {count} record(s)")
        else:
            print("   (No license types set yet)")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Migration completed!")
        print("=" * 60)
        print("\nNew valid license types:")
        print("  - Agent")
        print("  - Technical Representative")
        print("  - Insurer")
        print("  - Broker")
        print("  - Others")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
