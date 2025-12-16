#!/usr/bin/env python3
"""
Migration Script: Sync Assessment Data for Emails with Same INT Number

This script finds all emails that share the same INT number (caseprofile_id)
and syncs their assessment data to match the FIRST email (by received date or id).

The logic is: Same INT = Same allegation = Should have same assessment data

Run this script ONCE to align existing data. Going forward, the auto-sync
in int_source_update_assessment will keep them in sync.

Usage:
    python migrate_sync_same_int_emails.py
    
Or with --dry-run to see what would be changed:
    python migrate_sync_same_int_emails.py --dry-run
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_migration(dry_run=False):
    """
    Sync assessment data for all emails with the same INT number.
    Uses the first email (by received date or id) as the master.
    """
    from app1_production import app, db, Email, EmailAllegedSubject, CaseProfile, get_hk_time
    
    with app.app_context():
        print("=" * 70)
        print("🔄 MIGRATION: Sync Assessment Data for Same INT Emails")
        print("=" * 70)
        
        if dry_run:
            print("🧪 DRY RUN MODE - No changes will be made")
        
        print()
        
        # Assessment fields to sync
        assessment_fields = [
            'alleged_subject_english',
            'alleged_subject_chinese', 
            'alleged_subject',
            'alleged_nature',
            'allegation_summary',
            'source_category',
            'internal_source_type',
            'internal_source_other',
            'external_source_type',
            'external_regulator',
            'external_law_enforcement',
            'external_source_other',
            'source_reliability',
            'content_validity',
            'license_number',
            'license_numbers_json',
            'intermediary_types_json',
        ]
        
        # Find all CaseProfiles that have more than one email
        case_profiles = db.session.query(CaseProfile).all()
        
        total_int_with_multiple_emails = 0
        total_emails_synced = 0
        sync_details = []
        
        for case_profile in case_profiles:
            # Get all emails for this INT, ordered by received date (earliest first)
            emails = Email.query.filter_by(caseprofile_id=case_profile.id)\
                                .order_by(Email.received.asc(), Email.id.asc())\
                                .all()
            
            if len(emails) <= 1:
                continue  # Only one email, nothing to sync
            
            total_int_with_multiple_emails += 1
            
            # First email is the master
            master_email = emails[0]
            sibling_emails = emails[1:]
            
            print(f"\n📌 INT: {case_profile.int_reference} (CaseProfile ID: {case_profile.id})")
            print(f"   Master Email ID: {master_email.id}")
            print(f"   - Subject: {master_email.subject[:60] if master_email.subject else 'No Subject'}...")
            print(f"   - Received: {master_email.received}")
            print(f"   - Alleged Subject EN: {master_email.alleged_subject_english}")
            print(f"   - Alleged Subject CN: {master_email.alleged_subject_chinese}")
            print(f"   - Alleged Nature: {master_email.alleged_nature}")
            print(f"   Sibling Emails to sync: {len(sibling_emails)}")
            
            # Get master email's alleged subjects from relational table
            master_subjects = EmailAllegedSubject.query.filter_by(email_id=master_email.id)\
                                                        .order_by(EmailAllegedSubject.sequence_order)\
                                                        .all()
            
            for sibling in sibling_emails:
                print(f"\n   → Syncing to Email ID: {sibling.id}")
                print(f"      Subject: {sibling.subject[:50] if sibling.subject else 'No Subject'}...")
                
                # Show what will be changed
                changes = []
                for field in assessment_fields:
                    master_value = getattr(master_email, field, None)
                    sibling_value = getattr(sibling, field, None)
                    
                    if master_value != sibling_value:
                        changes.append(f"         {field}: '{sibling_value}' → '{master_value}'")
                
                if changes:
                    print(f"      Changes:")
                    for change in changes[:5]:  # Show first 5 changes
                        print(change)
                    if len(changes) > 5:
                        print(f"         ... and {len(changes) - 5} more changes")
                else:
                    print(f"      No field changes needed")
                
                if not dry_run:
                    # Copy assessment fields
                    for field in assessment_fields:
                        source_value = getattr(master_email, field, None)
                        setattr(sibling, field, source_value)
                    
                    # Copy EmailAllegedSubject records
                    # First, delete existing records for this sibling
                    deleted_count = EmailAllegedSubject.query.filter_by(email_id=sibling.id).delete()
                    if deleted_count > 0:
                        print(f"      Deleted {deleted_count} old alleged subject records")
                    
                    # Create copies from master
                    for subject in master_subjects:
                        new_subject = EmailAllegedSubject(
                            email_id=sibling.id,
                            english_name=subject.english_name,
                            chinese_name=subject.chinese_name,
                            is_insurance_intermediary=subject.is_insurance_intermediary,
                            license_type=subject.license_type,
                            license_number=subject.license_number,
                            sequence_order=subject.sequence_order
                        )
                        db.session.add(new_subject)
                    
                    if master_subjects:
                        print(f"      Copied {len(master_subjects)} alleged subject records")
                    
                    # Update timestamp
                    sibling.assessment_updated_at = get_hk_time()
                
                total_emails_synced += 1
                sync_details.append({
                    'int_reference': case_profile.int_reference,
                    'master_id': master_email.id,
                    'synced_id': sibling.id
                })
        
        if not dry_run and total_emails_synced > 0:
            try:
                db.session.commit()
                print(f"\n✅ Successfully committed changes to database")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Error committing changes: {e}")
                return False
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 MIGRATION SUMMARY")
        print("=" * 70)
        print(f"   Total INTs with multiple emails: {total_int_with_multiple_emails}")
        print(f"   Total emails synced: {total_emails_synced}")
        
        if dry_run:
            print(f"\n🧪 DRY RUN - No changes were made")
            print(f"   Run without --dry-run to apply changes")
        else:
            print(f"\n✅ Migration completed successfully!")
        
        return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Sync assessment data for emails with same INT number')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    args = parser.parse_args()
    
    success = run_migration(dry_run=args.dry_run)
    sys.exit(0 if success else 1)
