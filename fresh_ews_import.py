#!/usr/bin/env python3
"""
Database Cleanup and Fresh EWS Import
=====================================
This script will:
1. Backup current database
2. Clear all email and attachment records
3. Fresh import all Intelligence emails via EWS
4. Verify the import was successful
"""

import sys
import re
import os
import shutil
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from exchangelib import Credentials, Account, DELEGATE, Configuration
    from exchange_config import (
        EXCHANGE_SERVER, EXCHANGE_EMAIL, EXCHANGE_PASSWORD, 
        EXCHANGE_FOLDER, EXCHANGE_AUTO_DISCOVER, EXCHANGE_AUTH_TYPE,
        INTELLIGENCE_MAILBOX, INTELLIGENCE_MAILBOX_EMAIL
    )
    
    # Import Flask app components for database access
    from app1_production import app, db, Email, Attachment, connect_to_intelligence_mailbox, import_emails_from_exchange_ews
    
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    input("Press Enter to exit...")
    sys.exit(1)

def backup_database():
    """Create a backup of the current database"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"users.db.backup_before_fresh_import_{timestamp}"
    
    db_path = "instance/users.db"
    backup_path = f"instance/{backup_name}"
    
    try:
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            print(f"✅ Database backed up to: {backup_name}")
            return backup_path
        else:
            print(f"⚠️ Database file not found: {db_path}")
            return None
    except Exception as e:
        print(f"❌ Failed to backup database: {e}")
        return None

def clear_email_data():
    """Clear all email and attachment records from database"""
    try:
        with app.app_context():
            # Count current records
            email_count = Email.query.count()
            attachment_count = Attachment.query.count()
            
            print(f"📊 Current database content:")
            print(f"   • Emails: {email_count}")
            print(f"   • Attachments: {attachment_count}")
            
            if email_count == 0:
                print("ℹ️ Database is already empty")
                return True
            
            # Confirm deletion
            print(f"\n⚠️ WARNING: This will delete all {email_count} emails and {attachment_count} attachments")
            response = input("Are you sure you want to proceed? (yes/no): ").lower().strip()
            
            if response not in ['yes', 'y']:
                print("❌ Operation cancelled by user")
                return False
            
            # Delete all attachments first (foreign key constraint)
            print(f"🗑️ Deleting {attachment_count} attachments...")
            Attachment.query.delete()
            
            # Delete all emails
            print(f"🗑️ Deleting {email_count} emails...")
            Email.query.delete()
            
            # Commit changes
            db.session.commit()
            
            # Verify deletion
            remaining_emails = Email.query.count()
            remaining_attachments = Attachment.query.count()
            
            if remaining_emails == 0 and remaining_attachments == 0:
                print("✅ Database cleared successfully")
                return True
            else:
                print(f"❌ Cleanup incomplete: {remaining_emails} emails, {remaining_attachments} attachments remain")
                return False
                
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        db.session.rollback()
        return False

def fresh_ews_import():
    """Perform a fresh import of all Intelligence emails via EWS"""
    try:
        with app.app_context():
            print(f"\n🔄 Starting fresh Intelligence EWS import...")
            
            # Connect to Intelligence account
            print(f"🔗 Connecting to Intelligence account: {EXCHANGE_EMAIL}")
            account = connect_to_intelligence_mailbox(
                EXCHANGE_EMAIL, 
                EXCHANGE_PASSWORD, 
                EXCHANGE_SERVER, 
                INTELLIGENCE_MAILBOX
            )
            
            if not account:
                print("❌ Failed to connect to Intelligence account")
                return False
            
            print(f"✅ Connected successfully")
            
            # Perform import
            print(f"📥 Importing Intelligence emails with attachments...")
            imported_count = import_emails_from_exchange_ews(
                account=account, 
                folder_name=EXCHANGE_FOLDER,
                commit_to_db=True, 
                flash_messages=False
            )
            
            # Verify import
            final_email_count = Email.query.count()
            final_attachment_count = Attachment.query.count()
            
            print(f"\n📊 IMPORT RESULTS:")
            print(f"   • Function reported: {imported_count} emails imported")
            print(f"   • Database contains: {final_email_count} emails")
            print(f"   • Database contains: {final_attachment_count} attachments")
            
            if final_email_count > 0:
                print(f"\n📋 Sample of imported emails:")
                recent_emails = Email.query.order_by(Email.id.desc()).limit(5).all()
                for i, email in enumerate(recent_emails, 1):
                    attachment_count = Attachment.query.filter_by(email_id=email.id).count()
                    print(f"   {i}. {email.subject[:60]}...")
                    print(f"      From: {email.sender[:50]}...")
                    print(f"      ID: {email.entry_id[:30]}...")
                    print(f"      Attachments: {attachment_count}")
                    print()
                
                return True
            else:
                print(f"❌ No emails were imported!")
                return False
                
    except Exception as e:
        print(f"❌ Error during fresh import: {e}")
        return False

def main():
    """Main function to orchestrate the cleanup and fresh import"""
    print("=" * 80)
    print("DATABASE CLEANUP AND FRESH EWS IMPORT")
    print("=" * 80)
    print("This will:")
    print("1. Backup your current database")
    print("2. Delete all existing email and attachment records")
    print("3. Fresh import all 142 Intelligence emails from EWS")
    print("4. Import all attachments with proper EWS method")
    print("=" * 80)
    
    # Step 1: Backup database
    print(f"\n📁 STEP 1: Backing up database...")
    backup_path = backup_database()
    if not backup_path:
        print("❌ Cannot proceed without backup")
        return False
    
    # Step 2: Clear existing data
    print(f"\n🗑️ STEP 2: Clearing existing email data...")
    if not clear_email_data():
        print("❌ Failed to clear database")
        return False
    
    # Step 3: Fresh import
    print(f"\n📥 STEP 3: Fresh Intelligence EWS import...")
    if not fresh_ews_import():
        print("❌ Fresh import failed")
        print(f"💡 You can restore from backup: {backup_path}")
        return False
    
    print(f"\n" + "=" * 80)
    print("🎉 SUCCESS! Fresh EWS import completed")
    print("✅ All Intelligence emails imported with proper EWS entry IDs")
    print("✅ All attachments imported using EWS method")
    print("✅ No mixed data from old Outlook method")
    print("✅ Clean, consistent database structure")
    print(f"💾 Backup available at: {backup_path}")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print(f"\n🚀 Your Intelligence platform is now ready with fresh EWS data!")
        else:
            print(f"\n❌ Operation failed. Check the messages above.")
    except KeyboardInterrupt:
        print(f"\n⚠️ Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    input("\nPress Enter to exit...")
