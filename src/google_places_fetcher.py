"""
Google Places API Fetcher for Building Footprints
Accesses Google Places API to get building geometry and area data.

Requires GOOGLE_MAPS_API_KEY environment variable.
Cost: ~$5-17 per 1,000 requests (Places API)
"""
import os
import requests
from typing import Dict, List, Optional, Tuple
import math
try:
    from shapely.geometry import Polygon
    from pyproj import Transformer
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False


class GooglePlacesFetcher:
    """
    Fetches building footprints and data from Google Places API.
    
    Provides high-accuracy building geometry data when API key is available.
    Falls back gracefully if API key is not set.
    """
    
    PLACES_API_BASE_URL = "https://maps.googleapis.com/maps/api/place"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Google Places Fetcher.
        
        Args:
            api_key: Optional Google Maps API key. If not provided, checks environment variable.
        """
        self.api_key = api_key or os.getenv('GOOGLE_MAPS_API_KEY', '')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'IDF-Creator/1.0',
            'Accept': 'application/json'
        })
    
    def is_available(self) -> bool:
        """
        Check if Google Places API is available (API key exists).
        
        Returns:
            True if API key is available, False otherwise
        """
        return bool(self.api_key and self.api_key.strip())
    
    def get_building_footprint(self, latitude: float, longitude: float,
                               radius_meters: int = 50) -> Optional[Dict]:
        """
        Get building footprint near the given coordinates using Google Places API.
        
        Uses Place Search API to find nearby buildings, then Place Details API
        to get geometry information.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius_meters: Search radius in meters (max 50,000)
            
        Returns:
            Dictionary with building data or None if not available
        """
        if not self.is_available():
            return None
        
        try:
            # Step 1: Search for places near coordinates
            place_id = self._search_nearby_place(latitude, longitude, radius_meters)
            if not place_id:
                return None
            
            # Step 2: Get place details with geometry
            place_details = self._get_place_details(place_id)
            if not place_details:
                return None
            
            # Step 3: Extract footprint and area
            footprint = self._extract_footprint(place_details)
            area_estimate = None
            if footprint and len(footprint) >= 3:
                area_estimate = self._calculate_polygon_area(footprint)
            
            return {
                'footprint': footprint,
                'area_estimate_m2': area_estimate,
                'source': 'google_places',
                'properties': {
                    'name': place_details.get('name'),
                    'types': place_details.get('types', []),
                    'formatted_address': place_details.get('formatted_address'),
                    'place_id': place_id
                }
            }
        
        except Exception as e:
            # Silently fail - Google Places is optional
            # Only log if debugging is enabled
            if os.getenv('DEBUG_GOOGLE_PLACES'):
                print(f"⚠️  Google Places API error: {e}")
            return None
    
    def _search_nearby_place(self, latitude: float, longitude: float,
                            radius_meters: int) -> Optional[str]:
        """
        Search for a place near the given coordinates.
        
        Uses Places API Nearby Search to find buildings.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius_meters: Search radius
            
        Returns:
            Place ID or None
        """
        try:
            url = f"{self.PLACES_API_BASE_URL}/nearbysearch/json"
            params = {
                'location': f"{latitude},{longitude}",
                'radius': min(radius_meters, 50000),  # Max 50,000 meters
                'key': self.api_key,
                'type': 'establishment'  # Search for buildings/establishments
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'OK' or not data.get('results'):
                return None
            
            # Return the first result's place_id
            return data['results'][0].get('place_id')
        
        except Exception:
            return None
    
    def _get_place_details(self, place_id: str) -> Optional[Dict]:
        """
        Get detailed information about a place including geometry.
        
        Uses Places API Place Details endpoint.
        
        Args:
            place_id: Google Places place ID
            
        Returns:
            Place details dictionary or None
        """
        try:
            url = f"{self.PLACES_API_BASE_URL}/details/json"
            params = {
                'place_id': place_id,
                'fields': 'geometry,name,types,formatted_address,place_id',
                'key': self.api_key
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'OK' or not data.get('result'):
                return None
            
            return data['result']
        
        except Exception:
            return None
    
    def _extract_footprint(self, place_details: Dict) -> Optional[List[Tuple[float, float]]]:
        """
        Extract building footprint polygon from place details.
        
        Args:
            place_details: Place details dictionary from Google Places API
            
        Returns:
            List of (lat, lon) tuples representing footprint polygon or None
        """
        geometry = place_details.get('geometry', {})
        
        # Try to get viewport bounds (if available)
        viewport = geometry.get('viewport', {})
        if viewport:
            northeast = viewport.get('northeast', {})
            southwest = viewport.get('southwest', {})
            
            if northeast and southwest:
                # Create a rectangle from viewport bounds
                ne_lat = northeast.get('lat')
                ne_lng = northeast.get('lng')
                sw_lat = southwest.get('lat')
                sw_lng = southwest.get('lng')
                
                if all(x is not None for x in [ne_lat, ne_lng, sw_lat, sw_lng]):
                    # Return rectangle polygon
                    return [
                        (sw_lat, sw_lng),  # Southwest
                        (ne_lat, sw_lng),  # Southeast
                        (ne_lat, ne_lng),  # Northeast
                        (sw_lat, ne_lng),  # Northwest
                        (sw_lat, sw_lng)   # Close polygon
                    ]
        
        # Try to get precise location point (fallback)
        location = geometry.get('location', {})
        if location:
            lat = location.get('lat')
            lng = location.get('lng')
            if lat is not None and lng is not None:
                # Create a small square around the point (fallback)
                # Use ~50m radius (approximately 0.00045 degrees)
                offset = 0.00045
                return [
                    (lat - offset, lng - offset),
                    (lat + offset, lng - offset),
                    (lat + offset, lng + offset),
                    (lat - offset, lng + offset),
                    (lat - offset, lng - offset)
                ]
        
        return None
    
    def _calculate_polygon_area(self, nodes: List[Tuple[float, float]]) -> float:
        """
        Calculate polygon area using accurate spherical geometry.
        Returns area in square meters.
        
        Uses the same accurate calculation method as OSM and Microsoft fetchers.
        """
        if len(nodes) < 3:
            return 0.0
        
        # Extract coordinates (nodes are in format [(lat, lon), ...])
        coords = [(float(lat), float(lon)) for lat, lon in nodes]
        
        # Method 1: Use shapely + pyproj for accurate projection-based area
        if SHAPELY_AVAILABLE:
            try:
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
            except Exception:
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

