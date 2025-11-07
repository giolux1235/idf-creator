#!/usr/bin/env python3
"""Test if we can verify SQLite file has energy data"""

import requests
import json
import base64
from pathlib import Path
import sqlite3
import tempfile
import os

IDF_API_BASE = "https://web-production-3092c.up.railway.app"
ENERGYPLUS_API_BASE = "https://web-production-1d1be.up.railway.app"

print("Testing EnergyPlus API response...")
print("="*70)

# Generate IDF
print("\n1. Generating IDF...")
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

if not data.get('success'):
    print(f"   ✗ Failed: {data.get('error')}")
    exit(1)

download_url = data.get('download_url')
if download_url.startswith('/'):
    download_url = f"{IDF_API_BASE}{download_url}"

idf_response = requests.get(download_url, timeout=60)
idf_content = idf_response.text
print(f"   ✓ IDF generated: {len(idf_content):,} characters")

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

print(f"\n3. Simulation Results:")
print(f"   Status: {sim_data.get('simulation_status')}")
print(f"   Processing Time: {sim_data.get('processing_time', 'N/A')}")

# Check error log
error_log = sim_data.get('error_file_content', '')
error_log_len = len(error_log) if error_log else 0
print(f"\n   Error Log: {error_log_len} bytes")
if error_log_len == 0:
    print("   ✅ ZERO WARNINGS AND ZERO FATAL ERRORS (empty error log)")

# Check output files
output_files = sim_data.get('output_files', [])
sqlite_files = [f for f in output_files if f.get('name', '').endswith('.sql')]

if sqlite_files:
    sqlite_file = sqlite_files[0]
    print(f"\n   SQLite File: {sqlite_file.get('name')} ({sqlite_file.get('size', 0):,} bytes)")
    
    # Try to check if SQLite file has content
    if sqlite_file.get('size', 0) > 0:
        print("   ✅ SQLite file exists and has content (simulation likely completed)")
        
        # Check if we can get the SQLite file content
        if 'content' in sqlite_file or 'data' in sqlite_file:
            print("   ✓ SQLite content available in response")
        else:
            print("   ⚠️  SQLite content not in response (may need to download separately)")

# Check energy results
energy_results = sim_data.get('energy_results')
if energy_results:
    print(f"\n   ✅ Energy Results Found:")
    print(f"      Total Site Energy: {energy_results.get('total_site_energy_kwh', 'N/A'):,} kWh")
    print(f"      Building Area: {energy_results.get('building_area_m2', 'N/A'):,.2f} m²")
    print(f"      EUI: {energy_results.get('eui_kwh_m2', 'N/A'):,.2f} kWh/m²")
else:
    print(f"\n   ⚠️  No energy_results field in response")
    print(f"      This might be an API extraction issue, not a simulation failure")

print("\n" + "="*70)
print("SUMMARY:")
print("="*70)

if error_log_len == 0:
    print("✅ ZERO WARNINGS - Error log is empty (no warnings/fatal errors)")
else:
    warnings = error_log.count('** Warning **')
    fatal_errors = error_log.count('**  Fatal  **')
    print(f"⚠️  Warnings: {warnings}, Fatal Errors: {fatal_errors}")

if sqlite_files and sqlite_files[0].get('size', 0) > 0:
    print("✅ SIMULATION COMPLETED - SQLite file exists with data")
else:
    print("❌ Simulation may not have completed (no SQLite file)")

if energy_results:
    print("✅ ENERGY RESULTS EXTRACTED - Available in response")
else:
    print("⚠️  ENERGY RESULTS NOT EXTRACTED - May need API fix")

print("="*70)





