"""
Geometry Utilities for EnergyPlus Surface Orientation
Provides functions for calculating surface normals, tilt angles, and fixing vertex ordering
"""

import math
from typing import List, Tuple, Optional, Dict


def remove_coincident_vertices(vertices_3d: List[Tuple[float, float, float]], 
                               tolerance: float = 0.001) -> List[Tuple[float, float, float]]:
    """Remove coincident (duplicate) vertices from a list.
    
    Args:
        vertices_3d: List of (x, y, z) tuples
        tolerance: Minimum distance between vertices to be considered different
        
    Returns:
        List with coincident vertices removed
    """
    if len(vertices_3d) < 2:
        return vertices_3d
    
    cleaned = [vertices_3d[0]]
    for v in vertices_3d[1:]:
        # Check if this vertex is different from the last one
        last = cleaned[-1]
        dist = ((v[0] - last[0])**2 + (v[1] - last[1])**2 + (v[2] - last[2])**2)**0.5
        if dist > tolerance:
            cleaned.append(v)
    
    # Also check if first and last are coincident (for closed polygons)
    if len(cleaned) > 1:
        first = cleaned[0]
        last = cleaned[-1]
        dist = ((first[0] - last[0])**2 + (first[1] - last[1])**2 + (first[2] - last[2])**2)**0.5
        if dist <= tolerance and len(cleaned) > 2:
            # Remove last vertex if it's coincident with first
            cleaned = cleaned[:-1]
    
    return cleaned


def validate_surface_area(vertices_3d: List[Tuple[float, float, float]], 
                          min_area: float = 0.01) -> bool:
    """Validate that a surface has sufficient area.
    
    Args:
        vertices_3d: List of (x, y, z) tuples
        min_area: Minimum required area in m²
        
    Returns:
        True if surface area >= min_area, False otherwise
    """
    if len(vertices_3d) < 3:
        return False
    
    # Calculate surface area using cross product method
    # For a polygon, sum the areas of triangles formed with first vertex
    area = 0.0
    v0 = vertices_3d[0]
    
    for i in range(1, len(vertices_3d) - 1):
        v1 = vertices_3d[i]
        v2 = vertices_3d[i + 1]
        
        # Vectors from v0 to v1 and v0 to v2
        edge1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
        edge2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
        
        # Cross product magnitude = 2 * triangle area
        cross = (
            edge1[1] * edge2[2] - edge1[2] * edge2[1],
            edge1[2] * edge2[0] - edge1[0] * edge2[2],
            edge1[0] * edge2[1] - edge1[1] * edge2[0]
        )
        triangle_area = (cross[0]**2 + cross[1]**2 + cross[2]**2)**0.5 / 2.0
        area += triangle_area
    
    return area >= min_area


def calculate_surface_normal(vertices: List[Tuple[float, float, float]]) -> Tuple[float, float, float]:
    """Calculate surface normal from vertices using first three vertices.
    
    Args:
        vertices: List of (x, y, z) tuples representing surface vertices
        
    Returns:
        Normalized surface normal vector (nx, ny, nz)
    """
    if len(vertices) < 3:
        return (0.0, 0.0, 1.0)  # Default: upward
    
    # Use first three vertices to calculate normal
    v1 = vertices[0]
    v2 = vertices[1]
    v3 = vertices[2]
    
    # Calculate two edge vectors
    edge1 = (v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2])
    edge2 = (v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2])
    
    # Cross product to get normal
    normal = (
        edge1[1] * edge2[2] - edge1[2] * edge2[1],
        edge1[2] * edge2[0] - edge1[0] * edge2[2],
        edge1[0] * edge2[1] - edge1[1] * edge2[0]
    )
    
    # Normalize
    length = (normal[0]**2 + normal[1]**2 + normal[2]**2)**0.5
    if length > 0:
        return (normal[0]/length, normal[1]/length, normal[2]/length)
    return (0.0, 0.0, 1.0)


