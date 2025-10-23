# 📋 HOW TO RUN SURVEILLANCE MIGRATION ON SERVER

## Step-by-Step Instructions

### 1️⃣ Connect to your server via SSH
```bash
ssh your-username@your-server-ip
```

### 2️⃣ Go to your project directory
```bash
cd /app
```

### 3️⃣ Pull the latest code from GitHub
```bash
git pull
```

### 4️⃣ Run the migration script
```bash
python3 run_surveillance_migration.py
```

That's it! The script will automatically:
- ✅ Check your database
- ✅ Add new surveillance fields
- ✅ Fix the id column auto-increment
- ✅ Show you clear success/error messages

### 5️⃣ After migration succeeds, restart Docker
```bash
docker-compose restart
```

---

## ✅ Expected Output

If successful, you should see:
```
================================================================================
✅ MIGRATION COMPLETED SUCCESSFULLY!
================================================================================

Next steps:
  1. Restart your Docker containers:
     docker-compose restart
  
  2. Test creating a new surveillance entry

Surveillance entries now support:
  ✓ Operation findings (detailed observations)
  ✓ Adverse finding flag (red flag indicator)
  ✓ Observation notes (general notes)
  ✓ Unified INT reference system
```

---

## ❌ If You See Errors

### Error: "Could not import migration script"
**Fix:** Make sure you're in the `/app` directory:
```bash
pwd  # Should show /app
cd /app
python3 run_surveillance_migration.py
```

### Error: "Connection refused" or database errors
**Fix:** Make sure Docker containers are running:
```bash
docker-compose ps  # Check container status
docker-compose up -d  # Start containers if needed
```

### Error: "Permission denied"
**Fix:** Make the script executable:
```bash
chmod +x run_surveillance_migration.py
python3 run_surveillance_migration.py
```

---

## 🆘 Need Help?

If the migration fails:
1. Copy the full error message
2. Take a screenshot if possible
3. Send it to your developer

The script is safe to run multiple times - it will skip changes that are already applied.

---

## 🧪 Testing After Migration

1. Go to your Intelligence platform
2. Click "Intelligence Source" → "Add Surveillance"
3. Create a test entry:
   - Operation Type: Mystery Shopping
   - Date: Today
   - Venue: Test Location
   - Add a target
   - Save the entry

4. The entry should save successfully without errors!
