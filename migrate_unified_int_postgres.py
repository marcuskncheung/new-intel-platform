"""
Migration Script: Unified INT-### Reference System for PostgreSQL
Date: 2025-10-16
Purpose: Add caseprofile_id foreign keys to enable unified INT references across all sources

This migration adds:
- caseprofile_id to email table
- caseprofile_id to whats_app_entry table  
- caseprofile_id to online_patrol_entry table
- index_order to case_profile table
- source_type to case_profile table
- Foreign key relationships and indexes
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from datetime import datetime

def run_migration():
    """Run the migration to add unified INT reference system"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("Set it with: export DATABASE_URL='postgresql://user:pass@host:port/dbname'")
        return False
    
    print(f"🔄 Starting Unified INT Reference System migration...")
    print(f"📊 Database: PostgreSQL")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Enable autocommit for DDL statements
            conn = conn.execution_options(isolation_level="AUTOCOMMIT")
            
            inspector = inspect(engine)
            
            print(f"✅ Connected to PostgreSQL database")
            
            # ========================================
            # 1. Update case_profile table
            # ========================================
            print(f"\n📝 Step 1: Updating case_profile table...")
            
            case_profile_columns = [col['name'] for col in inspector.get_columns('case_profile')]
            
            # Add index_order if missing
            if 'index_order' not in case_profile_columns:
                print(f"  ➕ Adding index_order column...")
                conn.execute(text("""
                    ALTER TABLE case_profile 
                    ADD COLUMN index_order INTEGER
                """))
                print(f"  ✅ Added index_order column")
            else:
                print(f"  ⏭️  index_order already exists")
            
            # Add source_type if missing
            if 'source_type' not in case_profile_columns:
                print(f"  ➕ Adding source_type column...")
                conn.execute(text("""
                    ALTER TABLE case_profile 
                    ADD COLUMN source_type VARCHAR(20)
                """))
                print(f"  ✅ Added source_type column")
            else:
                print(f"  ⏭️  source_type already exists")
            
            # Add date_of_receipt if missing (should be TIMESTAMP)
            if 'date_of_receipt' in case_profile_columns:
                # Check if it's a string type and convert to TIMESTAMP
                print(f"  🔄 Checking date_of_receipt type...")
                result = conn.execute(text("""
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'case_profile' 
                    AND column_name = 'date_of_receipt'
                """))
                current_type = result.scalar()
                
                if current_type != 'timestamp without time zone':
                    print(f"  🔄 Converting date_of_receipt from {current_type} to TIMESTAMP...")
                    conn.execute(text("""
                        ALTER TABLE case_profile 
                        ALTER COLUMN date_of_receipt TYPE TIMESTAMP 
                        USING CASE 
                            WHEN date_of_receipt ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}' 
                            THEN date_of_receipt::TIMESTAMP 
                            ELSE NULL 
                        END
                    """))
                    print(f"  ✅ Converted date_of_receipt to TIMESTAMP")
            
            # Add created_at, updated_at if missing
            if 'created_at' not in case_profile_columns:
                print(f"  ➕ Adding created_at column...")
                conn.execute(text("""
                    ALTER TABLE case_profile 
                    ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """))
                print(f"  ✅ Added created_at column")
            
            if 'updated_at' not in case_profile_columns:
                print(f"  ➕ Adding updated_at column...")
                conn.execute(text("""
                    ALTER TABLE case_profile 
                    ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """))
                print(f"  ✅ Added updated_at column")
            
            if 'created_by' not in case_profile_columns:
                print(f"  ➕ Adding created_by column...")
                conn.execute(text("""
                    ALTER TABLE case_profile 
                    ADD COLUMN created_by VARCHAR(100)
                """))
                print(f"  ✅ Added created_by column")
            
            # ========================================
            # 2. Add caseprofile_id to email table
            # ========================================
            print(f"\n📝 Step 2: Adding caseprofile_id to email table...")
            
            email_columns = [col['name'] for col in inspector.get_columns('email')]
            
            if 'caseprofile_id' not in email_columns:
                print(f"  ➕ Adding caseprofile_id column...")
                conn.execute(text("""
                    ALTER TABLE email 
                    ADD COLUMN caseprofile_id INTEGER
                """))
                print(f"  ✅ Added caseprofile_id to email")
                
                # Add foreign key constraint
                print(f"  🔗 Adding foreign key constraint...")
                conn.execute(text("""
                    ALTER TABLE email 
                    ADD CONSTRAINT fk_email_caseprofile 
                    FOREIGN KEY (caseprofile_id) 
                    REFERENCES case_profile(id) 
                    ON DELETE SET NULL
                """))
                print(f"  ✅ Added foreign key constraint")
                
                # Add index
                print(f"  🔍 Creating index...")
                conn.execute(text("""
                    CREATE INDEX idx_email_caseprofile 
                    ON email(caseprofile_id)
                """))
                print(f"  ✅ Created index")
            else:
                print(f"  ⏭️  caseprofile_id already exists in email")
            
            # ========================================
            # 3. Add caseprofile_id to whats_app_entry table
            # ========================================
            print(f"\n📝 Step 3: Adding caseprofile_id to whats_app_entry table...")
            
            whatsapp_columns = [col['name'] for col in inspector.get_columns('whats_app_entry')]
            
            if 'caseprofile_id' not in whatsapp_columns:
                print(f"  ➕ Adding caseprofile_id column...")
                conn.execute(text("""
                    ALTER TABLE whats_app_entry 
                    ADD COLUMN caseprofile_id INTEGER
                """))
                print(f"  ✅ Added caseprofile_id to whats_app_entry")
                
                # Add foreign key constraint
                print(f"  🔗 Adding foreign key constraint...")
                conn.execute(text("""
                    ALTER TABLE whats_app_entry 
                    ADD CONSTRAINT fk_whatsapp_caseprofile 
                    FOREIGN KEY (caseprofile_id) 
                    REFERENCES case_profile(id) 
                    ON DELETE SET NULL
                """))
                print(f"  ✅ Added foreign key constraint")
                
                # Add index
                print(f"  🔍 Creating index...")
                conn.execute(text("""
                    CREATE INDEX idx_whatsapp_caseprofile 
                    ON whats_app_entry(caseprofile_id)
                """))
                print(f"  ✅ Created index")
            else:
                print(f"  ⏭️  caseprofile_id already exists in whats_app_entry")
            
            # ========================================
            # 4. Add caseprofile_id to online_patrol_entry table
            # ========================================
            print(f"\n📝 Step 4: Adding caseprofile_id to online_patrol_entry table...")
            
            patrol_columns = [col['name'] for col in inspector.get_columns('online_patrol_entry')]
            
            if 'caseprofile_id' not in patrol_columns:
                print(f"  ➕ Adding caseprofile_id column...")
                conn.execute(text("""
                    ALTER TABLE online_patrol_entry 
                    ADD COLUMN caseprofile_id INTEGER
                """))
                print(f"  ✅ Added caseprofile_id to online_patrol_entry")
                
                # Add foreign key constraint
                print(f"  🔗 Adding foreign key constraint...")
                conn.execute(text("""
                    ALTER TABLE online_patrol_entry 
                    ADD CONSTRAINT fk_patrol_caseprofile 
                    FOREIGN KEY (caseprofile_id) 
                    REFERENCES case_profile(id) 
                    ON DELETE SET NULL
                """))
                print(f"  ✅ Added foreign key constraint")
                
                # Add index
                print(f"  🔍 Creating index...")
                conn.execute(text("""
                    CREATE INDEX idx_patrol_caseprofile 
                    ON online_patrol_entry(caseprofile_id)
                """))
                print(f"  ✅ Created index")
            else:
                print(f"  ⏭️  caseprofile_id already exists in online_patrol_entry")
            
            print(f"\n✅ Migration completed successfully!")
            print(f"📊 Unified INT reference system database schema ready")
            return True
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 70)
    print("  🔗 UNIFIED INT-### REFERENCE SYSTEM MIGRATION (PostgreSQL)")
    print("  Add caseprofile_id foreign keys to all source tables")
    print("=" * 70)
    print()
    
    success = run_migration()
    
    if success:
        print("\n" + "=" * 70)
        print("  ✅ Migration completed successfully!")
        print("  🔗 Unified INT reference system is now ready")
        print()
        print("  Next steps:")
        print("  1. Restart the application: docker-compose restart intelligence-app")
        print("  2. Test the /int_source page")
        print("  3. Verify INT references display correctly")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print("  ❌ Migration failed - check errors above")
        print("  💡 Troubleshooting:")
        print("     - Ensure DATABASE_URL is set correctly")
        print("     - Check PostgreSQL connection")
        print("     - Verify user has ALTER TABLE permissions")
        print("=" * 70)
        sys.exit(1)
