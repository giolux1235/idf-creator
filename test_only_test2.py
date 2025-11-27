#!/usr/bin/env python3
"""Run only Test 2 for debugging - simplified version"""
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from main import IDFCreator
from tests.test_pdf_benchmark import EnergyPlusSimulator

# Load test data - handle both dict and list formats
test_file = Path('artifacts/leed_benchmark_tests/benchmark_tests_combined_validated.json')
with open(test_file) as f:
    data = json.load(f)

# Handle both formats: {'tests': [...]} or direct list
if isinstance(data, dict) and 'tests' in data:
    tests = data['tests']
elif isinstance(data, list):
    tests = data
else:
    tests = []

# Find Test 2 - it should be index 1 (second test, 0-indexed)
test2 = tests[1] if len(tests) > 1 else None

if not test2:
    print("❌ Test 2 not found!")
    print(f"Available tests: {len(tests)}")
    sys.exit(1)

print("=" * 70)
name = test2.get('building_name') or test2.get('pdf_filename') or test2.get('client_reference_name', 'Test 2')
print(f"TEST 2: {name}")
print("=" * 70)
print(f"  Building Type: {test2.get('building_type')}")
print(f"  Address: {test2.get('address')}")
print(f"  Area: {test2.get('area_m2')} m² ({test2.get('area_sqft')} sqft)")
print(f"  Stories: {test2.get('floors')}")
print()

# Prepare building params
# CRITICAL: Convert area_m2 to floor_area or floor_area_per_story_m2
area_m2 = test2.get('area_m2')
stories = test2.get('floors') or 1

building_params = {
    'building_type': test2.get('building_type'),
    'address': test2.get('address'),
    'stories': stories,
    'year_built': test2.get('year_built'),
    'leed_level': test2.get('leed_level'),
}

# CRITICAL: Set floor_area_per_story_m2 if area_m2 is provided
# This ensures the exact area is used instead of defaulting to 500 m²
if area_m2:
    building_params['floor_area_per_story_m2'] = area_m2 / stories  # Area per floor
    building_params['floor_area'] = area_m2  # Total area
    building_params['force_area'] = True  # CRITICAL: Prevent OSM from overriding
    building_params['floor_area_source'] = 'user'  # Mark as user-specified
    print(f"  ✓ Using specified area: {area_m2:.1f} m² ({area_m2 / stories:.1f} m²/floor × {stories} floors)")

if test2.get('hvac_details'):
    building_params['hvac_system_info'] = test2.get('hvac_details')

# Create output directory
output_dir = Path('artifacts/leed_benchmark_5_tests/test_2')
output_dir.mkdir(parents=True, exist_ok=True)

# Generate IDF
print("[1/4] Generating IDF...")
idf_creator = IDFCreator(enhanced=True, professional=True)

try:
    idf_path_str = idf_creator.create_idf(
        address=building_params.get('address', ''),
        user_params=building_params,
        output_path=str(output_dir / 'building.idf')
    )
    
    if not idf_path_str or not Path(idf_path_str).exists():
        print("  ❌ Failed to generate IDF file")
        sys.exit(1)
    
    idf_path = Path(idf_path_str)
    print(f"  ✓ IDF generated: {idf_path}")
    print(f"  ✓ IDF size: {idf_path.stat().st_size / 1024:.1f} KB")
    
except Exception as e:
    print(f"  ❌ Error generating IDF: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Find weather file
weather_file = test2.get('weather_file')
weather_path = None

if weather_file:
    search_roots = [
        Path('/Applications'),
        Path('/usr/local'),
        Path('artifacts/desktop_files/weather'),
    ]
    
    for root in search_roots:
        if not root.exists():
            continue
        for ep_dir in root.glob('EnergyPlus*'):
            weather_dirs = [
                ep_dir / 'WeatherData',
                ep_dir / 'EnergyPlus installation files' / 'WeatherData',
            ]
            for wd in weather_dirs:
                if wd.exists():
                    candidate = wd / weather_file
                    if candidate.exists():
                        weather_path = str(candidate)
                        break
            if weather_path:
                break
        if weather_path:
            break
        
        # Also try direct search
        for epw_file in root.rglob('*.epw'):
            if epw_file.name == weather_file or 'New.York' in str(epw_file) or 'LaGuardia' in str(epw_file):
                weather_path = str(epw_file)
                break
        if weather_path:
            break

if not weather_path or not Path(weather_path).exists():
    print(f"  ❌ Weather file not found: {weather_file}")
    sys.exit(1)

print(f"  ✓ Weather file: {weather_path}")

# Run simulation
print("\n[2/4] Running EnergyPlus simulation...")
simulator = EnergyPlusSimulator()
result = simulator.run_simulation(str(idf_path), weather_path, str(output_dir / 'simulation'))

if result.get('success'):
    print("  ✅ Simulation completed successfully!")
    print("\n[3/4] Extracting energy results...")
    energy_results = simulator.extract_energy_results(result['output_dir'])
    if energy_results:
        total_energy = energy_results.get('total_site_energy_kwh', 'N/A')
        eui = energy_results.get('eui_kbtu_per_sqft', 'N/A')
        if isinstance(total_energy, (int, float)):
            print(f"  Total Site Energy: {total_energy:,.0f} kWh")
        else:
            print(f"  Total Site Energy: {total_energy}")
        if isinstance(eui, (int, float)):
            print(f"  EUI: {eui:.1f} kBtu/sqft")
        else:
            print(f"  EUI: {eui} kBtu/sqft")
        print("\n🎉✅✅✅ TEST 2 PASSING! ✅✅✅🎉")
    else:
        print("  ❌ Could not extract energy results")
else:
    rc = result.get('returncode', 'N/A')
    print(f"  ❌ Simulation failed (return code: {rc})")
    
    if rc == -11:
        print("\n  ❌❌❌ SEGMENTATION FAULT DETECTED ❌❌❌")
        err_file = result['output_dir'] / 'eplusout.err'
        if err_file.exists():
            with open(err_file) as f:
                err_content = f.read()
            if err_content.strip():
                print(f"\n  Error file content (last 500 chars):")
                print(err_content[-500:])
            else:
                print("\n  Error file is empty (segfault before EnergyPlus could write errors)")
                print("  This suggests a fundamental configuration issue.")
        
    if result.get('stderr'):
        print(f"\n  STDERR: {result['stderr'][:500]}")
