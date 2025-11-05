#!/usr/bin/env python3
"""
Check for energy results in API response - comprehensive check
"""

import requests
import json
import base64
from pathlib import Path

IDF_API_BASE = "https://web-production-3092c.up.railway.app"
ENERGYPLUS_API_BASE = "https://web-production-1d1be.up.railway.app"

print("="*70)
print("Checking for Energy Results in API Response")
print("="*70)

# Download IDF
print("\n1. Downloading IDF...")
idf_response = requests.get(f"{IDF_API_BASE}/download/Office_api.idf", timeout=60)
idf_content = idf_response.text
print(f"   ✓ IDF downloaded: {len(idf_content):,} characters")

# Load weather file
print("\n2. Loading weather file...")
weather_file = Path('artifacts/desktop_files/weather/Chicago.epw')
with open(weather_file, 'rb') as f:
    weather_bytes = f.read()
    weather_b64 = base64.b64encode(weather_bytes).decode('utf-8')
print(f"   ✓ Weather file loaded: {len(weather_bytes):,} bytes")

# Send to external API
print("\n3. Sending to EnergyPlus API...")
payload = {
    'idf_content': idf_content,
    'idf_filename': 'Office_api.idf',
    'weather_content': weather_b64,
    'weather_filename': 'Chicago.epw'
}

response = requests.post(
    f"{ENERGYPLUS_API_BASE}/simulate",
    json=payload,
    headers={'Content-Type': 'application/json'},
    timeout=600
)

print(f"   ✓ Response received: {response.status_code}")
data = response.json()

print("\n" + "="*70)
print("RESPONSE ANALYSIS")
print("="*70)

# Check all possible locations for energy results
print("\n📊 Checking for energy results...")

# Check direct energy_results field
if 'energy_results' in data:
    print(f"\n✅ FOUND: 'energy_results' field!")
    print(json.dumps(data['energy_results'], indent=2))
else:
    print("❌ 'energy_results' field: NOT FOUND")

# Check for results in different locations
possible_keys = [
    'results', 'energy', 'energy_data', 'metrics', 
    'simulation_results', 'output', 'data', 'energy_metrics',
    'consumption', 'usage', 'building_energy'
]

for key in possible_keys:
    if key in data:
        print(f"\n⚠️  Found '{key}' field:")
        print(json.dumps(data[key], indent=2)[:500])

# Check simulation status
print(f"\n📈 Simulation Status: {data.get('simulation_status')}")

# Check if status is success but no results
if data.get('simulation_status') == 'success':
    print("✅ Simulation status is SUCCESS!")
    if not data.get('energy_results'):
        print("⚠️  But no energy_results field found")
        print("   Checking all fields in response...")
        for key in data.keys():
            print(f"   - {key}: {type(data[key]).__name__}")

# Check output files
print(f"\n📁 Output Files:")
output_files = data.get('output_files', [])
sql_file = next((f for f in output_files if 'sql' in f.get('name', '').lower() and 'sqlite.err' not in f.get('name', '')), None)
if sql_file:
    print(f"   ✅ SQLite file: {sql_file.get('name')} ({sql_file.get('size'):,} bytes)")
else:
    print("   ❌ SQLite file: NOT FOUND")

# Check error message
error_msg = data.get('error_message', '')
if error_msg:
    print(f"\n⚠️  Error Message:")
    print(f"   {error_msg[:200]}")

# Check for any numeric fields that might be energy
print(f"\n🔍 Checking for numeric values that might be energy...")
for key, value in data.items():
    if isinstance(value, (int, float)) and value > 1000:
        print(f"   {key}: {value} (might be energy?)")

# Save full response
with open('full_api_response.json', 'w') as f:
    json.dump(data, f, indent=2)

print("\n" + "="*70)
print(f"Full response saved to: full_api_response.json")
print("="*70)






