#!/usr/bin/env python3
"""
Test script to verify EnergyPlus API connection
Tests the Railway API endpoint and shows available capabilities
"""

import sys
import requests
import json
from pathlib import Path

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def test_api_health(api_url: str) -> bool:
    """Test API health endpoint"""
    print(f"{Colors.BOLD}{Colors.BLUE}Testing API Health Endpoint...{Colors.RESET}")
    
    health_url = api_url.replace('/simulate', '/health')
    print(f"  URL: {health_url}")
    
    try:
        response = requests.get(health_url, timeout=5)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"{Colors.GREEN}✓ Health endpoint is available{Colors.RESET}")
            try:
                data = response.json()
                print(f"  Response: {json.dumps(data, indent=2)}")
            except:
                print(f"  Response: {response.text[:200]}")
            return True
        else:
            print(f"{Colors.YELLOW}⚠ Health endpoint returned {response.status_code}{Colors.RESET}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}✗ Cannot connect to health endpoint{Colors.RESET}")
        return False
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
        return False


def test_api_simulate(api_url: str) -> bool:
    """Test API simulate endpoint with minimal IDF"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Testing API Simulate Endpoint...{Colors.RESET}")
    print(f"  URL: {api_url}")
    
    # Minimal valid IDF
    minimal_idf = """Version,
  25.1;

Building,
  Test Building,
  0.0,                       !- North Axis {deg}
  City,                      !- Terrain
  0.0400,                    !- Loads Convergence Tolerance Value
  0.4000,                    !- Temperature Convergence Tolerance Value {deltaC}
  FullExterior,              !- Solar Distribution
  25,                        !- Maximum Number of Warmup Days
  6;                         !- Minimum Number of Warmup Days

SimulationControl,
  Yes,                       !- Do Zone Sizing Calculation
  Yes,                       !- Do System Sizing Calculation
  Yes,                       !- Do Plant Sizing Calculation
  Yes,                       !- Run Simulation for Sizing Periods
  No;                        !- Run Simulation for Weather File Run Periods

RunPeriod,
  Test Run Period,
  1,                         !- Begin Month
  1,                         !- Begin Day of Month
  1,                         !- End Month
  1,                         !- End Day of Month
  UseWeatherFile,            !- Day of Week for Start
  Yes,                       !- Use Weather File Holidays and Special Days
  Yes,                       !- Use Weather File Daylight Saving Period
  No,                        !- Apply Weekend Holiday Rule
  Yes,                       !- Use Weather File Rain Indicators
  Yes;                       !- Use Weather File Snow Indicators

Timestep,
  6;                         !- Number of Timesteps per Hour

Site:Location,
  Test Location,
  40.0,                      !- Latitude {deg}
  -74.0,                     !- Longitude {deg}
  -5.0,                      !- Time Zone {hr}
  10.0;                      !- Elevation {m}

