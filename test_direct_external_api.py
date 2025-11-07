#!/usr/bin/env python3
"""
Test direct connection to external EnergyPlus API
This bypasses the main API and tests the external API directly
"""

import requests
import json
import time

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

def test_direct_external_api():
    """Test external EnergyPlus API directly"""
    print_header("Direct External EnergyPlus API Test")
    
    print(f"{Colors.BOLD}Step 1: Downloading IDF from main API{Colors.RESET}")
    print(f"{Colors.BLUE}{'-'*70}{Colors.RESET}")
    
    # Download IDF
    download_url = f"{IDF_API_BASE}/download/Office_api.idf"
    print(f"Downloading: {download_url}")
    
    idf_response = requests.get(download_url, timeout=60)
    
    if idf_response.status_code != 200:
        print(f"{Colors.RED}✗ Failed to download IDF{Colors.RESET}")
        return False
    
    idf_content = idf_response.text
    print(f"{Colors.GREEN}✓ IDF downloaded ({len(idf_content):,} characters){Colors.RESET}\n")
    
    print(f"{Colors.BOLD}Step 2: Sending to External EnergyPlus API{Colors.RESET}")
    print(f"{Colors.BLUE}{'-'*70}{Colors.RESET}")
    
    # Send directly to external API
    external_url = f"{ENERGYPLUS_API_BASE}/simulate"
    payload = {
        'idf_content': idf_content,
        'idf_filename': 'Office_api.idf'
    }
    
    print(f"Sending to: {external_url}")
    print(f"IDF Size: {len(idf_content):,} characters")
    print(f"\n{Colors.YELLOW}This may take several minutes...{Colors.RESET}\n")
    
    start_time = time.time()
    response = requests.post(
        external_url,
        json=payload,
        headers={'Content-Type': 'application/json'},
        timeout=600  # 10 minutes
    )
    elapsed = time.time() - start_time
    
    print(f"Response Status: {response.status_code}")
    print(f"Time: {elapsed:.2f} seconds ({elapsed / 60:.2f} minutes)\n")
    
    if response.status_code != 200:
        print(f"{Colors.RED}✗ Request failed{Colors.RESET}")
        print(f"Response: {response.text[:500]}")
        return False
    
    data = response.json()
    status = data.get('simulation_status', 'unknown')
    
    print(f"{Colors.BOLD}Simulation Status: {status}{Colors.RESET}")
    print(f"EnergyPlus Version: {data.get('energyplus_version', 'N/A')}")
    print(f"Real Simulation: {data.get('real_simulation', False)}\n")
    
    if status == 'success':
        print(f"{Colors.GREEN}✓ Simulation completed successfully!{Colors.RESET}\n")
        
        energy_results = data.get('energy_results', {})
        if energy_results:
            print(f"{Colors.BOLD}{Colors.GREEN}Energy Results:{Colors.RESET}")
            print(f"{Colors.GREEN}{'='*70}{Colors.RESET}")
            
            if 'total_site_energy_kwh' in energy_results:
                energy_kwh = energy_results['total_site_energy_kwh']
                print(f"  Total Site Energy:      {energy_kwh:,.2f} kWh")
                
                if 'building_area_m2' in energy_results:
                    area_m2 = energy_results['building_area_m2']
                    area_ft2 = area_m2 * 10.764
                    print(f"  Building Area:          {area_m2:,.2f} m² ({area_ft2:,.2f} sq ft)")
                    
                    if 'eui_kwh_m2' in energy_results:
                        eui = energy_results['eui_kwh_m2']
                        eui_btu = eui * 3.412
                        print(f"  Energy Use Intensity:  {eui:.2f} kWh/m² ({eui_btu:.2f} kBtu/sqft)")
            
            for key, value in energy_results.items():
                if key not in ['total_site_energy_kwh', 'total_site_energy_gj', 
                              'building_area_m2', 'eui_kwh_m2']:
                    if isinstance(value, (int, float)):
                        print(f"  {key:25s}: {value:,.2f}")
                    else:
                        print(f"  {key:25s}: {value}")
            
            print(f"{Colors.GREEN}{'='*70}{Colors.RESET}\n")
        
        warnings = data.get('warnings', [])
        if warnings:
            print(f"{Colors.YELLOW}Warnings ({len(warnings)}):{Colors.RESET}")
            for i, warning in enumerate(warnings[:5], 1):
                print(f"  {i}. {warning[:150]}")
            if len(warnings) > 5:
                print(f"  ... and {len(warnings) - 5} more\n")
        
        return True
    else:
        print(f"{Colors.RED}✗ Simulation failed{Colors.RESET}\n")
        error = data.get('error_message', 'Unknown error')
        print(f"{Colors.RED}Error:{Colors.RESET}")
        print(f"  {error[:500]}\n")
        
        warnings = data.get('warnings', [])
        if warnings:
            print(f"{Colors.YELLOW}Warnings ({len(warnings)}):{Colors.RESET}")
            for i, warning in enumerate(warnings[:3], 1):
                print(f"  {i}. {warning[:150]}")
            print()
        
        return False

if __name__ == '__main__':
    import sys
    success = test_direct_external_api()
    
    print_header("Test Summary")
    if success:
        print(f"{Colors.GREEN}✓ External EnergyPlus API is working!{Colors.RESET}\n")
        print(f"{Colors.YELLOW}Note: Once the main API is updated and deployed,{Colors.RESET}")
        print(f"{Colors.YELLOW}      the full workflow will work automatically.{Colors.RESET}\n")
        sys.exit(0)
    else:
        print(f"{Colors.RED}✗ External API test failed{Colors.RESET}\n")
        sys.exit(1)










