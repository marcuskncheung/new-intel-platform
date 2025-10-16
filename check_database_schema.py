#!/usr/bin/env python3
"""
🔍 DATABASE SCHEMA CHECKER
Check case_profile table structure and identify missing columns
Run this on your production server where the database is accessible
"""

import os
import sys
from sqlalchemy import create_engine, inspect, text
from tabulate import tabulate

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_database_schema():
    """Check database schema and report missing columns"""
    
    print("=" * 70)
    print("🔍 DATABASE SCHEMA CHECKER")
    print("=" * 70)
    print()
    
    # Get database URL from environment or config
    try:
        from database_config import get_database_config
        db_config = get_database_config()
        database_url = db_config['SQLALCHEMY_DATABASE_URI']
        print(f"✅ Database URL: {database_url[:50]}...")
    except Exception as e:
        print(f"❌ Error loading database config: {e}")
        return False
    
    try:
        # Create engine
        engine = create_engine(database_url)
        inspector = inspect(engine)
        
        print(f"✅ Connected to database\n")
        
        # Check if case_profile table exists
        if 'case_profile' not in inspector.get_table_names():
            print("❌ ERROR: case_profile table does NOT exist!")
            print("   Run Stage 1 migration first: python migrate_unified_int_postgres.py")
            return False
        
        print("✅ case_profile table exists")
        print()
        
        # Get current columns
        columns = inspector.get_columns('case_profile')
        column_names = [col['name'] for col in columns]
        
        print("📋 CURRENT COLUMNS IN case_profile:")
        print("-" * 70)
        table_data = []
        for col in columns:
            table_data.append([
                col['name'],
                str(col['type']),
                'YES' if col.get('nullable', True) else 'NO',
                'PK' if col.get('primary_key', False) else ''
            ])
        print(tabulate(table_data, headers=['Column', 'Type', 'Nullable', 'Key'], tablefmt='grid'))
        print()
        
        # Check for required unified INT columns
        required_columns = {
            'index': 'VARCHAR(20)',
            'index_order': 'INTEGER',
            'date_of_receipt': 'TIMESTAMP',
            'source_type': 'VARCHAR(20)',
            'email_id': 'INTEGER',
            'whatsapp_id': 'INTEGER',
            'patrol_id': 'INTEGER',
            'created_by': 'VARCHAR(100)',
        }
        
        print("🔍 CHECKING REQUIRED COLUMNS:")
        print("-" * 70)
        
        missing_columns = []
        present_columns = []
        
        for col_name, col_type in required_columns.items():
            if col_name in column_names:
                present_columns.append(f"✅ {col_name} ({col_type})")
            else:
                missing_columns.append(f"❌ {col_name} ({col_type})")
        
        for col in present_columns:
            print(col)
        
        if missing_columns:
            print()
            print("🚨 MISSING COLUMNS:")
            for col in missing_columns:
                print(col)
            print()
        
        # Check foreign key constraints
        print()
        print("🔗 FOREIGN KEY CONSTRAINTS:")
        print("-" * 70)
        
        foreign_keys = inspector.get_foreign_keys('case_profile')
        if foreign_keys:
            fk_data = []
            for fk in foreign_keys:
                fk_data.append([
                    fk.get('name', 'unnamed'),
                    ', '.join(fk['constrained_columns']),
                    fk['referred_table'],
                    ', '.join(fk['referred_columns'])
                ])
            print(tabulate(fk_data, headers=['Constraint', 'Column', 'References Table', 'References Column'], tablefmt='grid'))
        else:
            print("⚠️  No foreign key constraints found")
        
        print()
        
        # Check indexes
        print("📊 INDEXES:")
        print("-" * 70)
        
        indexes = inspector.get_indexes('case_profile')
        if indexes:
            idx_data = []
            for idx in indexes:
                idx_data.append([
                    idx['name'],
                    ', '.join(idx['column_names']),
                    'YES' if idx.get('unique', False) else 'NO'
                ])
            print(tabulate(idx_data, headers=['Index Name', 'Columns', 'Unique'], tablefmt='grid'))
        else:
            print("⚠️  No indexes found")
        
        print()
        print("=" * 70)
        
        # Summary and recommendations
        if missing_columns:
            print("🚨 ACTION REQUIRED:")
            print("=" * 70)
            print()
            print("Missing columns detected! Run the following SQL commands:")
            print()
            print("```sql")
            
            if 'email_id' not in column_names:
                print("ALTER TABLE case_profile ADD COLUMN email_id INTEGER;")
            if 'whatsapp_id' not in column_names:
                print("ALTER TABLE case_profile ADD COLUMN whatsapp_id INTEGER;")
            if 'patrol_id' not in column_names:
                print("ALTER TABLE case_profile ADD COLUMN patrol_id INTEGER;")
            
            print()
            print("-- Add foreign key constraints")
            if 'email_id' not in column_names:
                print("ALTER TABLE case_profile ADD CONSTRAINT fk_case_profile_email")
                print("    FOREIGN KEY (email_id) REFERENCES email(id) ON DELETE SET NULL;")
            if 'whatsapp_id' not in column_names:
                print("ALTER TABLE case_profile ADD CONSTRAINT fk_case_profile_whatsapp")
                print("    FOREIGN KEY (whatsapp_id) REFERENCES whats_app_entry(id) ON DELETE SET NULL;")
            if 'patrol_id' not in column_names:
                print("ALTER TABLE case_profile ADD CONSTRAINT fk_case_profile_patrol")
                print("    FOREIGN KEY (patrol_id) REFERENCES online_patrol_entry(id) ON DELETE SET NULL;")
            
            print()
            print("-- Add indexes for performance")
            if 'email_id' not in column_names:
                print("CREATE INDEX idx_case_profile_email ON case_profile(email_id);")
            if 'whatsapp_id' not in column_names:
                print("CREATE INDEX idx_case_profile_whatsapp ON case_profile(whatsapp_id);")
            if 'patrol_id' not in column_names:
                print("CREATE INDEX idx_case_profile_patrol ON case_profile(patrol_id);")
            
            print("```")
            print()
            print("💡 To run these commands:")
            print("   docker-compose exec intelligence-db psql -U intelligence_user -d intelligence_db")
            print()
            return False
        else:
            print("✅ ALL REQUIRED COLUMNS PRESENT!")
            print("=" * 70)
            print()
            print("Your case_profile table has all required columns.")
            print("Stage 2 auto-generation should work correctly.")
            print()
            return True
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = check_database_schema()
    sys.exit(0 if success else 1)
