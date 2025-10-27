# 🚨 URGENT: Deploy Required to Fix Production Error

## **Current Problem:**
Production server showing **500 errors** on all pages because `int_analytics` route doesn't exist yet.

**Error:**
```
Could not build url for endpoint 'int_analytics'. Did you mean 'analytics' instead?
```

**Root Cause:**
- We added INT Analytics navigation link to `base.html`
- Production server doesn't have the `/int_analytics` route yet
- Need to deploy commits 0453b3e and 55b3d77

---

## 🚀 **DEPLOY NOW (7 minutes) - MUST REBUILD DOCKER IMAGE**

### **⚠️ IMPORTANT: Why Simple Restart Won't Work**
Your code is **baked into the Docker image**, not mounted as a volume. You pulled the Docker image, but it was built BEFORE your recent code changes. You must rebuild the image with the new code.

### **Step 1: SSH to Server**
```bash
ssh pam-du-uat-ai@10.96.135.11
```

### **Step 2: Pull Latest Code from GitHub**
```bash
cd /root/new-intel-platform-main
git pull origin main
```

**Expected output:**
```
From https://github.com/marcuskncheung/new-intel-platform
 * branch            main       -> FETCH_HEAD
Updating 597290c..55b3d77
Fast-forward
 templates/int_analytics.html | 480 ++++++++++++++++++
 templates/int_reference_detail.html | 315 ++++++++++++
 app1_production.py | 220 +++++++++
 templates/base.html | 8 +-
 nginx/nginx.conf | 10 +-
 ... (and more files)
```

### **Step 3: Rebuild Docker Image with New Code**
```bash
# Stop current containers
docker-compose down

# Rebuild image with new code (takes 2-3 minutes)
docker-compose build --no-cache intelligence-platform

# Start with new image
docker-compose up -d
```

**This rebuilds the Docker image with your latest code from GitHub.**

**Wait 30-60 seconds for containers to fully start.**

### **Step 4: Reload Nginx (for rate limit changes)**
```bash
# If nginx is in docker-compose:
docker-compose restart nginx

# OR if nginx is running separately:
sudo nginx -t
sudo systemctl reload nginx
```

### **Step 5: Verify It Works**
```bash
# Check application logs
docker-compose logs -f --tail=50 intelligence-app
```

**Look for:** No more "Could not build url for endpoint 'int_analytics'" errors.

### **Step 6: Test in Browser**
Visit these URLs:
- ✅ https://10.96.135.11/home (should work now)
- ✅ https://10.96.135.11/int_analytics (new analytics dashboard)
- ✅ https://10.96.135.11/alleged_subject_list (should work now)

---

## 📊 **What Gets Deployed**

### **Commit 0453b3e: INT Analytics Dashboard**
- ✅ New route: `/int_analytics`
- ✅ New route: `/int_reference/<int_reference>`
- ✅ Template: `int_analytics.html` (480 lines)
- ✅ Template: `int_reference_detail.html` (315 lines)
- ✅ Updated: `base.html` (INT Analytics nav link)
- ✅ Updated: `alleged_subject_list.html` (POI count badges)
- ✅ Updated: `/alleged_subject_list` route (cross-source counting)

### **Commit 55b3d77: Nginx Rate Limits**
- ✅ API rate: 10 req/s → 100 req/s
- ✅ API burst: 20 → 200 requests
- ✅ Login rate: 1 req/s → 5 req/s
- ✅ Login burst: 5 → 10 attempts

---

## ⚠️ **Why Production is Broken**

```
base.html (line 60):
<a href="{{ url_for('int_analytics') }}">INT Analytics</a>
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
       This route doesn't exist on production yet!
```

Every page that extends `base.html` (home, alleged_subject_list, etc.) tries to render this nav link → Flask can't find the `int_analytics` route → **500 error**.

---

## ✅ **After Deployment**

**Before:**
- ❌ 500 errors on all pages
- ❌ "Could not build url" errors in logs

**After:**
- ✅ All pages work normally
- ✅ New INT Analytics dashboard available
- ✅ No rate limit errors on frequent refresh
- ✅ POI counts show all sources correctly

---

## 🔍 **Troubleshooting**

### **If git pull fails:**
```bash
# Check current commit
git log --oneline -1

# If it's not 55b3d77, force pull
git fetch origin
git reset --hard origin/main
```

### **If docker-compose restart fails:**
```bash
# Check what's running
docker-compose ps

# Stop and restart
docker-compose down
docker-compose up -d

# Check logs
docker-compose logs -f --tail=100
```

### **If still seeing errors:**
```bash
# Verify app1_production.py has int_analytics route
grep -n "def int_analytics" /root/new-intel-platform-main/app1_production.py

# Should output line number (around line 3260)
```

---

## 📝 **Quick Copy-Paste Commands**

```bash
# All commands in one block (run on server):
ssh pam-du-uat-ai@10.96.135.11
cd /root/new-intel-platform-main
git pull origin main
docker-compose down
docker-compose build --no-cache intelligence-platform
docker-compose up -d
sleep 60
docker-compose logs -f --tail=50 intelligence-app
```

Press `Ctrl+C` to exit logs when you see successful startup messages.

---

## 🔄 **Why You Must Rebuild**

**Your Setup:**
```yaml
# docker-compose.yml
intelligence-platform:
  build: .  # <-- Code is BAKED into image
  volumes:
    - app_logs:/app/logs  # <-- Only logs mounted, NOT code
```

**This means:**
- ❌ Code is inside the Docker image (not mounted as volume)
- ❌ Pulling pre-built image = old code
- ❌ Restarting container = still running old code
- ✅ **MUST rebuild image** to get new code from GitHub

---

**Time to deploy:** ~7 minutes (includes 2-3 min build time)  
**Downtime:** ~2 minutes (during rebuild and restart)  
**Risk:** Low (both commits tested locally)

🚀 **Deploy now to fix the production errors!**
