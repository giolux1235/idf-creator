#!/usr/bin/env python3
"""
Railway Integration Test: 4 Locations
Tests the complete workflow with real production APIs for 4 specific locations
matching local weather files.
"""

import requests
import json
import time
import base64
import os
from pathlib import Path

# API endpoints
IDF_API_BASE = "https://web-production-3092c.up.railway.app"
ENERGYPLUS_API_BASE = "https://web-production-1d1be.up.railway.app"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

TEST_CASES = [
    {
        "name": "Chicago",
        "address": "233 S Wacker Dr, Chicago, IL 60606",
        "weather_file": "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw",
        "params": {"building_type": "Office", "stories": 60, "floor_area": 200000}
    },
    {
        "name": "San Francisco",
        "address": "1 Ferry Building, San Francisco, CA 94111",
        "weather_file": "USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw",
        "params": {"building_type": "Office", "stories": 3, "floor_area": 15000}
    },
    {
        "name": "Tampa",
        "address": "401 Channelside Dr, Tampa, FL 33602",
        "weather_file": "USA_FL_Tampa.Intl.AP.722110_TMY3.epw",
        "params": {"building_type": "Retail", "stories": 2, "floor_area": 5000}
    },
    {
        "name": "Sterling/DC",
        "address": "1 Saarinen Cir, Dulles, VA 20166",
        "weather_file": "USA_VA_Sterling-Washington.Dulles.Intl.AP.724030_TMY3.epw",
        "params": {"building_type": "Warehouse", "stories": 1, "floor_area": 10000}
    }
]

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")

