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
    
    # Summary
    print_header("TEST SUMMARY")
    
    print(f"Health Endpoint (/api/health):    {'✓ PASS' if results['health'] else '✗ FAIL'}")
    print(f"Generate Endpoint (/api/generate): {'✓ PASS' if results['generate'] else '✗ FAIL'}")
    print(f"Simulate Endpoint (/simulate):    {'✓ PASS' if results['simulate'] else '✗ FAIL'}")
    print(f"Root Endpoint (/):                {'✓ PASS' if results['root'] else '✗ FAIL'}")
    
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
