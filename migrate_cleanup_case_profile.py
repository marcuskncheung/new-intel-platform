#!/usr/bin/env python3
"""
Migration script to remove unused columns from case_profile table.

These columns were never properly populated and just caused confusion:
- source (legacy - empty)
- case_status (legacy - status is on source tables)
- case_number (legacy - barely used)
- alleged_subject_en (never synced with source)
- alleged_subject_cn (never synced with source)
- agent_number (never synced with source)
- agent_company_broker (never synced with source)
- alleged_misconduct_type (never synced with source)
- description_of_incident (never synced with source)
- similarity_checked (never used)
- duplicate_of_id (never used for CaseProfile)
"""

import os
import sys

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://intel_user:intel_password@localhost:5432/intelligence_db')

COLUMNS_TO_DROP = [
    'source',
    'case_status',
    'case_number',
    'alleged_subject_en',
    'alleged_subject_cn',
    'agent_number',
    'agent_company_broker',
    'alleged_misconduct_type',
    'description_of_incident',
    'similarity_checked',
    'duplicate_of_id',
]

def run_migration():
    """Drop unused columns from case_profile table"""
    import psycopg2
    
    print("=" * 60)
    print("Migration: Remove unused columns from case_profile")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check which columns exist
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'case_profile'
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"Existing columns: {existing_columns}")
        
        # Drop each unused column if it exists
        for col in COLUMNS_TO_DROP:
            if col in existing_columns:
                print(f"\n🔄 Dropping column: {col}")
                try:
                    cursor.execute(f"ALTER TABLE case_profile DROP COLUMN IF EXISTS {col} CASCADE")
                    print(f"✅ Dropped: {col}")
                except Exception as e:
                    print(f"⚠️ Could not drop {col}: {e}")
            else:
                print(f"⏭️ Column {col} does not exist, skipping")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("Migration completed!")
        print("=" * 60)
        
        print("\n📋 Remaining case_profile columns should be:")
        print("  - id (Primary Key)")
        print("  - int_reference (INT-XXXX-XXXX)")
        print("  - index_order (for sorting)")
        print("  - date_of_receipt")
        print("  - source_type (EMAIL/WHATSAPP/PATROL/RECEIVED_BY_HAND)")
        print("  - email_id (FK)")
        print("  - whatsapp_id (FK)")
        print("  - patrol_id (FK)")
        print("  - received_by_hand_id (FK)")
        print("  - created_at")
        print("  - updated_at")
        print("  - created_by")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_migration()
