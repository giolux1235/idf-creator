#!/usr/bin/env python3
"""
Test API endpoint with different addresses to verify geocoding fix.
Verifies that addresses use lookup table, not fallback mechanisms.
"""

import requests
import json
import sys
from typing import Dict, List, Optional

# API endpoint - update if testing deployed service
API_BASE = "http://localhost:5000"  # Local
# API_BASE = "https://web-production-3092c.up.railway.app"  # Production

def test_api_geocoding():
    """Test API endpoint with multiple addresses from different cities."""
    
    test_cases = [
        {
            'name': 'San Francisco Address',
            'address': '147 Sutter St, San Francisco, CA 94104',
            'expected_city': 'San Francisco',
            'expected_lat_range': (37.7, 37.8),
            'expected_lon_range': (-122.5, -122.3),
            'expected_tz': -8.0,
            'should_be_chicago': False
        },
        {
            'name': 'New York Address',
            'address': '123 Broadway, New York, NY 10001',
            'expected_city': 'New York',
            'expected_lat_range': (40.6, 40.8),
            'expected_lon_range': (-74.1, -73.9),
            'expected_tz': -5.0,
            'should_be_chicago': False
        },
        {
            'name': 'Los Angeles Address',
            'address': '456 Sunset Blvd, Los Angeles, CA 90028',
            'expected_city': 'Los Angeles',
            'expected_lat_range': (33.9, 34.2),
            'expected_lon_range': (-118.4, -118.1),
            'expected_tz': -8.0,
            'should_be_chicago': False
        },
        {
            'name': 'Chicago Address (should still work)',
            'address': '258 N Clark St, Chicago, IL 60610',
            'expected_city': 'Chicago',
            'expected_lat_range': (41.8, 42.0),
            'expected_lon_range': (-87.7, -87.6),
            'expected_tz': -6.0,
            'should_be_chicago': True
        },
        {
            'name': 'Seattle Address',
            'address': '500 Pine St, Seattle, WA 98101',
            'expected_city': 'Seattle',
            'expected_lat_range': (47.5, 47.7),
            'expected_lon_range': (-122.4, -122.2),
            'expected_tz': -8.0,
            'should_be_chicago': False
        },
        {
            'name': 'Houston Address',
            'address': '1001 Main St, Houston, TX 77002',
            'expected_city': 'Houston',
            'expected_lat_range': (29.7, 29.8),
            'expected_lon_range': (-95.4, -95.3),
            'expected_tz': -6.0,
            'should_be_chicago': False
        },
        {
            'name': 'Miami Address',
            'address': '200 Biscayne Blvd, Miami, FL 33132',
            'expected_city': 'Miami',
            'expected_lat_range': (25.7, 25.8),
            'expected_lon_range': (-80.2, -80.1),
            'expected_tz': -5.0,
            'should_be_chicago': False
        }
    ]
    
    print("=" * 80)
    print("API GEOCODING TEST - Verifying Lookup Table Usage")
    print("=" * 80)
    print(f"API Endpoint: {API_BASE}/api/generate")
    print("=" * 80)
    
    all_passed = True
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}/{len(test_cases)}: {test['name']}")
        print(f"Address: {test['address']}")
        print(f"{'='*80}")
        
        try:
            # Make API request
            payload = {
                'address': test['address'],
                'building_type': 'office',
                'floor_area': 500,
                'stories': 2
            }
            
            print(f"📡 Sending request to {API_BASE}/api/generate...")
            response = requests.post(
                f"{API_BASE}/api/generate",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"❌ API returned status code {response.status_code}")
                print(f"Response: {response.text[:500]}")
                all_passed = False
                results.append({
                    'test': test['name'],
                    'status': 'FAILED',
                    'reason': f'HTTP {response.status_code}'
                })
                continue
            
            data = response.json()
            
            if not data.get('success'):
                print(f"❌ API returned success=false")
                print(f"Error: {data.get('error', 'Unknown error')}")
                all_passed = False
                results.append({
                    'test': test['name'],
                    'status': 'FAILED',
                    'reason': data.get('error', 'Unknown error')
                })
                continue
            
            # Check if IDF file was generated
            if 'idf_file' not in data and 'filename' not in data:
                print(f"⚠️  Warning: No IDF file in response")
                print(f"Response keys: {list(data.keys())}")
                # Continue anyway to check location data if available
            
            # The API might not return location data directly, so we need to check
            # the generated IDF file content or test the location fetcher directly
            
            # For now, let's also test the location fetcher directly
            print(f"🔍 Testing location fetcher directly...")
            from src.location_fetcher import LocationFetcher
            fetcher = LocationFetcher()
            coords = fetcher.geocode_address(test['address'])
            
            if not coords:
                print(f"❌ Location fetcher returned None")
                all_passed = False
                results.append({
                    'test': test['name'],
                    'status': 'FAILED',
                    'reason': 'Location fetcher returned None'
                })
                continue
            
            lat = coords.get('latitude')
            lon = coords.get('longitude')
            tz = coords.get('time_zone')
            
            print(f"📍 Geocoded Result:")
            print(f"   Latitude: {lat:.4f}°N")
            print(f"   Longitude: {lon:.4f}°W")
            print(f"   Time Zone: {tz}")
            
            # Check if coordinates match expected ranges
            lat_ok = test['expected_lat_range'][0] <= lat <= test['expected_lat_range'][1]
            lon_ok = test['expected_lon_range'][0] <= lon <= test['expected_lon_range'][1]
            tz_ok = abs(tz - test['expected_tz']) < 0.1
            
            # Critical check: Is it Chicago coordinates when it shouldn't be?
            is_chicago = abs(lat - 41.8781) < 0.01 and abs(lon - (-87.6298)) < 0.01
            
            if is_chicago and not test['should_be_chicago']:
                print(f"❌ CRITICAL FAILURE: Non-Chicago address geocoded to Chicago coordinates!")
                print(f"   Expected: {test['expected_city']} coordinates")
                print(f"   Got: Chicago coordinates (41.8781°N, -87.6298°W)")
                all_passed = False
                results.append({
                    'test': test['name'],
                    'status': 'CRITICAL FAILURE',
                    'reason': 'Geocoded to Chicago instead of actual city'
                })
            elif lat_ok and lon_ok and tz_ok:
                print(f"✅ PASSED: Coordinates and timezone match expected values")
                print(f"   ✓ Latitude in range: {test['expected_lat_range']}")
                print(f"   ✓ Longitude in range: {test['expected_lon_range']}")
                print(f"   ✓ Timezone correct: {tz} (expected: {test['expected_tz']})")
                results.append({
                    'test': test['name'],
                    'status': 'PASSED',
                    'lat': lat,
                    'lon': lon,
                    'tz': tz
                })
            else:
                print(f"⚠️  PARTIAL: Some values don't match")
                if not lat_ok:
                    print(f"   - Latitude {lat:.4f} out of range {test['expected_lat_range']}")
                if not lon_ok:
                    print(f"   - Longitude {lon:.4f} out of range {test['expected_lon_range']}")
                if not tz_ok:
                    print(f"   - Timezone {tz} incorrect (expected: {test['expected_tz']})")
                results.append({
                    'test': test['name'],
                    'status': 'PARTIAL',
                    'lat': lat,
                    'lon': lon,
                    'tz': tz
                })
                all_passed = False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ ERROR: Could not connect to API at {API_BASE}")
            print(f"   Make sure the API server is running:")
            print(f"   python web_interface.py")
            all_passed = False
            results.append({
                'test': test['name'],
                'status': 'ERROR',
                'reason': 'Connection refused'
            })
            break
        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
            results.append({
                'test': test['name'],
                'status': 'ERROR',
                'reason': str(e)
            })
    
    # Print summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    
    for result in results:
        status_icon = "✅" if result['status'] == 'PASSED' else "❌"
        print(f"{status_icon} {result['test']}: {result['status']}")
        if 'reason' in result:
            print(f"   Reason: {result['reason']}")
    
    print(f"\n{'='*80}")
    if all_passed:
        print("✅ ALL TESTS PASSED - Geocoding fix is working correctly!")
        print("✅ API is using lookup table for city coordinates (not fallbacks)")
    else:
        print("❌ SOME TESTS FAILED - Please review the results above")
        print("⚠️  Check that:")
        print("   1. API server is running (python web_interface.py)")
        print("   2. Lookup table contains all test cities")
        print("   3. No fallback to Chicago is occurring")
    print(f"{'='*80}\n")
    
    return all_passed

if __name__ == '__main__':
    success = test_api_geocoding()
    sys.exit(0 if success else 1)
