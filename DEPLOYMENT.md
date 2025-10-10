# Server Deployment Guide

This guide explains how to deploy the Intelligence Platform on your server. The platform includes all data and configurations in the repository.

## Quick Start (Complete Deployment)

### 1. Clone the Repository

```bash
git clone https://github.com/marcuskncheung/intel-platform.git
cd intel-platform
```

### 2. Deploy with All Data

```bash
# Make deployment script executable
chmod +x deploy.sh

# Run deployment (includes database and all files)
./deploy.sh
```

**That's it!** The platform will start with all your existing data included.

## Alternative: Docker Pull Method

### 1. Pull the Docker Image Only

```bash
docker pull ghcr.io/marcuskncheung/intel-platform:latest
```

### 2. Download Required Files

```bash
# Download the deployment script
wget https://raw.githubusercontent.com/marcuskncheung/intel-platform/main/deploy.sh
chmod +x deploy.sh

# Download docker-compose file  
wget https://raw.githubusercontent.com/marcuskncheung/intel-platform/main/docker-compose.production.yml
```

### 3. Initialize the Platform

```bash
# Run the setup script
./init-server.sh
```

This script will:
- Create required directories (`instance/`, `logs/`, `static/uploads/`)
- Generate secure encryption keys
- Create `.env` configuration file
- Initialize the SQLite database
- Set proper file permissions

### 4. Configure Environment

Edit the generated `.env` file:

```bash
nano .env
```

**Important settings to update:**
- `ADMIN_EMAIL` and `ADMIN_PASSWORD` - Your admin account
- `MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD` - Email configuration
- `EXCHANGE_SERVER` settings (if using Exchange integration)

### 5. Start the Platform

```bash
docker-compose -f docker-compose.production.yml up -d
```

### 6. Access the Platform

- **HTTPS**: https://your-server-ip
- **HTTP** (redirects to HTTPS): http://your-server-ip

## Manual Setup (Alternative)

If you prefer manual setup:

### 1. Create Directory Structure

```bash
mkdir -p intelligence-platform/{instance,logs,static/uploads,email_attachments,data/email_files}
cd intelligence-platform
```

### 2. Create Environment File

```bash
cat > .env << 'EOF'
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here
DB_ENCRYPTION_KEY=your-fernet-key-here
DATABASE_URL=sqlite:///instance/users.db
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=ChangeThisPassword123!
EOF
```

### 3. Generate Secure Keys

```bash
# Generate Flask secret key
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# Generate database encryption key
python3 -c "from cryptography.fernet import Fernet; print('DB_ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

### 4. Run Container

```bash
docker run -d \
  --name intel-platform \
  -p 80:8080 \
  -p 443:8080 \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/static/uploads:/app/static/uploads \
  -v $(pwd)/.env:/app/.env \
  ghcr.io/marcuskncheung/intel-platform:latest
```

## Troubleshooting

### Database Issues

If the database fails to initialize:

```bash
# Check if database exists
ls -la instance/

# Recreate database manually
rm -f instance/users.db*
./init-server.sh
```

### Permission Issues

```bash
# Fix file permissions
sudo chown -R 1001:1001 instance logs static/uploads
chmod 600 .env
chmod 755 instance logs
```

### Container Logs

```bash
# Check container logs
docker logs intel-platform

# Follow logs in real-time
docker logs -f intel-platform
```

### SSL Certificate Issues

The platform generates self-signed certificates automatically. For production, you should use proper SSL certificates:

```bash
# Copy your certificates to the ssl-certs directory
mkdir -p ssl-certs
cp your-certificate.pem ssl-certs/cert.pem
cp your-private-key.pem ssl-certs/key.pem
```

## Security Notes

1. **Change Default Passwords**: Always change the admin password after first login
2. **Secure the .env File**: Never commit this file to version control
3. **Use Proper SSL**: Replace self-signed certificates with valid ones
4. **Regular Backups**: Backup the `instance/` directory regularly
5. **Update Regularly**: Keep the Docker image updated

## File Structure

After setup, your directory should look like:

```
intelligence-platform/
├── .env                    # Environment configuration (secret!)
├── docker-compose.production.yml
├── init-server.sh
├── instance/
│   ├── users.db           # Main database (backup regularly!)
│   ├── users.db-shm       # SQLite shared memory
│   └── users.db-wal       # SQLite write-ahead log
├── logs/                  # Application logs
├── static/uploads/        # User uploaded files
└── ssl-certs/            # SSL certificates (optional)
```

## Support

For issues or questions:
1. Check the application logs: `docker logs intel-platform`
2. Review this guide for common solutions
3. Ensure all environment variables are properly configured
