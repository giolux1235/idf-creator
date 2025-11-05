"""
Advanced HVAC Controls Module
Includes PID controllers, economizers, VAV controls, and advanced setpoint management
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ControlStrategy:
    """Represents an HVAC control strategy"""
    name: str
    control_type: str
    parameters: Dict
    scheduling: str


class AdvancedHVACControls:
    """Manages advanced HVAC control systems"""
    
    def __init__(self):
        self.control_templates = self._load_control_templates()
    
    def _load_control_templates(self) -> Dict:
        """Load control templates for different system types"""
        return {
            'economizer': {
                'outdoor_air_schedule': 'EconomizerSchedule',
                'min_oa_temperature': -5.0,  # °C
                'max_oa_temperature': 24.0,  # °C
                'economizer_type': 'DifferentialDryBulb',  # ✅ ENABLED - Standard practice for modern buildings
                'max_enthalpy': 66000  # J/kg (for future DifferentialEnthalpy upgrade)
            },
            'pid': {
                'proportional_gain': 0.1,
                'integral_time_constant': 1000.0,
                'derivative_time_constant': 0.0
            },
            'vav_demand_control': {
                'enable_dc': True,
                'dc_ventilation_rate': 1.2,  # L/s per person
                'dc_occupied_threshold': 0.10
            }
        }
    
    def generate_economizer(self, zone_name: str, hvac_type: str) -> str:
        """Generate economizer control for air handling unit"""
        template = self.control_templates['economizer']
        
        # Controller:OutdoorAir object
        # Field order per EnergyPlus IDD v24.2.0 (verified from /Applications/EnergyPlus-24-2-0/Energy+.idd):
        # A1: Name
        # A2: Relief Air Outlet Node Name
        # A3: Return Air Node Name
        # A4: Mixed Air Node Name
        # A5: Actuator Node Name
        # N1: Minimum Outdoor Air Flow Rate (m3/s)
        # N2: Maximum Outdoor Air Flow Rate (m3/s)
        # A6: Economizer Control Type (DifferentialDryBulb, NoEconomizer, etc.)
        # A7: Economizer Control Action Type (ModulateFlow, MinimumFlowWithBypass)
        # N3: Economizer Maximum Limit Dry-Bulb Temperature (C)
        # N4: Economizer Maximum Limit Enthalpy (J/kg)
        # N5: Economizer Maximum Limit Dewpoint Temperature (C)
        # A8: Electronic Enthalpy Limit Curve Name
        # N6: Economizer Minimum Limit Dry-Bulb Temperature (C)
        # A9: Lockout Type
        # A10: Minimum Limit Type
        # A11: Minimum Outdoor Air Schedule Name
        # A12: Minimum Fraction of Outdoor Air Schedule Name
        # A13: Maximum Fraction of Outdoor Air Schedule Name
        # ... (more optional fields)
        
        # Generate node names based on zone name (will be connected to AirLoopHVAC)
        relief_node = f"{zone_name}_ReliefNode"
        return_node = f"{zone_name}_ReturnNode"
        mixed_node = f"{zone_name}_MixedNode"
        actuator_node = f"{zone_name}_OAActuatorNode"
        
        if template['economizer_type'] == 'NoEconomizer':
            oa_controller = f"""Controller:OutdoorAir,
  {zone_name}_OAController,          !- Name
  {relief_node},                      !- Relief Air Outlet Node Name
  {return_node},                      !- Return Air Node Name
  {mixed_node},                       !- Mixed Air Node Name
  {actuator_node},                    !- Actuator Node Name
  Autosize,                           !- Minimum Outdoor Air Flow Rate {{m3/s}}
  Autosize,                           !- Maximum Outdoor Air Flow Rate {{m3/s}}
  NoEconomizer,                        !- Economizer Control Type
  ,                                   !- Economizer Control Action Type
  ,                                   !- Economizer Maximum Limit Dry-Bulb Temperature {{C}}
  ,                                   !- Economizer Maximum Limit Enthalpy {{J/kg}}
  ,                                   !- Economizer Maximum Limit Dewpoint Temperature {{C}}
  ,                                   !- Electronic Enthalpy Limit Curve Name
  ,                                   !- Economizer Minimum Limit Dry-Bulb Temperature {{C}}
  ,                                   !- Lockout Type
  ,                                   !- Minimum Limit Type
  ,                                   !- Minimum Outdoor Air Schedule Name
  ,                                   !- Minimum Fraction of Outdoor Air Schedule Name
  ;                                   !- Maximum Fraction of Outdoor Air Schedule Name

