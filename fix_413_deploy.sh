#!/bin/bash

# Fix 413 Request Entity Too Large - Deployment Script
# This script ensures nginx configuration is properly updated

echo "============================================"
echo "🔧 Fixing 413 Request Entity Too Large"
echo "============================================"
echo ""

# Step 1: Pull latest code
echo "📥 Step 1: Pulling latest code from GitHub..."
git pull origin main
if [ $? -ne 0 ]; then
    echo "❌ Failed to pull latest code"
    exit 1
fi
echo "✅ Code updated"
echo ""

# Step 2: Verify nginx-ssl.conf has the fix
echo "🔍 Step 2: Verifying nginx-ssl.conf configuration..."
if grep -q "client_max_body_size 100M" nginx/nginx-ssl.conf; then
    echo "✅ client_max_body_size 100M found in nginx-ssl.conf"
else
    echo "❌ ERROR: client_max_body_size NOT found in nginx-ssl.conf"
    echo "Please ensure you have the latest code!"
    exit 1
fi
echo ""

# Step 3: Stop nginx container
echo "🛑 Step 3: Stopping nginx container..."
docker compose stop intelligence-nginx
echo "✅ Nginx stopped"
echo ""

# Step 4: Remove nginx container to force recreate
echo "🗑️  Step 4: Removing old nginx container..."
docker compose rm -f intelligence-nginx
echo "✅ Old container removed"
echo ""

# Step 5: Recreate nginx container with new config
echo "🚀 Step 5: Creating new nginx container with updated config..."
docker compose up -d intelligence-nginx
echo "✅ New nginx container created"
echo ""

# Step 6: Wait for nginx to start
echo "⏳ Step 6: Waiting for nginx to start..."
sleep 3
echo ""

# Step 7: Verify nginx is running
echo "🔍 Step 7: Verifying nginx is running..."
if docker ps | grep -q intelligence-nginx; then
    echo "✅ Nginx container is running"
else
    echo "❌ ERROR: Nginx container is not running!"
    docker compose logs intelligence-nginx
    exit 1
fi
echo ""

# Step 8: Test nginx configuration
echo "🧪 Step 8: Testing nginx configuration..."
docker exec -it intelligence-nginx nginx -t
if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ ERROR: Nginx configuration has errors!"
    exit 1
fi
echo ""

# Step 9: Check if client_max_body_size is loaded
echo "🔍 Step 9: Verifying client_max_body_size in running container..."
BODY_SIZE=$(docker exec -it intelligence-nginx cat /etc/nginx/nginx.conf | grep -c "client_max_body_size 100M")
if [ "$BODY_SIZE" -gt 0 ]; then
    echo "✅ client_max_body_size 100M is loaded in nginx container"
    echo "   Found $BODY_SIZE occurrence(s)"
else
    echo "⚠️  WARNING: client_max_body_size NOT found in container!"
    echo "   Showing nginx config:"
    docker exec -it intelligence-nginx cat /etc/nginx/nginx.conf | head -30
fi
echo ""

# Step 10: Show nginx status
echo "📊 Step 10: Current nginx status..."
docker compose ps intelligence-nginx
echo ""

echo "============================================"
echo "✅ Deployment Complete!"
echo "============================================"
echo ""
echo "🧪 Test Instructions:"
echo "1. Go to https://10.96.135.11"
echo "2. Try saving an online patrol entry"
echo "3. The 413 error should be gone!"
echo ""
echo "📝 If you still see 413 error:"
echo "   Run: docker compose logs intelligence-nginx"
echo "   And check for any error messages"
echo ""
