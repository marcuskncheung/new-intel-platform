"""
POI Date Migration Script
=========================

This script fixes POI profile dates to use the email source date instead of profile creation date.

Problem:
- POI profiles were created with today's date (created_at)
- Should use the email received date (first_mentioned_date)

Solution:
- For each POI profile, find the earliest linked email
- Update first_mentioned_date to use that email's received date
- Update last_mentioned_date to use the latest email's received date

Run this after deploying the code fix to update existing POI profiles.
"""

import sys
import os
from datetime import datetime

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app1_production import app, db, AllegedPersonProfile, Email, EmailAllegedPersonLink, POIIntelligenceLink
from sqlalchemy import text

def parse_email_date(date_str):
    """Parse email received date string to datetime object"""
    if not date_str:
        return None
    
    # Email dates are stored as strings in various formats
    # Common formats: "2022-01-15 10:30:00", "15 Jan 2022", etc.
    
    formats_to_try = [
        '%Y-%m-%d %H:%M:%S',  # 2022-01-15 10:30:00
        '%Y-%m-%d',           # 2022-01-15
        '%d %b %Y at %I:%M %p',  # 15 Jan 2022 at 10:30 AM
        '%d %b %Y',           # 15 Jan 2022
        '%Y/%m/%d %H:%M:%S',  # 2022/01/15 10:30:00
        '%Y/%m/%d',           # 2022/01/15
    ]
    
    for fmt in formats_to_try:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    
    # If all formats fail, return None
    print(f"  ⚠️ Could not parse date: {date_str}")
    return None

def fix_poi_dates():
    """Fix all POI profile dates to use source email dates"""
    
    print("=" * 80)
    print("POI DATE MIGRATION SCRIPT")
    print("=" * 80)
    print()
    
    with app.app_context():
        # Get all active POI profiles
        profiles = AllegedPersonProfile.query.filter_by(status='ACTIVE').all()
        
        print(f"Found {len(profiles)} active POI profiles")
        print()
        
        fixed_count = 0
        no_emails_count = 0
        error_count = 0
        
        for profile in profiles:
            try:
                print(f"Processing {profile.poi_id}: {profile.name_english or profile.name_chinese}...")
                
                # Find all linked emails from BOTH tables
                email_dates = []
                
                # Method 1: Check poi_intelligence_link table (POI v2.0)
                links = db.session.execute(text("""
                    SELECT e.id, e.received
                    FROM poi_intelligence_link pil
                    JOIN email e ON pil.source_id = e.id
                    WHERE pil.poi_id = :poi_id AND pil.source_type = 'EMAIL'
                    ORDER BY e.received ASC
                """), {'poi_id': profile.poi_id}).fetchall()
                
                for link in links:
                    email_id, received = link
                    received_dt = parse_email_date(received)
                    if received_dt:
                        email_dates.append(received_dt)
                        print(f"  📧 Email {email_id}: {received}")
                
                # Method 2: Check old email_alleged_person_link table (POI v1.0)
                old_links = db.session.query(Email).join(
                    EmailAllegedPersonLink, 
                    EmailAllegedPersonLink.email_id == Email.id
                ).filter(
                    EmailAllegedPersonLink.alleged_person_id == profile.id
                ).all()
                
                for email in old_links:
                    received_dt = parse_email_date(email.received)
                    if received_dt and received_dt not in email_dates:
                        email_dates.append(received_dt)
                        print(f"  📧 Email {email.id} (old table): {email.received}")
                
                if not email_dates:
                    print(f"  ⚠️ No linked emails found - keeping current dates")
                    no_emails_count += 1
                    print()
                    continue
                
                # Sort dates
                email_dates.sort()
                
                # Update POI dates
                first_date = email_dates[0]
                last_date = email_dates[-1]
                
                old_first = profile.first_mentioned_date
                old_last = profile.last_mentioned_date
                
                profile.first_mentioned_date = first_date
                profile.last_mentioned_date = last_date
                
                print(f"  ✅ Updated dates:")
                print(f"     First Mentioned: {old_first} → {first_date}")
                print(f"     Last Mentioned:  {old_last} → {last_date}")
                
                db.session.commit()
                fixed_count += 1
                print()
                
            except Exception as e:
                print(f"  ❌ Error processing {profile.poi_id}: {e}")
                db.session.rollback()
                error_count += 1
                print()
        
        print("=" * 80)
        print("MIGRATION COMPLETE")
        print("=" * 80)
        print(f"✅ Fixed: {fixed_count} profiles")
        print(f"⚠️  No emails: {no_emails_count} profiles")
        print(f"❌ Errors: {error_count} profiles")
        print()
        print("Next steps:")
        print("1. Check a few POI profiles to verify dates are correct")
        print("2. If correct, the migration was successful!")
        print("3. New POI profiles will automatically use source dates")
        print()

if __name__ == '__main__':
    try:
        fix_poi_dates()
    except KeyboardInterrupt:
        print("\n\n⚠️ Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
