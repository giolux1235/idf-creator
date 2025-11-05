#!/usr/bin/env python3
"""
Debug test - Check full API response with weather file
"""

import requests
import json
import base64
from pathlib import Path

IDF_API_BASE = "https://web-production-3092c.up.railway.app"
ENERGYPLUS_API_BASE = "https://web-production-1d1be.up.railway.app"

# Download IDF
print("Downloading IDF...")
idf_response = requests.get(f"{IDF_API_BASE}/download/Office_api.idf", timeout=60)
idf_content = idf_response.text
print(f"IDF downloaded: {len(idf_content):,} characters")

# Load weather file
weather_dir = Path('artifacts/desktop_files/weather')
weather_file = weather_dir / 'Chicago.epw'

with open(weather_file, 'rb') as f:
    weather_bytes = f.read()
    weather_b64 = base64.b64encode(weather_bytes).decode('utf-8')

print(f"Weather file loaded: {len(weather_bytes):,} bytes")

# Send to external API
payload = {
    'idf_content': idf_content,
    'idf_filename': 'Office_api.idf',
    'weather_content': weather_b64,
    'weather_filename': 'Chicago.epw'
}

print("\nSending to external EnergyPlus API...")
response = requests.post(
    f"{ENERGYPLUS_API_BASE}/simulate",
    json=payload,
    headers={'Content-Type': 'application/json'},
    timeout=600
)

print(f"Status: {response.status_code}")

data = response.json()

print("\n" + "="*70)
print("FULL RESPONSE:")
print("="*70)
print(json.dumps(data, indent=2))

# Save to file
with open('test_response_with_weather.json', 'w') as f:
    json.dump(data, f, indent=2)

print("\n" + "="*70)
print("Response saved to: test_response_with_weather.json")
print("="*70)