"""
        else:
            # With economizer enabled, use full field set
            oa_controller = f"""Controller:OutdoorAir,
  {zone_name}_OAController,          !- Name
  {relief_node},                      !- Relief Air Outlet Node Name
  {return_node},                      !- Return Air Node Name
  {mixed_node},                       !- Mixed Air Node Name
  {actuator_node},                    !- Actuator Node Name
  Autosize,                           !- Minimum Outdoor Air Flow Rate {{m3/s}}
  Autosize,                           !- Maximum Outdoor Air Flow Rate {{m3/s}}
  {template['economizer_type']},      !- Economizer Control Type
  ModulateFlow,                       !- Economizer Control Action Type
  {template['max_oa_temperature']:.1f}, !- Economizer Maximum Limit Dry-Bulb Temperature {{C}}
  ,                                   !- Economizer Maximum Limit Enthalpy {{J/kg}}
  ,                                   !- Economizer Maximum Limit Dewpoint Temperature {{C}}
  ,                                   !- Electronic Enthalpy Limit Curve Name
  {template['min_oa_temperature']:.1f}, !- Economizer Minimum Limit Dry-Bulb Temperature {{C}}
  ,                                   !- Lockout Type
  ,                                   !- Minimum Limit Type
  ,                                   !- Minimum Outdoor Air Schedule Name
  ,                                   !- Minimum Fraction of Outdoor Air Schedule Name
  ;                                   !- Maximum Fraction of Outdoor Air Schedule Name

"""
        return oa_controller
    
    def generate_economizer_with_nodes(self, zone_name: str, 
                                        relief_node: str, return_node: str,
                                        mixed_node: str, actuator_node: str) -> str:
        """Generate economizer control with specific node names"""
        template = self.control_templates['economizer']
        
        # Controller:OutdoorAir object with proper node connections
        # Advanced economizer with differential enthalpy (expert-level feature)
        oa_controller = f"""Controller:OutdoorAir,
  {zone_name}_OAController,          !- Name
  {relief_node},                      !- Relief Air Outlet Node Name
  {return_node},                      !- Return Air Node Name
  {mixed_node},                       !- Mixed Air Node Name
  {actuator_node},                    !- Actuator Node Name
  ,                                   !- Minimum Outdoor Air Schedule Name
  ,                                   !- Maximum Fraction of Outdoor Air Schedule Name
  ,                                   !- Minimum Outdoor Air Temperature Schedule Name
  ,                                   !- Minimum Limit Type (blank - use schedule)
  ,                                   !- Minimum Outdoor Air Flow Rate {{m3/s}}
  ,                                   !- Maximum Outdoor Air Flow Rate {{m3/s}}
  {template['economizer_type']},      !- Economizer Control Type
  LockoutWithHeating,                 !- Economizer Control Action Type
  {template['max_oa_temperature']:.1f}, !- Economizer Maximum Limit Dry-Bulb Temperature {{C}}
  0.0,                                 !- Economizer Maximum Limit Enthalpy {{J/kg}} (0 = not used)
  0.0,                                 !- Economizer Maximum Limit Dewpoint Temperature {{C}} (0 = not used)
  ,                                   !- Electronic Enthalpy Limit Curve Name
  {template['min_oa_temperature']:.1f}, !- Economizer Minimum Limit Dry-Bulb Temperature {{C}}
  LockoutWithCompressor;              !- Lockout Type

