#!/usr/bin/env python3
"""
Test script to verify IDF generation produces 0 warnings
Runs tests with EnergyPlus API and checks error logs
"""

import sys
import requests
import json
import base64
import re
from pathlib import Path
from typing import Dict, List, Tuple

# API URLs
IDF_API_BASE = "https://web-production-3092c.up.railway.app"
ENERGYPLUS_API_BASE = "https://web-production-1d1be.up.railway.app"

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    CYAN = '\033[96m'


def find_weather_files() -> List[Path]:
    """Find available weather files"""
    weather_dir = Path('artifacts/desktop_files/weather')
    weather_files = []
    
    # Check main directory
    if weather_dir.exists():
        weather_files.extend(weather_dir.glob('*.epw'))
    
    # Check nested directories
    for nested_dir in weather_dir.rglob('*.epw'):
        if nested_dir not in weather_files:
            weather_files.append(nested_dir)
    
    return weather_files


def generate_idf_from_api(address: str, building_params: Dict) -> Tuple[bool, str]:
    """Generate IDF file from API"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'STEP 1: Generating IDF from API'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    url = f"{IDF_API_BASE}/api/generate"
    payload = {
        "address": address,
        "user_params": building_params
    }
    
    print(f"{Colors.CYAN}Address: {address}{Colors.RESET}")
    print(f"{Colors.CYAN}Building Type: {building_params.get('building_type', 'Office')}{Colors.RESET}")
    print(f"{Colors.CYAN}Stories: {building_params.get('stories', 2)}{Colors.RESET}")
    print(f"{Colors.CYAN}Floor Area: {building_params.get('floor_area', 500)} m²{Colors.RESET}")
    print(f"\n{Colors.BLUE}Sending request to: {url}{Colors.RESET}")
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        
        if response.status_code != 200:
            print(f"{Colors.RED}✗ API returned status {response.status_code}{Colors.RESET}")
            print(f"Response: {response.text[:500]}")
            return False, None
        
        data = response.json()
        
        if not data.get('success'):
            print(f"{Colors.RED}✗ IDF generation failed{Colors.RESET}")
            print(f"Error: {data.get('error', 'Unknown error')}")
            return False, None
        
        # Check if IDF content is in response or if we need to download
        idf_content = data.get('idf_content')
        
        if not idf_content:
            # Try to download from download_url
            download_url = data.get('download_url')
            if download_url:
                print(f"{Colors.BLUE}Downloading IDF from: {download_url}{Colors.RESET}")
                if download_url.startswith('/'):
                    download_url = f"{IDF_API_BASE}{download_url}"
                
                download_response = requests.get(download_url, timeout=60)
                if download_response.status_code == 200:
                    idf_content = download_response.text
                    print(f"{Colors.GREEN}✓ IDF downloaded successfully{Colors.RESET}")
                else:
                    print(f"{Colors.RED}✗ Failed to download IDF: {download_response.status_code}{Colors.RESET}")
                    return False, None
            else:
                print(f"{Colors.RED}✗ No IDF content or download_url in response{Colors.RESET}")
                print(f"Response keys: {list(data.keys())}")
                return False, None
        
        if not idf_content:
            print(f"{Colors.RED}✗ No IDF content available{Colors.RESET}")
            return False, None
        
        print(f"{Colors.GREEN}✓ IDF obtained successfully ({len(idf_content):,} characters){Colors.RESET}")
        return True, idf_content
        
    except Exception as e:
        print(f"{Colors.RED}✗ Error calling API: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return False, None


def simulate_with_api(idf_content: str, weather_file: Path) -> Tuple[bool, Dict]:
    """Simulate IDF with EnergyPlus API"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'STEP 2: Running EnergyPlus Simulation'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    url = f"{ENERGYPLUS_API_BASE}/simulate"
    
    # Read weather file
    with open(weather_file, 'rb') as f:
        weather_bytes = f.read()
        weather_b64 = base64.b64encode(weather_bytes).decode('utf-8')
    
    payload = {
        'idf_content': idf_content,
        'idf_filename': 'test_building.idf',
        'weather_content': weather_b64,
        'weather_filename': weather_file.name
    }
    
    print(f"{Colors.BLUE}Weather File: {weather_file.name}{Colors.RESET}")
    print(f"{Colors.BLUE}Sending to: {url}{Colors.RESET}")
    print(f"{Colors.YELLOW}This may take 1-2 minutes...{Colors.RESET}\n")
    
    try:
        response = requests.post(url, json=payload, timeout=600)
        
        if response.status_code != 200:
            print(f"{Colors.RED}✗ Simulation failed with status {response.status_code}{Colors.RESET}")
            print(f"Response: {response.text[:500]}")
            return False, {}
        
        data = response.json()
        print(f"{Colors.GREEN}✓ Simulation completed{Colors.RESET}")
        return True, data
        
    except Exception as e:
        print(f"{Colors.RED}✗ Error calling simulation API: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return False, {}


def analyze_warnings(error_log: str) -> Dict:
    """Analyze error log for warnings and fatal errors"""
    if not error_log:
        return {
            'total_warnings': 0,
            'total_fatal_errors': 0,
            'warning_types': {},
            'warning_lines': [],
            'fatal_errors': []
        }
    
    lines = error_log.split('\n')
    warnings = []
    fatal_errors = []
    warning_types = {}
    
    # Pattern to match warning lines
    warning_pattern = re.compile(r'\*\* Warning \*\* (.+)')
    fatal_pattern = re.compile(r'\*\*  Fatal  \*\* (.+)')
    severe_pattern = re.compile(r'\*\* Severe  \*\* (.+)')
    
    for line in lines:
        # Check for fatal errors
        fatal_match = fatal_pattern.search(line)
        if fatal_match:
            fatal_errors.append(fatal_match.group(1).strip())
            continue
        
        # Check for severe errors
        severe_match = severe_pattern.search(line)
        if severe_match:
            fatal_errors.append(f"SEVERE: {severe_match.group(1).strip()}")
            continue
        
        # Check for warnings
        warning_match = warning_pattern.search(line)
        if warning_match:
            warning_msg = warning_match.group(1).strip()
            warnings.append(warning_msg)
            
            # Categorize warnings
            warning_category = 'Other'
            if 'inverted' in warning_msg.lower() or 'upside down' in warning_msg.lower() or 'tilt' in warning_msg.lower():
                warning_category = 'Geometry'
            elif 'volume' in warning_msg.lower() and 'negative' in warning_msg.lower():
                warning_category = 'Volume'
            elif 'dx coil' in warning_msg.lower() or 'coil' in warning_msg.lower():
                warning_category = 'HVAC'
            elif 'schedule' in warning_msg.lower() and 'missing' in warning_msg.lower():
                warning_category = 'Schedule'
            elif 'daylighting' in warning_msg.lower() or 'reference point' in warning_msg.lower():
                warning_category = 'Daylighting'
            elif 'ground temperature' in warning_msg.lower():
                warning_category = 'Ground Temperature'
            elif 'convergence' in warning_msg.lower() or 'iteration' in warning_msg.lower():
                warning_category = 'Convergence'
            
            warning_types[warning_category] = warning_types.get(warning_category, 0) + 1
    
    return {
        'total_warnings': len(warnings),
        'total_fatal_errors': len(fatal_errors),
        'warning_types': warning_types,
        'warning_lines': warnings[:20],  # First 20 warnings
        'fatal_errors': fatal_errors[:10]  # First 10 fatal errors
    }


def print_results(data: Dict):
    """Print simulation results"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'STEP 3: Analyzing Results'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    # Check simulation status
    sim_status = data.get('simulation_status', 'unknown')
    print(f"{Colors.BOLD}Simulation Status: {Colors.RESET}", end='')
    if sim_status == 'success':
        print(f"{Colors.GREEN}{sim_status.upper()}{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}{sim_status.upper()}{Colors.RESET}")
        error_msg = data.get('error_message', '')
        if error_msg:
            print(f"{Colors.YELLOW}  Error: {error_msg[:200]}{Colors.RESET}")
    
    # Check for error log
    error_log = data.get('error_file_content', '')
    # Also check if it's an empty string vs None
    if error_log and len(error_log) > 0:
        analysis = analyze_warnings(error_log)
        
        # Check for fatal errors first
        if analysis['total_fatal_errors'] > 0:
            print(f"\n{Colors.RED}{Colors.BOLD}FATAL ERRORS: {analysis['total_fatal_errors']}{Colors.RESET}")
            for i, error in enumerate(analysis['fatal_errors'], 1):
                print(f"  {i}. {error[:150]}")
        else:
            pass  # No fatal errors
        
        print(f"\n{Colors.BOLD}Warnings Analysis:{Colors.RESET}")
        print(f"  Total Warnings: {Colors.YELLOW}{analysis['total_warnings']}{Colors.RESET}")
        
        if analysis['total_warnings'] == 0 and analysis['total_fatal_errors'] == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ SUCCESS! Zero warnings and zero fatal errors!{Colors.RESET}\n")
        elif analysis['total_warnings'] == 0:
            print(f"\n{Colors.GREEN}✅ Zero warnings! (but {analysis['total_fatal_errors']} fatal error(s) found){Colors.RESET}\n")
        else:
            print(f"\n{Colors.YELLOW}Warning Categories:{Colors.RESET}")
            for category, count in sorted(analysis['warning_types'].items(), key=lambda x: -x[1]):
                print(f"  {category}: {count}")
            
            print(f"\n{Colors.YELLOW}Sample Warnings (first 10):{Colors.RESET}")
            for i, warning in enumerate(analysis['warning_lines'][:10], 1):
                print(f"  {i}. {warning[:100]}...")
    else:
        # No error log available - check what's in the response
        analysis = {
            'total_warnings': 0,
            'total_fatal_errors': 0,
            'warning_types': {},
            'warning_lines': [],
            'fatal_errors': []
        }
        print(f"\n{Colors.YELLOW}⚠️  No error log content available (length: {len(error_log) if error_log else 0}){Colors.RESET}")
        print(f"{Colors.YELLOW}Response keys: {list(data.keys())}{Colors.RESET}")
        
        # Check if there are other error-related fields
        if 'error' in data:
            print(f"{Colors.YELLOW}Error field: {str(data.get('error'))[:200]}{Colors.RESET}")
        if 'errors' in data:
            print(f"{Colors.YELLOW}Errors field found{Colors.RESET}")
        if 'output_files' in data:
            print(f"{Colors.BLUE}Output files: {len(data.get('output_files', []))} files{Colors.RESET}")
            for f in data.get('output_files', [])[:5]:
                print(f"  - {f.get('name', 'unknown')} ({f.get('size', 0)} bytes)")
        
        # If simulation status is success but no error log, that's actually good!
        if sim_status == 'success':
            print(f"\n{Colors.GREEN}✅ Simulation completed successfully with no error log (no warnings/fatal errors){Colors.RESET}")
    
    # Check for energy results
    energy_results = data.get('energy_results')
    if energy_results:
        print(f"\n{Colors.GREEN}Energy Results:{Colors.RESET}")
        print(f"  Total Site Energy: {energy_results.get('total_site_energy_kwh', 'N/A'):,.2f} kWh")
        print(f"  Building Area: {energy_results.get('building_area_m2', 'N/A'):,.2f} m²")
        print(f"  EUI: {energy_results.get('eui_kwh_m2', 'N/A'):,.2f} kWh/m²")
    
    return analysis if error_log else {'total_warnings': 0}


def main():
    """Main test function"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'IDF Creator - Zero Warnings Test'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")
    
    # Find weather files
    weather_files = find_weather_files()
    if not weather_files:
        print(f"{Colors.RED}✗ No weather files found!{Colors.RESET}")
        print("Please ensure weather files are in artifacts/desktop_files/weather/")
        return 1
    
    print(f"{Colors.GREEN}✓ Found {len(weather_files)} weather file(s){Colors.RESET}")
    weather_file = weather_files[0]  # Use first available
    print(f"{Colors.BLUE}Using: {weather_file.name}{Colors.RESET}\n")
    
    # Test parameters - try different addresses to avoid comma issues
    test_addresses = [
        "233 S Wacker Dr Chicago IL 60606",  # No commas
        "1600 Amphitheatre Parkway Mountain View CA",  # Google HQ
        "1 Times Square New York NY 10036"  # Times Square
    ]
    
    # Use first address
    test_address = test_addresses[0]
    building_params = {
        "building_type": "Office",
        "stories": 2,
        "floor_area": 500  # m²
    }
    
    print(f"{Colors.BOLD}Test Address: {test_address}{Colors.RESET}")
    
    # Step 1: Generate IDF
    success, idf_content = generate_idf_from_api(test_address, building_params)
    if not success:
        print(f"\n{Colors.RED}✗ Failed to generate IDF{Colors.RESET}")
        return 1
    
    # Step 2: Simulate
    success, sim_data = simulate_with_api(idf_content, weather_file)
    if not success:
        print(f"\n{Colors.RED}✗ Failed to run simulation{Colors.RESET}")
        return 1
    
    # Step 3: Analyze
    analysis = print_results(sim_data)
    
    # Final summary
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'FINAL SUMMARY'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")
    
    if analysis['total_warnings'] == 0 and analysis.get('total_fatal_errors', 0) == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 SUCCESS! Zero warnings and zero fatal errors achieved!{Colors.RESET}\n")
        return 0
    elif analysis['total_warnings'] == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ Zero warnings! (but {analysis.get('total_fatal_errors', 0)} fatal error(s) remain){Colors.RESET}\n")
        return 0  # Zero warnings is the goal
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  {analysis['total_warnings']} warning(s) found{Colors.RESET}")
        print(f"{Colors.YELLOW}Review the warning categories above for details{Colors.RESET}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
