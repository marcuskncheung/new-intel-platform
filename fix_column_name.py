#!/usr/bin/env python3
"""
Quick fix: Rename case_profile.index to case_profile.int_reference in PostgreSQL
Run this inside Docker container: docker-compose exec web python3 fix_column_name.py
"""
import os
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app1_production import app, db
from sqlalchemy import text

def fix_column():
    """Rename the 'index' column to 'int_reference' in case_profile table"""
    with app.app_context():
        try:
            print("=" * 80)
            print("🔄 FIXING: Rename case_profile.index → int_reference")
            print("=" * 80)
            
            # Check database type
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            is_postgres = db_uri.startswith('postgresql')
            
            if not is_postgres:
                print("❌ ERROR: This script is for PostgreSQL only!")
                print(f"   Current DB: {db_uri[:50]}...")
                return
            
            print(f"\n📊 Database Type: PostgreSQL")
            print(f"🔗 Database: {db_uri.split('@')[-1] if '@' in db_uri else 'Unknown'}")
            
            # Check if column exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('case_profile')]
            
            print(f"\n📋 Current columns in case_profile: {len(columns)} total")
            
            if 'int_reference' in columns:
                print("\n✅ SUCCESS: Column already renamed to 'int_reference'!")
                print("   No migration needed. Restart your app.")
                return
            
            if 'index' not in columns:
                print("\n❌ ERROR: 'index' column not found!")
                print(f"   Available columns: {', '.join(columns[:5])}...")
                return
            
            print("\n🔄 Renaming column in PostgreSQL...")
            print("   SQL: ALTER TABLE case_profile RENAME COLUMN \"index\" TO int_reference")
            
            # Execute the rename
            db.session.execute(text(
                'ALTER TABLE case_profile RENAME COLUMN "index" TO int_reference'
            ))
            db.session.commit()
            
            print("\n✅ SUCCESS: Column renamed successfully!")
            print("\n📝 Next steps:")
            print("   1. Restart your application: docker-compose restart web")
            print("   2. Check the /int_source page - it should work now!")
            
            # Verify the change
            inspector = db.inspect(db.engine)
            new_columns = [col['name'] for col in inspector.get_columns('case_profile')]
            
            if 'int_reference' in new_columns and 'index' not in new_columns:
                print("\n✅ VERIFIED: Migration successful!")
                print(f"   Column 'int_reference' now exists")
            else:
                print("\n⚠️  WARNING: Verification failed - check manually")
            
        except Exception as e:
            print(f"\n❌ ERROR during migration: {e}")
            print("\n💡 Troubleshooting:")
            print("   1. Make sure you have database access")
            print("   2. Check database credentials")
            print("   3. Verify PostgreSQL is running")
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DATABASE MIGRATION: Fix column name issue")
    print("=" * 80)
    fix_column()
    print("\n" + "=" * 80)
    print("✅ MIGRATION COMPLETE")
    print("=" * 80 + "\n")
