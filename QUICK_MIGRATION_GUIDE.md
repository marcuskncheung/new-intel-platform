# 🚀 QUICK START: Run Migration on Server

## Copy-Paste These Commands (In Order)

### 1. Connect to server
```bash
ssh your-username@your-server
```

### 2. Go to project & pull latest code
```bash
cd /app && git pull
```

### 3. Run migration
```bash
python3 run_surveillance_migration.py
```

### 4. Restart Docker (only if migration succeeds)
```bash
docker-compose restart
```

---

## ✅ Success Looks Like This:
```
🚀 SURVEILLANCE ASSESSMENT MIGRATION
✅ Migration script loaded successfully
🔧 Running database migration...
✅ Migration completed successfully!
```

## ❌ Error? Check This:
- Are you in `/app` directory? → Run `pwd`
- Is Docker running? → Run `docker-compose ps`
- Still stuck? → Copy error message and send to developer

---

**That's it! 4 simple commands.**
