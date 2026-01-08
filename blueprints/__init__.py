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
]
