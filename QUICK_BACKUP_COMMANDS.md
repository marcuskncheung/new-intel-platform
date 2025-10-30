# 🚀 Quick Backup & Database Access Commands

## 🔍 **Find Correct Database Credentials**

Your server error showed: `role "dbuser" does not exist`

Let's find the correct username:

```bash
# Method 1: Check docker-compose environment variables
grep -i postgres /home/pam-du-uat-ai/docker-compose.yml

# Method 2: Check running container environment
docker exec intelligence-db env | grep POSTGRES

# Method 3: Try default PostgreSQL username
docker exec intelligence-db psql -U postgres -d intelligence_db -c "\conninfo"
```

---

## ✅ **Working Backup Commands**

### **Option 1: Try 'postgres' user (most common)**
```bash
# Create backup with postgres user
docker exec intelligence-db pg_dump -U postgres intelligence_db > /tmp/backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh /tmp/backup_*.sql
```

### **Option 2: Try 'intelligence' user**
```bash
# Create backup with intelligence user
docker exec intelligence-db pg_dump -U intelligence intelligence_db > /tmp/backup_$(date +%Y%m%d_%H%M%S).sql
```

### **Option 3: Find username first, then backup**
```bash
# Step 1: Find the actual username
docker exec intelligence-db psql -U postgres -c "SELECT usename FROM pg_user;"

# Step 2: Use that username (replace YOUR_USERNAME)
docker exec intelligence-db pg_dump -U YOUR_USERNAME intelligence_db > /tmp/backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## 🔐 **Check Database Connection Info**

```bash
# Method 1: Check what user the app is using
docker exec intelligence-app env | grep -i database

# Method 2: Check docker-compose file
cat /home/pam-du-uat-ai/docker-compose.yml | grep -A 10 "postgres-db:"

# Method 3: Check .env file (if exists)
cat /home/pam-du-uat-ai/.env 2>/dev/null | grep -i postgres
```

---

## 🎯 **Most Likely Solution (Run This First)**

Based on PostgreSQL Docker defaults, try this:

```bash
# 1. Create backup using 'postgres' user (default superuser)
docker exec intelligence-db pg_dump -U postgres intelligence_db > /tmp/backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Check if backup succeeded
if [ -f /tmp/backup_$(date +%Y%m%d)*.sql ]; then
    echo "✅ Backup created successfully!"
    ls -lh /tmp/backup_*.sql
else
    echo "❌ Backup failed - trying to find correct username..."
    docker exec intelligence-db psql -U postgres -c "SELECT usename FROM pg_user;"
fi

# 3. Verify backup is not empty
ls -lh /tmp/backup_*.sql
```

---

## 🔍 **Quick Database Preview (Before Cleanup)**

Once you find the correct username, check what data you have:

```bash
# Replace YOUR_USERNAME with actual username (probably 'postgres')

# Check case_profile records
docker exec -i intelligence-db psql -U YOUR_USERNAME intelligence_db <<EOF
SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN created_by IN ('MIGRATION','SYSTEM','AI_AUTO') OR created_by IS NULL THEN 1 END) as migration_records,
    COUNT(CASE WHEN created_by NOT IN ('MIGRATION','SYSTEM','AI_AUTO') AND created_by IS NOT NULL THEN 1 END) as manual_records,
    MIN(created_at) as oldest,
    MAX(created_at) as newest
FROM case_profile;
EOF

# List all usernames who created records
docker exec -i intelligence-db psql -U YOUR_USERNAME intelligence_db <<EOF
SELECT DISTINCT created_by, COUNT(*) 
FROM case_profile 
GROUP BY created_by 
ORDER BY COUNT(*) DESC;
EOF
```

---

## 📊 **All-in-One Discovery Script**

Run this to find everything automatically:

```bash
#!/bin/bash
echo "=== Finding Database Credentials ==="

# Try postgres (most common)
echo ""
echo "Trying 'postgres' user..."
docker exec intelligence-db psql -U postgres -c "SELECT version();" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ 'postgres' user works!"
    DBUSER="postgres"
