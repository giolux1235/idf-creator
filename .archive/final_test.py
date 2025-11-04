#!/usr/bin/env python3
"""Final comprehensive test after reversion"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from main import IDFCreator
from src.validation.simulation_validator import EnergyPlusSimulationValidator

print("="*80)
print("FINAL COMPREHENSIVE TEST")
print("="*80)

creator = IDFCreator(professional=True, enhanced=True)

# Use Chicago with known good weather
idf_file = creator.create_idf(
    address='123 Main St, Chicago, IL',
    user_params={
        'building_type': 'Office',
        'stories': 10,
        'year_built': 1995,
        'floor_area_per_story_m2': 1500
    },
    output_path='test_outputs/final_test.idf'
)

import re
with open(idf_file, 'r') as f:
    content = f.read()

zone_count = content.count('Zone,')
surface_count = content.count('BuildingSurface:Detailed,')
floor_count = len(re.findall(r'_Floor,', content))

print(f'\nIDF Statistics:')
print(f'  Zones: {zone_count}')
print(f'  Surfaces: {surface_count}')
print(f'  Floors: {floor_count}')
print(f'  Surfaces per zone: {surface_count/zone_count:.1f}')

if surface_count < zone_count * 4:
    print(f'  ⚠️  Low surface coverage! Expected at least {zone_count*4}')
else:
    print(f'  ✅ Good surface coverage')

# Simulate
print('\nRunning simulation...')
validator = EnergyPlusSimulationValidator()
output_dir = 'test_outputs/sim_final'
os.makedirs(output_dir, exist_ok=True)

result = validator.validate_by_simulation(
    idf_file=idf_file,
    weather_file='artifacts/desktop_files/weather/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw',
    output_directory=output_dir,
    timeout=600
)

if result.success:
    print('\n✅ Simulation complete')
    
    # Read results
    with open(f'{output_dir}/eplustbl.csv', 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        if 'Total Site Energy' in line:
            parts = line.split(',')
            gj = float(parts[2].strip())
            mj_m2 = float(parts[3].strip())
            
            kwh_total = gj * 277.778
            kbtu_ft2 = (mj_m2 / 1000) * 277.778 * 3.412 / 10.764
            implied_area_m2 = (gj * 1000) / mj_m2
            
            print(f'\n📊 Results:')
            print(f'  Total: {kwh_total:,.0f} kWh/year')
            print(f'  EUI: {kbtu_ft2:.1f} kBtu/ft²/year')
            print(f'  Area: {implied_area_m2:.0f} m²')
            print(f'  Expected: 15,000 m²')
            print()
            
            efficiency = implied_area_m2 / 15000 * 100
            print(f'  Efficiency: {efficiency:.1f}%')
            
            if efficiency >= 80:
                print('  ✅ EXCELLENT')
            elif efficiency >= 60:
                print('  ⚠️  ACCEPTABLE')
            else:
                print('  🔴 NEEDS WORK')
else:
    print(f'\n❌ Simulation failed')
    print(f'   Errors: {result.errors}')


