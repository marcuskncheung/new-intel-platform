#!/usr/bin/env python3
"""
Quick Local Test Script for PostgreSQL Migration
Tests the Flask app connection to PostgreSQL without doing the full migration
"""

import os
import sys

# Set environment variable for PostgreSQL
os.environ['DATABASE_URL'] = 'postgresql://intelligence:TestDB123!@localhost:5432/intelligence_db'

# Import the Flask app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database_config import get_database_config, get_db_info
    print(f"✅ Database config loaded: {get_db_info()}")
    
    # Test database connection
    from sqlalchemy import create_engine, text
    
    db_config = get_database_config()
    engine = create_engine(db_config['SQLALCHEMY_DATABASE_URI'])
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"✅ PostgreSQL Connection: {version}")
        
        # Test creating a simple table
        conn.execute(text("CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, name TEXT)"))
        conn.execute(text("INSERT INTO test_table (name) VALUES ('Test PostgreSQL Connection')"))
        
        result = conn.execute(text("SELECT * FROM test_table"))
        rows = result.fetchall()
        print(f"✅ Test table created and populated: {len(rows)} rows")
        
        # Clean up
        conn.execute(text("DROP TABLE test_table"))
        conn.commit()
        
    print("\n🎉 PostgreSQL test successful! Ready for full migration.")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
