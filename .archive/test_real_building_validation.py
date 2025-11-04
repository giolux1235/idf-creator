#!/usr/bin/env python3
"""
Test IDF Creator with real buildings that have known energy consumption data.
Compares simulated results with known benchmarks.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import IDFCreator
from src.validation.simulation_validator import EnergyPlusSimulationValidator
import re

# Real buildings with known energy data
REAL_BUILDINGS = [
    {
        'name': 'Willis Tower',
        'address': '233 S Wacker Dr, Chicago, IL 60606',
        'building_type': 'Office',
        'stories': 5,  # Reduced for faster simulation (scale results proportionally)
        'year_built': 1973,
        'known_eui_kbtu_ft2': 75.0,  # Estimated for 50-year-old building
        'total_area_ft2': 4500000,  # Keep full area for EUI calculation
        'notes': '110-story office tower, built 1973. Estimated EUI based on building age.'
    },
    {
        'name': 'Empire State Building',
        'address': '350 5th Ave, New York, NY 10118',
        'building_type': 'Office',
        'stories': 5,  # Reduced for faster simulation (scale results proportionally)
        'year_built': 1931,
        'known_eui_kbtu_ft2': 85.0,  # Estimated for 90+ year old building (pre-renovation baseline)
        'total_area_ft2': 2700000,  # Keep full area for EUI calculation
        'notes': '102-story office building, built 1931, renovated 2009. Using pre-renovation baseline.'
    }
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
        return {'error': str(e)}

def test_building(building):
    """Test a single building and compare with known data"""
    print(f"\n{'='*80}")
    print(f"Testing: {building['name']}")
    print(f"{'='*80}")
    print(f"Address: {building['address']}")
    print(f"Building Type: {building['building_type']}")
    print(f"Stories: {building['stories']}")
    print(f"Year Built: {building['year_built']}")
    print(f"Known EUI: {building['known_eui_kbtu_ft2']} kBtu/ft²/year")
    print(f"Notes: {building['notes']}")
    
    # Create IDF Creator
    creator = IDFCreator(professional=True, enhanced=True)
    
    # Process inputs
    try:
        data = creator.process_inputs(
            building['address'],
            user_params={
                'building_type': building['building_type'],
                'stories': building['stories'],
                'year_built': building['year_built'],
                'floor_area_per_story_m2': 1500  # Use reasonable floor area for simulation speed
            }
        )
        
        # Estimate missing parameters
        bp = creator.estimate_missing_parameters(data['building_params'])
        
        # Generate IDF
        idf_file = creator.create_idf(
            building['address'],
            documents=None,
            user_params={
                'building_type': building['building_type'],
                'stories': building['stories'],
                'year_built': building['year_built'],
                'floor_area_per_story_m2': building['total_area_ft2'] * 0.092903 / building['stories']
            }
        )
        
        if not idf_file or not os.path.exists(idf_file):
            print(f"❌ Failed to generate IDF")
            return None
        
        print(f"✅ IDF Generated: {idf_file}")
        print(f"   File size: {os.path.getsize(idf_file):,} bytes")
        
        # Check features
        with open(idf_file, 'r') as f:
            idf_content = f.read()
            print(f"\n📊 Features Generated:")
            print(f"   Daylighting:Controls: {idf_content.count('Daylighting:Controls')}")
            print(f"   InternalMass: {idf_content.count('InternalMass')}")
            print(f"   SetpointManager:OutdoorAirReset: {idf_content.count('SetpointManager:OutdoorAirReset')}")
        
        # Run simulation
        validator = EnergyPlusSimulationValidator()
        
        # Find weather file
        weather_file = data['location'].get('weather_file')
        weather_path = None
        
        # Try common locations first
        common_paths = [
            'artifacts/desktop_files/weather',
            'weather',
            '/usr/share/EnergyPlus/weather',
            '/opt/EnergyPlus/weather'
        ]
        
        # Try to find any EPW file if specific one not found
        if weather_file:
            weather_name = os.path.basename(weather_file)
            for path in common_paths:
                test_path = os.path.join(path, weather_name)
                if os.path.exists(test_path):
                    weather_path = test_path
                    break
        
        # Fallback: find any EPW file
        if not weather_path:
            for path in common_paths:
                if os.path.exists(path):
                    for file in os.listdir(path):
                        if file.endswith('.epw'):
                            weather_path = os.path.join(path, file)
                            print(f"✅ Using fallback weather file: {weather_path}")
                            break
                    if weather_path:
                        break
        
        if not weather_path:
            print(f"⚠️  Weather file not found, simulation may fail")
            weather_path = None
        
        # Create output directory
        output_dir = f"artifacts/desktop_files/simulation/real_building_test_{building['name'].replace(' ', '_').lower()}"
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n🌤️  Running EnergyPlus simulation...")
        print(f"   Weather file: {weather_path or 'Auto-detect'}")
        
        result = validator.validate_by_simulation(
            idf_file,
            weather_file=weather_path,
            output_directory=output_dir,
            timeout=600  # 10 minutes for large buildings
        )
        
        print(f"\n⚙️  Simulation Results:")
        print(f"   Success: {'✅' if result.success else '❌'}")
        print(f"   Fatal errors: {result.fatal_errors}")
        print(f"   Severe errors: {result.severe_errors}")
        print(f"   Warnings: {result.warnings}")
        
        if not result.success:
            print(f"   ❌ Simulation failed - cannot compare energy results")
            return None
        
        # Extract energy results
        csv_file = os.path.join(output_dir, 'eplustbl.csv')
        energy = extract_energy_results(csv_file)
        
        if not energy or 'error' in energy:
            print(f"   ❌ Could not extract energy results")
            return None
        
        # Calculate building area from actual simulation
        # Get total area from IDF or calculate from simulated building
        # For now, use the known total area for EUI calculation
        total_area_ft2 = building['total_area_ft2']
        total_area_m2 = total_area_ft2 * 0.092903
        
        # Try to get actual simulated area from IDF
        with open(idf_file, 'r') as f:
            idf_content = f.read()
            # Look for Building object
            building_match = re.search(r'Building,\s*[^,]+,\s*([0-9.]+)', idf_content)
            if building_match:
                # This is usually the north axis angle, not area
                # Calculate from zones instead
                zone_matches = re.findall(r'Zone,\s*([^,]+),', idf_content)
                # Estimate area from zones (simplified - actual calculation would sum zone areas)
                print(f"   Found {len(zone_matches)} zones in IDF")
        
        # Get EUI
        simulated_eui_kbtu_ft2 = energy.get('eui_kbtu_ft2')
        if not simulated_eui_kbtu_ft2:
            # Calculate from total energy
            total_kwh = energy.get('total_site_energy_kwh', 0)
            simulated_eui_kbtu_ft2 = (total_kwh * 3.412) / total_area_ft2
        
        known_eui = building['known_eui_kbtu_ft2']
        difference = simulated_eui_kbtu_ft2 - known_eui
        percent_diff = (difference / known_eui) * 100
        
        print(f"\n📊 ENERGY COMPARISON:")
        print(f"   Total Energy: {energy.get('total_site_energy_kwh', 0):,.0f} kWh/year")
        print(f"   Building Area: {total_area_ft2:,.0f} ft² ({total_area_m2:,.0f} m²)")
        print(f"   Simulated EUI: {simulated_eui_kbtu_ft2:.1f} kBtu/ft²/year")
        print(f"   Known EUI: {known_eui:.1f} kBtu/ft²/year")
        print(f"   Difference: {difference:+.1f} kBtu/ft²/year ({percent_diff:+.1f}%)")
        
        # Evaluate accuracy
        if abs(percent_diff) <= 10:
            status = "✅ EXCELLENT"
        elif abs(percent_diff) <= 20:
            status = "✅ GOOD"
        elif abs(percent_diff) <= 30:
            status = "⚠️  ACCEPTABLE"
        else:
            status = "❌ NEEDS IMPROVEMENT"
        
        print(f"\n🎯 Accuracy Assessment: {status}")
        print(f"   {'✅' if abs(percent_diff) <= 20 else '⚠️'} Within ±20%: {abs(percent_diff) <= 20}")
        print(f"   {'✅' if abs(percent_diff) <= 10 else '⚠️'} Within ±10%: {abs(percent_diff) <= 10}")
        
        return {
            'building': building['name'],
            'simulated_eui': simulated_eui_kbtu_ft2,
            'known_eui': known_eui,
            'difference': difference,
            'percent_diff': percent_diff,
            'status': status,
            'total_energy_kwh': energy.get('total_site_energy_kwh', 0)
        }
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Test all real buildings"""
    print("="*80)
    print("REAL BUILDING VALIDATION TEST")
    print("="*80)
    print("\nTesting IDF Creator against buildings with known energy consumption data")
    
    results = []
    
    for building in REAL_BUILDINGS:
        result = test_building(building)
        if result:
            results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    if results:
        print(f"\n✅ Tested {len(results)} building(s):")
        for r in results:
            print(f"\n  {r['building']}:")
            print(f"    Simulated: {r['simulated_eui']:.1f} kBtu/ft²/year")
            print(f"    Known: {r['known_eui']:.1f} kBtu/ft²/year")
            print(f"    Difference: {r['percent_diff']:+.1f}%")
            print(f"    Status: {r['status']}")
        
        # Overall accuracy
        avg_diff = sum(abs(r['percent_diff']) for r in results) / len(results)
        print(f"\n📊 Overall Average Difference: {avg_diff:.1f}%")
        
        if avg_diff <= 10:
            print("🎉 EXCELLENT accuracy - IDF Creator is performing very well!")
        elif avg_diff <= 20:
            print("✅ GOOD accuracy - IDF Creator is performing well")
        elif avg_diff <= 30:
            print("⚠️  ACCEPTABLE accuracy - Some improvements needed")
        else:
            print("❌ NEEDS IMPROVEMENT - Significant calibration required")
    else:
        print("❌ No successful simulations")

if __name__ == '__main__':
    main()

