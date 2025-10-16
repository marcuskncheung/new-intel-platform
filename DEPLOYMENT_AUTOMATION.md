"""
SERVER DEPLOYMENT INSTRUCTIONS
Automated Alleged Person Profile System

This document explains how to deploy and run the automated alleged person 
profile system on your production server.

═══════════════════════════════════════════════════════════════════════════════
📋 DEPLOYMENT CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

1. UPLOAD FILES TO SERVER
   ✅ Upload these new files to your server:
   - alleged_person_automation.py
   - migrate_alleged_person_automation.py
   
   ✅ Updated files (contains new database models and routes):
   - app1_production.py
   - intelligence_ai.py (already updated with configurable limits)

2. BACKUP DATABASE (CRITICAL!)
   Before running any migration, backup your current database:
   
   ```bash
   # If using SQLite
   cp /path/to/your/database.db /path/to/backup/database_backup_$(date +%Y%m%d_%H%M%S).db
   
   # If using PostgreSQL
   pg_dump -U username -h hostname database_name > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

3. RUN DATABASE MIGRATION
   On your server, navigate to the application directory and run:
   
   ```bash
   cd /path/to/new-intel-platform-staging/
   python3 migrate_alleged_person_automation.py
   ```
   
   Expected output:
   ```
   🤖 ALLEGED PERSON AUTOMATION - Database Migration
   ============================================================
   📊 Current status:
      alleged_person_profile: MISSING
      email_alleged_person_link: MISSING
   
   🔧 Creating missing tables...
      Creating alleged_person_profile table...
      Creating email_alleged_person_link table...
   ✅ Automation tables created successfully!
   
   📝 Creating sample alleged person profiles...
      ✅ Created sample profile: POI-001 - LEUNG SHEUNG MAN EMERSON
      ✅ Created sample profile: POI-002 - WONG TAI SIN
      ✅ Created sample profile: POI-003 - CHAN SIU MING
   
   🎉 MIGRATION COMPLETE!
   ```

4. RESTART APPLICATION
   Restart your Flask application to load the new code:
   
   ```bash
   # If using systemd
   sudo systemctl restart your-app-service
   
   # If running with screen/tmux
   # Kill the old process and restart
   pkill -f app1_production.py
   python3 app1_production.py
   ```

═══════════════════════════════════════════════════════════════════════════════
🤖 HOW THE AUTOMATION WORKS
═══════════════════════════════════════════════════════════════════════════════

AUTOMATIC PROFILE CREATION:

1. AI ANALYSIS AUTOMATION
   When AI analysis identifies alleged persons in emails:
   - Automatically creates POI profiles (POI-001, POI-002, etc.)
   - Links emails to profiles 
   - Prevents duplicates using smart name matching
   - Updates existing profiles with new information

2. MANUAL INPUT AUTOMATION  
   When users manually enter alleged person information:
   - Automatically creates profiles from form submissions
   - Handles English + Chinese names separately
   - Links additional information (agent numbers, companies)

3. DUPLICATE DETECTION
   - Matches by agent number (exact match)
   - Matches by name similarity (85% threshold)
   - Matches by company + partial name
   - Prevents duplicate profiles for same person

═══════════════════════════════════════════════════════════════════════════════
📊 USING THE NEW SYSTEM
═══════════════════════════════════════════════════════════════════════════════

VIEWING PROFILES:
- Visit: http://your-server/alleged_subject_list
- See all POI profiles with unique IDs
- Click profiles to see details and related emails

TESTING AUTOMATION:

1. Test AI Analysis:
   - Upload an email with PDF attachment
   - Run AI analysis 
   - Check if POI profile was automatically created

2. Test Manual Input:
   - Edit an email and add alleged person information
   - Save the email
   - Check if POI profile was automatically created

3. View Results:
   - Go to /alleged_subject_list
   - See new profiles with POI-XXX IDs
   - Click profile to see linked emails

═══════════════════════════════════════════════════════════════════════════════
🔧 CONFIGURATION OPTIONS
═══════════════════════════════════════════════════════════════════════════════

ENVIRONMENT VARIABLES (set these on your server):

# Attachment text limits (already configured)
export ATTACHMENT_TEXT_LIMIT=100000      # 100K per PDF for better analysis
export TOTAL_ATTACHMENT_LIMIT=500000     # 500K total 
export PROMPT_ATTACHMENT_LIMIT=100000    # 100K in AI prompt

# Profile automation (new)
export ALLEGED_PERSON_AUTOMATION=true    # Enable/disable automation
export POI_ID_PREFIX=POI                 # Customize ID prefix (POI, PERSON, etc.)
export SIMILARITY_THRESHOLD=0.85         # Name matching threshold (0.0 to 1.0)

═══════════════════════════════════════════════════════════════════════════════
🚨 TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════════════

MIGRATION ERRORS:

1. "Table already exists"
   - This is normal if migration was run before
   - The script will skip existing tables

2. "Permission denied" 
   - Make sure your application has database write permissions
   - Check file/directory ownership

3. "Module not found"
   - Make sure all files are uploaded to the correct directory
   - Check Python path and imports

AUTOMATION NOT WORKING:

1. Check logs for errors:
   ```bash
   tail -f /path/to/your/app.log
   ```

2. Verify automation is enabled:
   - Look for "[AUTOMATION]" messages in logs
   - Check that DATABASE_AVAILABLE = True

3. Test manually:
   ```bash
   python3 -c "
   from alleged_person_automation import DATABASE_AVAILABLE
   print(f'Database available: {DATABASE_AVAILABLE}')
   
   from app1_production import AllegedPersonProfile
   count = AllegedPersonProfile.query.count()
   print(f'Profiles in database: {count}')
   "
   ```

DATABASE ISSUES:

1. Backup restore (if needed):
   ```bash
   # SQLite
   cp /path/to/backup/database_backup_*.db /path/to/your/database.db
   
   # PostgreSQL  
   psql -U username -h hostname database_name < backup_*.sql
   ```

2. Reset automation tables (if corrupted):
   ```bash
   python3 -c "
   from app1_production import app, db
   with app.app_context():
       db.drop_table('email_alleged_person_link')
       db.drop_table('alleged_person_profile')
   "
   
   # Then re-run migration
   python3 migrate_alleged_person_automation.py
   ```

═══════════════════════════════════════════════════════════════════════════════
📈 MONITORING & MAINTENANCE
═══════════════════════════════════════════════════════════════════════════════

CHECK SYSTEM STATUS:
```bash
python3 migrate_alleged_person_automation.py
```
(This shows current status without making changes)

VIEW STATISTICS:
```bash
python3 -c "
from app1_production import app, AllegedPersonProfile, EmailAllegedPersonLink
with app.app_context():
    total = AllegedPersonProfile.query.count()
    active = AllegedPersonProfile.query.filter_by(status='ACTIVE').count()
    links = EmailAllegedPersonLink.query.count()
    print(f'Total profiles: {total}')
    print(f'Active profiles: {active}') 
    print(f'Email links: {links}')
"
```

REGULAR MAINTENANCE:
- Monitor profile creation in logs
- Check for duplicate profiles periodically
- Review automation accuracy
- Update similarity thresholds if needed

═══════════════════════════════════════════════════════════════════════════════
✅ SUCCESS INDICATORS
═══════════════════════════════════════════════════════════════════════════════

After successful deployment, you should see:

✅ Migration completes without errors
✅ Sample profiles created (POI-001, POI-002, POI-003)  
✅ /alleged_subject_list page loads and shows profiles
✅ AI analysis automatically creates new profiles
✅ Manual input automatically creates new profiles
✅ No duplicate profiles for same person
✅ Email-profile linking works correctly

═══════════════════════════════════════════════════════════════════════════════
📞 SUPPORT
═══════════════════════════════════════════════════════════════════════════════

If you encounter issues:

1. Check the application logs for error messages
2. Verify all files were uploaded correctly  
3. Ensure database backup was created before migration
4. Test the system step-by-step as described above

The automation system is designed to be robust and fail gracefully - if automation 
fails, the main application continues to work normally.

═══════════════════════════════════════════════════════════════════════════════
"""
