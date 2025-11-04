#!/usr/bin/env python3
"""
Comprehensive API Test for Railway deployment
Tests all endpoints at web-production-3092c.up.railway.app
"""

import requests
import json
import base64
from pathlib import Path

API_BASE = "https://web-production-3092c.up.railway.app"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def test_health():
    """Test /api/health endpoint"""
    print_header("TEST 1: Health Check Endpoint")
    url = f"{API_BASE}/api/health"
    print(f"URL: {url}\n")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"{Colors.GREEN}✓ Health endpoint working{Colors.RESET}")
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"{Colors.RED}✗ Health endpoint failed: {response.status_code}{Colors.RESET}")
            return False
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
        return False

def test_generate_endpoint():
    """Test /api/generate endpoint"""
    print_header("TEST 2: IDF Generation Endpoint")
    url = f"{API_BASE}/api/generate"
    print(f"URL: {url}\n")
    
    payload = {
        "address": "233 S Wacker Dr, Chicago, IL 60606",
        "building_type": "Office",
        "stories": 5,
        "floor_area": 50000
    }
    
    print(f"Request payload: {json.dumps(payload, indent=2)}\n")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}\n")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get('success'):
                    print(f"{Colors.GREEN}✓ IDF generation successful{Colors.RESET}")
                    print(f"Filename: {data.get('filename', 'N/A')}")
                    print(f"Download URL: {data.get('download_url', 'N/A')}")
                    return True
                else:
                    print(f"{Colors.YELLOW}⚠ Generation returned error{Colors.RESET}")
                    print(f"Error: {data.get('error', 'Unknown error')}")
                    return False
            except json.JSONDecodeError:
                print(f"{Colors.YELLOW}⚠ Non-JSON response{Colors.RESET}")
                print(f"Response: {response.text[:500]}")
                return False
        else:
            print(f"{Colors.RED}✗ Request failed: {response.status_code}{Colors.RESET}")
            print(f"Response: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
        return False

def test_simulate_endpoint():
    """Test /simulate endpoint with minimal IDF"""
    print_header("TEST 3: EnergyPlus Simulation Endpoint")
    url = f"{API_BASE}/simulate"
    print(f"URL: {url}\n")
    
    minimal_idf = """Version,
  25.1;

Building,
  Test Building,
  0.0,
  City,
  0.04,
  0.4,
  FullExterior,
  25,
  6;

SimulationControl,
  No,
  No,
  No,
  No,
  Yes;

RunPeriod,
  Test Run,
  1, 1, 1, 1, 1,
  Yes, Yes, No, Yes, Yes;

Timestep, 6;

Site:Location,
  Test Location,
  40.0, -74.0, -5.0, 10.0;
"""
    
    payload = {
        'idf_content': minimal_idf,
        'idf_filename': 'test_minimal.idf'
    }
    
    print(f"Sending minimal IDF ({len(minimal_idf)} characters)...\n")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}\n")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"{Colors.GREEN}✓ Simulate endpoint responding{Colors.RESET}")
                print(f"Simulation Status: {data.get('simulation_status', 'unknown')}")
                
                if data.get('error_message'):
                    print(f"{Colors.YELLOW}⚠ Error: {data.get('error_message')[:200]}{Colors.RESET}")
                
                if data.get('energy_results'):
                    print(f"{Colors.GREEN}✓ Energy results available{Colors.RESET}")
                    print(f"Results: {json.dumps(data.get('energy_results'), indent=2)[:300]}")
                
                if data.get('warnings'):
                    print(f"Warnings: {len(data.get('warnings', []))}")
                
                return True
            except json.JSONDecodeError:
                print(f"{Colors.YELLOW}⚠ Non-JSON response{Colors.RESET}")
                print(f"Response: {response.text[:500]}")
                return False
        else:
            print(f"{Colors.RED}✗ Request failed: {response.status_code}{Colors.RESET}")
            print(f"Response: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
        return False

def test_root_endpoint():
    """Test root endpoint"""
    print_header("TEST 4: Root Endpoint")
    url = f"{API_BASE}/"
    print(f"URL: {url}\n")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        
        if response.status_code == 200:
            print(f"{Colors.GREEN}✓ Root endpoint responding{Colors.RESET}")
            if 'html' in response.headers.get('Content-Type', '').lower():
                print(f"Response appears to be HTML (web interface)")
            return True
        else:
            print(f"{Colors.YELLOW}⚠ Root endpoint returned {response.status_code}{Colors.RESET}")
            return False
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
        return False

def test_full_workflow():
    """Test complete workflow: Address → Generate IDF → Simulate → Results"""
    print_header("TEST 5: Full Workflow - Address to Production Results")
    
    test_address = "233 S Wacker Dr, Chicago, IL 60606"
    print(f"Test Address: {test_address}\n")
    
    try:
        # Step 1: Generate IDF from address
        print(f"{Colors.BOLD}Step 1: Generating IDF from address...{Colors.RESET}")
        generate_url = f"{API_BASE}/api/generate"
        generate_payload = {
            "address": test_address,
            "building_type": "Office",
            "stories": 5,
            "floor_area": 50000
        }
        
        generate_response = requests.post(
            generate_url,
            json=generate_payload,
            headers={'Content-Type': 'application/json'},
            timeout=120
        )
        
        if generate_response.status_code != 200:
            print(f"{Colors.RED}✗ IDF generation failed: {generate_response.status_code}{Colors.RESET}")
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
            print(f"{Colors.RED}✗ Missing filename or download_url in response{Colors.RESET}")
            return False
        
        print(f"{Colors.GREEN}✓ IDF generated: {filename}{Colors.RESET}")
        print(f"Download URL: {download_url}\n")
        
        # Step 2: Download IDF file
        print(f"{Colors.BOLD}Step 2: Downloading IDF file...{Colors.RESET}")
        if download_url.startswith('/'):
            download_url = f"{API_BASE}{download_url}"
        
        idf_response = requests.get(download_url, timeout=60)
        
        if idf_response.status_code != 200:
            print(f"{Colors.RED}✗ Failed to download IDF: {idf_response.status_code}{Colors.RESET}")
            return False
        
        idf_content = idf_response.text
        print(f"{Colors.GREEN}✓ IDF downloaded ({len(idf_content)} characters){Colors.RESET}\n")
        
        # Step 3: Simulate the IDF
        print(f"{Colors.BOLD}Step 3: Running EnergyPlus simulation...{Colors.RESET}")
        simulate_url = f"{API_BASE}/simulate"
        simulate_payload = {
            'idf_content': idf_content,
            'idf_filename': filename
        }
        
        simulate_response = requests.post(
            simulate_url,
            json=simulate_payload,
            headers={'Content-Type': 'application/json'},
            timeout=600  # 10 minutes for simulation
        )
        
        if simulate_response.status_code != 200:
            print(f"{Colors.RED}✗ Simulation request failed: {simulate_response.status_code}{Colors.RESET}")
            print(f"Response: {simulate_response.text[:500]}")
            return False
        
        simulate_data = simulate_response.json()
        simulation_status = simulate_data.get('simulation_status', 'unknown')
        
        print(f"Simulation Status: {simulation_status}")
        print(f"EnergyPlus Version: {simulate_data.get('energyplus_version', 'N/A')}")
        print(f"Real Simulation: {simulate_data.get('real_simulation', False)}\n")
        
        # Step 4: Display results
        if simulation_status == 'success':
            print(f"{Colors.GREEN}✓ Simulation completed successfully!{Colors.RESET}\n")
            
            energy_results = simulate_data.get('energy_results', {})
            if energy_results:
                print(f"{Colors.BOLD}Energy Results:{Colors.RESET}")
                print(f"{'='*70}")
                for key, value in energy_results.items():
                    if isinstance(value, (int, float)):
                        if 'energy' in key.lower() or 'eui' in key.lower():
                            print(f"  {key:30s}: {value:,.2f}")
                        else:
                            print(f"  {key:30s}: {value:,.2f}")
                    else:
                        print(f"  {key:30s}: {value}")
                print(f"{'='*70}\n")
            else:
                print(f"{Colors.YELLOW}⚠ No energy results in response{Colors.RESET}\n")
            
            warnings = simulate_data.get('warnings', [])
            if warnings:
                print(f"{Colors.YELLOW}Warnings ({len(warnings)}):{Colors.RESET}")
                for warning in warnings[:5]:  # Show first 5
                    print(f"  - {warning[:100]}")
                if len(warnings) > 5:
                    print(f"  ... and {len(warnings) - 5} more warnings")
                print()
            
            return True
        else:
            print(f"{Colors.RED}✗ Simulation failed{Colors.RESET}\n")
            error_message = simulate_data.get('error_message', 'Unknown error')
            print(f"Error: {error_message[:500]}\n")
            
            warnings = simulate_data.get('warnings', [])
            if warnings:
                print(f"{Colors.YELLOW}Warnings ({len(warnings)}):{Colors.RESET}")
                for warning in warnings[:3]:
                    print(f"  - {warning[:100]}")
                print()
            
            debug_info = simulate_data.get('debug_info', {})
            if debug_info:
                print(f"{Colors.YELLOW}Debug Info:{Colors.RESET}")
                for key, value in debug_info.items():
                    print(f"  {key}: {value}")
                print()
            
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
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'Comprehensive API Test for Railway'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"\nAPI Base URL: {API_BASE}\n")
    
    results = {}
    
    # Run all tests
    results['health'] = test_health()
    results['generate'] = test_generate_endpoint()
    results['simulate'] = test_simulate_endpoint()
    results['root'] = test_root_endpoint()
    results['full_workflow'] = test_full_workflow()
    
    # Summary
    print_header("TEST SUMMARY")
    
    print(f"Health Endpoint (/api/health):          {'✓ PASS' if results['health'] else '✗ FAIL'}")
    print(f"Generate Endpoint (/api/generate):      {'✓ PASS' if results['generate'] else '✗ FAIL'}")
    print(f"Simulate Endpoint (/simulate):          {'✓ PASS' if results['simulate'] else '✗ FAIL'}")
    print(f"Root Endpoint (/):                      {'✓ PASS' if results['root'] else '✗ FAIL'}")
    print(f"Full Workflow (Address → Results):      {'✓ PASS' if results['full_workflow'] else '✗ FAIL'}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}\n")
    
    if passed == total:
        print(f"{Colors.GREEN}✓ All API endpoints are working!{Colors.RESET}\n")
        return 0
    elif passed > 0:
        print(f"{Colors.YELLOW}⚠ Some endpoints have issues{Colors.RESET}\n")
        return 1
    else:
        print(f"{Colors.RED}✗ API is not responding correctly{Colors.RESET}\n")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
