# blueprints/auth.py
# Authentication routes: login, logout, signup

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models.user import User, AuditLog
import pytz
from datetime import datetime

# Create blueprint
auth_bp = Blueprint('auth', __name__)

HK_TZ = pytz.timezone('Asia/Hong_Kong')

def get_hk_time():
    return datetime.now(HK_TZ)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        try:
            AuditLog.log_action(
                action="login_redirect_authenticated",
                resource_type="authentication",
                user=current_user,
                severity="info"
            )
        except Exception as audit_error:
            print(f"⚠️ Audit log error during login redirect: {audit_error}")
        return redirect(url_for("main.home"))
        
    if request.method == "POST":
        u, p = request.form["username"].strip(), request.form["password"]
        user = User.query.filter_by(username=u).first()
        
        login_details = {
            "username": u,
            "ip_address": request.remote_addr,
            "user_agent": request.headers.get('User-Agent', '')[:200],
            "timestamp": get_hk_time().isoformat()
        }
        if user and user.is_active and check_password_hash(user.password, p):
            user.last_login = get_hk_time()
            db.session.commit()
            
            session.permanent = True
            login_user(user, remember=True)
            
            try:
                login_details["status"] = "success"
                login_details["user_id"] = user.id
                print(f"✅ Login successful for user: {user.username} (ID: {user.id})")
                AuditLog.log_action(
                    action="login_success",
                    resource_type="authentication",
                    resource_id=str(user.id),
                    details=login_details,
                    user=user,
                    severity="info"
                )
            except Exception as audit_error:
                print(f"⚠️ Audit log error during successful login: {audit_error}")
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.home')
            
            print(f"🔄 Redirecting to: {next_page}")
            return redirect(next_page)
        else:
            try:
                login_details["status"] = "failed"
                login_details["reason"] = "invalid_credentials" if user else "user_not_found"
                
                AuditLog.log_action(
                    action="login_failed",
                    resource_type="authentication",
                    details=login_details,
                    user=None,
                    severity="warning"
                )
            except Exception as audit_error:
                print(f"⚠️ Audit log error during failed login: {audit_error}")
            
            flash("Invalid credentials or account disabled", "danger")
    return render_template("login.html")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("poi.alleged_subject_list"))
    if request.method == "POST":
        u, p = request.form["username"].strip(), request.form["password"]
        if not u or not p:
            flash("Username & password required", "warning")
        elif User.query.filter_by(username=u).first():
            flash("Username exists", "danger")
        else:
            db.session.add(User(username=u, password=generate_password_hash(p)))
            db.session.commit()
            flash("Account created", "success")
            return redirect(url_for("auth.login"))
    return render_template("signup.html")


@auth_bp.route("/logout")
@login_required
def logout():
    AuditLog.log_action('User logout', f'User {current_user.username} logged out', current_user)
    logout_user()
    flash("Logged out", "info")
    return redirect(url_for("auth.login"))
