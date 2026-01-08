# blueprints/analytics.py
# Analytics and Statistics routes
# Migrated from app1_production.py

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.case import CaseProfile
from models.email import Email
from models.whatsapp import WhatsAppEntry
from models.patrol import OnlinePatrolEntry
from models.surveillance import SurveillanceEntry
from models.received_by_hand import ReceivedByHandEntry
from sqlalchemy import func
from collections import Counter

# Create blueprint
analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/int_analytics')
@login_required
def int_analytics():
    """
    📊 INT Analytics Dashboard
    Comprehensive intelligence analytics for management
    """
    try:
        # Get INT references with counts
        int_references = CaseProfile.query.filter(
            CaseProfile.int_reference.isnot(None)
        ).order_by(CaseProfile.int_reference.desc()).all()
        
        case_ids = [c.id for c in int_references]
        
        # Get counts using optimized queries
        email_counts = dict(
            db.session.query(Email.caseprofile_id, func.count(Email.id))
            .filter(Email.caseprofile_id.in_(case_ids))
            .group_by(Email.caseprofile_id)
            .all()
        )
        
        whatsapp_counts = dict(
            db.session.query(WhatsAppEntry.caseprofile_id, func.count(WhatsAppEntry.id))
            .filter(WhatsAppEntry.caseprofile_id.in_(case_ids))
            .group_by(WhatsAppEntry.caseprofile_id)
            .all()
        )
        
        patrol_counts = dict(
            db.session.query(OnlinePatrolEntry.caseprofile_id, func.count(OnlinePatrolEntry.id))
            .filter(OnlinePatrolEntry.caseprofile_id.in_(case_ids))
            .group_by(OnlinePatrolEntry.caseprofile_id)
            .all()
        )
        
        surveillance_counts = dict(
            db.session.query(SurveillanceEntry.caseprofile_id, func.count(SurveillanceEntry.id))
            .filter(SurveillanceEntry.caseprofile_id.in_(case_ids))
            .group_by(SurveillanceEntry.caseprofile_id)
            .all()
        )
        
        rbh_counts = dict(
            db.session.query(ReceivedByHandEntry.caseprofile_id, func.count(ReceivedByHandEntry.id))
            .filter(ReceivedByHandEntry.caseprofile_id.in_(case_ids))
            .group_by(ReceivedByHandEntry.caseprofile_id)
            .all()
        )
        
        # Build analytics data
        analytics_data = []
        for ref in int_references:
            analytics_data.append({
                'int_reference': ref.int_reference,
                'case_id': ref.id,
                'email_count': email_counts.get(ref.id, 0),
                'whatsapp_count': whatsapp_counts.get(ref.id, 0),
                'patrol_count': patrol_counts.get(ref.id, 0),
                'surveillance_count': surveillance_counts.get(ref.id, 0),
                'received_by_hand_count': rbh_counts.get(ref.id, 0),
            })
        
        # Calculate totals
        totals = {
            'int_references': len(int_references),
            'emails': sum(email_counts.values()),
            'whatsapp': sum(whatsapp_counts.values()),
            'patrol': sum(patrol_counts.values()),
            'surveillance': sum(surveillance_counts.values()),
            'received_by_hand': sum(rbh_counts.values())
        }
        
        return render_template(
            'int_analytics.html',
            analytics_data=analytics_data,
            totals=totals
        )
        
    except Exception as e:
        return render_template('error.html', error=str(e))


@analytics_bp.route('/case-statistics')
@login_required
def get_case_statistics():
    """
    📊 Case Statistics API
    """
    try:
        # Get case number statistics
        cases_with_number = Email.query.filter(Email.case_number.isnot(None)).count()
        cases_without_number = Email.query.filter(Email.case_number.is_(None)).count()
        
        # Get unique case numbers
        unique_cases = db.session.query(Email.case_number).filter(
            Email.case_number.isnot(None)
        ).distinct().count()
        
        return jsonify({
            'success': True,
            'statistics': {
                'assigned': cases_with_number,
                'unassigned': cases_without_number,
                'unique_cases': unique_cases,
                'total_emails': cases_with_number + cases_without_number
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/allegation-nature-statistics')
@login_required
def allegation_nature_statistics():
    """
    📊 Allegation Nature Statistics
    """
    try:
        # Get allegation nature distribution from emails
        emails = Email.query.filter(Email.alleged_nature.isnot(None)).all()
        
        nature_counter = Counter()
        for email in emails:
            if email.alleged_nature:
                nature_counter[email.alleged_nature] += 1
        
        # Also count from WhatsApp
        whatsapp = WhatsAppEntry.query.filter(WhatsAppEntry.alleged_nature.isnot(None)).all()
        for entry in whatsapp:
            if entry.alleged_nature:
                nature_counter[entry.alleged_nature] += 1
        
        statistics = [
            {'nature': nature, 'count': count}
            for nature, count in nature_counter.most_common()
        ]
        
        return jsonify({
            'success': True,
            'statistics': statistics
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@analytics_bp.route('/sender-stats')
@login_required
def get_sender_stats():
    """
    📊 Email Sender Statistics
    """
    try:
        # Get sender distribution
        emails = Email.query.all()
        
        sender_counter = Counter()
        for email in emails:
            if email.sender:
                sender_counter[email.sender] += 1
        
        # Get top 20 senders
        top_senders = [
            {'sender': sender, 'count': count}
            for sender, count in sender_counter.most_common(20)
        ]
        
        return jsonify({
            'success': True,
            'senders': top_senders,
            'total_unique': len(sender_counter)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
