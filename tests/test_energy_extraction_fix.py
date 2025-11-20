#!/usr/bin/env python3
"""
Test script to verify energy extraction after SQLite fixes.
Tests the external EnergyPlus API to see if energy results are now being extracted correctly.
"""

import sys
import os
import json
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import IDFCreator

# External API URL
ENERGYPLUS_API_BASE = "https://web-production-1d1be.up.railway.app"

def test_energy_extraction():
    """Test energy extraction with a medium office building"""
    print("=" * 80)
    print("TESTING ENERGY EXTRACTION AFTER SQLITE FIXES")
    print("=" * 80)
    
    # Test case: ASHRAE Medium Office (4,645 m²)
    print("\n1. Generating IDF for Medium Office...")
    print("-" * 80)
    
    try:
        creator = IDFCreator(professional=True, enhanced=True)
        
        # Create a medium office building
        address = "123 Main St, Chicago, IL 60601"
        params = {
            'building_type': 'Office',
            'stories': 10,
            'floor_area_per_story_m2': 464.5,  # Total ~4,645 m²
            'city': 'Chicago'
        }
        
        # Generate IDF
        idf_path = creator.create_idf(
            address=address,
            user_params=params,
            output_path="test_outputs/medium_office_test.idf"
        )
        
        print(f"✅ IDF generated: {idf_path}")
        
        # Check if Output:SQLite is in the IDF
        with open(idf_path, 'r') as f:
            idf_content = f.read()
        
        if 'Output:SQLite' in idf_content:
            print("✅ Output:SQLite found in IDF file")
        else:
            print("❌ Output:SQLite NOT found in IDF file")
            return
        
        print("\n2. Sending to EnergyPlus API...")
        print("-" * 80)
        
        # Read IDF file
        with open(idf_path, 'r') as f:
            idf_content = f.read()
        
        # Send to external API
        api_url = f"{ENERGYPLUS_API_BASE}/simulate"
        print(f"   API URL: {api_url}")
        
        files = {
            'idf_file': ('test_building.idf', idf_content, 'text/plain')
        }
        
        response = requests.post(api_url, files=files, timeout=300)
        
        if response.status_code != 200:
            print(f"❌ API returned status {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return
        
        result = response.json()
        
        print("\n3. Analyzing Results...")
        print("-" * 80)
        
        # Check simulation status
        sim_status = result.get('simulation_status', 'unknown')
        print(f"   Simulation Status: {sim_status}")
        
        if sim_status != 'success':
            print(f"❌ Simulation failed: {result.get('error_message', 'Unknown error')}")
            return
        
        # Check for energy results
        energy_results = result.get('energy_results', {})
        
        if not energy_results:
            print("❌ No energy_results in API response")
            print(f"   Available keys: {list(result.keys())}")
            return
        
        print("\n4. Energy Results:")
        print("-" * 80)
        
        # Extract method
        extraction_method = energy_results.get('extraction_method', 'unknown')
        print(f"   Extraction Method: {extraction_method}")
        
        if extraction_method == 'standard':
            print("   ⚠️  Using CSV/HTML extraction (not SQLite)")
        elif extraction_method == 'sqlite':
            print("   ✅ Using SQLite extraction")
        else:
            print("   ⚠️  Extraction method not specified")
        
        # Energy values
        total_energy = energy_results.get('total_site_energy_kwh', 0)
        building_area = energy_results.get('building_area_m2', 0)
        eui = energy_results.get('eui_kwh_m2', 0)
        
        print(f"\n   Total Site Energy: {total_energy:,.2f} kWh")
        print(f"   Building Area: {building_area:,.2f} m²")
        print(f"   EUI: {eui:.2f} kWh/m²")
        
        # Expected values for medium office
        expected_eui_min = 20.0
        expected_eui_max = 28.0
        expected_energy_min = 90_000
        expected_energy_max = 130_000
        
        print("\n5. Validation:")
        print("-" * 80)
        
        # Check if values are reasonable
        if total_energy < expected_energy_min:
            print(f"   ❌ Energy too low: {total_energy:,.0f} kWh (expected {expected_energy_min:,}-{expected_energy_max:,} kWh)")
            print(f"      This is {((expected_energy_min - total_energy) / expected_energy_min * 100):.1f}% below expected minimum")
        elif total_energy > expected_energy_max:
            print(f"   ⚠️  Energy higher than expected: {total_energy:,.0f} kWh (expected {expected_energy_min:,}-{expected_energy_max:,} kWh)")
        else:
            print(f"   ✅ Energy within expected range: {total_energy:,.0f} kWh")
        
        if eui < expected_eui_min:
            print(f"   ❌ EUI too low: {eui:.2f} kWh/m² (expected {expected_eui_min}-{expected_eui_max} kWh/m²)")
        elif eui > expected_eui_max:
            print(f"   ⚠️  EUI higher than expected: {eui:.2f} kWh/m² (expected {expected_eui_min}-{expected_eui_max} kWh/m²)")
        else:
            print(f"   ✅ EUI within expected range: {eui:.2f} kWh/m²")
        
        # Check if SQLite extraction was used
        if extraction_method != 'sqlite' and total_energy < expected_energy_min:
            print(f"\n   ⚠️  SQLite extraction not being used - this may be why values are low")
            print(f"      Extraction method: {extraction_method}")
        
        # Save full results
        output_file = Path("test_outputs") / "energy_extraction_test_results.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n📄 Full results saved to: {output_file}")
        
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        # Final verdict
        if extraction_method == 'sqlite' and expected_energy_min <= total_energy <= expected_energy_max:
            print("✅ SUCCESS: SQLite extraction working and values are reasonable!")
        elif extraction_method == 'sqlite':
            print("⚠️  PARTIAL: SQLite extraction working but values need verification")
        elif total_energy < expected_energy_min:
            print("❌ FAILED: Energy values too low - SQLite extraction may not be working")
        else:
            print("⚠️  UNKNOWN: Need more investigation")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    test_energy_extraction()



