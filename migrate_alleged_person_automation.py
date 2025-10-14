"""
Database Migration: Add Alleged Person Automation Tables

This script adds the new database tables for the automated alleged person 
profile system:

1. AllegedPersonProfile - Main profile table with POI IDs
2. EmailAllegedPersonLink - Many-to-many relationship table

Run this script once to set up the automation system.
"""

import os
import sys

# Add current directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app1_production import app, db, AllegedPersonProfile, EmailAllegedPersonLink
from sqlalchemy import text, inspect

def check_table_exists(table_name):
    """Check if a table exists in the database"""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()

def migrate_alleged_person_tables():
    """Create the new alleged person automation tables"""
    
    print("🤖 ALLEGED PERSON AUTOMATION - Database Migration")
    print("=" * 60)
    
    try:
        with app.app_context():
            # Check if tables already exist
            profile_exists = check_table_exists('alleged_person_profile')
            link_exists = check_table_exists('email_alleged_person_link')
            
            print(f"📊 Current status:")
            print(f"   alleged_person_profile: {'EXISTS' if profile_exists else 'MISSING'}")
            print(f"   email_alleged_person_link: {'EXISTS' if link_exists else 'MISSING'}")
            
            if profile_exists and link_exists:
                print("✅ All automation tables already exist!")
                return True
            
            # Create tables
            print(f"\n🔧 Creating missing tables...")
            
            if not profile_exists:
                print(f"   Creating alleged_person_profile table...")
            if not link_exists:
                print(f"   Creating email_alleged_person_link table...")
            
            # This creates both tables with all relationships
            db.create_all()
            
            # Verify tables were created
            profile_exists = check_table_exists('alleged_person_profile')
            link_exists = check_table_exists('email_alleged_person_link')
            
            if profile_exists and link_exists:
                print("✅ Automation tables created successfully!")
                
                # Show table structure
                print(f"\n📋 Table structures:")
                
                with db.engine.connect() as conn:
                    # Show AllegedPersonProfile columns
                    result = conn.execute(text("PRAGMA table_info(alleged_person_profile)"))
                    columns = result.fetchall()
                    print(f"\n   alleged_person_profile ({len(columns)} columns):")
                    for col in columns:
                        print(f"      - {col[1]} ({col[2]})")
                    
                    # Show EmailAllegedPersonLink columns  
                    result = conn.execute(text("PRAGMA table_info(email_alleged_person_link)"))
                    columns = result.fetchall()
                    print(f"\n   email_alleged_person_link ({len(columns)} columns):")
                    for col in columns:
                        print(f"      - {col[1]} ({col[2]})")
                
                print(f"\n🎯 Ready for automation!")
                print(f"   - AI analysis will auto-create POI profiles")
                print(f"   - Manual input will auto-create POI profiles") 
                print(f"   - Visit /alleged_subject_list to see profiles")
                
                return True
            
            else:
                print("❌ Failed to create automation tables")
                return False
                
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_sample_profiles():
    """Create sample alleged person profiles for testing"""
    
    try:
        with app.app_context():
            # Check if any profiles already exist
            existing_count = AllegedPersonProfile.query.count()
            
            if existing_count > 0:
                print(f"ℹ️ Found {existing_count} existing profiles, skipping sample creation")
                return
            
            print(f"\n📝 Creating sample alleged person profiles...")
            
            sample_profiles = [
                {
                    'poi_id': 'POI-001',
                    'name_english': 'LEUNG SHEUNG MAN EMERSON',
                    'name_chinese': '梁尚文',
                    'agent_number': 'AG123456',
                    'company': 'Prudential Hong Kong Limited',
                    'role': 'Agent',
                    'created_by': 'SAMPLE_DATA'
                },
                {
                    'poi_id': 'POI-002', 
                    'name_english': 'WONG TAI SIN',
                    'name_chinese': '黃大仙',
                    'agent_number': 'AG789012',
                    'company': 'AIA Hong Kong',
                    'role': 'Broker',
                    'created_by': 'SAMPLE_DATA'
                },
                {
                    'poi_id': 'POI-003',
                    'name_english': 'CHAN SIU MING',
                    'name_chinese': '陳小明',
                    'license_number': 'LIC456789',
                    'company': 'Manulife Hong Kong',
                    'role': 'Agent',
                    'created_by': 'SAMPLE_DATA'
                }
            ]
            
            for sample_data in sample_profiles:
                # Create normalized name
                name_parts = []
                if sample_data.get('name_english'):
                    from alleged_person_automation import normalize_name_for_matching
                    name_parts.append(normalize_name_for_matching(sample_data['name_english']))
                if sample_data.get('name_chinese'):
                    name_parts.append(normalize_name_for_matching(sample_data['name_chinese']))
                
                profile = AllegedPersonProfile(
                    poi_id=sample_data['poi_id'],
                    name_english=sample_data.get('name_english'),
                    name_chinese=sample_data.get('name_chinese'),
                    name_normalized=' | '.join(name_parts) if name_parts else None,
                    agent_number=sample_data.get('agent_number'),
                    license_number=sample_data.get('license_number'),
                    company=sample_data.get('company'),
                    role=sample_data.get('role'),
                    created_by=sample_data['created_by'],
                    email_count=0,
                    status='ACTIVE'
                )
                
                db.session.add(profile)
                print(f"   ✅ Created sample profile: {sample_data['poi_id']} - {sample_data.get('name_english', sample_data.get('name_chinese'))}")
            
            db.session.commit()
            
            total_count = AllegedPersonProfile.query.count()
            print(f"✅ Created {len(sample_profiles)} sample profiles (total: {total_count})")
            
    except Exception as e:
        print(f"❌ Error creating sample profiles: {e}")
        import traceback
        traceback.print_exc()

