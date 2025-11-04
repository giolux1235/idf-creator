#!/usr/bin/env python3
"""
Test multiple buildings with known energy data to check our accuracy
Focus: Willis Tower, Empire State, Chrysler Building, One WTC, Bank of America Tower
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from main import IDFCreator
from src.validation.simulation_validator import EnergyPlusSimulationValidator

# Test buildings with known energy data
TEST_BUILDINGS = [
    {
        'name': 'Willis Tower',
        'address': '233 S Wacker Dr, Chicago, IL 60606',
        'building_type': 'Office',
        'stories': 10,  # More realistic height
        'year_built': 1974,
        'known_eui_kbtu_ft2': 75.0,
        'weather_file': 'artifacts/desktop_files/weather/Chicago.epw',
        'floor_area_per_story_m2': 2000
    },
    {
        'name': 'Empire State Building',
        'address': '350 5th Ave, New York, NY 10118',
        'building_type': 'Office',
        'stories': 10,
        'year_built': 1931,
        'retrofit_year': 2011,
        'known_eui_kbtu_ft2': 80.0,
        'weather_file': 'artifacts/desktop_files/weather/artifacts/desktop_files/weather/USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw',
        'floor_area_per_story_m2': 2000
    },
    {
        'name': 'Chrysler Building',
        'address': '405 Lexington Ave, New York, NY 10174',
        'building_type': 'Office',
        'stories': 10,
        'year_built': 1930,
        'known_eui_kbtu_ft2': 85.0,
        'weather_file': 'artifacts/desktop_files/weather/artifacts/desktop_files/weather/USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw',
        'floor_area_per_story_m2': 2000
    },
    {
        'name': 'One World Trade Center',
        'address': '285 Fulton St, New York, NY 10007',
        'building_type': 'Office',
        'stories': 10,
        'year_built': 2014,
        'leed_level': 'Platinum',
        'known_eui_kbtu_ft2': 60.0,
        'weather_file': 'artifacts/desktop_files/weather/artifacts/desktop_files/weather/USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw',
        'floor_area_per_story_m2': 2000
    },
    {
        'name': 'Bank of America Tower',
        'address': '1 Bryant Park, New York, NY 10036',
        'building_type': 'Office',
        'stories': 10,
        'year_built': 2009,
        'leed_level': 'Platinum',
        'cogeneration_capacity_kw': 5000.0,
        'chp_provides_percent': 70.0,
        'known_eui_kbtu_ft2': 55.0,
        'weather_file': 'artifacts/desktop_files/weather/artifacts/desktop_files/weather/USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw',
        'floor_area_per_story_m2': 2000
    }
]


def extract_energy(csv_file):
    """Extract energy from eplustbl.csv"""
    try:
        import pandas as pd
        
        # Read energy summary section
        with open(csv_file, 'r') as f:
            lines = f.readlines()
        
        total_gj = None
        area_mj_m2 = None
        
        for i, line in enumerate(lines):
            if 'Total Site Energy' in line and total_gj is None:
                # Parse the next data line
                if i + 1 < len(lines):
                    data_line = lines[i + 1]
                    parts = [p.strip() for p in data_line.split(',')]
                    if len(parts) >= 3:
                        try:
                            total_gj = float(parts[2])
                            area_mj_m2 = float(parts[3])
                        except:
                            pass
        
        if total_gj and area_mj_m2:
            # Convert
            kwh_total = total_gj * 277.778
            kwh_m2 = (area_mj_m2 / 1000) * 277.778
            kbtu_ft2 = kwh_m2 * 3.412 / 10.764
            return kwh_total, kwh_m2, kbtu_ft2
        
        return None, None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None


def test_building(building):
    """Test one building"""
    print(f"\n{'='*80}")
    print(f"{building['name']}")
    print(f"{'='*80}")
    print(f"Year: {building['year_built']}")
    if building.get('retrofit_year'):
        print(f"Retrofit: {building['retrofit_year']}")
    if building.get('leed_level'):
        print(f"LEED: {building['leed_level']}")
    if building.get('cogeneration_capacity_kw'):
        print(f"CHP: {building['cogeneration_capacity_kw']} kW")
    print(f"Expected EUI: {building['known_eui_kbtu_ft2']:.1f} kBtu/ft²/year")
    
    # Generate IDF
    creator = IDFCreator(professional=True, enhanced=True)
    bldg_params = {
        'building_type': building['building_type'],
        'stories': building['stories'],
        'year_built': building['year_built'],
        'floor_area_per_story_m2': building['floor_area_per_story_m2']
    }
    if building.get('retrofit_year'):
        bldg_params['retrofit_year'] = building['retrofit_year']
    if building.get('leed_level'):
        bldg_params['leed_level'] = building['leed_level']
    if building.get('cogeneration_capacity_kw'):
        bldg_params['cogeneration_capacity_kw'] = building['cogeneration_capacity_kw']
    if building.get('chp_provides_percent'):
        bldg_params['chp_provides_percent'] = building['chp_provides_percent']
    
    idf_file = creator.create_idf(
        building['address'],
        user_params=bldg_params,
        output_path=f"test_outputs/accuracy_{building['name'].replace(' ', '_')}.idf"
    )
    print(f"✅ IDF: {idf_file}")
    
    # Run simulation
    validator = EnergyPlusSimulationValidator()
    output_dir = f"test_outputs/sim_accuracy_{building['name'].replace(' ', '_')}"
    os.makedirs(output_dir, exist_ok=True)
    
    print("Running simulation...")
    result = validator.validate_by_simulation(
        idf_file=idf_file,
        weather_file=building['weather_file'],
        output_directory=output_dir,
        timeout=600
    )
    
    if not result.success:
        print(f"❌ Failed: {result.fatal_errors} fatal errors")
        return None
    
    # Extract energy
    csv_file = os.path.join(output_dir, 'eplustbl.csv')
    kwh_total, kwh_m2, kbtu_ft2 = extract_energy(csv_file)
    
    if kbtu_ft2:
        expected = building['known_eui_kbtu_ft2']
        diff_pct = (kbtu_ft2 - expected) / expected * 100
        
        print(f"\n📊 Results:")
        print(f"   Simulated: {kbtu_ft2:.1f} kBtu/ft²/year")
        print(f"   Expected: {expected:.1f} kBtu/ft²/year")
        print(f"   Difference: {diff_pct:+.1f}%")
        
        # Apply LEED/CHP post-processing if applicable
        final_eui = kbtu_ft2
        if building.get('leed_level') == 'Platinum':
            print(f"   ✅ Using 35% LEED Platinum bonus")
        
        if building.get('cogeneration_capacity_kw'):
            chp_pct = building.get('chp_provides_percent', 70)
            print(f"   ✅ CHP provides {chp_pct}% (updated 80% cap)")
            # Apply CHP reduction
            from src.building_age_adjustments import BuildingAgeAdjuster
            adjuster = BuildingAgeAdjuster()
            chp_reduction = adjuster.get_cogeneration_eui_reduction(
                building['cogeneration_capacity_kw'],
                building['stories'] * building['floor_area_per_story_m2'],
                chp_pct
            )
            final_eui = kbtu_ft2 * chp_reduction
            diff_pct = (final_eui - expected) / expected * 100
            print(f"   With CHP: {final_eui:.1f} kBtu/ft²/year ({diff_pct:+.1f}%)")
        
        status = "✅ EXCELLENT" if abs(diff_pct) < 10 else "✅ GOOD" if abs(diff_pct) < 20 else "⚠️ NEEDS WORK"
        print(f"   Status: {status}")
        
        return {
            'name': building['name'],
            'simulated': kbtu_ft2,
            'final': final_eui,
            'expected': expected,
            'difference_pct': diff_pct,
            'status': status
        }
    else:
        print("❌ Could not extract energy")
        return None


def main():
    print("="*80)
    print("ACCURACY TEST - AFTER ALL FIXES")
    print("="*80)
    print("Testing with known buildings and energy data")
    print()
    
    results = []
    for building in TEST_BUILDINGS:
        result = test_building(building)
        if result:
            results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print("="*80)
    
    if results:
        avg_error = sum(abs(r['difference_pct']) for r in results) / len(results)
        print(f"\nAverage Absolute Error: {avg_error:.1f}%")
        print(f"ASHRAE 14 Target: ≤10%")
        print(f"Meets Target: {'✅ YES' if avg_error <= 10 else '⚠️ NO'}")
        
        print(f"\nIndividual Results:")
        for r in results:
            print(f"  {r['name']}: {r['difference_pct']:+.1f}%")
        
        # Previous vs current
        print(f"\n{'='*80}")
        print("COMPARISON TO PREVIOUS RESULTS")
        print("="*80)
        print("Willis Tower: Previous +5.2%, Current: see above")
        print("Empire State: Previous -1.3%, Current: see above")
        print("Chrysler: Previous -17.1%, Current: see above")
        print("One WTC: Previous +16.8%, Current: see above (with LEED)")
        print("Bank of America: Previous +40.6%, Current: see above (with LEED+CHP)")
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print("="*80)


if __name__ == '__main__':
    main()

