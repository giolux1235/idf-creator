"""
BESTEST (Building Energy Simulation Test) Compliance Validator
Validates IDF files against BESTEST criteria and ASHRAE 140 standards
"""
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from .idf_validator import ValidationError


@dataclass
class BESTESTCriteria:
    """BESTEST validation criteria"""
    name: str
    description: str
    check_function: str
    severity: str  # 'error', 'warning', 'info'


class BESTESTValidator:
    """Validates IDF files against BESTEST compliance criteria"""
    
    # BESTEST building categories
    BESTEST_BUILDINGS = {
        '600': 'Base Case (High Mass)',
        '610': 'Base Case (Low Mass)',
        '620': 'Base Case (Low Mass, Low Infiltration)',
        '630': 'Base Case (High Mass, High Solar)',
        '900': 'Massless Case',
        '910': 'Massless Case (Low Infiltration)',
        '920': 'Massless Case (No Solar)',
        '930': 'Massless Case (High Solar)',
    }
    
    # Typical BESTEST ranges for key metrics
    BESTEST_RANGES = {
        'annual_heating': (1000, 3000),  # kWh/year for base cases
        'annual_cooling': (500, 2500),   # kWh/year for base cases
        'peak_heating': (2, 8),          # kW for base cases
        'peak_cooling': (1.5, 6),        # kW for base cases
    }
    
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.compliance_score = 0.0
        self.total_checks = 0
    
    def validate_bestest_compliance(self, idf_content: str, 
                                    building_category: Optional[str] = None) -> Dict:
        """
        Validate IDF file against BESTEST criteria.
        
        Args:
            idf_content: Complete IDF file as string
            building_category: BESTEST building category (optional)
            
        Returns:
            Validation results dictionary
        """
        self.errors = []
        self.warnings = []
        self.compliance_score = 0.0
        self.total_checks = 0
        
        # Run BESTEST checks
        self._check_required_objects(idf_content)
        self._check_building_geometry(idf_content)
        self._check_material_properties(idf_content)
        self._check_infiltration(idf_content)
        self._check_internal_loads(idf_content)
        self._check_hvac_controls(idf_content)
        self._check_outputs(idf_content)
        
        # Calculate compliance score
        if self.total_checks > 0:
            passed_checks = self.total_checks - len(self.errors) - len(self.warnings)
            self.compliance_score = (passed_checks / self.total_checks) * 100
        
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'compliance_score': self.compliance_score,
            'total_checks': self.total_checks
        }
    
    def _check_required_objects(self, content: str):
        """Verify all required objects for BESTEST compliance"""
        required = [
            'Version',
            'Building',
            'SimulationControl',
            'RunPeriod',
            'Timestep',
            'Site:Location',
            'Zone',
            'Material',
            'Construction',
            'BuildingSurface:Detailed',
        ]
        
        for obj_type in required:
            self.total_checks += 1
            if not re.search(rf'^{re.escape(obj_type)},', content, re.MULTILINE):
                self.errors.append(ValidationError(
                    severity='error',
                    message=f'BESTEST: Missing required object: {obj_type}',
                    object_type=obj_type
                ))
            else:
                self.compliance_score += 1
    
    def _check_building_geometry(self, content: str):
        """Verify building geometry meets BESTEST requirements"""
        # BESTEST typically requires rectangular building
        # Check for rectangular geometry (not complex polygons)
        zone_pattern = r'Zone,\s*\n\s*([^,\n]+),'
        zones = re.findall(zone_pattern, content)
        
        for zone_name in zones:
            self.total_checks += 1
            zone_name = zone_name.strip()
            
            # Count surfaces per zone
            surface_pattern = rf'BuildingSurface:Detailed,\s*\n\s*([^,\n]+),\s*\n[^;]*?Zone Name\s*,\s*\n\s*{re.escape(zone_name)}[,\n]'
            surfaces = re.findall(surface_pattern, content, re.DOTALL)
            
            # BESTEST buildings typically have 6 surfaces (4 walls, floor, roof)
            if len(surfaces) < 4:
                self.warnings.append(ValidationError(
                    severity='warning',
                    message=f'BESTEST: Zone {zone_name} has {len(surfaces)} surfaces (expected 4-6 for rectangular building)',
                    object_type='Zone',
                    object_name=zone_name
                ))
            else:
                self.compliance_score += 0.5
    
    def _check_material_properties(self, content: str):
        """Verify material properties are within BESTEST ranges"""
        # Extract materials
        material_pattern = r'Material,\s*\n\s*([^,\n]+),\s*\n[^;]+'
        materials = re.findall(material_pattern, content, re.DOTALL)
        
        for material in materials:
            # Extract conductivity
            cond_pattern = r'Conductivity\s*,\s*\n\s*([^,\n]+)'
            cond_match = re.search(cond_pattern, material, re.DOTALL)
            
            if cond_match:
                self.total_checks += 1
                try:
                    conductivity = float(cond_match.group(1).strip())
                    
                    # BESTEST materials typically have conductivity 0.04-2.0 W/m-K
                    if conductivity < 0.01 or conductivity > 10:
                        self.warnings.append(ValidationError(
                            severity='warning',
                            message=f'BESTEST: Material conductivity {conductivity} W/m-K outside typical range (0.04-2.0)',
                            object_type='Material'
                        ))
                    else:
                        self.compliance_score += 0.3
                except ValueError:
                    pass
    
    def _check_infiltration(self, content: str):
        """Verify infiltration rates are within BESTEST ranges"""
        # Extract ZoneInfiltration:DesignFlowRate objects
        infiltration_pattern = r'ZoneInfiltration:DesignFlowRate,\s*\n\s*([^,\n]+),\s*\n[^;]+'
        infiltrations = re.findall(infiltration_pattern, content, re.DOTALL)
        
        for infiltration in infiltrations:
            # Extract air changes per hour
            ach_pattern = r'Air Changes per Hour\s*,\s*\n\s*([^,\n]+)'
            ach_match = re.search(ach_pattern, infiltration, re.DOTALL)
            
            if ach_match:
                self.total_checks += 1
                try:
                    ach = float(ach_match.group(1).strip())
                    
                    # BESTEST infiltration typically 0.25-0.5 ACH
                    if ach < 0.1 or ach > 2.0:
                        self.warnings.append(ValidationError(
                            severity='warning',
                            message=f'BESTEST: Infiltration rate {ach} ACH outside typical range (0.25-0.5)',
                            object_type='ZoneInfiltration:DesignFlowRate'
                        ))
                    else:
                        self.compliance_score += 0.3
                except ValueError:
                    pass
    
    def _check_internal_loads(self, content: str):
        """Verify internal loads are within BESTEST ranges"""
        # BESTEST typically has minimal or zero internal loads
        # Check for People, Lights, ElectricEquipment
        people_count = len(re.findall(r'People,', content))
        lights_count = len(re.findall(r'Lights,', content))
        equipment_count = len(re.findall(r'ElectricEquipment,', content))
        
        self.total_checks += 1
        total_loads = people_count + lights_count + equipment_count
        
        # BESTEST base cases often have zero internal loads
        if total_loads == 0:
            self.compliance_score += 1
        elif total_loads > 10:
            self.warnings.append(ValidationError(
                severity='warning',
                message=f'BESTEST: High number of internal load objects ({total_loads}), base cases typically have minimal loads',
                object_type='Internal Loads'
            ))
        else:
            self.compliance_score += 0.5
    
    def _check_hvac_controls(self, content: str):
        """Verify HVAC controls meet BESTEST requirements"""
        # BESTEST typically uses simple HVAC or ideal loads
        # Check for Ideal Loads system
        ideal_loads_pattern = r'ZoneHVAC:IdealLoadsAirSystem'
        has_ideal_loads = bool(re.search(ideal_loads_pattern, content))
        
        # Check for setpoint managers
        setpoint_pattern = r'SetpointManager'
        has_setpoints = bool(re.search(setpoint_pattern, content))
        
        self.total_checks += 1
        if has_ideal_loads or has_setpoints:
            self.compliance_score += 1
        else:
            self.warnings.append(ValidationError(
                severity='warning',
                message='BESTEST: No ideal loads or setpoint managers found (BESTEST typically uses simple HVAC)',
                object_type='HVAC Controls'
            ))
    
    def _check_outputs(self, content: str):
        """Verify required outputs for BESTEST compliance"""
        # BESTEST requires specific output variables
        required_outputs = [
            'Zone Mean Air Temperature',
            'Zone Total Heating Energy',
            'Zone Total Cooling Energy',
        ]
        
        # Check for Output:Variable objects
        output_pattern = r'Output:Variable[^;]*?Variable Name\s*,\s*\n\s*([^,\n]+)'
        outputs = re.findall(output_pattern, content, re.DOTALL)
        output_names = [out.strip().lower() for out in outputs]
        
        found_outputs = 0
        for req_out in required_outputs:
            self.total_checks += 1
            req_lower = req_out.lower()
            if any(req_lower in out for out in output_names):
                found_outputs += 1
                self.compliance_score += 0.3
            else:
                self.warnings.append(ValidationError(
                    severity='warning',
                    message=f'BESTEST: Recommended output variable not found: {req_out}',
                    object_type='Output:Variable'
                ))


def validate_bestest(idf_content: str, building_category: Optional[str] = None) -> Dict:
    """
    Convenience function to validate BESTEST compliance.
    
    Args:
        idf_content: Complete IDF file as string
        building_category: BESTEST building category (optional)
        
    Returns:
        Validation results dictionary
    """
    validator = BESTESTValidator()
    return validator.validate_bestest_compliance(idf_content, building_category)