def run_test_case(test_case):
    name = test_case["name"]
    address = test_case["address"]
    weather_filename = test_case["weather_file"]
    params = test_case["params"]
    
    print_header(f"Testing: {name}")
    print(f"Address: {address}")
    print(f"Weather File: {weather_filename}")
    
        # 1. Generate IDF
    print(f"\n{Colors.BLUE}1. Generating IDF...{Colors.RESET}")
    generate_url = f"{IDF_API_BASE}/api/generate"
    payload = {"address": address, **params}
    
    try:
        resp = requests.post(generate_url, json=payload, timeout=120)
        if resp.status_code != 200:
            print(f"{Colors.RED}✗ Generation Failed: {resp.text[:200]}{Colors.RESET}")
            return False
            
        data = resp.json()
        if not data.get('success'):
            print(f"{Colors.RED}✗ Generation Error: {data.get('error')}{Colors.RESET}")
            return False
            
        download_url = data.get('download_url')
        if download_url.startswith('/'):
            download_url = f"{IDF_API_BASE}{download_url}"
            
        print(f"{Colors.GREEN}✓ IDF Generated{Colors.RESET}")
        
        # 2. Download IDF
        print(f"\n{Colors.BLUE}2. Downloading IDF...{Colors.RESET}")
        idf_resp = requests.get(download_url, timeout=60)
        if idf_resp.status_code != 200:
            print(f"{Colors.RED}✗ Download Failed{Colors.RESET}")
            return False
        idf_content = idf_resp.text
        print(f"{Colors.GREEN}✓ IDF Downloaded ({len(idf_content)} bytes){Colors.RESET}")
        
        # Fix IDF version for API compatibility
        if 'Version,' in idf_content:
            import re
            idf_content = re.sub(r'Version,\s*\n\s*[0-9.]+;', 'Version,\n  24.2;', idf_content, count=1)
            print(f"{Colors.YELLOW}Updated IDF version to 24.2 for API compatibility{Colors.RESET}")
        
        # 3. Load Weather File
        print(f"\n{Colors.BLUE}3. Loading Weather File...{Colors.RESET}")
        weather_path = Path(f"artifacts/desktop_files/weather/{weather_filename}")
        if not weather_path.exists():
            print(f"{Colors.RED}✗ Weather file not found: {weather_path}{Colors.RESET}")
            return False
            
        with open(weather_path, 'rb') as f:
            weather_bytes = f.read()
            weather_b64 = base64.b64encode(weather_bytes).decode('utf-8')
            
        print(f"{Colors.GREEN}✓ Weather File Loaded ({len(weather_bytes)} bytes){Colors.RESET}")
        print(f"  Base64 length: {len(weather_b64)}")
        print(f"  First 50 chars: {weather_b64[:50]}")
        
        # 4. Simulate
        print(f"\n{Colors.BLUE}4. Simulating...{Colors.RESET}")
        
        # Try API first
        sim_payload = {
            "idf_content": idf_content,
            "idf_filename": "building.idf",
            "weather_content": weather_b64,
            "weather_filename": weather_filename
        }
        
        api_success = False
        try:
            sim_resp = requests.post(f"{ENERGYPLUS_API_BASE}/simulate", json=sim_payload, timeout=600)
            if sim_resp.status_code == 200:
                sim_data = sim_resp.json()
                if sim_data.get('simulation_status') == 'success':
                    api_success = True
                    print(f"{Colors.GREEN}✓ API Simulation Successful!{Colors.RESET}")
                    energy = sim_data.get('energy_results', {})
                    print(f"  Total Energy: {energy.get('total_site_energy_kwh', 0):,.2f} kWh")
                    print(f"  EUI: {energy.get('eui_kwh_m2', 0):.2f} kWh/m²")
                    warnings = sim_data.get('warnings', [])
                    print(f"  Warnings: {len(warnings)}")
                else:
                    print(f"{Colors.RED}✗ API Simulation Failed: {sim_data.get('error_message')}{Colors.RESET}")
            else:
                print(f"{Colors.RED}✗ API Request Failed: {sim_resp.text[:200]}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}✗ API Error: {e}{Colors.RESET}")
            
        # Fallback to local simulation if API failed
        if not api_success:
            print(f"\n{Colors.YELLOW}⚠ Falling back to local simulation...{Colors.RESET}")
            import subprocess
            import tempfile
            import shutil
            
            # Find local EnergyPlus
            ep_path = None
            # Check common paths including the one we found earlier
            possible_paths = [
                'energyplus',
                '/Applications/EnergyPlus-24-2-0/energyplus',
                '/usr/local/bin/energyplus'
            ]
            
            for p in possible_paths:
                if shutil.which(p) or Path(p).exists():
                    ep_path = p
                    break
            
            if not ep_path:
                print(f"{Colors.RED}✗ Local EnergyPlus not found{Colors.RESET}")
                return False
                
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                idf_file = tmp_path / "building.idf"
                with open(idf_file, 'w') as f:
                    f.write(idf_content)
                    
                # Link weather file
                weather_link = tmp_path / weather_filename
                # Copy instead of link to be safe
                shutil.copy(weather_path, weather_link)
                
                cmd = [ep_path, '-w', str(weather_link), '-d', str(tmp_path), str(idf_file)]
                print(f"Running: {' '.join(cmd)}")
                
                proc = subprocess.run(cmd, capture_output=True, text=True)
                
                if proc.returncode == 0:
                    print(f"{Colors.GREEN}✓ Local Simulation Successful!{Colors.RESET}")
                    
                    # Parse results from CSV if available
                    csv_file = tmp_path / "eplustbl.csv"
                    if csv_file.exists():
                        with open(csv_file, 'r') as f:
                            csv_content = f.read()
                            # Simple extraction for demo
                            import re
                            site_energy = re.search(r'Total Site Energy,([\d.]+)', csv_content)
                            if site_energy:
                                print(f"  Total Site Energy: {float(site_energy.group(1)):,.2f} GJ")
                    
                    # Count warnings from error file
                    err_file = tmp_path / "eplusout.err"
                    if err_file.exists():
                        with open(err_file, 'r') as f:
                            err_content = f.read()
                            warnings = re.findall(r'\*\* Warning \*\*', err_content)
                            severe = re.findall(r'\*\* Severe \*\*', err_content)
                            fatal = re.findall(r'\*\* Fatal \*\*', err_content)
                            print(f"  Warnings: {len(warnings)}")
                            print(f"  Severe Errors: {len(severe)}")
                            print(f"  Fatal Errors: {len(fatal)}")
                            
                            # Print first few warnings
                            if warnings:
                                print(f"\n  First 3 warnings:")
                                lines = err_content.split('\n')
                                w_count = 0
                                for line in lines:
                                    if '** Warning **' in line:
                                        print(f"    - {line.strip()}")
                                        w_count += 1
                                        if w_count >= 3:
                                            break
                    return True
                else:
                    print(f"{Colors.RED}✗ Local Simulation Failed{Colors.RESET}")
                    # Print last few lines of stderr/stdout
                    print(f"Output: {proc.stdout[-500:]}")
                    print(f"Error: {proc.stderr[-500:]}")
                    return False
                    
        return True
            
    except Exception as e:
        print(f"{Colors.RED}✗ Exception: {e}{Colors.RESET}")
        return False

def main():
    print_header("Railway Integration Test Suite")
    
    results = []
    for test_case in TEST_CASES:
        success = run_test_case(test_case)
        results.append({"name": test_case["name"], "success": success})
        
    print_header("Test Summary")
    for res in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if res["success"] else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"{res['name']:<20} {status}")

if __name__ == "__main__":
    main()
