# OpenShift Deployment Guide - Intelligence Platform

Complete guide for deploying the Intelligence Platform to OpenShift, including troubleshooting and best practices.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Deployment Architecture](#deployment-architecture)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [User Management](#user-management)
6. [Troubleshooting](#troubleshooting)
7. [Files Reference](#files-reference)

---

## Prerequisites

### Required Tools
- **OpenShift CLI (`oc`)**: Latest version
- **Docker or Podman**: For local builds (optional)
- **Git**: To clone the repository

### Required Access
- OpenShift cluster access with project/namespace permissions
- Cluster admin access if internal registry needs to be enabled

### Verify Access
```bash
# Login to OpenShift
oc login https://your-cluster:6443

# Switch to your project
oc project enforcement-intelligence-test

# Verify you can access the cluster
oc get pods
```

---

## Quick Start

### Windows (PowerShell)
```powershell
# Deploy everything with user creation
.\deploy-with-users.ps1
```

### Linux/Mac (Bash)
```bash
# Make script executable (first time only)
chmod +x deploy-with-users.sh

# Deploy everything with user creation
./deploy-with-users.sh
```

### What the script does:
1. Uploads source code and builds container image
2. Creates user creation ConfigMap
3. Deploys application with init container
4. Waits for rollout
5. Shows user creation logs
6. Shows deployment status and URL
7. Displays admin credentials info

---

## Deployment Architecture

### Components

```
┌─────────────────────────────────────────────────────┐
│                   OpenShift Cluster                  │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────────────────────────────────────┐   │
│  │          Internal Image Registry             │   │
│  │  image-registry.openshift-image-registry... │   │
│  └─────────────────────────────────────────────┘   │
│                        ↑                              │
│                        │ push built image             │
│  ┌─────────────────────────────────────────────┐   │
│  │            BuildConfig (Binary)              │   │
│  │  - Receives source code upload               │   │
│  │  - Builds Docker image                       │   │
│  │  - Pushes to ImageStream                     │   │
│  └─────────────────────────────────────────────┘   │
│                        │                              │
│                        ↓                              │
│  ┌─────────────────────────────────────────────┐   │
│  │              Deployment                      │   │
│  │  ┌─────────────────────────────────────┐   │   │
│  │  │ Init: wait-for-db                    │   │   │
│  │  │ - Waits for PostgreSQL               │   │   │
│  │  └─────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────┐   │   │
│  │  │ Main: intelligence-platform          │   │   │
│  │  │ - Creates admin user on startup      │   │   │
│  │  │ - Runs Flask application             │   │   │
│  │  └─────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────┘   │
│                        │                              │
│                        ↓                              │
│  ┌─────────────────────────────────────────────┐   │
│  │              Service                         │   │
│  │  - Internal load balancer                    │   │
│  │  - ClusterIP: 172.x.x.x:8080               │   │
│  └─────────────────────────────────────────────┘   │
│                        │                              │
│                        ↓                              │
│  ┌─────────────────────────────────────────────┐   │
│  │              Route (HTTPS)                   │   │
│  │  https://intelligence-platform-...apps...   │   │
│  └─────────────────────────────────────────────┘   │
│                                                       │
└─────────────────────────────────────────────────────┘
                         │
                         ↓
                  Public Internet
```

---

## Step-by-Step Deployment

### Step 1: Ensure Internal Registry is Enabled

**Check registry status:**
```bash
oc get configs.imageregistry.operator.openshift.io/cluster -o jsonpath='{.spec.managementState}'
```

**Expected output:** `Managed`

**If output is `Removed`, enable it (requires cluster-admin):**
```bash
# Create patch file
cat > enable-registry-patch.json <<EOF
{
  "spec": {
    "managementState": "Managed",
    "storage": {
      "emptyDir": {}
    }
  }
}
EOF

# Apply patch
oc patch configs.imageregistry.operator.openshift.io/cluster --type merge --patch-file enable-registry-patch.json

# Verify registry pods are running
oc get pods -n openshift-image-registry
```

**Why this is needed:**
OpenShift's BuildConfig pushes images to the internal registry. Without it enabled, builds fail with "InvalidOutputReference" error.

### Step 2: Create Secrets

**Database and application secrets:**
```bash
# From .env file
oc create secret generic intelligence-secrets \
  --from-literal=DATABASE_URL='postgresql://user:pass@host:5432/db' \
  --from-literal=SECRET_KEY='your-secret-key' \
  --from-literal=DB_ENCRYPTION_KEY='your-encryption-key' \
  --from-literal=ADMIN_EMAIL='admin@ia.org.hk' \
  --from-literal=ADMIN_PASSWORD='SecurePassword123!' \
  --from-literal=EXCHANGE_PASSWORD='your-exchange-password' \
  --from-literal=DB_PASSWORD='your-db-password'
```

**Or from existing .env file:**
```bash
oc create secret generic intelligence-secrets --from-env-file=.env
```

### Step 3: Create ImageStream

```bash
oc apply -f imagestream.yaml
```

**What this does:**
Creates a pointer to store container images in OpenShift's internal registry.

### Step 4: Create BuildConfig

```bash
oc apply -f buildconfig.yaml
```

**What this does:**
Defines how to build the container image using Docker and binary source upload.

### Step 5: Build the Image

```bash
oc start-build intelligence-platform --from-dir=. --follow
```

**What this does:**
- Compresses current directory
- Uploads to OpenShift build pod
- Executes Dockerfile build
- Pushes result to ImageStream
- Shows build logs in real-time

**Build time:** 2-5 minutes (depending on cluster and network)

### Step 6: Deploy Application

```bash
oc apply -f openshift-build-and-deploy.yaml
```

**What this does:**
Creates/updates:
- Deployment (with init containers)
- Service (internal load balancer)
- Route (public HTTPS endpoint)

### Step 7: Wait for Rollout

```bash
oc rollout status deployment/intelligence-platform --timeout=300s
```

**What this monitors:**
- Init container completion (wait-for-db)
- Pod startup
- Health check passing

### Step 8: Get Application URL

```bash
oc get route intelligence-platform -o jsonpath='{.spec.host}'
```

**Example output:**
```
intelligence-platform-enforcement-intelligence-test.apps.osc.corp.ia
```

**Access:** `https://intelligence-platform-enforcement-intelligence-test.apps.osc.corp.ia`

---

## User Management

### Default Admin User

**Created automatically on first startup:**
- **Username:** Extracted from `ADMIN_EMAIL` (e.g., `admin@ia.org.hk` → `admin`)
- **Password:** From `ADMIN_PASSWORD` in secrets
- **Role:** admin

### How It Works

User creation happens in `app1_production.py` at startup:

```python
# On first startup only
if not user_exists:
    create_admin_user(username, password, role='admin')
    print("✅ Created admin user: admin")
```

### Verify User Creation

```bash
# SSH into running pod
oc rsh deployment/intelligence-platform

# List users
python create_user.py list
```

**Expected output:**
```
📊 Current Users (1 total):
ID:  1 | admin | admin | ✅ Active | Last: Never
```

### Create Additional Users

```bash
# SSH into pod
oc rsh deployment/intelligence-platform

# Create regular user
python create_user.py create analyst Password123! user

# Create admin user
python create_user.py create superadmin Password456! admin
```

---

## Troubleshooting

### Issue 1: Build Fails - "InvalidOutputReference"

**Error:**
```
Error from server (BadRequest): build failed: InvalidOutputReference: 
Output image could not be resolved.
```

**Cause:** Internal registry is disabled

**Solution:**
```bash
# Enable registry (requires cluster-admin)
oc patch configs.imageregistry.operator.openshift.io/cluster \
  --type merge \
  --patch '{"spec":{"managementState":"Managed","storage":{"emptyDir":{}}}}'

# Wait for registry pods
oc get pods -n openshift-image-registry -w

# Retry build
oc start-build intelligence-platform --from-dir=. --follow
```

### Issue 2: Pod CrashLoopBackOff

**Check logs:**
```bash
# Get pod name
POD=$(oc get pods -l app=intelligence-platform -o jsonpath='{.items[0].metadata.name}')

# Check logs
oc logs $POD

# Check previous crash
oc logs $POD --previous
```

**Common causes:**
- Missing environment variables → Check secrets exist
- Database connection failure → Verify DATABASE_URL
- Permission errors → Check Dockerfile has `chmod 777` on writable dirs

### Issue 3: Permission Denied Errors

**Error in logs:**
```
PermissionError: [Errno 13] Permission denied: '/app/data'
```

**Cause:** OpenShift runs containers with random non-root UIDs

**Solution:** Ensure Dockerfile has:
```dockerfile
RUN mkdir -p /app/data /app/logs /app/email_attachments && \
    chmod -R 777 /app/data /app/logs /app/email_attachments
```

Then rebuild:
```bash
oc start-build intelligence-platform --from-dir=. --follow
```

### Issue 4: Old Pod Won't Terminate

**Symptom:**
```
Waiting for deployment "intelligence-platform" rollout to finish: 
1 old replicas are pending termination...
```

**Solution:**
```bash
# Force delete stuck pod
oc delete pod -l app=intelligence-platform --grace-period=0 --force

# New pod will start automatically
oc get pods -l app=intelligence-platform -w
```

### Issue 5: Cannot Access Route (404/503)

**Check route:**
```bash
oc get route intelligence-platform
```

**Check service endpoints:**
```bash
oc get endpoints intelligence-platform
```

**Should show pod IPs:**
```
NAME                    ENDPOINTS           AGE
intelligence-platform   10.131.0.45:8080    5m
```

**If empty, check pod status:**
```bash
oc get pods -l app=intelligence-platform
```

### Issue 6: Health Checks Failing

**Check health endpoint:**
```bash
# From within cluster
oc rsh deployment/intelligence-platform
curl http://localhost:8080/health

# Should return: {"status": "healthy"}
```

**If fails, check:**
- Application port matches (8080)
- Health endpoint exists in code
- No startup errors in logs

---

## Files Reference

### Core Deployment Files

| File | Purpose | When to Update |
|------|---------|----------------|
| `imagestream.yaml` | Defines image storage in internal registry | Never (unless changing app name) |
| `buildconfig.yaml` | Defines Docker build from binary source | If Dockerfile path changes |
| `openshift-build-and-deploy.yaml` | Complete deployment manifest | When changing env vars, resources, or adding services |
| `user-creation-configmap.yaml` | User creation script for init container | When modifying user creation logic |
| `deploy-with-users.ps1` | Windows deployment script | Main deployment tool for Windows |
| `deploy-with-users.sh` | Linux/Mac deployment script | Main deployment tool for Linux/Mac |
| `Dockerfile` | Container image definition | When adding dependencies or directories |

### Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Local development environment variables |
| `intelligence-secrets` (Secret) | Production environment variables in OpenShift |
| `.dockerignore` | Files excluded from build uploads |

### Documentation

| File | Purpose |
|------|---------|
| `OPENSHIFT_DEPLOYMENT.md` | This file - complete deployment guide |
| `DATABASE_ARCHITECTURE.md` | Database schema and architecture documentation |
| `README.md` | Project overview and getting started |

---

## Best Practices

### Security

1. **Never commit secrets to Git**
   ```bash
   # Create secrets from command line
   oc create secret generic intelligence-secrets --from-literal=KEY=VALUE
   ```

2. **Use strong passwords**
   - Minimum 12 characters
   - Mix of uppercase, lowercase, numbers, symbols

3. **Rotate secrets regularly**
   ```bash
   oc delete secret intelligence-secrets
   oc create secret generic intelligence-secrets --from-env-file=.env.production
   oc rollout restart deployment/intelligence-platform
   ```

4. **Enable HTTPS**
   - Already configured in Route
   - Automatic TLS certificate from OpenShift

### Performance

1. **Set appropriate resource limits**
   ```yaml
   resources:
     requests:
       memory: "512Mi"
       cpu: "250m"
     limits:
       memory: "2Gi"
       cpu: "1000m"
   ```

2. **Use health checks**
   - Configured in deployment YAML
   - Liveness: Restart unhealthy pods
   - Readiness: Don't route traffic until ready

3. **Scale horizontally**
   ```bash
   oc scale deployment/intelligence-platform --replicas=3
   ```

### Development Workflow

1. **Make code changes locally**
2. **Test with docker-compose** (optional)
   ```bash
   docker-compose up
   ```
3. **Deploy to OpenShift**
   ```bash
   # Windows
   .\deploy-with-users.ps1
   
   # Linux/Mac
   ./deploy-with-users.sh
   ```
4. **Check logs for errors**
   ```bash
   oc logs -f deployment/intelligence-platform
   ```

---

## Quick Commands Reference

```bash
# Deploy from scratch
./deploy-with-users.sh        # Linux/Mac
.\deploy-with-users.ps1       # Windows

# Rebuild after code changes
oc start-build intelligence-platform --from-dir=. --follow

# Restart pods
oc rollout restart deployment/intelligence-platform

# Check status
oc get pods -l app=intelligence-platform
oc rollout status deployment/intelligence-platform

# View logs
oc logs -f deployment/intelligence-platform
oc logs <pod-name> --previous  # Previous crashed pod

# View user creation logs (init container)
oc logs <pod-name> -c create-default-users

# Get application URL
oc get route intelligence-platform

# SSH into pod
oc rsh deployment/intelligence-platform

# List users
oc rsh deployment/intelligence-platform -- python create_user.py list

# Create additional user
oc rsh deployment/intelligence-platform -- python create_user.py create USERNAME PASSWORD [admin|user]

# Delete everything
oc delete all -l app=intelligence-platform

# Scale
oc scale deployment/intelligence-platform --replicas=2

# Update secrets
oc create secret generic intelligence-secrets --from-env-file=.env --dry-run=client -o yaml | oc apply -f -
```

---

## Support

**Common Issues:** See [Troubleshooting](#troubleshooting) section

**OpenShift Documentation:** https://docs.openshift.com/

**Project Repository:** https://github.com/Hong-Kong-Insurance-Authority/Enforcement-intelligence-platform

---

**Last Updated:** December 3, 2025  
**Version:** 2.0  
**Platform:** OpenShift 4.x  
**Project:** Enforcement Intelligence Platform
