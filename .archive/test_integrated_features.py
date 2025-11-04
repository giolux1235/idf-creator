#!/usr/bin/env python3
"""
Test Integrated IDF Features (Economizers, Daylighting, Advanced Setpoints)
"""
import os
import sys
from pathlib import Path

from main import IDFCreator
from src.validation.simulation_validator import EnergyPlusSimulationValidator
from src.validation.idf_validator import IDFValidator


def check_idf_features(idf_content: str) -> dict:
    """Check which advanced features are present in IDF"""
    features = {
        'economizer': False,
        'daylighting': False,
        'outdoor_air_reset': False,
        'internal_mass': False,
        'energy_recovery': False
    }
    
    # Check for economizer
    if 'Controller:OutdoorAir' in idf_content:
        features['economizer'] = True
    
    # Check for daylighting
    if 'Daylighting:Controls' in idf_content:
        features['daylighting'] = True
    
    # Check for outdoor air reset setpoint manager
    if 'SetpointManager:OutdoorAirReset' in idf_content:
        features['outdoor_air_reset'] = True
    
    # Check for internal mass
    if 'InternalMass' in idf_content:
        features['internal_mass'] = True
    
    # Check for energy recovery
    if 'HeatExchanger:AirToAir' in idf_content:
        features['energy_recovery'] = True
    
    return features


def test_integration(address: str, building_params: dict = None):
    """Test IDF generation with integrated features"""
    print("="*80)
    print("TESTING INTEGRATED IDF FEATURES")
    print("="*80)
    
    if building_params is None:
        building_params = {
            'building_type': 'Office',
            'stories': 3,
            'floor_area_per_story_m2': 1000
        }
    
    # Create IDF
    creator = IDFCreator(professional=True, enhanced=True)
    
    print(f"\n📝 Generating IDF for: {address}")
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
        
        if errors == 0:
            print(f"   ✅ IDF Validation: PASSED")
        else:
            print(f"   ❌ IDF Validation: FAILED")
            print(f"\n   Error details:")
            for error in validation_results.get('errors', [])[:5]:
                print(f"     - {error}")
    else:
        print(f"   ⚠️  Validation returned no results")
    
    # Save IDF
    output_dir = "artifacts/desktop_files/simulation/integration_test"
    os.makedirs(output_dir, exist_ok=True)
    idf_file = os.path.join(output_dir, "test_integrated.idf")
    
    with open(idf_file, 'w') as f:
        f.write(idf_content)
    
    print(f"\n💾 IDF saved: {idf_file}")
    
    # Try to run simulation if EnergyPlus is available
    print(f"\n⚙️  Attempting EnergyPlus simulation...")
    sim_validator = EnergyPlusSimulationValidator()
    
    # Find weather file
    weather_file = None
    weather_file_name = data['location'].get('weather_file_name')
    if weather_file_name:
        for path in ["artifacts/desktop_files/weather", "weather"]:
            candidate = os.path.join(path, weather_file_name)
            if os.path.exists(candidate):
                weather_file = candidate
                break
    
    if weather_file:
        print(f"   Using weather file: {weather_file}")
        result = sim_validator.validate_by_simulation(
            idf_file=idf_file,
            weather_file=weather_file,
            output_directory=output_dir,
            timeout=300
        )
        
        if result.success:
            print(f"   ✅ Simulation: SUCCESS")
            print(f"      Warnings: {result.warnings}")
            
            # Get energy results
            energy_results = sim_validator.get_energy_results(output_dir)
            if energy_results:
                eui = energy_results.get('eui_kbtu_ft2', 0)
                total_kwh = energy_results.get('total_energy_kwh', 0)
                print(f"\n📊 ENERGY RESULTS:")
                print(f"   Total Energy: {total_kwh:,.0f} kWh/year")
                print(f"   EUI: {eui:.1f} kBtu/ft²/year")
        else:
            print(f"   ❌ Simulation: FAILED")
            print(f"      Fatal errors: {result.fatal_errors}")
            print(f"      Severe errors: {result.severe_errors}")
    else:
        print(f"   ⚠️  Weather file not found, skipping simulation")
    
    return {
        'features': features,
        'idf_file': idf_file,
        'validation': validation_results
    }


def main():
    """Run integration test"""
    print("Testing Integrated Features...")
    
    # Test with a simple office building
    result = test_integration(
        "123 Main St, San Francisco, CA",
        {
            'building_type': 'Office',
            'stories': 3,
            'floor_area_per_story_m2': 1000
        }
    )
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"\nFeatures Integrated:")
    for feature, present in result['features'].items():
        print(f"   {'✅' if present else '❌'} {feature.replace('_', ' ').title()}")
    
    # Expected features
    expected = ['economizer', 'daylighting', 'outdoor_air_reset']
    missing = [f for f in expected if not result['features'].get(f, False)]
    
    if missing:
        print(f"\n⚠️  Missing expected features: {', '.join(missing)}")
    else:
        print(f"\n✅ All expected features integrated!")
    
    return 0 if len(missing) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())



