"""
Renewable Energy Systems Module
Includes photovoltaic, solar thermal, and wind energy systems
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import math


@dataclass
class RenewableSystem:
    """Represents a renewable energy system"""
    name: str
    system_type: str  # 'PV', 'SolarThermal', 'Wind'
    capacity: float
    parameters: Dict


class RenewableEnergyEngine:
    """Manages renewable energy systems"""
    
    def __init__(self):
        self.system_templates = self._load_system_templates()
    
    def _load_system_templates(self) -> Dict:
        """Load renewable energy system templates"""
        return {
            'pv_rooftop': {
                'module_type': 'Simple',
                'conversion_efficiency': 0.18,
                'fraction_surface_with_active_cells': 0.95,
                'surface_tilt': 0.0,  # Flat roof
                'surface_azimuth': 180.0,
                'inverter_efficiency': 0.95
            },
            'pv_facade': {
                'module_type': 'Simple',
                'conversion_efficiency': 0.16,
                'fraction_surface_with_active_cells': 0.80,
                'surface_tilt': 90.0,
                'surface_azimuth': 180.0,
                'inverter_efficiency': 0.93
            },
            'solar_thermal': {
                'collector_type': 'FlatPlate',
                'solar_thermal_conversion_efficiency': 0.60,
                'thermal_mass': 5.0,
                'loss_coefficient': 5.0
            },
            'wind_turbine': {
                'rotor_diameter': 10.0,
                'rated_wind_speed': 11.0,
                'rated_power': 10000.0,
                'hub_height': 30.0
            }
        }
    
    def generate_pv_system(self, name: str, surface_name: str, system_type: str = 'rooftop') -> str:
        """Generate photovoltaic system"""
        
        template_key = f'pv_{system_type}'
        template = self.system_templates.get(template_key, 
                                            self.system_templates['pv_rooftop'])
        
        # ElectricLoadCenter:Generators object
        generators = f"""ElectricLoadCenter:Generators,
  {name}_PV_Generators,              !- Name
  Generator:PV,                       !- Generator 1 Object Type
  {name}_PV_Generator,                !- Generator 1 Object Name
  1;                                  !- Generator 1 Rated Electric Power Output

"""
        
        # Generator:Photovoltaic:Simple
        pv_generator = f"""Generator:Photovoltaic:Simple,
  {name}_PV_Generator,                !- Name
  {surface_name},                     !- Surface Name
  {template['module_type']},          !- PV Module Performance Input Method
  {name}_PV_Performance,              !- Module Performance Name
  ,                                   !- Heat Transfer Integration Mode
  Decoupled;                          !- Number of Series Strings in Parallel

"""
        
        # PhotovoltaicPerformance:Simple
        performance = f"""PhotovoltaicPerformance:Simple,
  {name}_PV_Performance,              !- Name
  {template['fraction_surface_with_active_cells']:.3f}, !- Fraction of Surface Area with Active Solar Cells
  {template['conversion_efficiency']:.3f}; !- Conversion Efficiency Input Mode

"""
        
        # ElectricLoadCenter:Distribution
        distribution = f"""ElectricLoadCenter:Distribution,
  {name}_ElectricLoadCenter,          !- Name
  GeneratorPowerSpecification,        !- Generator List Name
  {name}_PV_Generators,               !- Generator Operation Scheme Type
  Baseload,                           !- Demand Limit Scheme Purchased Electric Demand Limit {{W}}
  ,                                   !- Track Schedule Name Scheme Schedule Name
  ,                                   !- Track Meter Scheme Meter Name
  ,                                   !- Electrical Buss Type
  DirectCurrentWithInverter,          !- Inverter Object Name
  {name}_PV_Inverter;                 !- Electrical Storage Object Name

"""
        
        # Inverter:Simple
        inverter = f"""ElectricLoadCenter:Inverter:Simple,
  {name}_PV_Inverter,                 !- Name
  AlwaysOn,                           !- Availability Schedule Name
  {template['inverter_efficiency']:.3f}; !- Zone Name

