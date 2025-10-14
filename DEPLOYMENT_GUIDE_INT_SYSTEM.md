# 🚀 INT Reference Number System - Deployment Guide

## ⚡ Quick Start (TL;DR)

```bash
# 1. Pull latest code
cd /path/to/new-intel-platform-staging
git pull origin main

# 2. Run migration (one command!)
sudo docker exec -it intelligence-app python migrate_add_int_reference.py

# 3. Restart
sudo docker-compose restart

# ✅ Done! All emails now have INT-001, INT-002, INT-003...
```

---

## What's New?
Your email case management system now has **professional INT reference numbering**:
- **INT-001, INT-002, INT-003...** for all emails
- Oldest email = INT-001, newest = highest number
- Can manually edit numbers (e.g., change INT-050 to INT-200)
- Allows duplicate INT numbers for related cases
- Auto-reorders when needed

---

## 📋 Deployment Steps (On Server)

### Step 1: Pull Latest Code from GitHub
```bash
ssh user@your-server
cd /path/to/new-intel-platform-staging
git pull origin main
```

### Step 2: Run Migration Script Directly
```bash
# Run migration inside Docker container (one command)
sudo docker exec -it intelligence-app python migrate_add_int_reference.py
```

**Alternative: Enter container shell first**
```bash
# Find container name (if different from intelligence-app)
sudo docker ps

# Enter container
sudo docker exec -it intelligence-app /bin/bash

# Inside container, run migration
python migrate_add_int_reference.py

# Exit container
exit
```

**Expected Output:**
```
============================================================
  INT Reference Number Migration
  Auto-generate INT-001, INT-002... for all emails
============================================================

✅ Connected to database
📋 Existing email table columns: 30

📝 Adding 5 new columns...
  ✅ Added column: int_reference_number
  ✅ Added column: int_reference_order
  ...

🔢 Generating INT reference numbers for existing emails...
  📧 Found 180 emails to process
  ✅ Assigned 180 new INT reference numbers

  📋 Sample INT numbers (oldest first):
    INT-001 - 2024-01-15 09:30:00
    INT-002 - 2024-01-15 10:45:00
    INT-003 - 2024-01-16 08:15:00

✅ Migration completed successfully!
============================================================
```

### Step 3: Restart Application
```bash
# Restart Docker container
sudo docker-compose restart
# or
sudo docker restart intelligence-app
```

---

## ✅ Verification

After deployment, check:

1. **Email List**: Should show INT-XXX badges/numbers
2. **Email Details**: Should display INT reference number
3. **Oldest Email**: Should be INT-001
4. **Newest Email**: Should be highest number (e.g., INT-180)

---

## 🎯 Key Features

### 1. Auto-Generated Numbers
- ✅ All existing emails get INT numbers (oldest first)
- ✅ New emails auto-assigned next available number
- ✅ Sequential: INT-001, INT-002, INT-003...

### 2. Manual Editing
- ✅ Click on INT number to edit
- ✅ Format: INT-XXX (up to 4 digits)
- ✅ System tracks who edited and when

### 3. Duplicate Support
- ✅ Multiple emails can have same INT number
- ✅ Useful for grouping related cases
- ✅ Example: 3 emails about Joe Lui can all be INT-100

### 4. Auto-Reorder
- ✅ Fills gaps in numbering
- ✅ Keeps manually edited numbers unchanged
- ✅ Run via: POST `/int_source/int_reference/reorder_all`

---

## 📱 User Interface Examples

### Email List Display
```
┌──────────┬────────────────────────┬─────────────────┬──────────────┐
│ INT Ref  │ Subject                │ Sender          │ Date         │
├──────────┼────────────────────────┼─────────────────┼──────────────┤
│ INT-001  │ Complaint about Agent  │ john@example    │ 2024-01-15   │
│ INT-002  │ Unlicensed Practice    │ mary@example    │ 2024-01-15   │
│ INT-100  │ Joe Lui Bribery        │ whistleblower   │ 2024-06-10   │
│ INT-100  │ Joe Lui Follow-up      │ whistleblower   │ 2024-06-15   │
└──────────┴────────────────────────┴─────────────────┴──────────────┘
```

### Email Detail Page
```
Intelligence Reference: [INT-100] 🖊️ Edit
                        └─ Click to edit

Manually Edited: ✓ Yes
Last Updated: 2025-10-14 by admin_user
```

---

## 🔧 API Endpoints

### Update INT Reference
```bash
curl -X POST http://your-server/int_source/email/167/update_int_reference \
  -H "Content-Type: application/json" \
  -d '{
    "int_reference_number": "INT-200",
    "reorder": false
  }'
```

### Reorder All References
```bash
curl -X POST http://your-server/int_source/int_reference/reorder_all
```

### Get Emails by INT Reference
```bash
curl http://your-server/int_source/int_reference/100/emails
```

---

## 🐛 Troubleshooting

### Problem: Migration fails
**Solution**: Migration script is idempotent - safe to run multiple times
```bash
sudo docker exec -it intelligence-app python migrate_add_int_reference.py
```

### Problem: INT numbers not showing
**Solution**: Restart application
```bash
sudo docker-compose restart
```

### Problem: Numbers out of order
**Solution**: Run reorder command
```bash
curl -X POST http://your-server/int_source/int_reference/reorder_all
```

### Problem: Permission denied
**Solution**: Use sudo for Docker commands
```bash
sudo docker exec -it intelligence-app python migrate_add_int_reference.py
sudo docker logs intelligence-app
```

---

## 📚 Full Documentation

See `INT_REFERENCE_SYSTEM.md` for:
- Complete API documentation
- Usage examples
- Workflow scenarios
- Best practices
- Security notes

---

## ⚠️ Important Notes

1. **Backup**: Database migration is safe, but backup recommended
2. **Downtime**: Minimal (~2 minutes for migration + restart)
3. **Rollback**: Keep current code version for rollback if needed
4. **Testing**: Test on staging environment first if available

---

## 📞 Support

If issues occur:
1. Check migration output for errors
2. Check Docker container logs: `sudo docker logs intelligence-app`
3. Review `INT_REFERENCE_SYSTEM.md` for troubleshooting
4. Contact development team

---

**Deployment Date**: 2025-10-14  
**Commit**: d45e6f5  
**Status**: ✅ Ready for Production
