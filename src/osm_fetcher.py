"""Module for fetching building data from OpenStreetMap."""
import requests
from typing import Dict, List, Optional
import json
import math
try:
    from shapely.geometry import Polygon
    from pyproj import Transformer
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False


class OSMFetcher:
    """Fetches building footprints and data from OpenStreetMap using Overpass API."""
    
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'IDF-Creator/1.0'})
    
    def get_building_footprint(self, latitude: float, longitude: float, 
                               radius_meters: int = 50) -> Optional[Dict]:
        """
        Get building footprint near the given coordinates.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius_meters: Search radius in meters
            
        Returns:
            Dictionary with building data or None
        """
        query = f"""
        [out:json][timeout:25];
        (
          way["building"](around:{radius_meters},{latitude},{longitude});
          relation["building"](around:{radius_meters},{latitude},{longitude});
        );
        out geom;
        """
        
        try:
            response = self.session.post(self.OVERPASS_URL, data={'data': query})
            response.raise_for_status()
            
            data = response.json()
            elements = data.get('elements', [])
            
            if not elements:
                return None
            
            best_building = None
            best_distance = float('inf')
            
            for building in elements:
                if 'geometry' not in building:
                    continue
                nodes = building['geometry']
                if not nodes:
                    continue
                footprint = [(node['lat'], node['lon']) for node in nodes]
                if len(footprint) < 3:
                    continue
                
                # Centroid distance to prefer the polygon closest to the requested coordinates
                centroid_lat = sum(node['lat'] for node in nodes) / len(nodes)
                centroid_lon = sum(node['lon'] for node in nodes) / len(nodes)
                distance = math.hypot(centroid_lat - latitude, centroid_lon - longitude)
                
                area_estimate = self._calculate_polygon_area(footprint)
                
                properties = {
                    'building': building.get('tags', {}).get('building', 'unknown'),
                    'building:levels': building.get('tags', {}).get('building:levels'),
                    'height': building.get('tags', {}).get('height'),
                    'roof:material': building.get('tags', {}).get('roof:material'),
                    'roof:shape': building.get('tags', {}).get('roof:shape'),
                    'addr:street': building.get('tags', {}).get('addr:street'),
                    'addr:housenumber': building.get('tags', {}).get('addr:housenumber')
                }
                
                if distance < best_distance:
                    best_distance = distance
                    best_building = {
                        'footprint': footprint,
                        'area_estimate_m2': area_estimate,
                        'properties': properties,
                        'tags': building.get('tags', {})
                    }
            
            return best_building
        
        except Exception as e:
            print(f"Error fetching OSM data: {e}")
            return None
    
    def get_building_height(self, tags: Dict) -> Optional[float]:
        """
        Extract building height from OSM tags.
        
        Args:
            tags: OSM tags dictionary
            
        Returns:
            Height in meters or None
        """
        # Try direct height tag
        height_str = tags.get('height')
        if height_str:
            try:
                # Parse height (might be "15 m" or "15")
                height_value = float(height_str.split()[0])
                return height_value
            except:
                pass
        
        # Try building:levels
        levels_str = tags.get('building:levels') or tags.get('building:min_levels')
        if levels_str:
            try:
                levels = float(levels_str)
                # Assume 3 meters per story
                return levels * 3.0
            except:
                pass
        
        return None
    
    def get_number_of_stories(self, tags: Dict) -> Optional[int]:
        """
        Extract number of stories from OSM tags.
        
        Args:
            tags: OSM tags dictionary
            
        Returns:
            Number of stories or None
        """
        levels_str = tags.get('building:levels') or tags.get('building:min_levels')
        if levels_str:
            try:
                return int(float(levels_str))
            except:
                pass
        return None
    
    def _calculate_polygon_area(self, nodes: List) -> float:
        """
        Calculate polygon area using accurate spherical geometry.
        Returns area in square meters.
        
        Uses proper coordinate projection for accurate area calculation,
        falling back to latitude-aware approximation if pyproj unavailable.
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
                
                # Determine appropriate UTM zone (for accurate area calculation)
                # UTM zones are 6 degrees wide, numbered 1-60 from -180 to +180
                utm_zone = int((avg_lon + 180) / 6) + 1
                # UTM uses "N" (north) for positive latitudes, "S" for negative
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
                # Fall back to improved approximation if projection fails
                print(f"Warning: Could not use projected area calculation: {e}")
                pass
        
        # Method 2: Improved latitude-aware approximation
        # This accounts for the fact that 1° longitude = 111 km × cos(latitude)
        avg_lat = sum(lat for lat, lon in coords) / len(coords)
        lat_rad = math.radians(avg_lat)
        
        # Conversion factors (meters per degree)
        meters_per_deg_lat = 111000.0  # Constant
        meters_per_deg_lon = 111000.0 * math.cos(lat_rad)  # Varies with latitude
        
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
    
    def search_area_buildings(self, latitude: float, longitude: float,
                             radius_meters: int = 100) -> List[Dict]:
        """
        Get all buildings in an area.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate  
            radius_meters: Search radius
            
        Returns:
            List of building dictionaries
        """
        query = f"""
        [out:json][timeout:25];
        (
          way["building"](around:{radius_meters},{latitude},{longitude});
        );
        out geom;
        """
        
        try:
            response = self.session.post(self.OVERPASS_URL, data={'data': query})
            response.raise_for_status()
            
            data = response.json()
            elements = data.get('elements', [])
            
            buildings = []
            for element in elements:
                if 'geometry' in element:
                    nodes = element['geometry']
                    footprint = [(node['lat'], node['lon']) for node in nodes]
                    
                    buildings.append({
                        'footprint': footprint,
                        'tags': element.get('tags', {}),
                        'properties': {
                            'building': element.get('tags', {}).get('building', 'unknown'),
                            'levels': self.get_number_of_stories(element.get('tags', {})),
                            'height': self.get_building_height(element.get('tags', {}))
                        }
                    })
            
            return buildings
        
        except Exception as e:
            print(f"Error searching buildings: {e}")
            return []























