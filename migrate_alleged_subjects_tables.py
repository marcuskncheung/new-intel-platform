#!/usr/bin/env python3
"""
Database Migration Script: Create Alleged Subject Relational Tables
=====================================================================

This script creates 3 new relational tables to fix English-Chinese name pairing:
1. whatsapp_alleged_subjects
2. online_patrol_alleged_subjects  
3. received_by_hand_alleged_subjects

These tables mimic the email_alleged_subjects architecture (already working).

Usage:
    python3 migrate_alleged_subjects_tables.py
"""

from app1_production import app, db
from app1_production import WhatsAppAllegedSubject, OnlinePatrolAllegedSubject, ReceivedByHandAllegedSubject

def create_alleged_subject_tables():
    """Create all 3 alleged subject relational tables"""
    
    print("\n" + "="*70)
    print("🚀 ALLEGED SUBJECT TABLES MIGRATION")
    print("="*70)
    
    with app.app_context():
        print("\n📊 Checking current database state...")
        
        # Check which tables already exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        tables_to_create = [
            ('whatsapp_alleged_subjects', WhatsAppAllegedSubject),
            ('online_patrol_alleged_subjects', OnlinePatrolAllegedSubject),
            ('received_by_hand_alleged_subjects', ReceivedByHandAllegedSubject)
        ]
        
        print("\n📋 Table Status:")
        print("-" * 70)
        for table_name, model_class in tables_to_create:
            status = "✅ EXISTS" if table_name in existing_tables else "❌ MISSING"
            print(f"  {table_name:<40} {status}")
        
        print("\n" + "="*70)
        print("🔨 Creating missing tables...")
        print("="*70)
        
        created_count = 0
        for table_name, model_class in tables_to_create:
            if table_name not in existing_tables:
                try:
                    print(f"\n📝 Creating table: {table_name}")
                    model_class.__table__.create(db.engine, checkfirst=True)
                    print(f"   ✅ SUCCESS: {table_name} created")
                    created_count += 1
                except Exception as e:
                    print(f"   ❌ ERROR: Failed to create {table_name}")
                    print(f"   Error details: {e}")
                    raise
            else:
                print(f"\n⏭️  SKIP: {table_name} already exists")
        
        print("\n" + "="*70)
        print("📊 MIGRATION SUMMARY")
        print("="*70)
        print(f"  Tables created: {created_count}")
        print(f"  Tables skipped: {len(tables_to_create) - created_count}")
        
        # Verify all tables exist now
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        print("\n📋 Final Table Status:")
        print("-" * 70)
        all_exist = True
        for table_name, _ in tables_to_create:
            if table_name in existing_tables:
                print(f"  ✅ {table_name}")
            else:
                print(f"  ❌ {table_name} - FAILED TO CREATE")
                all_exist = False
        
        print("\n" + "="*70)
        if all_exist:
            print("✅ MIGRATION COMPLETE - All tables ready!")
        else:
            print("❌ MIGRATION INCOMPLETE - Some tables missing!")
            return False
        print("="*70)
        
        # Show table structures
        print("\n📐 Table Structures:")
        print("="*70)
        for table_name, _ in tables_to_create:
            if table_name in existing_tables:
                print(f"\n🔹 {table_name}:")
                columns = inspector.get_columns(table_name)
                for col in columns:
                    col_type = str(col['type'])
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    print(f"   - {col['name']:<30} {col_type:<20} {nullable}")
        
        return True

if __name__ == "__main__":
    try:
        success = create_alleged_subject_tables()
        
        if success:
            print("\n" + "="*70)
            print("🎉 NEXT STEPS:")
            print("="*70)
            print("1. Restart your application:")
            print("   docker-compose restart web")
            print("")
            print("2. Test by creating entries with multiple alleged subjects:")
            print("   - WhatsApp: Add entry with 2+ persons")
            print("   - Online Patrol: Add entry with 2+ persons")
            print("   - Received By Hand: Add entry with 2+ persons")
            print("")
            print("3. Verify data in database:")
            print("   docker exec -it new-intel-platform-db-1 psql -U postgres -d intelligence_db")
            print("   SELECT * FROM whatsapp_alleged_subjects;")
            print("   SELECT * FROM online_patrol_alleged_subjects;")
            print("   SELECT * FROM received_by_hand_alleged_subjects;")
            print("="*70)
            exit(0)
        else:
            print("\n❌ Migration failed! Check errors above.")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
