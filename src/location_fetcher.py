"""Module for fetching location and climate data from user inputs."""
import os
import requests
from geopy.geocoders import Nominatim
import ssl
import certifi
import time
import re
from typing import Dict, Tuple, Optional
from threading import Lock


class GeocodingError(Exception):
    """Raised when geocoding fails to find real coordinates for an address."""
    pass


class LocationFetcher:
    """Handles geocoding and climate zone determination."""
    
    @staticmethod
    def extract_city_state(address: str) -> Optional[str]:
        """Extract city and state from address string"""
        if not address:
            return None
        
        # Pattern 1: "City, State ZIP" or "City, State"
        # Example: "147 Sutter St, San Francisco, CA 94104"
        match = re.search(r',\s*([^,]+?),\s*([A-Z]{2})(?:\s+\d+)?', address)
        if match:
            city = match.group(1).strip()
            state = match.group(2).strip()
            return f"{city}, {state}"
        
        # Pattern 2: "City State ZIP" (no comma before state)
        # Example: "Chicago IL 60601"
        match = re.search(r'([^,]+?)\s+([A-Z]{2})(?:\s+\d+)?', address)
        if match:
            city = match.group(1).strip()
            state = match.group(2).strip()
            return f"{city}, {state}"
        
        return None
    
    # City lookup table with 50+ major US cities - CHECKED FIRST for reliability
    CITY_LOOKUP = {
        'Chicago, IL': {'latitude': 41.8781, 'longitude': -87.6298, 'time_zone': -6.0, 'elevation': 200},
        'San Francisco, CA': {'latitude': 37.7749, 'longitude': -122.4194, 'time_zone': -8.0, 'elevation': 2},
        'New York, NY': {'latitude': 40.7128, 'longitude': -74.0060, 'time_zone': -5.0, 'elevation': 10},
        'Los Angeles, CA': {'latitude': 34.0522, 'longitude': -118.2437, 'time_zone': -8.0, 'elevation': 100},
        'Houston, TX': {'latitude': 29.7604, 'longitude': -95.3698, 'time_zone': -6.0, 'elevation': 13},
        'Phoenix, AZ': {'latitude': 33.4484, 'longitude': -112.0740, 'time_zone': -7.0, 'elevation': 331},
        'Philadelphia, PA': {'latitude': 39.9526, 'longitude': -75.1652, 'time_zone': -5.0, 'elevation': 12},
        'San Antonio, TX': {'latitude': 29.4241, 'longitude': -98.4936, 'time_zone': -6.0, 'elevation': 198},
        'San Diego, CA': {'latitude': 32.7157, 'longitude': -117.1611, 'time_zone': -8.0, 'elevation': 20},
        'Dallas, TX': {'latitude': 32.7767, 'longitude': -96.7970, 'time_zone': -6.0, 'elevation': 131},
        'San Jose, CA': {'latitude': 37.3382, 'longitude': -121.8863, 'time_zone': -8.0, 'elevation': 26},
        'Austin, TX': {'latitude': 30.2672, 'longitude': -97.7431, 'time_zone': -6.0, 'elevation': 149},
        'Jacksonville, FL': {'latitude': 30.3322, 'longitude': -81.6557, 'time_zone': -5.0, 'elevation': 5},
        'Fort Worth, TX': {'latitude': 32.7555, 'longitude': -97.3308, 'time_zone': -6.0, 'elevation': 199},
        'Columbus, OH': {'latitude': 39.9612, 'longitude': -82.9988, 'time_zone': -5.0, 'elevation': 275},
        'Charlotte, NC': {'latitude': 35.2271, 'longitude': -80.8431, 'time_zone': -5.0, 'elevation': 229},
        'Seattle, WA': {'latitude': 47.6062, 'longitude': -122.3321, 'time_zone': -8.0, 'elevation': 56},
        'Denver, CO': {'latitude': 39.7392, 'longitude': -104.9903, 'time_zone': -7.0, 'elevation': 1609},
        'Washington, DC': {'latitude': 38.9072, 'longitude': -77.0369, 'time_zone': -5.0, 'elevation': 7},
        'Boston, MA': {'latitude': 42.3601, 'longitude': -71.0589, 'time_zone': -5.0, 'elevation': 14},
        'El Paso, TX': {'latitude': 31.7619, 'longitude': -106.4850, 'time_zone': -7.0, 'elevation': 1140},
        'Detroit, MI': {'latitude': 42.3314, 'longitude': -83.0458, 'time_zone': -5.0, 'elevation': 183},
        'Nashville, TN': {'latitude': 36.1627, 'longitude': -86.7816, 'time_zone': -6.0, 'elevation': 170},
        'Portland, OR': {'latitude': 45.5152, 'longitude': -122.6784, 'time_zone': -8.0, 'elevation': 15},
        'Oklahoma City, OK': {'latitude': 35.4676, 'longitude': -97.5164, 'time_zone': -6.0, 'elevation': 396},
        'Las Vegas, NV': {'latitude': 36.1699, 'longitude': -115.1398, 'time_zone': -8.0, 'elevation': 610},
        'Memphis, TN': {'latitude': 35.1495, 'longitude': -90.0490, 'time_zone': -6.0, 'elevation': 87},
        'Louisville, KY': {'latitude': 38.2527, 'longitude': -85.7585, 'time_zone': -5.0, 'elevation': 142},
        'Baltimore, MD': {'latitude': 39.2904, 'longitude': -76.6122, 'time_zone': -5.0, 'elevation': 10},
        'Milwaukee, WI': {'latitude': 43.0389, 'longitude': -87.9065, 'time_zone': -6.0, 'elevation': 188},
        'Albuquerque, NM': {'latitude': 35.0844, 'longitude': -106.6504, 'time_zone': -7.0, 'elevation': 1619},
        'Tucson, AZ': {'latitude': 32.2226, 'longitude': -110.9747, 'time_zone': -7.0, 'elevation': 728},
        'Fresno, CA': {'latitude': 36.7378, 'longitude': -119.7871, 'time_zone': -8.0, 'elevation': 94},
        'Sacramento, CA': {'latitude': 38.5816, 'longitude': -121.4944, 'time_zone': -8.0, 'elevation': 9},
        'Kansas City, MO': {'latitude': 39.0997, 'longitude': -94.5786, 'time_zone': -6.0, 'elevation': 277},
        'Mesa, AZ': {'latitude': 33.4152, 'longitude': -111.8315, 'time_zone': -7.0, 'elevation': 378},
        'Atlanta, GA': {'latitude': 33.7490, 'longitude': -84.3880, 'time_zone': -5.0, 'elevation': 320},
        'Omaha, NE': {'latitude': 41.2565, 'longitude': -95.9345, 'time_zone': -6.0, 'elevation': 333},
        'Colorado Springs, CO': {'latitude': 38.8339, 'longitude': -104.8214, 'time_zone': -7.0, 'elevation': 1839},
        'Raleigh, NC': {'latitude': 35.7796, 'longitude': -78.6382, 'time_zone': -5.0, 'elevation': 96},
        'Virginia Beach, VA': {'latitude': 36.8529, 'longitude': -75.9780, 'time_zone': -5.0, 'elevation': 3},
        'Miami, FL': {'latitude': 25.7617, 'longitude': -80.1918, 'time_zone': -5.0, 'elevation': 2},
        'Oakland, CA': {'latitude': 37.8044, 'longitude': -122.2712, 'time_zone': -8.0, 'elevation': 13},
        'Minneapolis, MN': {'latitude': 44.9778, 'longitude': -93.2650, 'time_zone': -6.0, 'elevation': 253},
        'Tulsa, OK': {'latitude': 36.1540, 'longitude': -95.9928, 'time_zone': -6.0, 'elevation': 194},
        'Cleveland, OH': {'latitude': 41.4993, 'longitude': -81.6944, 'time_zone': -5.0, 'elevation': 199},
        'Wichita, KS': {'latitude': 37.6872, 'longitude': -97.3301, 'time_zone': -6.0, 'elevation': 396},
        'Arlington, TX': {'latitude': 32.7357, 'longitude': -97.1081, 'time_zone': -6.0, 'elevation': 184},
        'New Orleans, LA': {'latitude': 29.9511, 'longitude': -90.0715, 'time_zone': -6.0, 'elevation': -2},
        'Honolulu, HI': {'latitude': 21.3099, 'longitude': -157.8581, 'time_zone': -10.0, 'elevation': 6},
        'Anchorage, AK': {'latitude': 61.2181, 'longitude': -149.9003, 'time_zone': -9.0, 'elevation': 31}
    }
    
    # Rate limiting: Nominatim allows 1 request per second
    _last_request_time = 0.0
    _rate_limit_lock = Lock()
    
    def __init__(self):
        # Fix SSL certificate issue on macOS
        ctx = ssl.create_default_context(cafile=certifi.where())
        self.geolocator = Nominatim(user_agent="idf_creator", scheme='https', ssl_context=ctx)
        self.google_api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
    
    @classmethod
    def _respect_rate_limit(cls):
        """Ensure we respect Nominatim's 1 request per second rate limit."""
        with cls._rate_limit_lock:
            elapsed = time.time() - cls._last_request_time
            if elapsed < 1.1:  # Add 0.1s buffer for safety
                sleep_time = 1.1 - elapsed
                time.sleep(sleep_time)
            cls._last_request_time = time.time()
    
    def geocode_address(self, address: str) -> Optional[Dict[str, float]]:
        """
        Convert address to lat/lon coordinates.
        CHECKS CITY LOOKUP TABLE FIRST for reliability.
        
        Priority order:
        1. Lookup table (fast, free, reliable for 50+ major cities)
        2. Google Maps API (accurate, requires API key, costs money)
        3. Nominatim API (free, rate-limited)
        4. Keyword detection (backup)
        5. Raises GeocodingError if no real coordinates found
        
        Args:
            address: Street address string
            
        Returns:
            Dictionary with 'latitude', 'longitude', 'time_zone', 'elevation' keys, or None if failed
            
        Raises:
            GeocodingError: If real coordinates cannot be found for the address
        """
        if not address or not address.strip():
            print(f"⚠️  Warning: Empty address provided for geocoding")
            return None
        
        # STEP 1: Extract city and state from address
        city_state = self.extract_city_state(address)
        
        # STEP 2: Check city lookup table FIRST (fast, reliable)
        if city_state and city_state in self.CITY_LOOKUP:
            city_data = self.CITY_LOOKUP[city_state]
            print(f"✅ Found city in lookup table: {city_state} → {city_data['latitude']:.4f}°N, {city_data['longitude']:.4f}°W")
            return {
                'latitude': city_data['latitude'],
                'longitude': city_data['longitude'],
                'time_zone': city_data['time_zone'],
                'altitude': city_data['elevation'],
                'elevation': city_data['elevation']
            }
        
        # STEP 3: Try keyword detection as backup (for addresses like "147 Sutter St, SF, CA")
        address_lower = address.lower()
        keyword_cities = {
            'chicago': 'Chicago, IL',
            'san francisco': 'San Francisco, CA',
            'sf,': 'San Francisco, CA',
            'sf ': 'San Francisco, CA',
            'new york': 'New York, NY',
            'nyc': 'New York, NY',
            'manhattan': 'New York, NY',
            'los angeles': 'Los Angeles, CA',
            'la,': 'Los Angeles, CA',
            'la ': 'Los Angeles, CA',
        }
        
        for keyword, city_key in keyword_cities.items():
            if keyword in address_lower:
                if city_key in self.CITY_LOOKUP:
                    city_data = self.CITY_LOOKUP[city_key]
                    print(f"✅ Detected city from keywords: {city_key} → {city_data['latitude']:.4f}°N, {city_data['longitude']:.4f}°W")
                    return {
                        'latitude': city_data['latitude'],
                        'longitude': city_data['longitude'],
                        'time_zone': city_data['time_zone'],
                        'altitude': city_data['elevation'],
                        'elevation': city_data['elevation']
                    }
        
        # STEP 4: Try Google Maps API (if API key is available)
        if self.google_api_key:
            try:
                print(f"🗺️  Trying Google Maps API geocoding...")
                coords = self._geocode_with_google(address)
                if coords:
                    print(f"✅ Geocoded with Google Maps API: {coords['latitude']:.4f}°N, {coords['longitude']:.4f}°W")
                    return coords
                else:
                    print(f"⚠️  Google Maps API returned no results")
            except Exception as e:
                print(f"⚠️  Google Maps API error: {e}")
        
        # STEP 5: Try Nominatim geocoding API (free fallback)
        try:
            # Respect rate limit (1 request per second)
            self._respect_rate_limit()
            
            # Try geocoding with retry logic
            location = None
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    location = self.geolocator.geocode(address, timeout=15)
                    if location:
                        break
                    elif attempt < max_retries - 1:
                        # If no results, wait a bit longer before retry
                        wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
                        print(f"    ⏳ No results, waiting {wait_time}s before retry {attempt + 2}/{max_retries}...")
                        time.sleep(wait_time)
                        self._respect_rate_limit()
                except Exception as retry_error:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2
                        print(f"    ⏳ Geocoding error (attempt {attempt + 1}/{max_retries}): {retry_error}, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        self._respect_rate_limit()
                    else:
                        raise retry_error
            
            if location:
                coords = {
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'altitude': location.altitude if hasattr(location, 'altitude') else 0
                }
                
                # Validate coordinates are reasonable (not 0,0 or clearly wrong)
                if abs(coords['latitude']) < 0.1 and abs(coords['longitude']) < 0.1:
                    print(f"❌ Error: Geocoding returned invalid coordinates (0,0) for '{address}'")
                    raise GeocodingError(
                        f"Geocoding API returned invalid coordinates (0,0) for address '{address}'. "
                        "This is not a real location."
                    )
                
                # Validate coordinates are within reasonable bounds
                if abs(coords['latitude']) > 90 or abs(coords['longitude']) > 180:
                    print(f"❌ Error: Geocoding returned invalid coordinates for '{address}'")
                    raise GeocodingError(
                        f"Geocoding API returned invalid coordinates (lat={coords['latitude']:.4f}, lon={coords['longitude']:.4f}) "
                        f"for address '{address}'. Coordinates are outside valid range."
                    )
                
                # Additional validation: Check if coordinates look reasonable for US addresses
                # US addresses should have negative longitude (west of prime meridian)
                # and latitude between ~25-50 for continental US
                if ', US' in address or ', USA' in address or any(state in address for state in [' IL', ' NY', ' CA', ' TX', ' FL', ' IL,', ' NY,', ' CA,', ' TX,', ' FL,']):
                    if coords['longitude'] > 0:
                        print(f"❌ Error: US address '{address}' geocoded to positive longitude ({coords['longitude']:.4f}), which is invalid for US addresses")
                        raise GeocodingError(
                            f"Geocoding returned invalid coordinates for US address '{address}'. "
                            f"US addresses should have negative longitude (west of prime meridian), "
                            f"but got {coords['longitude']:.4f}."
                        )
                    if coords['latitude'] < 20 or coords['latitude'] > 55:
                        print(f"⚠️  Warning: US address '{address}' geocoded to latitude {coords['latitude']:.4f}, which seems unusual")
                        # Don't raise error for this, just warn - could be Alaska or Hawaii
                
                # Calculate timezone and elevation from coordinates
                time_zone = self.get_time_zone(coords['latitude'], coords['longitude'])
                elevation = self._get_elevation_from_coords(coords['latitude'], coords['longitude'])
                
                coords['time_zone'] = time_zone
                coords['elevation'] = elevation
                
                print(f"✓ Geocoded '{address}' to {coords['latitude']:.4f}°N, {coords['longitude']:.4f}°W")
                return coords
            else:
                print(f"❌ Error: Nominatim geocoding returned no results for '{address}'")
                # Try final fallback (which may raise error if nothing found)
                return self._geocode_fallback_final(address)
        except GeocodingError:
            # Re-raise GeocodingError
            raise
        except Exception as e:
            print(f"⚠️  Geocoding error for '{address}': {e}")
            # Try final fallback (which may raise error if nothing found)
            return self._geocode_fallback_final(address)
    
    def _geocode_with_google(self, address: str) -> Optional[Dict[str, float]]:
        """
        Geocode address using Google Maps API.
        
        Requires GOOGLE_MAPS_API_KEY environment variable.
        Costs approximately $5 per 1,000 requests after free tier.
        
        Args:
            address: Street address string
            
        Returns:
            Dictionary with coordinates, time_zone, and elevation, or None if failed
        """
        if not self.google_api_key:
            return None
        
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': address,
                'key': self.google_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"⚠️  Google Maps API returned status {response.status_code}")
                return None
            
            data = response.json()
            
            if data.get('status') != 'OK' or not data.get('results'):
                print(f"⚠️  Google Maps API status: {data.get('status', 'UNKNOWN')}")
                return None
            
            # Extract location from first result
            location = data['results'][0]['geometry']['location']
            lat = location['lat']
            lng = location['lng']
            
            # Calculate timezone and elevation
            time_zone = self.get_time_zone(lat, lng)
            elevation = self._get_elevation_from_coords(lat, lng)
            
            return {
                'latitude': lat,
                'longitude': lng,
                'time_zone': time_zone,
                'altitude': elevation,
                'elevation': elevation
            }
            
        except Exception as e:
            print(f"⚠️  Google Maps API error: {e}")
            return None
    
    def _get_elevation_from_coords(self, lat: float, lon: float) -> float:
        """Get elevation from coordinates (reasonable defaults based on location)"""
        # San Francisco area
        if 37 < lat < 38 and -123 < lon < -122:
            return 2
        # New York area
        elif 40 < lat < 41 and -74 < lon < -73:
            return 10
        # Los Angeles area
        elif 34 < lat < 35 and -119 < lon < -118:
            return 100
        # Chicago area
        elif 41 < lat < 42 and -88 < lon < -87:
            return 200
        # Denver area (high elevation)
        elif 39 < lat < 40 and -105 < lon < -104:
            return 1609
        # Default
        else:
            return 200
    
    def _geocode_fallback_final(self, address: str) -> Optional[Dict[str, float]]:
        """
        Final fallback: Try to extract city/state again or use keyword detection.
        Raises GeocodingError if no real coordinates can be found.
        """
        try:
            # Try city/state extraction again (maybe with different pattern)
            city_state = self.extract_city_state(address)
            if city_state and city_state in self.CITY_LOOKUP:
                city_data = self.CITY_LOOKUP[city_state]
                print(f"✅ Fallback found city in lookup table: {city_state}")
                return {
                    'latitude': city_data['latitude'],
                    'longitude': city_data['longitude'],
                    'time_zone': city_data['time_zone'],
                    'altitude': city_data['elevation'],
                    'elevation': city_data['elevation']
                }
            
            # Try keyword detection one more time
            address_lower = address.lower()
            keyword_cities = {
                'chicago': 'Chicago, IL',
                'san francisco': 'San Francisco, CA',
                'sf': 'San Francisco, CA',
                'new york': 'New York, NY',
                'nyc': 'New York, NY',
                'los angeles': 'Los Angeles, CA',
                'la': 'Los Angeles, CA',
            }
            
            for keyword, city_key in keyword_cities.items():
                if keyword in address_lower:
                    if city_key in self.CITY_LOOKUP:
                        city_data = self.CITY_LOOKUP[city_key]
                        print(f"✅ Fallback detected city from keywords: {city_key}")
                        return {
                            'latitude': city_data['latitude'],
                            'longitude': city_data['longitude'],
                            'time_zone': city_data['time_zone'],
                            'altitude': city_data['elevation'],
                            'elevation': city_data['elevation']
                        }
        except Exception as e:
            print(f"⚠️  Fallback geocoding error: {e}")
        
        # NO FALLBACK: Raise error if real coordinates cannot be found
        raise GeocodingError(
            f"Failed to geocode address '{address}'. "
            "Could not find real coordinates from any source (lookup table, Google Maps API, or Nominatim). "
            "Please provide a valid address with city and state information."
        )
    
    def _geocode_fallback(self, address: str) -> Optional[Dict[str, float]]:
        """
        Legacy fallback method - now redirects to final fallback.
        Kept for backwards compatibility.
        """
        return self._geocode_fallback_final(address)
    
    def get_time_zone(self, latitude: float, longitude: float) -> float:
        """
        Calculate timezone offset from coordinates.
        Handles US timezones including Hawaii and Alaska.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Timezone offset in hours (e.g., -6.0 for Chicago, -8.0 for San Francisco, -10.0 for Hawaii)
        """
        # Check Hawaii first (has specific lat/lon range)
        if 18 < latitude < 23 and -161 < longitude < -154:
            return -10.0
        
        # Check Alaska (west coast + specific lat range)
        if latitude > 55 and longitude < -125:
            return -9.0
        
        # Continental US timezone approximations (longitude-based)
        if -127 <= longitude < -112:  # Pacific Time (west coast)
            return -8.0
        elif -112 <= longitude < -102:  # Mountain Time
            return -7.0
        elif -102 <= longitude < -82:  # Central Time (includes Chicago at -87.63)
            return -6.0
        elif -82 <= longitude < -67:  # Eastern Time
            return -5.0
        elif -67 <= longitude < -60:  # Atlantic Time
            return -4.0
        else:
            # For other locations, use longitude/15 approximation
            # This is a rough approximation but works for most cases
            return round(longitude / 15.0, 1)
    
    def get_climate_zone(self, latitude: float, longitude: float) -> str:
        """
        Determine ASHRAE climate zone from coordinates.
        Uses simplified logic based on latitude and typical zones.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Climate zone string (e.g., "ASHRAE_C4")
        """
        # Simplified climate zone determination
        # More accurate implementation would use detailed climate data
        
        if latitude < 25:
            # Tropical
            if 30 < longitude < 70:  # Middle East
                return "ASHRAE_C0"
            else:
                return "ASHRAE_C1"
        elif 25 <= latitude < 30:
            return "ASHRAE_C1"
        elif 30 <= latitude < 35:
            return "ASHRAE_C3"
        elif 35 <= latitude < 40:
            return "ASHRAE_C4"
        elif 40 <= latitude < 45:
            return "ASHRAE_C5"
        elif 45 <= latitude < 50:
            return "ASHRAE_C6"
        elif 50 <= latitude < 55:
            return "ASHRAE_C7"
        else:
            return "ASHRAE_C8"
    
    def get_weather_file_name(self, latitude: float, longitude: float, 
                              country: str = "") -> str:
        """
        Suggest appropriate EPW weather file name.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            country: Country name (optional)
            
        Returns:
            Suggested weather file name
        """
        # For simplicity, return a generic weather file
        # In production, this would query a weather database
        return "USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw"
    
    def fetch_location_data(self, address: str) -> Dict:
        """
        Main method to fetch comprehensive location data.
        
        Args:
            address: Street address
            
        Returns:
            Dictionary with location and climate information
            
        Raises:
            GeocodingError: If real coordinates cannot be found for the address
        """
        if not address or not address.strip():
            raise GeocodingError(
                "Empty address provided. Please provide a valid address with city and state information."
            )
        
        coords = self.geocode_address(address)
        
        # If geocoding failed, try fallback (which will raise error if nothing found)
        if not coords:
            print(f"⚠️  Warning: Primary geocoding failed for '{address}', trying fallback...")
            coords = self._geocode_fallback_final(address)
        
        # Validate coordinates are present and valid
        if not coords or 'latitude' not in coords or 'longitude' not in coords:
            raise GeocodingError(
                f"Failed to obtain valid coordinates for address '{address}'. "
                "Geocoding returned incomplete data."
            )
        
        # Validate coordinates are real (not synthetic defaults)
        lat = coords['latitude']
        lon = coords['longitude']
        
        # Check if coordinates are the Chicago default (which we should never use as fallback)
        if abs(lat - 41.8781) < 0.0001 and abs(lon - (-87.6298)) < 0.0001:
            # Only allow Chicago if the address actually contains Chicago
            if 'chicago' not in address.lower() and 'il' not in address.lower():
                raise GeocodingError(
                    f"Geocoding returned Chicago default coordinates for non-Chicago address '{address}'. "
                    "This indicates geocoding failed. Please provide a valid address."
                )
        
        latitude = coords['latitude']
        longitude = coords['longitude']
        
        climate_zone = self.get_climate_zone(latitude, longitude)
        
        weather_file = self.get_weather_file_name(latitude, longitude)
        
        # Calculate timezone from coordinates (or use city lookup if available)
        time_zone = coords.get('time_zone')
        if time_zone is None:
            time_zone = self.get_time_zone(latitude, longitude)
        
        # Get elevation from coords or use city lookup
        elevation = coords.get('altitude') or coords.get('elevation')
        if elevation is None:
            # Try to get from city lookup
            import re
            city_state_match = re.search(r',\s*([^,]+?),\s*([A-Z]{2})', address)
            if city_state_match:
                city = city_state_match.group(1).strip()
                state = city_state_match.group(2).strip()
                city_key = f"{city}, {state}"
                if city_key in self.CITY_LOOKUP:
                    elevation = self.CITY_LOOKUP[city_key].get('elevation', 100)
            if elevation is None:
                elevation = 100  # Default elevation
        
        return {
            'address': address,
            'latitude': latitude,
            'longitude': longitude,
            'altitude': elevation,
            'elevation': elevation,
            'time_zone': time_zone,
            'climate_zone': climate_zone,
            'weather_file': weather_file
        }

