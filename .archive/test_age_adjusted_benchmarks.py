#!/usr/bin/env python3
"""
Test Building Age Adjustments with Benchmark Buildings
"""
import os
import sys
import re
from pathlib import Path

from main import IDFCreator
from src.validation.simulation_validator import EnergyPlusSimulationValidator


def find_weather_file(location_name: str):
    """Try to find a weather file for the location"""
    common_paths = [
        "artifacts/desktop_files/weather",
        "weather",
        "/usr/share/EnergyPlus/weather",
        "/opt/EnergyPlus/weather",
        "artifacts/desktop_files/simulation"
    ]
    
    # Try to find any EPW file
    for path in common_paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith('.epw'):
                    return os.path.join(path, file)
    
    return None


def extract_energy_results(csv_file: str):
    """Extract energy results from eplustbl.csv"""
    if not os.path.exists(csv_file):
        return None
    
    with open(csv_file, 'r') as f:
        content = f.read()
    
    # Look for Total Site Energy line
    match = re.search(r',Total Site Energy,([0-9.]+),([0-9.]+)', content)
    if match:
        total_gj = float(match.group(1))
        eui_mj_m2 = float(match.group(2))
        total_kwh = total_gj * 277.778
        eui_kwh_m2 = eui_mj_m2 / 3.6
        eui_kbtu_ft2 = (eui_kwh_m2 * 3.412) / 10.764
        
        return {
            'total_energy_kwh': total_kwh,
            'eui_kwh_m2': eui_kwh_m2,
            'eui_kbtu_ft2': eui_kbtu_ft2
        }
    
    return None


