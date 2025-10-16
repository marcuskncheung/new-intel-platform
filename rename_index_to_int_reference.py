#!/usr/bin/env python3
"""
Database migration: Rename CaseProfile.index to CaseProfile.int_reference

This fixes the naming conflict where Python's built-in list.index() method
was being called instead of accessing the column value.

Run this ONCE before deploying the updated code.
"""
import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app1_production import app, db
from sqlalchemy import text

def rename_column():
    """Rename the 'index' column to 'int_reference' in case_profile table"""
    with app.app_context():
        try:
            print("=" * 80)
            print("🔄 DATABASE MIGRATION: Rename case_profile.index → int_reference")
            print("=" * 80)
            
            # Check database type
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            is_postgres = db_uri.startswith('postgresql')
            is_sqlite = db_uri.startswith('sqlite')
            
            print(f"\n📊 Database Type: {'PostgreSQL' if is_postgres else 'SQLite'}")
            
            # Test if column exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('case_profile')]
            
            print(f"\n📋 Current columns in case_profile:")
            for col in columns:
                print(f"   - {col}")
            
            if 'int_reference' in columns:
                print("\n✅ Column already renamed! Nothing to do.")
                return
            
            if 'index' not in columns:
                print("\n❌ ERROR: 'index' column not found in case_profile table!")
                return
            
            print("\n⚠️  This will rename the 'index' column to 'int_reference'")
            response = input("\nProceed with migration? (yes/no): ").strip().lower()
            if response != 'yes':
                print("❌ Aborted. No changes made.")
                return
            
            # Perform the rename based on database type
            if is_postgres:
                print("\n🔄 Renaming column in PostgreSQL...")
                db.session.execute(text(
                    'ALTER TABLE case_profile RENAME COLUMN "index" TO int_reference'
                ))
                db.session.commit()
                print("✅ Column renamed successfully!")
                
            elif is_sqlite:
                print("\n🔄 Renaming column in SQLite...")
                # SQLite requires table recreation for column rename
                db.session.execute(text('''
                    CREATE TABLE case_profile_new (
                        id INTEGER PRIMARY KEY,
                        int_reference VARCHAR(20) UNIQUE NOT NULL,
                        index_order INTEGER UNIQUE NOT NULL,
                        date_of_receipt DATETIME NOT NULL,
                        source_type VARCHAR(20) NOT NULL,
                        email_id INTEGER UNIQUE,
                        whatsapp_id INTEGER UNIQUE,
                        patrol_id INTEGER UNIQUE,
                        source VARCHAR(255),
                        case_status VARCHAR(255),
                        case_number VARCHAR(255),
                        alleged_subject_en VARCHAR(255),
                        alleged_subject_cn VARCHAR(255),
                        agent_number VARCHAR(255),
                        agent_company_broker VARCHAR(255),
                        alleged_misconduct_type VARCHAR(255),
                        description_of_incident TEXT,
                        created_at DATETIME,
                        updated_at DATETIME,
                        created_by VARCHAR(100),
                        similarity_checked BOOLEAN,
                        duplicate_of_id INTEGER,
                        FOREIGN KEY(email_id) REFERENCES email(id),
                        FOREIGN KEY(whatsapp_id) REFERENCES whats_app_entry(id),
                        FOREIGN KEY(patrol_id) REFERENCES online_patrol_entry(id),
                        FOREIGN KEY(duplicate_of_id) REFERENCES case_profile(id)
                    )
                '''))
                
                # Copy data from old table to new table
                db.session.execute(text('''
                    INSERT INTO case_profile_new 
                    SELECT 
                        id, "index" as int_reference, index_order, date_of_receipt, 
                        source_type, email_id, whatsapp_id, patrol_id, source,
                        case_status, case_number, alleged_subject_en, alleged_subject_cn,
                        agent_number, agent_company_broker, alleged_misconduct_type,
                        description_of_incident, created_at, updated_at, created_by,
                        similarity_checked, duplicate_of_id
                    FROM case_profile
                '''))
                
                # Drop old table and rename new one
                db.session.execute(text('DROP TABLE case_profile'))
                db.session.execute(text('ALTER TABLE case_profile_new RENAME TO case_profile'))
                
                # Recreate indexes
                db.session.execute(text('CREATE UNIQUE INDEX ix_case_profile_int_reference ON case_profile(int_reference)'))
                db.session.execute(text('CREATE UNIQUE INDEX ix_case_profile_index_order ON case_profile(index_order)'))
                db.session.execute(text('CREATE INDEX ix_case_profile_date_of_receipt ON case_profile(date_of_receipt)'))
                db.session.execute(text('CREATE INDEX ix_case_profile_source_type ON case_profile(source_type)'))
                
                db.session.commit()
                print("✅ Column renamed successfully!")
            else:
                print("❌ ERROR: Unknown database type!")
                return
            
            # Verify the change
            inspector = db.inspect(db.engine)
            new_columns = [col['name'] for col in inspector.get_columns('case_profile')]
            
            print(f"\n📋 Updated columns in case_profile:")
            for col in new_columns:
                print(f"   - {col}")
            
            if 'int_reference' in new_columns and 'index' not in new_columns:
                print("\n✅ Migration completed successfully!")
                print("🔄 Please restart your application to use the updated schema.")
            else:
                print("\n⚠️  WARNING: Column may not have been renamed properly!")
                
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    rename_column()
