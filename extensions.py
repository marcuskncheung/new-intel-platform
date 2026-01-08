# extensions.py
# Flask extensions - shared across all blueprints

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import pytz

# Initialize extensions without app
db = SQLAlchemy()
login_mgr = LoginManager()
migrate = Migrate()

# 🇭🇰 HONG KONG TIMEZONE CONFIGURATION
HK_TZ = pytz.timezone('Asia/Hong_Kong')