"""
        return oa_controller
    
    def generate_pid_controller(self, zone_name: str, control_variable: str) -> str:
        """Generate PID controller for precise control"""
        template = self.control_templates['pid']
        
        pid_controller = f"""Controller:WaterCoil,
  {zone_name}_PID_{control_variable}, !- Name
  {control_variable},                  !- Control Variable
  Reverse,                            !- Action
  FLOW,                               !- Actuator Variable
  {zone_name}_{control_variable}_Sensor, !- Sensor Node Name
  {zone_name}_{control_variable}_Actuator, !- Actuator Node Name
  {template['proportional_gain']:.3f}, !- Controller Convergence Tolerance
  {template['integral_time_constant']:.1f}, !- Maximum Actuated Flow {{m3/s}}
  {template['derivative_time_constant']:.2f}; !- Minimum Actuated Flow {{m3/s}}

"""
        return pid_controller
    
    def generate_zone_vav_control(self, zone_name: str, hvac_type: str) -> str:
        """Generate advanced VAV control strategy"""
        template = self.control_templates['vav_demand_control']
        
        # AvailabilityManager:OptimumStart - Expert-level feature (5-10% HVAC savings)
        # Weather-predictive optimal start algorithm
        optimum_start = f"""AvailabilityManager:OptimumStart,
  {zone_name}_OptimumStart,           !- Name
  AdaptiveASHRAE90_1,                 !- Control Algorithm (expert: adaptive algorithm)
  MaximumOfZoneList,                  !- Control Type
  60.0,                               !- Facility Time in Heating Mode {{minutes}}
  60.0,                               !- Facility Time in Cooling Mode {{minutes}}
  2.0,                                !- Throttling Range Temperature Difference {{deltaC}}
  ,                                   !- Minimum Throttling Range {{deltaC}}
  ,                                   !- Maximum Throttling Range {{deltaC}}
  {zone_name}_Zone;                   !- Control Zone Name

"""

        # AvailabilityManager:NightCycle (fallback for night operation)
        night_cycle = f"""AvailabilityManager:NightCycle,
  {zone_name}_NightCycle,             !- Name
  CycleOnAny,                         !- Control Type
  1.5,                                !- Thermostat Tolerance {{deltaC}}
  1.0,                                !- Cycling Run Time Control
  ,                                   !- Cycling Run Time {{minutes}}
  ,                                   !- Control Zone or ZoneList Name
  ,                                   !- Cooling Control Zone or ZoneList Name
  ,                                   !- Heating Control Zone or ZoneList Name
  ,                                   !- Heating Zone Fans Only Zone or ZoneList Name
  ,                                   !- Cooling Zone Fans Only Zone or ZoneList Name
  ;                                   !- Dead Band Tolerance {{deltaC}}

"""
        
        # SetpointManager:SingleZone:Reheat
        setpoint_manager = f"""SetpointManager:SingleZone:Reheat,
  {zone_name}_ReheatSPM,              !- Name
  Temperature,                        !- Control Variable
  {zone_name}_HeatingSetpoint,        !- Minimum Setpoint Temperature {{C}}
  {zone_name}_CoolingSetpoint,        !- Maximum Setpoint Temperature {{C}}
  {zone_name}_Zone,                   !- Control Zone Name
  {zone_name}_SupplyOutlet;           !- Setpoint Node or NodeList Name

"""
        
        # People:Definition for demand-controlled ventilation
        if template['enable_dc']:
            dc_ventilation = f"""People:Definition,
  {zone_name}_DCV,                    !- Name
  {template['dc_ventilation_rate']:.2f}, !- Number of People Calculation Method
  ,                                   !- Number of People
  ,                                   !- People per Zone Floor Area {{person/m2}}
  ,                                   !- Zone Floor Area per Person {{m2/person}}
  Fraction,                           !- Fraction Radiant
  0.3,                                !- Sensible Heat Fraction
  120;                                !- Activity Level Schedule Name