def test_building(name: str, address: str, year_built: int, expected_eui: float,
                 retrofit_year: int = None, stories: int = 5, floor_area_per_story: float = 2000):
    """Test a building with age adjustments"""
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"{'='*80}")
    print(f"Address: {address}")
    print(f"Year Built: {year_built}")
    if retrofit_year:
        print(f"Retrofit Year: {retrofit_year}")
    print(f"Expected EUI: {expected_eui:.1f} kBtu/ft²/year")
    
    # Create IDF Creator
    creator = IDFCreator(professional=True, enhanced=True)
    
    # Generate IDF
    print(f"\n📝 Generating IDF...")
    user_params = {
        'year_built': year_built,
        'stories': stories,
        'floor_area_per_story_m2': floor_area_per_story,
        'building_type': 'Office'
    }
    if retrofit_year:
        user_params['retrofit_year'] = retrofit_year
    
    data = creator.process_inputs(address, user_params=user_params)
    
    # Generate IDF content
    building_params = creator.estimate_missing_parameters(data['building_params'])
    idf_content = creator.idf_generator.generate_professional_idf(
        address,
        building_params['building'],
        data['location']
    )
    
    # Save IDF
    output_dir = f"artifacts/desktop_files/simulation/age_benchmark_{name.lower().replace(' ', '_')}"
    os.makedirs(output_dir, exist_ok=True)
    idf_file = os.path.join(output_dir, f"{name.replace(' ', '_')}.idf")
    
    with open(idf_file, 'w') as f:
        f.write(idf_content)
    
    print(f"✅ IDF generated: {idf_file}")
    
    # Find weather file
    weather_file = find_weather_file(name)
    if not weather_file:
        # Try to use location weather file
        weather_file_name = data['location'].get('weather_file_name')
        if weather_file_name:
            for path in ["artifacts/desktop_files/weather", "weather"]:
                candidate = os.path.join(path, weather_file_name)
                if os.path.exists(candidate):
                    weather_file = candidate
                    break
    
    if weather_file and os.path.exists(weather_file):
        print(f"✅ Using weather file: {weather_file}")
    else:
        print(f"⚠️  Weather file not found, using default")
        weather_file = None
    
    # Run simulation
    print(f"\n⚙️  Running EnergyPlus simulation...")
    validator = EnergyPlusSimulationValidator()
    
    result = validator.validate_by_simulation(
        idf_file=idf_file,
        weather_file=weather_file,
        output_directory=output_dir,
        timeout=600
    )
    
    if not result.success:
        print(f"❌ Simulation failed!")
        print(f"   Fatal errors: {result.fatal_errors}")
        print(f"   Severe errors: {result.severe_errors}")
        print(f"   Warnings: {result.warnings}")
        return None
    
    print(f"✅ Simulation completed successfully")
    print(f"   Warnings: {result.warnings}")
    
    # Extract energy results - try CSV first
    csv_file = os.path.join(output_dir, 'eplustbl.csv')
    energy_data = extract_energy_results(csv_file)
    
    if energy_data:
        eui_kbtu_ft2 = energy_data['eui_kbtu_ft2']
        total_kwh = energy_data['total_energy_kwh']
        
        print(f"\n📊 ENERGY RESULTS:")
        print(f"   Total Energy: {total_kwh:,.0f} kWh/year")
        print(f"   EUI: {eui_kbtu_ft2:.1f} kBtu/ft²/year")
        
        # Compare to benchmark
        diff = ((eui_kbtu_ft2 - expected_eui) / expected_eui) * 100
        print(f"\n📈 COMPARISON:")
        print(f"   Expected: {expected_eui:.1f} kBtu/ft²/year")
        print(f"   Simulated: {eui_kbtu_ft2:.1f} kBtu/ft²/year")
        print(f"   Difference: {diff:+.1f}%")
        
        if abs(diff) < 5:
            print(f"   Status: ✅ EXCELLENT (within 5%)")
        elif abs(diff) < 10:
            print(f"   Status: ✅ GOOD (within 10%)")
        elif abs(diff) < 20:
            print(f"   Status: ⚠️  ACCEPTABLE (within 20%)")
        else:
            print(f"   Status: ❌ NEEDS IMPROVEMENT (>20%)")
        
        return {
            'name': name,
            'year_built': year_built,
            'retrofit_year': retrofit_year,
            'expected_eui': expected_eui,
            'simulated_eui': eui_kbtu_ft2,
            'difference_pct': diff,
            'total_energy_kwh': total_kwh
        }
    else:
        # Try manual extraction from CSV
        csv_file = os.path.join(output_dir, 'eplustbl.csv')
        energy_data = extract_energy_results(csv_file)
        
        if energy_data:
            eui_kbtu_ft2 = energy_data['eui_kbtu_ft2']
            total_kwh = energy_data['total_energy_kwh']
            
            print(f"\n📊 ENERGY RESULTS (from CSV):")
            print(f"   Total Energy: {total_kwh:,.0f} kWh/year")
            print(f"   EUI: {eui_kbtu_ft2:.1f} kBtu/ft²/year")
            
            diff = ((eui_kbtu_ft2 - expected_eui) / expected_eui) * 100
            print(f"\n📈 COMPARISON:")
            print(f"   Expected: {expected_eui:.1f} kBtu/ft²/year")
            print(f"   Simulated: {eui_kbtu_ft2:.1f} kBtu/ft²/year")
            print(f"   Difference: {diff:+.1f}%")
            
            if abs(diff) < 5:
                print(f"   Status: ✅ EXCELLENT (within 5%)")
            elif abs(diff) < 10:
                print(f"   Status: ✅ GOOD (within 10%)")
            elif abs(diff) < 20:
                print(f"   Status: ⚠️  ACCEPTABLE (within 20%)")
            else:
                print(f"   Status: ❌ NEEDS IMPROVEMENT (>20%)")
            
            return {
                'name': name,
                'year_built': year_built,
                'retrofit_year': retrofit_year,
                'expected_eui': expected_eui,
                'simulated_eui': eui_kbtu_ft2,
                'difference_pct': diff,
                'total_energy_kwh': total_kwh
            }
        else:
            print(f"❌ Could not extract energy results from CSV")
            # Try validator method as fallback
            energy_results = validator.get_energy_results(output_dir)
            if energy_results and energy_results.get('eui_kbtu_ft2'):
                eui_kbtu_ft2 = energy_results.get('eui_kbtu_ft2')
                total_kwh = energy_results.get('total_energy_kwh', 0)
                
                print(f"\n📊 ENERGY RESULTS (from validator):")
                print(f"   Total Energy: {total_kwh:,.0f} kWh/year")
                print(f"   EUI: {eui_kbtu_ft2:.1f} kBtu/ft²/year")
                
                diff = ((eui_kbtu_ft2 - expected_eui) / expected_eui) * 100
                print(f"\n📈 COMPARISON:")
                print(f"   Expected: {expected_eui:.1f} kBtu/ft²/year")
                print(f"   Simulated: {eui_kbtu_ft2:.1f} kBtu/ft²/year")
                print(f"   Difference: {diff:+.1f}%")
                
                return {
                    'name': name,
                    'year_built': year_built,
                    'retrofit_year': retrofit_year,
                    'expected_eui': expected_eui,
                    'simulated_eui': eui_kbtu_ft2,
                    'difference_pct': diff,
                    'total_energy_kwh': total_kwh
                }
            else:
                print(f"❌ Could not extract energy results")
                return None


