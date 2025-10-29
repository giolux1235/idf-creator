"""
Infiltration and Natural Ventilation Module
Models building air leakage and natural ventilation strategies
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import math


@dataclass
class VentilationStrategy:
    """Represents a ventilation strategy"""
    name: str
    vent_type: str  # 'Natural', 'Hybrid', 'Mechanical'
    parameters: Dict


class InfiltrationVentilationEngine:
    """Manages infiltration and natural ventilation modeling"""
    
    def __init__(self):
        self.infiltration_templates = self._load_infiltration_templates()
        self.ventilation_strategies = self._load_ventilation_strategies()
    
    def _load_infiltration_templates(self) -> Dict:
        """Load infiltration templates by building type and climate"""
        return {
            'office': {
                'air_changes_per_hour': 0.25,
                'effective_leakage_area': 0.00027,  # m²/m² envelope area
                'stack_coefficient': 0.000145,
                'wind_coefficient': 0.000174
            },
            'residential': {
                'air_changes_per_hour': 0.50,
                'effective_leakage_area': 0.00054,
                'stack_coefficient': 0.000145,
                'wind_coefficient': 0.000174
            },
            'retail': {
                'air_changes_per_hour': 0.30,
                'effective_leakage_area': 0.00032,
                'stack_coefficient': 0.000145,
                'wind_coefficient': 0.000174
            },
            'industrial': {
                'air_changes_per_hour': 0.50,
                'effective_leakage_area': 0.00081,
                'stack_coefficient': 0.000145,
                'wind_coefficient': 0.000174
            }
        }
    
    def _load_ventilation_strategies(self) -> Dict:
        """Load natural ventilation strategies"""
        return {
            'single_zone': {
                'airflow_method': 'Flow/Zone',
                'design_flow_rate': 0.02  # m³/s per m² floor area
            },
            'wind_cross': {
                'airflow_method': 'Flow/Area',
                'design_flow_rate': 0.0005  # m³/s per m²
            },
            'stack_effect': {
                'airflow_method': 'AirChanges/Hour',
                'design_flow_rate': 10  # ACH
            }
        }
    
    def generate_zone_infiltration(self, zone_name: str, building_type: str,
                                   climate_zone: str) -> str:
        """Generate zone infiltration object"""
        template = self.infiltration_templates.get(building_type, 
                                                   self.infiltration_templates['office'])
        
        # Determine infiltration rate based on climate zone
        ach = self._adjust_infiltration_for_climate(template['air_changes_per_hour'], 
                                                     climate_zone)
        
        infiltration = f"""ZoneInfiltration:DesignFlowRate,
  {zone_name}_Infiltration,           !- Name
  {zone_name}_Zone,                   !- Zone or ZoneList Name
  {zone_name}_InfiltrationSchedule,  !- Schedule Name
  AirChanges/Hour,                    !- Design Flow Rate Calculation Method
  {ach:.3f},                          !- Design Flow Rate {{m3/s}}
  ,                                   !- Flow per Zone Floor Area {{m3/s/m2}}
  ,                                   !- Flow per Exterior Surface Area {{m3/s/m2}}
  ,                                   !- Air Changes per Hour
  1.0,                                !- Constant Term Coefficient
  0.2242,                             !- Temperature Term Coefficient
  0.0,                                !- Velocity Term Coefficient
  0.0,                                !- Velocity Squared Term Coefficient

