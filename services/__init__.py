# services/__init__.py
# Service layer for business logic separation
# Each service module contains functions for CRUD operations and business rules

# Import service functions from modules
from services import email_service
from services import whatsapp_service
from services import patrol_service
from services import surveillance_service
from services import received_by_hand_service
from services import poi_service

__all__ = [
    'email_service',
    'whatsapp_service',
    'patrol_service',
    'surveillance_service',
    'received_by_hand_service',
    'poi_service',
]
