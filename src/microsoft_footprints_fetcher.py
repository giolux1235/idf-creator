"""
Microsoft Building Footprints Fetcher
Accesses Microsoft's high-resolution building footprint dataset for more accurate building area calculations.

Data Source: https://github.com/microsoft/USBuildingFootprints
129M+ buildings across the United States with computer-generated footprints from satellite imagery.
"""
import os
import requests
import json
from typing import Dict, List, Optional, Tuple
import math
try:
    from shapely.geometry import Polygon, Point
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False


class MicrosoftFootprintsFetcher:
    """
    Fetches building footprints from Microsoft Building Footprints dataset.
    
    This dataset provides high-resolution building footprints derived from computer vision
    analysis of satellite imagery, offering better accuracy than OSM for US buildings.
    """
    
    # Azure Maps API endpoint (if API key is available)
    AZURE_MAPS_BASE_URL = "https://atlas.microsoft.com"
    
    # Alternative: Direct GeoJSON access via state-level downloads
    # For production, consider using a tile-based service or pre-downloaded GeoJSON files
    
    def __init__(self, azure_maps_api_key: Optional[str] = None):
        """
        Initialize Microsoft Footprints Fetcher.
        
        Args:
            azure_maps_api_key: Optional Azure Maps API key for direct API access
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'IDF-Creator/1.0',
            'Accept': 'application/json'
        })
        self.azure_maps_api_key = azure_maps_api_key or os.getenv('AZURE_MAPS_API_KEY')
    
    def get_building_footprint(self, latitude: float, longitude: float,
                               radius_meters: int = 50) -> Optional[Dict]:
        """
        Get building footprint near the given coordinates using Microsoft Building Footprints.
        
        Priority order:
        1. Azure Maps API (if API key available)
        2. State-level GeoJSON query (if files available)
        3. Returns None (fallback to OSM)
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius_meters: Search radius in meters
            
        Returns:
            Dictionary with building data or None
        """
        # Try Azure Maps first (if API key available)
        if self.azure_maps_api_key:
            result = self._fetch_from_azure_maps(latitude, longitude, radius_meters)
            if result:
                return result
        
        # Try state-level GeoJSON (if available in cache/downloaded)
        result = self._fetch_from_state_geojson(latitude, longitude, radius_meters)
        if result:
            return result
        
        # No Microsoft data available - will fallback to OSM
        return None
    
    def _fetch_from_azure_maps(self, latitude: float, longitude: float,
                               radius_meters: int) -> Optional[Dict]:
        """
        Fetch building footprint from Azure Maps API.
        
        Note: Azure Maps may not directly expose Microsoft Building Footprints,
        but can provide building data if available.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius_meters: Search radius
            
        Returns:
            Building data dictionary or None
        """
        try:
            # Azure Maps Search API - search for buildings near point
            search_url = f"{self.AZURE_MAPS_BASE_URL}/search/poi/nearby/json"
            params = {
                'api-version': '2022-08-01',
                'subscription-key': self.azure_maps_api_key,
                'query': 'building',
                'lat': latitude,
                'lon': longitude,
                'radius': radius_meters,
                'limit': 1
            }
            
            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if results:
                # Parse Azure Maps result
                building = results[0]
                position = building.get('position', {})
                
                # Try to get footprint from geometry if available
                footprint = None
                if 'geometry' in building:
                    # Azure Maps geometry format
                    geom = building['geometry']
                    if geom.get('type') == 'Polygon':
                        coords = geom.get('coordinates', [])
                        if coords and len(coords) > 0:
                            # GeoJSON format: [[[lon, lat], ...]]
                            ring = coords[0]
                            footprint = [(lat, lon) for lon, lat in ring]
                
                # Calculate area if we have footprint
                area_estimate = None
                if footprint and len(footprint) >= 3:
                    area_estimate = self._calculate_polygon_area(footprint)
                
                return {
                    'footprint': footprint,
                    'area_estimate_m2': area_estimate,
                    'source': 'azure_maps',
                    'properties': {
                        'building': building.get('type', 'building'),
                        'name': building.get('poi', {}).get('name'),
                        'address': building.get('address', {}).get('freeformAddress')
                    }
                }
        
        except Exception as e:
            # Azure Maps not available or failed - silently fail and try other methods
            pass
        
        return None
    
    def _fetch_from_state_geojson(self, latitude: float, longitude: float,
                                  radius_meters: int) -> Optional[Dict]:
        """
        Fetch building footprint from state-level GeoJSON files.
        
        Microsoft Building Footprints are organized by state. This method would
        need access to pre-downloaded GeoJSON files or a tile-based service.
        
        For now, this is a placeholder for future implementation.
        State-level files can be downloaded from:
        https://github.com/microsoft/USBuildingFootprints
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius_meters: Search radius
            
        Returns:
            Building data dictionary or None
        """
        # TODO: Implement state-level GeoJSON querying
        # This would require:
        # 1. Downloading state-level GeoJSON files from Microsoft repo
        # 2. Creating a spatial index (R-tree) for fast queries
        # 3. Querying by bounding box around coordinates
        
        # For now, return None to indicate Microsoft data not available
        return None
    
    def _calculate_polygon_area(self, nodes: List[Tuple[float, float]]) -> float:
        """
        Calculate polygon area using accurate spherical geometry.
        Returns area in square meters.
        
        Uses the same accurate calculation method as OSM fetcher.
        """
        if len(nodes) < 3:
            return 0.0
        
        # Extract coordinates (nodes are in format [(lat, lon), ...])
        coords = [(float(lat), float(lon)) for lat, lon in nodes]
        
        # Method 1: Use shapely + pyproj for accurate projection-based area
        if SHAPELY_AVAILABLE:
            try:
                from pyproj import Transformer
                
                # Calculate average latitude for UTM zone selection
                avg_lat = sum(lat for lat, lon in coords) / len(coords)
                avg_lon = sum(lon for lat, lon in coords) / len(coords)
                
                # Determine appropriate UTM zone
                utm_zone = int((avg_lon + 180) / 6) + 1
                utm_hemisphere = 'N' if avg_lat >= 0 else 'S'
                utm_crs = f'EPSG:326{utm_zone:02d}' if utm_hemisphere == 'N' else f'EPSG:327{utm_zone:02d}'
                
                # Project to UTM for accurate area calculation
                transformer = Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)
                projected_coords = [transformer.transform(lon, lat) for lat, lon in coords]
                
                # Create polygon and calculate area (already in square meters)
                polygon = Polygon(projected_coords)
                if polygon.is_valid:
                    return abs(polygon.area)
            except Exception as e:
                # Fall back to approximation if projection fails
                pass
        
        # Method 2: Improved latitude-aware approximation
        avg_lat = sum(lat for lat, lon in coords) / len(coords)
        lat_rad = math.radians(avg_lat)
        
        # Conversion factors (meters per degree)
        meters_per_deg_lat = 111000.0
        meters_per_deg_lon = 111000.0 * math.cos(lat_rad)
        
        # Shoelace formula on projected coordinates
        area = 0.0
        for i in range(len(coords)):
            j = (i + 1) % len(coords)
            lat_i, lon_i = coords[i]
            lat_j, lon_j = coords[j]
            
            # Project to approximate meters
            x_i = lon_i * meters_per_deg_lon
            y_i = lat_i * meters_per_deg_lat
            x_j = lon_j * meters_per_deg_lon
            y_j = lat_j * meters_per_deg_lat
            
            area += (x_i * y_j - x_j * y_i)
        
        area = abs(area) / 2.0
        return area
    
    def is_us_location(self, latitude: float, longitude: float) -> bool:
        """
        Check if coordinates are within US bounds.
        
        Microsoft Building Footprints dataset only covers the United States.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            True if coordinates are within US bounds
        """
        # Rough US bounds (excluding Alaska and Hawaii for simplicity)
        # Mainland US: 24.5°N to 49.4°N, -125.0°W to -66.9°W
        us_lat_min, us_lat_max = 24.5, 49.4
        us_lon_min, us_lon_max = -125.0, -66.9
        
        return (us_lat_min <= latitude <= us_lat_max and
                us_lon_min <= longitude <= us_lon_max)

