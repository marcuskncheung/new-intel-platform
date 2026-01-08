# blueprints/__init__.py
# Blueprint registration module

from flask import Blueprint

# Create blueprint instances
auth_bp = Blueprint('auth', __name__)
main_bp = Blueprint('main', __name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Intelligence Source Blueprints (placeholders - routes still in app1_production.py)
email_bp = Blueprint('email', __name__)
whatsapp_bp = Blueprint('whatsapp', __name__)
patrol_bp = Blueprint('patrol', __name__)
surveillance_bp = Blueprint('surveillance', __name__)
received_by_hand_bp = Blueprint('received_by_hand', __name__)

# Feature Blueprints (placeholders)
poi_bp = Blueprint('poi', __name__)
int_reference_bp = Blueprint('int_reference', __name__)
analytics_bp = Blueprint('analytics', __name__)
ai_bp = Blueprint('ai', __name__)
export_bp = Blueprint('export', __name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')
tools_bp = Blueprint('tools', __name__)


def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    # Import blueprints with routes
    from blueprints import auth, main, admin
    
    # Register core blueprints (fully implemented)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    
    # Placeholder blueprints - routes still in app1_production.py
    # Uncomment as routes are moved:
    # from blueprints import email_intel, whatsapp_intel, patrol_intel
    # from blueprints import surveillance_intel, received_by_hand_intel
    # from blueprints import poi, int_reference, analytics, ai, export, api, tools
    # app.register_blueprint(email_bp)
    # app.register_blueprint(whatsapp_bp)
    # app.register_blueprint(patrol_bp)
    # app.register_blueprint(surveillance_bp)
    # app.register_blueprint(received_by_hand_bp)
    # app.register_blueprint(poi_bp)
    # app.register_blueprint(int_reference_bp)
    # app.register_blueprint(analytics_bp)
    # app.register_blueprint(ai_bp)
    # app.register_blueprint(export_bp)
    # app.register_blueprint(api_bp)
    # app.register_blueprint(tools_bp)
