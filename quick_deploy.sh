#!/bin/bash
# Quick deployment script for surveillance assessment updates

echo "🚀 Starting deployment..."
echo ""

# Step 1: Pull latest code
echo "📥 Step 1/4: Pulling latest code from GitHub..."
git pull
if [ $? -ne 0 ]; then
    echo "❌ Git pull failed. Please check your git status."
    exit 1
fi
echo "✅ Code updated"
echo ""

# Step 2: Run database migration
echo "🔧 Step 2/4: Running database migration..."
python3 run_surveillance_migration.py
if [ $? -ne 0 ]; then
    echo "⚠️ Migration failed, but continuing with restart..."
fi
echo ""

# Step 3: Restart Docker containers
echo "🔄 Step 3/4: Restarting Docker containers..."
docker-compose down
docker-compose up -d
echo "✅ Containers restarted"
echo ""

# Step 4: Check container status
echo "📊 Step 4/4: Checking container status..."
sleep 3
docker-compose ps
echo ""

echo "🎉 Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Check logs: docker-compose logs -f intelligence-app"
echo "   2. Test surveillance entry creation"
echo "   3. Verify assessment form displays correctly"
