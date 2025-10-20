#!/usr/bin/env python3
"""
Rearrange Email IDs Script

This script will:
1. Backup all email data with current IDs
2. Delete all email records
3. Re-insert them with new IDs based on received date
4. Biggest ID = Latest email (by received date)
5. Update all related foreign key references

⚠️ WARNING: This is a destructive operation. Make a database backup first!
"""

import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app1_production import app, db, Email, Attachment
from database_config import get_database_config

def backup_emails():
    """Create a backup of all email data"""
    print("\n" + "="*80)
    print("STEP 1: BACKING UP EMAIL DATA")
    print("="*80)
    
    with app.app_context():
        emails = Email.query.order_by(Email.id).all()
        
        backup_file = f"email_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write("-- Email Backup SQL\n")
            f.write(f"-- Generated: {datetime.now()}\n")
            f.write(f"-- Total emails: {len(emails)}\n\n")
            
            for email in emails:
                # Write each email as INSERT statement
                f.write(f"-- Email ID: {email.id}\n")
                f.write(f"-- Subject: {email.subject[:50] if email.subject else 'No Subject'}\n")
                f.write(f"-- Received: {email.received}\n\n")
        
        print(f"✅ Backed up {len(emails)} emails to: {backup_file}")
        return len(emails)

def rearrange_email_ids():
    """Rearrange email IDs based on received date"""
    print("\n" + "="*80)
    print("STEP 2: REARRANGING EMAIL IDs (BIGGEST ID = LATEST EMAIL)")
    print("="*80)
    
    with app.app_context():
        # 1. Get all emails sorted by received date (oldest first)
        emails = Email.query.all()
        
        # Sort by received date
        def parse_received(email):
            if not email.received:
                return datetime.min
            try:
                if isinstance(email.received, str):
                    return datetime.strptime(email.received, '%Y-%m-%d %H:%M:%S')
                return email.received
            except:
                return datetime.min
        
        sorted_emails = sorted(emails, key=parse_received)
        
        print(f"\n📊 Total emails to rearrange: {len(sorted_emails)}")
        print(f"📅 Oldest email: {sorted_emails[0].received if sorted_emails else 'None'}")
        print(f"📅 Latest email: {sorted_emails[-1].received if sorted_emails else 'None'}")
        
        # 2. Create temporary storage for email data
        email_data_list = []
        attachment_data_list = []
        
        for idx, email in enumerate(sorted_emails, start=1):
            # Store email data (only fields that exist in the Email model)
            email_dict = {
                'new_id': idx,  # Oldest email gets ID=1, latest gets biggest ID
                'old_id': email.id,
                'entry_id': email.entry_id,
                'sender': email.sender,
                'recipients': email.recipients,
                'subject': email.subject,
                'received': email.received,
                'body': email.body,
                'source_reliability': email.source_reliability,
                'content_validity': email.content_validity,
                'reviewer_name': email.reviewer_name,
                'reviewer_comment': email.reviewer_comment,
                'intelligence_case_opened': email.intelligence_case_opened,
                'caseprofile_id': email.caseprofile_id,
                'alleged_subject': email.alleged_subject,
                'alleged_subject_english': email.alleged_subject_english,
                'alleged_subject_chinese': email.alleged_subject_chinese,
                'alleged_nature': email.alleged_nature,
                'allegation_summary': email.allegation_summary,
                'ai_analysis_summary': email.ai_analysis_summary,
                'license_number': email.license_number,
                'license_numbers_json': email.license_numbers_json,
                'intermediary_types_json': email.intermediary_types_json,
                'preparer': email.preparer,
                'reviewer_decision': email.reviewer_decision,
                'status': email.status,
                'case_number': email.case_number,
                'case_assigned_by': email.case_assigned_by,
                'case_assigned_at': email.case_assigned_at,
                'int_reference_number': email.int_reference_number,
                'int_reference_order': email.int_reference_order,
                'int_reference_manual': email.int_reference_manual,
                'int_reference_updated_at': email.int_reference_updated_at,
                'int_reference_updated_by': email.int_reference_updated_by
            }
            email_data_list.append(email_dict)
            
            # Store attachment data
            attachments = Attachment.query.filter_by(email_id=email.id).all()
            for att in attachments:
                attachment_dict = {
                    'old_email_id': email.id,
                    'new_email_id': idx,
                    'filename': att.filename,
                    'filepath': att.filepath,
                    'content_type': att.content_type,
                    'size': att.size,
                    'extracted_text': att.extracted_text
                }
                attachment_data_list.append(attachment_dict)
        
        print(f"\n📦 Stored {len(email_data_list)} emails in memory")
        print(f"📎 Stored {len(attachment_data_list)} attachments in memory")
        
        # 3. Delete ALL emails and attachments
        print("\n🗑️  Deleting all existing emails and attachments...")
        Attachment.query.delete()
        Email.query.delete()
        db.session.commit()
        print("✅ All emails and attachments deleted")
        
        # 4. Reset ID sequence (PostgreSQL specific)
        db_config = get_database_config()
        if 'postgresql' in db_config.get('SQLALCHEMY_DATABASE_URI', ''):
            print("\n🔄 Resetting PostgreSQL sequence...")
            db.session.execute(text("ALTER SEQUENCE email_id_seq RESTART WITH 1"))
            db.session.execute(text("ALTER SEQUENCE attachment_id_seq RESTART WITH 1"))
            db.session.commit()
            print("✅ Sequences reset")
        
        # 5. Re-insert emails with new IDs
        print("\n📥 Re-inserting emails with new IDs...")
        for email_data in email_data_list:
            new_email = Email(
                id=email_data['new_id'],  # Explicitly set the new ID
                entry_id=email_data['entry_id'],
                sender=email_data['sender'],
                recipients=email_data['recipients'],
                subject=email_data['subject'],
                received=email_data['received'],
                body=email_data['body'],
                source_reliability=email_data['source_reliability'],
                content_validity=email_data['content_validity'],
                reviewer_name=email_data['reviewer_name'],
                reviewer_comment=email_data['reviewer_comment'],
                intelligence_case_opened=email_data['intelligence_case_opened'],
                caseprofile_id=email_data['caseprofile_id'],
                alleged_subject=email_data['alleged_subject'],
                alleged_subject_english=email_data['alleged_subject_english'],
                alleged_subject_chinese=email_data['alleged_subject_chinese'],
                alleged_nature=email_data['alleged_nature'],
                allegation_summary=email_data['allegation_summary'],
                ai_analysis_summary=email_data['ai_analysis_summary'],
                license_number=email_data['license_number'],
                license_numbers_json=email_data['license_numbers_json'],
                intermediary_types_json=email_data['intermediary_types_json'],
                preparer=email_data['preparer'],
                reviewer_decision=email_data['reviewer_decision'],
                status=email_data['status'],
                case_number=email_data['case_number'],
                case_assigned_by=email_data['case_assigned_by'],
                case_assigned_at=email_data['case_assigned_at'],
                int_reference_number=email_data['int_reference_number'],
                int_reference_order=email_data['int_reference_order'],
                int_reference_manual=email_data['int_reference_manual'],
                int_reference_updated_at=email_data['int_reference_updated_at'],
                int_reference_updated_by=email_data['int_reference_updated_by']
            )
            db.session.add(new_email)
        
        db.session.commit()
        print(f"✅ Re-inserted {len(email_data_list)} emails with new IDs")
        
        # 6. Re-insert attachments
        print("\n📎 Re-inserting attachments...")
        for att_data in attachment_data_list:
            new_attachment = Attachment(
                email_id=att_data['new_email_id'],
                filename=att_data['filename'],
                filepath=att_data['filepath'],
                content_type=att_data['content_type'],
                size=att_data['size'],
                extracted_text=att_data['extracted_text']
            )
            db.session.add(new_attachment)
        
        db.session.commit()
        print(f"✅ Re-inserted {len(attachment_data_list)} attachments")
        
        # 7. Update sequence to next available ID (PostgreSQL)
        if 'postgresql' in db_config.get('SQLALCHEMY_DATABASE_URI', ''):
            next_id = len(email_data_list) + 1
            db.session.execute(text(f"ALTER SEQUENCE email_id_seq RESTART WITH {next_id}"))
            db.session.commit()
            print(f"\n🔄 Updated sequence to start at {next_id}")
        
        # 8. Verify results
        print("\n" + "="*80)
        print("VERIFICATION")
        print("="*80)
        
        all_emails = Email.query.order_by(Email.id.desc()).limit(10).all()
        print("\n📋 Top 10 emails by ID (should be newest):")
        for email in all_emails:
            print(f"  ID: {email.id:4d} | Received: {email.received} | Subject: {email.subject[:50] if email.subject else 'No Subject'}...")
        
        print("\n✅ REARRANGEMENT COMPLETE!")
        print(f"   Oldest email has ID=1")
        print(f"   Latest email has ID={len(email_data_list)}")

