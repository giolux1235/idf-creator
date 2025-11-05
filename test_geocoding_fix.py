#!/usr/bin/env python3
"""Test script to verify geocoding fix for different cities."""

import sys
from src.location_fetcher import LocationFetcher

def test_geocoding():
    """Test geocoding for multiple cities."""
    fetcher = LocationFetcher()
    
    test_cases = [
        {
            'address': '147 Sutter St, San Francisco, CA 94104',
            'expected_city': 'San Francisco, CA',
            'expected_lat_range': (37.5, 38.0),
            'expected_lon_range': (-122.5, -122.3),
            'expected_tz': -8.0
        },
        {
            'address': '123 Broadway, New York, NY 10001',
            'expected_city': 'New York, NY',
            'expected_lat_range': (40.5, 41.0),
            'expected_lon_range': (-74.1, -73.9),
            'expected_tz': -5.0
        },
        {
            'address': '456 Sunset Blvd, Los Angeles, CA 90028',
            'expected_city': 'Los Angeles, CA',
            'expected_lat_range': (33.8, 34.3),
            'expected_lon_range': (-118.4, -118.1),
            'expected_tz': -8.0
        },
        {
            'address': '258 N Clark St, Chicago, IL 60610',
            'expected_city': 'Chicago, IL',
            'expected_lat_range': (41.8, 42.0),
            'expected_lon_range': (-87.7, -87.6),
            'expected_tz': -6.0
        },
        {
            'address': '369 E Lake St, Chicago, IL 60601',
            'expected_city': 'Chicago, IL',
            'expected_lat_range': (41.8, 42.0),
            'expected_lon_range': (-87.7, -87.6),
            'expected_tz': -6.0
        }
    ]
    
    print("=" * 80)
    print("GEOCODING FIX VERIFICATION TEST")
    print("=" * 80)
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}: {test['address']}")
        print(f"Expected City: {test['expected_city']}")
        print(f"{'='*80}")
        
        try:
            coords = fetcher.geocode_address(test['address'])
            
            if not coords:
                print(f"❌ FAILED: geocode_address returned None")
                all_passed = False
                continue
            
            lat = coords.get('latitude')
            lon = coords.get('longitude')
            tz = coords.get('time_zone')
            elevation = coords.get('elevation')
            
            print(f"Result:")
            print(f"  Latitude: {lat:.4f}°N (expected range: {test['expected_lat_range']})")
            print(f"  Longitude: {lon:.4f}°W (expected range: {test['expected_lon_range']})")
            print(f"  Time Zone: {tz} (expected: {test['expected_tz']})")
            print(f"  Elevation: {elevation}m")
            
            # Check if coordinates are in expected range
            lat_ok = test['expected_lat_range'][0] <= lat <= test['expected_lat_range'][1]
            lon_ok = test['expected_lon_range'][0] <= lon <= test['expected_lon_range'][1]
            tz_ok = tz == test['expected_tz']
            
            # Check if it's NOT Chicago coordinates (unless it's a Chicago address)
            is_chicago = abs(lat - 41.8781) < 0.01 and abs(lon - (-87.6298)) < 0.01
            should_be_chicago = 'Chicago' in test['address']
            
            if is_chicago and not should_be_chicago:
                print(f"❌ CRITICAL FAILURE: Non-Chicago address geocoded to Chicago coordinates!")
                all_passed = False
            elif lat_ok and lon_ok and tz_ok:
                print(f"✅ PASSED: Coordinates and timezone match expected values")
            else:
                print(f"⚠️  WARNING: Some values don't match expected ranges")
                if not lat_ok:
                    print(f"   - Latitude out of range")
                if not lon_ok:
                    print(f"   - Longitude out of range")
                if not tz_ok:
                    print(f"   - Timezone incorrect")
                all_passed = False
                
        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {e}")
            all_passed = False
    
    print(f"\n{'='*80}")
    if all_passed:
        print("✅ ALL TESTS PASSED - Geocoding fix is working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Please review the results above")
    print(f"{'='*80}\n")
    
    return all_passed

if __name__ == '__main__':
    success = test_geocoding()
    sys.exit(0 if success else 1)


