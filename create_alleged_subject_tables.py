#!/usr/bin/env python3
"""
Create WhatsAppAllegedSubject and OnlinePatrolAllegedSubject tables in production PostgreSQL
Run this script in your Docker container or server to create the new tables
"""

from app1_production import app, db, WhatsAppAllegedSubject, OnlinePatrolAllegedSubject
from sqlalchemy import inspect

def check_and_create_tables():
    """Check if tables exist and create them if needed"""
    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        print("=" * 80)
        print("🔍 CHECKING ALLEGED SUBJECT TABLES")
        print("=" * 80)
        
        # Check WhatsAppAllegedSubject table
        if 'whatsapp_alleged_subject' in existing_tables:
            print("✅ Table 'whatsapp_alleged_subject' already exists")
            columns = [col['name'] for col in inspector.get_columns('whatsapp_alleged_subject')]
            print(f"   Columns: {', '.join(columns)}")
        else:
            print("⚠️  Table 'whatsapp_alleged_subject' does NOT exist - will create")
        
        # Check OnlinePatrolAllegedSubject table
        if 'online_patrol_alleged_subject' in existing_tables:
            print("✅ Table 'online_patrol_alleged_subject' already exists")
            columns = [col['name'] for col in inspector.get_columns('online_patrol_alleged_subject')]
            print(f"   Columns: {', '.join(columns)}")
        else:
            print("⚠️  Table 'online_patrol_alleged_subject' does NOT exist - will create")
        
        print("\n" + "=" * 80)
        print("🔨 CREATING MISSING TABLES")
        print("=" * 80)
        
        # Create all tables (only creates missing ones)
        try:
            db.create_all()
            print("✅ Database tables created successfully!")
            print("\n📋 VERIFICATION:")
            
            # Re-check after creation
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'whatsapp_alleged_subject' in existing_tables:
                columns = [col['name'] for col in inspector.get_columns('whatsapp_alleged_subject')]
                print(f"✅ whatsapp_alleged_subject: {', '.join(columns)}")
            else:
                print("❌ whatsapp_alleged_subject: FAILED TO CREATE")
            
            if 'online_patrol_alleged_subject' in existing_tables:
                columns = [col['name'] for col in inspector.get_columns('online_patrol_alleged_subject')]
                print(f"✅ online_patrol_alleged_subject: {', '.join(columns)}")
            else:
                print("❌ online_patrol_alleged_subject: FAILED TO CREATE")
                
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n" + "=" * 80)
        print("✅ SETUP COMPLETE - New relational tables ready for English-Chinese name pairing!")
        print("=" * 80)
        return True

if __name__ == "__main__":
    check_and_create_tables()
