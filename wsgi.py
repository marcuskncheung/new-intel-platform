#!/usr/bin/env python3
"""
WSGI Production Deployment for Intelligence Platform
=====================================================

This file enables production-grade deployment using WSGI servers like Gunicorn.

Usage:
    gunicorn --workers 4 --bind 0.0.0.0:443 --timeout 120 wsgi:app
    
Features:
- Multi-process handling for 30+ concurrent users
- Enhanced database connection handling
- Production-ready error handling
- Automatic environment detection
"""

import os
import re
import sys
from app1_production import app

# Set production environment
os.environ.setdefault('PRODUCTION', 'true')

if __name__ == "__main__":
    app.run()
