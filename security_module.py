#!/usr/bin/env python3
"""
Database Security Enhancement Module
Adds encryption and comprehensive audit trails to the Intelligence Platform
"""

import os
import hashlib
import json
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import uuid
from functools import wraps
from flask import request, session

class DatabaseSecurity:
    """Handle database encryption and security"""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _get_or_create_key(self):
        """Get or create encryption key from environment or file"""
        # Try environment variable first (production)
        env_key = os.environ.get('DB_ENCRYPTION_KEY')
        if env_key:
            return env_key.encode()
        
        # Try key file
        key_file = 'db_encryption.key'
        salt_file = 'db_encryption.salt'
        
        if os.path.exists(key_file) and os.path.exists(salt_file):
            with open(key_file, 'rb') as f:
                return f.read()
        
        # Generate new key with random salt (secure)
        password = os.environ.get('DB_PASSWORD', 'intelligence-platform-key-2025').encode()
        salt = os.urandom(16)  # Random salt for better security
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        # Save key and salt securely
        with open(key_file, 'wb') as f:
            f.write(key)
        with open(salt_file, 'wb') as f:
            f.write(salt)
        
        print("🔑 Generated new encryption key with random salt for enhanced security")
        
        # Save key for future use
        with open(key_file, 'wb') as f:
            f.write(key)
        
        print("🔐 Database encryption key generated and saved")
        return key
    
    def encrypt_sensitive_data(self, data):
        """Encrypt sensitive data before database storage"""
        if not data:
            return None
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif not isinstance(data, bytes):
            data = str(data).encode('utf-8')
        
        encrypted = self.cipher.encrypt(data)
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt_sensitive_data(self, encrypted_data):
        """Decrypt sensitive data after database retrieval"""
        if not encrypted_data:
            return None
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            print(f"⚠️ Decryption error: {e}")
            return None

class AuditTrail:
    """Comprehensive audit trail system"""
    
    def __init__(self, db):
        self.db = db
    
    def log_action(self, user_id, action, resource_type, resource_id=None, 
                   details=None, ip_address=None, user_agent=None):
        """Log user action for audit trail"""
        from app1_production import AuditLog  # Import here to avoid circular import
        
        # Don't set id manually - let database auto-increment handle it
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details) if details else None,
            ip_address=ip_address or self._get_client_ip(),
            user_agent=user_agent or self._get_user_agent(),
            timestamp=datetime.utcnow(),
            severity='info'  # Set default severity
        )
        
        try:
            self.db.session.add(audit_entry)
            self.db.session.commit()
        except Exception as e:
            print(f"⚠️ Audit log error: {e}")
            self.db.session.rollback()
    
    def _get_client_ip(self):
        """Get client IP address"""
        if request:
            return request.environ.get('HTTP_X_FORWARDED_FOR', 
                                     request.environ.get('REMOTE_ADDR', 'unknown'))
        return 'system'
    
    def _get_user_agent(self):
        """Get client user agent"""
        if request:
            return request.headers.get('User-Agent', 'unknown')[:500]  # Limit length
        return 'system'

# Global security instances
db_security = DatabaseSecurity()
audit_trail = None  # Will be initialized when db is available

def init_security(db):
    """Initialize security components"""
    global audit_trail
    audit_trail = AuditTrail(db)
    print("🔐 Database security and audit trail initialized")

def audit_action(action, resource_type, resource_id=None, details=None):
    """Decorator for automatic audit logging"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = None
            try:
                from flask_login import current_user
                if hasattr(current_user, 'id'):
                    user_id = current_user.id
            except:
                pass
            
            # Execute the function
            result = func(*args, **kwargs)
            
            # Log the action
            if audit_trail:
                audit_trail.log_action(
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    details=details
                )
            
            return result
        return wrapper
    return decorator

def encrypt_field(data):
    """Encrypt a database field"""
    return db_security.encrypt_sensitive_data(data)

def decrypt_field(encrypted_data):
    """Decrypt a database field"""
    return db_security.decrypt_sensitive_data(encrypted_data)

# Security validation functions
def validate_data_integrity(data, expected_hash=None):
    """Validate data integrity using hash"""
    if not data:
        return False
    
    current_hash = hashlib.sha256(str(data).encode()).hexdigest()
    return current_hash == expected_hash if expected_hash else current_hash

def get_data_hash(data):
    """Get SHA256 hash of data for integrity checking"""
    return hashlib.sha256(str(data).encode()).hexdigest()
