#!/usr/bin/env python3
"""
Secure Production Deployment Script
Configures the application for secure production deployment
"""

import os
import re
import sys
import secrets
import subprocess
from pathlib import Path
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def generate_master_key():
    """Generate or load master encryption key for sensitive data storage - CodeQL Alert #24 fix"""
    master_key_file = Path('.master.key')
    
    if master_key_file.exists():
        # Load existing master key
        with open(master_key_file, 'rb') as f:
            return f.read()
    else:
        # Generate new master key
        key = Fernet.generate_key()
        with open(master_key_file, 'wb') as f:
            f.write(key)
        os.chmod(master_key_file, 0o600)  # Secure permissions
        print("🔐 Generated new master encryption key")
        return key

def encrypt_sensitive_data(data, master_key):
    """Encrypt sensitive data using master key - CodeQL Alert #24 fix"""
    fernet = Fernet(master_key)
    return fernet.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted_data, master_key):
    """Decrypt sensitive data using master key - CodeQL Alert #24 fix"""
    fernet = Fernet(master_key)
    return fernet.decrypt(encrypted_data.encode()).decode()

def generate_secure_keys():
    """Generate secure keys for production"""
    print("🔑 Generating secure keys...")
    
    # Generate Flask secret key
    secret_key = secrets.token_urlsafe(32)
    
    # Generate database encryption key
    db_key = secrets.token_urlsafe(32)
    
    # Generate JWT secret (if needed)
    jwt_secret = secrets.token_urlsafe(32)
    
    return {
        'SECRET_KEY': secret_key,
        'DB_ENCRYPTION_KEY': db_key,
        'JWT_SECRET_KEY': jwt_secret
    }

def create_env_file(keys):
    """
    Create .env file with encrypted sensitive configuration
    SECURITY FIX for CodeQL Alert #24: Clear-text storage of sensitive information
    """
    print("📝 Creating secure .env configuration with encrypted sensitive data...")
    
    # Generate master key for encrypting sensitive data
    master_key = generate_master_key()
    
    # Encrypt sensitive keys before storing
    encrypted_secret_key = encrypt_sensitive_data(keys['SECRET_KEY'], master_key)
    encrypted_db_key = encrypt_sensitive_data(keys['DB_ENCRYPTION_KEY'], master_key)
    encrypted_jwt_key = encrypt_sensitive_data(keys['JWT_SECRET_KEY'], master_key)
    
    env_content = f"""# Production Configuration - DO NOT COMMIT TO VERSION CONTROL
# Generated on: {__import__('datetime').datetime.now().isoformat()}
# SECURITY: Sensitive data is encrypted using master key (.master.key)

# Flask Configuration (ENCRYPTED)
SECRET_KEY_ENCRYPTED={encrypted_secret_key}
FLASK_ENV=production
FLASK_DEBUG=False

# Database Configuration (ENCRYPTED)
DATABASE_URL=sqlite:///instance/users.db
DB_ENCRYPTION_KEY_ENCRYPTED={encrypted_db_key}

# JWT Configuration (ENCRYPTED)  
JWT_SECRET_KEY_ENCRYPTED={encrypted_jwt_key}

# Security Configuration
FORCE_HTTPS=true
SESSION_TIMEOUT=3600

# CORS Configuration
CORS_ORIGINS=https://your-domain.com

# Email Configuration (if needed)
MAIL_SERVER=smtp.your-email-provider.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=your-email-password

# SSL Configuration
SSL_CERT_FILE=cert.pem
SSL_KEY_FILE=key.pem

# Rate Limiting
RATE_LIMIT_ENABLED=true
MAX_REQUESTS_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    # Set secure permissions
    os.chmod('.env', 0o600)
    print("✅ .env file created with secure permissions")

def create_ssl_certificates():
    """Create self-signed SSL certificates for development/testing"""
    print("🔒 Creating SSL certificates...")
    
    try:
        # Generate private key
        subprocess.run([
            'openssl', 'genrsa', '-out', 'key.pem', '2048'
        ], check=True, capture_output=True)
        
        # Generate certificate
        subprocess.run([
            'openssl', 'req', '-new', '-x509', '-key', 'key.pem', 
            '-out', 'cert.pem', '-days', '365',
            '-subj', '/C=US/ST=State/L=City/O=Organization/CN=localhost'
        ], check=True, capture_output=True)
        
        # Set secure permissions (0o600 = rw-------, 0o644 = rw-r--r--)
        os.chmod('key.pem', 0o600)  # Private key should be read-write for owner only
        os.chmod('cert.pem', 0o644)  # Certificate can be readable by others
        
        print("✅ SSL certificates created")
        print("⚠️  Note: These are self-signed certificates for testing only")
        print("   For production, use certificates from a trusted CA")
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  OpenSSL not found or failed. SSL certificates not created.")
        print("   Install OpenSSL or manually create SSL certificates")

def create_production_dirs():
    """Create necessary directories for production"""
    print("📁 Creating production directories...")
    
    directories = [
        'instance',
        'logs',
        'backups',
        'uploads',
        'static/uploads',
        'email_attachments'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def set_secure_permissions():
    """Set secure file permissions"""
    print("🔐 Setting secure file permissions...")
    
    # Secure application files
    sensitive_files = [
        'app1_production.py',
        'security_module.py',
        'secure_config.py',
        'secure_db_manager.py',
        '.env'
    ]
    
    for file in sensitive_files:
        if os.path.exists(file):
            os.chmod(file, 0o600)
            print(f"✅ Secured: {file}")
    
    # Secure directories
    secure_dirs = ['instance', 'logs', 'backups']
    for directory in secure_dirs:
        if os.path.exists(directory):
            os.chmod(directory, 0o700)
            print(f"✅ Secured directory: {directory}")

def create_systemd_service():
    """Create systemd service file for production deployment"""
    print("⚙️  Creating systemd service file...")
    
    current_dir = os.getcwd()
    user = os.environ.get('USER', 'app')
    
    service_content = f"""[Unit]
