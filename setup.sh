#!/bin/bash
# Intelligence Platform Setup Script
# This script initializes the platform with required files and settings

set -e

echo "🚀 Intelligence Platform Setup Starting..."

# Create required directories
echo "📁 Creating required directories..."
mkdir -p instance
mkdir -p logs
mkdir -p static/uploads
mkdir -p email_attachments
mkdir -p data/email_files

# Generate encryption key if not exists
if [ ! -f "db_encryption.key" ]; then
    echo "🔐 Generating database encryption key..."
    python3 -c "
from cryptography.fernet import Fernet
import base64
key = Fernet.generate_key()
with open('db_encryption.key', 'wb') as f:
    f.write(key)
print('✅ Database encryption key generated: db_encryption.key')
"
fi

# Generate Flask secret key if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "🔑 Creating .env file..."
    cp .env.example .env
    
    # Generate a random secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i.bak "s/your-secret-key-here-minimum-32-characters/$SECRET_KEY/g" .env
    
    # Read the generated encryption key and update .env
    if [ -f "db_encryption.key" ]; then
        DB_KEY=$(cat db_encryption.key | base64 -w 0 2>/dev/null || cat db_encryption.key | base64)
        sed -i.bak "s/your-44-character-base64-encoded-fernet-key-here=/$DB_KEY/g" .env
    fi
    
    echo "✅ .env file created with generated keys"
    echo "⚠️  Please edit .env file to configure email and other settings"
fi

# Initialize database if it doesn't exist
if [ ! -f "instance/users.db" ]; then
    echo "🗄️  Initializing database..."
    python3 -c "
import sys
import os
sys.path.append('.')

# Load environment variables
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()

try:
    from app1_production import app, init_db
    with app.app_context():
        init_db()
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'⚠️  Database initialization failed: {e}')
    print('   You may need to run this manually after starting the application')
"
fi

# Set proper permissions
echo "🔒 Setting file permissions..."
chmod 600 .env 2>/dev/null || true
chmod 600 db_encryption.key 2>/dev/null || true
chmod 600 instance/users.db* 2>/dev/null || true
chmod 755 instance
chmod 755 logs
chmod 755 static/uploads

echo "✅ Setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file to configure your email settings"
echo "2. Run: docker-compose up -d"
echo "3. Access the platform at: https://localhost"
echo ""
echo "🔐 Default admin login will be created on first run"
echo "   Check the application logs for admin credentials"
