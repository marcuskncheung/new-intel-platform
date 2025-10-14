#!/bin/bash
"""
AUTOMATED DEPLOYMENT SCRIPT
Alleged Person Profile System

This script automates the deployment of the alleged person automation system.
Run this on your server after uploading the new files.

Usage:
    chmod +x deploy_automation.sh
    ./deploy_automation.sh

"""

echo "🚀 DEPLOYING ALLEGED PERSON AUTOMATION SYSTEM"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "app1_production.py" ]; then
    echo -e "${RED}❌ Error: app1_production.py not found in current directory${NC}"
    echo "Please run this script from the new-intel-platform-staging directory"
    exit 1
fi

# Check if migration script exists
if [ ! -f "migrate_alleged_person_automation.py" ]; then
    echo -e "${RED}❌ Error: migrate_alleged_person_automation.py not found${NC}"
    echo "Please upload all required files first"
    exit 1
fi

# Check Python version
echo -e "${BLUE}🐍 Checking Python version...${NC}"
python3 --version || {
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
}

# Create backup directory if it doesn't exist
echo -e "${BLUE}💾 Creating backup directory...${NC}"
mkdir -p backups

# Backup database (if SQLite)
if [ -f "*.db" ]; then
    echo -e "${YELLOW}💾 Creating database backup...${NC}"
    BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S).db"
    cp *.db "backups/$BACKUP_NAME" && echo -e "${GREEN}✅ Database backed up to backups/$BACKUP_NAME${NC}"
fi

# Set environment variables for better PDF processing
echo -e "${BLUE}🔧 Setting environment variables...${NC}"
export ATTACHMENT_TEXT_LIMIT=100000
export TOTAL_ATTACHMENT_LIMIT=500000  
export PROMPT_ATTACHMENT_LIMIT=100000
export ALLEGED_PERSON_AUTOMATION=true

echo -e "${GREEN}✅ Environment variables set for enhanced PDF processing${NC}"

# Run database migration
echo -e "${BLUE}🗃️  Running database migration...${NC}"
python3 migrate_alleged_person_automation.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database migration completed successfully${NC}"
else
    echo -e "${RED}❌ Database migration failed${NC}"
    echo "Check the error messages above and fix any issues"
    exit 1
fi

# Test import of automation module
echo -e "${BLUE}🧪 Testing automation module...${NC}"
python3 -c "
try:
    from alleged_person_automation import DATABASE_AVAILABLE
    print(f'✅ Automation module loaded successfully')
    print(f'   Database available: {DATABASE_AVAILABLE}')
    
    from app1_production import AllegedPersonProfile, EmailAllegedPersonLink
    print(f'✅ Database models imported successfully')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
except Exception as e:
    print(f'❌ Error: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Automation module test passed${NC}"
else
    echo -e "${RED}❌ Automation module test failed${NC}"
    exit 1
fi

# Show system status
echo -e "${BLUE}📊 Checking system status...${NC}"
python3 -c "
from app1_production import app, AllegedPersonProfile, EmailAllegedPersonLink
with app.app_context():
    try:
        total_profiles = AllegedPersonProfile.query.count()
        active_profiles = AllegedPersonProfile.query.filter_by(status='ACTIVE').count()
        total_links = EmailAllegedPersonLink.query.count()
        
        print(f'📈 System Statistics:')
        print(f'   Total profiles: {total_profiles}')
        print(f'   Active profiles: {active_profiles}')
        print(f'   Email-profile links: {total_links}')
        
        if total_profiles > 0:
            print(f'✅ Database tables created and populated')
        else:
            print(f'⚠️  No profiles found - this may be normal for new installation')
            
    except Exception as e:
        print(f'❌ Database check failed: {e}')
        exit(1)
"

# Final instructions
echo ""
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo "=============================================="
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Restart your Flask application:"
echo "   sudo systemctl restart your-app-service"
echo "   OR"  
echo "   pkill -f app1_production.py && python3 app1_production.py"
echo ""
echo "2. Test the system:"
echo "   • Visit /alleged_subject_list to see profiles"
echo "   • Run AI analysis on an email to test automation"
echo "   • Manually edit email alleged persons to test automation"
echo ""
echo "3. Monitor the system:"
echo "   • Check application logs for [AUTOMATION] messages"
echo "   • Verify POI profiles are created automatically"
echo "   • Ensure no duplicate profiles for same person"
echo ""
echo -e "${YELLOW}🔍 Troubleshooting:${NC}"
echo "   • If issues occur, check DEPLOYMENT_AUTOMATION.md"
echo "   • Database backup saved in backups/ directory"
echo "   • Re-run this script if needed"
echo ""
echo -e "${GREEN}✅ Alleged Person Automation System is now active!${NC}"
