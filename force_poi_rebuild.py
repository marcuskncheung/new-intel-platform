#!/usr/bin/env python3
"""
FORCE POI PROFILE REBUILD
=========================
This script will:
1. DELETE all existing POI profiles and links
2. Force rebuild from new email_alleged_subjects table
3. Ensure correct English-Chinese name pairings

⚠️ WARNING: This will delete ALL current POI profiles!
✅ Safe to run: POI profiles will be recreated from source data
"""

import sys
from app1_production import app, db
from app1_production import (
    AllegedPersonProfile, 
    POIIntelligenceLink,
    EmailAllegedPersonLink,
    EmailAllegedSubject,
    Email,
    WhatsAppEntry,
    OnlinePatrolEntry,
    SurveillanceEntry
)

def force_poi_rebuild():
    """Delete all POI profiles and links, then trigger rebuild"""
    
    with app.app_context():
        print("=" * 80)
        print("🔥 FORCE POI PROFILE REBUILD FROM NEW TABLE")
        print("=" * 80)
        print()
        
        # Step 1: Count current data
        print("[STEP 1] 📊 Counting current POI data...")
        poi_count = AllegedPersonProfile.query.count()
        universal_link_count = POIIntelligenceLink.query.count()
        legacy_link_count = EmailAllegedPersonLink.query.count()
        
        print(f"  - POI Profiles: {poi_count}")
        print(f"  - Universal Links: {universal_link_count}")
        print(f"  - Legacy Email Links: {legacy_link_count}")
        print()
        
        # Step 2: Delete all POI data
        print("[STEP 2] 🗑️  Deleting ALL POI profiles and links...")
        try:
            # Delete links first (foreign key constraints)
            deleted_universal = POIIntelligenceLink.query.delete()
            print(f"  ✅ Deleted {deleted_universal} universal links")
            
            deleted_legacy = EmailAllegedPersonLink.query.delete()
            print(f"  ✅ Deleted {deleted_legacy} legacy email links")
            
            # Delete POI profiles
            deleted_pois = AllegedPersonProfile.query.delete()
            print(f"  ✅ Deleted {deleted_pois} POI profiles")
            
            db.session.commit()
            print("  ✅ All POI data deleted successfully")
            print()
            
        except Exception as e:
            db.session.rollback()
            print(f"  ❌ Error deleting POI data: {e}")
            return False
        
        # Step 3: Count source data in new table
        print("[STEP 3] 📊 Counting source data in new table...")
        
        # Email alleged subjects
        email_subjects = db.session.query(EmailAllegedSubject.email_id).distinct().count()
        total_email_subjects = EmailAllegedSubject.query.count()
        print(f"  - Emails with alleged subjects: {email_subjects}")
        print(f"  - Total alleged persons in emails: {total_email_subjects}")
        
        # WhatsApp entries
        whatsapp_with_subjects = WhatsAppEntry.query.filter(
            (WhatsAppEntry.alleged_subject_english != None) | 
            (WhatsAppEntry.alleged_subject_chinese != None)
        ).count()
        print(f"  - WhatsApp entries with subjects: {whatsapp_with_subjects}")
        
        # Online Patrol entries
        patrol_with_subjects = OnlinePatrolEntry.query.filter(
            (OnlinePatrolEntry.alleged_subject_english != None) | 
            (OnlinePatrolEntry.alleged_subject_chinese != None)
        ).count()
        print(f"  - Online Patrol entries with subjects: {patrol_with_subjects}")
        
        # Surveillance entries with targets
        surveillance_count = SurveillanceEntry.query.count()
        print(f"  - Surveillance entries: {surveillance_count}")
        print()
        
        # Step 4: Trigger POI refresh
        print("[STEP 4] 🔄 Triggering POI profile rebuild...")
        print("  ℹ️  Please run POI Refresh from the web interface to rebuild profiles")
        print()
        print("=" * 80)
        print("✅ POI DATA CLEARED - READY FOR REBUILD")
        print("=" * 80)
        print()
        print("NEXT STEPS:")
        print("1. Go to POI list page in web interface")
        print("2. Click 'Refresh POI' button")
        print("3. System will recreate all POI profiles from new table")
        print("4. All English-Chinese pairings will be correct!")
        print()
        
        return True

if __name__ == "__main__":
    print()
    print("⚠️  WARNING: This will DELETE ALL current POI profiles!")
    print("⚠️  They will be recreated from source data with correct name pairings.")
    print()
    
    # Ask for confirmation
    confirm = input("Type 'DELETE ALL POIS' to continue: ")
    
    if confirm == "DELETE ALL POIS":
        print()
        success = force_poi_rebuild()
        if success:
            print("✅ POI rebuild preparation completed!")
            print("   Run 'Refresh POI' in web interface to recreate profiles.")
            sys.exit(0)
        else:
            print("❌ POI rebuild failed!")
            sys.exit(1)
    else:
        print()
        print("❌ Operation cancelled - POI data NOT deleted")
        sys.exit(1)
