#!/usr/bin/env python3
"""
Fix WhatsApp and OnlinePatrol table sequences to start from 1
This script resets the auto-increment sequences for both tables
"""
import os
import sys

def create_sequence_fix_script():
    """Create SQL script to fix table sequences"""
    
    sql_script = """-- Fix WhatsApp and OnlinePatrol table sequences to start from 1
-- Run this script in PostgreSQL database

\\echo 'Checking current table data and sequences...'

-- Check current WhatsApp entries
SELECT 'WhatsApp entries:' as info, MIN(id) as min_id, MAX(id) as max_id, COUNT(*) as total_count 
FROM whats_app_entry;

-- Check current OnlinePatrol entries  
SELECT 'OnlinePatrol entries:' as info, MIN(id) as min_id, MAX(id) as max_id, COUNT(*) as total_count
FROM online_patrol_entry;

-- Check current sequence values
SELECT 'WhatsApp sequence:' as info, last_value as current_value FROM whats_app_entry_id_seq;
SELECT 'OnlinePatrol sequence:' as info, last_value as current_value FROM online_patrol_entry_id_seq;

\\echo ''
\\echo 'OPTION 1: Reset sequences only (if tables are empty)'
\\echo '======================================================='

-- Reset WhatsApp sequence to start from 1 (only if table is empty)
DO $$
BEGIN
    IF (SELECT COUNT(*) FROM whats_app_entry) = 0 THEN
        ALTER SEQUENCE whats_app_entry_id_seq RESTART WITH 1;
        RAISE NOTICE 'WhatsApp sequence reset to 1 (table was empty)';
    ELSE
        RAISE NOTICE 'WhatsApp table has % entries - sequence NOT reset', (SELECT COUNT(*) FROM whats_app_entry);
    END IF;
END $$;

-- Reset OnlinePatrol sequence to start from 1 (only if table is empty)  
DO $$
BEGIN
    IF (SELECT COUNT(*) FROM online_patrol_entry) = 0 THEN
        ALTER SEQUENCE online_patrol_entry_id_seq RESTART WITH 1;
        RAISE NOTICE 'OnlinePatrol sequence reset to 1 (table was empty)';
    ELSE
        RAISE NOTICE 'OnlinePatrol table has % entries - sequence NOT reset', (SELECT COUNT(*) FROM online_patrol_entry);
    END IF;
END $$;

\\echo ''
\\echo 'OPTION 2: Renumber existing entries (if tables have data starting from wrong IDs)'
\\echo '================================================================================'

-- WARNING: This will change existing IDs! Only run if you understand the implications.
-- Backup the data first!

-- Show what the renumbering would look like for WhatsApp
WITH renumbered_whatsapp AS (
    SELECT 
        id as old_id,
        ROW_NUMBER() OVER (ORDER BY received_time, id) as new_id,
        complaint_name,
        received_time
    FROM whats_app_entry
    ORDER BY received_time, id
)
SELECT 'WhatsApp renumbering preview:' as info, old_id, new_id, complaint_name, received_time
FROM renumbered_whatsapp
WHERE old_id != new_id
LIMIT 10;

-- Show what the renumbering would look like for OnlinePatrol
WITH renumbered_patrol AS (
    SELECT 
        id as old_id,
        ROW_NUMBER() OVER (ORDER BY created_at, id) as new_id,
        sender,
        created_at
    FROM online_patrol_entry  
    ORDER BY created_at, id
)
SELECT 'OnlinePatrol renumbering preview:' as info, old_id, new_id, sender, created_at
FROM renumbered_patrol
WHERE old_id != new_id
LIMIT 10;

\\echo ''
\\echo 'OPTION 3: Force reset sequences (DANGEROUS - could cause conflicts)'
\\echo '===================================================================='

-- Uncomment these lines ONLY if you want to force reset sequences
-- This could cause primary key conflicts if you add new entries!

-- ALTER SEQUENCE whats_app_entry_id_seq RESTART WITH 1;
-- ALTER SEQUENCE online_patrol_entry_id_seq RESTART WITH 1;

\\echo ''
\\echo 'Check final sequence values:'
SELECT 'Final WhatsApp sequence:' as info, last_value as current_value FROM whats_app_entry_id_seq;
SELECT 'Final OnlinePatrol sequence:' as info, last_value as current_value FROM online_patrol_entry_id_seq;
"""

    # Write the SQL script
    with open('fix_sequences.sql', 'w') as f:
        f.write(sql_script)
    
    print("✅ Created fix_sequences.sql")
    
    # Create a shell script to run this on the Docker container
    docker_script = """#!/bin/bash
# Script to fix WhatsApp and OnlinePatrol sequences in Docker container

echo "🔍 Checking database sequences in Docker container..."
echo "Container: intelligence-db"
echo "Database: intelligence_db"
echo "User: intelligence"
echo ""

# Check if Docker container is running
if ! docker ps | grep -q intelligence-db; then
    echo "❌ ERROR: intelligence-db container is not running"
    echo "Start it with: docker compose up -d"
    exit 1
fi

echo "📋 Current table status:"
docker exec -i intelligence-db psql -U intelligence -d intelligence_db << 'EOF'
-- Quick status check
SELECT 'WhatsApp entries:' as table_info, MIN(id) as min_id, MAX(id) as max_id, COUNT(*) as count FROM whats_app_entry;
SELECT 'OnlinePatrol entries:' as table_info, MIN(id) as min_id, MAX(id) as max_id, COUNT(*) as count FROM online_patrol_entry;
SELECT 'WhatsApp sequence:' as seq_info, last_value FROM whats_app_entry_id_seq;
SELECT 'OnlinePatrol sequence:' as seq_info, last_value FROM online_patrol_entry_id_seq;
EOF

echo ""
echo "🛠️  To fix the sequences, you have 3 options:"
echo ""
echo "1. If tables are empty - reset sequences safely:"
echo "   docker exec -i intelligence-db psql -U intelligence -d intelligence_db < fix_sequences.sql"
echo ""
echo "2. If tables have data - renumber existing entries (BACKUP FIRST!):"
echo "   # First backup:"
echo "   docker exec intelligence-db pg_dump -U intelligence intelligence_db > backup_before_renumber.sql"
echo "   # Then run the renumbering section of fix_sequences.sql"
echo ""
echo "3. Force reset (DANGEROUS - could cause conflicts):"
echo "   # Only if you know what you're doing!"
echo ""
echo "📁 Files created:"
echo "   - fix_sequences.sql (detailed SQL script)"
echo "   - fix_sequences_docker.sh (this script)"
echo ""
echo "🔧 Recommended action:"
if docker exec -i intelligence-db psql -U intelligence -d intelligence_db -t -c "SELECT COUNT(*) FROM whats_app_entry" | tr -d ' ' | grep -q '^0$'; then
    echo "   WhatsApp table is empty - safe to reset sequence"
else
    echo "   WhatsApp table has data - backup before renumbering"
fi

if docker exec -i intelligence-db psql -U intelligence -d intelligence_db -t -c "SELECT COUNT(*) FROM online_patrol_entry" | tr -d ' ' | grep -q '^0$'; then
    echo "   OnlinePatrol table is empty - safe to reset sequence"  
else
    echo "   OnlinePatrol table has data - backup before renumbering"
fi
"""

    with open('fix_sequences_docker.sh', 'w') as f:
        f.write(docker_script)
    
    # Make it executable
    os.chmod('fix_sequences_docker.sh', 0o755)
    
    print("✅ Created fix_sequences_docker.sh (executable)")
    
    print("""
🎯 NEXT STEPS:

1. Copy these files to your Linux server:
   scp fix_sequences.sql fix_sequences_docker.sh user@yourserver:/path/to/project/

2. On your Linux server, run:
   ./fix_sequences_docker.sh

3. This will show you the current status and recommend the safest approach.

The script will tell you whether the tables are empty (safe to reset) or have data (need backup first).
""")

if __name__ == "__main__":
    print("🔧 Creating sequence fix scripts for Docker environment...")
    create_sequence_fix_script()