else
    echo "❌ 'postgres' user doesn't work"
fi

# Try intelligence
if [ -z "$DBUSER" ]; then
    echo ""
    echo "Trying 'intelligence' user..."
    docker exec intelligence-db psql -U intelligence -c "SELECT version();" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ 'intelligence' user works!"
        DBUSER="intelligence"
    else
        echo "❌ 'intelligence' user doesn't work"
    fi
fi

# Try checking environment
if [ -z "$DBUSER" ]; then
    echo ""
    echo "Checking container environment..."
    docker exec intelligence-db env | grep POSTGRES_USER
fi

if [ -n "$DBUSER" ]; then
    echo ""
    echo "=== Creating Backup with user: $DBUSER ==="
    docker exec intelligence-db pg_dump -U $DBUSER intelligence_db > /tmp/backup_$(date +%Y%m%d_%H%M%S).sql
    
    if [ $? -eq 0 ]; then
        echo "✅ Backup successful!"
        ls -lh /tmp/backup_*.sql | tail -1
    else
        echo "❌ Backup failed"
    fi
    
    echo ""
    echo "=== Quick Data Preview ==="
    docker exec -i intelligence-db psql -U $DBUSER intelligence_db <<EOF
SELECT 
    COUNT(*) as total_case_profiles,
    MIN(id) as min_id,
    MAX(id) as max_id
FROM case_profile;
EOF
fi
```

**Save and run:**
```bash
# Copy the script above to file
nano find_db_creds.sh
# Paste the script

# Make executable
chmod +x find_db_creds.sh

# Run it
./find_db_creds.sh
```

---

## ⚡ **Quick Commands (Copy-Paste Ready)**

**Step 1: Find username**
```bash
docker exec intelligence-db psql -U postgres -c "\du" 2>/dev/null || docker exec intelligence-db psql -U intelligence -c "\du" 2>/dev/null
```

**Step 2: Create backup (try both)**
```bash
# Try method 1
docker exec intelligence-db pg_dump -U postgres intelligence_db > /tmp/backup_$(date +%Y%m%d_%H%M%S).sql 2>&1

# If above fails, try method 2
docker exec intelligence-db pg_dump -U intelligence intelligence_db > /tmp/backup_$(date +%Y%m%d_%H%M%S).sql 2>&1
```

**Step 3: Verify**
```bash
ls -lh /tmp/backup_*.sql | tail -3
```

---

## 🔧 **Update MIGRATION_CLEANUP_GUIDE.md**

Once you find the correct username, replace all instances of:
- `-U dbuser` 
- `-U YOUR_USERNAME`

With your actual username (probably `-U postgres`)

---

## 💡 **Common PostgreSQL Docker Usernames**

1. **`postgres`** ← Most likely (default superuser)
2. **`intelligence`** ← If custom user created
3. **`admin`** ← Sometimes used
4. **`root`** ← Rare for PostgreSQL
5. **Check container env**: `docker exec intelligence-db env | grep USER`

---

## 🎬 **Next Steps After Backup**

Once you have a successful backup:

1. ✅ Verify backup file exists and is not empty
   ```bash
   ls -lh /tmp/backup_*.sql
   # Should be > 1MB if you have data
   ```

2. ✅ Check what's in your case_profile table
   ```bash
   docker exec -i intelligence-db psql -U postgres intelligence_db <<EOF
   SELECT COUNT(*) FROM case_profile;
   SELECT DISTINCT created_by FROM case_profile;
   EOF
   ```

3. ✅ Proceed with cleanup using correct username in commands

---

## 🆘 **Still Can't Connect?**

Try connecting without specifying database:
```bash
# Connect to default postgres database first
docker exec -it intelligence-db psql -U postgres

# Then from psql prompt:
\l                           -- List all databases
\c intelligence_db          -- Connect to your database
\dt                         -- List tables
SELECT COUNT(*) FROM case_profile;
\q                          -- Quit
```

Good luck! 🚀
