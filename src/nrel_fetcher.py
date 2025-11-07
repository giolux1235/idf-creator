"""Module for fetching weather data from NREL APIs."""
import requests
from typing import Dict, Optional
import os


class NRELFetcher:
    """Fetches weather data from NREL NSRDB (National Solar Radiation Database)."""
    
    NSRDB_URL = "https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download"
    WEATHER_SEARCH_URL = "https://energyplus.net/weather-location/north_and_central_america_wmo_region_4/USA"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize NREL API fetcher.
        
        Args:
            api_key: NREL API key (optional, some features work without)
        """
        self.api_key = api_key or os.getenv('NREL_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'IDF-Creator/1.0'})
    
    def get_closest_weather_file(self, latitude: float, longitude: float,
                                 distance_km: int = 100) -> Optional[Dict]:
        """
        Find closest EPW weather file to given coordinates.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            distance_km: Maximum search distance in km
            
        Returns:
            Dictionary with weather file info or None
        """
        # For now, use heuristic to suggest weather file
        # In production, you'd query NREL's weather database
        
        return self._suggest_weather_file(latitude, longitude)
    
    def _suggest_weather_file(self, latitude: float, longitude: float) -> Dict:
        """
        Suggest appropriate weather file based on location.
        Uses simplified mapping to common weather files.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary with suggested weather file
        """
        # Simplified weather file mapping
        # In practice, you'd have a full database lookup
        
        # USA region mappings
        if 40.5 <= latitude <= 45 and -80 <= longitude <= -70:
            # Northeastern USA
            return {
                'file': 'USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw',
                'source': 'EnergyPlus Weather Data',
                'url': 'https://energyplus.net/weather-location/north_and_central_america_wmo_region_4/USA/NY',
                'description': 'New York LaGuardia Airport'
            }
        elif 37 <= latitude <= 38 and -123 <= longitude <= -121:
            # San Francisco Bay Area
            return {
                'file': 'USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw',
                'source': 'EnergyPlus Weather Data',
                'url': 'https://energyplus.net/weather-location/north_and_central_america_wmo_region_4/USA/CA',
                'description': 'San Francisco International Airport'
            }
        elif 33.7 <= latitude <= 34.7 and -118.6 <= longitude <= -117.8:
            # Los Angeles
            return {
                'file': 'USA_CA_Los.Angeles.Intl.AP.722950_TMY3.epw',
                'source': 'EnergyPlus Weather Data',
                'url': 'https://energyplus.net/weather-location/north_and_central_america_wmo_region_4/USA/CA',
                'description': 'Los Angeles International Airport'
            }
        elif 29 <= latitude <= 30 and -96 <= longitude <= -94:
            # Houston
            return {
                'file': 'USA_TX_Houston.Bush.Intercontinental.AP.722430_TMY3.epw',
                'source': 'EnergyPlus Weather Data',
                'url': 'https://energyplus.net/weather-location/north_and_central_america_wmo_region_4/USA/TX',
                'description': 'Houston Bush Intercontinental Airport'
            }
        elif 41.8 <= latitude <= 42 and -88 <= longitude <= -87:
            # Chicago
            return {
                'file': 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw',
                'source': 'EnergyPlus Weather Data',
                'url': 'https://energyplus.net/weather-location/north_and_central_america_wmo_region_4/USA/IL',
                'description': 'Chicago O\'Hare International Airport'
            }
        elif 39 <= latitude <= 40 and -106 <= longitude <= -104:
            # Denver
            return {
                'file': 'USA_CO_Denver.Intl.AP.725650_TMY3.epw',
                'source': 'EnergyPlus Weather Data',
                'url': 'https://energyplus.net/weather-location/north_and_central_america_wmo_region_4/USA/CO',
                'description': 'Denver International Airport'
            }
        elif 47.5 <= latitude <= 48 and -123 <= longitude <= -121:
            # Seattle
            return {
                'file': 'USA_WA_Seattle-Tacoma.Intl.AP.727930_TMY3.epw',
                'source': 'EnergyPlus Weather Data',
                'url': 'https://energyplus.net/weather-location/north_and_central_america_wmo_region_4/USA/WA',
                'description': 'Seattle-Tacoma International Airport'
            }
        else:
            # Generic US location - default to a common file
            return {
                'file': 'USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw',
                'source': 'EnergyPlus Weather Data',
                'url': 'https://energyplus.net/weather-location/north_and_central_america_wmo_region_4/USA',
                'description': 'Default US Weather (San Francisco)',
                'note': 'Consider downloading more specific file from energyplus.net'
            }
    
    def get_nsrdb_data(self, latitude: float, longitude: float,
                      year: int = 2021) -> Optional[Dict]:
        """
        Get hourly weather data from NSRDB.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            year: Year of data
            
        Returns:
            Dictionary with weather data or None
        """
        if not self.api_key:
            print("NREL API key not provided. Skipping NSRDB data fetch.")
            return None
        
        # NSRDB API requires specific parameters
        # This is a placeholder for the actual implementation
        return None
    
    def download_epw_file(self, weather_file_name: str, 
                         output_path: str = "weather_data/") -> Optional[str]:
        """
        Download an EPW weather file.
        
        Args:
            weather_file_name: Name of the weather file
            output_path: Directory to save the file
            
        Returns:
            Path to downloaded file or None
        """
        # In production, implement actual download from EnergyPlus weather database
        # For now, return the filename
        return weather_file_name



























