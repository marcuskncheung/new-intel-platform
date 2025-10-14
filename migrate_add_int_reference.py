"""
Migration Script: Add Intelligence Reference Number (INT-XX) System
Date: 2025-10-14
Purpose: Add INT-001, INT-002... numbering system for email case management

This migration adds:
- int_reference_number: The INT-XX display number
- int_reference_order: Numeric order for sorting
- int_reference_manual: Flag if manually edited
- int_reference_updated_at: Timestamp of last update
- int_reference_updated_by: Username who updated
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from datetime import datetime

def run_migration():
    """Run the migration to add INT reference number fields"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL', 'sqlite:///instance/users.db')
    
    print(f"🔄 Starting INT Reference Number migration...")
    print(f"📊 Database: {database_url.split('@')[0] if '@' in database_url else database_url}")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('email')]
            
            print(f"✅ Connected to database")
            print(f"📋 Existing email table columns: {len(columns)}")
            
            # Check if columns already exist
            new_columns = {
                'int_reference_number': "VARCHAR(20)",
                'int_reference_order': "INTEGER",
                'int_reference_manual': "BOOLEAN DEFAULT 0",
                'int_reference_updated_at': "DATETIME",
                'int_reference_updated_by': "VARCHAR(100)"
            }
            
            columns_to_add = []
            for col_name, col_type in new_columns.items():
                if col_name not in columns:
                    columns_to_add.append((col_name, col_type))
                else:
                    print(f"⏭️  Column '{col_name}' already exists, skipping")
            
            if not columns_to_add:
                print("✅ All INT reference columns already exist!")
                print("🔢 Generating INT numbers for existing emails...")
                generate_int_numbers(conn, database_url)
                return True
            
            # Add new columns
            print(f"\n📝 Adding {len(columns_to_add)} new columns...")
            
            for col_name, col_type in columns_to_add:
                try:
                    if database_url.startswith('postgresql'):
                        sql = f"ALTER TABLE email ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                    else:  # SQLite
                        # SQLite doesn't support IF NOT EXISTS, so check first
                        sql = f"ALTER TABLE email ADD COLUMN {col_name} {col_type}"
                    
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"  ✅ Added column: {col_name}")
                    
                except Exception as e:
                    if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"  ⏭️  Column {col_name} already exists")
                    else:
                        raise e
            
            # Create indexes for better performance
            print(f"\n🔍 Creating indexes...")
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_email_int_reference ON email(int_reference_number)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_email_int_order ON email(int_reference_order)"))
                conn.commit()
                print(f"  ✅ Created indexes")
            except Exception as e:
                print(f"  ⚠️  Index creation warning: {e}")
            
            # Generate INT numbers for all existing emails
            print(f"\n🔢 Generating INT reference numbers for existing emails...")
            generate_int_numbers(conn, database_url)
            
            print(f"\n✅ Migration completed successfully!")
            print(f"📊 INT reference number system is now active")
            return True
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_int_numbers(conn, database_url):
    """Generate INT-001, INT-002... numbers for all emails based on received date"""
    try:
        # Get all emails ordered by received date (oldest first)
        result = conn.execute(text("""
            SELECT id, received, int_reference_number 
            FROM email 
            ORDER BY received ASC
        """))
        
        emails = result.fetchall()
        total_emails = len(emails)
        
        print(f"  📧 Found {total_emails} emails to process")
        
        if total_emails == 0:
            print(f"  ℹ️  No emails in database yet")
            return
        
        # Assign INT numbers
        updated_count = 0
        for order, email in enumerate(emails, start=1):
            email_id, received, current_int = email
            
            # Only assign if not already assigned
            if current_int is None:
                int_number = f"INT-{order:03d}"  # INT-001, INT-002, etc.
                
                conn.execute(text("""
                    UPDATE email 
                    SET int_reference_number = :int_number,
                        int_reference_order = :order,
                        int_reference_manual = 0,
                        int_reference_updated_at = :now
                    WHERE id = :email_id
                """), {
                    'int_number': int_number,
                    'order': order,
                    'now': datetime.utcnow(),
                    'email_id': email_id
                })
                
                updated_count += 1
                
                if updated_count % 100 == 0:
                    print(f"    ✅ Assigned {updated_count} INT numbers...")
        
        conn.commit()
        
        print(f"  ✅ Assigned {updated_count} new INT reference numbers")
        print(f"  📊 Total emails with INT numbers: {total_emails}")
        
        # Show sample of assigned numbers
        result = conn.execute(text("""
            SELECT int_reference_number, received 
            FROM email 
            ORDER BY int_reference_order ASC 
            LIMIT 5
        """))
        
        samples = result.fetchall()
        print(f"\n  📋 Sample INT numbers (oldest first):")
        for int_num, received in samples:
            print(f"    {int_num} - {received}")
        
    except Exception as e:
        print(f"  ❌ Error generating INT numbers: {e}")
        raise e

if __name__ == '__main__':
    print("=" * 60)
    print("  INT Reference Number Migration")
    print("  Auto-generate INT-001, INT-002... for all emails")
    print("=" * 60)
    print()
    
    success = run_migration()
    
    if success:
        print("\n" + "=" * 60)
        print("  ✅ Migration completed successfully!")
        print("  🔢 INT reference numbers are now available")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("  ❌ Migration failed - check errors above")
        print("=" * 60)
        sys.exit(1)
