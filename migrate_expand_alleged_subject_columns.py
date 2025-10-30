#!/usr/bin/env python3
"""
🔧 DATABASE MIGRATION: Expand alleged_subject columns from VARCHAR to TEXT

Problem:
- alleged_subject: VARCHAR(255) → TOO SHORT for multiple names
- alleged_subject_english: VARCHAR(500) → TOO SHORT for company names
- alleged_subject_chinese: VARCHAR(500) → TOO SHORT for Chinese names

Solution:
- Change all three columns to TEXT (unlimited length)

Run this ONCE after deploying the code changes.
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not set")
    print("Set it with: export DATABASE_URL='postgresql://user:pass@host:port/dbname'")
    sys.exit(1)

print("="*80)
print("🔧 DATABASE MIGRATION: Expand alleged_subject columns to TEXT")
print("="*80)
print(f"Database: {DATABASE_URL.split('@')[-1]}")  # Hide credentials

engine = create_engine(DATABASE_URL)

# SQL migration queries
migrations = [
    {
        'name': 'Expand email.alleged_subject to TEXT',
        'sql': 'ALTER TABLE email ALTER COLUMN alleged_subject TYPE TEXT;'
    },
    {
        'name': 'Expand email.alleged_subject_english to TEXT',
        'sql': 'ALTER TABLE email ALTER COLUMN alleged_subject_english TYPE TEXT;'
    },
    {
        'name': 'Expand email.alleged_subject_chinese to TEXT',
        'sql': 'ALTER TABLE email ALTER COLUMN alleged_subject_chinese TYPE TEXT;'
    }
]

try:
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        for migration in migrations:
            print(f"\n📝 {migration['name']}")
            print(f"   SQL: {migration['sql']}")
            
            try:
                conn.execute(text(migration['sql']))
                print("   ✅ Success")
            except Exception as e:
                if 'does not exist' in str(e) or 'cannot alter type' in str(e):
                    print(f"   ⚠️  Already migrated or column doesn't exist: {e}")
                else:
                    raise e
        
        # Commit transaction
        trans.commit()
        print("\n" + "="*80)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY")
        print("="*80)
        print("📊 Column types updated:")
        print("   - alleged_subject: VARCHAR(255) → TEXT")
        print("   - alleged_subject_english: VARCHAR(500) → TEXT")
        print("   - alleged_subject_chinese: VARCHAR(500) → TEXT")
        print("\n💡 You can now store unlimited names in these fields!")
        
except Exception as e:
    print(f"\n❌ MIGRATION FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n🔄 Next steps:")
print("1. Restart the Docker containers: docker-compose restart intelligence-app")
print("2. Test the assessment update with multiple names")
print("3. Verify the renumber function works correctly")
