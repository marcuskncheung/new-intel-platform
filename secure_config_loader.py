#!/usr/bin/env python3
"""
Secure Configuration Loader
SECURITY FIX for CodeQL Alert #24: Clear-text storage of sensitive information

This module provides secure loading of encrypted configuration data.
Sensitive data is stored encrypted and decrypted only when needed.
"""

import os
from pathlib import Path
from cryptography.fernet import Fernet


class SecureConfig:
    """Secure configuration loader with encrypted sensitive data"""
    
    def __init__(self):
        self._master_key = None
        self._fernet = None
        self._load_master_key()
    
    def _load_master_key(self):
        """Load the master encryption key"""
        master_key_file = Path('.master.key')
        
        if not master_key_file.exists():
            raise FileNotFoundError(
                "Master key file not found. Run secure_deploy.py first to generate encryption keys."
            )
        
        try:
            with open(master_key_file, 'rb') as f:
                self._master_key = f.read()
            self._fernet = Fernet(self._master_key)
        except Exception as e:
            raise RuntimeError(f"Failed to load master encryption key: {e}")
    
    def decrypt_config_value(self, encrypted_value):
        """
        Decrypt a configuration value
        
        Args:
            encrypted_value (str): Base64 encoded encrypted value
            
        Returns:
            str: Decrypted plaintext value
        """
        try:
            return self._fernet.decrypt(encrypted_value.encode()).decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt configuration value: {e}")
    
    def get_secret_key(self):
        """Get decrypted Flask SECRET_KEY"""
        encrypted_value = os.getenv('SECRET_KEY_ENCRYPTED')
        if not encrypted_value:
            # Fallback to plain text for backward compatibility (less secure)
            return os.getenv('SECRET_KEY')
        return self.decrypt_config_value(encrypted_value)
    
    def get_db_encryption_key(self):
        """Get decrypted database encryption key"""
        encrypted_value = os.getenv('DB_ENCRYPTION_KEY_ENCRYPTED')
        if not encrypted_value:
            # Fallback to plain text for backward compatibility (less secure)
            return os.getenv('DB_ENCRYPTION_KEY')
        return self.decrypt_config_value(encrypted_value)
    
    def get_jwt_secret_key(self):
        """Get decrypted JWT secret key"""
        encrypted_value = os.getenv('JWT_SECRET_KEY_ENCRYPTED')
        if not encrypted_value:
            # Fallback to plain text for backward compatibility (less secure)
            return os.getenv('JWT_SECRET_KEY')
        return self.decrypt_config_value(encrypted_value)
    
    def is_secure_mode(self):
        """Check if running in secure mode with encrypted configuration"""
        return (
            os.getenv('SECRET_KEY_ENCRYPTED') is not None and
            os.getenv('DB_ENCRYPTION_KEY_ENCRYPTED') is not None and
            Path('.master.key').exists()
        )


# Global secure config instance
_secure_config = None

def get_secure_config():
    """Get the global secure configuration instance"""
    global _secure_config
    if _secure_config is None:
        _secure_config = SecureConfig()
    return _secure_config

def get_config_value(key_name, encrypted_key_name=None, fallback_value=None):
    """
    Get a configuration value, trying encrypted version first
    
    Args:
        key_name (str): Plain text environment variable name
        encrypted_key_name (str): Encrypted environment variable name
        fallback_value: Default value if neither is found
        
    Returns:
        str: Configuration value
    """
    try:
        config = get_secure_config()
        
        if encrypted_key_name:
            encrypted_value = os.getenv(encrypted_key_name)
            if encrypted_value:
                return config.decrypt_config_value(encrypted_value)
        
        # Fallback to plain text
        plain_value = os.getenv(key_name)
        if plain_value:
            return plain_value
            
        return fallback_value
        
    except Exception:
        # If encryption fails, try plain text fallback
        return os.getenv(key_name, fallback_value)


# Convenience functions for common config values
def get_secret_key():
    """Get Flask SECRET_KEY (encrypted if available)"""
    return get_config_value('SECRET_KEY', 'SECRET_KEY_ENCRYPTED')

def get_db_encryption_key():
    """Get database encryption key (encrypted if available)"""
    return get_config_value('DB_ENCRYPTION_KEY', 'DB_ENCRYPTION_KEY_ENCRYPTED')

def get_jwt_secret_key():
    """Get JWT secret key (encrypted if available)"""
    return get_config_value('JWT_SECRET_KEY', 'JWT_SECRET_KEY_ENCRYPTED')


if __name__ == "__main__":
    # Test the secure configuration
    try:
        config = get_secure_config()
        print(f"🔒 Secure mode: {config.is_secure_mode()}")
        print("✅ Secure configuration loader working")
        
        if config.is_secure_mode():
            # Test decryption (don't print actual values for security)
            secret_key = config.get_secret_key()
            print(f"✅ SECRET_KEY loaded (length: {len(secret_key) if secret_key else 0})")
            
            db_key = config.get_db_encryption_key()
            print(f"✅ DB_ENCRYPTION_KEY loaded (length: {len(db_key) if db_key else 0})")
            
            jwt_key = config.get_jwt_secret_key()
            print(f"✅ JWT_SECRET_KEY loaded (length: {len(jwt_key) if jwt_key else 0})")
        else:
            print("⚠️  Running in fallback mode (plain text configuration)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
