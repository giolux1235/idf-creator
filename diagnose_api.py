#!/usr/bin/env python3
"""
Diagnose EnergyPlus API - Test different request formats
"""

import requests
import json
import base64
from pathlib import Path

API_URL = "https://web-production-1d1be.up.railway.app/simulate"

def test_api_format(format_type, payload, files=None):
    """Test API with different formats"""
    print(f"\n{'='*70}")
    print(f"Testing {format_type}")
    print(f"{'='*70}\n")
    
    try:
        if files:
            response = requests.post(API_URL, files=files, timeout=30)
        else:
            response = requests.post(
                API_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"\nResponse body:")
        try:
            result = response.json()
            print(json.dumps(result, indent=2))
        except:
            print(response.text[:500])
        
        return response
        
    except Exception as e:
        print(f"Error: {e}")
        return None

# Test 1: Minimal JSON
print("TEST 1: Minimal JSON with idf_content")
test_api_format("JSON with idf_content", {
    "idf_content": "Version,\n  24.2.0;"
})

# Test 2: JSON with base64 weather
idf_path = Path('test_outputs/api_test/api_test_233_S_Wacker_Dr__Chicago__IL_60606.idf')
if idf_path.exists():
    with open(idf_path, 'r') as f:
        idf_content = f.read()[:5000]  # First 5000 chars for testing
    
    print("\nTEST 2: JSON with full IDF (truncated)")
    test_api_format("JSON with full IDF", {
        "idf_content": idf_content,
        "idf_filename": "test.idf"
    })

# Test 3: Multipart with files
if idf_path.exists():
    print("\nTEST 3: Multipart/form-data")
    files = {
        'idf': ('test.idf', idf_content, 'text/plain')
    }
    test_api_format("Multipart", None, files=files)

# Test 4: Check API health/endpoints
print("\nTEST 4: Checking API root")
try:
    root_response = requests.get("https://web-production-1d1be.up.railway.app/", timeout=10)
    print(f"Root status: {root_response.status_code}")
    print(f"Root content: {root_response.text[:200]}")
except Exception as e:
    print(f"Root error: {e}")

print("\n" + "="*70)
print("Diagnostic complete")
print("="*70)













