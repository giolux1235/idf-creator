#!/usr/bin/env python3
"""
Benchmark IDF Creator with Expert Features against Real Buildings
Tests the improvements from expert-level features against known building energy data
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import IDFCreator
from src.validation.simulation_validator import EnergyPlusSimulationValidator

# Real buildings with known energy data from public sources
REAL_BUILDINGS = [
    {
        'name': 'Willis Tower',
        'address': '233 S Wacker Dr, Chicago, IL 60606',
        'building_type': 'Office',
        'stories': 5,  # Reduced for simulation speed
        'year_built': 1973,
        'known_eui_kbtu_ft2': 75.0,
        'total_area_ft2': 4500000,
        'source': 'Estimated from building age and typical office EUI',
        'notes': '110-story office tower, built 1973'
    },
    {
        'name': 'Empire State Building',
        'address': '350 5th Ave, New York, NY 10118',
        'building_type': 'Office',
        'stories': 5,
        'year_built': 1931,
        'retrofit_year': 2011,
        'known_eui_kbtu_ft2': 80.0,  # Post-retrofit (2011) - 38% reduction from 130
        'total_area_ft2': 2700000,
        'source': 'Empire State Building Retrofit Report (2011)',
        'notes': '102-story, retrofitted 2011, achieved 38% energy reduction'
    },
    {
        'name': 'Chrysler Building',
        'address': '405 Lexington Ave, New York, NY 10174',
        'building_type': 'Office',
        'stories': 5,
        'year_built': 1930,
        'known_eui_kbtu_ft2': 85.0,
        'total_area_ft2': 1100000,
        'source': 'NYC Energy Benchmarking (estimated)',
        'notes': '77-story Art Deco tower, built 1930'
    },
    {
        'name': 'One World Trade Center',
        'address': '285 Fulton St, New York, NY 10007',
        'building_type': 'Office',
        'stories': 5,
        'year_built': 2014,
        'known_eui_kbtu_ft2': 60.0,  # LEED Platinum, ultra-efficient
        'total_area_ft2': 3677000,
        'source': 'LEED Platinum certification documents',
        'notes': 'LEED Platinum, completed 2014, state-of-the-art systems'
    },
    {
        'name': 'Bank of America Tower',
        'address': 'One Bryant Park, New York, NY 10036',
        'building_type': 'Office',
        'stories': 5,
        'year_built': 2009,
        'known_eui_kbtu_ft2': 55.0,  # LEED Platinum, CHP system
        'total_area_ft2': 2100000,
        'source': 'LEED Platinum, CHP system',
        'notes': 'LEED Platinum, completed 2009, cogeneration plant'
    },
    {
        'name': '30 Rockefeller Plaza',
        'address': '30 Rockefeller Plaza, New York, NY 10112',
        'building_type': 'Office',
        'stories': 5,
        'year_built': 1933,
        'known_eui_kbtu_ft2': 80.0,
        'total_area_ft2': 8430000,
        'source': 'NYC Energy Benchmarking (estimated)',
        'notes': '70-story Art Deco building, built 1933'
    },
    {
        'name': 'John Hancock Center',
        'address': '875 N Michigan Ave, Chicago, IL 60611',
        'building_type': 'Office',
        'stories': 5,
        'year_built': 1969,
        'known_eui_kbtu_ft2': 72.0,
        'total_area_ft2': 2790000,
        'source': 'Estimated from building age',
        'notes': '100-story office/residential tower, built 1969'
    },
]

def extract_energy_results(csv_file):
    """Extract energy results from eplustbl.csv"""
    if not os.path.exists(csv_file):
        return None
    
    try:
        with open(csv_file, 'r') as f:
            lines = f.readlines()
        
        energy_data = {}
        for i, line in enumerate(lines):
            if 'Total Site Energy' in line:
                parts = line.split(',')
                if len(parts) >= 3:
                    try:
                        total_gj = float(parts[2].strip())
                        total_kwh = total_gj * 277.778
                        energy_data['total_site_energy_kwh'] = total_kwh
                        
                        if len(parts) >= 4 and parts[3].strip():
                            eui_mj_m2 = float(parts[3].strip())
                            eui_kwh_m2 = eui_mj_m2 / 3.6
                            eui_kbtu_ft2 = eui_kwh_m2 * 0.317
                            energy_data['eui_kwh_m2'] = eui_kwh_m2
                            energy_data['eui_kbtu_ft2'] = eui_kbtu_ft2
                        break
                    except (ValueError, IndexError):
                        continue
        
        return energy_data
    except Exception as e:
        print(f"  ⚠️  Error reading results: {e}")
        return None

def calculate_eui(total_kwh, total_area_ft2):
    """Calculate Energy Use Intensity (EUI) in kBtu/ft²/year"""
    if total_area_ft2 == 0:
        return 0.0
    
    # Convert kWh to kBtu (1 kWh = 3.412 kBtu)
    total_kbtu = total_kwh * 3.412
    
    # Calculate EUI
    eui_kbtu_ft2 = total_kbtu / total_area_ft2
    
    return eui_kbtu_ft2

def test_building(building):
    """Test a single building"""
    print(f"\n{'='*80}")
    print(f"Testing: {building['name']}")
    print(f"{'='*80}")
    print(f"Address: {building['address']}")
    print(f"Year Built: {building['year_built']}")
    print(f"Known EUI: {building['known_eui_kbtu_ft2']:.1f} kBtu/ft²/year")
    
    try:
        # Create IDF Creator instance
        creator = IDFCreator(professional=True)
        
        # Process inputs
        user_params = {
            'building_type': building['building_type'].lower(),
            'stories': building['stories'],
            'floor_area': building['total_area_ft2'] / building['stories'] / 10.764,  # Convert to m² per floor
            'year_built': building['year_built']
        }
        
        print(f"\n📊 Generating IDF...")
        data = creator.process_inputs(building['address'], user_params=user_params)
        
        # Get building parameters
        bp = dict(data['building_params'])
        bp['__location_building'] = data.get('location', {}).get('building') or {}
        params = creator.estimate_missing_parameters(bp)
        
        # Generate IDF
        idf = creator.idf_generator.generate_professional_idf(
            building['name'],
            params['building'],
            data['location'],
            []
        )
        
        # Save IDF for inspection
        idf_file = f"test_outputs/{building['name'].replace(' ', '_')}_expert.idf"
        os.makedirs('test_outputs', exist_ok=True)
        with open(idf_file, 'w') as f:
            f.write(idf)
        print(f"  ✓ IDF generated: {idf_file}")
        
        # Check expert features
        expert_features = {
            'Differential Enthalpy Economizer': 'DifferentialEnthalpy' in idf,
            'Optimal Start': 'AvailabilityManager:OptimumStart' in idf,
            'Ground Coupling': 'Site:GroundTemperature:BuildingSurface' in idf,
            'Advanced Infiltration': 'ZoneInfiltration' in idf,
        }
        
        print(f"\n🔍 Expert Features:")
        for feature, present in expert_features.items():
            status = "✅" if present else "⚠️"
            print(f"  {status} {feature}")
        
        # Run simulation
        print(f"\n⚡ Running EnergyPlus simulation...")
        validator = EnergyPlusSimulationValidator()
        
        # Find weather file
        weather_file = data['location'].get('weather_file')
        weather_path = None
        
        common_paths = [
            'artifacts/desktop_files/weather',
            'weather',
            '/usr/share/EnergyPlus/weather',
            '/opt/EnergyPlus/weather'
        ]
        
        if weather_file:
            weather_name = os.path.basename(weather_file)
            for path in common_paths:
                test_path = os.path.join(path, weather_name)
                if os.path.exists(test_path):
                    weather_path = test_path
                    break
        
        if not weather_path:
            for path in common_paths:
                if os.path.exists(path):
                    for file in os.listdir(path):
                        if file.endswith('.epw'):
                            weather_path = os.path.join(path, file)
                            break
                    if weather_path:
                        break
        
        output_dir = f"artifacts/desktop_files/simulation/test_expert_{building['name'].replace(' ', '_').replace('/', '_').lower()}"
        os.makedirs(output_dir, exist_ok=True)
        
        result = validator.validate_by_simulation(
            idf_file,
            weather_file=weather_path,
            output_directory=output_dir,
            timeout=600
        )
        
        if not result.success:
            print(f"  ❌ Simulation failed: {result.fatal_errors} fatal, {result.severe_errors} severe errors")
            return None
        
        # Extract results
        csv_file = os.path.join(output_dir, 'eplustbl.csv')
        energy_results = extract_energy_results(csv_file)
        
        if not energy_results:
            print(f"  ⚠️  Could not extract energy results")
            return None
        
        # Check for zero energy (simulation failure)
        total_kwh = energy_results.get('total_site_energy_kwh', 0)
        if total_kwh == 0:
            print(f"  ❌ Simulation returned zero energy - simulation likely failed")
            return None
        
        # Calculate EUI
        total_area_ft2 = building['total_area_ft2']
        simulated_eui_kbtu_ft2 = energy_results.get('eui_kbtu_ft2')
        
        if not simulated_eui_kbtu_ft2:
            simulated_eui_kbtu_ft2 = (total_kwh * 3.412) / total_area_ft2 if total_area_ft2 > 0 else 0
        
        simulated_eui = simulated_eui_kbtu_ft2
        
        # Calculate difference
        percent_diff = ((simulated_eui - building['known_eui_kbtu_ft2']) / 
                       building['known_eui_kbtu_ft2']) * 100
        
        status = "✅ EXCELLENT" if abs(percent_diff) <= 10 else \
                 "✅ GOOD" if abs(percent_diff) <= 20 else \
                 "⚠️  ACCEPTABLE" if abs(percent_diff) <= 30 else \
                 "❌ NEEDS WORK"
        
        print(f"\n📈 Results:")
        print(f"  Simulated EUI: {simulated_eui:.1f} kBtu/ft²/year")
        print(f"  Known EUI: {building['known_eui_kbtu_ft2']:.1f} kBtu/ft²/year")
        print(f"  Difference: {percent_diff:+.1f}%")
        print(f"  Status: {status}")
        
        return {
            'building': building['name'],
            'year_built': building['year_built'],
            'known_eui': building['known_eui_kbtu_ft2'],
            'simulated_eui': simulated_eui,
            'percent_diff': percent_diff,
            'status': status,
            'expert_features': expert_features,
            'energy_results': energy_results,
            'total_energy_kwh': total_kwh
        }
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Test all real buildings"""
    print("="*80)
    print("EXPERT FEATURES BENCHMARK TEST")
    print("="*80)
    print("\nTesting IDF Creator with Expert Features against real buildings")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Buildings to Test: {len(REAL_BUILDINGS)}")
    
    results = []
    
    for building in REAL_BUILDINGS:
        result = test_building(building)
        if result:
            results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY - EXPERT FEATURES BENCHMARK")
    print(f"{'='*80}")
    
    if results:
        print(f"\n✅ Tested {len(results)} building(s):\n")
        
        # Detailed results
        print(f"{'Building':<30} {'Year':<6} {'Known':<8} {'Simulated':<10} {'Diff %':<8} {'Status':<20}")
        print("-" * 90)
        for r in results:
            print(f"{r['building']:<30} {r['year_built']:<6} "
                  f"{r['known_eui']:<8.1f} {r['simulated_eui']:<10.1f} "
                  f"{r['percent_diff']:+<8.1f} {r['status']:<20}")
        
        # Statistics
        avg_diff = sum(abs(r['percent_diff']) for r in results) / len(results)
        within_10 = sum(1 for r in results if abs(r['percent_diff']) <= 10)
        within_20 = sum(1 for r in results if abs(r['percent_diff']) <= 20)
        
        # Group by building age
        pre_1980 = [r for r in results if r['year_built'] < 1980]
        modern = [r for r in results if r['year_built'] >= 2000]
        
        pre_1980_avg = sum(abs(r['percent_diff']) for r in pre_1980) / len(pre_1980) if pre_1980 else 0
        modern_avg = sum(abs(r['percent_diff']) for r in modern) / len(modern) if modern else 0
        
        print(f"\n📊 Statistics:")
        print(f"  Average Absolute Error: {avg_diff:.1f}%")
        print(f"  Within ±10%: {within_10}/{len(results)} ({within_10*100/len(results):.0f}%)")
        print(f"  Within ±20%: {within_20}/{len(results)} ({within_20*100/len(results):.0f}%)")
        
        print(f"\n📅 By Building Age:")
        if pre_1980:
            print(f"  Pre-1980 Buildings ({len(pre_1980)}): Average Error {pre_1980_avg:.1f}%")
        if modern:
            print(f"  Modern Buildings (2000+, {len(modern)}): Average Error {modern_avg:.1f}%")
        
        # Expert features summary
        print(f"\n🔍 Expert Features Summary:")
        feature_counts = {}
        for r in results:
            for feature, present in r['expert_features'].items():
                if feature not in feature_counts:
                    feature_counts[feature] = {'present': 0, 'total': 0}
                feature_counts[feature]['total'] += 1
                if present:
                    feature_counts[feature]['present'] += 1
        
        for feature, counts in feature_counts.items():
            pct = (counts['present'] / counts['total']) * 100
            print(f"  {feature}: {counts['present']}/{counts['total']} ({pct:.0f}%)")
        
        # Overall assessment
        print(f"\n🎯 Overall Assessment:")
        if avg_diff <= 10:
            print("  🎉 EXCELLENT accuracy - Expert features are working well!")
        elif avg_diff <= 15:
            print("  ✅ GOOD accuracy - Expert features showing improvement")
        elif avg_diff <= 20:
            print("  ⚠️  ACCEPTABLE accuracy - Some room for improvement")
        else:
            print("  ❌ NEEDS IMPROVEMENT - Further calibration required")
        
        # Comparison to previous results
        print(f"\n📊 Comparison to Previous Tests:")
        print(f"  Previous Average Error: 11.0%")
        print(f"  Current Average Error: {avg_diff:.1f}%")
        if avg_diff < 11.0:
            improvement = 11.0 - avg_diff
            print(f"  ✅ Improvement: {improvement:.1f}% better")
        else:
            print(f"  ⚠️  Slight regression: {avg_diff - 11.0:.1f}% worse")
        
    else:
        print("❌ No successful simulations")
    
    print(f"\n{'='*80}")
    print("Test Complete")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()

