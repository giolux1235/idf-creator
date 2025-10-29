"""
City Open Data Fetcher for Commercial Building Data
Integrates with free city APIs for building energy benchmarking and characteristics
"""

from typing import Dict, Optional, List
import requests
import time


class CityDataFetcher:
    """Fetches commercial building data from city open data portals"""
    
    def __init__(self):
        self.nyc_api_base = "https://data.cityofnewyork.us/api/views"
        self.sf_api_base = "https://data.sfgov.org/api"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'IDF-Creator/1.0',
            'Accept': 'application/json'
        })
    
    def fetch_building_data(self, address: str, city: str, 
                           latitude: float = None, longitude: float = None) -> Dict:
        """
        Fetch building data based on city
        
        Args:
            address: Building address
            city: City name (NYC, San Francisco, Chicago, etc.)
            latitude: Optional lat for proximity search
            longitude: Optional lon for proximity search
            
        Returns:
            Dictionary with building data or None
        """
        city_lower = city.lower()
        
        if 'new york' in city_lower or 'nyc' in city_lower:
            return self.fetch_nyc_benchmarking(address, latitude, longitude)
        elif 'san francisco' in city_lower or 'sf' in city_lower:
            return self.fetch_sf_building_data(address, latitude, longitude)
        elif 'chicago' in city_lower:
            return self.fetch_chicago_building_data(address, latitude, longitude)
        else:
            return {}
    
    def fetch_nyc_benchmarking(self, address: str, 
                              latitude: float = None, longitude: float = None) -> Dict:
        """
        Fetch NYC Energy Benchmarking data
        
        NYC Dataset: Energy Benchmarking data for 26,000+ buildings
        Endpoint: https://data.cityofnewyork.us/Environment/Energy-Benchmarking
        
        Args:
            address: Building address
            latitude: Latitude for proximity search
            longitude: Longitude for proximity search
            
        Returns:
            Building data dictionary
        """
        try:
            # NYC uses SODA API (Simple Open Data API)
            # Dataset ID: https://data.cityofnewyork.us/Environment/Energy-and-Water-Data-Disclosure-for-Local-Law-84/usc3-8zwd
            
            # Try to query by address (if address parsing works)
            # For now, return structure for integration
            
            # API endpoint
            base_url = "https://data.cityofnewyork.us/api/views/usc3-8zwd/rows.json"
            
            # Example query (would need address geocoding first)
            params = {
                '$limit': 10,  # Limit results
                '$offset': 0
            }
            
            # Note: NYC API doesn't have direct address search in free tier
            # Would need to download full dataset or use Socrata API with app token
            
            # For now, return empty dict - implement full integration later
            return {}
            
        except Exception as e:
            print(f"⚠️  Error fetching NYC data: {e}")
            return {}
    
    def fetch_sf_building_data(self, address: str,
                              latitude: float = None, longitude: float = None) -> Dict:
        """
        Fetch SF Building Performance data
        
        SF Dataset: Building Energy Performance Ordinance
        Source: datasf.org
        
        Args:
            address: Building address
            latitude: Latitude for search
            longitude: Longitude for search
            
        Returns:
            Building data dictionary
        """
        try:
            # SF uses Socrata API
            # Dataset: Building Energy Performance Benchmarks
            # https://data.sfgov.org/dataset/Building-Energy-Performance-Ordinance
            
            # Example structure
            base_url = "https://data.sfgov.org/resource/2qh3-5sp5.json"
            
            # Query by location if lat/lon provided
            where_clause = ""
            if latitude and longitude:
                # Approximate: within 0.001 degrees (~100m)
                where_clause = f"latitude between {latitude-0.001} and {latitude+0.001} and longitude between {longitude-0.001} and {longitude+0.001}"
            
            params = {
                '$limit': 1,
                '$where': where_clause
            }
            
            # For now, return structure
            return {}
            
        except Exception as e:
            print(f"⚠️  Error fetching SF data: {e}")
            return {}
    
    def fetch_chicago_building_data(self, address: str,
                                   latitude: float = None, longitude: float = None) -> Dict:
        """
        Fetch Chicago building data
        
        Args:
            address: Building address
            latitude: Latitude for search
            longitude: Longitude for search
            
        Returns:
            Building data dictionary
        """
        # Chicago has limited building energy data publicly available
        return {}
    
    def parse_nyc_benchmark_data(self, record: Dict) -> Dict:
        """
        Parse NYC benchmarking record into IDF-relevant data
        
        Args:
            record: Raw NYC data record
            
        Returns:
            Parsed building data
        """
        return {
            'building_name': record.get('building_name'),
            'property_address': record.get('property_address'),
            'building_age': self._parse_year(record.get('year_built')),
            'total_square_footage': self._parse_number(record.get('property_floor_area_1000_sf')) * 1000,
            'site_eui': self._parse_number(record.get('site_eui_wn', {}).get('value')),
            'source_eui': self._parse_number(record.get('source_eui_wn', {}).get('value')),
            'eui_year': record.get('reporting_year'),
            'building_type': record.get('reported_primary_property_type'),
            'stories': self._parse_number(record.get('number_of_floors')),
            'units': self._parse_number(record.get('number_of_units')),
            'occupancy_code': record.get('occupancy_code')
        }
    
    def parse_sf_benchmark_data(self, record: Dict) -> Dict:
        """
        Parse SF benchmarking record into IDF-relevant data
        
        Args:
            record: Raw SF data record
            
        Returns:
            Parsed building data
        """
        return {
            'building_name': record.get('building_name'),
            'address': record.get('address'),
            'building_age': self._parse_year(record.get('year_built')),
            'total_square_footage': self._parse_number(record.get('total_gfa')),
            'site_eui': self._parse_number(record.get('site_eui')),
            'source_eui': self._parse_number(record.get('source_eui')),
            'eui_year': record.get('disclosure_year'),
            'building_type': record.get('primary_property_type'),
            'stories': self._parse_number(record.get('number_of_floors')),
            'energy_score': record.get('energy_score')
        }
    
    def _parse_year(self, value) -> Optional[int]:
        """Parse year from various formats"""
        if not value:
            return None
        try:
            return int(str(value).split('-')[0])
        except:
            return None
    
    def _parse_number(self, value) -> Optional[float]:
        """Parse number from string or dict"""
        if not value:
            return None
        try:
            if isinstance(value, dict):
                return float(value.get('value', 0))
            return float(value)
        except:
            return None