AvailabilityManager:OptimumStart,
  {zone_name}_OptimumStart,           !- Name
  ControlZone,                        !- Control Algorithm
  MaximumOfZoneList,                  !- Control Type
  10.0,                               !- Facility Time in Heating Mode {{minutes}}
  10.0,                               !- Facility Time in Cooling Mode {{minutes}}
  ,                                   !- Throttling Range Temperature Difference {{deltaC}}
  ,                                   !- Minimum Throttling Range {{deltaC}}
  ,                                   !- Maximum Throttling Range {{deltaC}}
  {zone_name}_Zone;                   !- Control Zone Name

"""
        else:
            dc_ventilation = ""
        
        return optimum_start + night_cycle + setpoint_manager + dc_ventilation
    
    def generate_advanced_setpoint_manager(self, zone_name: str, control_strategy: str) -> str:
        """Generate advanced setpoint managers"""
        
        if control_strategy == 'outdoor_air_reset':
            spm = f"""SetpointManager:OutdoorAirReset,
  {zone_name}_OutdoorReset,           !- Name
  Temperature,                        !- Control Variable
  22.0,                               !- Setpoint at Outdoor Low Temperature {{C}}
  16.0,                               !- Outdoor Low Temperature {{C}}
  24.0,                               !- Setpoint at Outdoor High Temperature {{C}}
  24.0;                               !- Outdoor High Temperature {{C}}

"""
        elif control_strategy == 'warmest':
            spm = f"""SetpointManager:Warmest,
  {zone_name}_WarmestSPM,             !- Name
  Temperature,                        !- Control Variable
  19.0,                               !- Maximum Setpoint Temperature {{C}}
  22.0,                               !- Minimum Setpoint Temperature {{C}}
  ,                                   !- Strategy
  ,                                   !- Setpoint Node or NodeList Name
  ;                                   !- HVAC Air Loop Name

"""
        elif control_strategy == 'coldest':
            spm = f"""SetpointManager:Coldest,
  {zone_name}_ColdestSPM,             !- Name
  Temperature,                        !- Control Variable
  24.0,                               !- Maximum Setpoint Temperature {{C}}
  21.0,                               !- Minimum Setpoint Temperature {{C}}
  ,                                   !- Strategy
  ,                                   !- Setpoint Node or NodeList Name
  ;                                   !- HVAC Air Loop Name

"""
        elif control_strategy == 'scheduled_dual':
            spm = f"""SetpointManager:Scheduled:DualSetpoint,
  {zone_name}_DualSPM,                !- Name
  Temperature,                        !- Control Variable
  {zone_name}_HeatingSetpoint,        !- High Setpoint Schedule Name
  {zone_name}_CoolingSetpoint;        !- Low Setpoint Schedule Name

"""
        else:
            spm = ""
        
        return spm
    
    def generate_unitary_control(self, zone_name: str, equipment_name: str, hvac_type: str) -> str:
        """Generate controls for unitary equipment (PTAC, RTU, etc.)"""
        
        # Thermostat setpoint
        thermostat = f"""ZoneControl:Thermostat,
  {zone_name}_Thermostat,             !- Name
  {zone_name}_Zone,                   !- Zone or ZoneList Name
  {zone_name}_ThermostatSchedule,     !- Control Type Schedule Name
  ThermostatSetpoint:DualSetpoint,    !- Control 1 Object Type
  {zone_name}_ThermostatSetpoint;     !- Control 1 Name

ThermostatSetpoint:DualSetpoint,
  {zone_name}_ThermostatSetpoint,     !- Name
  {zone_name}_HeatingSetpoint,        !- Heating Setpoint Temperature Schedule Name
  {zone_name}_CoolingSetpoint;        !- Cooling Setpoint Temperature Schedule Name

