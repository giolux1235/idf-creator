#!/usr/bin/env python3
"""
Test Status Checks with Real Building Simulations
Runs status checks and then tests simulations for buildings with addresses
that match available weather files.
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import json

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


def find_weather_files() -> Dict[str, str]:
    """Find available weather files and map them to cities"""
    weather_dir = Path('artifacts/desktop_files/weather')
    weather_files = {}
    
    # Check for nested structure
    nested_dir = weather_dir / 'artifacts' / 'desktop_files' / 'weather'
    
    # Known weather file patterns
    patterns = {
        'Chicago': [
            'Chicago.epw',
            'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'
        ],
        'New York': [
            'USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw'
        ],
        'San Francisco': [
            'USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw'
        ]
    }
    
    for city, filenames in patterns.items():
        for filename in filenames:
            # Check main weather directory
            file_path = weather_dir / filename
            if file_path.exists():
                weather_files[city] = str(file_path)
                break
            
            # Check nested directory
            nested_path = nested_dir / filename
            if nested_path.exists():
                weather_files[city] = str(nested_path)
                break
    
    return weather_files


def get_test_buildings(weather_files: Dict[str, str]) -> List[Dict]:
    """Get test buildings that match available weather files"""
    buildings = []
    
    # Chicago buildings
    if 'Chicago' in weather_files:
        buildings.append({
            'name': 'Test Office Chicago',
            'address': '233 S Wacker Dr, Chicago, IL 60606',
            'city': 'Chicago',
            'weather_file': weather_files['Chicago'],
            'params': {
                'building_type': 'Office',
                'stories': 5,
                'floor_area_per_story_m2': 2000
            }
        })
    
    # New York buildings
    if 'New York' in weather_files:
        buildings.append({
            'name': 'Test Office NYC',
            'address': '350 5th Ave, New York, NY 10118',
            'city': 'New York',
            'weather_file': weather_files['New York'],
            'params': {
                'building_type': 'Office',
                'stories': 5,
                'floor_area_per_story_m2': 2000
            }
        })
    
    # San Francisco buildings
    if 'San Francisco' in weather_files:
        buildings.append({
            'name': 'Test Office SF',
            'address': '600 Montgomery St, San Francisco, CA 94111',
            'city': 'San Francisco',
            'weather_file': weather_files['San Francisco'],
            'params': {
                'building_type': 'Office',
                'stories': 5,
                'floor_area_per_story_m2': 2000
            }
        })
    
    return buildings


def run_status_check() -> Dict:
    """Run the comprehensive status check"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'STEP 1: Running Status Checks'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    try:
        # Import and run status checker
        from test_status import StatusChecker
        
        checker = StatusChecker()
        results = checker.run_all_checks(check_api=False)  # Skip API check
        
        return results
    except Exception as e:
        print(f"{Colors.RED}Error running status check: {e}{Colors.RESET}")
        return {'error': str(e)}


