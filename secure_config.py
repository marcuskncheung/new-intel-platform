#!/usr/bin/env python3
"""
Secure Configuration Manager
Handles secure configuration and secret management
"""

import os
import re
import secrets
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class SecureConfig:
    """Secure configuration management"""
    
    @staticmethod
    def generate_secret_key():
        """Generate a cryptographically secure secret key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def get_secret_key():
        """
        Get secret key with encryption support - SECURITY FIX for CodeQL Alert #24
        Tries encrypted version first, falls back to plain text for compatibility
        """
        try:
            # Import the secure config loader
            from secure_config_loader import get_secret_key
            secret_key = get_secret_key()
            
            if secret_key:
                return secret_key
                
        except Exception as e:
            print(f"⚠️  Encrypted config loading failed, using fallback: {e}")
        
        # Fallback to original behavior
        secret_key = os.environ.get("SECRET_KEY")
        
        if not secret_key:
            # In production, this should fail with an error
            # For development, generate a temporary secure key
            if os.environ.get("FLASK_ENV") == "production":
                raise RuntimeError("SECRET_KEY environment variable must be set in production")
            
            # Generate a secure random key for development
            secret_key = SecureConfig.generate_secret_key()
            print("⚠️  Using auto-generated secret key for development. Set SECRET_KEY environment variable for production.")
        
        return secret_key
    
    @staticmethod
    def get_database_url():
        """Get database URL with secure defaults"""
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            # Use absolute path for SQLite to avoid connection issues
            db_path = os.path.abspath(os.path.join(os.getcwd(), "instance", "users.db"))
            db_url = f"sqlite:///{db_path}"
        return db_url
    
    @staticmethod
    def get_encryption_key():
        """
        Get database encryption key with encryption support - SECURITY FIX for CodeQL Alert #24
        Tries encrypted version first, falls back to existing methods for compatibility
        """
        try:
            # Try encrypted configuration first
            from secure_config_loader import get_db_encryption_key
            encrypted_key = get_db_encryption_key()
            
            if encrypted_key:
                return encrypted_key.encode()
                
        except Exception as e:
            print(f"⚠️  Encrypted DB key loading failed, using fallback: {e}")
        
        # Fallback to original behavior
        # Try environment variable first
        env_key = os.environ.get('DB_ENCRYPTION_KEY')
        if env_key:
            return env_key.encode()
        
        # Try key file
        key_file = 'db_encryption.key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        
        # Generate new key with random salt
        password = os.environ.get('DB_PASSWORD', 'default-key-change-in-production').encode()
        salt = os.urandom(16)  # Random salt for better security
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        # Save key and salt for future use
        with open(key_file, 'wb') as f:
            f.write(key)
        with open('db_encryption.salt', 'wb') as f:
            f.write(salt)
        
        print("🔑 Generated new encryption key. Store db_encryption.key and db_encryption.salt securely.")
        return key
    
    @staticmethod
    def is_production():
        """Check if running in production environment"""
        return os.environ.get('FLASK_ENV') == 'production' or os.environ.get('PRODUCTION_MODE') == 'true'
    
    @staticmethod
    def get_flask_config():
        """Get secure Flask configuration"""
        db_url = SecureConfig.get_database_url()
        
        config = {
            'SECRET_KEY': SecureConfig.get_secret_key(),
            'SQLALCHEMY_DATABASE_URI': db_url,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SQLALCHEMY_ENGINE_OPTIONS': {
                'pool_pre_ping': True,
                'pool_recycle': 300,
                'connect_args': {
                    'timeout': 30,
                    'check_same_thread': False
                } if db_url.startswith('sqlite:') else {}
            }
        }
        
        # Session security settings
        config.update({
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'PERMANENT_SESSION_LIFETIME': 3600,  # 1 hour
        })
        
        # Only require HTTPS in production
        if SecureConfig.is_production():
            config.update({
                'SESSION_COOKIE_SECURE': True,
            })
        else:
            # For development/HTTP, don't require secure cookies
            config.update({
                'SESSION_COOKIE_SECURE': False,
            })
        
        return config
    
    @staticmethod
    def validate_environment():
        """Validate required environment variables"""
        required_vars = []
        missing_vars = []
        
        if SecureConfig.is_production():
            required_vars = ['SECRET_KEY', 'DATABASE_URL', 'DB_ENCRYPTION_KEY']
        
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
