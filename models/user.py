# models/user.py
# User-related database models

from datetime import datetime
import json
import pytz
from flask_login import UserMixin
from extensions import db

# Hong Kong timezone
HK_TZ = pytz.timezone('Asia/Hong_Kong')

def get_hk_time():
    """Get current time in Hong Kong timezone"""
    return datetime.now(HK_TZ)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'
    created_at = db.Column(db.DateTime, default=get_hk_time)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    def is_admin(self):
        return self.role == 'admin'


class AuditLog(db.Model):
    """Enhanced audit log with encryption and comprehensive tracking"""
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    username = db.Column(db.String(80))
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(200))
    resource_id = db.Column(db.String(100))
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=get_hk_time)
    session_id = db.Column(db.String(200))
    severity = db.Column(db.String(20), default='info')
    
    @staticmethod
    def log_action(action, resource_type=None, resource_id=None, details=None, user=None, severity='info'):
        """Enhanced audit logging with encryption and proper Flask context handling"""
        try:
            from flask import request, session as flask_session, has_request_context, has_app_context
            
            # Import security module
            try:
                from security_module import encrypt_field, SECURITY_MODULE_AVAILABLE
            except ImportError:
                SECURITY_MODULE_AVAILABLE = False
                def encrypt_field(data):
                    return data
            
            if not has_app_context():
                print(f"⚠️ Audit log skipped - no app context: {action}")
                return
            
            encrypted_details = None
            if details:
                if isinstance(details, dict):
                    details = json.dumps(details)
                details_str = str(details)
                if len(details_str) > 5000:
                    details_str = details_str[:4900] + "...[truncated]"
                
                if SECURITY_MODULE_AVAILABLE:
                    encrypted_details = encrypt_field(details_str)
                else:
                    encrypted_details = details_str
            
            username_val = (user.username if user else 'Anonymous')[:80] if user and user.username else 'Anonymous'
            action_val = action[:100] if action else ''
            resource_type_val = resource_type[:200] if resource_type else None
            resource_id_val = str(resource_id)[:100] if resource_id else None
            ip_address_val = (request.remote_addr if has_request_context() and request else None)
            if ip_address_val and len(ip_address_val) > 45:
                ip_address_val = ip_address_val[:45]
            user_agent_val = (request.headers.get('User-Agent', '') if has_request_context() and request else '')[:500]
            session_id_val = (flask_session.get('_id', 'unknown') if has_request_context() and flask_session else 'unknown')[:200]
            severity_val = severity[:20] if severity else 'info'
            
            log_entry = AuditLog(
                user_id=user.id if user else None,
                username=username_val,
                action=action_val,
                resource_type=resource_type_val,
                resource_id=resource_id_val,
                details=encrypted_details,
                ip_address=ip_address_val,
                user_agent=user_agent_val,
                session_id=session_id_val,
                severity=severity_val
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as e:
            print(f"⚠️ Audit log error: {e}")
            try:
                db.session.rollback()
            except Exception:
                pass
    
    def get_decrypted_details(self):
        """Get decrypted details for authorized viewing"""
        if not self.details:
            return None
        
        try:
            from security_module import decrypt_field, SECURITY_MODULE_AVAILABLE
            if SECURITY_MODULE_AVAILABLE:
                return decrypt_field(self.details)
        except ImportError:
            pass
        return self.details
    
    def to_dict(self):
        """Convert audit log to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.get_decrypted_details(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'session_id': self.session_id,
            'severity': self.severity
        }


class FeatureSettings(db.Model):
    """Admin-controlled feature visibility settings"""
    __tablename__ = 'feature_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    feature_key = db.Column(db.String(100), unique=True, nullable=False)
    feature_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_enabled = db.Column(db.Boolean, default=True)
    admin_only = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=get_hk_time, onupdate=get_hk_time)
    updated_by = db.Column(db.String(100))
    
    DEFAULT_FEATURES = [
        {
            'feature_key': 'ai_analysis',
            'feature_name': 'AI Analysis (Email)',
            'description': 'AI-powered comprehensive analysis for emails including attachments and alleged persons detection',
            'is_enabled': True,
            'admin_only': True
        },
        {
            'feature_key': 'ai_status_button',
            'feature_name': 'AI Status Button',
            'description': 'Button to check AI analysis status in Email inbox',
            'is_enabled': True,
            'admin_only': True
        },
        {
            'feature_key': 'rebuild_poi_list',
            'feature_name': 'Rebuild POI List',
            'description': 'Button to rebuild/resync POI list from all sources',
            'is_enabled': True,
            'admin_only': True
        },
        {
            'feature_key': 'surveillance_tab',
            'feature_name': 'Surveillance Tab',
            'description': 'Surveillance Operation tab in Intel Source',
            'is_enabled': True,
            'admin_only': False
        },
        {
            'feature_key': 'database_admin',
            'feature_name': 'Database Overview',
            'description': 'Access to database statistics and management',
            'is_enabled': True,
            'admin_only': True
        },
    ]
    
    @classmethod
    def get_setting(cls, feature_key):
        """Get a feature setting by key"""
        return cls.query.filter_by(feature_key=feature_key).first()
    
    @classmethod
    def is_feature_visible(cls, feature_key, user=None):
        """Check if a feature should be visible to the given user"""
        setting = cls.get_setting(feature_key)
        if not setting:
            return True
        
        if not setting.is_enabled:
            return False
        
        if setting.admin_only:
            if user and hasattr(user, 'is_admin'):
                return user.is_admin() if callable(user.is_admin) else user.is_admin
            return False
        
        return True
    
    @classmethod
    def initialize_defaults(cls):
        """Initialize default feature settings if they don't exist"""
        for feature in cls.DEFAULT_FEATURES:
            existing = cls.query.filter_by(feature_key=feature['feature_key']).first()
            if not existing:
                new_setting = cls(
                    feature_key=feature['feature_key'],
                    feature_name=feature['feature_name'],
                    description=feature['description'],
                    is_enabled=feature['is_enabled'],
                    admin_only=feature['admin_only'],
                    updated_by='system'
                )
                db.session.add(new_setting)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"⚠️ Error initializing feature settings: {e}")


def can_see_feature(feature_key):
    """Template helper to check if current user can see a feature"""
    from flask_login import current_user
    return FeatureSettings.is_feature_visible(feature_key, current_user if current_user.is_authenticated else None)
