"""
Shading and Daylighting Module
Provides external/internal shading, daylight controls, and advanced lighting controls
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class ShadingElement:
    """Represents a shading element"""
    name: str
    shading_type: str  # 'External', 'Internal', 'Overhang', 'Fin'
    vertices: List[Tuple[float, float, float]]
    transmittance: float
    reflectivity: float


class ShadingDaylightingEngine:
    """Manages shading and daylighting features"""
    
    def __init__(self):
        self.shading_templates = self._load_shading_templates()
    
    def _load_shading_templates(self) -> Dict:
        """Load shading templates for different building types"""
        return {
            'office': {
                'external_shading_probability': 0.7,
                'internal_shading': True,
                'overhang_depth': 0.6,  # meters
                'fin_depth': 0.4,  # meters
                'shading_transmittance': 0.2
            },
            'residential': {
                'external_shading_probability': 0.5,
                'internal_shading': True,
                'overhang_depth': 0.3,
                'fin_depth': 0.2,
                'shading_transmittance': 0.3
            },
            'retail': {
                'external_shading_probability': 0.3,
                'internal_shading': False,
                'overhang_depth': 0.5,
                'fin_depth': 0.3,
                'shading_transmittance': 0.4
            }
        }
    
    def generate_window_shading(self, window_name: str, window_surface_name: str,
                              building_type: str, orientation: str) -> str:
        """Generate shading object for a window"""
        template = self.shading_templates.get(building_type, self.shading_templates['office'])
        
        # Generate overhang if appropriate for orientation
        overhang = ""
        if orientation in ['South', 'East', 'West']:
            overhang = self._generate_overhang(window_name, window_surface_name, 
                                              building_type, template)
        
        # Generate fins if appropriate
        fins = ""
        if orientation in ['East', 'West']:
            fins = self._generate_fins(window_name, window_surface_name,
                                      building_type, template)
        
        # Generate interior shading
        interior_shading = ""
        if template['internal_shading']:
            interior_shading = self._generate_interior_shading(window_name, window_surface_name,
                                                             template)
        
        return overhang + fins + interior_shading
    
    def _generate_overhang(self, window_name: str, window_surface_name: str,
                          building_type: str, template: Dict) -> str:
        """Generate overhang shading"""
        overhang_name = f"{window_name}_Overhang"
        depth = template['overhang_depth']
        
        # Overhang (simple horizontal shade above window)
        overhang = f"""Shading:Building:Detailed,
  {overhang_name},                    !- Name
  {window_surface_name},              !- Base Surface Name
  ,                                   !- Shading Surface Group
  3,                                  !- Number of Vertices
  -2.0,  2.0,  3.0,                   !- Vertex 1 X, Y, Z {{m}}
   2.0,  2.0,  3.0,                   !- Vertex 2 X, Y, Z {{m}}
   0.0, {depth:.2f},  3.0;            !- Vertex 3 X, Y, Z {{m}}

"""
        return overhang
    
    def _generate_fins(self, window_name: str, window_surface_name: str,
                      building_type: str, template: Dict) -> str:
        """Generate vertical fin shading"""
        fin_name = f"{window_name}_Fin"
        depth = template['fin_depth']
        
        # Vertical fin
        fin = f"""Shading:Building:Detailed,
  {fin_name},                         !- Name
  {window_surface_name},              !- Base Surface Name
  ,                                   !- Shading Surface Group
  4,                                  !- Number of Vertices
   2.0,  0.0,  0.0,                   !- Vertex 1 X, Y, Z {{m}}
   2.0,  0.0,  2.0,                   !- Vertex 2 X, Y, Z {{m}}
  {depth:.2f},  0.0,  2.0,            !- Vertex 3 X, Y, Z {{m}}
  {depth:.2f},  0.0,  0.0;            !- Vertex 4 X, Y, Z {{m}}

