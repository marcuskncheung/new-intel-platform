#!/bin/bash
# Deployment script for surveillance assessment update
# Run this on your production server after git pull

echo "======================================================================"
echo "🚀 DEPLOYING SURVEILLANCE ASSESSMENT UPDATE"
echo "======================================================================"

# Navigate to project directory
cd /app || exit 1

# Pull latest changes
echo "📥 Pulling latest code from GitHub..."
git pull origin main

# Run database migration
echo ""
echo "🔧 Running database migration for surveillance assessment..."
python3 migrate_surveillance_assessment.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migration completed successfully!"
    echo ""
    echo "🔄 Restarting Docker containers..."
    docker-compose restart
    
    echo ""
    echo "======================================================================"
    echo "✅ DEPLOYMENT COMPLETE!"
    echo "======================================================================"
    echo ""
    echo "Surveillance entries now support:"
    echo "  ✓ Operation findings (detailed observations)"
    echo "  ✓ Adverse finding flag (red flag indicator)"
    echo "  ✓ Observation notes (general notes)"
    echo "  ✓ Unified INT reference system"
    echo ""
    echo "Next steps:"
    echo "  1. Test creating a new surveillance entry"
    echo "  2. Test updating assessment with adverse finding"
    echo "  3. Verify targets are linked to POI profiles"
    echo ""
else
    echo ""
    echo "❌ Migration failed! Check error messages above."
    echo "   Do NOT restart Docker until migration succeeds."
    exit 1
fi
