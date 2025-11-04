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
            # Fallback to rectangular if parsing failed
            if base_polygon is None or base_polygon.area < 1:
                base_polygon = self._generate_rectangular_footprint(total_area, template)
        else:
            base_polygon = self._generate_rectangular_footprint(total_area, template)
        
        # Add complexity based on building type
        footprint = self._add_geometric_complexity(
            base_polygon, building_type, template, total_area
        )
        
        # Final safety check: if footprint is invalid, use base polygon
        if footprint is None or footprint.area < 1:
            footprint = base_polygon
        
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
        """Parse OSM geometry data into Shapely polygon
        Handles both GeoJSON (projected coords) and geographic lat/lon coords
        """
        try:
            if geometry_data.get('type') == 'Polygon':
                coords = geometry_data['coordinates'][0]  # Exterior ring
                
                # Check if coordinates are geographic (lat/lon) and need projection
                first_coord = coords[0]
                if len(first_coord) == 2:
                    # Check if lat/lon (rough heuristic: abs(lat) <= 90, abs(lon) <= 180)
                    lat, lon = first_coord[1], first_coord[0]
                    if abs(lat) <= 90 and abs(lon) <= 180 and (abs(lat) > 1 or abs(lon) > 1):
                        # Geographic coordinates - convert to local meters
                        coords = self._convert_latlon_to_local_meters(coords)
                
                polygon = Polygon(coords)
                return polygon if polygon.is_valid else None
                
            elif geometry_data.get('type') == 'MultiPolygon':
                polygons = []
                for poly_coords in geometry_data['coordinates']:
                    ext_ring = poly_coords[0]  # Exterior ring of each polygon
                    
                    # Convert if geographic
                    if ext_ring and len(ext_ring[0]) == 2:
                        first = ext_ring[0]
                        lat, lon = first[1], first[0]
                        if abs(lat) <= 90 and abs(lon) <= 180 and (abs(lat) > 1 or abs(lon) > 1):
                            ext_ring = self._convert_latlon_to_local_meters(ext_ring)
                    
                    p = Polygon(ext_ring)
                    if p.is_valid:
                        polygons.append(p)
                
                if polygons:
                    return unary_union(polygons) if len(polygons) > 1 else polygons[0]
                return None
                
        except Exception as e:
            print(f"Error parsing OSM geometry: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        return None
    
    def _convert_latlon_to_local_meters(self, coords):
        """
        Convert geographic lat/lon coordinates to local meters centered on first point.
        Uses simple equirectangular projection (good for small buildings).
        """
        if not coords:
            return coords
        
        # Get reference point (first coordinate)
        lon0, lat0 = coords[0]
        
        # Earth radius in meters
        R = 6371000
        
        # Convert all coordinates to local meters
        local_coords = []
        for lon, lat in coords:
            # Equirectangular projection
            x = R * np.radians(lon - lon0) * np.cos(np.radians(lat0))
            y = R * np.radians(lat - lat0)
            local_coords.append([x, y])
        
        return local_coords
    
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
    
    def _add_irregularity(self, polygon, building_type: str):
        """Add irregularity to building footprint"""
        # Handle MultiPolygon (use largest component)
        if hasattr(polygon, 'geoms'):
            # It's a MultiPolygon
            polygon = max(polygon.geoms, key=lambda p: p.area)
        
        if not hasattr(polygon, 'exterior'):
            return polygon
        
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
        
        # Track zone types already created on this floor to avoid duplicate names
        created_types = set()
        for z in core_zones:
            base = z.name.rsplit('_', 1)[0]
            created_types.add(base)
        
        # Calculate remaining area and create polygon excluding core zones
        used_area = sum(zone.area for zone in core_zones)
        remaining_area = floor_area - used_area
        
        # IMPROVED: Exclude core zones from floor polygon for grid generation
        available_polygon = floor_polygon
        if core_zones:
            # Subtract core zone polygons from floor polygon
            core_polygons = [zone.polygon for zone in core_zones]
            if core_polygons:
                try:
                    core_union = unary_union(core_polygons)
                    available_polygon = floor_polygon.difference(core_union)
                    # If difference creates multiple polygons, use the largest
                    if hasattr(available_polygon, 'geoms'):
                        available_polygon = max(available_polygon.geoms, key=lambda p: p.area)
                except Exception:
                    # Fallback to original polygon if difference fails
                    available_polygon = floor_polygon
        
        # Generate typical zones to fill remaining space using grid-based approach
        if remaining_area > 50:  # Only if significant area remains
            typical_zones = self._generate_typical_zones(
                available_polygon, floor_level, template, remaining_area, created_types
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
                              template: Dict, available_area: float,
                              created_types: Optional[set] = None) -> List[ZoneGeometry]:
        """Generate typical zones using efficient grid-based tiling"""
        zones = []
        typical_zone_types = template['typical_zones']
        created_types = created_types or set()
        
        # IMPROVED: Use grid-based tiling for better coverage
        # Calculate optimal zone size for grid
        target_zone_area = 150.0  # Target ~150 m² per zone (good balance)
        if available_area > 0:
            # Adjust target based on available area
            if available_area > 5000:
                target_zone_area = 200.0
            elif available_area < 1000:
                target_zone_area = 100.0
        
        # Calculate grid dimensions
        bounds = floor_polygon.bounds
        footprint_width = bounds[2] - bounds[0]
        footprint_height = bounds[3] - bounds[1]
        
        # Calculate cells per row/column to achieve target zone area
        cells_per_row = max(3, int(math.sqrt(available_area / target_zone_area)))
        cells_per_col = max(3, int(math.sqrt(available_area / target_zone_area)))
        
        # Adjust for aspect ratio
        aspect_ratio = footprint_width / footprint_height if footprint_height > 0 else 1.0
        if aspect_ratio > 1.5:
            cells_per_row = int(cells_per_row * aspect_ratio)
        elif aspect_ratio < 0.67:
            cells_per_col = int(cells_per_col / aspect_ratio)
        
        # Calculate cell size
        cell_width = footprint_width / cells_per_row
        cell_height = footprint_height / cells_per_col
        
        # Generate grid cells and clip to footprint
        zone_type_index = 0
        for row in range(cells_per_row):
            for col in range(cells_per_col):
                # Create cell rectangle
                x_min = bounds[0] + col * cell_width
                x_max = bounds[0] + (col + 1) * cell_width
                y_min = bounds[1] + row * cell_height
                y_max = bounds[1] + (row + 1) * cell_height
                
                cell_polygon = Polygon([
                    (x_min, y_min),
                    (x_max, y_min),
                    (x_max, y_max),
                    (x_min, y_max)
                ])
                
                # Clip to actual footprint
                clipped = floor_polygon.intersection(cell_polygon)
                
                # Only keep cells with sufficient area (at least 20 m²)
                if isinstance(clipped, Polygon) and clipped.area > 20.0:
                    # Select zone type (rotate through typical zones)
                    if typical_zone_types:
                        zone_type = typical_zone_types[zone_type_index % len(typical_zone_types)]
                        zone_type_index += 1
                        
                        # Skip if already created
                        if zone_type in created_types:
                            zone_type = typical_zone_types[0]  # Default fallback
                    else:
                        zone_type = 'office_private'
                    
                    zone = ZoneGeometry(
                        name=f"{zone_type}_{floor_level}",
                        polygon=clipped,
                        floor_level=floor_level,
                        height=3.0,
                        area=clipped.area,
                        perimeter=clipped.length
                    )
                    zones.append(zone)
                    if zone_type not in created_types:
                        created_types.add(zone_type)
        
        return zones
    
    def _create_zone_polygon(self, floor_polygon: Polygon, target_area: float) -> Optional[Polygon]:
        """Create a zone polygon within the floor polygon (improved implementation)"""
        # IMPROVED: Try multiple attempts with different positions and sizes
        bounds = floor_polygon.bounds
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        
        # Try up to 10 random placements
        for attempt in range(10):
            # Calculate zone dimensions
            aspect_ratio = np.random.uniform(1.0, 2.0)
            zone_width = math.sqrt(target_area / aspect_ratio)
            zone_height = target_area / zone_width
            
            # Ensure zone fits within floor
            if zone_width > width or zone_height > height:
                zone_width = min(zone_width, width * 0.9)
                zone_height = min(zone_height, height * 0.9)
                # Recalculate to maintain aspect ratio
                actual_area = zone_width * zone_height
                if actual_area < target_area * 0.5:
                    continue  # Skip if too small
            
            # Random position within floor
            max_x_offset = max(0, width - zone_width)
            max_y_offset = max(0, height - zone_height)
            
            if max_x_offset <= 0 or max_y_offset <= 0:
                continue
            
            x_offset = np.random.uniform(0, max_x_offset)
            y_offset = np.random.uniform(0, max_y_offset)
            
            zone_polygon = Polygon([
                (bounds[0] + x_offset, bounds[1] + y_offset),
                (bounds[0] + x_offset + zone_width, bounds[1] + y_offset),
                (bounds[0] + x_offset + zone_width, bounds[1] + y_offset + zone_height),
                (bounds[0] + x_offset, bounds[1] + y_offset + zone_height)
            ])
            
            # Clip to floor polygon and check if valid
            clipped = floor_polygon.intersection(zone_polygon)
            if isinstance(clipped, Polygon) and clipped.area > target_area * 0.7:
                # Fix invalid polygons using buffer(0) trick
                if not clipped.is_valid:
                    clipped = clipped.buffer(0)
                if isinstance(clipped, Polygon) and clipped.is_valid and clipped.area >= 0.1:
                    return clipped
        
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
            # Skip zones with invalid polygons
            if not zone.polygon or not zone.polygon.is_valid or zone.polygon.area < 0.1:
                continue
                
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
    
    def _generate_floor_surface(self, zone: ZoneGeometry, footprint: BuildingFootprint) -> Optional[Dict]:
        """Generate floor surface for zone"""
        # Validate polygon has sufficient area
        if not zone.polygon or zone.polygon.area < 0.1:
            return None
            
        coords = list(zone.polygon.exterior.coords[:-1])
        # Ensure we have at least 3 vertices
        if len(coords) < 3:
            return None
            
        # Remove duplicate vertices (within tolerance)
        cleaned_coords = []
        for x, y in coords:
            if not cleaned_coords or abs(x - cleaned_coords[-1][0]) > 0.001 or abs(y - cleaned_coords[-1][1]) > 0.001:
                cleaned_coords.append((x, y))
        
        # Need at least 3 unique vertices
        if len(cleaned_coords) < 3:
            return None
        
        # Reverse vertex order so outward normal points downward (tilt ~180)
        cleaned_coords = list(reversed(cleaned_coords))
        z_coord = zone.floor_level * 3.0
        
        vertices = []
        for x, y in cleaned_coords:
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
    
    def _generate_ceiling_surface(self, zone: ZoneGeometry, footprint: BuildingFootprint) -> Optional[Dict]:
        """Generate ceiling surface for zone"""
        # Validate polygon has sufficient area
        if not zone.polygon or zone.polygon.area < 0.1:
            return None
            
        coords = list(zone.polygon.exterior.coords[:-1])
        # Ensure we have at least 3 vertices
        if len(coords) < 3:
            return None
            
        # Remove duplicate vertices (within tolerance)
        cleaned_coords = []
        for x, y in coords:
            if not cleaned_coords or abs(x - cleaned_coords[-1][0]) > 0.001 or abs(y - cleaned_coords[-1][1]) > 0.001:
                cleaned_coords.append((x, y))
        
        # Need at least 3 unique vertices
        if len(cleaned_coords) < 3:
            return None
        
        z_coord = (zone.floor_level + 1) * 3.0
        
        vertices = []
        for x, y in cleaned_coords:
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
            
            # Skip walls with zero length (same start and end points)
            # Use a small tolerance to account for floating point precision
            if abs(x2 - x1) < 0.001 and abs(y2 - y1) < 0.001:
                continue
            
            # Calculate wall area to ensure it's not zero
            wall_length = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
            wall_height = z_top - z_bottom
            wall_area = wall_length * wall_height
            
            # Skip walls with very small area (< 0.01 m²)
            if wall_area < 0.01:
                continue
            
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
