# 🔧 Fix: 413 Request Entity Too Large Error

## Problem
When saving online patrol entries or uploading large attachments, the system returns:
```
413 Request Entity Too Large
```

## Root Cause
The nginx SSL configuration (`nginx/nginx-ssl.conf`) was missing the `client_max_body_size` setting, causing the server to reject any request larger than the default 1MB limit.

## Solution Applied

### 1. Updated nginx-ssl.conf
Added the following settings to allow larger file uploads:

```nginx
http {
    # ... existing settings ...
    
    # Allow large file uploads (online patrol entries, email attachments, etc.)
    client_max_body_size 100M;
    client_body_buffer_size 10M;
    client_body_timeout 120s;
    
    # ... rest of config ...
}
```

**Settings Explained:**
- `client_max_body_size 100M` - Maximum allowed size for request body (100MB)
- `client_body_buffer_size 10M` - Buffer size for reading client request body
- `client_body_timeout 120s` - Timeout for reading client request body (2 minutes)

## Deployment Instructions

### Step 1: Pull Latest Changes
```bash
ssh root@10.96.135.11
cd /var/www/new-intel-platform
sudo git pull origin main
```

### Step 2: Restart Nginx Container
```bash
# Restart nginx to reload the configuration
sudo docker-compose restart intelligence-nginx

# OR if you need to rebuild
sudo docker-compose up -d --force-recreate intelligence-nginx
```

### Step 3: Verify Configuration
```bash
# Check nginx configuration is valid
sudo docker exec -it intelligence-nginx nginx -t

# Should output:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### Step 4: Check Nginx Logs
```bash
# Monitor for any errors
sudo docker-compose logs -f intelligence-nginx --tail=50
```

## Testing

After deployment, test the following:

1. **Upload a large attachment** (e.g., 10MB PDF)
2. **Save an online patrol entry** with multiple screenshots
3. **Submit an email assessment** with attachments

All should work without 413 errors.

## Additional Notes

### Current Upload Limits:
- **Nginx**: 100MB per request
- **Flask**: No limit (defaults to system memory)
- **Recommended**: Keep individual files under 50MB for best performance

### If You Still Get 413 Errors:

1. **Check which nginx config is loaded:**
   ```bash
   sudo docker exec -it intelligence-nginx cat /etc/nginx/nginx.conf | grep client_max_body_size
   ```
   Should show: `client_max_body_size 100M;`

2. **Increase the limit if needed:**
   Edit `nginx/nginx-ssl.conf` and change `100M` to `200M` or higher

3. **Restart nginx:**
   ```bash
   sudo docker-compose restart intelligence-nginx
   ```

### Related Files:
- `nginx/nginx-ssl.conf` - HTTPS configuration (PRODUCTION - **NOW FIXED**)
- `nginx/nginx.conf` - HTTP configuration (Already had 50M limit)
- `docker-compose-https.yml` - Uses nginx-ssl.conf

---

**Fix Applied:** November 5, 2025  
**Commit:** [Will be shown after commit]  
**Issue:** 413 Request Entity Too Large when saving online patrol entries
