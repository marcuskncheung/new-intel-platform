#!/usr/bin/env python3
"""
POI v2.0 Database Migration Script
Adds new columns to alleged_person_profile table for enhanced POI tracking system
"""

import os
import sys
import psycopg2
from psycopg2 import sql

def run_migration():
    """Run the POI v2.0 migration"""
    
    # Get database connection details from environment
    db_url = os.environ.get('DATABASE_URL', 'postgresql://intelligence:SecureIntelDB2024!@postgres-db:5432/intelligence_db')
    
    # Parse database URL
    # Format: postgresql://user:password@host:port/database
    try:
        from urllib.parse import urlparse
        result = urlparse(db_url)
        conn_params = {
            'host': result.hostname,
            'port': result.port or 5432,
            'user': result.username,
            'password': result.password,
            'database': result.path[1:]  # Remove leading /
        }
    except Exception as e:
        print(f"❌ Failed to parse DATABASE_URL: {e}")
        return False
    
    print("=" * 80)
    print("🔄 POI v2.0 Database Migration")
    print("=" * 80)
    print(f"📊 Database: {conn_params['database']}")
    print(f"🖥️  Host: {conn_params['host']}:{conn_params['port']}")
    print(f"👤 User: {conn_params['user']}")
    print()
    
    try:
        # Connect to database
        print("🔌 Connecting to PostgreSQL...")
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = False
        cursor = conn.cursor()
        print("✅ Connected successfully")
        print()
        
        # Read migration SQL
        migration_file = os.path.join(os.path.dirname(__file__), 'migrations', '02_poi_v2_upgrade.sql')
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("📝 Executing migration SQL...")
        print()
        
        # Execute migration
        cursor.execute(migration_sql)
        
        # Commit transaction
        conn.commit()
        print("✅ Migration completed successfully!")
        print()
        
        # Verify columns were added
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'alleged_person_profile'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print(f"📋 Table now has {len(columns)} columns:")
        for col_name, col_type in columns[:10]:  # Show first 10
            print(f"   • {col_name}: {col_type}")
        if len(columns) > 10:
            print(f"   ... and {len(columns - 10)} more columns")
        print()
        
        # Count existing profiles
        cursor.execute("SELECT COUNT(*) FROM alleged_person_profile")
        count = cursor.fetchone()[0]
        print(f"✅ {count} POI profiles in database")
        print()
        
        cursor.close()
        conn.close()
        
        print("=" * 80)
        print("🎉 POI v2.0 migration completed successfully!")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
