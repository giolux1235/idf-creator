"""Module for fetching location and climate data from user inputs."""
import os
import requests
from geopy.geocoders import Nominatim
import ssl
import certifi
from typing import Dict, Tuple, Optional


class LocationFetcher:
    """Handles geocoding and climate zone determination."""
    
    def __init__(self):
        # Fix SSL certificate issue on macOS
        ctx = ssl.create_default_context(cafile=certifi.where())
        self.geolocator = Nominatim(user_agent="idf_creator", scheme='https', ssl_context=ctx)
        self.google_api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
    
    def geocode_address(self, address: str) -> Optional[Dict[str, float]]:
        """
        Convert address to lat/lon coordinates.
        
        Args:
            address: Street address string
            
        Returns:
            Dictionary with 'latitude' and 'longitude' keys, or None if failed
        """
        if not address or not address.strip():
            print(f"⚠️  Warning: Empty address provided for geocoding")
            return None
        
        # Try Nominatim geocoding first
        try:
            location = self.geolocator.geocode(address, timeout=10)
            if location:
                coords = {
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'altitude': location.altitude if hasattr(location, 'altitude') else 0
                }
                
                # Validate coordinates are reasonable (not 0,0 or clearly wrong)
                if abs(coords['latitude']) < 0.1 and abs(coords['longitude']) < 0.1:
                    print(f"⚠️  Warning: Geocoding returned suspicious coordinates (0,0) for '{address}'")
                    return None
                
                # Validate coordinates are within reasonable bounds
                if abs(coords['latitude']) > 90 or abs(coords['longitude']) > 180:
                    print(f"⚠️  Warning: Geocoding returned invalid coordinates for '{address}'")
                    return None
                
                # Additional validation: Check if coordinates look reasonable for US addresses
                # US addresses should have negative longitude (west of prime meridian)
                # and latitude between ~25-50 for continental US
                if ', US' in address or ', USA' in address or any(state in address for state in [' IL', ' NY', ' CA', ' TX', ' FL', ' IL,', ' NY,', ' CA,', ' TX,', ' FL,']):
                    if coords['longitude'] > 0:
                        print(f"⚠️  Warning: US address '{address}' geocoded to positive longitude ({coords['longitude']:.4f}), which is likely wrong")
                        # Try fallback geocoding
                        return self._geocode_fallback(address)
                    if coords['latitude'] < 20 or coords['latitude'] > 55:
                        print(f"⚠️  Warning: US address '{address}' geocoded to latitude {coords['latitude']:.4f}, which seems unusual")
                        # Try fallback geocoding
                        return self._geocode_fallback(address)
                
                print(f"✓ Geocoded '{address}' to {coords['latitude']:.4f}°N, {coords['longitude']:.4f}°E")
                return coords
            else:
                print(f"⚠️  Warning: Nominatim geocoding returned no results for '{address}'")
                # Try fallback
                return self._geocode_fallback(address)
        except Exception as e:
            print(f"⚠️  Geocoding error for '{address}': {e}")
            # Try fallback
            return self._geocode_fallback(address)
    
    def _geocode_fallback(self, address: str) -> Optional[Dict[str, float]]:
        """
        Fallback geocoding using OpenStreetMap Nominatim API directly.
        This is a secondary attempt if the primary geocoding fails.
        """
        try:
            import re
            # Extract city and state from address for better geocoding
            # Pattern: "..., City, State ZIP" or "..., City, State"
            city_state_match = re.search(r',\s*([^,]+?),\s*([A-Z]{2})(?:\s+\d{5})?', address)
            if city_state_match:
                city = city_state_match.group(1).strip()
                state = city_state_match.group(2).strip()
                city_state_query = f"{city}, {state}, USA"
                print(f"🔄 Trying fallback geocoding for '{city_state_query}'")
                
                location = self.geolocator.geocode(city_state_query, timeout=10)
                if location:
                    coords = {
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'altitude': location.altitude if hasattr(location, 'altitude') else 0
                    }
                    # Validate coordinates
                    if abs(coords['latitude']) > 90 or abs(coords['longitude']) > 180:
                        return None
                    if abs(coords['latitude']) < 0.1 and abs(coords['longitude']) < 0.1:
                        return None
                    print(f"✓ Fallback geocoding succeeded: {coords['latitude']:.4f}°N, {coords['longitude']:.4f}°E")
                    return coords
        except Exception as e:
            print(f"⚠️  Fallback geocoding also failed: {e}")
        
        return None
    
    def get_time_zone(self, latitude: float, longitude: float) -> float:
        """
        Calculate timezone offset from longitude.
        Uses a simplified approximation: timezone ≈ longitude / 15
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Timezone offset in hours (e.g., -6.0 for Chicago)
        """
        # Simplified timezone calculation based on longitude
        # More accurate would use timezonefinder or similar library
        # For US locations, use approximate timezone boundaries
        
        # US timezone approximations (longitude-based)
        if -125 <= longitude < -102:  # Pacific Time
            return -8.0
        elif -102 <= longitude < -90:  # Mountain Time
            return -7.0
        elif -90 <= longitude < -75:  # Central Time (includes Chicago)
            return -6.0
        elif -75 <= longitude < -60:  # Eastern Time
            return -5.0
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
            ValueError: If geocoding fails or returns invalid coordinates
        """
        if not address or not address.strip():
            raise ValueError(f"Address is required and cannot be empty")
        
        coords = self.geocode_address(address)
        
        if not coords:
            raise ValueError(
                f"CRITICAL: Could not geocode address '{address}'. "
                f"Please check the address format and try again. "
                f"Geocoding service may be unavailable or the address may be invalid."
            )
        
        # Validate coordinates are present
        if 'latitude' not in coords or 'longitude' not in coords:
            raise ValueError(
                f"CRITICAL: Geocoding returned incomplete coordinates for '{address}'. "
                f"Coordinates: {coords}"
            )
        
        latitude = coords['latitude']
        longitude = coords['longitude']
        
        climate_zone = self.get_climate_zone(latitude, longitude)
        
        weather_file = self.get_weather_file_name(latitude, longitude)
        
        # Calculate timezone from coordinates
        time_zone = self.get_time_zone(latitude, longitude)
        
        return {
            'address': address,
            'latitude': latitude,
            'longitude': longitude,
            'altitude': coords.get('altitude', 0),
            'elevation': coords.get('altitude', 0),  # Also provide as 'elevation' for compatibility
            'time_zone': time_zone,
            'climate_zone': climate_zone,
            'weather_file': weather_file
        }

