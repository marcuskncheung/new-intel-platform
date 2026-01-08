# blueprints/__init__.py
# Blueprint registration module
# Each blueprint is defined in its own file to avoid circular imports

# Import blueprint instances from their respective files
from blueprints.auth import auth_bp
from blueprints.main import main_bp
from blueprints.admin import admin_bp
from blueprints.email_intel import email_intel_bp
from blueprints.whatsapp_intel import whatsapp_intel_bp
from blueprints.patrol_intel import patrol_intel_bp
from blueprints.surveillance_intel import surveillance_intel_bp
from blueprints.received_by_hand_intel import received_by_hand_intel_bp
from blueprints.poi import poi_bp
from blueprints.int_reference import int_reference_bp
from blueprints.analytics import analytics_bp
from blueprints.ai import ai_bp
from blueprints.export import export_bp
from blueprints.api import api_bp
from blueprints.tools import tools_bp

__all__ = [
    'auth_bp',
    'main_bp',
    'admin_bp',
    'email_intel_bp',
    'whatsapp_intel_bp',
    'patrol_intel_bp',
    'surveillance_intel_bp',
    'received_by_hand_intel_bp',
    'poi_bp',
    'int_reference_bp',
    'analytics_bp',
    'ai_bp',
    'export_bp',
    'api_bp',
    'tools_bp',
    'register_blueprints',
]


def register_blueprints(app):
    """
    Register all blueprints with the Flask application.
    
    This function should be called from the app factory (create_app)
    to register all modular blueprints.
    
    Blueprint URL Prefixes:
    - auth: / (login, logout, register)
    - main: / (index, dashboard)
    - admin: /admin (user management, settings)
    - email_intel: / (email intelligence routes)
    - whatsapp_intel: / (WhatsApp intelligence routes)
    - patrol_intel: / (online patrol routes)
    - surveillance_intel: / (surveillance routes)
    - received_by_hand_intel: / (received by hand routes)
    - poi: / (POI/Alleged Subject routes)
    - int_reference: / (INT reference routes)
    - analytics: / (analytics routes)
    - ai: / (AI analysis routes)
    - export: / (export routes)
    - api: / (API routes)
    - tools: / (utility tools)
    """
    # Core blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Intel source blueprints
    app.register_blueprint(email_intel_bp)
    app.register_blueprint(whatsapp_intel_bp)
    app.register_blueprint(patrol_intel_bp)
    app.register_blueprint(surveillance_intel_bp)
    app.register_blueprint(received_by_hand_intel_bp)
    
    # POI and reference management
    app.register_blueprint(poi_bp)
    app.register_blueprint(int_reference_bp)
    
    # Analytics and AI
    app.register_blueprint(analytics_bp)
    app.register_blueprint(ai_bp)
    
    # Export and API
    app.register_blueprint(export_bp)
    app.register_blueprint(api_bp)
    
    # Utility tools
    app.register_blueprint(tools_bp)
    
    return app
