"""
Geometry Utilities for EnergyPlus Surface Orientation
Provides functions for calculating surface normals, tilt angles, and fixing vertex ordering
"""

import math
from typing import List, Tuple, Optional


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
