#!/bin/bash
# ============================================================================
# ALLEGED SUBJECT TABLES MIGRATION SCRIPT
# ============================================================================
# Creates 3 relational tables for correct English-Chinese name pairing:
# 1. whatsapp_alleged_subjects
# 2. online_patrol_alleged_subjects
# 3. received_by_hand_alleged_subjects
# ============================================================================

set -e  # Exit on error

echo ""
echo "============================================================================"
echo "🚀 ALLEGED SUBJECT TABLES MIGRATION"
echo "============================================================================"
echo ""

# Check if we're inside Docker container or on host
if [ -f /.dockerenv ]; then
    echo "📦 Running inside Docker container"
    PYTHON_CMD="python3"
else
    echo "💻 Running on host machine"
    echo "🔄 Will execute migration inside Docker container..."
    
    # Check if container exists
    if ! docker ps | grep -q "new-intel-platform-web-1"; then
        echo "❌ ERROR: Docker container 'new-intel-platform-web-1' is not running!"
        echo ""
        echo "Please start your containers first:"
        echo "  docker-compose up -d"
        exit 1
    fi
    
    echo ""
    echo "📝 Copying migration script to container..."
    docker cp migrate_alleged_subjects_tables.py new-intel-platform-web-1:/app/
    
    echo "🔨 Executing migration inside container..."
    echo ""
    docker exec -it new-intel-platform-web-1 python3 /app/migrate_alleged_subjects_tables.py
    
    MIGRATION_EXIT_CODE=$?
    
    if [ $MIGRATION_EXIT_CODE -eq 0 ]; then
        echo ""
        echo "============================================================================"
        echo "✅ MIGRATION SUCCESSFUL!"
        echo "============================================================================"
        echo ""
        echo "🔄 Restarting application to apply changes..."
        docker-compose restart web
        
        echo ""
        echo "⏳ Waiting for application to start..."
        sleep 5
        
        echo ""
        echo "============================================================================"
        echo "✅ ALL DONE! Your application is ready."
        echo "============================================================================"
        echo ""
        echo "📋 Verification Commands:"
        echo ""
        echo "1. Check all tables exist:"
        echo "   docker exec -it new-intel-platform-db-1 psql -U postgres -d intelligence_db -c \\"
        echo "   \"SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%alleged_subjects' ORDER BY table_name;\""
        echo ""
        echo "2. View WhatsApp table structure:"
        echo "   docker exec -it new-intel-platform-db-1 psql -U postgres -d intelligence_db -c \"\\d whatsapp_alleged_subjects\""
        echo ""
        echo "3. Test by creating entries with multiple alleged subjects in:"
        echo "   - WhatsApp Intelligence"
        echo "   - Online Patrol"
        echo "   - Received By Hand"
        echo ""
        exit 0
    else
        echo ""
        echo "============================================================================"
        echo "❌ MIGRATION FAILED!"
        echo "============================================================================"
        echo ""
        echo "Please check the error messages above and try again."
        echo ""
        exit 1
    fi
fi
