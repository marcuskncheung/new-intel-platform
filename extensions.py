# extensions.py
# Flask extensions - shared across all blueprints
# This file prevents circular imports by declaring extensions separately from app

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import pytz

# ========================================
# Initialize extensions without app
# (will be initialized with app in create_app())
# ========================================
db = SQLAlchemy()
login_mgr = LoginManager()
migrate = Migrate()

# Optional caching
try:
    from flask_caching import Cache
    cache = Cache()
    CACHING_AVAILABLE = True
except ImportError:
    cache = None
    CACHING_AVAILABLE = False

# ========================================
# 🇭🇰 HONG KONG TIMEZONE CONFIGURATION
# ========================================
HK_TZ = pytz.timezone('Asia/Hong_Kong')

# ========================================
# Global configuration flags
# ========================================
# These will be set during app initialization
SECURITY_MODULE_AVAILABLE = False
AI_AVAILABLE = False
EXCHANGELIB_AVAILABLE = False
ALLEGED_PERSON_AUTOMATION = False
