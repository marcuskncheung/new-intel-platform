# blueprints/export.py
# Export routes
# Migrated from app1_production.py

from flask import Blueprint, render_template, request, jsonify, send_file, make_response
from flask_login import login_required, current_user
from extensions import db
from models.email import Email, Attachment
from models.whatsapp import WhatsAppEntry
from models.patrol import OnlinePatrolEntry
from models.surveillance import SurveillanceEntry
from models.received_by_hand import ReceivedByHandEntry
from models.case import CaseProfile
from models.user import AuditLog
from utils.helpers import get_hk_time
import io
import csv

# Create blueprint
export_bp = Blueprint('export', __name__)


@export_bp.route('/master')
@login_required
def master_export():
    """
    📤 Master Export - All Intelligence Sources
    """
    try:
        fmt = request.args.get('format', 'csv')
        
        # Get all data
        emails = Email.query.order_by(Email.received.desc()).all()
        whatsapp = WhatsAppEntry.query.order_by(WhatsAppEntry.id.desc()).all()
        patrol = OnlinePatrolEntry.query.order_by(OnlinePatrolEntry.id.desc()).all()
        surveillance = SurveillanceEntry.query.order_by(SurveillanceEntry.id.desc()).all()
        received_by_hand = ReceivedByHandEntry.query.order_by(ReceivedByHandEntry.id.desc()).all()
        
        if fmt == 'csv':
            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                'Source', 'ID', 'Subject/Title', 'Date', 'Status',
                'Source Reliability', 'Content Validity', 'INT Reference'
            ])
            
            # Emails
            for e in emails:
                case = CaseProfile.query.get(e.caseprofile_id) if e.caseprofile_id else None
                writer.writerow([
                    'Email', e.id, e.subject, e.received, e.status,
                    e.source_reliability, e.content_validity,
                    case.int_reference if case else ''
                ])
            
            # WhatsApp
            for w in whatsapp:
                case = CaseProfile.query.get(w.caseprofile_id) if w.caseprofile_id else None
                writer.writerow([
                    'WhatsApp', w.id, w.alleged_subject, w.created_at, '',
                    w.source_reliability, w.content_validity,
                    case.int_reference if case else ''
                ])
            
            # Patrol
            for p in patrol:
                case = CaseProfile.query.get(p.caseprofile_id) if p.caseprofile_id else None
                writer.writerow([
                    'Patrol', p.id, p.platform, p.created_at, '',
                    p.source_reliability, p.content_validity,
                    case.int_reference if case else ''
                ])
            
            # Surveillance
            for s in surveillance:
                case = CaseProfile.query.get(s.caseprofile_id) if s.caseprofile_id else None
                writer.writerow([
                    'Surveillance', s.id, s.target_name, s.start_date, '',
                    s.source_reliability, s.content_validity,
                    case.int_reference if case else ''
                ])
            
            # Received By Hand
            for r in received_by_hand:
                case = CaseProfile.query.get(r.caseprofile_id) if r.caseprofile_id else None
                writer.writerow([
                    'Received By Hand', r.id, r.received_from, r.received_date, '',
                    r.source_reliability, r.content_validity,
                    case.int_reference if case else ''
                ])
            
            output.seek(0)
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=master_export_{get_hk_time().strftime("%Y%m%d_%H%M%S")}.csv'
            
            return response
        
        else:
            return jsonify({'error': 'Format not supported'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@export_bp.route('/inbox/<fmt>')
@login_required
def inbox_export(fmt):
    """
    📧 Email Inbox Export
    """
    try:
        emails = Email.query.order_by(Email.received.desc()).all()
        
        if fmt == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow([
                'ID', 'Subject', 'Sender', 'Recipients', 'Received',
                'Status', 'Source Reliability', 'Content Validity',
                'Alleged Subject', 'Alleged Nature', 'INT Reference'
            ])
            
            for e in emails:
                case = CaseProfile.query.get(e.caseprofile_id) if e.caseprofile_id else None
                writer.writerow([
                    e.id, e.subject, e.sender, e.recipients, e.received,
                    e.status, e.source_reliability, e.content_validity,
                    e.alleged_subject, e.alleged_nature,
                    case.int_reference if case else ''
                ])
            
            output.seek(0)
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=inbox_export_{get_hk_time().strftime("%Y%m%d_%H%M%S")}.csv'
            
            return response
        
        return jsonify({'error': 'Format not supported'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@export_bp.route('/whatsapp/<fmt>')
@login_required
def whatsapp_export(fmt):
    """
    📱 WhatsApp Export
    """
    try:
        entries = WhatsAppEntry.query.order_by(WhatsAppEntry.id.desc()).all()
        
        if fmt == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow([
                'ID', 'Alleged Subject', 'Alleged Type', 'Alleged Nature',
                'Source Reliability', 'Content Validity', 'Intel Summary',
                'Created At', 'INT Reference'
            ])
            
            for e in entries:
                case = CaseProfile.query.get(e.caseprofile_id) if e.caseprofile_id else None
                writer.writerow([
                    e.id, e.alleged_subject, e.alleged_type, e.alleged_nature,
                    e.source_reliability, e.content_validity, e.intel_summary,
                    e.created_at, case.int_reference if case else ''
                ])
            
            output.seek(0)
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=whatsapp_export_{get_hk_time().strftime("%Y%m%d_%H%M%S")}.csv'
            
            return response
        
        return jsonify({'error': 'Format not supported'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@export_bp.route('/patrol/<fmt>')
@login_required
def patrol_export(fmt):
    """
    🔍 Online Patrol Export
    """
    try:
        entries = OnlinePatrolEntry.query.order_by(OnlinePatrolEntry.id.desc()).all()
        
        if fmt == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow([
                'ID', 'Platform', 'URL', 'Alleged Subject', 'Alleged Nature',
                'Source Reliability', 'Content Validity', 'Intel Summary',
                'Created At', 'INT Reference'
            ])
            
            for e in entries:
                case = CaseProfile.query.get(e.caseprofile_id) if e.caseprofile_id else None
                writer.writerow([
                    e.id, e.platform, e.url, e.alleged_subject, e.alleged_nature,
                    e.source_reliability, e.content_validity, e.intel_summary,
                    e.created_at, case.int_reference if case else ''
                ])
            
            output.seek(0)
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=patrol_export_{get_hk_time().strftime("%Y%m%d_%H%M%S")}.csv'
            
            return response
        
        return jsonify({'error': 'Format not supported'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@export_bp.route('/surveillance/<fmt>')
@login_required
def surveillance_export(fmt):
    """
    🔭 Surveillance Export
    """
    try:
        entries = SurveillanceEntry.query.order_by(SurveillanceEntry.id.desc()).all()
        
        if fmt == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow([
                'ID', 'Operation Type', 'Target Name', 'Target Location',
                'Start Date', 'End Date', 'Source Reliability', 'Content Validity',
                'Intel Summary', 'Created At', 'INT Reference'
            ])
            
            for e in entries:
                case = CaseProfile.query.get(e.caseprofile_id) if e.caseprofile_id else None
                writer.writerow([
                    e.id, e.operation_type, e.target_name, e.target_location,
                    e.start_date, e.end_date, e.source_reliability, e.content_validity,
                    e.intel_summary, e.created_at, case.int_reference if case else ''
                ])
            
            output.seek(0)
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=surveillance_export_{get_hk_time().strftime("%Y%m%d_%H%M%S")}.csv'
            
            return response
        
        return jsonify({'error': 'Format not supported'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@export_bp.route('/received_by_hand/<fmt>')
@login_required
def received_by_hand_export(fmt):
    """
    📝 Received By Hand Export
    """
    try:
        entries = ReceivedByHandEntry.query.order_by(ReceivedByHandEntry.id.desc()).all()
        
        if fmt == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow([
                'ID', 'Received From', 'Received Date', 'Alleged Subject', 'Alleged Nature',
                'Source Reliability', 'Content Validity', 'Intel Summary',
                'Created At', 'INT Reference'
            ])
            
            for e in entries:
                case = CaseProfile.query.get(e.caseprofile_id) if e.caseprofile_id else None
                writer.writerow([
                    e.id, e.received_from, e.received_date, e.alleged_subject, e.alleged_nature,
                    e.source_reliability, e.content_validity, e.intel_summary,
                    e.created_at, case.int_reference if case else ''
                ])
            
            output.seek(0)
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=received_by_hand_export_{get_hk_time().strftime("%Y%m%d_%H%M%S")}.csv'
            
            return response
        
        return jsonify({'error': 'Format not supported'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
