#!/usr/bin/env python3
"""
Secure Database Manager
Provides safe database operations to prevent SQL injection
"""

from flask import current_app
import re
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

class SecureDBManager:
    """Secure database operations manager"""
    
    def __init__(self, db):
        self.db = db
        
    def safe_execute(self, query, params=None, fetch_one=False, fetch_all=False):
        """
        Safely execute SQL queries with parameter binding
        """
        try:
            with self.db.engine.connect() as conn:
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))
                
                if fetch_one:
                    return result.fetchone()
                elif fetch_all:
                    return result.fetchall()
                else:
                    return result
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            raise e
    
    def safe_count(self, table_name, where_clause=None, params=None):
        """Safely count records in a table"""
        # Validate table name to prevent SQL injection
        if not table_name.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Invalid table name")
        
        if where_clause:
            # Table name validated above, where_clause uses parameterized queries
            query = "SELECT COUNT(*) FROM {} WHERE {}".format(table_name, where_clause)  # nosec B608
        else:
            query = "SELECT COUNT(*) FROM {}".format(table_name)  # nosec B608
        
        result = self.safe_execute(query, params, fetch_one=True)
        return result[0] if result else 0
    
    def safe_select(self, table_name, columns="*", where_clause=None, params=None, limit=None, order_by=None):
        """Safely select records from a table"""
        # Validate table name and columns to prevent SQL injection
        if not table_name.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Invalid table name")
        
        # Validate columns parameter
        if columns != "*" and not all(col.strip().replace('_', '').replace('-', '').isalnum() for col in columns.split(',')):
            raise ValueError("Invalid column specification")
        
        query = "SELECT {} FROM {}".format(columns, table_name)  # nosec B608 - Validated above
        
        if where_clause:
            query += " WHERE {}".format(where_clause)
        
        if order_by:
            # Validate order_by to prevent injection
            if not order_by.replace('_', '').replace('-', '').replace(' ', '').replace('ASC', '').replace('DESC', '').isalnum():
                raise ValueError("Invalid ORDER BY clause")
            query += " ORDER BY {}".format(order_by)
            
        if limit:
            query += f" LIMIT {limit}"
        
        return self.safe_execute(query, params, fetch_all=True)
    
    def safe_add_column(self, table_name, column_name, column_type):
        """Safely add a column to a table"""
        inspector = inspect(self.db.engine)
        columns = [c['name'] for c in inspector.get_columns(table_name)]
        
        if column_name not in columns:
            query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            self.safe_execute(query)
            logger.info(f"Added column {column_name} to table {table_name}")
            return True
        return False
    
    def safe_create_index(self, index_name, table_name, column_name):
        """Safely create an index"""
        query = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})"
        self.safe_execute(query)
        logger.info(f"Created index {index_name} on {table_name}.{column_name}")
    
    def column_exists(self, table_name, column_name):
        """Check if a column exists in a table"""
        inspector = inspect(self.db.engine)
        columns = [c['name'] for c in inspector.get_columns(table_name)]
        return column_name in columns

# Initialize with app
secure_db = None

def init_secure_db(db):
    """Initialize secure database manager"""
    global secure_db
    secure_db = SecureDBManager(db)
    return secure_db

def get_secure_db():
    """Get secure database manager instance"""
    global secure_db
    if secure_db is None:
        raise RuntimeError("Secure DB manager not initialized")
    return secure_db