"""
        return fin
    
    def _generate_interior_shading(self, window_name: str, window_surface_name: str,
                                  template: Dict) -> str:
        """Generate interior shading control"""
        shading_schedule = f"{window_name}_ShadingSchedule"
        
        # Window Shading Control
        shading_control = f"""WindowMaterial:Shade,
  {window_name}_Shade_Material,       !- Name
  SpectralAverage,                    !- Optical Data Type
  0.2,                                !- Solar Transmittance
  0.5,                                !- Solar Reflectance
  0.3,                                !- Visible Transmittance
  0.5,                                !- Visible Reflectance
  0.0,                                !- Infrared Hemispherical Emissivity
  0.90,                               !- Infrared Transmittance
  0.05,                               !- Thickness {{m}}
  0.005,                              !- Conductivity {{W/m-K}}
  3.0,                                !- Density {{kg/m3}}
  1200,                               !- Specific Heat {{J/kg-K}}
  0.0,                                !- Thermal Absorptance
  0.0,                                !- Solar Absorptance
  0.0;                                !- Visible Absorptance

WindowShadingControl,
  {window_name}_ShadingControl,       !- Name
  {window_name},                      !- Shading Control Sequence Number
  1,                                  !- Multiple Surface Control Type
  OnIfScheduleAllows,                 !- Shading Control Type
  ,                                   !- Shading Type
  ,                                   !- Construction with Shading Name
  {shading_schedule},                 !- Schedule Name
  20.0,                               !- Setpoint {{W/m2}}
  No,                                 !- Shading Control Is Scheduled
  Yes,                                !- Glare Control Is Active
  ,                                   !- Shading Device Material Name
  Closed,                             !- Type of Slat Angle Control for Blinds
  ,                                   !- Slat Angle Schedule Name
  ,                                   !- Setpoint 2 {{W/m2}}
  Linear,                             !- Daylighting Control Object Type
  ,                                   !- Fenestration Surface 1 Name
  ;                                   !- ... (additional fenestration surfaces)

Schedule:Compact,
  {shading_schedule},                 !- Name
  Control,                            !- Schedule Type Limits Name
  Through: 12/31,
  For: AllDays,
  Until: 24:00,0;

"""
        return shading_control
    
    def generate_daylight_controls(self, zone_name: str, building_type: str) -> str:
        """Generate daylighting controls for a zone"""
        
        # Daylighting:Controls
        daylighting_controls = f"""Daylighting:Controls,
  {zone_name}_Daylight,               !- Name
  {zone_name}_Zone,                   !- Zone Name
  SplitFlux,                          !- Daylighting Method
  ,                                   !- Availability Schedule Name
  Continuous,                         !- Lighting Control Type
  300,                                !- Minimum Input Power Fraction for Continuous or ContinuousOff Dimming Control
  0.2,                                !- Minimum Light Output Fraction for Continuous or ContinuousOff Dimming Control
  ,                                   !- Number of Stepped Control Steps
  ,                                   !- Probability Lighting will be Reset When Needed in Manual Stepped Control
  {zone_name}_ReferencePoint1,        !- Glare Calculation Daylighting Reference Point Name
  18000,                              !- Glare Calculation Azimuth Angle of View Direction Clockwise from Zone yAxis {{deg}}
  0.8,                                !- Glare Calculation Maximum Allowable Discomfort Glare Index
  1.0,                                !- Glare Calculation Minimum Allowable Illuminance Setpoint {{lux}}
  -1,                                 !- DElight Gridding Resolution
  ,                                   !- Control:Zone name
  0.9,                                !- Fraction of Zone Controlled by Reference Point 1
  10000,                              !- Illuminance Setpoint at Reference Point 1 {{lux}}
  ,                                   !- Glare Setpoint at Reference Point 1
  ,                                   !- Illuminance Setpoint at Reference Point 2 {{lux}}
  ,                                   !- Glare Setpoint at Reference Point 2
  ,                                   !- Angle Factor for Reference Point 1
  ,                                   !- Fraction of Zone Controlled by Reference Point 2
  ,                                   !- Angle Factor for Reference Point 2
  1;                                  !- ID-Algorithm

