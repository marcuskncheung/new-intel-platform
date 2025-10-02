#!/bin/bash
# Intelligence Platform - Server Initialization Script
# Run this script after pulling the Docker image to set up the platform

set -e

echo "🚀 Intelligence Platform Server Setup"
echo "====================================="

# Function to generate secure key
generate_secret_key() {
    python3 -c "import secrets; print(secrets.token_hex(32))"
}

# Function to generate Fernet key
generate_fernet_key() {
    python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
}

# Create required directories
echo "📁 Creating application directories..."
mkdir -p instance
mkdir -p logs
mkdir -p static/uploads
mkdir -p email_attachments
mkdir -p data/email_files

# Create environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔧 Creating environment configuration..."
    
    SECRET_KEY=$(generate_secret_key)
    DB_KEY=$(generate_fernet_key)
    
    cat > .env << EOF
# Production Environment Configuration
# Generated on $(date)

FLASK_ENV=production
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=8080

# Security Keys (KEEP THESE SECRET!)
SECRET_KEY=${SECRET_KEY}
DB_ENCRYPTION_KEY=${DB_KEY}

# Database
DATABASE_URL=sqlite:///instance/users.db

# Email Configuration (Update these with your SMTP settings)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-app-password

# Exchange Configuration (Optional - for email integration)
EXCHANGE_SERVER=
EXCHANGE_USERNAME=
EXCHANGE_PASSWORD=

# Admin Account (Change these!)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=ChangeThisPassword123!

# File Upload Limits
MAX_CONTENT_LENGTH=52428800
UPLOAD_FOLDER=static/uploads
EOF

    echo "✅ Environment file created: .env"
    echo "⚠️  IMPORTANT: Edit .env file to configure your email and admin settings"
else
    echo "✅ Environment file already exists"
fi

# Initialize database
echo "🗄️  Initializing database..."
python3 << 'PYTHON_SCRIPT'
import os
import sys
import sqlite3
from pathlib import Path

# Ensure instance directory exists
Path("instance").mkdir(exist_ok=True)

# Create basic database structure
db_path = "instance/users.db"
if not os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    
    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_token TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create intelligence_sources table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS intelligence_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            source_type TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Create audit_log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            resource_type TEXT,
            resource_id INTEGER,
            ip_address TEXT,
            user_agent TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized with basic schema")
else:
    print("✅ Database already exists")
PYTHON_SCRIPT

# Set proper permissions
echo "🔒 Setting secure file permissions..."
chmod 600 .env
chmod 600 instance/users.db* 2>/dev/null || true
chmod 755 instance
chmod 755 logs
chmod 755 static/uploads

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "📋 Next Steps:"
echo "1. Edit .env file with your actual email/admin settings:"
echo "   nano .env"
echo ""
echo "2. Start the platform:"
echo "   docker-compose up -d"
echo ""
echo "3. Access the platform:"
echo "   https://your-server-ip"
echo ""
echo "🔐 Security Notes:"
echo "- Keep your .env file secure and never commit it to version control"
echo "- Change the default admin password after first login"
echo "- Configure email settings for notifications"
echo ""
echo "📝 Configuration files created:"
echo "- .env (environment configuration)"
echo "- instance/users.db (application database)"
echo ""