def generate_idf(building: Dict) -> Optional[str]:
    """Generate IDF file for a building"""
    print(f"\n{Colors.BOLD}Generating IDF for: {building['name']}{Colors.RESET}")
    print(f"Address: {building['address']}")
    
    try:
        creator = IDFCreator(enhanced=True, professional=True)
        
        output_dir = Path('test_outputs') / 'status_test'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_filename = f"status_test_{building['name'].lower().replace(' ', '_')}.idf"
        output_path = output_dir / output_filename
        
        idf_path = creator.create_idf(
            address=building['address'],
            user_params=building['params'],
            output_path=str(output_path)
        )
        
        print(f"{Colors.GREEN}✓ IDF generated: {idf_path}{Colors.RESET}")
        return idf_path
        
    except Exception as e:
        print(f"{Colors.RED}✗ Error generating IDF: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return None


def find_energyplus() -> Optional[str]:
    """Find EnergyPlus executable"""
    # Common locations
    possible_paths = [
        'energyplus',
        '/usr/local/bin/energyplus',
        '/opt/EnergyPlus/energyplus',
        '/Applications/EnergyPlus-9-6-0/energyplus',
    ]
    
    for path in possible_paths:
        try:
            result = subprocess.run(
                [path, '--version'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    return None


def run_simulation(idf_path: str, weather_file: str) -> Dict:
    """Run EnergyPlus simulation"""
    print(f"\n{Colors.BOLD}Running EnergyPlus simulation...{Colors.RESET}")
    
    energyplus = find_energyplus()
    if not energyplus:
        return {
            'success': False,
            'error': 'EnergyPlus not found',
            'message': 'EnergyPlus executable not available - skipping simulation'
        }
    
    print(f"Using EnergyPlus: {energyplus}")
    print(f"IDF file: {idf_path}")
    print(f"Weather file: {weather_file}")
    
    # Create output directory
    output_dir = Path('test_outputs') / 'status_test' / 'simulations' / Path(idf_path).stem
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Run EnergyPlus
        cmd = [
            energyplus,
            '-w', weather_file,
            '-d', str(output_dir),
            idf_path
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Check for output files - EnergyPlus generates multiple file types
        csv_files = list(output_dir.glob('*.csv'))
        sql_files = list(output_dir.glob('*.sql'))
        err_files = list(output_dir.glob('*.err'))
        eso_files = list(output_dir.glob('*.eso'))
        
        # Check error file for completion status
        simulation_completed = False
        errors = []
        warnings = []
        fatal_errors = []
        
        if err_files:
            with open(err_files[0], 'r') as f:
                content = f.read()
                # Check if simulation completed
                if 'EnergyPlus Completed Successfully' in content:
                    simulation_completed = True
                elif 'EnergyPlus Terminated' in content:
                    simulation_completed = False
                
                # Parse errors and warnings
                for line in content.split('\n'):
                    if '** Fatal' in line or '** Severe' in line:
                        fatal_errors.append(line.strip())
                    elif '** Warning' in line:
                        warnings.append(line.strip())
        
        # Success criteria: simulation completed OR output files generated
        has_output = bool(csv_files or sql_files or eso_files)
        
        if simulation_completed or (has_output and not fatal_errors):
            return {
                'success': True,
                'completed': simulation_completed,
                'output_dir': str(output_dir),
                'csv_files': [str(f) for f in csv_files],
                'sql_files': [str(f) for f in sql_files],
                'eso_files': [str(f) for f in eso_files],
                'errors': errors,
                'warnings': warnings[:10],  # Limit warnings
                'fatal_errors': fatal_errors,
                'returncode': result.returncode
            }
        else:
            return {
                'success': False,
                'error': 'Simulation failed or incomplete',
                'fatal_errors': fatal_errors[:5],  # Show first 5 fatal errors
                'warnings': warnings[:5],
                'has_output_files': has_output,
                'stderr': result.stderr[:500] if result.stderr else 'No error output'
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Simulation timeout (exceeded 5 minutes)'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """Main test function"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'IDF Creator Status Test with Simulations'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    # Step 1: Run status checks
    status_results = run_status_check()
    
    # Step 2: Find weather files
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'STEP 2: Finding Weather Files'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    weather_files = find_weather_files()
    
    if not weather_files:
        print(f"{Colors.RED}✗ No weather files found!{Colors.RESET}")
        print("Please ensure weather files are in artifacts/desktop_files/weather/")
        return
    
    print(f"{Colors.GREEN}✓ Found {len(weather_files)} weather file(s):{Colors.RESET}")
    for city, file_path in weather_files.items():
        print(f"  • {city}: {file_path}")
    
    # Step 3: Get test buildings
    buildings = get_test_buildings(weather_files)
    
    if not buildings:
        print(f"{Colors.RED}✗ No test buildings configured!{Colors.RESET}")
        return
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'STEP 3: Testing Building Simulations'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    # Step 4: Generate IDFs and run simulations
    test_results = []
    
    for building in buildings:
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}Testing: {building['name']}{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
        
        # Generate IDF
        idf_path = generate_idf(building)
        if not idf_path:
            test_results.append({
                'building': building['name'],
                'idf_generated': False,
                'simulation': None
            })
            continue
        
        # Run simulation
        sim_result = run_simulation(idf_path, building['weather_file'])
        
        test_results.append({
            'building': building['name'],
            'address': building['address'],
            'idf_path': idf_path,
            'weather_file': building['weather_file'],
            'idf_generated': True,
            'simulation': sim_result
        })
        
        # Print simulation result
        if sim_result.get('success'):
            status = "completed successfully" if sim_result.get('completed') else "generated output files"
            print(f"{Colors.GREEN}✓ Simulation {status}{Colors.RESET}")
            if sim_result.get('sql_files'):
                print(f"  SQL output: {len(sim_result['sql_files'])} file(s)")
            if sim_result.get('csv_files'):
                print(f"  CSV output: {len(sim_result['csv_files'])} file(s)")
            if sim_result.get('warnings'):
                print(f"{Colors.YELLOW}  Warnings: {len(sim_result['warnings'])}{Colors.RESET}")
            if sim_result.get('fatal_errors'):
                print(f"{Colors.YELLOW}  Fatal errors (but output generated): {len(sim_result['fatal_errors'])}{Colors.RESET}")
        else:
            print(f"{Colors.RED}✗ Simulation failed: {sim_result.get('error', 'Unknown error')}{Colors.RESET}")
            if sim_result.get('fatal_errors'):
                print(f"{Colors.RED}  Fatal errors:{Colors.RESET}")
                for err in sim_result['fatal_errors'][:3]:
                    print(f"    • {err[:100]}...")
    
    # Step 5: Summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'TEST SUMMARY'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    idf_success = sum(1 for r in test_results if r.get('idf_generated'))
    sim_success = sum(1 for r in test_results if r.get('simulation', {}).get('success'))
    
    print(f"Status Check: {'✓' if status_results.get('overall', {}).get('status') == 'healthy' else '⚠'}")
    print(f"IDF Generation: {idf_success}/{len(test_results)} successful")
    print(f"Simulations: {sim_success}/{len(test_results)} successful")
    
    print(f"\n{Colors.BOLD}Detailed Results:{Colors.RESET}")
    for result in test_results:
        print(f"\n  {result['building']}:")
        print(f"    IDF Generated: {'✓' if result.get('idf_generated') else '✗'}")
        if result.get('simulation'):
            sim = result['simulation']
            if sim.get('success'):
                status = "Completed" if sim.get('completed') else "Output generated"
                print(f"    Simulation: ✓ {status}")
                if sim.get('sql_files'):
                    print(f"      SQL files: {len(sim['sql_files'])}")
                if sim.get('csv_files'):
                    print(f"      CSV files: {len(sim['csv_files'])}")
                if sim.get('warnings'):
                    print(f"      Warnings: {len(sim['warnings'])}")
            else:
                print(f"    Simulation: ✗ {sim.get('error', 'Failed')}")
                if sim.get('fatal_errors'):
                    print(f"      Fatal errors: {len(sim['fatal_errors'])}")
    
    # Save results
    output_file = Path('test_outputs') / 'status_test' / 'test_results.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    full_results = {
        'status_check': status_results,
        'weather_files': weather_files,
        'test_buildings': test_results,
        'summary': {
            'total_buildings': len(test_results),
            'idf_generated': idf_success,
            'simulations_successful': sim_success
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(full_results, f, indent=2, default=str)
    
    print(f"\n{Colors.BLUE}Full results saved to: {output_file}{Colors.RESET}")


if __name__ == '__main__':
    main()

