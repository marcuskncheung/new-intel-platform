# 🚀 DEPLOYMENT INSTRUCTIONS - POI v2.0 Factory Pattern Fix

## ⚠️ CRITICAL: Wait for GitHub Actions to Build New Image

The latest code (commit `b01424b`) has been pushed to GitHub.
**GitHub Actions is now building a new Docker image** and pushing it to GHCR.

## 📋 Step 1: Check GitHub Actions Status

1. Go to: https://github.com/marcuskncheung/new-intel-platform/actions
2. Look for the **"Build and Push to GHCR"** workflow
3. **Wait until it shows ✅ green checkmark** (takes ~3-5 minutes)
4. ❌ If it shows red X, the build failed - check the logs

## 📋 Step 2: Pull New Image on Production Server

**ONLY AFTER GitHub Actions completes successfully:**

```bash
# 1. SSH to production server
ssh pam-du-uat-ai@saiuapp11

# 2. Stop current containers
sudo docker compose down

# 3. Pull NEW image from GitHub Container Registry
sudo docker compose pull intelligence-platform

# 4. Start containers with new image
sudo docker compose up -d

# 5. Watch the logs for POI model initialization
sudo docker compose logs -f intelligence-app | grep "POI MODELS"
```

## ✅ Expected Success Output

You should see in the logs:
```
[POI MODELS] Calling init_models() factory function...
[POI MODELS] ✅ Factory init_models() completed successfully
[POI MODELS] 📦 Created classes: _AllegedPersonProfile, _POIIntelligenceLink, _EmailAllegedPersonLink
[POI MODELS] ✅ Successfully loaded POI models at module level
[POI MODELS] 🎯 AllegedPersonProfile is now: <class 'models_poi_enhanced._AllegedPersonProfile'>
[POI MODELS] 🎯 Has .query attribute: True
```

## ❌ If You See This Error Again

```
AttributeError: module 'models_poi_enhanced' has no attribute 'init_models'
```

This means the old image is still cached. Force remove it:

```bash
sudo docker compose down
sudo docker rmi ghcr.io/marcuskncheung/new-intel-platform:latest
sudo docker compose pull intelligence-platform
sudo docker compose up -d
```

## 🔍 Verification Steps

After deployment, test:

1. Navigate to: `https://10.96.135.11/alleged_subject_list`
2. Should see POI list (not "Error loading profiles")
3. Click any POI → should go to `/alleged_subject_profile/POI-XXX` (not `/details/211`)
4. POI profile page should show 7 colored stat cards with numbers visible