"""
        
        # Run time fraction controls for part-load operation
        runtime_frac = f"""AvailabilityManager:HybridVentilation,
  {zone_name}_HybridVent,             !- Name
  {zone_name}_HybridVentSchedule,     !- Ventilation Control Mode Schedule Name
  Scheduled,                          !- Use Weather File Rain Indicators
  No,                                 !- Use Weather File Wind Indicators
  ,                                   !- Minimum Outdoor Temperature {{C}}
  ,                                   !- Maximum Outdoor Temperature {{C}}
  ,                                   !- Minimum Outdoor Enthalpy {{J/kg}}
  ,                                   !- Maximum Outdoor Enthalpy {{J/kg}}
  ,                                   !- Minimum Outdoor Dewpoint {{C}}
  ,                                   !- Maximum Outdoor Dewpoint {{C}}
  ,                                   !- Minimum Outdoor Ventilation Air Schedule Name
  ,                                   !- Opening Factor Function of Wind Speed Curve Name
  ,                                   !- Closing Factor Function of Wind Speed Curve Name
  ,                                   !- Opening Factor Function of Wind Speed Curve Name
  ,                                   !- Closing Factor Function of Wind Speed Curve Name
  ,                                   !- HVAC Opening Factor Schedule Name
  ;                                   !- Minimum HVAC Time Step {{minutes}}

"""
        
        return thermostat + runtime_frac
    
    def generate_load_range_control(self, zone_name: str, min_load_ratio: float = 0.25) -> str:
        """Generate load range-based control"""
        
        lrc = f"""ZoneControl:Thermostatic,
  {zone_name}_LoadRangeControl,       !- Name
  {zone_name}_Zone,                   !- Zone or ZoneList Name
  {zone_name}_LoadRangeControlSchedule, !- Control Type Schedule Name
  Temperature,                        !- Control 1 Object Type
  {zone_name}_LoadRangeThermostat;    !- Control 1 Name

ZoneControl:Thermostatic,
  {zone_name}_LoadRangeControl,       !- Name
  Throttling Range,                   !- Control Method
  {zone_name}_HeatingSetpoint,        !- Heating Setpoint {{C}}
  {zone_name}_CoolingSetpoint,        !- Cooling Setpoint {{C}}
  Scheduled,                          !- All Control Type
  ;                                   !- Scheduled Values

"""
        
        return lrc
    
    def generate_schedule(self, name: str, sch_type: str = 'DualSetpoint') -> str:
        """Generate control schedules"""
        
        if sch_type == 'DualSetpoint':
            # Seasonal setpoint schedules:
            # Heating: 21°C in winter (Oct-Mar), 15°C (off) in summer (Apr-Sep)
            # Cooling: 26°C in summer (Apr-Sep), 35°C (off) in winter (Oct-Mar)
            schedule = f"""Schedule:Compact,
  {name}_HeatingSetpoint,             !- Name
  AnyNumber,                          !- Schedule Type Limits Name
  Through: 3/31,                      !- Winter: Jan-Mar
  For: AllDays,
  Until: 24:00,
  21.0,                               !- Heating setpoint 21°C in winter
  Through: 9/30,                      !- Summer: Apr-Sep
  For: AllDays,
  Until: 24:00,
  15.0,                               !- Heating off (low setpoint) in summer
  Through: 12/31,                     !- Winter: Oct-Dec
  For: AllDays,
  Until: 24:00,
  21.0;                               !- Heating setpoint 21°C in winter

Schedule:Compact,
  {name}_CoolingSetpoint,             !- Name
  AnyNumber,                          !- Schedule Type Limits Name
  Through: 3/31,                      !- Winter: Jan-Mar
  For: AllDays,
  Until: 24:00,
  35.0,                               !- Cooling off (high setpoint) in winter
  Through: 9/30,                      !- Summer: Apr-Sep
  For: AllDays,
  Until: 24:00,
  24.0,                               !- Cooling setpoint 24°C in summer
  Through: 12/31,                     !- Winter: Oct-Dec
  For: AllDays,
  Until: 24:00,
  35.0;                               !- Cooling off (high setpoint) in winter

"""
        elif sch_type == 'Economizer':
            schedule = f"""Schedule:Compact,
  {name}_Economizer,                  !- Name
  Fraction,                           !- Schedule Type Limits Name
  Through: 12/31,                     !- Field 1
  For: AllDays,                       !- Field 2
  Until: 24:00,                       !- Field 3
  1.0;                                !- Field 4

"""
        else:
            schedule = ""
        
        return schedule


