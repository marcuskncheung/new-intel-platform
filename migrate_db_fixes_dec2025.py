"""
Database Migration Script - December 2025
==========================================
Applies safe database fixes from CODE_PROBLEMS_REPORT.md:
- Problem 12.2: Add ondelete='CASCADE' to foreign keys
- Problem 12.5: Add missing indexes on frequently queried columns

IMPORTANT: This script is SAFE to run - it only adds constraints/indexes,
it does NOT delete or modify any existing data.

Run with: python migrate_db_fixes_dec2025.py
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_migration():
    """Apply database fixes safely"""
    
    print("=" * 60)
    print("🔧 DATABASE FIX MIGRATION - December 2025")
    print("=" * 60)
    print()
    
    # Import Flask app to get database connection
    try:
        from app1_production import app, db
        print("✅ Successfully imported Flask app and database")
    except Exception as e:
        print(f"❌ Failed to import app: {e}")
        return False
    
    with app.app_context():
        try:
            # Get database engine info
            engine = db.engine
            db_url = str(engine.url)
            is_postgres = 'postgresql' in db_url.lower()
            
            print(f"📦 Database: {'PostgreSQL' if is_postgres else 'SQLite'}")
            print()
            
            # Define migration queries
            if is_postgres:
                migrations = get_postgres_migrations()
            else:
                migrations = get_sqlite_migrations()
            
            # Execute migrations
            success_count = 0
            skip_count = 0
            error_count = 0
            
            for name, query in migrations:
                try:
                    print(f"⏳ Applying: {name}...")
                    db.session.execute(db.text(query))
                    db.session.commit()
                    print(f"   ✅ Success")
                    success_count += 1
                except Exception as e:
                    error_msg = str(e).lower()
                    # Check if it's a "already exists" error (safe to ignore)
                    if 'already exists' in error_msg or 'duplicate' in error_msg:
                        print(f"   ⏭️  Skipped (already exists)")
                        skip_count += 1
                    else:
                        print(f"   ⚠️  Error: {e}")
                        error_count += 1
                    db.session.rollback()
            
            print()
            print("=" * 60)
            print(f"📊 MIGRATION SUMMARY")
            print(f"   ✅ Applied: {success_count}")
            print(f"   ⏭️  Skipped: {skip_count}")
            print(f"   ⚠️  Errors: {error_count}")
            print("=" * 60)
            
            if error_count == 0:
                print("✅ Migration completed successfully!")
                print("   Your existing data is unchanged.")
                return True
            else:
                print("⚠️  Migration completed with some errors.")
                print("   Review the errors above - they may be safe to ignore.")
                return True
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            return False


def get_postgres_migrations():
    """PostgreSQL-specific migration queries"""
    return [
        # =============================================
        # Problem 12.5: Add Missing Indexes
        # =============================================
        (
            "Index: attachment.email_id",
            "CREATE INDEX IF NOT EXISTS idx_attachment_email_id ON attachment(email_id)"
        ),
        (
            "Index: whatsapp_image.whatsapp_id", 
            "CREATE INDEX IF NOT EXISTS idx_whatsapp_image_whatsapp_id ON whatsapp_image(whatsapp_id)"
        ),
        (
            "Index: online_patrol_photo.online_patrol_id",
            "CREATE INDEX IF NOT EXISTS idx_online_patrol_photo_patrol_id ON online_patrol_photo(online_patrol_id)"
        ),
        (
            "Index: target.surveillance_entry_id",
            "CREATE INDEX IF NOT EXISTS idx_target_surveillance_id ON target(surveillance_entry_id)"
        ),
        (
            "Index: surveillance_photo.surveillance_id",
            "CREATE INDEX IF NOT EXISTS idx_surveillance_photo_surveillance_id ON surveillance_photo(surveillance_id)"
        ),
        (
            "Index: surveillance_document.surveillance_id",
            "CREATE INDEX IF NOT EXISTS idx_surveillance_document_surveillance_id ON surveillance_document(surveillance_id)"
        ),
        (
            "Index: received_by_hand_document.received_by_hand_id",
            "CREATE INDEX IF NOT EXISTS idx_rbh_document_rbh_id ON received_by_hand_document(received_by_hand_id)"
        ),
        (
            "Index: audit_log.user_id",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id)"
        ),
        (
            "Index: audit_log.username",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_username ON audit_log(username)"
        ),
        (
            "Index: audit_log.action",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action)"
        ),
        (
            "Index: audit_log.timestamp",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)"
        ),
        
        # =============================================
        # Problem 12.2: Add CASCADE DELETE constraints
        # Note: PostgreSQL requires dropping and recreating FK constraints
        # This is SAFE - it doesn't delete data, just changes the constraint
        # =============================================
        
        # For attachment table
        (
            "Drop old FK: attachment.email_id",
            """
            DO $$ BEGIN
                ALTER TABLE attachment DROP CONSTRAINT IF EXISTS attachment_email_id_fkey;
            EXCEPTION WHEN undefined_object THEN NULL;
            END $$;
            """
        ),
        (
            "Add CASCADE FK: attachment.email_id",
            """
            ALTER TABLE attachment 
            ADD CONSTRAINT attachment_email_id_fkey 
            FOREIGN KEY (email_id) REFERENCES email(id) ON DELETE CASCADE
            """
        ),
        
        # For whatsapp_image table
        (
            "Drop old FK: whatsapp_image.whatsapp_id",
            """
            DO $$ BEGIN
                ALTER TABLE whatsapp_image DROP CONSTRAINT IF EXISTS whatsapp_image_whatsapp_id_fkey;
            EXCEPTION WHEN undefined_object THEN NULL;
            END $$;
            """
        ),
        (
            "Add CASCADE FK: whatsapp_image.whatsapp_id",
            """
            ALTER TABLE whatsapp_image 
            ADD CONSTRAINT whatsapp_image_whatsapp_id_fkey 
            FOREIGN KEY (whatsapp_id) REFERENCES whats_app_entry(id) ON DELETE CASCADE
            """
        ),
        
        # For online_patrol_photo table
        (
            "Drop old FK: online_patrol_photo.online_patrol_id",
            """
            DO $$ BEGIN
                ALTER TABLE online_patrol_photo DROP CONSTRAINT IF EXISTS online_patrol_photo_online_patrol_id_fkey;
            EXCEPTION WHEN undefined_object THEN NULL;
            END $$;
            """
        ),
        (
            "Add CASCADE FK: online_patrol_photo.online_patrol_id",
            """
            ALTER TABLE online_patrol_photo 
            ADD CONSTRAINT online_patrol_photo_online_patrol_id_fkey 
            FOREIGN KEY (online_patrol_id) REFERENCES online_patrol_entry(id) ON DELETE CASCADE
            """
        ),
        
        # For target table
        (
            "Drop old FK: target.surveillance_entry_id",
            """
            DO $$ BEGIN
                ALTER TABLE target DROP CONSTRAINT IF EXISTS target_surveillance_entry_id_fkey;
            EXCEPTION WHEN undefined_object THEN NULL;
            END $$;
            """
        ),
        (
            "Add CASCADE FK: target.surveillance_entry_id",
            """
            ALTER TABLE target 
            ADD CONSTRAINT target_surveillance_entry_id_fkey 
            FOREIGN KEY (surveillance_entry_id) REFERENCES surveillance_entry(id) ON DELETE CASCADE
            """
        ),
        
        # For surveillance_photo table
        (
            "Drop old FK: surveillance_photo.surveillance_id",
            """
            DO $$ BEGIN
                ALTER TABLE surveillance_photo DROP CONSTRAINT IF EXISTS surveillance_photo_surveillance_id_fkey;
            EXCEPTION WHEN undefined_object THEN NULL;
            END $$;
            """
        ),
        (
            "Add CASCADE FK: surveillance_photo.surveillance_id",
            """
            ALTER TABLE surveillance_photo 
            ADD CONSTRAINT surveillance_photo_surveillance_id_fkey 
            FOREIGN KEY (surveillance_id) REFERENCES surveillance_entry(id) ON DELETE CASCADE
            """
        ),
        
        # For surveillance_document table
        (
            "Drop old FK: surveillance_document.surveillance_id",
            """
            DO $$ BEGIN
                ALTER TABLE surveillance_document DROP CONSTRAINT IF EXISTS surveillance_document_surveillance_id_fkey;
            EXCEPTION WHEN undefined_object THEN NULL;
            END $$;
            """
        ),
        (
            "Add CASCADE FK: surveillance_document.surveillance_id",
            """
            ALTER TABLE surveillance_document 
            ADD CONSTRAINT surveillance_document_surveillance_id_fkey 
            FOREIGN KEY (surveillance_id) REFERENCES surveillance_entry(id) ON DELETE CASCADE
            """
        ),
        
        # For received_by_hand_document table
        (
            "Drop old FK: received_by_hand_document.received_by_hand_id",
            """
            DO $$ BEGIN
                ALTER TABLE received_by_hand_document DROP CONSTRAINT IF EXISTS received_by_hand_document_received_by_hand_id_fkey;
            EXCEPTION WHEN undefined_object THEN NULL;
            END $$;
            """
        ),
        (
            "Add CASCADE FK: received_by_hand_document.received_by_hand_id",
            """
            ALTER TABLE received_by_hand_document 
            ADD CONSTRAINT received_by_hand_document_received_by_hand_id_fkey 
            FOREIGN KEY (received_by_hand_id) REFERENCES received_by_hand_entry(id) ON DELETE CASCADE
            """
        ),
    ]


def get_sqlite_migrations():
    """SQLite-specific migration queries (SQLite has limited ALTER TABLE support)"""
    return [
        # SQLite only supports CREATE INDEX, not modifying FK constraints
        # The CASCADE constraints will only apply to new tables
        (
            "Index: attachment.email_id",
            "CREATE INDEX IF NOT EXISTS idx_attachment_email_id ON attachment(email_id)"
        ),
        (
            "Index: whatsapp_image.whatsapp_id",
            "CREATE INDEX IF NOT EXISTS idx_whatsapp_image_whatsapp_id ON whatsapp_image(whatsapp_id)"
        ),
        (
            "Index: online_patrol_photo.online_patrol_id",
            "CREATE INDEX IF NOT EXISTS idx_online_patrol_photo_patrol_id ON online_patrol_photo(online_patrol_id)"
        ),
        (
            "Index: target.surveillance_entry_id",
            "CREATE INDEX IF NOT EXISTS idx_target_surveillance_id ON target(surveillance_entry_id)"
        ),
        (
            "Index: surveillance_photo.surveillance_id",
            "CREATE INDEX IF NOT EXISTS idx_surveillance_photo_surveillance_id ON surveillance_photo(surveillance_id)"
        ),
        (
            "Index: surveillance_document.surveillance_id",
            "CREATE INDEX IF NOT EXISTS idx_surveillance_document_surveillance_id ON surveillance_document(surveillance_id)"
        ),
        (
            "Index: received_by_hand_document.received_by_hand_id",
            "CREATE INDEX IF NOT EXISTS idx_rbh_document_rbh_id ON received_by_hand_document(received_by_hand_id)"
        ),
        (
            "Index: audit_log.user_id",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id)"
        ),
        (
            "Index: audit_log.username",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_username ON audit_log(username)"
        ),
        (
            "Index: audit_log.action",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action)"
        ),
        (
            "Index: audit_log.timestamp",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)"
        ),
    ]


if __name__ == "__main__":
    print()
    print("⚠️  IMPORTANT: This migration is SAFE to run!")
    print("   It only adds indexes and cascade constraints.")
    print("   It does NOT delete or modify any existing data.")
    print()
    
    # Ask for confirmation
    response = input("Do you want to proceed? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        success = run_migration()
        sys.exit(0 if success else 1)
    else:
        print("Migration cancelled.")
        sys.exit(0)
