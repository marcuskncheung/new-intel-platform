# 🚨 URGENT: Fix 413 Request Entity Too Large

## Quick Fix - Run These Commands on Server

```bash
# 1. Go to project directory
cd /home/pam-du-uat-ai

# 2. Pull latest code
git pull origin main

# 3. Stop and remove nginx container
docker compose stop intelligence-nginx
docker compose rm -f intelligence-nginx

# 4. Recreate nginx container (forces new config)
docker compose up -d intelligence-nginx

# 5. Verify the fix is loaded
docker exec intelligence-nginx cat /etc/nginx/nginx.conf | grep "client_max_body_size"
```

**Expected Output:**
You should see multiple lines with `client_max_body_size 100M`

## What We Fixed

Updated **BOTH** nginx configs:
- ✅ `nginx/nginx.conf` - Now has 100M limit (was 50M)
- ✅ `nginx/nginx-ssl.conf` - Now has 100M limit (was missing)
- ✅ Added `client_max_body_size 100M` in **every location block**

## Why It Was Failing

The server was using `nginx.conf` (not `nginx-ssl.conf`), and:
1. Old limit was only 50M
2. Location blocks didn't have the setting
3. Container wasn't restarted properly after code update

## Test After Deployment

1. Go to https://10.96.135.11
2. Save an online patrol entry with screenshots
3. Should work without 413 error!

## Still Getting 413?

Run this diagnostic:

```bash
# Check which config is loaded
docker exec intelligence-nginx cat /etc/nginx/nginx.conf | head -30

# Check nginx error logs
docker compose logs intelligence-nginx --tail=50

# Verify container was recreated
docker ps | grep intelligence-nginx
```

---

**Files Changed:**
- `nginx/nginx.conf` - Increased to 100M, added to location blocks
- `nginx/nginx-ssl.conf` - Added 100M limit everywhere
- Both configs now identical in upload limits

**Commit:** 6d6bd3a (already pushed to GitHub)
