# blueprints/__init__.py
# Blueprint registration module

from flask import Blueprint

# Create blueprint instances
auth_bp = Blueprint('auth', __name__)
main_bp = Blueprint('main', __name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
email_bp = Blueprint('email', __name__)
whatsapp_bp = Blueprint('whatsapp', __name__)
patrol_bp = Blueprint('patrol', __name__)
surveillance_bp = Blueprint('surveillance', __name__)
received_by_hand_bp = Blueprint('received_by_hand', __name__)
poi_bp = Blueprint('poi', __name__)
int_reference_bp = Blueprint('int_reference', __name__)
analytics_bp = Blueprint('analytics', __name__)
ai_bp = Blueprint('ai', __name__)
export_bp = Blueprint('export', __name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')
tools_bp = Blueprint('tools', __name__)


def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    from blueprints import auth, main, admin
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    # More blueprints will be added as they are created
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
