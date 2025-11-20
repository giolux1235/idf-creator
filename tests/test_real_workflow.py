#!/usr/bin/env python3
"""
Real End-to-End Test: Address → Generate IDF → Simulate → Results
Tests the complete workflow with real production APIs
"""

import requests
import json
import time
import base64
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

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")

def print_step(step_num, description):
    print(f"\n{Colors.BOLD}{Colors.BLUE}[Step {step_num}] {description}{Colors.RESET}")
    print(f"{Colors.BLUE}{'-'*70}{Colors.RESET}")

def test_real_workflow():
    """Test complete real workflow"""
    print_header("Real End-to-End Workflow Test")
    
    # Real building address
    test_address = "233 S Wacker Dr, Chicago, IL 60606"
    building_params = {
        "building_type": "Office",
        "stories": 5,
        "floor_area": 50000
    }
    
    print(f"{Colors.BOLD}Test Address: {test_address}{Colors.RESET}")
    print(f"{Colors.BOLD}Building Type: {building_params['building_type']}{Colors.RESET}")
    print(f"{Colors.BOLD}Stories: {building_params['stories']}{Colors.RESET}")
    print(f"{Colors.BOLD}Floor Area: {building_params['floor_area']:,} sq ft{Colors.RESET}\n")
    
    try:
        # ==========================================
        # Step 1: Generate IDF from Address
        # ==========================================
        print_step(1, "Generating IDF File from Address")
        
        generate_url = f"{IDF_API_BASE}/api/generate"
        generate_payload = {
            "address": test_address,
            **building_params
        }
        
        print(f"Sending request to: {generate_url}")
        print(f"Payload: {json.dumps(generate_payload, indent=2)}")
        
        start_time = time.time()
        generate_response = requests.post(
            generate_url,
            json=generate_payload,
            headers={'Content-Type': 'application/json'},
            timeout=120
        )
        generate_time = time.time() - start_time
        
        print(f"\nResponse Status: {generate_response.status_code}")
        print(f"Time: {generate_time:.2f} seconds")
        
        if generate_response.status_code != 200:
            print(f"{Colors.RED}✗ IDF generation failed{Colors.RESET}")
            print(f"Response: {generate_response.text[:500]}")
            return False
        
        generate_data = generate_response.json()
        
        if not generate_data.get('success'):
            print(f"{Colors.RED}✗ IDF generation returned error{Colors.RESET}")
            print(f"Error: {generate_data.get('error', 'Unknown error')}")
            return False
        
        filename = generate_data.get('filename')
        download_url = generate_data.get('download_url')
        
        if not filename or not download_url:
            print(f"{Colors.RED}✗ Missing filename or download_url{Colors.RESET}")
            return False
        
        print(f"{Colors.GREEN}✓ IDF generated successfully{Colors.RESET}")
        print(f"  Filename: {filename}")
        print(f"  Download URL: {download_url}")
        
        if generate_data.get('parameters_used'):
            print(f"\n  Parameters Used:")
            for key, value in generate_data.get('parameters_used', {}).items():
                print(f"    {key}: {value}")
        
        # ==========================================
        # Step 2: Download IDF File
        # ==========================================
        print_step(2, "Downloading IDF File")
        
        if download_url.startswith('/'):
            download_url = f"{IDF_API_BASE}{download_url}"
        
        print(f"Downloading from: {download_url}")
        
        start_time = time.time()
        idf_response = requests.get(download_url, timeout=60)
        download_time = time.time() - start_time
        
        print(f"Response Status: {idf_response.status_code}")
        print(f"Time: {download_time:.2f} seconds")
        
        if idf_response.status_code != 200:
            print(f"{Colors.RED}✗ Failed to download IDF{Colors.RESET}")
            return False
        
        idf_content = idf_response.text
        idf_size = len(idf_content)
        
        print(f"{Colors.GREEN}✓ IDF downloaded successfully{Colors.RESET}")
        print(f"  Size: {idf_size:,} characters ({idf_size / 1024 / 1024:.2f} MB)")
        
        # Show first few lines of IDF
        idf_lines = idf_content.split('\n')[:10]
        print(f"\n  IDF Preview (first 10 lines):")
        for i, line in enumerate(idf_lines, 1):
            print(f"    {i:2d}: {line[:80]}")
        
        # ==========================================
        # Step 3: Load Weather File
        # ==========================================
        print_step(3, "Loading Weather File")
        
        # Find Chicago weather file
        weather_dir = Path('artifacts/desktop_files/weather')
        weather_files = list(weather_dir.glob('*Chicago*.epw'))
        
        if not weather_files:
            # Try alternative location
            weather_files = list(weather_dir.glob('*.epw'))
        
        # Also check nested directories
        if not weather_files:
            weather_files = list(weather_dir.rglob('*Chicago*.epw'))
        if not weather_files:
            weather_files = list(weather_dir.rglob('*.epw'))
        
        weather_content_b64 = None
        weather_filename = None
        
        if weather_files:
            weather_file_path = weather_files[0]
            print(f"Found weather file: {weather_file_path.name}")
            
            with open(weather_file_path, 'rb') as f:
                weather_bytes = f.read()
                weather_content_b64 = base64.b64encode(weather_bytes).decode('utf-8')
                weather_filename = weather_file_path.name
            
            print(f"{Colors.GREEN}✓ Weather file loaded ({len(weather_bytes):,} bytes){Colors.RESET}")
            print(f"  Filename: {weather_filename}")
        else:
            print(f"{Colors.YELLOW}⚠ No weather file found, simulation will use default weather{Colors.RESET}")
        
        # ==========================================
        # Step 4: Run EnergyPlus Simulation
        # ==========================================
        print_step(4, "Running EnergyPlus Simulation")
        
        simulate_url = f"{IDF_API_BASE}/simulate"
        simulate_payload = {
            'idf_content': idf_content,
            'idf_filename': filename
        }
        
        # Add weather file if available
        if weather_content_b64:
            simulate_payload['weather_content'] = weather_content_b64
            simulate_payload['weather_filename'] = weather_filename
            print(f"Including weather file: {weather_filename}")
        
        print(f"Sending request to: {simulate_url}")
        print(f"IDF Filename: {filename}")
        print(f"IDF Size: {idf_size:,} characters")
        if weather_content_b64:
            print(f"Weather File: {weather_filename} ({len(base64.b64decode(weather_content_b64)):,} bytes)")
        print(f"\n{Colors.YELLOW}Note: Since main API not yet updated, calling external API directly{Colors.RESET}")
        print(f"External API: {ENERGYPLUS_API_BASE}/simulate")
        print(f"\n{Colors.YELLOW}This may take several minutes...{Colors.RESET}\n")
        
        # Call external API directly since main API hasn't been deployed yet
        start_time = time.time()
        simulate_response = requests.post(
            f"{ENERGYPLUS_API_BASE}/simulate",  # Call external API directly
            json=simulate_payload,
            headers={'Content-Type': 'application/json'},
            timeout=600  # 10 minutes
        )
        simulation_time = time.time() - start_time
        
        print(f"Response Status: {simulate_response.status_code}")
        print(f"Time: {simulation_time:.2f} seconds ({simulation_time / 60:.2f} minutes)")
        
        if simulate_response.status_code != 200:
            print(f"{Colors.RED}✗ Simulation request failed{Colors.RESET}")
            print(f"Response: {simulate_response.text[:500]}")
            return False
        
        simulate_data = simulate_response.json()
        simulation_status = simulate_data.get('simulation_status', 'unknown')
        
        print(f"\n{Colors.BOLD}Simulation Details:{Colors.RESET}")
        print(f"  Status: {simulation_status}")
        print(f"  EnergyPlus Version: {simulate_data.get('energyplus_version', 'N/A')}")
        print(f"  Real Simulation: {simulate_data.get('real_simulation', False)}")
        
        if simulate_data.get('used_external_api'):
            print(f"  {Colors.CYAN}✓ Used External API: {simulate_data.get('external_api_url')}{Colors.RESET}")
        
        # Show diagnostics if available
        diagnostics = simulate_data.get('diagnostics', {})
        if diagnostics:
            print(f"\n{Colors.BOLD}Diagnostics:{Colors.RESET}")
            for key, value in diagnostics.items():
                if key != 'external_debug_info':
                    print(f"  {key}: {value}")
        
        # ==========================================
        # Step 5: Display Results
        # ==========================================
        print_step(5, "Simulation Results")
        
        if simulation_status == 'success':
            print(f"{Colors.GREEN}✓ Simulation completed successfully!{Colors.RESET}\n")
            
            # Energy Results
            energy_results = simulate_data.get('energy_results', {})
            if energy_results:
                print(f"{Colors.BOLD}{Colors.GREEN}Energy Results:{Colors.RESET}")
                print(f"{Colors.GREEN}{'='*70}{Colors.RESET}")
                
                # Format and display energy results
                if 'total_site_energy_kwh' in energy_results:
                    energy_kwh = energy_results['total_site_energy_kwh']
                    print(f"  Total Site Energy:      {energy_kwh:,.2f} kWh")
                    
                    if 'building_area_m2' in energy_results:
                        area_m2 = energy_results['building_area_m2']
                        area_ft2 = area_m2 * 10.764  # Convert to sq ft
                        print(f"  Building Area:          {area_m2:,.2f} m² ({area_ft2:,.2f} sq ft)")
                        
                        if 'eui_kwh_m2' in energy_results:
                            eui = energy_results['eui_kwh_m2']
                            eui_btu = eui * 3.412  # Convert to kBtu/sqft
                            print(f"  Energy Use Intensity:  {eui:.2f} kWh/m² ({eui_btu:.2f} kBtu/sqft)")
                    
                    if 'total_site_energy_gj' in energy_results:
                        print(f"  Total Site Energy:      {energy_results['total_site_energy_gj']:.2f} GJ")
                
                # Display all other results
                for key, value in energy_results.items():
                    if key not in ['total_site_energy_kwh', 'total_site_energy_gj', 
                                  'building_area_m2', 'eui_kwh_m2']:
                        if isinstance(value, (int, float)):
                            print(f"  {key:25s}: {value:,.2f}")
                        else:
                            print(f"  {key:25s}: {value}")
                
                print(f"{Colors.GREEN}{'='*70}{Colors.RESET}\n")
            else:
                print(f"{Colors.YELLOW}⚠ No energy results in response{Colors.RESET}\n")
            
            # Warnings
            warnings = simulate_data.get('warnings', [])
            if warnings:
                print(f"{Colors.YELLOW}Warnings ({len(warnings)}):{Colors.RESET}")
                for i, warning in enumerate(warnings[:10], 1):  # Show first 10
                    print(f"  {i:2d}. {warning[:150]}")
                if len(warnings) > 10:
                    print(f"  ... and {len(warnings) - 10} more warnings")
                print()
            
            return True
            
        else:
            print(f"{Colors.RED}✗ Simulation failed{Colors.RESET}\n")
            
            error_message = simulate_data.get('error_message', 'Unknown error')
            print(f"{Colors.RED}Error:{Colors.RESET}")
            print(f"  {error_message[:500]}\n")
            
            # Show warnings if any
            warnings = simulate_data.get('warnings', [])
            if warnings:
                print(f"\n{Colors.YELLOW}⚠ Warnings ({len(warnings)}):{Colors.RESET}")
                
                # Categorize warnings
                fatal_errors = [w for w in warnings if '** Fatal' in w or 'Fatal' in w]
                severe_errors = [w for w in warnings if '** Severe' in w and w not in fatal_errors]
                other_warnings = [w for w in warnings if w not in fatal_errors and w not in severe_errors]
                
                if fatal_errors:
                    print(f"\n  {Colors.RED}Fatal Errors ({len(fatal_errors)}):{Colors.RESET}")
                    for i, warning in enumerate(fatal_errors[:5], 1):
                        print(f"    {i}. {warning[:250]}")
                    if len(fatal_errors) > 5:
                        print(f"    ... and {len(fatal_errors) - 5} more fatal errors")
                
                if severe_errors:
                    print(f"\n  {Colors.YELLOW}Severe Errors ({len(severe_errors)}):{Colors.RESET}")
                    for i, warning in enumerate(severe_errors[:10], 1):
                        print(f"    {i:2d}. {warning[:200]}")
                    if len(severe_errors) > 10:
                        print(f"    ... and {len(severe_errors) - 10} more severe errors")
                
                if other_warnings:
                    print(f"\n  {Colors.YELLOW}Other Warnings ({len(other_warnings)}):{Colors.RESET}")
                    for i, warning in enumerate(other_warnings[:5], 1):
                        print(f"    {i}. {warning[:200]}")
                    if len(other_warnings) > 5:
                        print(f"    ... and {len(other_warnings) - 5} more warnings")
                
                print()
            
            # Show output files if available
            output_files = simulate_data.get('output_files', [])
            if output_files:
                print(f"\n{Colors.YELLOW}Output Files Generated:{Colors.RESET}")
                for file_info in output_files:
                    name = file_info.get('name', 'unknown')
                    size = file_info.get('size', 0)
                    size_kb = size / 1024
                    status = f"{Colors.GREEN}✓{Colors.RESET}" if size > 0 else f"{Colors.RED}✗{Colors.RESET}"
                    print(f"  {status} {name:30s}: {size:>10,} bytes ({size_kb:>7.2f} KB)")
                
                # Check for key files
                csv_file = next((f for f in output_files if 'csv' in f.get('name', '').lower()), None)
                sql_file = next((f for f in output_files if 'sql' in f.get('name', '').lower() and 'sqlite.err' not in f.get('name', '')), None)
                err_file = next((f for f in output_files if 'err' in f.get('name', '').lower() and 'sqlite' not in f.get('name', '')), None)
                
                print(f"\n{Colors.BOLD}Key Files Analysis:{Colors.RESET}")
                if csv_file:
                    print(f"  CSV File: {Colors.GREEN}✓ Found{Colors.RESET} ({csv_file.get('size', 0):,} bytes)")
                else:
                    print(f"  CSV File: {Colors.RED}✗ Missing{Colors.RESET} (eplustbl.csv not found)")
                
                if sql_file:
                    print(f"  SQLite File: {Colors.GREEN}✓ Found{Colors.RESET} ({sql_file.get('size', 0):,} bytes)")
                else:
                    print(f"  SQLite File: {Colors.RED}✗ Missing{Colors.RESET}")
                
                if err_file:
                    err_size = err_file.get('size', 0)
                    if err_size > 0:
                        print(f"  Error File: {Colors.GREEN}✓ Found{Colors.RESET} ({err_size:,} bytes)")
                    else:
                        print(f"  Error File: {Colors.YELLOW}⚠ Empty{Colors.RESET} (0 bytes - unusual)")
                else:
                    print(f"  Error File: {Colors.RED}✗ Missing{Colors.RESET}")
            
            # Show error file content if available
            error_file_content = simulate_data.get('error_file_content', '')
            if error_file_content:
                print(f"\n{Colors.YELLOW}Error File Content:{Colors.RESET}")
                print(f"{Colors.BLUE}{'-'*70}{Colors.RESET}")
                # Show first 1000 characters
                print(error_file_content[:1000])
                if len(error_file_content) > 1000:
                    print(f"\n  ... ({len(error_file_content) - 1000} more characters)")
                print(f"{Colors.BLUE}{'-'*70}{Colors.RESET}\n")
            elif output_files:
                err_file = next((f for f in output_files if 'err' in f.get('name', '').lower() and 'sqlite' not in f.get('name', '')), None)
                if err_file and err_file.get('size', 0) == 0:
                    print(f"\n{Colors.YELLOW}⚠ Error file is empty (0 bytes) - this is unusual{Colors.RESET}")
                    print(f"  This suggests EnergyPlus may not have run properly\n")
            
            # Show debug info if available
            debug_info = simulate_data.get('debug_info', {})
            if debug_info:
                print(f"{Colors.YELLOW}Debug Information:{Colors.RESET}")
                for key, value in debug_info.items():
                    if isinstance(value, dict):
                        print(f"  {key}:")
                        for k, v in value.items():
                            print(f"    {k}: {v}")
                    else:
                        print(f"  {key}: {value}")
                print()
            
            # Show full error message if available
            if error_message and len(error_message) > 500:
                print(f"{Colors.YELLOW}Full Error Message:{Colors.RESET}")
                print(f"  {error_message}\n")
            
            return False
            
    except requests.exceptions.Timeout:
        print(f"{Colors.RED}✗ Request timed out{Colors.RESET}")
        return False
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'Real End-to-End Workflow Test'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"\n{Colors.BOLD}IDF Generator API: {IDF_API_BASE}{Colors.RESET}")
    print(f"{Colors.BOLD}EnergyPlus API:     {ENERGYPLUS_API_BASE}{Colors.RESET}\n")
    
    success = test_real_workflow()
    
    # Final Summary
    print_header("Test Summary")
    
    if success:
        print(f"{Colors.GREEN}✓ Full workflow completed successfully!{Colors.RESET}\n")
        print(f"{Colors.GREEN}The complete pipeline is working:{Colors.RESET}")
        print(f"  1. ✓ Address → IDF Generation")
        print(f"  2. ✓ IDF Download")
        print(f"  3. ✓ EnergyPlus Simulation (via external API)")
        print(f"  4. ✓ Results Returned\n")
        return 0
    else:
        print(f"{Colors.RED}✗ Workflow failed{Colors.RESET}\n")
        print(f"{Colors.YELLOW}Check the errors above for details{Colors.RESET}\n")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())

