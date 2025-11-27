#!/usr/bin/env python3
"""
Test script to run 5 LEED benchmark tests.
Loads validated test data, generates IDFs, runs simulations, and compares results.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from main import IDFCreator
from tests.test_pdf_benchmark import EnergyPlusSimulator, BenchmarkComparator


def load_test_data(json_path: str) -> List[Dict]:
    """Load test data from JSON file"""
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Handle both formats: {'tests': [...]} or direct list
    if 'tests' in data:
        return data['tests']
    return data if isinstance(data, list) else []


def run_test(test_number: int, test_data: Dict, output_base_dir: Path) -> Dict:
    """Run a single benchmark test"""
    print(f"\n{'='*80}")
    print(f"TEST {test_number}: {test_data.get('building_name', test_data.get('pdf_filename', 'Unknown'))[:60]}")
    print('='*80)
    
    # Create test-specific output directory
    test_dir = output_base_dir / f"test_{test_number}"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    result = {
        'test_number': test_number,
        'test_data': test_data,
        'success': False,
        'errors': [],
        'idf_path': None,
        'simulation_result': None,
        'energy_results': None,
        'comparison': None
    }
    
    try:
        # Extract building parameters
        area_m2 = test_data.get('area_m2')
        stories = test_data.get('floors') or test_data.get('stories', 1)
        
        building_params = {
            'address': test_data.get('address', ''),
            'building_type': test_data.get('building_type', 'office'),
            'year_built': test_data.get('year_built'),
            'stories': stories,
        }
        
        # CRITICAL: Convert area_m2 to floor_area_per_story_m2 and floor_area
        # This ensures the exact area is used instead of defaulting to OSM/500 m²
        if area_m2:
            building_params['floor_area_per_story_m2'] = area_m2 / stories  # Area per floor
            building_params['floor_area'] = area_m2  # Total area
            building_params['force_area'] = True  # Prevent OSM from overriding
            building_params['floor_area_source'] = 'user'  # Mark as user-specified
        
        # Remove None values
        building_params = {k: v for k, v in building_params.items() if v is not None}
        
        # Handle residential buildings - force PTAC if window AC detected
        hvac_system_types = test_data.get('hvac_details', {}).get('hvac_system_types', [])
        if building_params['building_type'].lower() == 'residential':
            hvac_types_str = ' '.join(str(h) for h in hvac_system_types).lower()
            if 'window air conditioner' in hvac_types_str or 'split system' in hvac_types_str:
                building_params['force_hvac_type'] = 'PTAC'
                print(f"  ℹ️  Residential building with window AC/split system → forcing PTAC")
        
        # Get HVAC system info if available
        hvac_system_info = test_data.get('hvac_system_info')
        if hvac_system_info:
            building_params['hvac_system_info'] = hvac_system_info
        
        print(f"  Building Type: {building_params['building_type']}")
        print(f"  Address: {building_params.get('address', 'N/A')}")
        if 'floor_area_m2' in building_params:
            print(f"  Area: {building_params['floor_area_m2']:.1f} m² ({building_params.get('floor_area_sqft', 0):,.0f} sqft)")
        if 'stories' in building_params:
            print(f"  Stories: {building_params['stories']}")
        
        # Step 1: Generate IDF
        print(f"\n[1/4] Generating IDF...")
        idf_creator = IDFCreator(enhanced=True, professional=True)
        
        # Use create_idf which returns the path to the IDF file
        idf_path_str = idf_creator.create_idf(
            address=building_params.get('address', ''),
            user_params=building_params,
            output_path=str(test_dir / 'building.idf')
        )
        
        if not idf_path_str or not Path(idf_path_str).exists():
            raise ValueError("Failed to generate IDF file")
        
        idf_path = Path(idf_path_str)
        result['idf_path'] = str(idf_path)
        print(f"  ✓ IDF generated: {idf_path}")
        
        # Step 2: Get weather file
        weather_file = test_data.get('weather_file')
        if not weather_file:
            raise ValueError("No weather file specified in test data")
        
        # Find weather file path - comprehensive search
        weather_path = None
        
        # Search in multiple locations
        search_roots = [
            Path('/Applications'),
            Path('/usr/local'),
            Path.home(),
            Path('artifacts/desktop_files/weather'),
            Path('artifacts/weather'),
        ]
        
        # Look for EnergyPlus installations
        for root in search_roots:
            if not root.exists():
                continue
            
            # Try different EnergyPlus directory patterns
            for ep_dir in root.glob('EnergyPlus*'):
                weather_dirs = [
                    ep_dir / 'WeatherData',
                    ep_dir / 'EnergyPlus installation files' / 'WeatherData',
                    ep_dir / 'weather',
                ]
                for wd in weather_dirs:
                    if wd.exists():
                        candidate = wd / weather_file
                        if candidate.exists():
                            weather_path = str(candidate)
                            break
                if weather_path:
                    break
            
            # Also check directly in weather subdirectories
            for weather_dir in [root / 'weather', root / 'WeatherData']:
                if weather_dir.exists():
                    candidate = weather_dir / weather_file
                    if candidate.exists():
                        weather_path = str(candidate)
                        break
            
            if weather_path:
                break
        
        # Also try searching by filename pattern
        if not weather_path:
            weather_filename = weather_file
            for root in search_roots:
                if not root.exists():
                    continue
                for epw_file in root.rglob('*.epw'):
                    if epw_file.name == weather_filename:
                        weather_path = str(epw_file)
                        break
                if weather_path:
                    break
        
        if not weather_path or not Path(weather_path).exists():
            raise ValueError(f"Weather file not found: {weather_file}\nSearched in: {[str(r) for r in search_roots]}")
        
        print(f"  ✓ Weather file: {weather_path}")
        
        # Step 3: Run simulation
        print(f"\n[2/4] Running EnergyPlus simulation...")
        simulator = EnergyPlusSimulator()
        
        if not simulator.energyplus_path:
            raise ValueError("EnergyPlus not found. Please install EnergyPlus.")
        
        sim_output_dir = test_dir / 'simulation'
        sim_result = simulator.run_simulation(
            idf_path=str(idf_path),
            output_dir=str(sim_output_dir),
            weather_file=weather_path
        )
        
        result['simulation_result'] = sim_result
        
        if 'error' in sim_result:
            raise ValueError(f"Simulation error: {sim_result['error']}")
        
        if not sim_result.get('success'):
            # Check error file
            err_file = sim_output_dir / 'eplusout.err'
            if err_file.exists():
                with open(err_file, 'r') as f:
                    err_content = f.read()
                    # Extract severe/fatal errors
                    errors = [line for line in err_content.split('\n') 
                            if '** Severe' in line or '** Fatal' in line or '** Error' in line]
                    if errors:
                        error_msg = errors[0][:200]
                        raise ValueError(f"Simulation failed: {error_msg}")
            raise ValueError(f"Simulation failed: Unknown error")
        
        print(f"  ✓ Simulation completed successfully")
        
        # Step 4: Extract energy results
        print(f"\n[3/4] Extracting energy results...")
        energy_results = simulator.extract_energy_results(str(sim_output_dir))
        
        if not energy_results or 'error' in energy_results:
            raise ValueError(f"Failed to extract energy results: {energy_results.get('error', 'Unknown')}")
        
        result['energy_results'] = energy_results
        
        if 'total_site_energy_kwh' in energy_results:
            print(f"  Total Site Energy: {energy_results['total_site_energy_kwh']:,.0f} kWh")
        if 'eui_kbtu_sqft' in energy_results:
            print(f"  EUI: {energy_results['eui_kbtu_sqft']:.1f} kBtu/sqft")
        
        # Step 5: Compare with target data
        print(f"\n[4/4] Comparing with target data...")
        
        comparison = {}
        
        # Compare EUI
        target_eui = test_data.get('eui_kbtu_sqft') or test_data.get('site_eui_kbtu_sqft')
        sim_eui = energy_results.get('eui_kbtu_sqft')
        
        if target_eui and sim_eui:
            eui_error = ((sim_eui - target_eui) / target_eui) * 100
            comparison['eui_error_percent'] = eui_error
            comparison['target_eui_kbtu_sqft'] = target_eui
            comparison['simulated_eui_kbtu_sqft'] = sim_eui
            print(f"  Target EUI: {target_eui:.1f} kBtu/sqft")
            print(f"  Simulated EUI: {sim_eui:.1f} kBtu/sqft")
            print(f"  Error: {eui_error:+.1f}%")
        
        # Compare total energy
        target_energy = test_data.get('annual_electric_kwh')
        sim_energy = energy_results.get('total_site_energy_kwh')
        
        if target_energy and sim_energy:
            energy_error = ((sim_energy - target_energy) / target_energy) * 100
            comparison['total_error_percent'] = energy_error
            comparison['target_energy_kwh'] = target_energy
            comparison['simulated_energy_kwh'] = sim_energy
            print(f"  Target Energy: {target_energy:,.0f} kWh")
            print(f"  Simulated Energy: {sim_energy:,.0f} kWh")
            print(f"  Error: {energy_error:+.1f}%")
        
        result['comparison'] = comparison
        result['success'] = True
        
        # Determine status
        max_error = max(
            abs(comparison.get('eui_error_percent', 0)),
            abs(comparison.get('total_error_percent', 0))
        )
        
        if max_error < 10:
            status = "EXCELLENT"
        elif max_error < 30:
            status = "GOOD"
        else:
            status = "NEEDS IMPROVEMENT"
        
        print(f"\n  ✓ Test {test_number} completed: {status}")
        
    except Exception as e:
        error_msg = str(e)
        result['errors'].append(error_msg)
        print(f"\n  ❌ Test {test_number} failed: {error_msg}")
        import traceback
        traceback.print_exc()
    
    return result


def main():
    """Main function to run all 5 benchmark tests"""
    print("="*80)
    print("LEED BENCHMARK TESTS - 5 Tests")
    print("="*80)
    
    # Load test data
    test_data_path = Path('artifacts/leed_benchmark_tests/benchmark_tests_combined_validated.json')
    
    if not test_data_path.exists():
        # Try alternative path
        test_data_path = Path('artifacts/leed_benchmark_tests/benchmark_tests_combined.json')
    
    if not test_data_path.exists():
        print(f"❌ Test data file not found: {test_data_path}")
        print("   Please ensure benchmark test data has been extracted.")
        return 1
    
    print(f"\nLoading test data from: {test_data_path}")
    tests = load_test_data(str(test_data_path))
    
    if not tests:
        print("❌ No test data loaded")
        return 1
    
    print(f"✓ Loaded {len(tests)} test(s)")
    
    # Create output directory
    output_dir = Path('artifacts/leed_benchmark_5_tests')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run each test
    results = []
    for i, test_data in enumerate(tests, start=1):
        result = run_test(i, test_data, output_dir)
        results.append(result)
    
    # Generate summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print(f"\n✅ Passing: {successful}/{len(results)}")
    print(f"❌ Failing: {failed}/{len(results)}")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        test_name = result['test_data'].get('building_name', result['test_data'].get('pdf_filename', 'Unknown'))[:40]
        print(f"\n{status} Test {result['test_number']}: {test_name}")
        
        if result['success'] and result.get('comparison'):
            comp = result['comparison']
            if 'eui_error_percent' in comp:
                print(f"   EUI Error: {comp['eui_error_percent']:+.1f}%")
            if 'total_error_percent' in comp:
                print(f"   Energy Error: {comp['total_error_percent']:+.1f}%")
        elif not result['success']:
            if result['errors']:
                print(f"   Error: {result['errors'][0][:80]}")
    
    # Save summary to JSON
    summary = {
        'total_tests': len(results),
        'successful': successful,
        'failed': failed,
        'results': results
    }
    
    summary_path = output_dir / 'summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n✓ Summary saved to: {summary_path}")
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
