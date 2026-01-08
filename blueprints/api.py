# blueprints/api.py
# REST API routes - PLACEHOLDER
# TODO: Move routes from app1_production.py

from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Routes to be moved:
# - /api/global-search (line 2070)
# - /api/debug/db-status (line 4903)
# - /api/refresh-emails (line 4944)
# - /api/clean-duplicates (line 4970)
# - /api/bulk-assign-case (line 9604)
# - /api/features/check/<key> (line 6635)
# - /api/poi/* routes

# Placeholder - routes still in app1_production.py for now
