#!/usr/bin/env python3
"""
Benchmark IDF Creator results against known building energy reports
"""
import sys
import os
from main import IDFCreator
from src.validation import EnergyPlusSimulationValidator, validate_energy_coherence
from src.cbecs_lookup import CBECSLookup


# Known building energy data from public reports
KNOWN_BUILDINGS = {
    'empire_state': {
        'address': 'Empire State Building, New York, NY',
        'name': 'Empire State Building',
        'building_type': 'Office',
        'total_area_ft2': 2658589,  # 2.6M ft²
        'stories': 102,
        # From Empire State Building retrofit report (2011)
        'reported_eui_kbtu_ft2': 80.0,  # After retrofit
        'reported_eui_pre_retrofit': 130.0,  # Before retrofit
        'source': 'Empire State Building Retrofit Report (2011)',
        'year': 2011
    },
    'willis_tower': {
        'address': 'Willis Tower, Chicago, IL',
        'name': 'Willis Tower (Sears Tower)',
        'building_type': 'Office',
        'total_area_ft2': 4600000,  # 4.6M ft²
        'stories': 110,
        # Estimated from public reports
        'reported_eui_kbtu_ft2': 70.0,  # Typical for large office buildings
        'source': 'Estimated from public building energy reports',
        'year': 2020
    },
    'chrysler_building': {
        'address': 'Chrysler Building, New York, NY',
        'name': 'Chrysler Building',
        'building_type': 'Office',
        'total_area_ft2': 1100000,  # 1.1M ft²
        'stories': 77,
        # Estimated from NYC benchmarking
        'reported_eui_kbtu_ft2': 85.0,
        'source': 'NYC Energy Benchmarking (estimated)',
        'year': 2020
    }
}

# DOE Reference Building typical values
DOE_REFERENCE_BUILDINGS = {
    'office_small': {
        'name': 'Small Office (DOE Reference)',
        'area_ft2': 5500,
        'stories': 1,
        'eui_kbtu_ft2': 52.0,  # Climate Zone 4-5
        'source': 'DOE Commercial Reference Buildings'
    },
    'office_medium': {
        'name': 'Medium Office (DOE Reference)',
        'area_ft2': 49800,
        'stories': 3,
        'eui_kbtu_ft2': 51.6,  # Climate Zone 4-5
        'source': 'DOE Commercial Reference Buildings'
    },
    'office_large': {
        'name': 'Large Office (DOE Reference)',
        'area_ft2': 498587,
        'stories': 12,
        'eui_kbtu_ft2': 62.2,  # Climate Zone 4-5
        'source': 'DOE Commercial Reference Buildings'
    }
}


