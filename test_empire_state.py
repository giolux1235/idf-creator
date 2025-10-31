#!/usr/bin/env python3
"""
Test Empire State Building with IDF Creator and EnergyPlus API
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

# EnergyPlus API endpoint
API_URL = "https://web-production-1d1be.up.railway.app/simulate"

def find_weather_file():
    """Find a weather file to use for testing"""
    common_paths = [
        "artifacts/weather/Chicago.epw",
        "/Applications/EnergyPlus-24-2-0/EnergyPlus installation files/WeatherData/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw",
        "/Applications/EnergyPlus-25-1-0/EnergyPlus installation files/WeatherData/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw",
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
        response = requests.post(api_url, json=payload, timeout=300)
        
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
        
        # Compare to known Empire State Building stats
        print("\n📊 COMPARISON TO REAL EMPIRE STATE BUILDING:")
        real_area = 257211  # m²
        real_eui_range = (150, 300)  # Typical office building range
        print(f"   Real Building Area: {real_area:,.0f} m²")
        print(f"   Simulated Area: {building_area:,.0f} m²")
        area_ratio = (building_area / real_area * 100) if real_area > 0 else 0
        print(f"   Area Match: {area_ratio:.1f}%")
        print(f"   Expected EUI Range: {real_eui_range[0]}-{real_eui_range[1]} kWh/m²/year")
        print(f"   Simulated EUI: {eui:.2f} kWh/m²/year")
        
        if real_eui_range[0] <= eui <= real_eui_range[1]:
            print(f"   ✅ EUI within realistic range!")
        else:
            print(f"   ⚠️  EUI outside expected range")
    
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
    print("\n" + "="*80)
    print("❌ ERROR DETAILS:")
    print("="*80)
    
    if result.get('error_message'):
        print("\n📝 Error Message:")
        error_lines = result.get('error_message', '').split('\n')[:50]
        for line in error_lines:
            if line.strip():
                print(f"   {line}")
    
    warnings_count = result.get('warnings_count', 0)
    if warnings_count > 0:
        print(f"\n⚠️  Warnings ({warnings_count}):")
        for warning in result.get('warnings', [])[:20]:
            print(f"   - {warning}")

def test_empire_state_building():
    """Test Empire State Building with IDF Creator"""
    print("\n" + "=" * 80)
    print("🏗️  EMPIRE STATE BUILDING TEST")
    print("=" * 80)
    
    # Create an IDF using IDF Creator
    print("\n📝 Step 1: Creating IDF with IDF Creator...")
    print("   Address: Empire State Building, 350 5th Ave, New York, NY")
    print("   Expected: ~257,000 m² total area, 102 floors")
    
    creator = IDFCreator(enhanced=True, professional=True)
    
    # Create output directory
    output_dir = Path("artifacts/desktop_files/idf")
    output_dir.mkdir(parents=True, exist_ok=True)
    test_idf_path = output_dir / "empire_state_building.idf"
    
    try:
        creator.create_idf(
            address="Empire State Building, 350 5th Ave, New York, NY",
            user_params={
                'building_type': 'office',
                'name': 'Empire State Building',
                'stories': 102,  # Empire State Building has 102 floors
                'floor_area': 257000,  # Approx 2.77M sqft = ~257k m² total
                'simple_hvac': True
            },
            output_path=str(test_idf_path)
        )
        
        print(f"✅ IDF created: {test_idf_path}")
        
        # Check file size
        file_size = os.path.getsize(test_idf_path)
        print(f"✅ File size: {file_size:,} bytes")
        
        # Read and analyze IDF
        with open(test_idf_path, 'r') as f:
            idf_lines = f.readlines()
        
        # Count zones
        zones = [line for line in idf_lines if line.startswith('Zone,')]
        print(f"✅ Zones found: {len(zones)}")
        
        # Test the generated IDF with the API
        print("\n📝 Step 2: Testing IDF with EnergyPlus API...")
        result = test_idf_with_api(str(test_idf_path))
        
        if result and result.get('simulation_status') == 'success':
            print("\n" + "=" * 80)
            print("✅ ✅ ✅ FULL TEST PASSED! ✅ ✅ ✅")
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
    success = test_empire_state_building()
    sys.exit(0 if success else 1)

