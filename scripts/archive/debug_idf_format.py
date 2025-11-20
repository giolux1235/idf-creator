#!/usr/bin/env python3
"""Debug IDF format issues"""

import requests
import json

IDF_API_BASE = "https://web-production-3092c.up.railway.app"

# Generate IDF
url = f"{IDF_API_BASE}/api/generate"
payload = {
    "address": "123 Market St, San Francisco, CA 94103",
    "user_params": {
        "building_type": "Office",
        "stories": 2,
        "floor_area": 500
    }
}

response = requests.post(url, json=payload, timeout=120)
data = response.json()

if data.get('success'):
    download_url = data.get('download_url')
    if download_url.startswith('/'):
        download_url = f"{IDF_API_BASE}{download_url}"
    
    idf_response = requests.get(download_url, timeout=60)
    idf_content = idf_response.text
    
    # Find Site:Location object
    lines = idf_content.split('\n')
    in_site_location = False
    site_location_lines = []
    
    for i, line in enumerate(lines[:100]):  # Check first 100 lines
        if 'Site:Location' in line:
            in_site_location = True
            site_location_lines.append(f"Line {i+1}: {line}")
        elif in_site_location:
            site_location_lines.append(f"Line {i+1}: {line}")
            if line.strip().endswith(';'):
                break
    
    print("Site:Location object:")
    print('\n'.join(site_location_lines))
    print("\n" + "="*70)
    print("Raw lines around line 51:")
    for i in range(45, min(60, len(lines))):
        print(f"Line {i+1}: {repr(lines[i])}")





