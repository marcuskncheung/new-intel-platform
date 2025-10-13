#!/usr/bin/env python3
"""
Direct Docling API Test Script
Helps diagnose why Docling returns 404/502 errors
"""
import requests
import urllib3
import json
import sys
import os

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_endpoint_simple(url):
    """Simple GET test to see if endpoint exists"""
    print(f"\n{'='*70}")
    print(f"SIMPLE TEST: {url}")
    print(f"{'='*70}")
    
    try:
        response = requests.get(url, verify=False, timeout=10)
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Response: {response.text[:500]}")
        return response.status_code
    except requests.RequestException as e:
        print(f"✗ Error: {type(e).__name__}: {str(e)}")
        return None

def test_endpoint_with_pdf(url, pdf_path):
    """Test endpoint with actual PDF file"""
    print(f"\n{'='*70}")
    print(f"PDF UPLOAD TEST: {url}")
    print(f"{'='*70}")
    
    if not os.path.exists(pdf_path):
        print(f"✗ PDF file not found: {pdf_path}")
        return False
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        print(f"✓ PDF loaded: {len(pdf_data)} bytes")
        
        # Try different parameter names
        for param_name in ['file', 'document', 'pdf', 'upload', 'attachment']:
            print(f"\n  Testing parameter: '{param_name}'")
            
            files = {param_name: (os.path.basename(pdf_path), pdf_data, 'application/pdf')}
            
            # Try different header combinations
            headers_sets = [
                {},
                {'Accept': 'application/json'},
                {'Content-Type': 'multipart/form-data'},
            ]
            
            for headers in headers_sets:
                try:
                    response = requests.post(
                        url,
                        files=files,
                        headers=headers,
                        verify=False,
                        timeout=60
                    )
                    
                    status = response.status_code
                    print(f"    Status {status}: ", end='')
                    
                    if status == 200:
                        print(f"✓✓✓ SUCCESS!")
                        print(f"    Response preview: {response.text[:200]}")
                        try:
                            data = response.json()
                            print(f"    JSON keys: {list(data.keys())}")
                        except:
                            pass
                        return True
                    elif status == 404:
                        print(f"✗ Not Found (wrong endpoint)")
                    elif status == 502:
                        print(f"✗ Bad Gateway (service crashed/unavailable)")
                    elif status == 400:
                        print(f"✗ Bad Request")
                        print(f"    Response: {response.text[:200]}")
                    elif status == 401:
                        print(f"✗ Unauthorized (needs auth)")
                    elif status == 413:
                        print(f"✗ Payload Too Large (file too big)")
                    else:
                        print(f"✗ Unexpected status")
                        print(f"    Response: {response.text[:200]}")
                        
                except requests.Timeout:
                    print(f"    ✗ Timeout (service too slow or hung)")
                except requests.RequestException as e:
                    print(f"    ✗ Request error: {type(e).__name__}")
                    
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    return False

def main():
    print("="*70)
    print("DOCLING SERVICE DIAGNOSTIC TEST")
    print("="*70)
    print("\nThis script will help identify why Docling returns 404/502 errors")
    print("="*70)
    
    # Get test PDF path
    if len(sys.argv) > 1:
        test_pdf = sys.argv[1]
    else:
        test_pdf = input("\nEnter path to a test PDF file: ").strip()
    
    if not test_pdf or not os.path.exists(test_pdf):
        print(f"\n✗ Error: PDF file not found: {test_pdf}")
        print("\nUsage: python3 test_docling.py /path/to/test.pdf")
        sys.exit(1)
    
    # Base URLs to test
    base_urls = [
        "https://ai-poc.corp.ia/docling",
        "https://ai-poc.corp.ia/api/docling",
        "https://ai-poc.corp.ia",
    ]
    
    # Endpoints to test
    endpoints = [
        "/convert",
        "/api/convert",
        "/v1/convert",
        "/api/v1/convert",
        "/upload",
        "/process",
        "/extract",
        "/parse",
        "",  # Try base URL
    ]
    
    print(f"\n✓ Test PDF: {test_pdf} ({os.path.getsize(test_pdf)} bytes)")
    print(f"\nTesting {len(base_urls)} base URLs × {len(endpoints)} endpoints = {len(base_urls) * len(endpoints)} combinations...")
    
    # First, test if base URLs are reachable
    print("\n" + "="*70)
    print("PHASE 1: Testing Base URL Connectivity")
    print("="*70)
    
    reachable_bases = []
    for base in base_urls:
        status = test_endpoint_simple(base)
        if status:
            reachable_bases.append(base)
    
    if not reachable_bases:
        print("\n✗✗✗ FATAL: No base URLs are reachable!")
        print("\nPossible issues:")
        print("  1. Network/firewall blocking access")
        print("  2. Service is completely down")
        print("  3. Wrong domain name")
        print("\nAction: Contact AI team to verify the correct URL")
        sys.exit(1)
    
    # Test each reachable base with all endpoints
    print("\n" + "="*70)
    print("PHASE 2: Testing PDF Upload Endpoints")
    print("="*70)
    
    working_endpoint = None
    
    for base in reachable_bases:
        for endpoint in endpoints:
            url = base + endpoint if endpoint else base
            
            if test_endpoint_with_pdf(url, test_pdf):
                working_endpoint = url
                print(f"\n✓✓✓ FOUND WORKING ENDPOINT: {url}")
                break
        
        if working_endpoint:
            break
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    if working_endpoint:
        print(f"\n✓✓✓ SUCCESS! Docling is working at: {working_endpoint}")
        print("\nUpdate your code:")
        print(f'  self.docling_api = "{working_endpoint}"')
        print(f'\nOr update intelligence_ai.py line 18:')
        print(f'  self.docling_api = "{working_endpoint}"')
    else:
        print("\n✗✗✗ ALL ENDPOINTS FAILED")
        print("\nYour 404/502 errors are likely caused by:")
        print("  1. Wrong endpoint URL (AI team using different path)")
        print("  2. Missing authentication (API key/token required)")
        print("  3. Wrong request format (parameter name, headers)")
        print("  4. Service restrictions (firewall, IP whitelist)")
        print("\nAction Required:")
        print("  📧 Email AI team with this test output")
        print("  ❓ Ask for: exact endpoint, auth method, curl example")
        print("  ✅ Keep skip_pdf_processing = True until resolved")

if __name__ == "__main__":
    main()
