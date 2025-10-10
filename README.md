# 🚀 Intelligence Platform - PostgreSQL Edition

**Modern Intelligence Management System with Enterprise PostgreSQL Database**

🆕 **This is the upgraded PostgreSQL version** - Migrated from SQLite to PostgreSQL for better performance, scalability, and multi-user support.

## 🎯 Platform Overview

The Intelligence Platform is a secure, web-based application designed for intelligence gathering, analysis, and case management. Built with enterprise security standards, PostgreSQL database, and modern containerized deployment.

### ✨ Key Features

- � **PostgreSQL Database**: Production-grade PostgreSQL 15 with ACID compliance
- � **Docker Orchestration**: Full containerized deployment with health monitoring
- 🔒 **Enterprise Security**: Multi-layer security with encryption and audit trails
- 📊 **Intelligence Management**: Email, WhatsApp, surveillance, case profiles
- � **Data Migration**: Automated SQLite to PostgreSQL migration tools
- 💾 **Persistent Storage**: Docker volumes for data persistence and backups
- �️ **Advanced Protection**: Rate limiting, XSS protection, CSRF prevention
- 👥 **Multi-user Support**: Concurrent access with PostgreSQL scalability
- � **Modern Interface**: Responsive UI with real-time analytics

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed
- 4GB RAM minimum (8GB recommended)
- Ports 80, 443 available

### 1-Minute Deployment
```bash
# Clone the repository
git clone https://github.com/marcuskncheung/new-intel-platform.git
cd new-intel-platform

# Configure environment
cp .env.example .env
nano .env  # Set your DB_PASSWORD and other configs

# Start PostgreSQL platform
docker compose up -d

# Access the platform
open http://localhost:8080
```

**Default Admin**: Create admin account on first run

## 📋 Deployment Options

### � Production PostgreSQL (Recommended)
```bash
# Full production deployment
docker compose up -d
```
- **URL**: `http://localhost:8080`
- **Database**: PostgreSQL 15 with persistent volumes
- **Features**: Health checks, auto-restart, monitoring

### � With Data Migration
```bash
# If migrating from SQLite version
cp your_old_database.db ./instance/users.db
docker compose --profile migration up db-migrate
docker compose up -d
```

### 🌐 Network Access
```bash
# Find your server IP
ifconfig | grep "inet " | grep -v "127.0.0.1"

# Access from any device on network
http://[SERVER-IP]:8080
```

## 🛡️ Security Features

### 🔐 Encryption & Protection
- **HTTPS/TLS 1.2/1.3**: All communications encrypted
- **Database Encryption**: Fernet encryption for stored data
- **Session Security**: Secure cookies, timeout protection
- **Input Validation**: Comprehensive sanitization

### 🔍 Monitoring & Auditing
- **Audit Logging**: Complete action tracking
- **Rate Limiting**: 100 requests/minute protection
- **Security Headers**: HSTS, XSS protection, frame denial
- **Access Control**: Role-based permissions

### 🏢 Enterprise Compliance
- **ISO 27001** compatible security controls
- **OWASP Top 10** protection implementation
- **GDPR** data protection features
- **SOC 2** security framework alignment

## 🛠 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │────│  Flask App       │────│  PostgreSQL DB  │
│   (Port 80/443) │    │  (Port 8080)     │    │  (Port 5432)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                        │                        │
        │                        │                        │
    SSL/TLS                Intelligence             Persistent
   Termination              Processing              Data Storage
                                                         │
                                               ┌─────────────────┐
                                               │  Docker Volumes │
                                               │  (Data Safety)  │
                                               └─────────────────┘
```

## 📊 Technology Stack

- **Backend**: Python 3.11, Flask 2.3.7, SQLAlchemy 3.0.5
- **Database**: PostgreSQL 15 with performance tuning and encryption
- **Frontend**: Bootstrap 5, Chart.js, responsive HTML5
- **Containers**: Docker & Docker Compose with health monitoring
- **Security**: Multi-layer security, audit trails, input validation
- **Storage**: Persistent Docker volumes with backup strategies

## 🆕 What's New in PostgreSQL Edition

### 🚀 **Upgraded Features**
- **Database**: Migrated from SQLite to PostgreSQL 15 
- **Performance**: Optimized for concurrent users and large datasets
- **Scalability**: Connection pooling and performance tuning
- **Reliability**: ACID compliance and data integrity
- **Backup**: Automated PostgreSQL backup system

### 🔄 **Migration Support**
```bash
# Migrate from old SQLite version
docker compose --profile migration up db-migrate
```

### 💾 **Data Persistence**
- All data stored in Docker volumes
- Survives container restarts and updates
- Automated backup retention (7 days)

## 🔧 Configuration

### Environment Variables
```bash
# PostgreSQL configuration (.env)
DB_PASSWORD=SecureIntelDB2024!
EXCHANGE_PASSWORD=YourExchangePassword123
SECRET_KEY=generated-secret-key
DB_ENCRYPTION_KEY=generated-encryption-key
```

### Security Settings
```python
# Security configuration
SECURITY_HEADERS = True
RATE_LIMITING = True
SESSION_TIMEOUT = 3600
AUDIT_LOGGING = True
```

## 📚 Documentation

- **[GitHub Enterprise Setup](GITHUB_ENTERPRISE_SETUP.md)**: Complete security scanning setup
- **[Security Policy](SECURITY.md)**: Vulnerability reporting and security guidelines
- **[Docker Documentation](docker/README.md)**: Deployment and configuration details
- **[API Documentation](docs/api.md)**: REST API reference (if applicable)

## 🔍 GitHub Enterprise Security

This repository includes comprehensive security scanning:

- **CodeQL Analysis**: Automated vulnerability detection
- **Dependency Scanning**: CVE monitoring for all dependencies
- **Secret Detection**: Credential and key exposure prevention
- **Container Security**: Docker image vulnerability scanning
- **Code Quality**: SonarCloud integration for quality metrics

See [GITHUB_ENTERPRISE_SETUP.md](GITHUB_ENTERPRISE_SETUP.md) for complete setup instructions.

## 🚨 Security Reporting

Found a security issue? Please see our [Security Policy](SECURITY.md) for responsible disclosure guidelines.

## 📋 Requirements

### System Requirements
- **OS**: Linux, macOS, Windows (with Docker)
- **RAM**: 4GB minimum, 8GB recommended for PostgreSQL
- **Storage**: 10GB available space (PostgreSQL data growth)
- **Network**: Port 8080 (app), 5432 (database), 80/443 (nginx)

### Dependencies
```bash
# Python dependencies
Flask==2.3.7
Flask-Login==0.6.3
Flask-SQLAlchemy==3.0.5
cryptography==41.0.4
# See requirements_production.txt for complete list
```



---

**Intelligence Platform 
# Enforcement-intelligence-platform