def calculate_tilt_angle(normal: Tuple[float, float, float]) -> float:
    """Calculate tilt angle from surface normal.
    
    Tilt angle is the angle from horizontal:
    - 0° = horizontal surface pointing upward
    - 180° = horizontal surface pointing downward
    
    Args:
        normal: Normalized surface normal vector (nx, ny, nz)
        
    Returns:
        Tilt angle in degrees (0-180)
    """
    # Z component of normal determines tilt
    # For horizontal surfaces: z = 1 → 0°, z = -1 → 180°
    z = normal[2]
    # Clamp to valid range for acos
    z = max(-1.0, min(1.0, z))
    tilt = math.degrees(math.acos(z))
    return tilt


def calculate_polygon_area_2d(vertices_2d: List[Tuple[float, float]]) -> float:
    """Calculate area of 2D polygon using shoelace formula.
    
    Args:
        vertices_2d: List of (x, y) tuples
        
    Returns:
        Area in square meters (always positive)
    """
    if len(vertices_2d) < 3:
        return 0.0
    
    area = 0.0
    n = len(vertices_2d)
    for i in range(n):
        j = (i + 1) % n
        area += vertices_2d[i][0] * vertices_2d[j][1]
        area -= vertices_2d[j][0] * vertices_2d[i][1]
    
    return abs(area) / 2.0


def calculate_polygon_center_2d(vertices_2d: List[Tuple[float, float]]) -> Tuple[float, float]:
    """Calculate center point of 2D polygon.
    
    Args:
        vertices_2d: List of (x, y) tuples
        
    Returns:
        Center point (cx, cy)
    """
    if not vertices_2d:
        return (0.0, 0.0)
    
    cx = sum(v[0] for v in vertices_2d) / len(vertices_2d)
    cy = sum(v[1] for v in vertices_2d) / len(vertices_2d)
    return (cx, cy)


def fix_vertex_ordering_for_wall(vertices_3d: List[Tuple[float, float, float]],
                                  zone_center_2d: Tuple[float, float]) -> List[Tuple[float, float, float]]:
    """Fix vertex ordering for wall surface to ensure normal points outward from zone.
    
    For EnergyPlus, wall normals must point outward from the zone.
    This function checks if the normal points toward or away from the zone center
    and reverses vertex order if needed.
    
    Args:
        vertices_3d: List of (x, y, z) tuples representing wall vertices
        zone_center_2d: Zone center point (cx, cy) in 2D
        
    Returns:
        List of (x, y, z) tuples with correct ordering (normal pointing outward)
    """
    if len(vertices_3d) < 3:
        return vertices_3d
    
    # Calculate current normal
    normal = calculate_surface_normal(vertices_3d)
    
    # Get wall center point (average of first 3 vertices projected to 2D)
    wall_center_x = sum(v[0] for v in vertices_3d[:3]) / min(3, len(vertices_3d))
    wall_center_y = sum(v[1] for v in vertices_3d[:3]) / min(3, len(vertices_3d))
    
    # Vector from zone center to wall center
    to_wall = (
        wall_center_x - zone_center_2d[0],
        wall_center_y - zone_center_2d[1]
    )
    
    # Normalize to wall direction
    to_wall_length = (to_wall[0]**2 + to_wall[1]**2)**0.5
    if to_wall_length > 0:
        to_wall = (to_wall[0] / to_wall_length, to_wall[1] / to_wall_length)
    else:
        # If wall center == zone center, use first edge direction
        if len(vertices_3d) >= 2:
            edge = (
                vertices_3d[1][0] - vertices_3d[0][0],
                vertices_3d[1][1] - vertices_3d[0][1]
            )
            edge_length = (edge[0]**2 + edge[1]**2)**0.5
            if edge_length > 0:
                to_wall = (edge[0] / edge_length, edge[1] / edge_length)
            else:
                to_wall = (1.0, 0.0)
        else:
            to_wall = (1.0, 0.0)
    
    # Project wall normal to 2D (ignore Z component for walls)
    wall_normal_2d = (normal[0], normal[1])
    wall_normal_length = (wall_normal_2d[0]**2 + wall_normal_2d[1]**2)**0.5
    if wall_normal_length > 0:
        wall_normal_2d = (wall_normal_2d[0] / wall_normal_length, wall_normal_2d[1] / wall_normal_length)
    else:
        wall_normal_2d = (1.0, 0.0)
    
    # Dot product: if positive, normal points away from zone (good)
    # If negative, normal points toward zone (need to reverse)
    dot_product = to_wall[0] * wall_normal_2d[0] + to_wall[1] * wall_normal_2d[1]
    
    # If dot product is negative or very small, reverse vertex order
    if dot_product < 0.1:  # Allow small tolerance for walls that are nearly radial
        return list(reversed(vertices_3d))
    
    return vertices_3d


