#!/usr/bin/env python3
"""
Test to verify lookup table is being used (not fallback mechanisms).
Captures console output to verify "✅ Found city in lookup table" messages.
"""

import sys
import io
from contextlib import redirect_stdout
from src.location_fetcher import LocationFetcher

def test_lookup_table_usage():
    """Test that addresses use lookup table, not fallbacks."""
    
    test_addresses = [
        '147 Sutter St, San Francisco, CA 94104',
        '123 Broadway, New York, NY 10001',
        '456 Sunset Blvd, Los Angeles, CA 90028',
        '500 Pine St, Seattle, WA 98101',
        '1001 Main St, Houston, TX 77002',
        '200 Biscayne Blvd, Miami, FL 33132',
        '258 N Clark St, Chicago, IL 60610'
    ]
    
    print("=" * 80)
    print("LOOKUP TABLE USAGE VERIFICATION")
    print("=" * 80)
    print("Testing that addresses use lookup table (not fallback mechanisms)")
    print("=" * 80)
    
    fetcher = LocationFetcher()
    all_using_lookup = True
    results = []
    
    for address in test_addresses:
        print(f"\n{'='*80}")
        print(f"Testing: {address}")
        print(f"{'='*80}")
        
        # Capture stdout to check for lookup table messages
        f = io.StringIO()
        with redirect_stdout(f):
            coords = fetcher.geocode_address(address)
        output = f.getvalue()
        
        # Check if lookup table was used
        using_lookup = "Found city in lookup table" in output or "✅ Found city in lookup table" in output
        using_fallback = "fallback" in output.lower() or "Chicago default" in output or "WARNING" in output
        
        if coords:
            lat = coords.get('latitude', 0)
            lon = coords.get('longitude', 0)
            tz = coords.get('time_zone', 0)
            
            # Check if it's Chicago when it shouldn't be
            is_chicago = abs(lat - 41.8781) < 0.01 and abs(lon - (-87.6298)) < 0.01
            should_be_chicago = 'Chicago' in address
            
            print(f"📍 Result: {lat:.4f}°N, {lon:.4f}°W, TZ: {tz}")
            
            if using_lookup:
                print(f"✅ Using lookup table (CORRECT)")
                results.append({
                    'address': address,
                    'status': 'PASS',
                    'method': 'lookup_table',
                    'coords': (lat, lon)
                })
            elif using_fallback and not should_be_chicago:
                print(f"❌ Using fallback (WRONG - should use lookup table)")
                all_using_lookup = False
                results.append({
                    'address': address,
                    'status': 'FAIL',
                    'method': 'fallback',
                    'coords': (lat, lon)
                })
            elif is_chicago and not should_be_chicago:
                print(f"❌ CRITICAL: Geocoded to Chicago coordinates!")
                all_using_lookup = False
                results.append({
                    'address': address,
                    'status': 'CRITICAL_FAIL',
                    'method': 'chicago_fallback',
                    'coords': (lat, lon)
                })
            else:
                print(f"⚠️  Using geocoding API (not ideal, but acceptable)")
                results.append({
                    'address': address,
                    'status': 'PARTIAL',
                    'method': 'api',
                    'coords': (lat, lon)
                })
        else:
            print(f"❌ Failed to geocode")
            all_using_lookup = False
            results.append({
                'address': address,
                'status': 'FAIL',
                'method': 'none',
                'coords': None
            })
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    lookup_count = sum(1 for r in results if r['method'] == 'lookup_table')
    fallback_count = sum(1 for r in results if 'fallback' in r['method'])
    api_count = sum(1 for r in results if r['method'] == 'api')
    
    print(f"✅ Using lookup table: {lookup_count}/{len(test_addresses)}")
    print(f"⚠️  Using geocoding API: {api_count}/{len(test_addresses)}")
    print(f"❌ Using fallback: {fallback_count}/{len(test_addresses)}")
    
    print(f"\nDetailed Results:")
    for result in results:
        icon = "✅" if result['status'] == 'PASS' else "❌"
        print(f"  {icon} {result['address']}")
        print(f"     Method: {result['method']}")
        if result['coords']:
            print(f"     Coords: {result['coords'][0]:.4f}°N, {result['coords'][1]:.4f}°W")
    
    print(f"\n{'='*80}")
    if all_using_lookup and lookup_count == len(test_addresses):
        print("✅ PERFECT: All addresses using lookup table (no fallbacks)")
    elif all_using_lookup:
        print("✅ GOOD: No fallbacks to Chicago detected")
        print(f"⚠️  Note: {api_count} addresses used geocoding API instead of lookup")
    else:
        print("❌ FAILED: Some addresses are using fallback mechanisms")
    print(f"{'='*80}\n")
    
    return all_using_lookup and fallback_count == 0

if __name__ == '__main__':
    success = test_lookup_table_usage()
    sys.exit(0 if success else 1)
