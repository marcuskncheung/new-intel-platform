# utils/decorators.py
# Custom decorators for the application

from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            from models.user import AuditLog
            AuditLog.log_action(
                'Unauthorized admin access attempt',
                f'User {current_user.username if current_user.is_authenticated else "Anonymous"} tried to access admin area',
                current_user if current_user.is_authenticated else None
            )
            flash("Access denied. Admin privileges required.", "danger")
            return redirect(url_for("main.home"))
        return f(*args, **kwargs)
    return decorated_function
