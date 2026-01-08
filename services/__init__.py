# services/__init__.py
# Service layer for business logic separation
# Each service encapsulates CRUD operations and business rules for a specific domain

from services.email_service import EmailService
from services.whatsapp_service import WhatsAppService
from services.patrol_service import PatrolService
from services.surveillance_service import SurveillanceService
from services.received_by_hand_service import ReceivedByHandService
from services.poi_service import POIService

__all__ = [
    'EmailService',
    'WhatsAppService',
    'PatrolService',
    'SurveillanceService',
    'ReceivedByHandService',
    'POIService',
]