def main():
    """Run benchmark tests with age adjustments"""
    print("="*80)
    print("BUILDING AGE ADJUSTMENT BENCHMARK TEST")
    print("="*80)
    
    results = []
    
    # Empire State Building
    # Built 1931, major retrofit 2011 (post-retrofit = modern standards)
    empire_result = test_building(
        name="Empire State Building",
        address="Empire State Building, New York, NY",
        year_built=1931,
        retrofit_year=2011,  # Post-retrofit = modern standards
        expected_eui=80.0,
        stories=5,
        floor_area_per_story=2421.46  # ~26,000 ft² per floor (5 stories for testing)
    )
    if empire_result:
        results.append(empire_result)
    
    # Willis Tower
    # Built 1973, no major retrofit (pre-1980 category)
    willis_result = test_building(
        name="Willis Tower",
        address="Willis Tower, Chicago, IL",
        year_built=1973,  # Pre-1980 = old construction
        retrofit_year=None,
        expected_eui=70.0,
        stories=5,
        floor_area_per_story=3885.00  # ~41,800 ft² per floor (5 stories for testing)
    )
    if willis_result:
        results.append(willis_result)
    
    # Summary
    print(f"\n{'='*80}")
    print("BENCHMARK SUMMARY")
    print(f"{'='*80}\n")
    
    if results:
        for r in results:
            print(f"{r['name']}:")
            print(f"  Year Built: {r['year_built']}")
            if r.get('retrofit_year'):
                print(f"  Retrofit: {r['retrofit_year']}")
            print(f"  Expected: {r['expected_eui']:.1f} kBtu/ft²/year")
            print(f"  Simulated: {r['simulated_eui']:.1f} kBtu/ft²/year")
            print(f"  Difference: {r['difference_pct']:+.1f}%")
            if abs(r['difference_pct']) < 10:
                print(f"  Status: ✅ GOOD")
            elif abs(r['difference_pct']) < 20:
                print(f"  Status: ⚠️  ACCEPTABLE")
            else:
                print(f"  Status: ❌ NEEDS WORK")
            print()
        
        avg_diff = sum(abs(r['difference_pct']) for r in results) / len(results)
        print(f"Average absolute difference: {avg_diff:.1f}%")
        
        # Check if Willis Tower improved
        willis = next((r for r in results if 'Willis' in r['name']), None)
        if willis:
            if abs(willis['difference_pct']) < 18.7:
                print(f"\n✅ Willis Tower accuracy IMPROVED from 18.7% to {abs(willis['difference_pct']):.1f}%")
            else:
                print(f"\n⚠️  Willis Tower accuracy: {abs(willis['difference_pct']):.1f}% (target: <18.7%)")
    else:
        print("❌ No results to summarize")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

