# Deploy Intelligence Platform with User Creation
# This script deploys the application and sets up default users

Write-Host "=== Intelligence Platform - Complete Deployment ===" -ForegroundColor Cyan
Write-Host ""

$APP_NAME = "intelligence-platform"

# Step 1: Build the image
Write-Host "Step 1: Building application image..." -ForegroundColor Yellow
oc start-build $APP_NAME --from-dir=. --follow
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed" -ForegroundColor Red
    exit 1
}
Write-Host "Build completed successfully" -ForegroundColor Green

# Step 2: Create user creation script ConfigMap
Write-Host ""
Write-Host "Step 2: Creating user creation script..." -ForegroundColor Yellow
oc apply -f user-creation-configmap.yaml
if ($LASTEXITCODE -eq 0) {
    Write-Host "User creation script configured" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to create ConfigMap" -ForegroundColor Red
    exit 1
}

# Step 3: Apply deployment
Write-Host ""
Write-Host "Step 3: Deploying application..." -ForegroundColor Yellow
oc apply -f openshift-build-and-deploy.yaml
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Deployment failed" -ForegroundColor Red
    exit 1
}

# Step 4: Trigger rollout
Write-Host ""
Write-Host "Step 4: Restarting deployment..." -ForegroundColor Yellow
oc rollout restart deployment/$APP_NAME

# Step 5: Wait for rollout
Write-Host ""
Write-Host "Step 5: Waiting for deployment..." -ForegroundColor Yellow
oc rollout status deployment/$APP_NAME --timeout=300s

if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Rollout did not complete in time" -ForegroundColor Yellow
}

# Step 6: Show init container logs (user creation)
Write-Host ""
Write-Host "=== User Creation Logs ===" -ForegroundColor Cyan
$POD_NAME = oc get pods -l app=$APP_NAME --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}' 2>$null
if ($POD_NAME) {
    Write-Host "Checking init container logs for user creation..." -ForegroundColor Gray
    oc logs $POD_NAME -c create-default-users 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Init container logs not available (may still be running)" -ForegroundColor Yellow
    }
}

# Step 7: Show status
Write-Host ""
Write-Host "=== Deployment Status ===" -ForegroundColor Green
Write-Host ""
oc get pods -l app=$APP_NAME
Write-Host ""
$ROUTE_HOST = oc get route $APP_NAME -o jsonpath='{.spec.host}' 2>$null
if ($ROUTE_HOST) {
    Write-Host "Application URL: https://$ROUTE_HOST" -ForegroundColor Cyan
}

# Step 8: Show application logs
Write-Host ""
Write-Host "=== Recent Application Logs ===" -ForegroundColor Cyan
if ($POD_NAME) {
    oc logs $POD_NAME -c intelligence-platform --tail=30 2>$null
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Admin credentials from .env file:" -ForegroundColor Cyan
Write-Host "   Username: admin (from ADMIN_EMAIL)" -ForegroundColor Gray
Write-Host "   Password: (from ADMIN_PASSWORD in intelligence-secrets)" -ForegroundColor Gray
Write-Host ""
Write-Host "To view users created:" -ForegroundColor Cyan
Write-Host "   oc rsh deployment/$APP_NAME" -ForegroundColor Gray
Write-Host "   python create_user.py list" -ForegroundColor Gray
Write-Host ""
Write-Host "To create additional users:" -ForegroundColor Cyan
Write-Host "   oc rsh deployment/$APP_NAME" -ForegroundColor Gray
Write-Host "   python create_user.py create USERNAME PASSWORD [admin|user]" -ForegroundColor Gray
Write-Host ""
