#!/usr/bin/env python3
"""
Test Integrated Features with Florida Building Simulation
"""
import os
import sys
from pathlib import Path

from main import IDFCreator
from src.validation.simulation_validator import EnergyPlusSimulationValidator
from src.validation.idf_validator import IDFValidator


def find_weather_file(location_name: str):
    """Find weather file on machine"""
    search_paths = [
        "artifacts/desktop_files/weather",
        "weather",
        "/usr/share/EnergyPlus/weather",
        "/opt/EnergyPlus/weather",
        os.path.expanduser("~/EnergyPlus/weather"),
        os.path.expanduser("~/epw"),
    ]
    
    # Try to find Florida weather files
    florida_cities = [
        "Miami", "Tampa", "Orlando", "Jacksonville", "Fort_Myers",
        "Tallahassee", "West_Palm", "FL", "Florida"
    ]
    
    for path in search_paths:
        if not os.path.exists(path):
            continue
        
        # First try exact location match
        if location_name:
            candidate = os.path.join(path, f"{location_name}.epw")
            if os.path.exists(candidate):
                return candidate
        
        # Try Florida cities
        for city in florida_cities:
            for filename in os.listdir(path):
                if city.lower() in filename.lower() and filename.endswith('.epw'):
                    return os.path.join(path, filename)
        
        # Try any EPW file in directory
        for filename in os.listdir(path):
            if filename.endswith('.epw'):
                return os.path.join(path, filename)
    
    return None


def check_idf_features(idf_content: str) -> dict:
    """Check which advanced features are present in IDF"""
    features = {
        'economizer': 'Controller:OutdoorAir' in idf_content,
        'daylighting': 'Daylighting:Controls' in idf_content,
        'outdoor_air_reset': 'SetpointManager:OutdoorAirReset' in idf_content,
        'vav_system': 'AirLoopHVAC' in idf_content,
    }
    return features