def calculate_zone_volume_from_surfaces(surfaces: List[Dict], zone_center_2d: Tuple[float, float]) -> float:
    """Calculate zone volume using divergence theorem (Gauss's theorem).
    
    Volume = (1/3) * sum(area * (point - center) · normal) for each surface
    
    Args:
        surfaces: List of surface dictionaries with 'vertices' and 'surface_type'
        zone_center_2d: Zone center point (cx, cy) in 2D
        
    Returns:
        Zone volume in m³ (always positive)
    """
    volume = 0.0
    
    for surface in surfaces:
        if 'vertices' not in surface:
            continue
        
        # Parse vertices
        vertices = []
        for v_str in surface['vertices']:
            if isinstance(v_str, str):
                parts = v_str.split(',')
                if len(parts) >= 3:
                    try:
                        x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
                        vertices.append((x, y, z))
                    except (ValueError, IndexError):
                        continue
            elif isinstance(v_str, (list, tuple)) and len(v_str) >= 3:
                vertices.append((float(v_str[0]), float(v_str[1]), float(v_str[2])))
        
        if len(vertices) < 3:
            continue
        
        # Calculate surface area
        # For horizontal surfaces, use 2D area
        # For vertical surfaces, use 3D area
        surface_type = surface.get('surface_type', '').lower()
        
        if 'floor' in surface_type or 'ceiling' in surface_type or 'roof' in surface_type:
            # Horizontal surface: use 2D area
            vertices_2d = [(v[0], v[1]) for v in vertices]
            area = calculate_polygon_area_2d(vertices_2d)
        else:
            # Vertical surface (wall): calculate area from 3D vertices
            area = 0.0
            n = len(vertices)
            if n >= 3:
                # Use first 3 vertices to get normal and calculate area
                v1, v2, v3 = vertices[0], vertices[1], vertices[2]
                edge1 = (v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2])
                edge2 = (v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2])
                # Cross product magnitude = area of parallelogram / 2
                cross = (
                    edge1[1] * edge2[2] - edge1[2] * edge2[1],
                    edge1[2] * edge2[0] - edge1[0] * edge2[2],
                    edge1[0] * edge2[1] - edge1[1] * edge2[0]
                )
                area = (cross[0]**2 + cross[1]**2 + cross[2]**2)**0.5
                # For remaining vertices, add contribution
                for i in range(3, n):
                    # Approximate: assume surface is mostly planar
                    pass  # Simplified for now
        
        # Get surface center
        surface_center_x = sum(v[0] for v in vertices) / len(vertices)
        surface_center_y = sum(v[1] for v in vertices) / len(vertices)
        surface_center_z = sum(v[2] for v in vertices) / len(vertices)
        
        # Get surface normal
        normal = calculate_surface_normal(vertices)
        
        # Vector from zone center to surface center (extend to 3D)
        vector = (
            surface_center_x - zone_center_2d[0],
            surface_center_y - zone_center_2d[1],
            surface_center_z  # Use actual Z for vertical component
        )
        
        # Dot product: vector · normal
        dot_product = (
            vector[0] * normal[0] +
            vector[1] * normal[1] +
            vector[2] * normal[2]
        )
        
        # Volume contribution from this surface
        volume_contribution = (1.0 / 3.0) * area * dot_product
        volume += volume_contribution
    
    # Volume should be positive
    return abs(volume)