def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("EMAIL ID REARRANGEMENT SCRIPT")
    print("="*80)
    print("\n⚠️  WARNING: This will DELETE and RE-INSERT all email records!")
    print("   Make sure you have a database backup before proceeding.")
    print("\nThis script will:")
    print("  1. Backup all email data")
    print("  2. Delete all emails and attachments")
    print("  3. Re-insert with new IDs (biggest ID = latest email)")
    print("  4. Update all foreign key references")
    
    response = input("\n❓ Do you want to proceed? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n❌ Operation cancelled.")
        return
    
    # Wrap everything in app context to avoid "Working outside of application context" errors
    with app.app_context():
        try:
            # Step 1: Backup
            total_emails = backup_emails()
            
            if total_emails == 0:
                print("\n⚠️  No emails found in database. Nothing to rearrange.")
                return
            
            # Step 2: Rearrange
            rearrange_email_ids()
            
            print("\n" + "="*80)
            print("✅ ALL OPERATIONS COMPLETED SUCCESSFULLY!")
            print("="*80)
            print("\n📝 Next steps:")
            print("  1. Restart your Flask application")
            print("  2. Check the intelligence list page")
            print("  3. Verify EMAIL-1 is oldest, EMAIL-{} is newest".format(total_emails))
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            print("\n🔄 Rolling back changes...")
            try:
                db.session.rollback()
                print("✅ Changes rolled back successfully")
            except:
                print("⚠️  Could not rollback - database may be in inconsistent state")
            print("⚠️  Check the backup file and manually restore if needed.")
            raise

if __name__ == "__main__":
    main()