"""
        
        return generators + pv_generator + performance + distribution + inverter
    
    def generate_solar_thermal_collector(self, name: str, surface_name: str) -> str:
        """Generate solar thermal collector"""
        
        template = self.system_templates['solar_thermal']
        
        # SolarCollector:FlatPlate:Water
        collector = f"""SolarCollector:FlatPlate:Water,
  {name}_SolarCollector,             !- Name
  {surface_name},                     !- Surface Name
  Solar Collector Performance Flat Plate 1, !- Performance Mode
  {name}_WaterLoop,                   !- Plant Inlet Node Name
  {name}_WaterOutlet,                 !- Plant Outlet Node Name
  Parallel,                           !- Configuration Type
  1,                                  !- Number of Modules in Parallel
  1,                                  !- Number of Modules in Series
  0.95,                               !- Setpoint Node Name

"""
        
        # SolarCollectorPerformance:FlatPlate
        performance = f"""SolarCollectorPerformance:FlatPlate,
  Solar Collector Performance Flat Plate 1, !- Name
  0.8,                                !- Gross Area {{m2}}
  ,                                   !- Test Fluid
  Water,                              !- Test Correlation Type
  0.6,                                !- Thermal Efficiency
  3.0,                                !- Heat Loss Coefficient {{W/m2-K}}
  0.5,                                !- Heat Loss Coefficient as a Function of Temperature
  0.1,                                !- Incidence Angle Modifier
  1.0,                                !- Coefficient of Incident Angle Modifier
  0.0,                                !- Coefficient of Incident Angle Modifier
  20,                                 !- Test Flow Rate {{m3/s}}
  100,                                !- Test Delta Temperature {{C}}

"""
        
        return collector + performance
    
    def generate_wind_turbine(self, name: str, hub_height: float = 30.0) -> str:
        """Generate wind turbine system"""
        
        template = self.system_templates['wind_turbine']
        
        # Generator:WindTurbine
        turbine = f"""Generator:WindTurbine,
  {name}_WindTurbine,                 !- Name
  1,                                  !- Availability Schedule Name
  {hub_height:.1f},                   !- Rotor Type
  {template['rotor_diameter']:.1f},  !- Power Control
  {template['rated_wind_speed']:.1f}, !- Rotor Diameter {{m}}
  {template['rated_power']:.0f};     !- Overall Hub Height {{m}}

"""
        
        return turbine
    
    def generate_electric_load_center_distribution(self, name: str, 
                                                   generator_names: List[str],
                                                   use_inverter: bool = True) -> str:
        """Generate electric load center distribution"""
        
        # Generator list
        generator_list = ",\n  ".join(generator_names)
        
        distribution = f"""ElectricLoadCenter:Generators,
  {name}_Generator_List,              !- Name
{self._format_generator_list(generator_names)}

ElectricLoadCenter:Distribution,
  {name}_LoadCenter,                  !- Name
  {name}_Generator_List,              !- Generator List Name
  Baseload,                           !- Generator Operation Scheme Type
  Baseload,                           !- Demand Limit Scheme Purchased Electric Demand Limit {{W}}
  ,                                   !- Track Schedule Name Scheme Schedule Name
  ,                                   !- Track Meter Scheme Meter Name
  AlternatingCurrent,                 !- Electrical Buss Type
  ,                                   !- Inverter Object Name
  ;                                   !- Electrical Storage Object Name

