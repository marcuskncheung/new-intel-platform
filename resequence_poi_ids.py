#!/usr/bin/env python3
"""
🔧 POI ID RESEQUENCING SCRIPT
==============================
Fixes gaps in POI IDs (e.g., POI-001, POI-002, POI-004 → POI-001, POI-002, POI-003)

This script:
1. Finds all existing POI profiles ordered by creation date
2. Reassigns sequential POI IDs without gaps
3. Updates all references in related tables

⚠️ CAUTION: This changes POI IDs! Run on server after backing up database.

Run: docker exec -it ia-flask-app python resequence_poi_ids.py

Author: AI Assistant
Date: December 2, 2025
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def analyze_gaps():
    """Analyze POI ID gaps without making changes."""
    
    print("=" * 60)
    print("🔍 POI ID GAP ANALYSIS")
    print("=" * 60)
    
    try:
        from app1_production import app, db
        from models_poi_enhanced import AllegedPersonProfile
        from sqlalchemy import text
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        return None
    
    with app.app_context():
        # Get all POI IDs ordered
        pois = db.session.query(
            AllegedPersonProfile.id,
            AllegedPersonProfile.poi_id,
            AllegedPersonProfile.name_english,
            AllegedPersonProfile.created_at
        ).filter(
            AllegedPersonProfile.poi_id.like('POI-%')
        ).order_by(AllegedPersonProfile.created_at.asc()).all()
        
        print(f"\n📊 Total POIs: {len(pois)}")
        
        # Extract numbers and find gaps
        poi_numbers = []
        for poi in pois:
            try:
                num = int(poi.poi_id.split('-')[1])
                poi_numbers.append((num, poi.poi_id, poi.name_english))
            except (IndexError, ValueError):
                print(f"   ⚠️ Invalid POI ID format: {poi.poi_id}")
        
        poi_numbers.sort(key=lambda x: x[0])
        
        # Find gaps
        gaps = []
        expected = 1
        for num, poi_id, name in poi_numbers:
            while expected < num:
                gaps.append(expected)
                expected += 1
            expected = num + 1
        
        if gaps:
            print(f"\n🕳️ Found {len(gaps)} gaps in POI IDs:")
            for i, gap in enumerate(gaps[:20]):  # Show first 20 gaps
                print(f"   - POI-{gap:03d} is missing")
            if len(gaps) > 20:
                print(f"   ... and {len(gaps) - 20} more gaps")
        else:
            print("\n✅ No gaps found in POI IDs!")
        
        # Show current range
        if poi_numbers:
            print(f"\n📈 POI ID Range: POI-{poi_numbers[0][0]:03d} to POI-{poi_numbers[-1][0]:03d}")
            print(f"   Expected count: {poi_numbers[-1][0]}")
            print(f"   Actual count: {len(poi_numbers)}")
            print(f"   Missing: {poi_numbers[-1][0] - len(poi_numbers)}")
        
        return gaps


def resequence_poi_ids(dry_run=True):
    """
    Resequence all POI IDs to remove gaps.
    
    Args:
        dry_run: If True, only shows what would change without making changes.
    """
    
    print("=" * 60)
    print("🔧 POI ID RESEQUENCING" + (" (DRY RUN)" if dry_run else ""))
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    
    try:
        from app1_production import app, db
        from models_poi_enhanced import AllegedPersonProfile, POIIntelligenceLink
        from sqlalchemy import text
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        return False
    
    with app.app_context():
        try:
            # Get all POIs ordered by creation date
            pois = db.session.query(AllegedPersonProfile).filter(
                AllegedPersonProfile.poi_id.like('POI-%')
            ).order_by(AllegedPersonProfile.created_at.asc()).all()
            
            print(f"\n📊 Found {len(pois)} POI profiles to resequence")
            
            # Build mapping of old ID → new ID
            changes = []
            for idx, poi in enumerate(pois, start=1):
                new_poi_id = f"POI-{idx:03d}"
                if poi.poi_id != new_poi_id:
                    changes.append({
                        'id': poi.id,
                        'old_poi_id': poi.poi_id,
                        'new_poi_id': new_poi_id,
                        'name': poi.name_english or poi.name_chinese or 'Unknown'
                    })
            
            if not changes:
                print("\n✅ No changes needed - POI IDs are already sequential!")
                return True
            
            print(f"\n📝 {len(changes)} POI IDs need to be changed:")
            for i, change in enumerate(changes[:20]):
                print(f"   {change['old_poi_id']} → {change['new_poi_id']} ({change['name']})")
            if len(changes) > 20:
                print(f"   ... and {len(changes) - 20} more changes")
            
            if dry_run:
                print("\n⏸️ DRY RUN - No changes made")
                print("   Run with dry_run=False to apply changes")
                return True
            
            # Apply changes
            print("\n🔄 Applying changes...")
            
            # Step 1: Temporarily rename to avoid unique constraint conflicts
            print("   Step 1: Temporarily renaming...")
            for change in changes:
                temp_id = f"TEMP-{change['id']}"
                db.session.execute(
                    text("UPDATE alleged_person_profile SET poi_id = :temp WHERE id = :id"),
                    {'temp': temp_id, 'id': change['id']}
                )
                # Update references in poi_intelligence_link
                db.session.execute(
                    text("UPDATE poi_intelligence_link SET poi_id = :temp WHERE poi_id = :old"),
                    {'temp': temp_id, 'old': change['old_poi_id']}
                )
            
            db.session.flush()
            
            # Step 2: Apply final IDs
            print("   Step 2: Applying new sequential IDs...")
            for change in changes:
                temp_id = f"TEMP-{change['id']}"
                db.session.execute(
                    text("UPDATE alleged_person_profile SET poi_id = :new WHERE id = :id"),
                    {'new': change['new_poi_id'], 'id': change['id']}
                )
                # Update references
                db.session.execute(
                    text("UPDATE poi_intelligence_link SET poi_id = :new WHERE poi_id = :temp"),
                    {'new': change['new_poi_id'], 'temp': temp_id}
                )
            
            db.session.commit()
            
            print(f"\n✅ Successfully resequenced {len(changes)} POI IDs!")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Resequence POI IDs to remove gaps')
    parser.add_argument('--analyze', action='store_true', help='Only analyze gaps, no changes')
    parser.add_argument('--apply', action='store_true', help='Apply changes (default is dry run)')
    
    args = parser.parse_args()
    
    if args.analyze:
        gaps = analyze_gaps()
        if gaps:
            print(f"\n💡 Run with --apply to fix these gaps")
    else:
        dry_run = not args.apply
        resequence_poi_ids(dry_run=dry_run)
        if dry_run:
            print("\n💡 Run with --apply to make actual changes")


if __name__ == "__main__":
    main()
