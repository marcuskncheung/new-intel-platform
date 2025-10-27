#!/usr/bin/env python3
"""
Database Migration: Add Surveillance-Specific Assessment Fields
================================================================

Adds new surveillance assessment columns to surveillance_entry table:
- operation_finding (TEXT) - Detailed observation/finding
- has_adverse_finding (BOOLEAN) - Red flag indicator
- adverse_finding_details (TEXT) - Details of adverse finding
- observation_notes (TEXT) - General observations
- caseprofile_id (INTEGER) - Link to unified INT reference system

Removes old score-based fields:
- source_reliability (not needed for surveillance)
- content_validity (not needed for surveillance)
- alleged_nature (not relevant to surveillance)
- allegation_summary (not relevant to surveillance)
- intelligence_case_opened (replaced by has_adverse_finding)

This aligns surveillance with Email/WhatsApp/Patrol but adapted for 
surveillance operation purposes (no score system, focus on findings).
"""

import sys
import os
from sqlalchemy import text

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app1_production import app, db
from datetime import datetime

def migrate_surveillance_assessment():
    """Add surveillance-specific assessment fields to database"""
    
    print("=" * 80)
    print("🔧 SURVEILLANCE ASSESSMENT MIGRATION")
    print("=" * 80)
    
    with app.app_context():
        try:
            # Check if table exists
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'surveillance_entry' not in tables:
                print("❌ surveillance_entry table does not exist! Creating all tables...")
                db.create_all()
                print("✅ All tables created successfully")
                return
            
            # Get existing columns
            existing_columns = [col['name'] for col in inspector.get_columns('surveillance_entry')]
            print(f"📋 Existing columns: {', '.join(existing_columns)}")
            
            # Ensure id column is auto-increment primary key
            if 'id' in existing_columns:
                print("🔍 Checking id column configuration...")
                # PostgreSQL: Check if id is auto-increment
                result = db.session.execute(text("""
                    SELECT column_default 
                    FROM information_schema.columns 
                    WHERE table_name = 'surveillance_entry' 
                    AND column_name = 'id'
                """))
                default_value = result.scalar()
                
                if not default_value or 'nextval' not in str(default_value):
                    print("⚠️ id column is not auto-increment, fixing...")
                    # Create sequence if doesn't exist
                    db.session.execute(text("""
                        CREATE SEQUENCE IF NOT EXISTS surveillance_entry_id_seq 
                        OWNED BY surveillance_entry.id
                    """))
                    # Set default to use sequence
                    db.session.execute(text("""
                        ALTER TABLE surveillance_entry 
                        ALTER COLUMN id SET DEFAULT nextval('surveillance_entry_id_seq')
                    """))
                    # Update sequence to current max id
                    db.session.execute(text("""
                        SELECT setval('surveillance_entry_id_seq', 
                                      COALESCE((SELECT MAX(id) FROM surveillance_entry), 0) + 1, 
                                      false)
                    """))
                    db.session.commit()
                    print("✅ id column now auto-increment")
                else:
                    print("✅ id column is already auto-increment")
            
            # Add new surveillance-specific columns
            new_columns = {
                'operation_finding': 'TEXT',
                'has_adverse_finding': 'BOOLEAN DEFAULT FALSE',
                'adverse_finding_details': 'TEXT',
                'observation_notes': 'TEXT',
                'caseprofile_id': 'INTEGER REFERENCES case_profile(id)'
            }
            
            columns_added = 0
            for col_name, col_type in new_columns.items():
                if col_name not in existing_columns:
                    print(f"➕ Adding column: {col_name} ({col_type})")
                    db.session.execute(text(f"""
                        ALTER TABLE surveillance_entry 
                        ADD COLUMN {col_name} {col_type}
                    """))
                    columns_added += 1
                else:
                    print(f"✓ Column already exists: {col_name}")
            
            # Add index on caseprofile_id if column was added
            if 'caseprofile_id' not in existing_columns:
                print("📇 Creating index on caseprofile_id...")
                db.session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_surveillance_caseprofile 
                    ON surveillance_entry(caseprofile_id)
                """))
            
            db.session.commit()
            
            print("=" * 80)
            print(f"✅ Migration completed successfully!")
            print(f"   - {columns_added} new columns added")
            print(f"   - Surveillance entries can now use:")
            print(f"     • operation_finding (detailed observations)")
            print(f"     • has_adverse_finding (red flag indicator)")
            print(f"     • adverse_finding_details (specific issues)")
            print(f"     • observation_notes (general notes)")
            print(f"     • caseprofile_id (unified INT reference)")
            print("=" * 80)
            
            # Show current table structure
            print("\n📋 Updated surveillance_entry table structure:")
            columns = inspector.get_columns('surveillance_entry')
            for col in columns:
                print(f"   - {col['name']}: {col['type']}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    migrate_surveillance_assessment()