"""
        
        # Schedule for infiltration
        schedule = self._generate_infiltration_schedule(zone_name, climate_zone)
        
        return infiltration + schedule
    
    def _adjust_infiltration_for_climate(self, base_ach: float, climate_zone: str) -> float:
        """Adjust infiltration rate based on climate zone severity"""
        # Colder climates typically have more infiltration
        multipliers = {
            '1': 0.9,  # Hot
            '2': 0.95,
            '3': 1.0,
            '4': 1.1,
            '5': 1.2,
            '6': 1.3,
            '7': 1.4,
            '8': 1.5   # Subarctic
        }
        
        zone_num = climate_zone[0] if climate_zone else '3'
        return base_ach * multipliers.get(zone_num, 1.0)
    
    def _generate_infiltration_schedule(self, zone_name: str, climate_zone: str) -> str:
        """Generate infiltration schedule"""
        
        schedule = f"""Schedule:Compact,
  {zone_name}_InfiltrationSchedule,  !- Name
  Fraction,                           !- Schedule Type Limits Name
  Through: 12/31,
  For: AllDays,
  Until: 24:00,1.0;

"""
        return schedule
    
    def generate_surface_infiltration(self, surface_name: str, surface_type: str,
                                     building_type: str) -> str:
        """Generate surface-level infiltration"""
        template = self.infiltration_templates.get(building_type,
                                                   self.infiltration_templates['office'])
        
        infiltration = f"""ZoneInfiltration:EffectiveLeakageArea,
  {surface_name}_Infiltration,        !- Name
  {surface_name},                     !- Zone Name
  InfiltrationSchedule,               !- Schedule Name
  {template['effective_leakage_area']:.6f}, !- Effective Air Leakage Area {{m2}}
  1.0,                                !- Stack Coefficient
  {template['wind_coefficient']:.6f}; !- Wind Coefficient {{m3/s-m2}}

"""
        return infiltration
    
    def generate_natural_ventilation(self, zone_name: str, ventilation_type: str = 'single_zone') -> str:
        """Generate natural ventilation objects"""
        
        strategy = self.ventilation_strategies.get(ventilation_type, 
                                                   self.ventilation_strategies['single_zone'])
        
        ventilation = f"""ZoneVentilation:WindandStackOpenArea,
  {zone_name}_NaturalVentilation,     !- Name
  {zone_name}_Zone,                   !- Zone or ZoneList Name
  {zone_name}_NaturalVentSchedule,   !- Opening Area Fraction Schedule Name
  ,                                   !- Opening Area Fraction Schedule Name for Fault
  0.2,                                !- Opening Effectiveness {{dimensionless}}
  ,                                   !- Effective Angle {{degrees}}
  ,                                   !- Discharge Coefficient for Opening {{dimensionless}}
  ,                                   !- Width Factor for Opening Profile {{dimensionless}}
  ,                                   !- Height Factor for Opening Profile {{dimensionless}}
  {strategy['airflow_method']},        !- Opening Area Calculation Method
  {strategy['design_flow_rate']:.4f}, !- Opening Area {{m2}}
  ,                                   !- Opening Area per Zone Floor Area {{m2/m2}}
  ,                                   !- Opening Area per Exterior Surface Area {{m2/m2}}
  5.0,                                !- Minimum Indoor Temperature {{C}}
  30.0,                               !- Maximum Indoor Temperature {{C}}
  -10.0,                              !- Delta Temperature {{C}}
  2.0,                                !- Minimum Outdoor Temperature {{C}}
  35.0,                               !- Maximum Outdoor Temperature {{C}}
  ,                                   !- Maximum Wind Speed {{m/s}}
  0.001,                              !- Constant Term Coefficient
  0.0015,                             !- Temperature Term Coefficient
  0.0,                                !- Velocity Term Coefficient
  0.0;                                !- Velocity Squared Term Coefficient

"""
        
        # Schedule
        schedule = f"""Schedule:Compact,
  {zone_name}_NaturalVentSchedule,   !- Name
  Fraction,                           !- Schedule Type Limits Name
  Through: 12/31,
  For: AllDays,
  Until: 24:00,1.0;

