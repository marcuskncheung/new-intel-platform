# 🐘 PostgreSQL Migration Guide
## Intelligence Platform Database Migration

### 📋 **Prerequisites**

1. **Backup your current SQLite database**:
   ```bash
   cp instance/users.db instance/users.db.backup
   ```

2. **Install Docker and Docker Compose** (if not already installed)

3. **Update your Exchange password** in `.env.postgresql`

---

### 🚀 **Quick Migration (Recommended)**

#### **Step 1: Prepare Environment**
```bash
# Copy PostgreSQL environment file
cp .env.postgresql .env.production

# Update the Exchange password (REQUIRED)
nano .env.production
# Edit: EXCHANGE_PASSWORD=YourRealExchangePassword123
```

#### **Step 2: Start PostgreSQL Database**
```bash
# Start only the PostgreSQL database first
docker-compose -f docker-compose.postgresql.yml up -d postgres-db

# Wait for database to be ready (about 30 seconds)
docker-compose -f docker-compose.postgresql.yml logs -f postgres-db
```

#### **Step 3: Run Database Migration**
```bash
# Run the migration script to transfer your 300MB SQLite data
docker-compose -f docker-compose.postgresql.yml --profile migration up db-migrate

# Check migration logs
docker-compose -f docker-compose.postgresql.yml logs db-migrate
```

#### **Step 4: Start Full Application**
```bash
# Start the complete application stack
docker-compose -f docker-compose.postgresql.yml up -d

# Monitor startup
docker-compose -f docker-compose.postgresql.yml logs -f intelligence-platform
```

#### **Step 5: Verify Migration**
```bash
# Check application status
docker-compose -f docker-compose.postgresql.yml ps

# Access the platform
open https://localhost
```

---

### 🔧 **Manual Migration (Advanced)**

If you need more control over the migration process:

#### **1. Install PostgreSQL Dependencies**
```bash
pip install -r requirements.txt
```

#### **2. Set Environment Variables**
```bash
export DATABASE_URL="postgresql://intelligence:SecureIntelDB2024!@localhost:5432/intelligence_db"
```

#### **3. Run Migration Script**
```bash
python migrate_sqlite_to_postgres.py
```

---

### 📊 **Verification Steps**

#### **Check Database Connection**
```bash
# Connect to PostgreSQL
docker exec -it intelligence-db psql -U intelligence -d intelligence_db

# Run verification queries
\dt  # List all tables
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM emails;  -- Or whatever your main tables are
\q
```

#### **Check Application Logs**
```bash
# Monitor application startup
docker-compose -f docker-compose.postgresql.yml logs -f intelligence-platform

# Check for successful database connection
docker-compose -f docker-compose.postgresql.yml logs intelligence-platform | grep -i postgresql
```

#### **Test Web Interface**
1. Open https://localhost
2. Login with admin credentials
3. Check that all data is present
4. Verify search functionality works
5. Test Exchange email import (if network allows)

---

### 🛡️ **Security & Production Setup**

#### **Update Passwords (CRITICAL)**
```bash
# Edit the environment file
nano .env.production

# Update these values:
DB_PASSWORD=YourSecureDBPassword2024!
EXCHANGE_PASSWORD=YourRealExchangePassword
ADMIN_PASSWORD=YourSecureAdminPassword2024!
```

#### **SSL Certificates**
```bash
# Your SSL certificates should already be in nginx/ssl/
ls -la nginx/ssl/
# Should show: cert.pem and key.pem
```

#### **Firewall Configuration**
```bash
# On your Linux server, ensure these ports are open:
sudo ufw allow 80/tcp     # HTTP (redirects to HTTPS)
sudo ufw allow 443/tcp    # HTTPS
sudo ufw allow 5432/tcp   # PostgreSQL (optional, for external access)
```

---

### 🔄 **Backup & Maintenance**

#### **Automatic Backups**
```bash
# Start backup service (runs daily)
docker-compose -f docker-compose.postgresql.yml --profile backup up -d db-backup

# Manual backup
docker exec intelligence-db pg_dump -U intelligence -d intelligence_db > backup_$(date +%Y%m%d).sql
```

#### **Monitor Performance**
```bash
# Check PostgreSQL performance
docker exec -it intelligence-db psql -U intelligence -d intelligence_db -c "
SELECT 
    schemaname,
    tablename,
    n_live_tup as row_count,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_stat_user_tables 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

---

### ⚠️ **Troubleshooting**

#### **Migration Failed**
```bash
# Check migration logs
docker-compose -f docker-compose.postgresql.yml logs db-migrate

# Reset and retry
docker-compose -f docker-compose.postgresql.yml down -v
docker-compose -f docker-compose.postgresql.yml up -d postgres-db
# Wait 30 seconds, then retry migration
```

#### **Database Connection Issues**
```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.postgresql.yml ps postgres-db

# Check database logs
docker-compose -f docker-compose.postgresql.yml logs postgres-db

# Test connection manually
docker exec -it intelligence-db psql -U intelligence -d intelligence_db -c "SELECT version();"
```

#### **Application Errors**
```bash
# Check app logs
docker-compose -f docker-compose.postgresql.yml logs intelligence-platform

# Common issues:
# - Template missing: Copy missing templates from templates/ folder
# - CSS missing: Check static/css/ folder has all required files
# - Exchange timeout: Network/firewall blocking Exchange server
```

---

### 📈 **Performance Benefits**

**PostgreSQL vs SQLite:**
- ✅ **Concurrent Users**: PostgreSQL supports multiple simultaneous users
- ✅ **Larger Datasets**: Better performance with large email datasets
- ✅ **Full-text Search**: Advanced text search capabilities
- ✅ **Transactions**: Better data integrity with ACID transactions
- ✅ **Scalability**: Can handle TB-scale databases
- ✅ **Monitoring**: Better performance monitoring and tuning options

**Expected Performance:**
- 🚀 **50-100x** faster complex queries
- 🚀 **Unlimited** concurrent users (vs SQLite's single writer)
- 🚀 **Advanced indexing** for intelligence analysis
- 🚀 **Real-time analytics** without blocking operations

---

### 🎯 **Next Steps After Migration**

1. **Test thoroughly** with your production data
2. **Update firewall rules** for Exchange server connectivity
3. **Set up monitoring** and alerting
4. **Configure regular backups**
5. **Train users** on new PostgreSQL-powered features
6. **Monitor performance** and optimize as needed

---

### 📞 **Support**

If you encounter issues during migration:

1. Check the troubleshooting section above
2. Review Docker logs for detailed error messages
3. Verify all environment variables are correctly set
4. Ensure sufficient disk space for database migration
5. Check network connectivity to Exchange server

The migration script includes detailed logging and verification steps to help identify and resolve any issues.