Description=Intelligence Platform Flask Application
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={current_dir}
Environment=FLASK_ENV=production
Environment=PYTHONPATH={current_dir}
ExecStart={sys.executable} app1_production.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths={current_dir}/instance {current_dir}/logs {current_dir}/backups

[Install]
WantedBy=multi-user.target
"""
    
    service_file = 'intelligence-platform.service'
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    print(f"✅ Systemd service file created: {service_file}")
    print(f"   To install: sudo cp {service_file} /etc/systemd/system/")
    print(f"   To enable: sudo systemctl enable intelligence-platform")
    print(f"   To start: sudo systemctl start intelligence-platform")

def create_nginx_config():
    """Create nginx configuration"""
    print("🌐 Creating nginx configuration...")
    
    nginx_config = """# Intelligence Platform Nginx Configuration
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Proxy to Flask application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static {
        alias /path/to/your/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # File upload size limit
    client_max_body_size 50M;
}
"""
    
    with open('nginx-intelligence-platform.conf', 'w') as f:
        f.write(nginx_config)
    
    print("✅ Nginx configuration created: nginx-intelligence-platform.conf")
    print("   Copy to: /etc/nginx/sites-available/")
    print("   Enable with: sudo ln -s /etc/nginx/sites-available/nginx-intelligence-platform.conf /etc/nginx/sites-enabled/")

def create_backup_script():
    """Create automated backup script"""
    print("💾 Creating backup script...")
    
    backup_script = """#!/bin/bash
# Intelligence Platform Backup Script

BACKUP_DIR="/path/to/backups"
APP_DIR="/path/to/app"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="intelligence_platform_backup_${DATE}.tar.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create backup
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \\
    --exclude="$APP_DIR/__pycache__" \\
    --exclude="$APP_DIR/*.pyc" \\
    --exclude="$APP_DIR/logs" \\
    --exclude="$APP_DIR/.git" \\
    "$APP_DIR"

# Keep only last 30 backups
cd "$BACKUP_DIR"
ls -t *.tar.gz | tail -n +31 | xargs -r rm

echo "Backup completed: $BACKUP_FILE"

# Optional: Upload to cloud storage
# aws s3 cp "$BACKUP_DIR/$BACKUP_FILE" s3://your-backup-bucket/
"""
    
    with open('backup.sh', 'w') as f:
        f.write(backup_script)
    
    # Use restrictive permissions for security - executable only by owner (0o750 = rwxr-x---)
    os.chmod('backup.sh', 0o700)  # Even more secure: only owner can read/write/execute
    print("✅ Backup script created: backup.sh")

def main():
    """Main deployment function"""
    print("🚀 Intelligence Platform - Secure Production Deployment")
    print("=" * 60)
    
    # Generate secure keys
    keys = generate_secure_keys()
    
    # Create configuration
    create_env_file(keys)
    
    # Create directories
    create_production_dirs()
    
    # Set permissions
    set_secure_permissions()
    
    # Create SSL certificates (optional)
    create_ssl_certificates()
    
    # Create service files
    create_systemd_service()
    create_nginx_config()
    create_backup_script()
    
    print("\n✅ Production deployment setup completed!")
    print("\n📋 Next Steps:")
    print("1. Review and customize the .env file")
    print("2. Install the systemd service")
    print("3. Configure nginx with your SSL certificates")
    print("4. Set up automated backups with backup.sh")
    print("5. Test the application in production mode")
    print("\n⚠️  Security Reminders:")
    print("- Never commit .env files to version control")
    print("- Use proper SSL certificates in production")
    print("- Regularly update dependencies")
    print("- Monitor logs for security issues")
    print("- Set up firewall rules")

if __name__ == "__main__":
    main()
