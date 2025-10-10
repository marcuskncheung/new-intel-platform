#!/bin/bash

# Enforcement Intelligence Platform - Production Deployment Script
# Usage: ./deploy.sh [environment]

set -e

# Configuration - Updated with your actual GitHub repository
GITHUB_USERNAME="marcuskncheung"
REPO_NAME="intel-platform"
ENVIRONMENT=${1:-production}
REPO_URL="ghcr.io/${GITHUB_USERNAME}/${REPO_NAME}"
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env.production"

echo "🚀 Starting deployment of Enforcement Intelligence Platform"
echo "Environment: $ENVIRONMENT"
echo "Repository: $REPO_URL"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "🔍 Checking dependencies..."
if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p {nginx/ssl,nginx/logs,backups,logs}

# Generate SSL certificates if they don't exist
if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then
    echo "🔐 Generating SSL certificates..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=HK/ST=Hong Kong/L=Hong Kong/O=Intelligence Agency/CN=intelligence.local"
    chmod 600 nginx/ssl/key.pem
    chmod 644 nginx/ssl/cert.pem
    echo "✅ SSL certificates generated"
fi

# Setup environment configuration
echo "📋 Setting up environment configuration..."
if [ -f ".env.production" ]; then
    cp .env.production .env
    echo "✅ Using provided production environment configuration"
elif [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  Creating default environment file: $ENV_FILE"
    cat > "$ENV_FILE" << EOF
# Production Environment Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$(openssl rand -base64 32)
DB_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
DATABASE_URL=sqlite:////app/instance/users.db

# Email Configuration (optional)
# MAIL_SERVER=smtp.your-email-provider.com
# MAIL_PORT=587
# MAIL_USE_TLS=True
# MAIL_USERNAME=your-email@domain.com
# MAIL_PASSWORD=your-email-password

# Exchange Configuration (optional)
# EXCHANGE_SERVER=your-exchange-server.com
# EXCHANGE_USERNAME=exchange-user
# EXCHANGE_PASSWORD=exchange-password
EOF
    echo "📝 Please edit $ENV_FILE with your production values"
    echo "⚠️  Make sure to set secure SECRET_KEY and DB_ENCRYPTION_KEY"
fi

# Pull latest images
echo "📥 Pulling latest Docker images..."
docker pull $REPO_URL:latest || {
    echo "❌ Failed to pull Docker image. Make sure you're logged in to GitHub Container Registry:"
    echo "   docker login ghcr.io -u YOUR_GITHUB_USERNAME"
    exit 1
}

# Stop existing containers
echo "⏹️  Stopping existing containers..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down || true

# Backup database if it exists
if [ -f "intelligence_data/users.db" ]; then
    echo "💾 Creating database backup..."
    cp intelligence_data/users.db "backups/users_backup_$(date +%Y%m%d_%H%M%S).db"
fi

# Start services
echo "🚀 Starting services..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Health check
echo "🏥 Performing health check..."
for i in {1..30}; do
    if curl -f http://localhost/health >/dev/null 2>&1; then
        echo "✅ Services are healthy!"
        break
    fi
    echo "Waiting for services... ($i/30)"
    sleep 5
done

# Display status
echo "📊 Container status:"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "🌐 Access URLs:"
echo "   HTTPS: https://your-domain.com"
echo "   HTTP:  http://your-domain.com (redirects to HTTPS)"
echo ""
echo "📋 Useful commands:"
echo "   View logs:     docker compose -f $COMPOSE_FILE logs -f"
echo "   Stop services: docker compose -f $COMPOSE_FILE down"
echo "   Update:        ./deploy.sh"
echo ""
echo "⚠️  Next steps:"
echo "   1. Update nginx/nginx.conf with your actual domain name"
echo "   2. Replace self-signed certificates with real SSL certificates"
echo "   3. Configure firewall to allow ports 80 and 443"
echo "   4. Set up monitoring and backup procedures"
