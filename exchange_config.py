# Exchange Web Services Configuration
# ===================================
# Configuration for connecting to Exchange server using EWS

# Exchange Server Settings
EXCHANGE_SERVER = 'webmail.ia.org.hk'
EXCHANGE_EMAIL = 'intel@ia.org.hk'
# SECURITY: Password moved to environment variable for security
import os
EXCHANGE_PASSWORD = os.environ.get('EXCHANGE_PASSWORD', '')  # Set via environment variable

# Intelligence Mailbox Settings - IMPORTANT!
# Using direct Intelligence account credentials
INTELLIGENCE_MAILBOX = 'intelligence_direct'  # Direct Intelligence account
INTELLIGENCE_MAILBOX_EMAIL = 'intel@ia.org.hk'  # Direct Intelligence mailbox
EXCHANGE_FOLDER = 'Inbox'  # Intelligence emails are in Intelligence account Inbox

# Advanced Settings
EXCHANGE_AUTO_DISCOVER = False  # Set to True to use auto-discovery instead of server
EXCHANGE_AUTH_TYPE = 'basic'    # 'basic' or 'ntlm'

# Background Import Settings
BACKGROUND_IMPORT_ENABLED = True
BACKGROUND_IMPORT_INTERVAL = 300  # seconds (5 minutes)

# Security Notes:
# ===============
# 1. This file contains sensitive credentials
# 2. In production, consider using environment variables
# 3. Ensure this file is not committed to version control
# 4. Consider using encrypted credential storage
