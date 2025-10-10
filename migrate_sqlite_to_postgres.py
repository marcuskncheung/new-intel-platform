"""
SQLite to PostgreSQL Migration Script
Converts your existing 300MB SQLite database to PostgreSQL
"""

import os
import sys
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self, sqlite_path, postgres_url):
        self.sqlite_path = sqlite_path
        self.postgres_url = postgres_url
        self.sqlite_conn = None
        self.postgres_conn = None
        
    def connect_databases(self):
        """Connect to both SQLite and PostgreSQL databases"""
        try:
            # Connect to SQLite
            logger.info(f"Connecting to SQLite: {self.sqlite_path}")
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            
            # Connect to PostgreSQL
            logger.info("Connecting to PostgreSQL...")
            self.postgres_conn = psycopg2.connect(self.postgres_url)
            self.postgres_conn.autocommit = False
            
            logger.info("Database connections established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            return False
    
    def get_table_schema(self, table_name):
        """Get table schema from SQLite"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        return columns
    
    def convert_sqlite_type_to_postgres(self, sqlite_type):
        """Convert SQLite data types to PostgreSQL"""
        type_mapping = {
            'INTEGER': 'INTEGER',
            'TEXT': 'TEXT',
            'REAL': 'REAL',
            'BLOB': 'BYTEA',
            'DATETIME': 'TIMESTAMP',
            'DATE': 'DATE',
            'TIME': 'TIME',
            'BOOLEAN': 'BOOLEAN',
            'VARCHAR': 'VARCHAR',
            'CHAR': 'CHAR'
        }
        
        sqlite_type = sqlite_type.upper()
        for sqlite_key, postgres_type in type_mapping.items():
            if sqlite_key in sqlite_type:
                return postgres_type
        
        # Default fallback
        return 'TEXT'
    
    def create_postgres_table(self, table_name, sqlite_columns):
        """Create PostgreSQL table based on SQLite schema"""
        postgres_cursor = self.postgres_conn.cursor()
        
        # Build CREATE TABLE statement
        column_definitions = []
        primary_keys = []
        
        for col in sqlite_columns:
            col_name = col[1]
            col_type = self.convert_sqlite_type_to_postgres(col[2])
            not_null = "NOT NULL" if col[3] else ""
            
            # Handle primary keys
            if col[5]:  # pk column in PRAGMA table_info
                primary_keys.append(col_name)
                if col_type == 'INTEGER':
                    col_type = 'SERIAL'
            
            column_def = f"{col_name} {col_type} {not_null}".strip()
            column_definitions.append(column_def)
        
        # Add primary key constraint
        if primary_keys:
            pk_constraint = f"PRIMARY KEY ({', '.join(primary_keys)})"
            column_definitions.append(pk_constraint)
        
        # Quote table name to handle PostgreSQL reserved words
        quoted_table_name = f'"{table_name}"' if table_name.lower() in ['user', 'order', 'group', 'table'] else table_name
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {quoted_table_name} (
            {', '.join(column_definitions)}
        )
        """
        
        logger.info(f"Creating table {table_name}...")
        logger.debug(f"SQL: {create_sql}")
        
        try:
            postgres_cursor.execute(f"DROP TABLE IF EXISTS {quoted_table_name} CASCADE")
            postgres_cursor.execute(create_sql)
            self.postgres_conn.commit()
            logger.info(f"Table {table_name} created successfully")
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            self.postgres_conn.rollback()
            raise
    
    def migrate_table_data(self, table_name):
        """Migrate data from SQLite table to PostgreSQL"""
        sqlite_cursor = self.sqlite_conn.cursor()
        postgres_cursor = self.postgres_conn.cursor()
        
        # Get all data from SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            logger.info(f"No data to migrate for table {table_name}")
            return
        
        # Get column names
        column_names = [description[0] for description in sqlite_cursor.description]
        
        # Quote table name to handle PostgreSQL reserved words  
        quoted_table_name = f'"{table_name}"' if table_name.lower() in ['user', 'order', 'group', 'table'] else table_name
        
        # Prepare PostgreSQL insert
        placeholders = ', '.join(['%s'] * len(column_names))
        insert_sql = f"INSERT INTO {quoted_table_name} ({', '.join(column_names)}) VALUES ({placeholders})"
        
        # Get PostgreSQL column types for proper conversion
        postgres_cursor.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table_name.lower()}'
            ORDER BY ordinal_position
        """)
        pg_columns = {row[0]: row[1] for row in postgres_cursor.fetchall()}
        
        # Convert rows to tuples for PostgreSQL
        data_tuples = []
        for row in rows:
            row_data = []
            for i, value in enumerate(row):
                column_name = column_names[i]
                pg_type = pg_columns.get(column_name, '')
                
                # Convert data types appropriately
                converted_value = self.convert_data_types(value, column_name, pg_type)
                row_data.append(converted_value)
            data_tuples.append(tuple(row_data))
        
        # Batch insert for better performance
        try:
            # Use executemany for better compatibility
            postgres_cursor.executemany(insert_sql, data_tuples)
            self.postgres_conn.commit()
            logger.info(f"Migrated {len(data_tuples)} rows to {table_name}")
        except Exception as e:
            logger.error(f"Failed to migrate data for table {table_name}: {e}")
            self.postgres_conn.rollback()
            raise
    
    def convert_data_types(self, value, column_name, postgres_type):
        """Convert SQLite data types to PostgreSQL compatible types"""
        if value is None:
            return None
        
        # Handle boolean conversions - SQLite stores as 0/1, PostgreSQL needs boolean
        if 'boolean' in postgres_type.lower() or column_name.lower() in ['is_active', 'is_admin', 'is_verified', 'active']:
            if isinstance(value, (int, str)):
                return bool(int(value))
            return bool(value)
            
        # Handle datetime conversions - check for datetime column names and PostgreSQL timestamp types
        datetime_indicators = ['timestamp', 'datetime', 'date'] 
        datetime_columns = ['received_time', 'created_at', 'updated_at', 'assessment_updated_at', 'last_login', 'complaint_time', 'date', 'uploaded_at', 'case_assigned_at']
        
        is_datetime_field = (
            any(indicator in postgres_type.lower() for indicator in datetime_indicators) or 
            column_name.lower() in datetime_columns or
            column_name.lower().endswith('_time') or
            column_name.lower().endswith('_at') or
            column_name.lower().endswith('_date')
        )
        
        if is_datetime_field and isinstance(value, str):
            # Try to parse as datetime
            for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        
        # Handle string encoding issues
        if isinstance(value, str):
            try:
                return value.encode('utf-8').decode('utf-8')
            except (UnicodeDecodeError, UnicodeEncodeError):
                return str(value)
        
        return value

    def get_sqlite_tables(self):
        """Get list of all tables in SQLite database"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        return [table for table in tables if not table.startswith('sqlite_')]
    
    def create_indexes(self):
        """Create essential indexes for performance"""
        postgres_cursor = self.postgres_conn.cursor()
        
        index_queries = [
            # Users table indexes
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            
            # Email/Intelligence indexes (adjust based on your schema)
            "CREATE INDEX IF NOT EXISTS idx_emails_date ON emails(date_received) WHERE date_received IS NOT NULL",
            "CREATE INDEX IF NOT EXISTS idx_emails_subject ON emails(subject) WHERE subject IS NOT NULL",
            "CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender) WHERE sender IS NOT NULL",
            
            # Activity logs
            "CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_logs(timestamp) WHERE timestamp IS NOT NULL",
            "CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_logs(user_id) WHERE user_id IS NOT NULL",
        ]
        
        for query in index_queries:
            try:
                postgres_cursor.execute(query)
                logger.info(f"Created index: {query.split('idx_')[1].split(' ')[0] if 'idx_' in query else 'index'}")
            except Exception as e:
                logger.warning(f"Could not create index: {e}")
        
        self.postgres_conn.commit()
    
    def verify_migration(self):
        """Verify that migration was successful"""
        sqlite_cursor = self.sqlite_conn.cursor()
        postgres_cursor = self.postgres_conn.cursor()
        
        tables = self.get_sqlite_tables()
        
        logger.info("Verifying migration...")
        for table in tables:
            # Count rows in both databases
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = sqlite_cursor.fetchone()[0]
            
            quoted_table = f'"{table}"' if table.lower() in ['user', 'order', 'group', 'table'] else table
            postgres_cursor.execute(f"SELECT COUNT(*) FROM {quoted_table}")
            postgres_count = postgres_cursor.fetchone()[0]
            
            if sqlite_count == postgres_count:
                logger.info(f"✓ {table}: {sqlite_count} rows migrated successfully")
            else:
                logger.error(f"✗ {table}: SQLite has {sqlite_count} rows, PostgreSQL has {postgres_count} rows")
    
    def migrate(self):
        """Main migration process"""
        if not self.connect_databases():
            return False
        
        try:
            logger.info("Starting SQLite to PostgreSQL migration...")
            
            # Get all tables
            tables = self.get_sqlite_tables()
            logger.info(f"Found {len(tables)} tables to migrate: {', '.join(tables)}")
            
            # Migrate each table
            for table in tables:
                logger.info(f"\n--- Migrating table: {table} ---")
                
                # Get SQLite schema
                schema = self.get_table_schema(table)
                
                # Create PostgreSQL table
                self.create_postgres_table(table, schema)
                
                # Migrate data
                self.migrate_table_data(table)
            
            # Create indexes
            logger.info("\n--- Creating indexes ---")
            self.create_indexes()
            
            # Verify migration
            logger.info("\n--- Verifying migration ---")
            self.verify_migration()
            
            logger.info("\n🎉 Migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
        
        finally:
            if self.sqlite_conn:
                self.sqlite_conn.close()
            if self.postgres_conn:
                self.postgres_conn.close()

def main():
    # Configuration
    sqlite_path = "/app/migrate_data/users.db"  # Path in Docker container
    postgres_url = os.getenv('DATABASE_URL')
    
    if not postgres_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    if not os.path.exists(sqlite_path):
        logger.error(f"SQLite database not found at {sqlite_path}")
        sys.exit(1)
    
    # Run migration
    migrator = DatabaseMigrator(sqlite_path, postgres_url)
    success = migrator.migrate()
    
    if success:
        logger.info("✅ Database migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Database migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
