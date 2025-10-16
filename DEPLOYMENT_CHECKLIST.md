# Deployment Checklist and Instructions

## Issues Fixed in This Update:

### 1. Database Schema Issues ✅
- **Problem**: `audit_log` table columns too small causing errors:
  - `session_id` VARCHAR(100) → VARCHAR(200)
  - `resource_type` VARCHAR(50) → VARCHAR(200) 
  - `resource_id` VARCHAR(36) → VARCHAR(100)

- **Fix**: Updated model definitions and added migration script

### 2. SQLAlchemy Deprecation Warning ✅
- **Problem**: Using legacy `User.query.get(int(uid))` 
- **Fix**: Updated to `db.session.get(User, int(uid))`

### 3. Data Truncation Protection ✅
- **Problem**: Long data causing database errors
- **Fix**: Added proper truncation in `AuditLog.log_action()` method

### 4. Dark Mode Support ✅
- **Feature**: Added comprehensive dark/light theme toggle
- **Benefits**: Better user experience for users with dark mode preferences
- **Implementation**: CSS variables, theme persistence, smooth transitions

## Server Deployment Steps:

### Step 1: Pull Latest Code
```bash
cd /path/to/new-intel-platform-staging
git pull origin main
```

### Step 2: Run Database Migration
```bash
# Run the migration script inside the container
docker exec -it intelligence-app python3 fix_audit_log_columns.py
# OR if service name is different:
docker compose exec intelligence-platform python3 fix_audit_log_columns.py
```

### Step 3: Restart Docker Services
```bash
# Restart containers to apply code changes
docker compose down
docker compose up -d
```

### Step 4: Verify Deployment
```bash
# Check container status
docker compose ps

# Check logs for errors (use correct service name from docker compose ps)
docker compose logs intelligence-platform --tail 50

# Test the application
curl -k https://your-server-ip/health
```

## Expected Results:

### Before Fix (Error Logs):
```
intelligence-db | ERROR: value too long for type character varying(100)
intelligence-app | ⚠️ Audit log error: (psycopg2.errors.StringDataRightTruncation)
```

### After Fix (Clean Logs):
```
intelligence-app | ✅ Audit log entry created successfully
intelligence-db | [No more varchar length errors]
```

## Rollback Plan:
If issues occur, rollback using:
```bash
git checkout HEAD~1  # Go back to previous version
docker-compose down
docker-compose up -d
```

## Files Modified:
- `app1_production.py`: Fixed SQLAlchemy deprecation and added data truncation
- `fix_audit_log_columns.py`: Database migration script
- `static/css/dark-mode.css`: Comprehensive dark mode support
- `static/js/theme.js`: Theme management and toggle functionality
- `templates/base.html`: Added theme toggle and dark mode resources
- `DEPLOYMENT_CHECKLIST.md`: This file

## Database Compatibility:
- ✅ PostgreSQL (Production)
- ✅ SQLite (Development)
- ✅ Handles both with appropriate migration strategy

## Security Notes:
- All sensitive data continues to be encrypted
- Migration script includes error handling and rollback
- No user data is lost during migration
