# models/__init__.py
# Database models - shared across all blueprints

from .user import User, AuditLog, FeatureSettings
from .email import Email, Attachment, EmailAllegedSubject, EmailAnalysisLock
from .whatsapp import WhatsAppEntry, WhatsAppImage, WhatsAppAllegedSubject
from .patrol import OnlinePatrolEntry, OnlinePatrolPhoto, OnlinePatrolAllegedSubject
from .surveillance import SurveillanceEntry, SurveillancePhoto, SurveillanceDocument, Target
from .received_by_hand import ReceivedByHandEntry, ReceivedByHandDocument, ReceivedByHandAllegedSubject
from .case import CaseProfile

__all__ = [
    # User models
    'User', 'AuditLog', 'FeatureSettings',
    # Email models
    'Email', 'Attachment', 'EmailAllegedSubject', 'EmailAnalysisLock',
    # WhatsApp models
    'WhatsAppEntry', 'WhatsAppImage', 'WhatsAppAllegedSubject',
    # Online Patrol models
    'OnlinePatrolEntry', 'OnlinePatrolPhoto', 'OnlinePatrolAllegedSubject',
    # Surveillance models
    'SurveillanceEntry', 'SurveillancePhoto', 'SurveillanceDocument', 'Target',
    # Received by Hand models
    'ReceivedByHandEntry', 'ReceivedByHandDocument', 'ReceivedByHandAllegedSubject',
    # Case models
    'CaseProfile',
]
