"""
Advanced Geometry Engine for IDF Creator
Handles complex building geometries, multi-zone layouts, and irregular footprints
"""

import math
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
import numpy as np


@dataclass
class BuildingFootprint:
    """Represents a building footprint with complex geometry"""
    polygon: Polygon
    height: float
    stories: int
    building_type: str
    roof_type: str
    courtyards: List[Polygon] = None
    wings: List[Polygon] = None
    
    def __post_init__(self):
        if self.courtyards is None:
            self.courtyards = []
        if self.wings is None:
            self.wings = []


@dataclass
class ZoneGeometry:
    """Represents a single zone's geometry"""
    name: str
    polygon: Polygon
    floor_level: int
    height: float
    area: float
    perimeter: float
    adjacent_zones: List[str] = None
    
    def __post_init__(self):
        if self.adjacent_zones is None:
            self.adjacent_zones = []


class AdvancedGeometryEngine:
    """Generates complex building geometries for professional IDF creation"""
    
    def __init__(self):
        self.building_templates = self._load_building_templates()
        self.zone_templates = self._load_zone_templates()
    
    def _load_building_templates(self) -> Dict:
        """Load building type templates for geometry generation"""
        return {
            'office': {
                'typical_floor_area': 2000,  # m²
                'aspect_ratio_range': (1.2, 2.5),
                'courtyard_probability': 0.3,
                'wing_probability': 0.4,
                'irregular_probability': 0.2
            },
            'residential': {
                'typical_floor_area': 150,
                'aspect_ratio_range': (1.0, 1.8),
                'courtyard_probability': 0.1,
                'wing_probability': 0.2,
                'irregular_probability': 0.1
            },
            'retail': {
                'typical_floor_area': 5000,
                'aspect_ratio_range': (1.0, 3.0),
                'courtyard_probability': 0.1,
                'wing_probability': 0.6,
                'irregular_probability': 0.3
            },
            'healthcare': {
                'typical_floor_area': 3000,
                'aspect_ratio_range': (1.0, 2.0),
                'courtyard_probability': 0.4,
                'wing_probability': 0.8,
                'irregular_probability': 0.1
            },
            'education': {
                'typical_floor_area': 2500,
                'aspect_ratio_range': (1.0, 2.5),
                'courtyard_probability': 0.2,
                'wing_probability': 0.5,
                'irregular_probability': 0.2
            }
        }
    
    def _load_zone_templates(self) -> Dict:
        """Load zone type templates for space planning"""
        return {
            'office': {
                'core_zones': ['lobby', 'conference', 'break_room', 'mechanical'],
                'typical_zones': ['office_open', 'office_private', 'storage'],
                'zone_sizes': {
                    'lobby': (50, 200),
                    'conference': (30, 100),
                    'break_room': (20, 80),
                    'office_open': (100, 500),
                    'office_private': (15, 50),
                    'storage': (10, 50),
                    'mechanical': (20, 100)
                }
            },
            'residential': {
                'core_zones': ['living', 'kitchen', 'bedroom', 'bathroom'],
                'typical_zones': ['dining', 'storage', 'utility'],
                'zone_sizes': {
                    'living': (20, 60),
                    'kitchen': (10, 30),
                    'bedroom': (12, 25),
                    'bathroom': (5, 15),
                    'dining': (8, 20),
                    'storage': (3, 10),
                    'utility': (3, 8)
                }
            },
            'retail': {
                'core_zones': ['sales_floor', 'storage', 'office', 'break_room'],
                'typical_zones': ['fitting_room', 'customer_service', 'mechanical'],
                'zone_sizes': {
                    'sales_floor': (500, 3000),
                    'storage': (50, 300),
                    'office': (20, 100),
                    'break_room': (15, 50),
                    'fitting_room': (10, 40),
                    'customer_service': (20, 80),
                    'mechanical': (30, 150)
                }
            }
        }
    
    def generate_complex_footprint(self, osm_data: Dict, building_type: str, 
                                 total_area: float, stories: int) -> BuildingFootprint:
        """Generate complex building footprint from OSM data and building parameters"""
        
        # Get building template
        template = self.building_templates.get(building_type, self.building_templates['office'])
        
        # Extract or generate base polygon
        if 'geometry' in osm_data and osm_data['geometry']:
            base_polygon = self._parse_osm_geometry(osm_data['geometry'])
        else:
            base_polygon = self._generate_rectangular_footprint(total_area, template)
        
        # Add complexity based on building type
        footprint = self._add_geometric_complexity(
            base_polygon, building_type, template, total_area
        )
        
        # Extract height information
        height = self._extract_building_height(osm_data, stories)
        
        return BuildingFootprint(
            polygon=footprint,
            height=height,
            stories=stories,
            building_type=building_type,
            roof_type=self._determine_roof_type(building_type, osm_data)
        )
    
    def _parse_osm_geometry(self, geometry_data: Dict) -> Polygon:
        """Parse OSM geometry data into Shapely polygon"""
        try:
            if geometry_data.get('type') == 'Polygon':
                coords = geometry_data['coordinates'][0]  # Exterior ring
                return Polygon(coords)
            elif geometry_data.get('type') == 'MultiPolygon':
                polygons = []
                for poly_coords in geometry_data['coordinates']:
                    polygons.append(Polygon(poly_coords[0]))
                return unary_union(polygons)
        except Exception as e:
            print(f"Error parsing OSM geometry: {e}")
            return None
        
        return None
    
    def _generate_rectangular_footprint(self, area: float, template: Dict) -> Polygon:
        """Generate rectangular footprint when OSM data is unavailable"""
        aspect_ratio = np.random.uniform(*template['aspect_ratio_range'])
        
        # Calculate dimensions
        width = math.sqrt(area / aspect_ratio)
        length = area / width
        
        # Create rectangle centered at origin
        half_width = width / 2
        half_length = length / 2
        
        return Polygon([
            (-half_length, -half_width),
            (half_length, -half_width),
            (half_length, half_width),
            (-half_length, half_width)
        ])
    
    def _add_geometric_complexity(self, base_polygon: Polygon, building_type: str, 
                                template: Dict, area: float) -> Polygon:
        """Add geometric complexity to base polygon based on building type"""
        
        # Add courtyards
        if np.random.random() < template['courtyard_probability']:
            base_polygon = self._add_courtyard(base_polygon, area)
        
        # Add wings
        if np.random.random() < template['wing_probability']:
            base_polygon = self._add_wings(base_polygon, building_type, area)
        
        # Add irregularity
        if np.random.random() < template['irregular_probability']:
            base_polygon = self._add_irregularity(base_polygon, building_type)
        
        return base_polygon
    
    def _add_courtyard(self, polygon: Polygon, area: float) -> Polygon:
        """Add courtyard to building footprint"""
        # Calculate courtyard size (10-20% of building area)
        courtyard_area = area * np.random.uniform(0.1, 0.2)
        courtyard_side = math.sqrt(courtyard_area)
        
        # Find suitable location for courtyard
        bounds = polygon.bounds
        center_x = (bounds[0] + bounds[2]) / 2
        center_y = (bounds[1] + bounds[3]) / 2
        
        # Create courtyard polygon
        courtyard = Polygon([
            (center_x - courtyard_side/2, center_y - courtyard_side/2),
            (center_x + courtyard_side/2, center_y - courtyard_side/2),
            (center_x + courtyard_side/2, center_y + courtyard_side/2),
            (center_x - courtyard_side/2, center_y + courtyard_side/2)
        ])
        
        # Subtract courtyard from main polygon
        return polygon.difference(courtyard)
    
    def _add_wings(self, polygon: Polygon, building_type: str, area: float) -> Polygon:
        """Add wings to building footprint"""
        wings = []
        
        # Number of wings based on building type
        num_wings = {
            'healthcare': np.random.randint(2, 5),
            'education': np.random.randint(1, 3),
            'retail': np.random.randint(1, 4),
            'office': np.random.randint(0, 2),
            'residential': 0
        }.get(building_type, 1)
        
        for _ in range(num_wings):
            wing = self._generate_wing(polygon, area)
            if wing:
                wings.append(wing)
        
        # Union all wings with main polygon
        if wings:
            all_polygons = [polygon] + wings
            return unary_union(all_polygons)
        
        return polygon
    
    def _generate_wing(self, main_polygon: Polygon, area: float) -> Optional[Polygon]:
        """Generate a single wing attached to main polygon"""
        bounds = main_polygon.bounds
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        
        # Wing dimensions (20-40% of main building)
        wing_area = area * np.random.uniform(0.2, 0.4)
        wing_aspect = np.random.uniform(1.0, 3.0)
        
        wing_width = math.sqrt(wing_area / wing_aspect)
        wing_length = wing_area / wing_width
        
        # Choose attachment side
        side = np.random.choice(['north', 'south', 'east', 'west'])
        
        if side == 'north':
            wing = Polygon([
                (bounds[0], bounds[3]),
                (bounds[2], bounds[3]),
                (bounds[2], bounds[3] + wing_length),
                (bounds[0], bounds[3] + wing_length)
            ])
        elif side == 'south':
            wing = Polygon([
                (bounds[0], bounds[1] - wing_length),
                (bounds[2], bounds[1] - wing_length),
                (bounds[2], bounds[1]),
                (bounds[0], bounds[1])
            ])
        elif side == 'east':
            wing = Polygon([
                (bounds[2], bounds[1]),
                (bounds[2] + wing_length, bounds[1]),
                (bounds[2] + wing_length, bounds[3]),
                (bounds[2], bounds[3])
            ])
        else:  # west
            wing = Polygon([
                (bounds[0] - wing_length, bounds[1]),
                (bounds[0], bounds[1]),
                (bounds[0], bounds[3]),
                (bounds[0] - wing_length, bounds[3])
            ])
        
        return wing
    
    def _add_irregularity(self, polygon: Polygon, building_type: str) -> Polygon:
        """Add irregularity to building footprint"""
        # Get polygon coordinates
        coords = list(polygon.exterior.coords[:-1])  # Remove duplicate last point
        
        # Add slight random variations to vertices
        irregular_coords = []
        for x, y in coords:
            # Add random variation (1-5% of building size)
            bounds = polygon.bounds
            max_dim = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
            variation = max_dim * np.random.uniform(0.01, 0.05)
            
            new_x = x + np.random.uniform(-variation, variation)
            new_y = y + np.random.uniform(-variation, variation)
            irregular_coords.append((new_x, new_y))
        
        return Polygon(irregular_coords)

    def scale_polygon_to_area(self, polygon: Polygon, target_area: float) -> Polygon:
        """Uniformly scale a polygon around its centroid to match target area.
        Returns original polygon if invalid inputs.
        """
        try:
            current = polygon.area
            if current <= 0 or target_area <= 0:
                return polygon
            scale = np.sqrt(target_area / current)
            cx, cy = polygon.centroid.x, polygon.centroid.y
            scaled_coords = []
            for x, y in list(polygon.exterior.coords[:-1]):
                sx = cx + (x - cx) * scale
                sy = cy + (y - cy) * scale
                scaled_coords.append((sx, sy))
            return Polygon(scaled_coords)
        except Exception:
            return polygon
    
    def _extract_building_height(self, osm_data: Dict, stories: int) -> float:
        """Extract building height from OSM data or estimate from stories"""
        # Try to get height from OSM tags
        if 'tags' in osm_data:
            tags = osm_data['tags']
            if 'height' in tags:
                try:
                    return float(tags['height'])
                except:
                    pass
            if 'building:levels' in tags:
                try:
                    levels = int(tags['building:levels'])
                    return levels * 3.0  # Assume 3m per story
                except:
                    pass
        
        # Estimate from stories
        return stories * 3.0
    
    def _determine_roof_type(self, building_type: str, osm_data: Dict) -> str:
        """Determine roof type from building type and OSM data"""
        if 'tags' in osm_data and 'roof:type' in osm_data['tags']:
            return osm_data['tags']['roof:type']
        
        # Default based on building type
        roof_types = {
            'office': ['flat', 'shed'],
            'residential': ['gabled', 'hipped', 'shed'],
            'retail': ['flat', 'shed'],
            'healthcare': ['flat', 'shed'],
            'education': ['gabled', 'hipped', 'flat']
        }
        
        return np.random.choice(roof_types.get(building_type, ['flat']))
    
    def generate_zone_layout(self, footprint: BuildingFootprint, 
                           building_type: str) -> List[ZoneGeometry]:
        """Generate detailed zone layout for complex building footprint"""
        
        template = self.zone_templates.get(building_type, self.zone_templates['office'])
        zones = []
        
        # Calculate total floor area
        total_area = footprint.polygon.area * footprint.stories
        
        # Generate zones for each floor
        for floor in range(footprint.stories):
            floor_zones = self._generate_floor_zones(
                footprint.polygon, floor, building_type, template, total_area
            )
            zones.extend(floor_zones)
        
        # Add zone adjacencies
        zones = self._calculate_zone_adjacencies(zones)
        
        return zones
    
    def _generate_floor_zones(self, floor_polygon: Polygon, floor_level: int,
                            building_type: str, template: Dict, total_area: float) -> List[ZoneGeometry]:
        """Generate zones for a single floor"""
        zones = []
        
        # Calculate available floor area
        floor_area = floor_polygon.area
        
        # Generate core zones first
        core_zones = self._generate_core_zones(floor_polygon, floor_level, template)
        zones.extend(core_zones)
        
        # Calculate remaining area
        used_area = sum(zone.area for zone in core_zones)
        remaining_area = floor_area - used_area
        
        # Generate typical zones to fill remaining space
        if remaining_area > 0:
            typical_zones = self._generate_typical_zones(
                floor_polygon, floor_level, template, remaining_area
            )
            zones.extend(typical_zones)
        
        return zones
    
    def _generate_core_zones(self, floor_polygon: Polygon, floor_level: int,
                           template: Dict) -> List[ZoneGeometry]:
        """Generate core zones (lobby, mechanical, etc.)"""
        zones = []
        core_zone_types = template['core_zones']
        
        for zone_type in core_zone_types:
            if zone_type in template['zone_sizes']:
                min_area, max_area = template['zone_sizes'][zone_type]
                area = np.random.uniform(min_area, max_area)
                
                # Create zone polygon (simplified - would use proper space planning)
                zone_polygon = self._create_zone_polygon(floor_polygon, area)
                
                if zone_polygon and zone_polygon.area > 0:
                    zone = ZoneGeometry(
                        name=f"{zone_type}_{floor_level}",
                        polygon=zone_polygon,
                        floor_level=floor_level,
                        height=3.0,  # Standard floor height
                        area=zone_polygon.area,
                        perimeter=zone_polygon.length
                    )
                    zones.append(zone)
        
        return zones
    
    def _generate_typical_zones(self, floor_polygon: Polygon, floor_level: int,
                              template: Dict, available_area: float) -> List[ZoneGeometry]:
        """Generate typical zones to fill remaining floor area"""
        zones = []
        typical_zone_types = template['typical_zones']
        
        remaining_area = available_area
        
        for zone_type in typical_zone_types:
            if remaining_area <= 0:
                break
                
            if zone_type in template['zone_sizes']:
                min_area, max_area = template['zone_sizes'][zone_type]
                max_possible = min(max_area, remaining_area)
                
                if max_possible >= min_area:
                    area = np.random.uniform(min_area, max_possible)
                    
                    zone_polygon = self._create_zone_polygon(floor_polygon, area)
                    
                    if zone_polygon and zone_polygon.area > 0:
                        zone = ZoneGeometry(
                            name=f"{zone_type}_{floor_level}",
                            polygon=zone_polygon,
                            floor_level=floor_level,
                            height=3.0,
                            area=zone_polygon.area,
                            perimeter=zone_polygon.length
                        )
                        zones.append(zone)
                        remaining_area -= zone.area
        
        return zones
    
    def _create_zone_polygon(self, floor_polygon: Polygon, target_area: float) -> Optional[Polygon]:
        """Create a zone polygon within the floor polygon (simplified implementation)"""
        # This is a simplified implementation
        # In practice, you'd use proper space planning algorithms
        
        bounds = floor_polygon.bounds
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        
        # Calculate zone dimensions
        aspect_ratio = np.random.uniform(1.0, 2.0)
        zone_width = math.sqrt(target_area / aspect_ratio)
        zone_height = target_area / zone_width
        
        # Ensure zone fits within floor
        if zone_width > width or zone_height > height:
            zone_width = min(zone_width, width * 0.8)
            zone_height = min(zone_height, height * 0.8)
        
        # Random position within floor
        x_offset = np.random.uniform(0, width - zone_width)
        y_offset = np.random.uniform(0, height - zone_height)
        
        zone_polygon = Polygon([
            (bounds[0] + x_offset, bounds[1] + y_offset),
            (bounds[0] + x_offset + zone_width, bounds[1] + y_offset),
            (bounds[0] + x_offset + zone_width, bounds[1] + y_offset + zone_height),
            (bounds[0] + x_offset, bounds[1] + y_offset + zone_height)
        ])
        
        # Ensure zone is within floor polygon
        if floor_polygon.contains(zone_polygon):
            return zone_polygon
        
        return None
    
    def _calculate_zone_adjacencies(self, zones: List[ZoneGeometry]) -> List[ZoneGeometry]:
        """Calculate which zones are adjacent to each other"""
        for i, zone1 in enumerate(zones):
            for j, zone2 in enumerate(zones):
                if i != j and zone1.floor_level == zone2.floor_level:
                    # Check if zones are adjacent (simplified)
                    if zone1.polygon.touches(zone2.polygon) or zone1.polygon.distance(zone2.polygon) < 0.1:
                        zone1.adjacent_zones.append(zone2.name)
        
        return zones
    
    def generate_building_surfaces(self, zones: List[ZoneGeometry], 
                                 footprint: BuildingFootprint) -> List[Dict]:
        """Generate detailed building surfaces for complex geometry"""
        surfaces = []
        
        for zone in zones:
            # Generate floor surface
            floor_surface = self._generate_floor_surface(zone, footprint)
            if floor_surface:
                surfaces.append(floor_surface)
            
            # Generate ceiling surface
            ceiling_surface = self._generate_ceiling_surface(zone, footprint)
            if ceiling_surface:
                surfaces.append(ceiling_surface)
            
            # Generate wall surfaces
            wall_surfaces = self._generate_wall_surfaces(zone, footprint)
            surfaces.extend(wall_surfaces)
        
        return surfaces
    
    def _generate_floor_surface(self, zone: ZoneGeometry, footprint: BuildingFootprint) -> Dict:
        """Generate floor surface for zone"""
        coords = list(zone.polygon.exterior.coords[:-1])
        # Reverse vertex order so outward normal points downward (tilt ~180)
        coords = list(reversed(coords))
        z_coord = zone.floor_level * 3.0
        
        vertices = []
        for x, y in coords:
            vertices.append(f"{x:.4f},{y:.4f},{z_coord:.4f}")
        
        return {
            'type': 'BuildingSurface:Detailed',
            'name': f"{zone.name}_Floor",
            'surface_type': 'Floor',
            'construction': 'Building_ExteriorFloor',
            'zone': zone.name,
            'outside_boundary_condition': 'Outdoors',
            'sun_exposure': 'SunExposed',
            'wind_exposure': 'WindExposed',
            'view_factor_to_ground': 'AutoCalculate',
            'vertices': vertices
        }
    
    def _generate_ceiling_surface(self, zone: ZoneGeometry, footprint: BuildingFootprint) -> Dict:
        """Generate ceiling surface for zone"""
        coords = list(zone.polygon.exterior.coords[:-1])
        z_coord = (zone.floor_level + 1) * 3.0
        
        vertices = []
        for x, y in coords:
            vertices.append(f"{x:.4f},{y:.4f},{z_coord:.4f}")
        
        return {
            'type': 'BuildingSurface:Detailed',
            'name': f"{zone.name}_Ceiling",
            'surface_type': 'Roof',
            'construction': 'Building_ExteriorRoof',
            'zone': zone.name,
            'outside_boundary_condition': 'Outdoors',
            'sun_exposure': 'SunExposed',
            'wind_exposure': 'WindExposed',
            'view_factor_to_ground': 'AutoCalculate',
            'vertices': vertices
        }
    
    def _generate_wall_surfaces(self, zone: ZoneGeometry, footprint: BuildingFootprint) -> List[Dict]:
        """Generate wall surfaces for zone"""
        walls = []
        coords = list(zone.polygon.exterior.coords[:-1])
        z_bottom = zone.floor_level * 3.0
        z_top = (zone.floor_level + 1) * 3.0
        
        for i, (x1, y1) in enumerate(coords):
            x2, y2 = coords[(i + 1) % len(coords)]
            
            wall = {
                'type': 'BuildingSurface:Detailed',
                'name': f"{zone.name}_Wall_{i+1}",
                'surface_type': 'Wall',
                'construction': 'Building_ExteriorWall',
                'zone': zone.name,
                'outside_boundary_condition': 'Outdoors',
                'sun_exposure': 'SunExposed',
                'wind_exposure': 'WindExposed',
                'view_factor_to_ground': 'AutoCalculate',
                'vertices': [
                    f"{x1:.4f},{y1:.4f},{z_bottom:.4f}",
                    f"{x2:.4f},{y2:.4f},{z_bottom:.4f}",
                    f"{x2:.4f},{y2:.4f},{z_top:.4f}",
                    f"{x1:.4f},{y1:.4f},{z_top:.4f}"
                ]
            }
            walls.append(wall)
        
        return walls