"""
    
    payload = {
        'idf_content': minimal_idf,
        'idf_filename': 'test_minimal.idf'
    }
    
    print(f"  Sending minimal IDF ({len(minimal_idf)} characters)...")
    
    try:
        response = requests.post(
            api_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"  Status: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"{Colors.GREEN}✓ API simulate endpoint is working{Colors.RESET}")
                print(f"  Simulation Status: {result.get('simulation_status', 'unknown')}")
                
                if result.get('error_message'):
                    print(f"  Error: {result.get('error_message')[:200]}")
                
                if result.get('warnings'):
                    print(f"  Warnings: {len(result.get('warnings', []))}")
                
                if result.get('energy_results'):
                    print(f"  Energy Results: Available")
                    print(f"  {json.dumps(result.get('energy_results'), indent=4)[:500]}")
                
                return True
            except json.JSONDecodeError:
                print(f"{Colors.YELLOW}⚠ API returned non-JSON response{Colors.RESET}")
                print(f"  Response preview: {response.text[:500]}")
                return False
        else:
            print(f"{Colors.YELLOW}⚠ API returned status {response.status_code}{Colors.RESET}")
            print(f"  Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}✗ Cannot connect to API{Colors.RESET}")
        print(f"  Check if the Railway service is running")
        return False
    except requests.exceptions.Timeout:
        print(f"{Colors.RED}✗ API request timed out{Colors.RESET}")
        return False
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
        return False


def test_api_with_weather(api_url: str) -> bool:
    """Test API with actual weather file"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Testing API with Weather File...{Colors.RESET}")
    
    # Find a weather file
    weather_dir = Path('artifacts/desktop_files/weather')
    weather_files = list(weather_dir.glob('*.epw'))
    
    if not weather_files:
        print(f"{Colors.YELLOW}⚠ No weather files found in {weather_dir}{Colors.RESET}")
        print(f"   Skipping weather file test")
        return False
    
    weather_file = weather_files[0]
    print(f"  Using weather file: {weather_file.name}")
    
    # Use minimal IDF from previous test
    minimal_idf = """Version,
  25.1;

Building,
  Test Building,
  0.0,                       !- North Axis {deg}
  City,                      !- Terrain
  0.0400,                    !- Loads Convergence Tolerance Value
  0.4000,                    !- Temperature Convergence Tolerance Value {deltaC}
  FullExterior,              !- Solar Distribution
  25,                        !- Maximum Number of Warmup Days
  6;                         !- Minimum Number of Warmup Days

SimulationControl,
  Yes,                       !- Do Zone Sizing Calculation
  Yes,                       !- Do System Sizing Calculation
  Yes,                       !- Do Plant Sizing Calculation
  Yes,                       !- Run Simulation for Sizing Periods
  No;                        !- Run Simulation for Weather File Run Periods

RunPeriod,
  Test Run Period,
  1,                         !- Begin Month
  1,                         !- Begin Day of Month
  1,                         !- End Month
  1,                         !- End Day of Month
  UseWeatherFile,            !- Day of Week for Start
  Yes,                       !- Use Weather File Holidays and Special Days
  Yes,                       !- Use Weather File Daylight Saving Period
  No,                        !- Apply Weekend Holiday Rule
  Yes,                       !- Use Weather File Rain Indicators
  Yes;                       !- Use Weather File Snow Indicators

Timestep,
  6;                         !- Number of Timesteps per Hour

Site:Location,
  Test Location,
  40.0,                      !- Latitude {deg}
  -74.0,                     !- Longitude {deg}
  -5.0,                      !- Time Zone {hr}
  10.0;                      !- Elevation {m}

"""
    
    import base64
    with open(weather_file, 'rb') as f:
        weather_b64 = base64.b64encode(f.read()).decode('utf-8')
    
    payload = {
        'idf_content': minimal_idf,
        'idf_filename': 'test_with_weather.idf',
        'weather_content': weather_b64,
        'weather_filename': weather_file.name
    }
    
    print(f"  Sending request with weather file ({len(weather_b64)} bytes encoded)...")
    
    try:
        response = requests.post(
            api_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"{Colors.GREEN}✓ API simulation with weather file completed{Colors.RESET}")
                print(f"  Simulation Status: {result.get('simulation_status', 'unknown')}")
                
                if result.get('energy_results'):
                    print(f"  Energy Results: Available")
                    energy = result.get('energy_results', {})
                    if isinstance(energy, dict):
                        for key, value in list(energy.items())[:5]:
                            print(f"    {key}: {value}")
                
                return True
            except json.JSONDecodeError:
                print(f"{Colors.YELLOW}⚠ API returned non-JSON response{Colors.RESET}")
                return False
        else:
            print(f"{Colors.YELLOW}⚠ API returned status {response.status_code}{Colors.RESET}")
            return False
            
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
        return False


def main():
    """Main test function"""
    api_url = 'https://web-production-3092c.up.railway.app/simulate'
    
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'EnergyPlus API Connection Test'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    print(f"API URL: {api_url}\n")
    
    # Test 1: Health endpoint
    health_ok = test_api_health(api_url)
    
    # Test 2: Simulate endpoint (minimal)
    simulate_ok = test_api_simulate(api_url)
    
    # Test 3: Simulate with weather file
    weather_ok = test_api_with_weather(api_url)
    
    # Summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'TEST SUMMARY'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    print(f"Health Endpoint:     {'✓ PASS' if health_ok else '✗ FAIL'}")
    print(f"Simulate Endpoint:   {'✓ PASS' if simulate_ok else '✗ FAIL'}")
    print(f"Weather File Test:   {'✓ PASS' if weather_ok else '✗ FAIL'}")
    
    if health_ok or simulate_ok:
        print(f"\n{Colors.GREEN}✓ API is available and working{Colors.RESET}")
        print(f"   The auto-fix engine can use this API as fallback")
        return 0
    else:
        print(f"\n{Colors.RED}✗ API is not available{Colors.RESET}")
        print(f"   The auto-fix engine will only work with local EnergyPlus")
        return 1


if __name__ == '__main__':
    sys.exit(main())

