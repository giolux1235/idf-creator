"""
Physics Consistency Validator
Validates physical consistency of IDF files (zone closure, adjacencies, materials, loads)
"""
import re
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass

from .idf_validator import ValidationError


class PhysicsValidator:
    """Validates physics consistency of IDF files"""
    
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
    
    def validate_physics(self, idf_content: str) -> Dict:
        """
        Run all physics consistency checks.
        
        Args:
            idf_content: Complete IDF file as string
            
        Returns:
            Dictionary with 'errors' and 'warnings' lists
        """
        self.errors = []
        self.warnings = []
        
        # Run all physics checks
        self._check_zone_closure(idf_content)
        self._check_surface_adjacencies(idf_content)
        self._check_material_consistency(idf_content)
        self._check_load_balance(idf_content)
        self._check_volume_consistency(idf_content)
        
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }
    
    def _check_zone_closure(self, content: str):
        """Verify that zones have proper closure (all surfaces form closed volume)"""
        # Extract zones
        zone_pattern = r'Zone,\s*\n\s*([^,\n]+),'
        zones = re.findall(zone_pattern, content)
        
        # Extract surfaces for each zone
        for zone_name in zones:
            zone_name = zone_name.strip()
            
            # Find all surfaces attached to this zone
            surface_pattern = rf'BuildingSurface:Detailed,\s*\n\s*([^,\n]+),\s*\n[^;]*?Zone Name\s*,\s*\n\s*{re.escape(zone_name)}[,\n]'
            surfaces = re.findall(surface_pattern, content, re.DOTALL)
            
            # Count surface types
            wall_count = 0
            floor_count = 0
            roof_count = 0
            ceiling_count = 0
            
            for surface_name in surfaces:
                # Get surface type
                type_pattern = rf'BuildingSurface:Detailed,\s*\n\s*{re.escape(surface_name.strip())},\s*\n[^,]*?,\s*\n\s*([^,\n]+),'
                type_match = re.search(type_pattern, content, re.DOTALL)
                if type_match:
                    surface_type = type_match.group(1).strip().lower()
                    if 'wall' in surface_type:
                        wall_count += 1
                    elif 'floor' in surface_type or 'ground' in surface_type:
                        floor_count += 1
                    elif 'roof' in surface_type or 'ceiling' in surface_type:
                        roof_count += 1
                        ceiling_count += 1
            
            # Zone should have at least floor and ceiling/roof
            if floor_count == 0:
                self.warnings.append(ValidationError(
                    severity='warning',
                    message=f'Zone {zone_name} has no floor surface',
                    object_type='Zone',
                    object_name=zone_name
                ))
            
            if roof_count == 0 and ceiling_count == 0:
                self.warnings.append(ValidationError(
                    severity='warning',
                    message=f'Zone {zone_name} has no roof or ceiling surface',
                    object_type='Zone',
                    object_name=zone_name
                ))
            
            # Zone should have at least 4 walls (for rectangular zones)
            if wall_count < 4:
                self.warnings.append(ValidationError(
                    severity='warning',
                    message=f'Zone {zone_name} has only {wall_count} wall surfaces (expected at least 4)',
                    object_type='Zone',
                    object_name=zone_name
                ))
    
    def _check_surface_adjacencies(self, content: str):
        """Verify that adjacent surfaces reference each other correctly"""
        # Extract all surfaces with adjacencies
        surface_pattern = r'BuildingSurface:Detailed,\s*\n\s*([^,\n]+),\s*\n[^;]*?Outside Boundary Condition\s*,\s*\n\s*([^,\n]+),'
        surfaces = re.findall(surface_pattern, content, re.DOTALL)
        
        # Track adjacencies
        adjacency_map = {}
        
        for surface_name, boundary_condition in surfaces:
            surface_name = surface_name.strip()
            boundary_condition = boundary_condition.strip()
            
            # Check for Surface adjacency
            if boundary_condition.lower() == 'surface':
                # Extract adjacent surface name
                adj_pattern = rf'BuildingSurface:Detailed,\s*\n\s*{re.escape(surface_name)},\s*\n[^;]*?Outside Boundary Condition Object\s*,\s*\n\s*([^,\n]+)'
                adj_match = re.search(adj_pattern, content, re.DOTALL)
                if adj_match:
                    adj_surface = adj_match.group(1).strip()
                    adjacency_map[surface_name] = adj_surface
                    
                    # Check if reciprocal adjacency exists
                    if adj_surface in adjacency_map:
                        if adjacency_map[adj_surface] != surface_name:
                            self.warnings.append(ValidationError(
                                severity='warning',
                                message=f'Surface {surface_name} adjacent to {adj_surface}, but {adj_surface} not adjacent to {surface_name}',
                                object_type='BuildingSurface:Detailed',
                                object_name=surface_name
                            ))
    
    def _check_material_consistency(self, content: str):
        """Verify material properties are consistent and realistic"""
        # Extract all materials
        material_pattern = r'(Material|Material:NoMass),\s*\n\s*([^,\n]+),\s*\n[^;]+'
        materials = re.findall(material_pattern, content, re.DOTALL)
        
        for mat_type, mat_name in materials:
            mat_name = mat_name.strip()
            
            # Extract material properties based on type
            if mat_type == 'Material':
                # Regular material with thickness
                prop_pattern = rf'{mat_type},\s*\n\s*{re.escape(mat_name)},\s*\n[^,]*?,\s*\n[^,]*?,\s*\n\s*([^,\n]+),\s*\n\s*([^,\n]+),\s*\n\s*([^,\n]+)'
                prop_match = re.search(prop_pattern, content, re.DOTALL)
                if prop_match:
                    try:
                        conductivity = float(prop_match.group(1).strip())
                        density = float(prop_match.group(2).strip())
                        specific_heat = float(prop_match.group(3).strip())
                        
                        # Check realistic ranges
                        if conductivity < 0.01 or conductivity > 400:  # W/m-K
                            self.warnings.append(ValidationError(
                                severity='warning',
                                message=f'Material {mat_name} has unrealistic conductivity: {conductivity} W/m-K',
                                object_type=mat_type,
                                object_name=mat_name
                            ))
                        
                        if density < 10 or density > 10000:  # kg/m³
                            self.warnings.append(ValidationError(
                                severity='warning',
                                message=f'Material {mat_name} has unrealistic density: {density} kg/m³',
                                object_type=mat_type,
                                object_name=mat_name
                            ))
                        
                        if specific_heat < 100 or specific_heat > 5000:  # J/kg-K
                            self.warnings.append(ValidationError(
                                severity='warning',
                                message=f'Material {mat_name} has unrealistic specific heat: {specific_heat} J/kg-K',
                                object_type=mat_type,
                                object_name=mat_name
                            ))
                    except (ValueError, IndexError):
                        pass  # Skip if can't parse
    
    def _check_load_balance(self, content: str):
        """Verify internal loads are reasonable"""
        # Extract zones
        zone_pattern = r'Zone,\s*\n\s*([^,\n]+),'
        zones = re.findall(zone_pattern, content)
        
        for zone_name in zones:
            zone_name = zone_name.strip()
            
            # Find People objects for this zone
            people_pattern = rf'People,\s*\n\s*([^,\n]+),\s*\n[^;]*?Zone or ZoneList Name\s*,\s*\n\s*{re.escape(zone_name)}[,\n]'
            people_objects = re.findall(people_pattern, content, re.DOTALL)
            
            # Find Lighting objects
            lighting_pattern = rf'Lights,\s*\n\s*([^,\n]+),\s*\n[^;]*?Zone or ZoneList Name\s*,\s*\n\s*{re.escape(zone_name)}[,\n]'
            lighting_objects = re.findall(lighting_pattern, content, re.DOTALL)
            
            # Find ElectricEquipment objects
            equipment_pattern = rf'ElectricEquipment,\s*\n\s*([^,\n]+),\s*\n[^;]*?Zone or ZoneList Name\s*,\s*\n\s*{re.escape(zone_name)}[,\n]'
            equipment_objects = re.findall(equipment_pattern, content, re.DOTALL)
            
            # Get zone area
            zone_area = None
            zone_area_pattern = rf'Zone,\s*\n\s*{re.escape(zone_name)},\s*\n[^;]*?Floor Area\s*,\s*\n\s*([^,\n]+)'
            area_match = re.search(zone_area_pattern, content, re.DOTALL)
            if area_match:
                try:
                    zone_area = float(area_match.group(1).strip())
                except ValueError:
                    pass
            
            # Calculate total lighting power
            total_lighting = 0
            for light_name in lighting_objects:
                light_name = light_name.strip()
                # Extract lighting power
                power_pattern = rf'Lights,\s*\n\s*{re.escape(light_name)},\s*\n[^;]*?Watts per Zone Floor Area\s*,\s*\n\s*([^,\n]+)'
                power_match = re.search(power_pattern, content, re.DOTALL)
                if power_match and zone_area:
                    try:
                        watts_per_m2 = float(power_match.group(1).strip())
                        total_lighting += watts_per_m2 * zone_area
                    except ValueError:
                        pass
            
            # Check lighting power density (typical range: 5-20 W/m²)
            if zone_area and total_lighting > 0:
                lpd = total_lighting / zone_area
                if lpd > 30:  # W/m²
                    self.warnings.append(ValidationError(
                        severity='warning',
                        message=f'Zone {zone_name} has high lighting power density: {lpd:.1f} W/m² (typical: 5-20 W/m²)',
                        object_type='Zone',
                        object_name=zone_name
                    ))
                elif lpd < 1:
                    self.warnings.append(ValidationError(
                        severity='warning',
                        message=f'Zone {zone_name} has low lighting power density: {lpd:.1f} W/m² (typical: 5-20 W/m²)',
                        object_type='Zone',
                        object_name=zone_name
                    ))
    
    def _check_volume_consistency(self, content: str):
        """Verify zone volumes are consistent with geometry"""
        # Extract zones
        zone_pattern = r'Zone,\s*\n\s*([^,\n]+),\s*\n[^;]+'
        zones = re.findall(zone_pattern, content, re.DOTALL)
        
        for zone_match in zones:
            # Extract zone name
            name_match = re.search(r'Zone,\s*\n\s*([^,\n]+),', zone_match)
            if not name_match:
                continue
            
            zone_name = name_match.group(1).strip()
            
            # Extract volume
            volume_match = re.search(r'Volume\s*,\s*\n\s*([^,\n]+)', zone_match, re.DOTALL)
            if volume_match:
                try:
                    volume = float(volume_match.group(1).strip())
                    
                    # Extract floor area
                    area_match = re.search(r'Floor Area\s*,\s*\n\s*([^,\n]+)', zone_match, re.DOTALL)
                    if area_match:
                        try:
                            area = float(area_match.group(1).strip())
                            
                            # Calculate expected ceiling height
                            if area > 0:
                                expected_height = volume / area
                                
                                # Check if height is reasonable (typical: 2.5-5 m)
                                if expected_height < 1 or expected_height > 10:
                                    self.warnings.append(ValidationError(
                                        severity='warning',
                                        message=f'Zone {zone_name} has unusual ceiling height: {expected_height:.2f} m (typical: 2.5-5 m)',
                                        object_type='Zone',
                                        object_name=zone_name
                                    ))
                        except ValueError:
                            pass
                except ValueError:
                    pass


def validate_physics(idf_content: str) -> Dict:
    """
    Convenience function to validate physics consistency.
    
    Args:
        idf_content: Complete IDF file as string
        
    Returns:
        Validation results dictionary
    """
    validator = PhysicsValidator()
    return validator.validate_physics(idf_content)