"""
        
        return ventilation + schedule
    
    def generate_hybrid_ventilation(self, zone_name: str, building_type: str) -> str:
        """Generate hybrid ventilation controls"""
        
        hybrid_vent = f"""AvailabilityManager:HybridVentilation,
  {zone_name}_HybridVent,             !- Name
  {zone_name}_HVControlSchedule,     !- Ventilation Control Mode Schedule Name
  Scheduled,                          !- Use Weather File Rain Indicators
  No,                                 !- Use Weather File Wind Indicators
  16.0,                               !- Minimum Outdoor Temperature {{C}}
  28.0,                               !- Maximum Outdoor Temperature {{C}}
  ,                                   !- Minimum Outdoor Enthalpy {{J/kg}}
  ,                                   !- Maximum Outdoor Enthalpy {{J/kg}}
  ,                                   !- Minimum Outdoor Dewpoint {{C}}
  ,                                   !- Maximum Outdoor Dewpoint {{C}}
  {zone_name}_MinOAFlow,             !- Minimum Outdoor Ventilation Air Schedule Name
  ,                                   !- Opening Factor Function of Wind Speed Curve Name
  ,                                   !- Closing Factor Function of Wind Speed Curve Name
  ,                                   !- Opening Factor Function of Temperature Difference Curve Name
  ,                                   !- Closing Factor Function of Temperature Difference Curve Name
  ,                                   !- HVAC Opening Factor Schedule Name
  15;                                 !- Minimum HVAC Time Step {{minutes}}

"""
        
        # Control schedule
        control_schedule = f"""Schedule:Compact,
  {zone_name}_HVControlSchedule,     !- Name
  Discrete,                           !- Schedule Type Limits Name
  Through: 5/31,
  For: AllDays,
  Until: 24:00,1,
  Through: 8/31,
  For: AllDays,
  Until: 24:00,2,
  Through: 12/31,
  For: AllDays,
  Until: 24:00,1;

"""
        
        # Minimum OA flow schedule
        min_oa_schedule = f"""Schedule:Compact,
  {zone_name}_MinOAFlow,             !- Name
  Any Number,                         !- Schedule Type Limits Name
  Through: 12/31,
  For: AllDays,
  Until: 24:00,0.02;

"""
        
        return hybrid_vent + control_schedule + min_oa_schedule
    
    def generate_ventilation_opening(self, surface_name: str, zone_name: str,
                                    opening_fraction: float = 0.3) -> str:
        """Generate vent opening object"""
        
        opening = f"""AirflowNetwork:MultiZone:Surface,
  {surface_name}_AFN,                 !- Name
  {surface_name},                     !- Surface Name
  AirflowNetwork:MultiZone:Component:DetailedOpening, !- Leakage Component Name
  {zone_name}_Opening,                !- External Node Name
  ,                                   !- Window/Door Opening Factor, or Crack Factor {{dimensionless}}
  {opening_fraction:.2f},             !- Ventilation Control Mode Schedule Name
  Temperature,                        !- Ventilation Control Zone Temperature Setpoint Schedule Name
  20.0,                               !- Ventilation Schedule Name
  2.0;                                !- Venting Availability Schedule Name

AirflowNetwork:MultiZone:Component:DetailedOpening,
  {zone_name}_Opening,                !- Name
  {opening_fraction:.2f},             !- Air Mass Flow Coefficient When Opening is Closed {{kg/s-m}}
  0.75,                               !- Air Mass Flow Exponent When Opening is Closed
  ,                                   !- Type of Rectangular Large Vertical Opening (RLVO)
  NonPivoted,                         !- Extra Crack Length or Height of Opening to Windward
  1.0,                                !- Number of Sets of Opening Factor Data
  0.5,                                !- Opening Factor 1
  0.0,                                !- Discharge Coefficient for Opening Factor 1
  1.0,                                !- Width Factor for Opening Factor 1
  0.0,                                !- Height Factor for Opening Factor 1
  0.5,                                !- Start Height Factor for Opening Factor 1
  1.0;                                !- Opening Factor 2

AirflowNetwork:MultiZone:Zone,
  {zone_name}_Zone,                   !- Name
  {zone_name}_Zone,                   !- Zone Name
  ;                                   !- Ventilation Control Mode

"""
        return opening