def test_florida_building():
    """Test IDF generation and simulation for Florida building"""
    print("="*80)
    print("FLORIDA BUILDING SIMULATION TEST - INTEGRATED FEATURES")
    print("="*80)
    
    # Florida address
    address = "200 E Broward Blvd, Fort Lauderdale, FL 33301"
    
    building_params = {
        'building_type': 'Office',
        'stories': 3,
        'floor_area_per_story_m2': 1500
    }
    
    # Create IDF
    creator = IDFCreator(professional=True, enhanced=True)
    
    print(f"\n📝 Generating IDF for: {address}")
    print(f"   Building: {building_params['building_type']}, {building_params['stories']} stories")
    
    try:
        data = creator.process_inputs(address, user_params=building_params)
        building_params_complete = creator.estimate_missing_parameters(data['building_params'])
        
        idf_content = creator.idf_generator.generate_professional_idf(
            address,
            building_params_complete['building'],
            data['location']
        )
        
        # Check features
        features = check_idf_features(idf_content)
        
        print(f"\n✅ IDF Generated Successfully")
        print(f"\n📊 FEATURE CHECK:")
        for feature, present in features.items():
            status = "✅" if present else "❌"
            print(f"   {status} {feature.replace('_', ' ').title()}: {'Present' if present else 'Missing'}")
        
        # Validate IDF
        print(f"\n🔍 Validating IDF...")
        validator = IDFValidator()
        validation_results = validator.validate(idf_content)
        
        if validation_results:
            errors = validation_results.get('error_count', 0)
            warnings = validation_results.get('warning_count', 0)
            print(f"   Errors: {errors}")
            print(f"   Warnings: {warnings}")
            
            if errors > 0:
                print(f"\n   ⚠️  First few errors:")
                for error in validation_results.get('errors', [])[:3]:
                    print(f"     - {error}")
        else:
            print(f"   ⚠️  Validation returned no results")
        
        # Save IDF
        output_dir = "artifacts/desktop_files/simulation/florida_test"
        os.makedirs(output_dir, exist_ok=True)
        idf_file = os.path.join(output_dir, "florida_office.idf")
        
        with open(idf_file, 'w') as f:
            f.write(idf_content)
        
        print(f"\n💾 IDF saved: {idf_file}")
        print(f"   File size: {len(idf_content):,} bytes")
        print(f"   Lines: {len(idf_content.splitlines()):,}")
        
        # Find weather file
        location_name = data['location'].get('weather_file_name', '')
        if not location_name:
            # Try to extract from weather file path
            weather_path = data['location'].get('weather_file', '')
            if weather_path:
                location_name = os.path.basename(weather_path).replace('.epw', '')
        
        print(f"\n🌤️  Searching for weather file...")
        weather_file = find_weather_file(location_name)
        
        if not weather_file:
            # Try to get from location data
            weather_path = data['location'].get('weather_file', '')
            if weather_path and os.path.exists(weather_path):
                weather_file = weather_path
            elif location_name:
                # Try common locations
                for path in ["artifacts/desktop_files/weather", "weather"]:
                    candidate = os.path.join(path, f"{location_name}.epw")
                    if os.path.exists(candidate):
                        weather_file = candidate
                        break
        
        if weather_file and os.path.exists(weather_file):
            print(f"   ✅ Found: {weather_file}")
        else:
            print(f"   ⚠️  Weather file not found locally")
            print(f"   Location data suggested: {location_name or 'N/A'}")
            if data['location'].get('weather_file'):
                print(f"   Full path: {data['location'].get('weather_file')}")
            return 1
        
        # Run simulation
        print(f"\n⚙️  Running EnergyPlus simulation...")
        sim_validator = EnergyPlusSimulationValidator()
        
        result = sim_validator.validate_by_simulation(
            idf_file=idf_file,
            weather_file=weather_file,
            output_directory=output_dir,
            timeout=600  # 10 minutes
        )
        
        if result.success:
            print(f"   ✅ Simulation: SUCCESS")
            print(f"      Fatal errors: {result.fatal_errors}")
            print(f"      Severe errors: {result.severe_errors}")
            print(f"      Warnings: {result.warnings}")
            
            # Get energy results
            print(f"\n📊 ENERGY RESULTS:")
            
            # Try manual extraction first (more reliable)
            csv_file = os.path.join(output_dir, 'eplustbl.csv')
            total_kwh = 0
            eui_kbtu_ft2 = 0
            if os.path.exists(csv_file):
                try:
                    with open(csv_file, 'r') as f:
                        content = f.read()
                        lines = content.split('\n')
                        for line in lines:
                            if 'Total Site Energy' in line and ',' in line:
                                parts = line.split(',')
                                if len(parts) >= 3 and parts[1].strip() == 'Total Site Energy':
                                    try:
                                        total_gj = float(parts[2].strip())
                                        eui_mj_m2 = float(parts[3].strip()) if len(parts) >= 4 and parts[3].strip() else 0
                                        total_kwh = total_gj * 277.778
                                        if eui_mj_m2 > 0:
                                            eui_kwh_m2 = eui_mj_m2 / 3.6
                                            eui_kbtu_ft2 = eui_kwh_m2 * 0.317
                                    except:
                                        pass
                except:
                    pass
            
            # Fallback to validator method
            if total_kwh == 0:
                energy_results = sim_validator.get_energy_results(output_dir)
                if energy_results:
                    total_kwh = energy_results.get('total_site_energy_kwh', 0)
                    eui_kwh_m2 = energy_results.get('eui_kwh_m2', 0)
                    eui_kbtu_ft2 = eui_kwh_m2 * 0.317
            
            total_area = building_params['stories'] * building_params['floor_area_per_story_m2']
            
            if total_kwh > 0:
                print(f"   Total Building Area: {total_area:,.0f} m² ({total_area * 10.764:,.0f} ft²)")
                print(f"   Total Site Energy: {total_kwh:,.0f} kWh/year")
                eui_kwh_m2 = (total_kwh / total_area) if total_area > 0 else 0
                if eui_kbtu_ft2 == 0:
                    eui_kbtu_ft2 = eui_kwh_m2 * 0.317
                print(f"   EUI: {eui_kwh_m2:.1f} kWh/m²/year ({eui_kbtu_ft2:.1f} kBtu/ft²/year)")
                
                # Compare to typical
                typical_eui_office = 150  # kBtu/ft²/year for office
                diff_pct = ((eui_kbtu_ft2 - typical_eui_office) / typical_eui_office) * 100
                print(f"\n   📈 Comparison to Typical Office Building:")
                print(f"      Typical EUI: {typical_eui_office:.1f} kBtu/ft²/year")
                print(f"      Simulated EUI: {eui_kbtu_ft2:.1f} kBtu/ft²/year")
                print(f"      Difference: {diff_pct:+.1f}%")
            else:
                print(f"   ⚠️  Could not extract energy results")
                print(f"   Check: {os.path.join(output_dir, 'eplustbl.csv')}")
        else:
            print(f"   ❌ Simulation: FAILED")
            print(f"      Fatal errors: {result.fatal_errors}")
            print(f"      Severe errors: {result.severe_errors}")
            print(f"      Warnings: {result.warnings}")
            
            # Show error details
            if result.errors:
                print(f"\n   Error details:")
                for error in result.errors[:5]:
                    print(f"     [{error.severity}] {error.message}")
            
            # Check error file
            error_file = os.path.join(output_dir, 'eplusout.err')
            if os.path.exists(error_file):
                print(f"\n   Error file: {error_file}")
                with open(error_file, 'r') as f:
                    error_lines = f.readlines()
                    fatal_lines = [l for l in error_lines if 'Fatal' in l or 'Severe' in l][:10]
                    if fatal_lines:
                        print(f"   Recent errors:")
                        for line in fatal_lines:
                            print(f"     {line.strip()}")
            
            return 1
        
        print(f"\n{'='*80}")
        print("✅ SIMULATION TEST COMPLETE")
        print(f"{'='*80}")
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(test_florida_building())