"""
        
        return distribution
    
    def _format_generator_list(self, generator_names: List[str]) -> str:
        """Format generator list for ElectricLoadCenter:Generators"""
        lines = []
        for i, gen_name in enumerate(generator_names, 1):
            gen_type = self._determine_generator_type(gen_name)
            lines.append(f"  {gen_type},                    !- Generator {i} Object Type")
            lines.append(f"  {gen_name},                    !- Generator {i} Object Name")
            lines.append(f"  {i};                             !- Generator {i} Rated Electric Power Output")
        
        return '\n'.join(lines)
    
    def _determine_generator_type(self, name: str) -> str:
        """Determine generator type from name"""
        if 'PV' in name or 'pv' in name:
            return 'Generator:Photovoltaic:Simple'
        elif 'Wind' in name or 'wind' in name:
            return 'Generator:WindTurbine'
        else:
            return 'Generator:InternalCombustionEngine'
    
    def generate_battery_storage(self, name: str, capacity_kwh: float = 50.0) -> str:
        """Generate battery energy storage system"""
        
        # ElectricLoadCenter:Storage:Simple
        battery = f"""ElectricLoadCenter:Storage:Simple,
  {name}_Battery,                     !- Name
  AlwaysOn,                           !- Availability Schedule Name
  {capacity_kwh * 1000:.0f},          !- Nominal Energizing Capacity {{J}}
  1000,                               !- Zone Name
  0.95,                               !- Radiative Fraction for Zone Heat Gains
  0.5,                                !- Nominal Charging Discharging Efficiencies
  0.5,                                !- Initial State of Charge
  0.1,                                !- Design Maximum Control Discharge Power {{W}}
  10000,                              !- Design Maximum Control Discharge Power
  0.05,                               !- Design Maximum Storage Discharge Power {{W}}
  50000;                              !- Design Maximum Storage Discharge Power

"""
        
        return battery
    
    def generate_schedule_for_renewables(self, system_name: str, system_type: str) -> str:
        """Generate schedule for renewable energy systems"""
        
        if system_type == 'PV':
            schedule_name = f"{system_name}_PV_Operation"
            # PV typically operates during daylight hours
            schedule = f"""Schedule:Compact,
  {schedule_name},                    !- Name
  Fraction,                           !- Schedule Type Limits Name
  Through: 12/31,
  For: AllDays,
  Until: 7:00,0.0,
  Until: 8:00,0.2,
  Until: 9:00,0.8,
  Until: 17:00,1.0,
  Until: 18:00,0.8,
  Until: 19:00,0.2,
  Until: 24:00,0.0;

"""
        elif system_type == 'SolarThermal':
            schedule_name = f"{system_name}_SolarThermal_Operation"
            # Solar thermal similar to PV
            schedule = f"""Schedule:Compact,
  {schedule_name},                    !- Name
  Fraction,                           !- Schedule Type Limits Name
  Through: 12/31,
  For: AllDays,
  Until: 7:00,0.0,
  Until: 8:00,0.3,
  Until: 9:00,0.9,
  Until: 17:00,1.0,
  Until: 18:00,0.7,
  Until: 19:00,0.3,
  Until: 24:00,0.0;

"""
        else:  # Wind
            schedule_name = f"{system_name}_Wind_Operation"
            # Wind is more variable, simple always-on availability
            schedule = f"""Schedule:Compact,
  {schedule_name},                    !- Name
  Fraction,                           !- Schedule Type Limits Name
  Through: 12/31,
  For: AllDays,
  Until: 24:00,1.0;

"""
        
        return schedule
    
    def calculate_pv_output(self, system_capacity_kw: float, location: Dict) -> Dict:
        """Calculate expected PV system output"""
        # Simplified calculation - would use actual irradiance data in practice
        annual_irradiance = 1800  # kWh/m²/year (typical)
        system_efficiency = 0.85  # Inverter + system losses
        
        annual_output_kwh = system_capacity_kw * (annual_irradiance / 1000) * system_efficiency
        
        return {
            'system_capacity_kw': system_capacity_kw,
            'annual_output_kwh': annual_output_kwh,
            'capacity_factor': (annual_output_kwh / (system_capacity_kw * 8760)) * 100
        }