def show_migration_status():
    """Show current migration and automation status"""
    
    try:
        with app.app_context():
            print(f"\n📊 AUTOMATION SYSTEM STATUS")
            print(f"=" * 40)
            
            # Check tables
            profile_exists = check_table_exists('alleged_person_profile')
            link_exists = check_table_exists('email_alleged_person_link')
            
            print(f"📋 Database Tables:")
            print(f"   alleged_person_profile: {'✅ EXISTS' if profile_exists else '❌ MISSING'}")
            print(f"   email_alleged_person_link: {'✅ EXISTS' if link_exists else '❌ MISSING'}")
            
            if profile_exists:
                total_profiles = AllegedPersonProfile.query.count()
                active_profiles = AllegedPersonProfile.query.filter_by(status='ACTIVE').count()
                
                print(f"\n👥 Profile Statistics:")
                print(f"   Total profiles: {total_profiles}")
                print(f"   Active profiles: {active_profiles}")
                
                # Show recent profiles
                recent_profiles = AllegedPersonProfile.query.filter_by(status='ACTIVE').order_by(
                    AllegedPersonProfile.created_at.desc()
                ).limit(5).all()
                
                if recent_profiles:
                    print(f"\n🕐 Recent profiles:")
                    for profile in recent_profiles:
                        name = profile.name_english or profile.name_chinese or profile.poi_id
                        created = profile.created_at.strftime("%Y-%m-%d %H:%M") if profile.created_at else "Unknown"
                        print(f"   {profile.poi_id}: {name} (created {created})")
            
            if link_exists:
                total_links = EmailAllegedPersonLink.query.count()
                print(f"\n🔗 Email Links: {total_links} email-profile connections")
            
            # Check automation module
            try:
                import alleged_person_automation
                # Test if automation can initialize database properly
                db_init_success = alleged_person_automation.initialize_database()
                print(f"\n🤖 Automation Module: {'✅ AVAILABLE' if db_init_success else '❌ NOT AVAILABLE'}")
            except ImportError as e:
                print(f"\n🤖 Automation Module: ❌ IMPORT ERROR - {e}")
            except Exception as e:
                print(f"\n🤖 Automation Module: ❌ INITIALIZATION ERROR - {e}")
            
            return profile_exists and link_exists
            
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Alleged Person Automation Migration")
    
    # Show current status
    status_ok = show_migration_status()
    
    if not status_ok:
        print(f"\n🔧 Running migration...")
        migration_success = migrate_alleged_person_tables()
        
        if migration_success:
            # Create sample profiles for testing
            create_sample_profiles()
            
            # Show final status
            print(f"\n" + "=" * 60)
            show_migration_status()
            
            print(f"\n🎉 MIGRATION COMPLETE!")
            print(f"📝 Next steps:")
            print(f"   1. Start the application: python app1_production.py")
            print(f"   2. Visit /alleged_subject_list to see profiles")
            print(f"   3. Run AI analysis on emails to auto-create profiles")
            print(f"   4. Manually input alleged persons to auto-create profiles")
        else:
            print(f"\n❌ Migration failed. Check error messages above.")
    else:
        print(f"\n✅ Automation system already set up and ready!")
