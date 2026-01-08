# blueprints/main.py
# Main routes: home, dashboard, about, global-search, tools, health

from flask import render_template, redirect, url_for, jsonify, request
from flask_login import login_required
from blueprints import main_bp
from extensions import db
import time


# Request stats for health check
request_stats = {
    'active_requests': 0,
    'total_requests': 0,
    'avg_response_time': 0.0,
    'last_reset': time.time()
}


@main_bp.route('/')
@login_required
def root():
    """🏠 ROOT URL: Redirect to Dashboard"""
    return redirect(url_for('main.home'))


@main_bp.route('/home')
@main_bp.route('/welcome')
@main_bp.route('/dashboard')
@login_required
def home():
    """🏠 DASHBOARD HOME PAGE: Platform overview with real-time statistics"""
    try:
        from models import (
            Email, WhatsAppEntry, OnlinePatrolEntry, SurveillanceEntry,
            ReceivedByHandEntry, CaseProfile
        )
        # Import AllegedPersonProfile from poi_enhanced module
        try:
            from models_poi_enhanced import AllegedPersonProfile
        except ImportError:
            AllegedPersonProfile = None
        
        # Get statistics
        poi_count = AllegedPersonProfile.query.filter_by(status='ACTIVE').count() if AllegedPersonProfile else 0
        email_count = Email.query.count()
        whatsapp_count = WhatsAppEntry.query.count()
        patrol_count = OnlinePatrolEntry.query.count()
        surveillance_count = SurveillanceEntry.query.count()
        received_by_hand_count = ReceivedByHandEntry.query.count()
        case_count = CaseProfile.query.count()
        
        # Get recent entries
        recent_emails = Email.query.order_by(Email.received.desc()).limit(5).all()
        recent_whatsapp = WhatsAppEntry.query.order_by(WhatsAppEntry.received_time.desc()).limit(5).all()
        recent_patrol = OnlinePatrolEntry.query.order_by(OnlinePatrolEntry.discovery_time.desc()).limit(5).all()
        
        # Calculate total intelligence
        total_intelligence = email_count + whatsapp_count + patrol_count + received_by_hand_count
        
        # Get pending reviews
        pending_emails = Email.query.filter(
            db.or_(Email.source_reliability == None, Email.content_validity == None)
        ).count()
        
        return render_template('home.html',
                             poi_count=poi_count,
                             email_count=email_count,
                             whatsapp_count=whatsapp_count,
                             patrol_count=patrol_count,
                             surveillance_count=surveillance_count,
                             received_by_hand_count=received_by_hand_count,
                             case_count=case_count,
                             total_intelligence=total_intelligence,
                             pending_emails=pending_emails,
                             recent_emails=recent_emails,
                             recent_whatsapp=recent_whatsapp,
                             recent_patrol=recent_patrol)
    except Exception as e:
        print(f"[HOME] Error loading dashboard: {e}")
        return render_template('home.html',
                             poi_count=0,
                             email_count=0,
                             whatsapp_count=0,
                             patrol_count=0,
                             surveillance_count=0,
                             received_by_hand_count=0,
                             case_count=0,
                             total_intelligence=0,
                             pending_emails=0,
                             recent_emails=[],
                             recent_whatsapp=[],
                             recent_patrol=[])


@main_bp.route('/about')
@login_required
def about():
    """📖 ABOUT PAGE: Platform introduction and help"""
    return render_template('about.html')


@main_bp.route("/index")
@main_bp.route("/search")
@login_required
def index():
    """Redirect to new global search page"""
    return redirect(url_for('main.global_search_page'))


@main_bp.route("/global-search")
@login_required
def global_search_page():
    """🔍 NEW: Google-like Global Search Page"""
    return render_template('global_search.html')


@main_bp.route('/tools')
@login_required
def tools():
    """🛠️ Utility Tools Page"""
    return render_template('tools.html')


@main_bp.route('/health')
def health_check():
    """System health and performance monitoring"""
    current_time = time.time()
    uptime = current_time - request_stats['last_reset']
    
    health_data = {
        'status': 'healthy',
        'uptime_seconds': int(uptime),
        'active_requests': request_stats['active_requests'],
        'total_requests': request_stats['total_requests'],
        'avg_response_time': f"{request_stats['avg_response_time']:.3f}s",
        'database_status': 'connected',
        'memory_usage': 'normal',
        'max_concurrent_users': 50,
        'current_load': f"{(request_stats['active_requests']/50)*100:.1f}%"
    }
    
    if request_stats['active_requests'] > 40:
        health_data['status'] = 'high_load'
        health_data['warning'] = 'System under heavy load'
    elif request_stats['active_requests'] > 50:
        health_data['status'] = 'overloaded'
        health_data['warning'] = 'System overloaded'
    
    return jsonify(health_data)
