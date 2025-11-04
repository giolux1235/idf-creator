"""Module for fetching building data from OpenStreetMap."""
import requests
from typing import Dict, List, Optional
import json


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
            
            # Get the closest building
            building = elements[0]
            
            # Extract nodes for footprint
            if 'geometry' in building:
                nodes = building['geometry']
                footprint = [(node['lat'], node['lon']) for node in nodes]
            else:
                footprint = None
            
            # Extract building properties
            properties = {
                'building': building.get('tags', {}).get('building', 'unknown'),
                'building:levels': building.get('tags', {}).get('building:levels'),
                'height': building.get('tags', {}).get('height'),
                'roof:material': building.get('tags', {}).get('roof:material'),
                'roof:shape': building.get('tags', {}).get('roof:shape'),
                'addr:street': building.get('tags', {}).get('addr:street'),
                'addr:housenumber': building.get('tags', {}).get('addr:housenumber')
            }
            
            # Calculate area if we have footprint
            area_estimate = None
            if footprint and len(footprint) >= 3:
                area_estimate = self._calculate_polygon_area(footprint)
            
            return {
                'footprint': footprint,
                'area_estimate_m2': area_estimate,
                'properties': properties,
                'tags': building.get('tags', {})
            }
        
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
        Calculate polygon area using shoelace formula.
        Returns area in square meters.
        """
        if len(nodes) < 3:
            return 0.0
        
        # Shoelace formula for spherical coordinates
        area = 0.0
        for i in range(len(nodes)):
            j = (i + 1) % len(nodes)
            lat_i, lon_i = nodes[i]
            lat_j, lon_j = nodes[j]
            
            area += (lon_i * lat_j - lon_j * lat_i)
        
        area = abs(area) / 2.0
        
        # Convert to square meters (approximate)
        # 1 degree latitude ≈ 111 km
        # This is a simplified calculation
        return area * 111000 * 111000
    
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

