def benchmark_building(building_key: str, known_data: dict, weather_file: str = None):
    """Benchmark a building against known energy data"""
    print("=" * 80)
    print(f"BENCHMARKING: {known_data['name']}")
    print("=" * 80)
    
    print(f"\nKnown Energy Data:")
    print(f"  - Source: {known_data.get('source', 'Unknown')}")
    print(f"  - Reported EUI: {known_data['reported_eui_kbtu_ft2']:.1f} kBtu/ft²/year")
    print(f"  - Total Area: {known_data['total_area_ft2']:,} ft² ({known_data['total_area_ft2']/10.764:,.0f} m²)")
    print(f"  - Stories: {known_data.get('stories', 'Unknown')}")
    
    # Calculate reasonable test parameters
    total_area_m2 = known_data['total_area_ft2'] / 10.764
    floor_area_m2 = total_area_m2 / known_data.get('stories', 10)  # Estimate per floor
    
    # Limit for reasonable simulation time
    if floor_area_m2 > 10000:
        floor_area_m2 = 10000
        print(f"\n  ⚠ Limiting floor area to 10,000 m² for simulation speed")
    
    stories = min(known_data.get('stories', 10), 5)  # Limit to 5 stories max
    print(f"\n  → Simulating {stories} stories × {floor_area_m2:.0f} m² = {stories * floor_area_m2:.0f} m² total")
    
    # Generate IDF
    print(f"\n1. Generating IDF...")
    try:
        creator = IDFCreator(professional=True, enhanced=True)
        
        location_data = creator.process_inputs(
            address=known_data['address'],
            user_params={
                'building_type': known_data['building_type'],
                'stories': stories,
                'floor_area': floor_area_m2
            }
        )
        
        idf_file = creator.create_idf(
            address=known_data['address'],
            user_params={
                'building_type': known_data['building_type'],
                'stories': stories,
                'floor_area': floor_area_m2
            },
            output_path=f"artifacts/desktop_files/idf/benchmark_{building_key}.idf"
        )
        
        print(f"   ✓ IDF generated: {idf_file}")
        
    except Exception as e:
        print(f"   ✗ IDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Run simulation
    print(f"\n2. Running simulation...")
    output_dir = f"artifacts/desktop_files/simulation/benchmark_{building_key}"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        validator = EnergyPlusSimulationValidator()
        result = validator.validate_by_simulation(
            idf_file=os.path.abspath(idf_file),
            weather_file=weather_file,
            output_directory=os.path.abspath(output_dir),
            timeout=600
        )
        
        if not result.success:
            print(f"   ⚠ Simulation had errors (fatal: {result.fatal_errors})")
            return None
        
        print(f"   ✓ Simulation completed successfully")
        
    except Exception as e:
        print(f"   ✗ Simulation failed: {e}")
        return None
    
    # Extract energy results
    print(f"\n3. Extracting energy results...")
    try:
        energy_results = validator.get_energy_results(output_dir)
        
        if not energy_results:
            # Try parsing CSV manually
            csv_file = os.path.join(output_dir, 'eplustbl.csv')
            if os.path.exists(csv_file):
                import re
                with open(csv_file, 'r') as f:
                    content = f.read()
                
                match = re.search(r',Total Site Energy,([0-9.]+),([0-9.]+)', content)
                if match:
                    total_gj = float(match.group(1))
                    eui_mj_m2 = float(match.group(2))
                    total_kwh = total_gj * 277.778
                    eui_kwh_m2 = eui_mj_m2 / 3.6
                    eui_kbtu_ft2 = (eui_kwh_m2 * 3.412) / 10.764
                    
                    simulated_area_m2 = stories * floor_area_m2
                    
                    return {
                        'building': known_data['name'],
                        'reported_eui': known_data['reported_eui_kbtu_ft2'],
                        'simulated_eui': eui_kbtu_ft2,
                        'total_energy_kwh': total_kwh,
                        'total_area_m2': simulated_area_m2,
                        'percent_diff': ((eui_kbtu_ft2 - known_data['reported_eui_kbtu_ft2']) / known_data['reported_eui_kbtu_ft2']) * 100,
                        'source': known_data.get('source', 'Unknown')
                    }
        
        return None
        
    except Exception as e:
        print(f"   ✗ Energy extraction failed: {e}")
        return None


def compare_to_doe_reference():
    """Compare to DOE Reference Building values"""
    print("\n" + "=" * 80)
    print("COMPARISON TO DOE REFERENCE BUILDINGS")
    print("=" * 80)
    
    cbecs = CBECSLookup()
    typical_eui = cbecs.get_site_eui('office')
    
    print(f"\nCBECS Typical Office EUI: {typical_eui:.1f} kBtu/ft²/year")
    
    print(f"\nDOE Reference Building Values:")
    for ref_key, ref_data in DOE_REFERENCE_BUILDINGS.items():
        print(f"\n  {ref_data['name']}:")
        print(f"    - Area: {ref_data['area_ft2']:,} ft²")
        print(f"    - Stories: {ref_data['stories']}")
        print(f"    - EUI: {ref_data['eui_kbtu_ft2']:.1f} kBtu/ft²/year")
        print(f"    - Source: {ref_data['source']}")
    
    return typical_eui


def main():
    """Run benchmark comparisons"""
    print("=" * 80)
    print("BUILDING ENERGY BENCHMARK ANALYSIS")
    print("=" * 80)
    
    # Find weather file
    weather_file = None
    for path in ["artifacts/desktop_files/weather/Chicago.epw",
                  "artifacts/desktop_files/weather/*.epw"]:
        if os.path.exists(path):
            weather_file = path
            break
    
    if weather_file:
        print(f"\nUsing weather file: {weather_file}")
    else:
        print(f"\n⚠ No weather file found - simulations may fail")
    
    # Compare to DOE/CBECS
    typical_eui = compare_to_doe_reference()
    
    # Benchmark known buildings
    results = []
    
    # Test Empire State Building (if we have NY weather)
    if weather_file or True:  # Try anyway
        print("\n\n" + "=" * 80)
        empire_result = benchmark_building('empire_state', KNOWN_BUILDINGS['empire_state'], weather_file)
        if empire_result:
            results.append(empire_result)
    
    # Test Willis Tower (we have Chicago weather)
    if weather_file:
        print("\n\n" + "=" * 80)
        willis_result = benchmark_building('willis_tower', KNOWN_BUILDINGS['willis_tower'], weather_file)
        if willis_result:
            results.append(willis_result)
    
    # Summary
    print("\n\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)
    
    if results:
        print(f"\nComparison Results:")
        print(f"\n{'Building':<30} {'Reported':<12} {'Simulated':<12} {'Difference':<12} {'Status':<20}")
        print("-" * 90)
        
        for r in results:
            diff_pct = r['percent_diff']
            if abs(diff_pct) < 20:
                status = "✅ Excellent match"
            elif abs(diff_pct) < 40:
                status = "✅ Good match"
            elif abs(diff_pct) < 60:
                status = "⚠ Moderate difference"
            else:
                status = "❌ Large difference"
            
            print(f"{r['building']:<30} {r['reported_eui']:>10.1f}    {r['simulated_eui']:>10.1f}    {diff_pct:>+10.1f}%    {status}")
        
        print(f"\n\nNotes:")
        print(f"- Reported values are from public building energy reports")
        print(f"- Simulated values are from IDF Creator + EnergyPlus")
        print(f"- Differences can be due to:")
        print(f"  * Building age and retrofit status")
        print(f"  * Operational schedules (actual vs simulated)")
        print(f"  * HVAC system efficiency")
        print(f"  * Weather year differences")
        print(f"  * Building-specific features not modeled")
    else:
        print("\n⚠ No simulation results available for comparison")
    
    print(f"\n\nCBECS Benchmark:")
    print(f"- Typical Office EUI: {typical_eui:.1f} kBtu/ft²/year")
    if results:
        for r in results:
            vs_cbecs = ((r['simulated_eui'] - typical_eui) / typical_eui) * 100
            print(f"- {r['building']} vs CBECS: {vs_cbecs:+.1f}%")


if __name__ == "__main__":
    main()



