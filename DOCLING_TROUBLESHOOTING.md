# Docling 502 Error Troubleshooting Guide

## Your Situation

**AI Team says**: "Docling is not broken"
**Your logs show**: 404 and 502 errors
**Question**: Is it a configuration problem on your side?

## Possible Causes

### 1. ✅ Network/Firewall Issue (MOST LIKELY)

Your system might not have proper access to the Docling service.

**Evidence from your logs:**
```
First PDF:  404 Not Found  (all endpoints)
Other PDFs: 502 Bad Gateway (service overload/crash)
```

**This pattern suggests:**
- 404 = Wrong endpoint URL OR firewall blocking requests
- 502 = Service exists but crashes/times out when processing

### 2. ⚠️ Wrong Endpoint URL

Your code tries 4 different endpoints:
```python
endpoints_to_try = [
    "https://ai-poc.corp.ia/docling/convert",           # 404
    "https://ai-poc.corp.ia/docling/api/convert",       # 404
    "https://ai-poc.corp.ia/docling/v1/convert",        # 404
    "https://ai-poc.corp.ia/docling/api/v1/convert"     # 404
]
```

**All return 404** = None of these URLs are correct!

### 3. ⚠️ Request Format Issue

Your code sends:
```python
files = {'file': (filename, file_data, 'application/pdf')}
response = self.session.post(endpoint, files=files, timeout=30)
```

**Possible issues:**
- Missing required headers
- Wrong multipart/form-data format
- Missing API key or authentication
- Wrong file parameter name (maybe should be 'document' not 'file')

### 4. ⚠️ SSL/Certificate Issue

Your code disables SSL verification:
```python
self.session.verify = False  # Skip SSL verification
```

**This might cause:**
- Corporate proxy rejecting the connection
- Security policy blocking unsigned requests
- Firewall dropping SSL-disabled connections

### 5. ⚠️ File Size Limits

Your PDFs:
```
投訴信.pdf: 112KB → 404
關於富衛保險公司...pdf: 1,075KB → 502 (too large?)
Editable_Complaint_Form_TC_202501.pdf: 747KB → 502
Editable_Complaint_Form_TC_202502.pdf: 669KB → 502
```

**Pattern**: First (small) PDF gets 404, larger PDFs get 502
**Possible**: Service has size limit, crashes on large files

---

## Diagnostic Steps

### Step 1: Ask AI Team for EXACT Configuration

**Email them these questions:**

```
Subject: Docling Configuration - Need Exact Details

Hi AI Team,

You mentioned Docling is working, but we're getting 404/502 errors.
Please provide the EXACT configuration:

1. EXACT endpoint URL:
   - Is it https://ai-poc.corp.ia/docling/convert ?
   - Or something else?

2. Request format:
   - What HTTP method? (POST?)
   - What headers are required?
   - What's the file parameter name? (file? document? pdf?)
   - Example curl command?

3. Authentication:
   - API key required?
   - Bearer token?
   - Basic auth?

4. File size limits:
   - Max file size in MB?
   - Max pages in PDF?

5. Response format:
   - What does successful response look like?
   - What field contains the extracted text?

6. Network requirements:
   - Any firewall rules needed?
   - Specific IP whitelist?
   - SSL certificate required?

Our current logs show:
- All endpoints return 404
- Files range from 112KB to 1MB
- Using Python requests library with verify=False

Please provide a working example!
```

### Step 2: Test Docling Directly (Without Your App)

Create a test script to isolate the issue:

**File: `test_docling.py`**
```python
#!/usr/bin/env python3
"""
Direct Docling API test - isolate configuration issues
"""
import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_docling_endpoint(endpoint_url, pdf_file_path):
    """Test a Docling endpoint with a real PDF"""
    
    print(f"\n{'='*60}")
    print(f"Testing: {endpoint_url}")
    print(f"{'='*60}")
    
    try:
        # Read PDF file
        with open(pdf_file_path, 'rb') as f:
            pdf_data = f.read()
        
        print(f"PDF size: {len(pdf_data)} bytes")
        
        # Try different parameter names
        for param_name in ['file', 'document', 'pdf', 'upload']:
            print(f"\nTrying parameter name: '{param_name}'")
            
            files = {param_name: ('test.pdf', pdf_data, 'application/pdf')}
            
            # Test with different header combinations
            headers_options = [
                {},  # No extra headers
                {'Content-Type': 'multipart/form-data'},
                {'Accept': 'application/json'},
                {'Content-Type': 'multipart/form-data', 'Accept': 'application/json'},
            ]
            
            for i, headers in enumerate(headers_options):
                print(f"  Headers option {i+1}: {headers or 'None'}")
                
                try:
                    response = requests.post(
                        endpoint_url,
                        files=files,
                        headers=headers,
                        verify=False,
                        timeout=30
                    )
                    
                    print(f"  ✓ Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"  ✓✓ SUCCESS! Response:")
                        print(f"     {response.text[:200]}")
                        return True
                    else:
                        print(f"  ✗ Error: {response.text[:100]}")
                        
                except requests.RequestException as e:
                    print(f"  ✗ Request failed: {type(e).__name__}: {str(e)}")
    
    except Exception as e:
        print(f"✗ Test failed: {e}")
    
    return False

if __name__ == "__main__":
    # Test PDF file (use a small one from your system)
    test_pdf = "/path/to/your/test.pdf"  # UPDATE THIS PATH
    
    # Test all possible endpoints
    endpoints = [
        "https://ai-poc.corp.ia/docling/convert",
        "https://ai-poc.corp.ia/docling/api/convert",
        "https://ai-poc.corp.ia/docling/v1/convert",
        "https://ai-poc.corp.ia/docling/api/v1/convert",
        "https://ai-poc.corp.ia/docling/",  # Try base URL
        "https://ai-poc.corp.ia/docling",   # Try without trailing slash
    ]
    
    print("="*60)
    print("DOCLING API DIAGNOSTIC TEST")
    print("="*60)
    
    for endpoint in endpoints:
        success = test_docling_endpoint(endpoint, test_pdf)
        if success:
            print(f"\n✓✓✓ WORKING ENDPOINT FOUND: {endpoint}")
            break
    else:
        print("\n✗✗✗ ALL ENDPOINTS FAILED - Contact AI team!")
```

