#!/usr/bin/env python3
"""Test with detailed response analysis"""

import requests
import json
import base64
from pathlib import Path

IDF_API_BASE = "https://web-production-3092c.up.railway.app"
ENERGYPLUS_API_BASE = "https://web-production-1d1be.up.railway.app"

# Generate IDF
print("1. Generating IDF...")
url = f"{IDF_API_BASE}/api/generate"
payload = {
    "address": "233 S Wacker Dr Chicago IL 60606",
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
    print(f"   ✓ IDF generated: {len(idf_content):,} characters")
else:
    print(f"   ✗ Failed: {data.get('error')}")
    exit(1)

# Simulate
print("\n2. Running simulation...")
weather_file = Path('artifacts/desktop_files/weather/Chicago.epw')
with open(weather_file, 'rb') as f:
    weather_bytes = f.read()
    weather_b64 = base64.b64encode(weather_bytes).decode('utf-8')

sim_payload = {
    'idf_content': idf_content,
    'idf_filename': 'test.idf',
    'weather_content': weather_b64,
    'weather_filename': 'Chicago.epw'
}

sim_response = requests.post(
    f"{ENERGYPLUS_API_BASE}/simulate",
    json=sim_payload,
    timeout=600
)

sim_data = sim_response.json()

print(f"\n3. Response Analysis:")
print(f"   Status: {sim_data.get('simulation_status')}")
print(f"   Error Message: {sim_data.get('error_message', 'N/A')[:200]}")
print(f"   Processing Time: {sim_data.get('processing_time', 'N/A')}")

# Check error log
error_log = sim_data.get('error_file_content', '')
print(f"\n   Error Log Length: {len(error_log) if error_log else 0} bytes")

if error_log and len(error_log) > 0:
    print(f"\n   Error Log Content (first 500 chars):")
    print("   " + "-" * 60)
    print("   " + error_log[:500].replace('\n', '\n   '))
    print("   " + "-" * 60)
    
    # Count warnings/errors
    warnings = error_log.count('** Warning **')
    fatal_errors = error_log.count('**  Fatal  **')
    severe_errors = error_log.count('** Severe  **')
    
    print(f"\n   Warnings: {warnings}")
    print(f"   Fatal Errors: {fatal_errors}")
    print(f"   Severe Errors: {severe_errors}")
else:
    print("   No error log content (empty or not provided)")

# Check output files
output_files = sim_data.get('output_files', [])
print(f"\n   Output Files: {len(output_files)}")
for f in output_files[:5]:
    print(f"     - {f.get('name')}: {f.get('size', 0)} bytes")

# Check energy results
energy_results = sim_data.get('energy_results')
if energy_results:
    print(f"\n   Energy Results:")
    print(f"     Total Site Energy: {energy_results.get('total_site_energy_kwh', 'N/A')} kWh")
    print(f"     Building Area: {energy_results.get('building_area_m2', 'N/A')} m²")
    print(f"     EUI: {energy_results.get('eui_kwh_m2', 'N/A')} kWh/m²")
else:
    print(f"\n   No energy results in response")

# Check for SQLite file
sqlite_files = [f for f in output_files if f.get('name', '').endswith('.sql')]
if sqlite_files:
    print(f"\n   SQLite file found: {sqlite_files[0].get('name')} ({sqlite_files[0].get('size', 0)} bytes)")

print("\n" + "="*70)





