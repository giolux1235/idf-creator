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
                'min_oa_temperature': 10.0,  # °C
                'max_oa_temperature': 24.0,  # °C
                'economizer_type': 'DifferentialDryBulb'
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
        oa_controller = f"""Controller:OutdoorAir,
  {zone_name}_OAController,          !- Name
  {zone_name}_OA_Mixer,               !- Relief Air Outlet Node Name
  {zone_name}_OA_Node,                !- Return Air Node Name
  {zone_name}_Mixed_Air_Node,         !- Mixed Air Node Name
  {zone_name}_Outside_Air_Node,       !- Actuator Node Name
  ,                                   !- Minimum Outdoor Air Schedule Name
  ,                                   !- Maximum Fraction of Outdoor Air Schedule Name
  ,                                   !- Minimum Outdoor Air Temperature Schedule Name
  MinimumLimit,                       !- Minimum Limit Type
  ,                                   !- Minimum Outdoor Air Flow Rate {{m3/s}}
  ,                                   !- Maximum Outdoor Air Flow Rate {{m3/s}}
  {template['economizer_type']},      !- Economizer Control Type
  {template['min_oa_temperature']:.1f}, !- Economizer Control Action Type
  {template['max_oa_temperature']:.1f}, !- Economizer Maximum Limit Dry-Bulb Temperature {{C}}
  ,                                   !- Economizer Maximum Limit Enthalpy {{J/kg}}
  ,                                   !- Economizer Maximum Limit Dewpoint Temperature {{C}}
  LockoutWithHeating,                 !- Electronic Enthalpy Limit Curve Name
  LockoutWithCompressor,              !- Economizer Minimum Limit Dry-Bulb Temperature {{C}}
  LockoutWithHeating;                 !- Lockout Type

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
        
        # AvailabilityManager:NightCycle
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
        
        return night_cycle + setpoint_manager + dc_ventilation
    
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
            schedule = f"""Schedule:Compact,
  {name}_HeatingSetpoint,             !- Name
  Any Number,                         !- Schedule Type Limits Name
  Through: 12/31,                     !- Field 1
  For: AllDays,                       !- Field 2
  Until: 24:00,                       !- Field 3
  21.0;                               !- Field 4 (Heating setpoint in °C)

Schedule:Compact,
  {name}_CoolingSetpoint,             !- Name
  Any Number,                         !- Schedule Type Limits Name
  Through: 12/31,                     !- Field 1
  For: AllDays,                       !- Field 2
  Until: 24:00,                       !- Field 3
  24.0;                               !- Field 4 (Cooling setpoint in °C)

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