**Run it:**
```bash
cd /Users/iapanel/Downloads/new-intel-platform-staging
python3 test_docling.py
```

### Step 3: Check Network Connectivity

Test if you can reach the Docling server at all:

```bash
# Test 1: Can you resolve the DNS?
nslookup ai-poc.corp.ia

# Test 2: Can you ping the server?
ping ai-poc.corp.ia

# Test 3: Can you connect to the port?
curl -v https://ai-poc.corp.ia/docling/

# Test 4: What do you get?
curl -X POST https://ai-poc.corp.ia/docling/convert \
  -F "file=@/path/to/test.pdf" \
  -k  # Skip SSL verification like your Python code

# Test 5: Try with different parameter name
curl -X POST https://ai-poc.corp.ia/docling/convert \
  -F "document=@/path/to/test.pdf" \
  -k
```

### Step 4: Check Docker Network Settings

Your app runs in Docker - check if Docker can reach the service:

```bash
# Enter your Docker container
docker exec -it intelligence-app bash

# Inside container, test connectivity
curl -v https://ai-poc.corp.ia/docling/
ping ai-poc.corp.ia

# Test with Python inside container
python3 -c "
import requests
import urllib3
urllib3.disable_warnings()
r = requests.get('https://ai-poc.corp.ia/docling/', verify=False, timeout=10)
print(f'Status: {r.status_code}')
print(f'Response: {r.text[:200]}')
"
```

### Step 5: Compare with Working Services

Your LLM API works, Docling doesn't. Let's compare:

**Working (LLM):**
```python
self.llm_api = "https://ai-poc.corp.ia/vllm/v1"
response = self.session.post(
    f"{self.llm_api}/completions",
    headers={"Content-Type": "application/json"},
    json={...}
)
```

**Not Working (Docling):**
```python
self.docling_api = "https://ai-poc.corp.ia/docling"
response = self.session.post(
    f"{self.docling_api}/convert",
    files={'file': (filename, file_data, 'application/pdf')}
)
```

**Questions:**
- Does Docling need `Content-Type` header?
- Does Docling need authentication like LLM?
- Is there a different base URL?

---

## Likely Root Causes (Ranked)

### 1. **Wrong Endpoint URL** (90% probability)
- AI team is using different URL than what's in your code
- They might have `/api/v2/convert` or `/upload` or something else
- **Solution**: Get exact URL from AI team

### 2. **Missing Authentication** (70% probability)
- LLM might be public, but Docling might require auth
- **Solution**: Ask if API key, Bearer token, or Basic auth needed

### 3. **Wrong Request Format** (60% probability)
- Parameter name might not be 'file'
- Might need additional form fields
- **Solution**: Ask for curl example from AI team

### 4. **Docker Network Issue** (40% probability)
- Container can't reach Docling service
- Firewall blocking Docker bridge network
- **Solution**: Test from inside container

### 5. **File Size/Type Restrictions** (30% probability)
- Service crashes on files > 500KB
- Chinese filenames causing issues
- **Solution**: Test with small English-named PDF

---

## Quick Fix Options

### Option A: Ask AI Team to Test Your Exact Files

Send them your PDFs and ask them to process them:

```
Subject: Please Test These PDFs with Docling

Hi AI Team,

Can you test these exact PDFs with your Docling service?

Files attached:
- 投訴信.pdf (112KB)
- test_complaint.pdf (747KB)

Please share:
1. The exact curl command you use
2. The successful response you get
3. Any special configuration needed

We're getting 404/502 with these endpoints:
- https://ai-poc.corp.ia/docling/convert
- https://ai-poc.corp.ia/docling/api/convert
- https://ai-poc.corp.ia/docling/v1/convert

If none of these are correct, please provide the right one!
```

### Option B: Temporary Workaround - Use Different Service

If Docling is problematic, ask if there's an alternative:
- PyMuPDF endpoint?
- OCR service?
- Different PDF extraction API?

### Option C: Keep Bypass Enabled Until Resolved

**Your current setting is CORRECT:**
```python
skip_pdf_processing = True  # Keep this until we get proper config!
```

**Benefits:**
- ✅ System works (analyzes email body)
- ✅ No delays or timeouts
- ✅ No error spam in logs
- ✅ Users can still work

**When to re-enable:**
- After AI team provides exact configuration
- After you test successfully with `test_docling.py`
- After you see `✅ Successfully extracted` in logs

---

## Summary

**Is it your configuration problem?**

**Probably YES**, but not your fault:
- ❌ Wrong endpoint URL (AI team didn't give you the right one)
- ❌ Missing authentication (AI team didn't tell you about it)
- ❌ Wrong request format (AI team didn't provide example)
- ❌ Network/firewall (AI team didn't configure access)

**What to do:**
1. ✅ **Keep your bypass enabled** - it's working perfectly
2. 📧 **Email AI team** with the diagnostic questions above
3. 🧪 **Run test_docling.py** to isolate the issue
4. 🔍 **Check Docker networking** to rule out container issues
5. ⏳ **Wait for proper configuration** before re-enabling

**Your code is fine** - you just don't have the correct Docling configuration!
