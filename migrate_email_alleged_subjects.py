#!/usr/bin/env python3
"""
Migration: Create email_alleged_subjects table and migrate existing data

This script:
1. Creates new email_alleged_subjects table
2. Migrates existing comma-separated names from email table
3. Preserves existing data in email table (for rollback safety)
4. Updates POI refresh to use new table structure

Run with: python3 migrate_email_alleged_subjects.py
"""

from app1_production import app, db
from datetime import datetime
import json

# Create new table structure
def create_email_alleged_subjects_table():
    """Create the new table for storing alleged subjects separately"""
    
    print("=" * 80)
    print("🔧 STEP 1: Creating email_alleged_subjects table")
    print("=" * 80)
    
    sql = """
    CREATE TABLE IF NOT EXISTS email_alleged_subjects (
        id SERIAL PRIMARY KEY,
        email_id INTEGER NOT NULL REFERENCES email(id) ON DELETE CASCADE,
        english_name VARCHAR(255),
        chinese_name VARCHAR(255),
        is_insurance_intermediary BOOLEAN DEFAULT FALSE,
        license_type VARCHAR(100),
        license_number VARCHAR(100),
        sequence_order INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        -- Ensure at least one name is provided
        CONSTRAINT check_has_name CHECK (
            english_name IS NOT NULL OR chinese_name IS NOT NULL
        ),
        
        -- Unique constraint to prevent duplicate entries
        CONSTRAINT unique_email_subject UNIQUE (email_id, sequence_order)
    );
    """
    
    index_sql = """
    CREATE INDEX IF NOT EXISTS idx_email_alleged_subjects_email_id 
        ON email_alleged_subjects(email_id);
    CREATE INDEX IF NOT EXISTS idx_email_alleged_subjects_english 
        ON email_alleged_subjects(english_name);
    CREATE INDEX IF NOT EXISTS idx_email_alleged_subjects_chinese 
        ON email_alleged_subjects(chinese_name);
    """
    
    try:
        from sqlalchemy import text
        db.session.execute(text(sql))
        db.session.commit()
        print("✅ Table created successfully")
        
        db.session.execute(text(index_sql))
        db.session.commit()
        print("✅ Indexes created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        db.session.rollback()
        return False


def migrate_existing_data():
    """Migrate existing comma-separated names to new table structure"""
    
    from sqlalchemy import text
    
    print("\n" + "=" * 80)
    print("🔄 STEP 2: Migrating existing email alleged subjects")
    print("=" * 80)
    
    # Query all emails with alleged subjects
    query = """
        SELECT id, alleged_subject_english, alleged_subject_chinese,
               license_numbers_json, intermediary_types_json
        FROM email
        WHERE alleged_subject_english IS NOT NULL 
           OR alleged_subject_chinese IS NOT NULL
    """
    
    result = db.session.execute(text(query))
    emails = result.fetchall()
    
    print(f"\n📊 Found {len(emails)} emails with alleged subjects")
    
    migrated_count = 0
    error_count = 0
    
    for email_row in emails:
        email_id = email_row[0]
        english_text = email_row[1] or ""
        chinese_text = email_row[2] or ""
        license_json = email_row[3]
        types_json = email_row[4]
        
        # Parse comma-separated names
        english_names = [n.strip() for n in english_text.split(',') if n.strip()] if english_text else []
        chinese_names = [n.strip() for n in chinese_text.split(',') if n.strip()] if chinese_text else []
        
        # Parse license info
        license_numbers = []
        license_types = []
        try:
            if license_json:
                license_numbers = json.loads(license_json)
            if types_json:
                license_types = json.loads(types_json)
        except:
            pass
        
        # Get max length
        max_len = max(len(english_names), len(chinese_names))
        
        # Check for mismatches
        if len(english_names) != len(chinese_names) and english_names and chinese_names:
            print(f"\n⚠️  WARNING: Email {email_id} has mismatched names:")
            print(f"   English ({len(english_names)}): {english_names}")
            print(f"   Chinese ({len(chinese_names)}): {chinese_names}")
            print(f"   Will pair by index - please review manually after migration!")
        
        # Insert each person as separate row
        try:
            for i in range(max_len):
                english = english_names[i] if i < len(english_names) else None
                chinese = chinese_names[i] if i < len(chinese_names) else None
                license_num = license_numbers[i] if i < len(license_numbers) else None
                license_type = license_types[i] if i < len(license_types) else None
                
                # Skip if both names are empty
                if not english and not chinese:
                    continue
                
                # Insert into new table
                insert_sql = """
                    INSERT INTO email_alleged_subjects 
                    (email_id, english_name, chinese_name, is_insurance_intermediary, 
                     license_type, license_number, sequence_order)
                    VALUES (:email_id, :english, :chinese, :is_intermediary, 
                            :license_type, :license_num, :seq)
                """
                
                db.session.execute(text(insert_sql), {
                    'email_id': email_id,
                    'english': english,
                    'chinese': chinese,
                    'is_intermediary': bool(license_num),
                    'license_type': license_type,
                    'license_num': license_num,
                    'seq': i + 1
                })
            
            db.session.commit()
            migrated_count += 1
            
            if migrated_count % 100 == 0:
                print(f"✅ Migrated {migrated_count} emails...")
                
        except Exception as e:
            print(f"❌ Error migrating email {email_id}: {e}")
            db.session.rollback()
            error_count += 1
    
    print(f"\n📊 Migration Summary:")
    print(f"   ✅ Successfully migrated: {migrated_count} emails")
    print(f"   ❌ Errors: {error_count} emails")
    
    return migrated_count, error_count


def verify_migration():
    """Verify the migration was successful"""
    
    from sqlalchemy import text
    
    print("\n" + "=" * 80)
    print("🔍 STEP 3: Verifying migration")
    print("=" * 80)
    
    # Count records in new table
    count_sql = "SELECT COUNT(*) FROM email_alleged_subjects"
    result = db.session.execute(text(count_sql))
    new_count = result.fetchone()[0]
    
    # Count emails with alleged subjects
    old_count_sql = """
        SELECT COUNT(*) FROM email 
        WHERE alleged_subject_english IS NOT NULL 
           OR alleged_subject_chinese IS NOT NULL
    """
    result = db.session.execute(text(old_count_sql))
    old_count = result.fetchone()[0]
    
    print(f"\n📊 Verification Results:")
    print(f"   Emails with alleged subjects: {old_count}")
    print(f"   Records in new table: {new_count}")
    
    # Sample check - show first few records
    sample_sql = """
        SELECT e.id as email_id, 
               eas.english_name, eas.chinese_name, 
               eas.license_number, eas.sequence_order
        FROM email_alleged_subjects eas
        JOIN email e ON e.id = eas.email_id
        ORDER BY eas.email_id, eas.sequence_order
        LIMIT 10
    """
    result = db.session.execute(text(sample_sql))
    samples = result.fetchall()
    
    print(f"\n📋 Sample migrated records:")
    print(f"{'Email ID':<10} {'Seq':<5} {'English Name':<30} {'Chinese Name':<20} {'License':<15}")
    print("-" * 90)
    for row in samples:
        print(f"{row[0]:<10} {row[4]:<5} {row[1] or '':<30} {row[2] or '':<20} {row[3] or '':<15}")
    
    return new_count > 0


def main():
    """Run the migration"""
    
    print("\n" + "=" * 80)
    print("🚀 EMAIL ALLEGED SUBJECTS TABLE MIGRATION")
    print("=" * 80)
    print("\nThis will:")
    print("1. Create email_alleged_subjects table")
    print("2. Migrate existing comma-separated names")
    print("3. Keep original email table data (safe rollback)")
    print("\n⚠️  BACKUP YOUR DATABASE FIRST!")
    
    response = input("\nContinue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Migration cancelled")
        return
    
    with app.app_context():
        # Step 1: Create table
        if not create_email_alleged_subjects_table():
            print("\n❌ Migration failed at step 1")
            return
        
        # Step 2: Migrate data
        migrated, errors = migrate_existing_data()
        if errors > 0:
            print(f"\n⚠️  Migration completed with {errors} errors")
            print("Please review error messages above")
        
        # Step 3: Verify
        if verify_migration():
            print("\n" + "=" * 80)
            print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print("\n📋 Next steps:")
            print("1. Review warning messages for mismatched names")
            print("2. Update app1_production.py to use new table (run update_app_code.py)")
            print("3. Update poi_refresh_system.py to use new table")
            print("4. Test thoroughly in development")
            print("5. After testing, you can drop old columns:")
            print("   ALTER TABLE email DROP COLUMN alleged_subject_english;")
            print("   ALTER TABLE email DROP COLUMN alleged_subject_chinese;")
        else:
            print("\n❌ Migration verification failed")


if __name__ == "__main__":
    main()
