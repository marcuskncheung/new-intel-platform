#!/usr/bin/env python3
"""
🚀 SIMPLE MIGRATION RUNNER FOR SURVEILLANCE ASSESSMENT
======================================================

This script runs the surveillance database migration automatically.
Just run it on your server after git pull.

Usage:
    python3 run_surveillance_migration.py

The script will:
1. Check if migration is needed
2. Apply database changes
3. Show clear success/error messages
"""

import sys
import os

# Make sure we can import from current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Run the migration"""
    print("=" * 80)
    print("🚀 SURVEILLANCE ASSESSMENT MIGRATION")
    print("=" * 80)
    print("")
    
    try:
        # Import the migration function
        print("📦 Loading migration script...")
        from migrate_surveillance_assessment import migrate_surveillance_assessment
        
        print("✅ Migration script loaded successfully")
        print("")
        
        # Run the migration
        print("🔧 Running database migration...")
        print("")
        migrate_surveillance_assessment()
        
        print("")
        print("=" * 80)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("")
        print("Next steps:")
        print("  1. Restart your Docker containers:")
        print("     docker-compose restart")
        print("")
        print("  2. Test creating a new surveillance entry")
        print("")
        print("Surveillance entries now support:")
        print("  ✓ Operation findings (detailed observations)")
        print("  ✓ Adverse finding flag (red flag indicator)")
        print("  ✓ Observation notes (general notes)")
        print("  ✓ Unified INT reference system")
        print("")
        
        return 0
        
    except ImportError as e:
        print("")
        print("❌ ERROR: Could not import migration script")
        print(f"   Details: {e}")
        print("")
        print("Make sure you are in the correct directory:")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Expected files: migrate_surveillance_assessment.py")
        print("")
        return 1
        
    except Exception as e:
        print("")
        print("❌ MIGRATION FAILED!")
        print(f"   Error: {e}")
        print("")
        print("Troubleshooting:")
        print("  1. Check if you're running this from the app directory")
        print("  2. Make sure Docker containers are running")
        print("  3. Check database connection settings")
        print("")
        print("If the error persists, contact support with the error message above.")
        print("")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
