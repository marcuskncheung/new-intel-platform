#!/bin/bash
# Deploy Intelligence Platform with User Creation
# This script deploys the application and sets up default users

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

echo -e "${CYAN}=== Intelligence Platform - Complete Deployment ===${NC}"
echo ""

APP_NAME="intelligence-platform"

# Step 1: Build the image
echo -e "${YELLOW}Step 1: Building application image...${NC}"
oc start-build $APP_NAME --from-dir=. --follow
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Build failed${NC}"
    exit 1
fi
echo -e "${GREEN}Build completed successfully${NC}"

# Step 2: Create user creation script ConfigMap
echo ""
echo -e "${YELLOW}Step 2: Creating user creation script...${NC}"
oc apply -f user-creation-configmap.yaml
if [ $? -eq 0 ]; then
    echo -e "${GREEN}User creation script configured${NC}"
else
    echo -e "${RED}ERROR: Failed to create ConfigMap${NC}"
    exit 1
fi

# Step 3: Apply deployment
echo ""
echo -e "${YELLOW}Step 3: Deploying application...${NC}"
oc apply -f openshift-build-and-deploy.yaml
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Deployment failed${NC}"
    exit 1
fi

# Step 4: Trigger rollout
echo ""
echo -e "${YELLOW}Step 4: Restarting deployment...${NC}"
oc rollout restart deployment/$APP_NAME

# Step 5: Wait for rollout
echo ""
echo -e "${YELLOW}Step 5: Waiting for deployment...${NC}"
oc rollout status deployment/$APP_NAME --timeout=300s

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}WARNING: Rollout did not complete in time${NC}"
fi

# Step 6: Show init container logs (user creation)
echo ""
echo -e "${CYAN}=== User Creation Logs ===${NC}"
POD_NAME=$(oc get pods -l app=$APP_NAME --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}' 2>/dev/null)
if [ -n "$POD_NAME" ]; then
    echo -e "${GRAY}Checking init container logs for user creation...${NC}"
    oc logs $POD_NAME -c create-default-users 2>/dev/null || echo -e "${YELLOW}WARNING: Init container logs not available (may still be running)${NC}"
fi

# Step 7: Show status
echo ""
echo -e "${GREEN}=== Deployment Status ===${NC}"
echo ""
oc get pods -l app=$APP_NAME
echo ""
ROUTE_HOST=$(oc get route $APP_NAME -o jsonpath='{.spec.host}' 2>/dev/null)
if [ -n "$ROUTE_HOST" ]; then
    echo -e "${CYAN}Application URL: https://$ROUTE_HOST${NC}"
fi

# Step 8: Show application logs
echo ""
echo -e "${CYAN}=== Recent Application Logs ===${NC}"
if [ -n "$POD_NAME" ]; then
    oc logs $POD_NAME -c intelligence-platform --tail=30 2>/dev/null
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${CYAN}Admin credentials from .env file:${NC}"
echo -e "${GRAY}   Username: admin (from ADMIN_EMAIL)${NC}"
echo -e "${GRAY}   Password: (from ADMIN_PASSWORD in intelligence-secrets)${NC}"
echo ""
echo -e "${CYAN}To view users created:${NC}"
echo -e "${GRAY}   oc rsh deployment/$APP_NAME${NC}"
echo -e "${GRAY}   python create_user.py list${NC}"
echo ""
echo -e "${CYAN}To create additional users:${NC}"
echo -e "${GRAY}   oc rsh deployment/$APP_NAME${NC}"
echo -e "${GRAY}   python create_user.py create USERNAME PASSWORD [admin|user]${NC}"
echo ""
