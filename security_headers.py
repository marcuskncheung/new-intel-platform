#!/usr/bin/env python3
"""
Security Headers and HTTPS Configuration
Provides security headers and HTTPS enforcement
"""

from flask import request, make_response, redirect
from functools import wraps
import ssl
import os

class SecurityHeaders:
    """Security headers management"""
    
    @staticmethod
    def add_security_headers(response):
        """Add comprehensive security headers"""
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        response.headers.update({
            # Content Security Policy
            'Content-Security-Policy': csp,
            
            # XSS Protection
            'X-XSS-Protection': '1; mode=block',
            
            # Content Type Options
            'X-Content-Type-Options': 'nosniff',
            
            # Frame Options
            'X-Frame-Options': 'DENY',
            
            # Referrer Policy
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            
            # Feature Policy
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        })
        
        # HTTPS-specific headers
        if request.is_secure or os.environ.get('FORCE_HTTPS') == 'true':
            response.headers.update({
                # HSTS
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
                
                # Secure cookies
                'Set-Cookie': response.headers.get('Set-Cookie', '') + '; Secure; HttpOnly; SameSite=Lax'
            })
        
        return response
    
    @staticmethod
    def security_headers_middleware(app):
        """Flask middleware to add security headers to all responses"""
        @app.after_request
        def after_request(response):
            return SecurityHeaders.add_security_headers(response)
        
        return app
    
    @staticmethod
    def force_https(f):
        """Decorator to force HTTPS for specific routes"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_secure and os.environ.get('FORCE_HTTPS') == 'true':
                return redirect(request.url.replace('http://', 'https://'), code=301)
            return f(*args, **kwargs)
        return decorated_function

class HTTPSConfig:
    """HTTPS configuration helper"""
    
    @staticmethod
    def get_ssl_context():
        """Get SSL context for HTTPS"""
        cert_file = os.environ.get('SSL_CERT_FILE', 'cert.pem')
        key_file = os.environ.get('SSL_KEY_FILE', 'key.pem')
        
        if os.path.exists(cert_file) and os.path.exists(key_file):
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(cert_file, key_file)
            return context
        
        return None
    
    @staticmethod
    def is_https_enabled():
        """Check if HTTPS is enabled"""
        return (
            os.environ.get('FORCE_HTTPS') == 'true' or
            os.environ.get('FLASK_ENV') == 'production'
        )

def configure_security(app):
    """Configure comprehensive security for Flask app"""
    # Add security headers middleware
    SecurityHeaders.security_headers_middleware(app)
    
    # Configure session security
    if HTTPSConfig.is_https_enabled():
        app.config.update({
            'SESSION_COOKIE_SECURE': True,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'PERMANENT_SESSION_LIFETIME': 3600,  # 1 hour
        })
    
    print("🛡️  Security headers and HTTPS configuration applied")
    
    return app
