#!/usr/bin/env python3
"""
Test: Generate IDF from creator API, run simulation, analyze warnings
"""

import requests
import json
import time
import base64
from pathlib import Path
from collections import Counter

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

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")

def print_step(step_num, description):
    print(f"\n{Colors.BOLD}{Colors.BLUE}[Step {step_num}] {description}{Colors.RESET}")
    print(f"{Colors.BLUE}{'-'*70}{Colors.RESET}")

def find_weather_file():
    """Find a weather file on the machine"""
    weather_dir = Path('artifacts/desktop_files/weather')
    
    # Collect EPW candidates from project and system EnergyPlus installations
    all_epw_files = []
    # 1) Project weather dir
    all_epw_files.extend(list(weather_dir.rglob('*.epw')))
    # 2) System EnergyPlus WeatherData directories (macOS default)
    system_dirs = [
        Path('/Applications').glob('EnergyPlus-*/WeatherData/*.epw'),
        Path('/Applications').glob('EnergyPlus-*/EnergyPlus installation files/WeatherData/*.epw'),
        Path('/usr/local').glob('EnergyPlus-*/WeatherData/*.epw'),
    ]
    for it in system_dirs:
        for f in it:
            all_epw_files.append(Path(f))
    
    if not all_epw_files:
        return None
    
    # Prefer San Francisco for SF address; then Chicago
    for f in all_epw_files:
        name = f.name
        if 'San.Francisco' in name or '724940' in name:
            return f
    for f in all_epw_files:
        name = f.name
        if 'Chicago' in name or '725300' in name:
            return f
    
    # Otherwise return the first
    return all_epw_files[0]

def generate_idf_from_api(address: str, building_params: dict = None):
    """Generate IDF using the creator API"""
    print_step(1, f"Generating IDF from Address: {address}")
    
    generate_url = f"{IDF_API_BASE}/api/generate"
    payload = {
        "address": address
    }
    
    if building_params:
        payload.update(building_params)
    
    print(f"API URL: {generate_url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            generate_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=120
        )
        elapsed = time.time() - start_time
        
        print(f"\nStatus: {response.status_code}")
        print(f"Time: {elapsed:.2f} seconds")
        
        if response.status_code != 200:
            print(f"{Colors.RED}✗ Failed: {response.text[:500]}{Colors.RESET}")
            return None, None
        
        data = response.json()
        
        if not data.get('success'):
            print(f"{Colors.RED}✗ Error: {data.get('error', 'Unknown error')}{Colors.RESET}")
            return None, None
        
        filename = data.get('filename')
        download_url = data.get('download_url')
        
        if not filename or not download_url:
            print(f"{Colors.RED}✗ Missing filename or download_url{Colors.RESET}")
            return None, None
        
        print(f"{Colors.GREEN}✓ IDF generated: {filename}{Colors.RESET}")
        
        # Download IDF content
        if download_url.startswith('/'):
            download_url = f"{IDF_API_BASE}{download_url}"
        
        print(f"\nDownloading IDF from: {download_url}")
        idf_response = requests.get(download_url, timeout=60)
        
        if idf_response.status_code != 200:
            print(f"{Colors.RED}✗ Failed to download IDF{Colors.RESET}")
            return None, None
        
        idf_content = idf_response.text
        print(f"{Colors.GREEN}✓ IDF downloaded: {len(idf_content):,} characters{Colors.RESET}")
        
        return idf_content, filename
        
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return None, None

def load_weather_file():
    """Load weather file"""
    print_step(2, "Loading Weather File")
    
    weather_path = find_weather_file()
    
    if not weather_path:
        print(f"{Colors.RED}✗ No weather file found{Colors.RESET}")
        return None, None
    
    print(f"{Colors.GREEN}✓ Found weather file: {weather_path}{Colors.RESET}")
    
    try:
        with open(weather_path, 'rb') as f:
            weather_content = f.read()
            weather_b64 = base64.b64encode(weather_content).decode('utf-8')
        
        print(f"  Size: {len(weather_content):,} bytes")
        print(f"  Filename: {weather_path.name}")
        
        return weather_b64, weather_path.name
        
    except Exception as e:
        print(f"{Colors.RED}✗ Error loading weather file: {e}{Colors.RESET}")
        return None, None

