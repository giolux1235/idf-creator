#!/usr/bin/env python3
"""Diagnostic script to test geocoding and identify why it might be failing."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from geopy.geocoders import Nominatim
import ssl
import certifi
import time
from typing import Optional, Dict

def test_geocoding():
    """Test geocoding with various addresses and configurations."""
    
    test_addresses = [
        "123 N Michigan Ave, Chicago, IL 60601",
        "Chicago, IL",
        "258 N Clark St, Chicago, IL 60610",
        "369 E Lake St, Chicago, IL 60601",
    ]
    
    print("=" * 60)
    print("Geocoding Diagnostic Test")
    print("=" * 60)
    
    # Test 1: Basic Nominatim setup
    print("\n1. Testing Nominatim Setup...")
    try:
        ctx = ssl.create_default_context(cafile=certifi.where())
        geolocator = Nominatim(user_agent="idf_creator_test", scheme='https', ssl_context=ctx)
        print("✓ Nominatim geolocator created successfully")
    except Exception as e:
        print(f"❌ Failed to create Nominatim geolocator: {e}")
        return
    
    # Test 2: Test each address
    print("\n2. Testing Geocoding for Each Address...")
    for i, address in enumerate(test_addresses, 1):
        print(f"\n  Test {i}: {address}")
        try:
            # Add delay to respect rate limits (1 req/sec)
            if i > 1:
                print("    Waiting 1.5 seconds (rate limit)...")
                time.sleep(1.5)
            
            location = geolocator.geocode(address, timeout=15)
            
            if location:
                print(f"    ✓ Success!")
                print(f"    - Latitude: {location.latitude:.6f}")
                print(f"    - Longitude: {location.longitude:.6f}")
                print(f"    - Address: {location.address}")
                
                # Validate coordinates
                if location.longitude > 0:
                    print(f"    ⚠️  WARNING: Positive longitude (likely wrong for US address)")
                if location.latitude < 20 or location.latitude > 55:
                    print(f"    ⚠️  WARNING: Latitude out of typical US range")
            else:
                print(f"    ❌ No results returned")
                
        except Exception as e:
            print(f"    ❌ Error: {type(e).__name__}: {e}")
    
    # Test 3: Test with different user agents
    print("\n3. Testing Different User Agents...")
    user_agents = [
        "idf_creator_test",
        "IDF-Creator-Service/1.0",
        "Mozilla/5.0 (compatible; IDF-Creator/1.0)",
    ]
    
    test_addr = "Chicago, IL"
    for ua in user_agents:
        try:
            print(f"\n  Testing with user agent: {ua}")
            geolocator_ua = Nominatim(user_agent=ua, scheme='https', ssl_context=ctx)
            time.sleep(1.5)  # Rate limit
            location = geolocator_ua.geocode(test_addr, timeout=15)
            if location:
                print(f"    ✓ Success: {location.latitude:.4f}, {location.longitude:.4f}")
            else:
                print(f"    ❌ No results")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Test 4: Test network connectivity
    print("\n4. Testing Network Connectivity...")
    try:
        import requests
        response = requests.get("https://nominatim.openstreetmap.org", timeout=10)
        print(f"    ✓ Nominatim server reachable (status: {response.status_code})")
    except Exception as e:
        print(f"    ❌ Cannot reach Nominatim server: {e}")
    
    # Test 5: Test direct API call
    print("\n5. Testing Direct API Call (bypassing geopy)...")
    try:
        import requests
        test_addr_encoded = requests.utils.quote("Chicago, IL, USA")
        url = f"https://nominatim.openstreetmap.org/search?q={test_addr_encoded}&format=json&limit=1"
        headers = {
            'User-Agent': 'IDF-Creator-Diagnostic/1.0',
            'Accept': 'application/json'
        }
        print(f"    URL: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        print(f"    Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"    ✓ Direct API call successful")
                print(f"    - Found {len(data)} result(s)")
                print(f"    - First result: {data[0].get('display_name', 'N/A')}")
                print(f"    - Lat: {data[0].get('lat')}, Lon: {data[0].get('lon')}")
            else:
                print(f"    ⚠️  Empty response")
        else:
            print(f"    ❌ HTTP {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"    ❌ Direct API call failed: {e}")
    
    # Test 6: Check rate limiting
    print("\n6. Testing Rate Limiting...")
    print("    Making 3 rapid requests to check for rate limiting...")
    try:
        for i in range(3):
            print(f"    Request {i+1}...")
            location = geolocator.geocode("Chicago, IL", timeout=10)
            if location:
                print(f"      ✓ Success")
            else:
                print(f"      ⚠️  No results (might be rate limited)")
            if i < 2:
                time.sleep(0.5)  # Short delay
    except Exception as e:
        print(f"    ❌ Rate limiting test failed: {e}")
    
    print("\n" + "=" * 60)
    print("Diagnostic Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_geocoding()



