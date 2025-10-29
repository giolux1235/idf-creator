#!/usr/bin/env python3
"""
Test IDF Creator output with the EnergyPlus API
Validates that generated IDFs work correctly with real EnergyPlus simulation
"""

import sys
import os
import requests
import json
from pathlib import Path

# Add parent directory to path to import IDF Creator
sys.path.insert(0, os.path.dirname(__file__))

from main import IDFCreator

# EnergyPlus API endpoint (using the Railway API from energyplus test folder)
API_URL = "https://web-production-1d1be.up.railway.app/simulate"

def find_weather_file():
    """Find a weather file to use for testing"""
    common_paths = [
        "/Applications/EnergyPlus-24-2-0/WeatherData/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw",
        "/Applications/EnergyPlus-25-1-0/WeatherData/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw",
        "~/energyplus test/test-chicago-weather.epw",
    ]
    
    for path in common_paths:
        expanded = os.path.expanduser(path)
        if os.path.exists(expanded):
            return expanded
    
    return None

def test_idf_with_api(idf_path, api_url=API_URL):
    """
    Test an IDF file with the EnergyPlus API
    
    Args:
        idf_path: Path to IDF file
        api_url: API endpoint URL
        
    Returns:
        dict: API response with results
    """
    print(f"\n🧪 Testing IDF: {idf_path}")
    print("=" * 80)
    
    # Read IDF file
    if not os.path.exists(idf_path):
        print(f"❌ IDF file not found: {idf_path}")
        return None
    
    with open(idf_path, 'r') as f:
        idf_content = f.read()
    
    print(f"✅ IDF file read: {len(idf_content):,} bytes")
    
    # Find weather file
    weather_path = find_weather_file()
    if not weather_path:
        print("❌ Weather file not found")
        return None
    
    with open(weather_path, 'rb') as f:
        weather_content = f.read().decode('latin1')
    
    print(f"✅ Weather file read: {weather_path}")
    
    # Prepare request
    payload = {
        "idf_content": idf_content,
        "weather_content": weather_content,
    }
    
    print(f"\n🚀 Calling EnergyPlus API...")
    print(f"   URL: {api_url}")
    
    try:
        response = requests.post(api_url, json=payload, timeout=180)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('simulation_status') == 'success':
                print("\n✅ ✅ ✅ SIMULATION SUCCESSFUL! ✅ ✅ ✅")
                print_result_summary(result)
                return result
            else:
                print("\n❌ ❌ ❌ SIMULATION FAILED! ❌ ❌ ❌")
                print_errors(result)
                
                # Save detailed response for debugging
                debug_file = idf_path.replace('.idf', '_api_response.json')
                with open(debug_file, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"\n💾 Full API response saved to: {debug_file}")
                
                return result
        else:
            print(f"\n❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None
            
    except requests.exceptions.Timeout:
        print("\n❌ Request timed out")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None

def print_result_summary(result):
    """Print formatted simulation results"""
    total_energy = result.get('total_energy_consumption', 0)
    building_area = result.get('building_area', 0)
    
    print("\n📊 ENERGY RESULTS:")
    print(f"   Total Energy: {total_energy:,.0f} kWh/year")
    print(f"   Building Area: {building_area:,.2f} m²")
    
    if building_area > 0:
        eui = total_energy / building_area
        print(f"   Energy Intensity (EUI): {eui:.2f} kWh/m²/year")
    
    # Energy breakdown
    if total_energy > 0:
        print("\n📋 ENERGY BREAKDOWN:")
        print(f"   🔥 Heating:      {result.get('heating_energy', 0):>10,.0f} kWh ({result.get('heating_energy', 0)/total_energy*100:.1f}%)")
        print(f"   ❄️  Cooling:      {result.get('cooling_energy', 0):>10,.0f} kWh ({result.get('cooling_energy', 0)/total_energy*100:.1f}%)")
        print(f"   💡 Lighting:     {result.get('lighting_energy', 0):>10,.0f} kWh ({result.get('lighting_energy', 0)/total_energy*100:.1f}%)")
        print(f"   💻 Equipment:    {result.get('equipment_energy', 0):>10,.0f} kWh ({result.get('equipment_energy', 0)/total_energy*100:.1f}%)")
        print(f"   🌪️  Fans:         {result.get('fans_energy', 0):>10,.0f} kWh ({result.get('fans_energy', 0)/total_energy*100:.1f}%)")

def print_errors(result):
    """Print error messages"""
    # Print all available error fields
    print("\n" + "="*80)
    print("❌ ERROR DETAILS:")
    print("="*80)
    
    # Main error message
    if result.get('error_message'):
        print("\n📝 Error Message:")
        error_lines = result.get('error_message', '').split('\n')[:50]
        for line in error_lines:
            if line.strip():
                print(f"   {line}")
    
    # Detailed errors
    if 'detailed_errors' in result and result['detailed_errors']:
        print("\n📋 Detailed Errors:")
        for i, error in enumerate(result['detailed_errors'][:30], 1):
            print(f"   {i}. {error}")
    
    # Error file content
    if 'error_file_content' in result and result['error_file_content']:
        print("\n📄 Error File Content:")
        error_lines = result['error_file_content'].split('\n')[:100]
        for line in error_lines:
            if line.strip():
                print(f"   {line}")
    
    # Warnings
    warnings_count = result.get('warnings_count', 0)
    if warnings_count > 0:
        print(f"\n⚠️  Warnings ({warnings_count}):")
        if warnings_count <= 20:
            for warning in result.get('warnings', []):
                print(f"   - {warning}")
        else:
            for warning in result.get('warnings', [])[:20]:
                print(f"   - {warning}")
            print(f"   ... and {warnings_count - 20} more warnings")
    
    # Debug info
    print(f"\n📊 API Debug Info:")
    print(f"   Processing Time: {result.get('processing_time', 'N/A')}")
    print(f"   API Version: {result.get('version', 'N/A')}")
    print(f"   EnergyPlus Version: {result.get('energyplus_version', 'N/A')}")
    
    # Show all available keys in response for debugging
    print(f"\n🔍 Available fields in API response:")
    for key in result.keys():
        if key not in ['error_message', 'detailed_errors', 'warnings', 'warnings_count']:
            value = result[key]
            if isinstance(value, (str, int, float)):
                print(f"   {key}: {value}")
            elif isinstance(value, list):
                print(f"   {key}: list with {len(value)} items")
            elif isinstance(value, dict):
                print(f"   {key}: dict with {len(value)} keys")

def test_idf_creator():
    """Test IDF Creator with the EnergyPlus API"""
    print("\n" + "=" * 80)
    print("🏗️  IDF Creator + EnergyPlus API Integration Test")
    print("=" * 80)
    
    # Create an IDF using IDF Creator
    print("\n📝 Step 1: Creating IDF with IDF Creator...")
    
    creator = IDFCreator(enhanced=True)
    
    test_idf_path = "/Users/giovanniamenta/Desktop/tester-14-TEST.idf"
    
    try:
        creator.create_idf(
            address="Empire State Building, New York, NY",
            user_params={
                'building_type': 'Office',
                'stories': 3,
                'floor_area': 1500,
                'window_to_wall_ratio': 0.4
            },
            output_path=test_idf_path
        )
        
        print(f"✅ IDF created: {test_idf_path}")
        
        # Test the generated IDF with the API
        print("\n📝 Step 2: Testing IDF with EnergyPlus API...")
        result = test_idf_with_api(test_idf_path)
        
        if result and result.get('simulation_status') == 'success':
            print("\n" + "=" * 80)
            print("✅ ✅ ✅ FULL TEST PASSED! ✅ ✅ ✅")
            print("Your IDF Creator generates valid, simulation-ready IDF files!")
            print("=" * 80)
            return True
        else:
            print("\n" + "=" * 80)
            print("❌ Test failed - IDF has errors")
            print("=" * 80)
            return False
            
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_idf_creator()
    sys.exit(0 if success else 1)