def run_simulation(idf_content: str, idf_filename: str, weather_b64: str, weather_filename: str):
    """Run simulation on EnergyPlus service"""
    print_step(3, "Running EnergyPlus Simulation")
    
    simulate_url = f"{ENERGYPLUS_API_BASE}/simulate"
    
    payload = {
        'idf_content': idf_content,
        'idf_filename': idf_filename,
        'weather_content': weather_b64,
        'weather_filename': weather_filename
    }
    
    print(f"API URL: {simulate_url}")
    print(f"IDF: {idf_filename} ({len(idf_content):,} chars)")
    print(f"Weather: {weather_filename}")
    
    try:
        start_time = time.time()
        response = requests.post(
            simulate_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=600  # 10 minutes
        )
        elapsed = time.time() - start_time
        
        print(f"\nStatus: {response.status_code}")
        print(f"Time: {elapsed:.2f} seconds")
        
        if response.status_code != 200:
            print(f"{Colors.RED}✗ Failed: {response.text[:500]}{Colors.RESET}")
            return None
        
        data = response.json()
        return data
        
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return None

def analyze_warnings(simulation_result: dict):
    """Analyze and categorize warnings from simulation"""
    print_step(4, "Analyzing Warnings")
    
    warnings = simulation_result.get('warnings', [])
    error_message = simulation_result.get('error_message', '')
    error_file_content = simulation_result.get('error_file_content', '')
    status = simulation_result.get('simulation_status', 'unknown')
    
    print(f"\n{Colors.BOLD}Simulation Status: {status}{Colors.RESET}")
    print(f"Total Warnings: {len(warnings)}")
    
    if error_message:
        print(f"\n{Colors.RED}Error Message:{Colors.RESET}")
        print(f"  {error_message[:500]}")
    
    # Extract warnings from error file if available
    if error_file_content:
        error_lines = error_file_content.split('\n')
        # Extract all warning/error lines
        for line in error_lines:
            line_stripped = line.strip()
            if '**' in line_stripped and ('Warning' in line_stripped or 'Severe' in line_stripped or 'Fatal' in line_stripped):
                # Only add if not already in warnings list
                if not any(line_stripped in w for w in warnings):
                    warnings.append(line_stripped)
        
        # Also look for specific node connection errors
        for i, line in enumerate(error_lines):
            if 'node' in line.lower() and ('error' in line.lower() or 'not found' in line.lower() or 'missing' in line.lower()):
                # Get context (previous and next lines)
                context_start = max(0, i-2)
                context_end = min(len(error_lines), i+3)
                context = '\n'.join(error_lines[context_start:context_end])
                if context not in warnings:
                    warnings.append(f"Node-related error context:\n{context}")
    
    if not warnings:
        print(f"\n{Colors.GREEN}✓ No warnings!{Colors.RESET}")
        return
    
    # Categorize warnings
    warning_types = {
        'Severe': [],
        'Warning': [],
        'Fatal': [],
        'Other': []
    }
    
    for warning in warnings:
        warning_lower = warning.lower()
        if '**  fatal  **' in warning_lower or 'fatal error' in warning_lower:
            warning_types['Fatal'].append(warning)
        elif '**  severe  **' in warning_lower or 'severe' in warning_lower:
            warning_types['Severe'].append(warning)
        elif '** warning **' in warning_lower or 'warning' in warning_lower:
            warning_types['Warning'].append(warning)
        else:
            warning_types['Other'].append(warning)
    
    # Print categorized warnings
    print(f"\n{Colors.BOLD}Warning Categories:{Colors.RESET}")
    print(f"  Fatal: {len(warning_types['Fatal'])}")
    print(f"  Severe: {len(warning_types['Severe'])}")
    print(f"  Warning: {len(warning_types['Warning'])}")
    print(f"  Other: {len(warning_types['Other'])}")
    
    # Show fatal errors
    if warning_types['Fatal']:
        print(f"\n{Colors.RED}{'='*70}{Colors.RESET}")
        print(f"{Colors.RED}{Colors.BOLD}FATAL ERRORS:{Colors.RESET}")
        print(f"{Colors.RED}{'='*70}{Colors.RESET}")
        for i, fatal in enumerate(warning_types['Fatal'][:10], 1):
            print(f"\n{i}. {fatal[:200]}")
    
    # Show severe errors
    if warning_types['Severe']:
        print(f"\n{Colors.YELLOW}{'='*70}{Colors.RESET}")
        print(f"{Colors.YELLOW}{Colors.BOLD}SEVERE ERRORS (showing first 10):{Colors.RESET}")
        print(f"{Colors.YELLOW}{'='*70}{Colors.RESET}")
        for i, severe in enumerate(warning_types['Severe'][:10], 1):
            print(f"\n{i}. {severe[:200]}")
    
    # Show common warning patterns
    print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}COMMON WARNING PATTERNS:{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}")
    
    # Count common patterns
    patterns = Counter()
    all_warnings_text = ' '.join(warnings).lower()
    
    common_patterns = [
        'zone volume',
        'air flow',
        'convergence',
        'sizing',
        'schedule',
        'construction',
        'material',
        'surface',
        'hvac',
        'coil',
        'fan',
        'thermostat',
        'daylighting',
        'output',
        'meter'
    ]
    
    for pattern in common_patterns:
        count = all_warnings_text.count(pattern)
        if count > 0:
            patterns[pattern] = count
    
    if patterns:
        for pattern, count in patterns.most_common(10):
            print(f"  {pattern}: {count} occurrences")
    else:
        print("  No common patterns found")
    
    # Show sample warnings
    if warning_types['Warning']:
        print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}SAMPLE WARNINGS (first 5):{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
        for i, warning in enumerate(warning_types['Warning'][:5], 1):
            print(f"\n{i}. {warning[:200]}")

def main():
    """Main test function"""
    print_header("IDF Creator → Simulation → Warning Analysis")
    
    # Test address
    test_address = "147 Sutter St, San Francisco, CA 94104"
    building_params = {
        "building_type": "Office",
        "stories": 3,
        "floor_area": 10000
    }
    
    print(f"{Colors.BOLD}Test Address: {test_address}{Colors.RESET}")
    print(f"{Colors.BOLD}Building Parameters: {json.dumps(building_params, indent=2)}{Colors.RESET}\n")
    
    # Step 1: Generate IDF
    idf_content, idf_filename = generate_idf_from_api(test_address, building_params)
    if not idf_content:
        print(f"\n{Colors.RED}✗ Failed to generate IDF{Colors.RESET}")
        return
    
    # Step 2: Load weather file (optional - simulation can run without it)
    # Temporarily skip weather file to see IDF warnings
    print(f"\n{Colors.YELLOW}⚠ Running simulation WITHOUT weather file to analyze IDF warnings{Colors.RESET}")
    weather_b64 = None
    weather_filename = None
    
    # Step 3: Run simulation without weather file
    print(f"\n{Colors.YELLOW}Running simulation without weather file...{Colors.RESET}")
    simulate_url = f"{ENERGYPLUS_API_BASE}/simulate"
    payload = {
        'idf_content': idf_content,
        'idf_filename': idf_filename
    }
    try:
        response = requests.post(
            simulate_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=600
        )
        if response.status_code == 200:
            simulation_result = response.json()
        else:
            print(f"{Colors.RED}✗ Simulation failed: {response.status_code}{Colors.RESET}")
            return
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
        return
    if not simulation_result:
        print(f"\n{Colors.RED}✗ Failed to run simulation{Colors.RESET}")
        return
    
    # Step 4: Analyze warnings
    analyze_warnings(simulation_result)
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}SUMMARY{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"Status: {simulation_result.get('simulation_status', 'unknown')}")
    print(f"EnergyPlus Version: {simulation_result.get('energyplus_version', 'unknown')}")
    print(f"Warnings: {len(simulation_result.get('warnings', []))}")
    
    if simulation_result.get('energy_results'):
        print(f"\n{Colors.GREEN}Energy Results:{Colors.RESET}")
        for key, value in simulation_result.get('energy_results', {}).items():
            print(f"  {key}: {value}")
    
    print(f"\n{Colors.GREEN}✓ Test completed!{Colors.RESET}\n")

if __name__ == '__main__':
    main()

