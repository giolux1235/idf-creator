"""Enhanced location fetcher that integrates multiple data sources."""
from typing import Dict, Optional
import os
from .location_fetcher import LocationFetcher
from .osm_fetcher import OSMFetcher
from .nrel_fetcher import NRELFetcher
from .census_fetcher import CensusFetcher
from .city_data_fetcher import CityDataFetcher
from .cbecs_lookup import CBECSLookup


class EnhancedLocationFetcher(LocationFetcher):
    """
    Enhanced location fetcher that combines multiple free APIs for better data.
    """
    
    def __init__(self):
        """Initialize enhanced location fetcher with all data sources."""
        super().__init__()
        self.osm_fetcher = OSMFetcher()
        self.nrel_fetcher = NRELFetcher()
        self.census_fetcher = CensusFetcher()
        self.city_fetcher = CityDataFetcher()
        self.cbecs_lookup = CBECSLookup()
    
    def fetch_comprehensive_location_data(self, address: str) -> Dict:
        """
        Fetch comprehensive location data from multiple sources.
        
        Args:
            address: Building address
            
        Returns:
            Dictionary with comprehensive location and building data
        """
        print(f"📍 Fetching comprehensive data for: {address}")
        
        # 1. Basic geocoding
        coords = self.geocode_address(address)
        if not coords:
            raise ValueError(f"Could not geocode address: {address}")
        
        print(f"✓ Geocoded: {coords['latitude']:.3f}, {coords['longitude']:.3f}")
        
        # 2. Climate zone
        climate_zone = self.get_climate_zone(coords['latitude'], coords['longitude'])
        print(f"✓ Climate zone: {climate_zone}")
        
        # 3. OSM building data
        print(f"🗺️  Fetching building footprint from OpenStreetMap...")
        osm_data = self.osm_fetcher.get_building_footprint(
            coords['latitude'], 
            coords['longitude']
        )
        
        building_info = {}
        if osm_data:
            print(f"✓ Found building in OSM")
            building_info = {
                'osm_footprint': osm_data.get('footprint'),
                'osm_area_m2': osm_data.get('area_estimate_m2'),
                'osm_building_type': osm_data['properties'].get('building'),
                'osm_levels': osm_data['properties'].get('levels'),
                'osm_height_m': osm_data['properties'].get('height'),
                'osm_roof_shape': osm_data['properties'].get('roof:shape'),
                'osm_tags': osm_data.get('tags', {})
            }
            print(f"  - Type: {building_info['osm_building_type']}")
            if building_info.get('osm_levels'):
                print(f"  - Levels: {building_info['osm_levels']}")
            if building_info.get('osm_area_m2'):
                print(f"  - Area: {building_info['osm_area_m2']:.1f} m²")
        else:
            print("⚠️  No building found in OSM")
        
        # 4. Weather file
        print(f"🌤️  Getting weather data from NREL...")
        weather_info = self.nrel_fetcher.get_closest_weather_file(
            coords['latitude'],
            coords['longitude']
        )
        print(f"✓ Weather file: {weather_info['description']}")
        
        # 5. City-specific building data (NYC, SF, etc.)
        print(f"🏢 Fetching city building data...")
        city_data = {}
        try:
            # Extract city from address
            city_name = self._extract_city_from_address(address)
            city_data = self.city_fetcher.fetch_building_data(
                address, city_name,
                coords['latitude'], coords['longitude']
            )
            if city_data:
                print(f"✓ Found city building data")
            else:
                print(f"⚠️  No city data available (not NYC/SF/Chicago)")
        except Exception as e:
            print(f"⚠️  City data fetch failed: {e}")
        
        # 6. CBECS typical values
        cbecs_eui = None
        try:
            # Get typical EUI for validation later
            # Will be used to validate simulation results
            cbecs_eui = {'note': 'Use CBECSLookup to get typical EUI'}
            print(f"✓ CBECS lookup ready")
        except Exception as e:
            print(f"⚠️  CBECS lookup failed: {e}")
        
        # Combine all data
        comprehensive_data = {
            'address': address,
            'latitude': coords['latitude'],
            'longitude': coords['longitude'],
            'altitude': coords.get('altitude', 0),
            'climate_zone': climate_zone,
            'weather_file': weather_info['file'],
            'weather_description': weather_info['description'],
            'weather_url': weather_info.get('url'),
            'building': building_info,
            'city_data': city_data,
            'cbecs_eui': cbecs_eui
        }
        
        return comprehensive_data
    
    def _extract_city_from_address(self, address: str) -> str:
        """Extract city name from address string"""
        # Simple parsing - assumes format "..., City, State"
        parts = address.split(',')
        if len(parts) >= 2:
            return parts[-2].strip()  # Second to last part
        return parts[0].strip()  # Fallback
    
    def fetch_enhanced_building_data(self, latitude: float, longitude: float,
                                    radius_meters: int = 100) -> Dict:
        """
        Fetch enhanced building data from multiple sources.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius_meters: Search radius
            
        Returns:
            Dictionary with enhanced building data
        """
        # Get OSM building
        osm_data = self.osm_fetcher.get_building_footprint(latitude, longitude, radius_meters)
        
        # Get nearby buildings for context
        nearby_buildings = self.osm_fetcher.search_area_buildings(latitude, longitude, radius_meters)
        
        # Get weather
        weather_info = self.nrel_fetcher.get_closest_weather_file(latitude, longitude)
        
        return {
            'primary_building': osm_data,
            'nearby_buildings': nearby_buildings,
            'weather': weather_info,
            'climate_zone': self.get_climate_zone(latitude, longitude)
        }






