#!/usr/bin/env python3
"""
Test Integrated Features: Model Calibration & Retrofit Optimization
Tests the new integration into IDFCreator class
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from main import IDFCreator
from src.model_calibration import UtilityData
from src.retrofit_optimizer import UtilityRates
import subprocess

def find_weather_file():
    """Find a weather file for testing"""
    weather_dirs = [
        '/Applications/EnergyPlus-24-2-0/EnergyPlus installation files/WeatherData',
        'artifacts/desktop_files/weather',
        '.'
    ]
    
    for wdir in weather_dirs:
        if os.path.exists(wdir):
            for file in Path(wdir).glob('*.epw'):
                return str(file)
    return None

def test_integrated_calibration():
    """Test integrated calibration feature"""
    print("="*70)
    print("TEST: Integrated Model Calibration")
    print("="*70)
    
    weather_file = find_weather_file()
    if not weather_file:
        print("❌ No weather file found. Skipping test.")
        return False
    
    print(f"✅ Using weather file: {weather_file}")
    
    # Create IDF Creator
    creator = IDFCreator(professional=True)
    
    # Create utility data
    utility_data = UtilityData(
        monthly_kwh=[45000, 42000, 38000, 35000, 32000, 30000,
                     28000, 30000, 32000, 35000, 40000, 44000],
        peak_demand_kw=850,
        heating_fuel='electric',
        cooling_fuel='electric'
    )
    
    try:
        print("\n🔄 Testing create_and_calibrate_idf()...")
        result = creator.create_and_calibrate_idf(
            address="123 Main St, Chicago, IL 60601",
            utility_data=utility_data,
            weather_file=weather_file,
            user_params={'building_type': 'Office', 'stories': 5},
            tolerance=0.15,  # 15% for testing
            max_iterations=3  # Limit for testing
        )
        
        print(f"\n✅ Integrated Calibration Test: PASSED")
        print(f"   Baseline IDF: {result['baseline_idf_path']}")
        print(f"   Calibrated IDF: {result['calibrated_idf_path']}")
        return True
        
    except Exception as e:
        print(f"\n❌ Integrated Calibration Test: FAILED")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integrated_retrofit():
    """Test integrated retrofit optimization feature"""
    print("\n" + "="*70)
    print("TEST: Integrated Retrofit Optimization")
    print("="*70)
    
    weather_file = find_weather_file()
    if not weather_file:
        print("❌ No weather file found. Skipping test.")
        return False
    
    print(f"✅ Using weather file: {weather_file}")
    
    # Create IDF Creator
    creator = IDFCreator(professional=True)
    
    # Create utility rates
    utility_rates = UtilityRates(
        electricity_rate_kwh=0.12,
        demand_rate_kw=15.0,
        escalation_rate=0.03
    )
    
    try:
        print("\n🔄 Testing create_and_optimize_retrofits()...")
        result = creator.create_and_optimize_retrofits(
            address="123 Main St, Chicago, IL 60601",
            utility_rates=utility_rates,
            weather_file=weather_file,
            user_params={'building_type': 'Office', 'stories': 5},
            budget=500000,
            max_payback=10.0,
            max_measures_per_scenario=3  # Limit for testing
        )
        
        print(f"\n✅ Integrated Retrofit Test: PASSED")
        print(f"   Baseline IDF: {result['baseline_idf_path']}")
        print(f"   Scenarios generated: {len(result['scenarios'])}")
        print(f"   Optimized scenarios: {len(result['optimized_scenarios'])}")
        return True
        
    except Exception as e:
        print(f"\n❌ Integrated Retrofit Test: FAILED")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n" + "="*70)
    print("INTEGRATED FEATURES TEST")
    print("="*70)
    
    test1 = test_integrated_calibration()
    test2 = test_integrated_retrofit()
    
    print("\n" + "="*70)
    if test1 and test2:
        print("✅ ALL INTEGRATED FEATURES TESTS: PASSED")
    else:
        print("⚠️  SOME TESTS FAILED (may require valid IDF files)")
    print("="*70)
    
    sys.exit(0 if (test1 and test2) else 1)





