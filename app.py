# app.py
# Main application factory - Blueprint architecture
# This is the new entry point for the refactored application

import os
import sys
import re
import json
import base64
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask

# Import extensions
from extensions import db, login_mgr, migrate, cache, HK_TZ, CACHING_AVAILABLE

# Import models
from models import (
    User, AuditLog, FeatureSettings,
    Email, Attachment, EmailAllegedSubject, EmailAnalysisLock,
    WhatsAppEntry, WhatsAppImage,
    OnlinePatrolEntry, OnlinePatrolPhoto,
    SurveillanceEntry, Target,
    ReceivedByHandEntry,
    CaseProfile
)

# Import blueprints
from blueprints import (
    auth_bp, main_bp, admin_bp,
    email_intel_bp, whatsapp_intel_bp, patrol_intel_bp,
    surveillance_intel_bp, received_by_hand_intel_bp,
    poi_bp, int_reference_bp, analytics_bp,
    ai_bp, export_bp, api_bp, tools_bp
)

# Import utility functions
from utils.helpers import get_hk_time, utc_to_hk, format_hk_time


def create_app(config_name=None):
    """Application factory function"""
    
    app = Flask(__name__, static_folder="static")
    
    # ========================================
    # CONFIGURATION
    # ========================================
    
    # Import secure configuration
    from secure_config import SecureConfig
    
    try:
        SecureConfig.validate_environment()
        secure_config = SecureConfig.get_flask_config()
        app.config.update(secure_config)
        print("✅ SECURE MODE: Configuration loaded with proper security controls")
    except RuntimeError as e:
        if SecureConfig.is_production():
            print(f"❌ PRODUCTION ERROR: {e}")
            raise e
        else:
            app.config.update(SecureConfig.get_flask_config())
            print("⚠️  DEVELOPMENT MODE: Using secure fallback configuration")
    
    # Database configuration
    from database_config import get_database_config, get_db_info
    db_config = get_database_config()
    app.config.update(db_config)
    
    # ========================================
    # INITIALIZE EXTENSIONS
    # ========================================
    
    db.init_app(app)
    login_mgr.init_app(app)
    login_mgr.login_view = "auth.login"  # Blueprint-aware login view
    migrate.init_app(app, db)
    
    if CACHING_AVAILABLE and cache:
        cache.init_app(app)
        print("✅ Flask-Caching initialized")
    
    print(f"🗄️  Database Type: {get_db_info()}")
    
    # ========================================
    # USER LOADER
    # ========================================
    
    @login_mgr.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # ========================================
    # TEMPLATE FILTERS
    # ========================================
    
    @app.template_filter('strftime')
    def _jinja2_filter_datetime(value, format='%Y-%m-%d %H:%M:%S'):
        """🇭🇰 Format datetime in Hong Kong timezone"""
        if value is None or value == "":
            return ""
        if hasattr(value, 'strftime'):
            return format_hk_time(value, format)
        if isinstance(value, str):
            for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
                try:
                    parsed_dt = datetime.strptime(value, fmt)
                    return format_hk_time(parsed_dt, format)
                except ValueError:
                    continue
            return value
        return str(value) if value else ""
    
    @app.template_filter('safe_datetime')
    def safe_datetime_filter(value, format='%Y-%m-%d %H:%M'):
        """🇭🇰 Safe datetime formatting in Hong Kong timezone"""
        if value is None or value == "":
            return ""
        if hasattr(value, 'strftime'):
            return format_hk_time(value, format)
        if isinstance(value, str):
            for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
                try:
                    parsed_dt = datetime.strptime(value, fmt)
                    return format_hk_time(parsed_dt, format)
                except ValueError:
                    continue
            return value[:16] if len(value) > 16 else value
        return str(value)[:16] if value else ""
    
    @app.template_filter('regex_replace')
    def regex_replace(s, find, replace):
        return re.sub(find, replace, s)
    
    @app.template_filter('fromjson')
    def fromjson_filter(value):
        """Parse JSON string to Python object for Jinja2 templates"""
        if not value:
            return []
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return []
        return value
    
    @app.template_filter('b64decode')
    def b64decode_filter(data):
        """Template filter to decode base64 data"""
        try:
            return base64.b64decode(data).decode('utf-8')
        except Exception:
            return data
    
    @app.template_filter('from_json')
    def from_json_filter(data):
        """Template filter to parse JSON data"""
        try:
            return json.loads(data) if data else []
        except Exception:
            return []
    
    @app.template_filter('date_format')
    def date_format_filter(value, format='%Y-%m-%d %H:%M:%S'):
        """Template filter to format datetime values"""
        if value == 'now' or value is None:
            return get_hk_time().strftime(format)
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except Exception:
                return value
        if isinstance(value, datetime):
            return value.strftime(format)
        return value
    
    # ========================================
    # CONTEXT PROCESSOR
    # ========================================
    
    @app.context_processor
    def inject_helpers():
        """Make helper functions available in all templates"""
        from flask_login import current_user
        
        def can_see_feature(feature_key):
            """Check if current user can see a feature"""
            try:
                setting = FeatureSettings.query.filter_by(feature_key=feature_key).first()
                if not setting:
                    return True
                if not setting.is_enabled:
                    return False
                if setting.admin_only:
                    if current_user.is_authenticated and hasattr(current_user, 'is_admin'):
                        return current_user.is_admin() if callable(current_user.is_admin) else current_user.is_admin
                    return False
                return True
            except Exception:
                return True
        
        def get_source_display_id(source_type, source_id):
            """Format source-specific ID for display"""
            return f"{source_type}-{source_id}"
        
        return dict(
            get_hk_time=get_hk_time,
            format_hk_time=format_hk_time,
            can_see_feature=can_see_feature,
            get_source_display_id=get_source_display_id,
        )
    
    # ========================================
    # REGISTER BLUEPRINTS
    # ========================================
    
    # Core blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Intelligence source blueprints
    app.register_blueprint(email_intel_bp, url_prefix='/int_source')
    app.register_blueprint(whatsapp_intel_bp, url_prefix='/whatsapp')
    app.register_blueprint(patrol_intel_bp, url_prefix='/patrol')
    app.register_blueprint(surveillance_intel_bp, url_prefix='/surveillance')
    app.register_blueprint(received_by_hand_intel_bp, url_prefix='/received_by_hand')
    
    # Feature blueprints
    app.register_blueprint(poi_bp, url_prefix='/poi')
    app.register_blueprint(int_reference_bp, url_prefix='/int_reference')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(ai_bp, url_prefix='/ai')
    app.register_blueprint(export_bp, url_prefix='/export')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(tools_bp, url_prefix='/tools')
    
    # ========================================
    # SECURITY CONFIGURATION
    # ========================================
    
    from security_headers import configure_security
    app = configure_security(app)
    
    # ========================================
    # DATABASE INITIALIZATION
    # ========================================
    
    with app.app_context():
        db.create_all()
        print("✅ Database tables created/verified")
    
    return app


# ========================================
# MAIN ENTRY POINT
# ========================================

if __name__ == '__main__':
    app = create_app()
    
    # Production server settings for Docker
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 8080))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"\n🚀 Starting Flask application on {host}:{port}")
    print(f"   Debug mode: {debug_mode}")
    print(f"   Open: http://{host}:{port}/\n")
    
    app.run(host=host, port=port, debug=debug_mode)
