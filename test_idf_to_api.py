#!/usr/bin/env python3
"""
Test: Generate IDF from address and send to EnergyPlus API
"""

import sys
import os
import requests
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import IDFCreator

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def generate_idf(address: str, params: dict = None) -> str:
    """Generate IDF file from address"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'STEP 1: Generating IDF File'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    print(f"{Colors.BOLD}Address: {address}{Colors.RESET}")
    
    try:
        creator = IDFCreator(enhanced=True, professional=True)
        
        output_dir = Path('test_outputs') / 'api_test'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_filename = f"api_test_{address.replace(' ', '_').replace(',', '_')[:50]}.idf"
        output_path = output_dir / output_filename
        
        idf_path = creator.create_idf(
            address=address,
            user_params=params or {},
            output_path=str(output_path)
        )
        
        print(f"\n{Colors.GREEN}✓ IDF file generated: {idf_path}{Colors.RESET}")
        return idf_path
        
    except Exception as e:
        print(f"{Colors.RED}✗ Error generating IDF: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return None


def send_to_energyplus_api(idf_path: str, api_url: str = None) -> dict:
    """Send IDF file to EnergyPlus API"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'STEP 2: Sending to EnergyPlus API'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    # Try to find API URL from environment or use default
    if not api_url:
        api_url = os.getenv('ENERGYPLUS_API_URL', 'https://web-production-1d1be.up.railway.app/simulate')
    
    print(f"{Colors.BOLD}API URL: {api_url}{Colors.RESET}")
    print(f"{Colors.BOLD}IDF File: {idf_path}{Colors.RESET}")
    
    if not Path(idf_path).exists():
        return {
            'success': False,
            'error': f'IDF file not found: {idf_path}'
        }
    
    try:
        # Read IDF file
        with open(idf_path, 'r') as f:
            idf_content = f.read()
        
        print(f"{Colors.BLUE}Reading IDF file... ({len(idf_content)} characters){Colors.RESET}")
        
        # Try to find weather file
        weather_file_path = None
        weather_content_b64 = None
        weather_dir = Path('artifacts/desktop_files/weather')
        weather_files = list(weather_dir.glob('*.epw'))
        if weather_files:
            weather_file_path = weather_files[0]
            print(f"{Colors.BLUE}Found weather file: {weather_file_path}{Colors.RESET}")
            import base64
            with open(weather_file_path, 'rb') as f:
                weather_content_b64 = base64.b64encode(f.read()).decode('utf-8')
        
        # API expects JSON format with idf_content
        print(f"{Colors.BLUE}Preparing JSON request...{Colors.RESET}")
        
        # Fix version in IDF content if needed (API expects 25.1)
        if 'Version,' in idf_content:
            # Update version to match API expectations
            import re
            idf_content = re.sub(
                r'Version,\s*\n\s*[0-9.]+;',
                'Version,\n  25.1;',
                idf_content,
                count=1
            )
            print(f"{Colors.YELLOW}Updated IDF version to 25.1 for API compatibility{Colors.RESET}")
        
        json_payload = {
            'idf_content': idf_content,
            'idf_filename': Path(idf_path).name
        }
        
        if weather_content_b64:
            json_payload['weather_content'] = weather_content_b64
            json_payload['weather_filename'] = weather_file_path.name
            print(f"{Colors.BLUE}Including weather file: {weather_file_path.name}{Colors.RESET}")
        
        print(f"{Colors.BLUE}Sending JSON request to API...{Colors.RESET}")
        
        # Send JSON request (this is the correct format)
        response = requests.post(
            api_url,
            json=json_payload,
            headers={'Content-Type': 'application/json'},
            timeout=600  # 10 minute timeout
        )
        
        print(f"{Colors.BLUE}Response status: {response.status_code}{Colors.RESET}")
        print(f"{Colors.BLUE}Response headers: {dict(response.headers)}{Colors.RESET}")
        
        # Print response content preview
        response_text = response.text[:1000] if response.text else ''
        print(f"{Colors.BLUE}Response preview (first 1000 chars):{Colors.RESET}")
        print(f"{Colors.BLUE}{response_text}{Colors.RESET}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"{Colors.GREEN}✓ API request successful{Colors.RESET}")
                
                # Check if simulation actually succeeded
                if result.get('simulation_status') == 'error':
                    print(f"{Colors.RED}⚠ API returned error status{Colors.RESET}")
                    print(f"{Colors.RED}  Error: {result.get('error_message', 'Unknown error')}{Colors.RESET}")
                    
                    # Print warnings if available
                    if result.get('warnings'):
                        print(f"{Colors.YELLOW}  Warnings ({len(result['warnings'])}):{Colors.RESET}")
                        for warning in result.get('warnings', [])[:5]:
                            print(f"    • {warning[:150]}")
                    
                    # Print energy results if available (even if status is error)
                    if result.get('energy_results'):
                        print(f"{Colors.GREEN}  Energy Results Available:{Colors.RESET}")
                        print(f"    {json.dumps(result.get('energy_results'), indent=4)}")
                    
                    return {
                        'success': result.get('real_simulation', False) and result.get('energy_results') is not None,
                        'status_code': response.status_code,
                        'result': result,
                        'error': result.get('error_message', 'Simulation error'),
                        'simulation_status': result.get('simulation_status'),
                        'warnings': result.get('warnings', []),
                        'energy_results': result.get('energy_results')
                    }
                else:
                    return {
                        'success': True,
                        'status_code': response.status_code,
                        'result': result,
                        'simulation_status': result.get('simulation_status', 'unknown')
                    }
            except json.JSONDecodeError as e:
                # Might be a file download or HTML
                print(f"{Colors.YELLOW}⚠ Response is not JSON{Colors.RESET}")
                print(f"{Colors.YELLOW}  Content-Type: {response.headers.get('Content-Type')}{Colors.RESET}")
                print(f"{Colors.YELLOW}  Content length: {len(response.content)} bytes{Colors.RESET}")
                print(f"{Colors.YELLOW}  JSON decode error: {e}{Colors.RESET}")
                
                # Save response for inspection
                debug_file = Path('test_outputs') / 'api_test' / 'api_response_debug.txt'
                debug_file.parent.mkdir(parents=True, exist_ok=True)
                with open(debug_file, 'w') as f:
                    f.write(f"Status: {response.status_code}\n")
                    f.write(f"Headers: {dict(response.headers)}\n")
                    f.write(f"Content:\n{response.text}\n")
                print(f"{Colors.BLUE}  Full response saved to: {debug_file}{Colors.RESET}")
                
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'content_type': response.headers.get('Content-Type'),
                    'content_length': len(response.content),
                    'debug_file': str(debug_file)
                }
        else:
            error_text = response.text[:500] if response.text else 'No error message'
            print(f"{Colors.RED}✗ API request failed: {response.status_code}{Colors.RESET}")
            print(f"{Colors.RED}  Error: {error_text}{Colors.RESET}")
            return {
                'success': False,
                'status_code': response.status_code,
                'error': error_text
            }
            
    except requests.exceptions.ConnectionError:
        print(f"{Colors.YELLOW}⚠ Could not connect to API{Colors.RESET}")
        print(f"{Colors.YELLOW}  URL: {api_url}{Colors.RESET}")
        print(f"{Colors.YELLOW}  This might be a local EnergyPlus installation instead{Colors.RESET}")
        return {
            'success': False,
            'error': 'Could not connect to API',
            'suggestion': 'API might not be available. Use local EnergyPlus installation instead.'
        }
    except requests.exceptions.Timeout:
        print(f"{Colors.RED}✗ API request timeout{Colors.RESET}")
        return {
            'success': False,
            'error': 'Request timeout (exceeded 10 minutes)'
        }
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def run_local_simulation(idf_path: str) -> dict:
    """Run EnergyPlus simulation locally as fallback"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'STEP 2 (Fallback): Running Local EnergyPlus'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    import subprocess
    
    # Find EnergyPlus
    energyplus_path = None
    for path in ['energyplus', '/usr/local/bin/energyplus', '/opt/EnergyPlus/energyplus']:
        try:
            result = subprocess.run([path, '--version'], capture_output=True, timeout=5)
            if result.returncode == 0:
                energyplus_path = path
                break
        except:
            continue
    
    if not energyplus_path:
        return {
            'success': False,
            'error': 'EnergyPlus not found locally',
            'suggestion': 'Install EnergyPlus or use API endpoint'
        }
    
    print(f"{Colors.BLUE}Using EnergyPlus: {energyplus_path}{Colors.RESET}")
    
    # Find weather file
    weather_dir = Path('artifacts/desktop_files/weather')
    weather_files = list(weather_dir.glob('*.epw'))
    weather_file = weather_files[0] if weather_files else None
    
    if not weather_file:
        return {
            'success': False,
            'error': 'No weather file found'
        }
    
    print(f"{Colors.BLUE}Using weather file: {weather_file}{Colors.RESET}")
    
    # Create output directory
    output_dir = Path('test_outputs') / 'api_test' / 'simulation'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        cmd = [
            energyplus_path,
            '-w', str(weather_file),
            '-d', str(output_dir),
            str(Path(idf_path).absolute())
        ]
        
        print(f"{Colors.BLUE}Running: {' '.join(cmd)}{Colors.RESET}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes
        )
        
        # Check for output files
        sql_files = list(output_dir.glob('*.sql'))
        err_files = list(output_dir.glob('*.err'))
        
        if err_files:
            with open(err_files[0], 'r') as f:
                content = f.read()
                if 'EnergyPlus Completed Successfully' in content:
                    print(f"{Colors.GREEN}✓ Simulation completed successfully{Colors.RESET}")
                    return {
                        'success': True,
                        'output_dir': str(output_dir),
                        'sql_files': [str(f) for f in sql_files],
                        'method': 'local_energyplus'
                    }
        
        print(f"{Colors.YELLOW}⚠ Simulation completed with issues{Colors.RESET}")
        return {
            'success': False,
            'error': 'Simulation had errors',
            'output_dir': str(output_dir),
            'returncode': result.returncode
        }
        
    except Exception as e:
        print(f"{Colors.RED}✗ Error running simulation: {e}{Colors.RESET}")
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate IDF from address and send to EnergyPlus API'
    )
    parser.add_argument(
        'address',
        type=str,
        help='Building address (e.g., "233 S Wacker Dr, Chicago, IL 60606")'
    )
    parser.add_argument(
        '--api-url',
        type=str,
        help='EnergyPlus API URL (default: https://web-production-1d1be.up.railway.app/simulate)'
    )
    parser.add_argument(
        '--stories',
        type=int,
        help='Number of stories'
    )
    parser.add_argument(
        '--floor-area',
        type=float,
        help='Floor area per story (m²)'
    )
    parser.add_argument(
        '--building-type',
        type=str,
        default='Office',
        help='Building type'
    )
    parser.add_argument(
        '--local-only',
        action='store_true',
        help='Skip API and use local EnergyPlus only'
    )
    
    args = parser.parse_args()
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'IDF to EnergyPlus API Test'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    # Prepare parameters
    params = {
        'building_type': args.building_type
    }
    if args.stories:
        params['stories'] = args.stories
    if args.floor_area:
        params['floor_area_per_story_m2'] = args.floor_area
    
    # Step 1: Generate IDF
    idf_path = generate_idf(args.address, params)
    if not idf_path:
        print(f"\n{Colors.RED}Failed to generate IDF file{Colors.RESET}")
        return
    
    # Step 2: Send to API or run locally
    if args.local_only:
        result = run_local_simulation(idf_path)
    else:
        result = send_to_energyplus_api(idf_path, args.api_url)
        
        # Fallback to local if API fails
        if not result.get('success') and 'Could not connect' in result.get('error', ''):
            print(f"\n{Colors.YELLOW}Attempting local simulation as fallback...{Colors.RESET}")
            result = run_local_simulation(idf_path)
    
    # Summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'TEST SUMMARY'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    print(f"IDF Generation: {Colors.GREEN}✓ Success{Colors.RESET}")
    print(f"IDF File: {idf_path}")
    
    if result.get('success'):
        print(f"Simulation: {Colors.GREEN}✓ Success{Colors.RESET}")
        if result.get('output_dir'):
            print(f"Output Directory: {result['output_dir']}")
        if result.get('sql_files'):
            print(f"SQL Files: {len(result['sql_files'])}")
    else:
        print(f"Simulation: {Colors.RED}✗ Failed{Colors.RESET}")
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    # Save results
    output_file = Path('test_outputs') / 'api_test' / 'api_test_results.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    test_results = {
        'address': args.address,
        'idf_path': idf_path,
        'idf_generated': True,
        'simulation': result
    }
    
    with open(output_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    
    print(f"\n{Colors.BLUE}Results saved to: {output_file}{Colors.RESET}")


if __name__ == '__main__':
    main()

