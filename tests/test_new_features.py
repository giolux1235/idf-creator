#!/usr/bin/env python3
"""
Test new features (economizers, daylighting, setpoints, internal mass)
with real addresses and weather files.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import IDFCreator

# Test addresses we HAVEN'T used before (different from Willis Tower, Empire State, etc.)
TEST_ADDRESSES = [
    {
        'name': 'One World Trade Center',
        'address': '285 Fulton St, New York, NY 10007',
        'params': {'stories': 94, 'floor_area_per_story_m2': 2000, 'building_type': 'Office'}
    },
    {
        'name': 'Transamerica Pyramid',
        'address': '600 Montgomery St, San Francisco, CA 94111',
        'params': {'stories': 48, 'floor_area_per_story_m2': 1800, 'building_type': 'Office'}
    },
    {
        'name': 'Space Needle',
        'address': '400 Broad St, Seattle, WA 98109',
        'params': {'stories': 6, 'floor_area_per_story_m2': 500, 'building_type': 'Office'}
    },
    {
        'name': 'John Hancock Center',
        'address': '875 N Michigan Ave, Chicago, IL 60611',
        'params': {'stories': 100, 'floor_area_per_story_m2': 1200, 'building_type': 'Office'}
    },
    {
        'name': 'Miami Tower',
        'address': '100 SE 2nd St, Miami, FL 33131',
        'params': {'stories': 47, 'floor_area_per_story_m2': 1500, 'building_type': 'Office'}
    },
    {
        'name': 'Bank of America Tower (Seattle)',
        'address': '800 5th Ave, Seattle, WA 98104',
        'params': {'stories': 44, 'floor_area_per_story_m2': 1600, 'building_type': 'Office'}
    },
    {
        'name': 'Boston City Hall',
        'address': '1 City Hall Square, Boston, MA 02201',
        'params': {'stories': 9, 'floor_area_per_story_m2': 2500, 'building_type': 'Office'}
    },
    {
        'name': 'US Bank Tower (LA)',
        'address': '633 West 5th Street, Los Angeles, CA 90071',
        'params': {'stories': 73, 'floor_area_per_story_m2': 1800, 'building_type': 'Office'}
    }
]

def check_idf_features(idf_path: str) -> Dict[str, bool]:
    """Check if IDF contains new features"""
    features = {
        'economizer': False,
        'daylighting': False,
        'advanced_setpoint': False,
        'internal_mass': False
    }
    
    try:
        with open(idf_path, 'r') as f:
            content = f.read()
        
        # Check for economizer
        if 'Controller:OutdoorAir' in content:
            # Check if it's not NoEconomizer
            if 'DifferentialDryBulb' in content or 'FixedDryBulb' in content:
                features['economizer'] = True
        
        # Check for daylighting
        if 'Daylighting:Controls' in content and 'Daylighting:ReferencePoint' in content:
            features['daylighting'] = True
        
        # Check for advanced setpoint manager
        if 'SetpointManager:OutdoorAirReset' in content:
            features['advanced_setpoint'] = True
        
        # Check for internal mass
        if 'InternalMass' in content:
            features['internal_mass'] = True
        
    except Exception as e:
        print(f"  ⚠️  Error checking IDF: {e}")
    
    return features

def test_address(address_info: Dict) -> Dict:
    """Test a single address"""
    name = address_info['name']
    address = address_info['address']
    params = address_info['params']
    
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"Address: {address}")
    print(f"{'='*70}")
    
    result = {
        'name': name,
        'address': address,
        'success': False,
        'features': {},
        'errors': [],
        'idf_path': None
    }
    
    try:
        # Create IDF
        creator = IDFCreator(professional=True)
        output_path = f"artifacts/desktop_files/idf/test_{name.lower().replace(' ', '_').replace('(', '').replace(')', '')}.idf"
        
        idf_path = creator.create_idf(
            address=address,
            user_params=params,
            output_path=output_path
        )
        
        result['idf_path'] = idf_path
        result['success'] = True
        
        # Check features
        result['features'] = check_idf_features(idf_path)
        
        # Print results
        print(f"\n✅ IDF Generated: {idf_path}")
        print(f"   Features Found:")
        for feature, found in result['features'].items():
            status = "✅" if found else "❌"
            print(f"     {status} {feature}: {found}")
        
    except Exception as e:
        result['errors'].append(str(e))
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    return result

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("TESTING NEW FEATURES WITH REAL ADDRESSES")
    print("="*70)
    print("\nTesting: Economizers, Daylighting, Advanced Setpoints, Internal Mass")
    
    # Ensure output directory exists
    Path("artifacts/desktop_files/idf").mkdir(parents=True, exist_ok=True)
    
    results = []
    for address_info in TEST_ADDRESSES:
        result = test_address(address_info)
        results.append(result)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    successful = sum(1 for r in results if r['success'])
    print(f"\n✅ Successful: {successful}/{len(results)}")
    
    # Feature counts
    feature_counts = {
        'economizer': sum(1 for r in results if r.get('features', {}).get('economizer')),
        'daylighting': sum(1 for r in results if r.get('features', {}).get('daylighting')),
        'advanced_setpoint': sum(1 for r in results if r.get('features', {}).get('advanced_setpoint')),
        'internal_mass': sum(1 for r in results if r.get('features', {}).get('internal_mass'))
    }
    
    print(f"\nFeatures Found:")
    for feature, count in feature_counts.items():
        percentage = (count / successful * 100) if successful > 0 else 0
        print(f"  {feature}: {count}/{successful} ({percentage:.0f}%)")
    
    # Errors
    errors = [r for r in results if r['errors']]
    if errors:
        print(f"\n❌ Errors Found: {len(errors)}")
        for r in errors:
            print(f"  {r['name']}: {r['errors']}")
    
    # Issues/Oddities
    print(f"\n⚠️  Checking for Issues/Oddities:")
    
    # Check if economizers are missing
    missing_economizer = [r for r in results if r['success'] and not r.get('features', {}).get('economizer')]
    if missing_economizer:
        print(f"  ⚠️  Economizers missing in {len(missing_economizer)} IDFs:")
        for r in missing_economizer:
            print(f"     - {r['name']}")
    
    # Check if daylighting is missing
    missing_daylighting = [r for r in results if r['success'] and not r.get('features', {}).get('daylighting')]
    if missing_daylighting:
        print(f"  ⚠️  Daylighting missing in {len(missing_daylighting)} IDFs:")
        for r in missing_daylighting:
            print(f"     - {r['name']}")
    
    # Check if advanced setpoints are missing
    missing_setpoint = [r for r in results if r['success'] and not r.get('features', {}).get('advanced_setpoint')]
    if missing_setpoint:
        print(f"  ⚠️  Advanced setpoints missing in {len(missing_setpoint)} IDFs:")
        for r in missing_setpoint:
            print(f"     - {r['name']}")
    
    # Check if internal mass is missing
    missing_mass = [r for r in results if r['success'] and not r.get('features', {}).get('internal_mass')]
    if missing_mass:
        print(f"  ⚠️  Internal mass missing in {len(missing_mass)} IDFs:")
        for r in missing_mass:
            print(f"     - {r['name']}")
    
    print("\n" + "="*70)
    print("TESTING COMPLETE")
    print("="*70 + "\n")
    
    return results

if __name__ == "__main__":
    results = main()