"""
        
        # Daylighting:ReferencePoint
        reference_point = f"""Daylighting:ReferencePoint,
  {zone_name}_ReferencePoint1,        !- Name
  {zone_name}_Zone,                   !- Zone Name
  2.0,                                !- X-Coordinate of Reference Point {{m}}
  2.0,                                !- Y-Coordinate of Reference Point {{m}}
  0.8;                                !- Z-Coordinate of Reference Point {{m}}

"""
        
        return daylighting_controls + reference_point
    
    def generate_lighting_control_schedule(self, zone_name: str, building_type: str) -> str:
        """Generate lighting control schedule"""
        
        # Lighting control schedule (based on daylighting)
        control_schedule = f"""Schedule:Compact,
  {zone_name}_LightingControl,        !- Name
  Fraction,                           !- Schedule Type Limits Name
  Through: 3/31,
  For: AllDays,
  Until: 6:00,0.0,
  Until: 7:00,0.3,
  Until: 8:00,0.7,
  Until: 18:00,1.0,
  Until: 19:00,0.8,
  Until: 20:00,0.5,
  Until: 24:00,0.3,
  Through: 9/30,
  For: AllDays,
  Until: 6:00,0.0,
  Until: 7:00,0.2,
  Until: 8:00,0.6,
  Until: 19:00,1.0,
  Until: 20:00,0.8,
  Until: 21:00,0.5,
  Until: 24:00,0.3,
  Through: 12/31,
  For: AllDays,
  Until: 7:00,0.0,
  Until: 8:00,0.3,
  Until: 9:00,0.7,
  Until: 17:00,1.0,
  Until: 18:00,0.8,
  Until: 19:00,0.5,
  Until: 24:00,0.3;

"""
        return control_schedule
    
    def generate_tubular_daylight_device(self, zone_name: str) -> str:
        """Generate tubular daylighting device (TDD)"""
        
        tdd = f"""DaylightingDevice:Tubular,
  {zone_name}_TDD1,                   !- Name
  {zone_name}_Dome,                   !- Dome Name
  ,                                   !- Transition Zone Name
  {zone_name}_Diffuser,               !- Diffuser Name
  ,                                   !- Construction Name
  0.05,                               !- Diameter {{m}}
  0.60,                               !- Total Length {{m}}
  0.80,                               !- Effective Thermal Resistance {{m2-K/W}}
  0.60;                               !- Transmittance

FenestrationSurface:Detailed,
  {zone_name}_Dome,                   !- Name
  TubularDaylightDome,                !- Surface Type
  TDD_Dome,                           !- Construction Name
  {zone_name}_RoofSurface,            !- Building Surface Name
  ,                                   !- Outside Boundary Condition Object
  AutoCalculate,                      !- View Factor to Ground
  ,                                   !- Frame and Divider Name
  1.0000,                             !- Multiplier
  4,                                  !- Number of Vertices
  5.0, 5.0, 5.5,                      !- Vertex 1 X, Y, Z {{m}}
  6.0, 5.0, 5.5,                      !- Vertex 2 X, Y, Z {{m}}
  6.0, 6.0, 5.5,                      !- Vertex 3 X, Y, Z {{m}}
  5.0, 6.0, 5.5;                      !- Vertex 4 X, Y, Z {{m}}

FenestrationSurface:Detailed,
  {zone_name}_Diffuser,               !- Name
  TubularDaylightDiffuser,            !- Surface Type
  TDD_Diffuser,                       !- Construction Name
  {zone_name}_Ceiling,                !- Building Surface Name
  ,                                   !- Outside Boundary Condition Object
  AutoCalculate,                      !- View Factor to Ground
  ,                                   !- Frame and Divider Name
  1.0000,                             !- Multiplier
  4,                                  !- Number of Vertices
  5.0, 5.0, 3.0,                      !- Vertex 1 X, Y, Z {{m}}
  6.0, 5.0, 3.0,                      !- Vertex 2 X, Y, Z {{m}}
  6.0, 6.0, 3.0,                      !- Vertex 3 X, Y, Z {{m}}
  5.0, 6.0, 3.0;                      !- Vertex 4 X, Y, Z {{m}}

"""
        return tdd


