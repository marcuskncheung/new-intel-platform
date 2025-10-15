"""
Backfill Alleged Person Profiles from Existing Email Data

This script processes ALL existing emails that have alleged person information
but no profiles created yet (because they were created before automation existed).

It will:
1. Query all emails with alleged_subject_english or alleged_subject_chinese
2. Parse the names (handle comma-separated lists for multiple persons)
3. Use smart matching to find existing profiles or create new ones
4. Link emails to profiles
5. Handle multiple persons per email properly
6. Print detailed progress report

Run this ONCE to backfill historical data.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app1_production import app, db, Email, AllegedPersonProfile, EmailAllegedPersonLink
from alleged_person_automation import process_manual_input
import json

def backfill_alleged_profiles():
    """
    Process all existing emails and create profiles for alleged persons
    """
    with app.app_context():
        print("=" * 80)
        print("🚀 ALLEGED PERSON PROFILE BACKFILL MIGRATION")
        print("=" * 80)
        print()
        
        # Get all emails that have alleged person data but may not have profiles
        emails_with_alleged = Email.query.filter(
            db.or_(
                Email.alleged_subject_english.isnot(None),
                Email.alleged_subject_chinese.isnot(None),
                Email.alleged_subject.isnot(None)  # Legacy field
            )
        ).all()
        
        print(f"📊 Found {len(emails_with_alleged)} emails with alleged person information")
        print()
        
        # Statistics
        stats = {
            'total_emails': len(emails_with_alleged),
            'emails_processed': 0,
            'emails_skipped': 0,
            'profiles_created': 0,
            'profiles_updated': 0,
            'links_created': 0,
            'errors': 0
        }
        
        for i, email in enumerate(emails_with_alleged, 1):
            try:
                print(f"\n[{i}/{len(emails_with_alleged)}] Processing Email ID {email.id} ({email.int_reference_number or 'No INT#'})")
                
                # Get alleged person information
                alleged_english = email.alleged_subject_english or ''
                alleged_chinese = email.alleged_subject_chinese or ''
                
                # Parse license numbers if available
                license_numbers = []
                intermediary_types = []
                if email.license_numbers_json:
                    try:
                        license_numbers = json.loads(email.license_numbers_json)
                    except:
                        pass
                
                if email.intermediary_types_json:
                    try:
                        intermediary_types = json.loads(email.intermediary_types_json)
                    except:
                        pass
                
                # Skip if no names
                if not alleged_english.strip() and not alleged_chinese.strip():
                    print(f"   ⏭️  Skipped: No alleged person names")
                    stats['emails_skipped'] += 1
                    continue
                
                # Parse names (comma-separated)
                english_names = [n.strip() for n in alleged_english.split(',') if n.strip()]
                chinese_names = [n.strip() for n in alleged_chinese.split(',') if n.strip()]
                
                num_persons = max(len(english_names), len(chinese_names))
                print(f"   👤 Found {num_persons} alleged person(s)")
                
                # Create pairs of English/Chinese names
                name_pairs = []
                for j in range(num_persons):
                    eng = english_names[j] if j < len(english_names) else ''
                    chi = chinese_names[j] if j < len(chinese_names) else ''
                    license = license_numbers[j] if j < len(license_numbers) else ''
                    int_type = intermediary_types[j] if j < len(intermediary_types) else ''
                    
                    name_pairs.append({
                        'english': eng,
                        'chinese': chi,
                        'license': license,
                        'type': int_type
                    })
                    
                    print(f"      #{j+1}: {eng or '(none)'} / {chi or '(none)'} / {license or 'No License'}")
                
                # Process each person
                for person_data in name_pairs:
                    additional_info = {}
                    if person_data['license']:
                        additional_info['agent_number'] = person_data['license']
                        additional_info['license_number'] = person_data['license']
                    if person_data['type']:
                        additional_info['role'] = person_data['type']
                    
                    # Use the process_manual_input function to create/update profile
                    results = process_manual_input(
                        db, AllegedPersonProfile, EmailAllegedPersonLink,
                        email_id=email.id,
                        alleged_subject_english=person_data['english'],
                        alleged_subject_chinese=person_data['chinese'],
                        additional_info=additional_info
                    )
                    
                    # Count results
                    for result in results:
                        if result.get('success'):
                            action = result.get('action', '')
                            poi_id = result.get('poi_id', '')
                            
                            if 'created' in action.lower():
                                stats['profiles_created'] += 1
                                print(f"      ✅ Created profile: {poi_id}")
                            elif 'updated' in action.lower():
                                stats['profiles_updated'] += 1
                                print(f"      ♻️  Updated profile: {poi_id}")
                            
                            if result.get('linked'):
                                stats['links_created'] += 1
                                print(f"      🔗 Linked to profile: {poi_id}")
                
                stats['emails_processed'] += 1
                
            except Exception as e:
                print(f"   ❌ Error processing email {email.id}: {e}")
                stats['errors'] += 1
                import traceback
                traceback.print_exc()
        
        # Print final summary
        print("\n" + "=" * 80)
        print("📊 MIGRATION SUMMARY")
        print("=" * 80)
        print(f"Total Emails Scanned:      {stats['total_emails']}")
        print(f"Emails Processed:          {stats['emails_processed']}")
        print(f"Emails Skipped:            {stats['emails_skipped']}")
        print(f"Profiles Created:          {stats['profiles_created']}")
        print(f"Profiles Updated:          {stats['profiles_updated']}")
        print(f"Email-Profile Links:       {stats['links_created']}")
        print(f"Errors:                    {stats['errors']}")
        print("=" * 80)
        
        # Show current profile count
        total_profiles = AllegedPersonProfile.query.count()
        active_profiles = AllegedPersonProfile.query.filter_by(status='ACTIVE').count()
        
        print(f"\n✅ Total Profiles in Database: {total_profiles}")
        print(f"✅ Active Profiles: {active_profiles}")
        print()
        
        # Show sample profiles
        print("📋 Sample Profiles Created:")
        sample_profiles = AllegedPersonProfile.query.order_by(AllegedPersonProfile.created_at.desc()).limit(10).all()
        for profile in sample_profiles:
            linked_count = EmailAllegedPersonLink.query.filter_by(alleged_person_id=profile.id).count()
            print(f"   {profile.poi_id}: {profile.name_english or profile.name_chinese}")
            print(f"      License: {profile.agent_number or 'None'}")
            print(f"      Linked to: {linked_count} email(s)")
            print()
        
        print("✅ Backfill migration completed successfully!")
        print()
        print("Next steps:")
        print("1. Review the alleged subject profiles page to verify data")
        print("2. Test AI analysis on new emails - should link to existing profiles")
        print("3. Test manual assessment - should also link to profiles")
        print()

if __name__ == '__main__':
    print("\n⚠️  WARNING: This script will process ALL emails and create profiles.")
    print("⚠️  Make sure you have a database backup before proceeding.")
    print()
    
    response = input("Do you want to continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        backfill_alleged_profiles()
    else:
        print("❌ Migration cancelled.")
