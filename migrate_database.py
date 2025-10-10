#!/usr/bin/env python3
"""
Database Migration: Add new fields for English and Chinese names
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app1_production import app, db, Email

def migrate_database():
    """Add new fields to Email table for proper English/Chinese name storage"""
    
    print("🔄 Starting database migration for enhanced alleged subject storage...")
    
    with app.app_context():
        try:
            # Check if new columns exist
            from sqlalchemy import text
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('email')]
            
            print(f"📋 Current email table columns: {len(columns)} columns")
            
            # Add new columns if they don't exist
            new_columns_added = 0
            
            if 'alleged_subject_english' not in columns:
                with db.engine.connect() as connection:
                    connection.execute(text('ALTER TABLE email ADD COLUMN alleged_subject_english VARCHAR(500)'))
                    connection.commit()
                print("✅ Added alleged_subject_english column")
                new_columns_added += 1
            
            if 'alleged_subject_chinese' not in columns:
                with db.engine.connect() as connection:
                    connection.execute(text('ALTER TABLE email ADD COLUMN alleged_subject_chinese VARCHAR(500)'))
                    connection.commit()
                print("✅ Added alleged_subject_chinese column")
                new_columns_added += 1
            
            if 'license_numbers_json' not in columns:
                with db.engine.connect() as connection:
                    connection.execute(text('ALTER TABLE email ADD COLUMN license_numbers_json TEXT'))
                    connection.commit()
                print("✅ Added license_numbers_json column")
                new_columns_added += 1
            
            if 'intermediary_types_json' not in columns:
                with db.engine.connect() as connection:
                    connection.execute(text('ALTER TABLE email ADD COLUMN intermediary_types_json TEXT'))
                    connection.commit()
                print("✅ Added intermediary_types_json column")
                new_columns_added += 1
            
            if 'allegation_summary' not in columns:
                with db.engine.connect() as connection:
                    connection.execute(text('ALTER TABLE email ADD COLUMN allegation_summary TEXT'))
                    connection.commit()
                print("✅ Added allegation_summary column")
                new_columns_added += 1
            
            if 'ai_analysis_summary' not in columns:
                with db.engine.connect() as connection:
                    connection.execute(text('ALTER TABLE email ADD COLUMN ai_analysis_summary TEXT'))
                    connection.commit()
                print("✅ Added ai_analysis_summary column")
                new_columns_added += 1
            
            if new_columns_added > 0:
                print(f"✅ Added {new_columns_added} new columns to email table")
            else:
                print("ℹ️ All columns already exist")
            
            # Migrate existing data from alleged_subject to new fields
            emails_with_subjects = Email.query.filter(Email.alleged_subject.isnot(None)).all()
            migrated_count = 0
            
            for email in emails_with_subjects:
                if email.alleged_subject and not email.alleged_subject_english and not email.alleged_subject_chinese:
                    # Parse existing alleged_subject field
                    subject_text = email.alleged_subject
                    
                    # Check if it contains Chinese characters and parentheses pattern
                    import re
                    
                    # Pattern for "English (Chinese)" format
                    pattern = r'([^(]+)\s*\(([^)]+)\)'
                    matches = re.findall(pattern, subject_text)
                    
                    english_names = []
                    chinese_names = []
                    
                    if matches:
                        # Found "English (Chinese)" patterns
                        for match in matches:
                            english_part = match[0].strip()
                            chinese_part = match[1].strip()
                            
                            # Check if chinese_part contains Chinese characters
                            if re.search(r'[\u4e00-\u9fff]', chinese_part):
                                english_names.append(english_part)
                                chinese_names.append(chinese_part)
                            else:
                                # Both parts are probably English
                                english_names.append(f"{english_part} ({chinese_part})")
                        
                        # Handle remaining text not in parentheses
                        remaining_text = re.sub(pattern, '', subject_text)
                        remaining_parts = [part.strip() for part in remaining_text.split(',') if part.strip()]
                        english_names.extend(remaining_parts)
                    else:
                        # No parentheses pattern, split by commas and check each part
                        parts = [part.strip() for part in subject_text.split(',') if part.strip()]
                        for part in parts:
                            if re.search(r'[\u4e00-\u9fff]', part):
                                chinese_names.append(part)
                            else:
                                english_names.append(part)
                    
                    # Update the email with separated names
                    if english_names:
                        email.alleged_subject_english = ', '.join(english_names)
                    if chinese_names:
                        email.alleged_subject_chinese = ', '.join(chinese_names)
                    
                    migrated_count += 1
                    
                    if migrated_count % 10 == 0:
                        print(f"📊 Migrated {migrated_count} emails...")
            
            db.session.commit()
            
            print(f"✅ Migration completed successfully!")
            print(f"📊 Summary:")
            print(f"   • New columns added: {new_columns_added}")
            print(f"   • Emails migrated: {migrated_count}")
            print(f"   • Total emails in database: {Email.query.count()}")
            
            # Show sample of migrated data
            sample_emails = Email.query.filter(
                Email.alleged_subject_english.isnot(None) | 
                Email.alleged_subject_chinese.isnot(None)
            ).limit(5).all()
            
            if sample_emails:
                print(f"\n📋 Sample migrated data:")
                for email in sample_emails:
                    print(f"   ID {email.id}: EN='{email.alleged_subject_english}' CN='{email.alleged_subject_chinese}'")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🗄️ Database Migration for Enhanced Alleged Subject Storage")
    print("=" * 60)
    
    success = migrate_database()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("✅ Your platform now supports:")
        print("   • Separate English and Chinese name storage")
        print("   • Multiple license numbers per person")  
        print("   • Improved data structure for alleged subjects")
        print("\n🚀 You can now use the enhanced assessment form!")
    else:
        print("\n💥 Migration failed. Please check the errors above.")
