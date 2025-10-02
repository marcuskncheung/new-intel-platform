"""
Database Configuration Module for PostgreSQL Migration
Handles database connections for both SQLite and PostgreSQL
"""

import os
from sqlalchemy import create_engine, text
from flask import current_app

def get_database_config():
    """Get database configuration from environment"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Fallback to SQLite for development
        database_url = 'sqlite:///instance/users.db'
    
    return {
        'SQLALCHEMY_DATABASE_URI': database_url,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_ENGINE_OPTIONS': get_engine_options(database_url)
    }

def get_engine_options(database_url):
    """Get appropriate engine options based on database type"""
    if database_url.startswith('postgresql://'):
        return {
            'pool_size': 20,
            'max_overflow': 30,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'connect_args': {
                'connect_timeout': 30,
                'application_name': 'intelligence_platform'
            }
        }
    elif database_url.startswith('sqlite:'):
        return {
            'pool_pre_ping': True,
            'connect_args': {
                'check_same_thread': False,
                'timeout': 30
            }
        }
    else:
        return {}

def configure_database_for_production(app, db):
    """Configure database for production use"""
    database_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    
    if database_url.startswith('postgresql://'):
        configure_postgresql_for_production(db)
    elif database_url.startswith('sqlite:'):
        configure_sqlite_for_production(db)
    
    return True

def configure_postgresql_for_production(db):
    """Configure PostgreSQL database for production"""
    try:
        with db.engine.connect() as conn:
            # Test connection
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL connected: {version}")
            
            # Set session parameters for better performance
            conn.execute(text("SET statement_timeout = '300s'"))
            conn.execute(text("SET lock_timeout = '30s'"))
            conn.execute(text("SET idle_in_transaction_session_timeout = '600s'"))
            
            conn.commit()
            print("✅ PostgreSQL configured for production")
            return True
            
    except Exception as e:
        print(f"⚠️ Warning: Could not configure PostgreSQL: {e}")
        return False

def configure_sqlite_for_production(db):
    """Configure SQLite database for production with WAL mode"""
    try:
        with db.engine.connect() as conn:
            # Test basic connection
            conn.execute(text("SELECT 1"))
            
            # Enable WAL mode for better concurrency
            conn.execute(text("PRAGMA journal_mode=WAL;"))
            conn.execute(text("PRAGMA synchronous=NORMAL;"))
            conn.execute(text("PRAGMA cache_size=10000;"))
            conn.execute(text("PRAGMA temp_store=MEMORY;"))
            conn.execute(text("PRAGMA busy_timeout=30000;"))
            
            conn.commit()
            print("✅ SQLite configured for production with WAL mode")
            return True
            
    except Exception as e:
        print(f"⚠️ Warning: Could not configure SQLite: {e}")
        print("⚠️ Database will use default SQLite configuration")
        return False

def is_postgresql():
    """Check if the current database is PostgreSQL"""
    try:
        database_url = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        return database_url.startswith('postgresql://')
    except:
        return False

def is_sqlite():
    """Check if the current database is SQLite"""
    try:
        database_url = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        return database_url.startswith('sqlite:')
    except:
        return False

def get_db_info():
    """Get database information for logging"""
    try:
        database_url = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if database_url.startswith('postgresql://'):
            return "PostgreSQL (Production)"
        elif database_url.startswith('sqlite:'):
            return "SQLite (Development/Single-user)"
        else:
            return "Unknown database type"
    except:
        return "Database not configured"