def fix_vertex_ordering_for_floor(vertices_2d: List[Tuple[float, float]], 
                                   z_coord: float) -> List[Tuple[float, float, float]]:
    """Fix vertex ordering for floor surface to ensure downward normal (tilt ~180°).
    
    For EnergyPlus with CounterClockWise vertex entry direction:
    - Floor vertices should be ordered so normal points downward when viewed from outside
    
    Args:
        vertices_2d: List of (x, y) tuples
        z_coord: Z coordinate for all vertices
        
    Returns:
        List of (x, y, z) tuples with correct ordering
    """
    if len(vertices_2d) < 3:
        return [(v[0], v[1], z_coord) for v in vertices_2d]
    
    # Convert to 3D vertices
    vertices_3d = [(v[0], v[1], z_coord) for v in vertices_2d]
    
    # Calculate current normal
    normal = calculate_surface_normal(vertices_3d)
    tilt = calculate_tilt_angle(normal)
    
    # Floor should have tilt ~180° (normal pointing downward)
    # If normal points upward (tilt < 90°), reverse vertex order
    if tilt < 90.0:
        vertices_3d = list(reversed(vertices_3d))
        normal = calculate_surface_normal(vertices_3d)
        tilt = calculate_tilt_angle(normal)
    
    # Verify tilt is near 180° (allow 5° tolerance)
    if abs(tilt - 180.0) > 5.0:
        # If still not correct, try reversing again and adjust
        # This handles edge cases where polygon winding might be ambiguous
        vertices_3d = list(reversed(vertices_3d))
        normal = calculate_surface_normal(vertices_3d)
        tilt = calculate_tilt_angle(normal)
        # If reverse made it worse, reverse back
        if abs(tilt - 180.0) > abs(180.0 - tilt):
            vertices_3d = list(reversed(vertices_3d))
    
    return vertices_3d


def fix_vertex_ordering_for_ceiling(vertices_2d: List[Tuple[float, float]], 
                                     z_coord: float) -> List[Tuple[float, float, float]]:
    """Fix vertex ordering for ceiling surface to ensure upward normal (tilt ~0°).
    
    For EnergyPlus with CounterClockWise vertex entry direction:
    - Ceiling vertices should be ordered so normal points upward when viewed from outside
    
    Args:
        vertices_2d: List of (x, y) tuples
        z_coord: Z coordinate for all vertices
        
    Returns:
        List of (x, y, z) tuples with correct ordering
    """
    if len(vertices_2d) < 3:
        return [(v[0], v[1], z_coord) for v in vertices_2d]
    
    # Convert to 3D vertices
    vertices_3d = [(v[0], v[1], z_coord) for v in vertices_2d]
    
    # Calculate current normal
    normal = calculate_surface_normal(vertices_3d)
    tilt = calculate_tilt_angle(normal)
    
    # Ceiling should have tilt ~0° (normal pointing upward)
    # If normal points downward (tilt > 90°), reverse vertex order
    if tilt > 90.0:
        vertices_3d = list(reversed(vertices_3d))
        normal = calculate_surface_normal(vertices_3d)
        tilt = calculate_tilt_angle(normal)
    
    # Verify tilt is near 0° (allow 5° tolerance)
    if abs(tilt) > 5.0:
        # If still not correct, try reversing again
        vertices_3d = list(reversed(vertices_3d))
        normal = calculate_surface_normal(vertices_3d)
        tilt = calculate_tilt_angle(normal)
        # If reverse made it worse, reverse back
        if abs(tilt) > abs(180.0 - tilt):
            vertices_3d = list(reversed(vertices_3d))
    
    return vertices_3d




