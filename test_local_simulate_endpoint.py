#!/usr/bin/env python3
"""
Local test for /simulate endpoint integration
Tests the logic without requiring external API connection
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import Flask app (handle optional CORS)
try:
    from web_interface import app
except ImportError as e:
    if 'flask_cors' in str(e):
        # Make CORS optional for testing
        import sys
        import importlib
        
        # Temporarily install a mock flask_cors
        class MockCORS:
            def __init__(self, app):
                pass
        
        sys.modules['flask_cors'] = type(sys)('flask_cors')
        sys.modules['flask_cors'].CORS = MockCORS
        
        # Now import
        from web_interface import app
    else:
        raise

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

def test_simulate_endpoint_logic():
    """Test the /simulate endpoint logic locally"""
    print_header("Local Test: Simulate Endpoint Logic")
    
    # Minimal valid IDF content
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
    
    with app.test_client() as client:
        # Test 1: Check that endpoint accepts requests
        print(f"{Colors.BOLD}Test 1: Endpoint accepts requests{Colors.RESET}")
        
        payload = {
            'idf_content': minimal_idf,
            'idf_filename': 'test.idf'
        }
        
        # Mock the subprocess.run to simulate EnergyPlus not found
        with patch('subprocess.run') as mock_subprocess:
            # Make subprocess.run raise an exception (simulating EnergyPlus not found)
            mock_subprocess.side_effect = FileNotFoundError()
            
            # Mock requests.post to simulate external API call
            with patch('requests.post') as mock_requests:
                # Simulate successful external API response
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'version': '33.0.0',
                    'simulation_status': 'success',
                    'energyplus_version': '25.1.0',
                    'real_simulation': True,
                    'energy_results': {
                        'total_site_energy_kwh': 50000,
                        'building_area_m2': 5000,
                        'eui_kwh_m2': 10.0
                    },
                    'warnings': []
                }
                mock_requests.return_value = mock_response
                
                # Make the request
                response = client.post(
                    '/simulate',
                    json=payload,
                    content_type='application/json'
                )
                
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"{Colors.GREEN}✓ Endpoint responds correctly{Colors.RESET}")
                    
                    # Check if external API was used
                    if data.get('used_external_api'):
                        print(f"{Colors.GREEN}✓ External API integration working{Colors.RESET}")
                        print(f"  External API URL: {data.get('external_api_url')}")
                    else:
                        print(f"{Colors.YELLOW}⚠ External API not used (local EnergyPlus found){Colors.RESET}")
                    
                    # Check simulation status
                    if data.get('simulation_status') == 'success':
                        print(f"{Colors.GREEN}✓ Simulation status: success{Colors.RESET}")
                        if data.get('energy_results'):
                            print(f"{Colors.GREEN}✓ Energy results included{Colors.RESET}")
                            for key, value in data.get('energy_results', {}).items():
                                print(f"  {key}: {value}")
                    else:
                        print(f"{Colors.YELLOW}⚠ Simulation status: {data.get('simulation_status')}{Colors.RESET}")
                        if data.get('error_message'):
                            print(f"  Error: {data.get('error_message')[:200]}")
                    
                    return True
                else:
                    print(f"{Colors.RED}✗ Unexpected status code: {response.status_code}{Colors.RESET}")
                    print(f"Response: {response.get_data(as_text=True)[:500]}")
                    return False

def test_error_handling():
    """Test error handling when external API fails"""
    print_header("Test 2: Error Handling")
    
    minimal_idf = """Version, 25.1;"""
    
    with app.test_client() as client:
        payload = {
            'idf_content': minimal_idf,
            'idf_filename': 'test.idf'
        }
        
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.side_effect = FileNotFoundError()
            
            # Mock requests.post to simulate external API failure
            with patch('requests.post') as mock_requests:
                import requests
                mock_requests.side_effect = requests.exceptions.ConnectionError("Connection failed")
                
                response = client.post(
                    '/simulate',
                    json=payload,
                    content_type='application/json'
                )
                
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.get_json()
                    if data.get('simulation_status') == 'error':
                        print(f"{Colors.GREEN}✓ Error handling works correctly{Colors.RESET}")
                        print(f"  Error message: {data.get('error_message', '')[:200]}")
                        return True
                    else:
                        print(f"{Colors.YELLOW}⚠ Unexpected status: {data.get('simulation_status')}{Colors.RESET}")
                        return False
                else:
                    print(f"{Colors.RED}✗ Unexpected status code: {response.status_code}{Colors.RESET}")
                    return False

def test_missing_idf_content():
    """Test handling of missing idf_content"""
    print_header("Test 3: Missing IDF Content")
    
    with app.test_client() as client:
        payload = {
            'idf_filename': 'test.idf'
            # Missing idf_content
        }
        
        response = client.post(
            '/simulate',
            json=payload,
            content_type='application/json'
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            if data.get('simulation_status') == 'error':
                error_msg = data.get('error_message', '')
                if 'Missing idf_content' in error_msg:
                    print(f"{Colors.GREEN}✓ Correctly handles missing idf_content{Colors.RESET}")
                    return True
                else:
                    print(f"{Colors.YELLOW}⚠ Unexpected error message{Colors.RESET}")
                    return False
            else:
                print(f"{Colors.YELLOW}⚠ Expected error status{Colors.RESET}")
                return False
        else:
            print(f"{Colors.RED}✗ Unexpected status code: {response.status_code}{Colors.RESET}")
            return False

def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'Local Test: Simulate Endpoint Integration'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    results = {}
    
    results['endpoint_logic'] = test_simulate_endpoint_logic()
    results['error_handling'] = test_error_handling()
    results['missing_idf'] = test_missing_idf_content()
    
    # Summary
    print_header("Test Summary")
    
    print(f"Endpoint Logic Test:        {'✓ PASS' if results['endpoint_logic'] else '✗ FAIL'}")
    print(f"Error Handling Test:        {'✓ PASS' if results['error_handling'] else '✗ FAIL'}")
    print(f"Missing IDF Content Test:   {'✓ PASS' if results['missing_idf'] else '✗ FAIL'}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}\n")
    
    if passed == total:
        print(f"{Colors.GREEN}✓ All local tests passed!{Colors.RESET}\n")
        print(f"{Colors.BLUE}Note: This tests the logic locally.{Colors.RESET}")
        print(f"{Colors.BLUE}For production, the external API integration will be used.{Colors.RESET}\n")
        return 0
    else:
        print(f"{Colors.YELLOW}⚠ Some tests failed{Colors.RESET}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())

