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
                    print(f"⚠️  Warning: Geocoding returned suspicious coordinates (0,0)")
                    return None
                # Validate coordinates are within reasonable bounds
                if abs(coords['latitude']) > 90 or abs(coords['longitude']) > 180:
                    print(f"⚠️  Warning: Geocoding returned invalid coordinates")
                    return None
                return coords
        except Exception as e:
            print(f"Geocoding error: {e}")
        
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
        """
        coords = self.geocode_address(address)
        
        if not coords:
            raise ValueError(f"Could not geocode address: {address}")
        
        climate_zone = self.get_climate_zone(
            coords['latitude'], 
            coords['longitude']
        )
        
        weather_file = self.get_weather_file_name(
            coords['latitude'],
            coords['longitude']
        )
        
        # Calculate timezone from coordinates
        time_zone = self.get_time_zone(
            coords['latitude'],
            coords['longitude']
        )
        
        return {
            'address': address,
            'latitude': coords['latitude'],
            'longitude': coords['longitude'],
            'altitude': coords.get('altitude', 0),
            'time_zone': time_zone,
            'climate_zone': climate_zone,
            'weather_file': weather_file
        }

