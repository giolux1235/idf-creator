"""
Advanced HVAC Systems for IDF Creator
Real HVAC systems instead of simple ideal loads
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class HVACSystem:
    """Represents an HVAC system configuration"""
    name: str
    system_type: str
    heating_fuel: str
    cooling_fuel: str
    efficiency: Dict[str, float]  # COP, EER, etc.
    controls: str
    zoning: str
    components: List[str]


class AdvancedHVACSystems:
    """Manages advanced HVAC system generation"""
    
    def __init__(self):
        self.hvac_templates = self._load_hvac_templates()
        self.equipment_templates = self._load_equipment_templates()
        self.control_templates = self._load_control_templates()
    
    def _load_hvac_templates(self) -> Dict[str, HVACSystem]:
        """Load HVAC system templates"""
        return {
            'VAV': HVACSystem(
                name='Variable Air Volume',
                system_type='VAV',
                heating_fuel='Electric',
                cooling_fuel='Electric',
                efficiency={'heating_cop': 3.5, 'cooling_eer': 12.0},
                controls='Advanced',
                zoning='Multiple',
                components=['AirLoopHVAC', 'Coil:Heating:Electric', 'Coil:Cooling:DX:SingleSpeed', 'Fan:VariableVolume']
            ),
            'RTU': HVACSystem(
                name='Rooftop Unit',
                system_type='RTU',
                heating_fuel='Gas',
                cooling_fuel='Electric',
                efficiency={'heating_efficiency': 0.8, 'cooling_eer': 10.0},
                controls='Basic',
                zoning='Single',
                components=['ZoneHVAC:PackagedTerminalAirConditioner']
            ),
            'PTAC': HVACSystem(
                name='Packaged Terminal Air Conditioner',
                system_type='PTAC',
                heating_fuel='Electric',
                cooling_fuel='Electric',
                efficiency={'heating_cop': 3.0, 'cooling_eer': 9.0},
                controls='Basic',
                zoning='Individual',
                components=['ZoneHVAC:PackagedTerminalAirConditioner']
            ),
            'HeatPump': HVACSystem(
                name='Heat Pump',
                system_type='HeatPump',
                heating_fuel='Electric',
                cooling_fuel='Electric',
                efficiency={'heating_cop': 4.0, 'cooling_eer': 14.0},
                controls='Advanced',
                zoning='Multiple',
                components=['AirLoopHVAC', 'Coil:Heating:DX:SingleSpeed', 'Coil:Cooling:DX:SingleSpeed', 'Fan:VariableVolume']
            ),
            'ChilledWater': HVACSystem(
                name='Chilled Water System',
                system_type='ChilledWater',
                heating_fuel='Gas',
                cooling_fuel='Electric',
                efficiency={'heating_efficiency': 0.85, 'cooling_cop': 5.0},
                controls='Advanced',
                zoning='Multiple',
                components=['AirLoopHVAC', 'Coil:Heating:Water', 'Coil:Cooling:Water', 'Fan:VariableVolume']
            ),
            'Radiant': HVACSystem(
                name='Radiant Heating/Cooling',
                system_type='Radiant',
                heating_fuel='Electric',
                cooling_fuel='Electric',
                efficiency={'heating_cop': 4.5, 'cooling_cop': 6.0},
                controls='Advanced',
                zoning='Multiple',
                components=['ZoneHVAC:LowTemperatureRadiant:VariableFlow']
            )
        }
    
    def _load_equipment_templates(self) -> Dict[str, Dict]:
        """Load HVAC equipment templates"""
        return {
            'AirLoopHVAC': {
                'name_template': '{zone_name}_AirLoop',
                'components': ['Fan:VariableVolume', 'Coil:Heating:Electric', 'Coil:Cooling:DX:SingleSpeed'],
                'controls': ['Controller:OutdoorAir', 'SetpointManager:Scheduled']
            },
            'ZoneHVAC:PackagedTerminalAirConditioner': {
                'name_template': '{zone_name}_PTAC',
                'components': ['Fan:ConstantVolume', 'Coil:Heating:Electric', 'Coil:Cooling:DX:SingleSpeed'],
                'controls': ['Thermostat']
            },
            'ZoneHVAC:LowTemperatureRadiant:VariableFlow': {
                'name_template': '{zone_name}_Radiant',
                'components': ['Coil:Heating:Water', 'Coil:Cooling:Water'],
                'controls': ['SetpointManager:Scheduled']
            }
        }
    
    def _load_control_templates(self) -> Dict[str, Dict]:
        """Load HVAC control templates"""
        return {
            'Basic': {
                'thermostat_type': 'Thermostat',
                'setpoint_manager': 'SetpointManager:Scheduled',
                'outdoor_air_control': 'Controller:OutdoorAir',
                'scheduling': 'Simple'
            },
            'Advanced': {
                'thermostat_type': 'ThermostatSetpoint:DualSetpoint',
                'setpoint_manager': 'SetpointManager:OutdoorAirReset',
                'outdoor_air_control': 'Controller:OutdoorAir',
                'scheduling': 'Advanced'
            }
        }
    
    def generate_hvac_system(self, building_type: str, zone_name: str,
                           zone_area: float, hvac_type: str,
                           climate_zone: str,
                           catalog_equipment: Optional[Dict] = None) -> List[Dict]:
        """Generate HVAC system for a zone.

        If catalog_equipment is provided, use pre-translated IDF strings from the
        equipment catalog to replace template coils where applicable.
        """
        
        hvac_template = self.hvac_templates.get(hvac_type)
        if not hvac_template:
            hvac_template = self.hvac_templates['VAV']  # Default fallback
        
        # Size equipment based on zone area and building type
        sizing_params = self._calculate_hvac_sizing(building_type, zone_area, climate_zone)
        
        # Generate system components
        components = []
        
        if hvac_template.system_type == 'VAV':
            components.extend(self._generate_vav_system(zone_name, sizing_params, hvac_template))
        elif hvac_template.system_type == 'RTU':
            components.extend(self._generate_rtu_system(zone_name, sizing_params, hvac_template))
        elif hvac_template.system_type == 'PTAC':
            components.extend(self._generate_ptac_system(zone_name, sizing_params, hvac_template))
        elif hvac_template.system_type == 'HeatPump':
            components.extend(self._generate_heatpump_system(zone_name, sizing_params, hvac_template))
        elif hvac_template.system_type == 'ChilledWater':
            components.extend(self._generate_chilledwater_system(zone_name, sizing_params, hvac_template))
        elif hvac_template.system_type == 'Radiant':
            components.extend(self._generate_radiant_system(zone_name, sizing_params, hvac_template))
        
        # Attach catalog equipment strings if provided
        if catalog_equipment and isinstance(catalog_equipment.get('idf_objects'), list):
            components.extend([{ 'type': 'IDF_STRING', 'name': obj.split(',')[0], 'raw': obj } for obj in catalog_equipment['idf_objects']])

        return components
    
    def _calculate_hvac_sizing(self, building_type: str, zone_area: float, 
                             climate_zone: str) -> Dict:
        """Calculate HVAC sizing parameters"""
        
        # Base cooling load (W/m²)
        cooling_load_density = {
            'office': 100,  # W/m²
            'residential': 60,
            'retail': 120,
            'healthcare': 150,
            'education': 80,
            'industrial': 50,
            'hospitality': 100
        }.get(building_type, 100)
        
        # Base heating load (W/m²)
        heating_load_density = {
            'office': 80,
            'residential': 100,
            'retail': 90,
            'healthcare': 120,
            'education': 70,
            'industrial': 60,
            'hospitality': 90
        }.get(building_type, 80)
        
        # Adjust for climate zone
        climate_multipliers = {
            '1': {'cooling': 1.2, 'heating': 0.3},
            '2': {'cooling': 1.1, 'heating': 0.4},
            '3': {'cooling': 1.0, 'heating': 0.6},
            '4': {'cooling': 0.9, 'heating': 0.8},
            '5': {'cooling': 0.8, 'heating': 1.0},
            '6': {'cooling': 0.7, 'heating': 1.2},
            '7': {'cooling': 0.6, 'heating': 1.4},
            '8': {'cooling': 0.5, 'heating': 1.6}
        }
        
        cz = climate_zone[0] if climate_zone else '3'
        multipliers = climate_multipliers.get(cz, {'cooling': 1.0, 'heating': 1.0})
        
        cooling_load = zone_area * cooling_load_density * multipliers['cooling']
        heating_load = zone_area * heating_load_density * multipliers['heating']
        
        # Air flow rates (L/s)
        ventilation_rate = zone_area * 0.5  # 0.5 L/s-m²
        supply_air_flow = max(ventilation_rate * 2, cooling_load / 1200)  # 1200 W per L/s
        
        return {
            'cooling_load': cooling_load,
            'heating_load': heating_load,
            'supply_air_flow': supply_air_flow,
            'ventilation_rate': ventilation_rate,
            'zone_area': zone_area
        }
    
    def _generate_vav_system(self, zone_name: str, sizing_params: Dict, 
                           hvac_template: HVACSystem) -> List[Dict]:
        """Generate VAV system components"""
        components = []
        
        # Air Loop
        air_loop = {
            'type': 'AirLoopHVAC',
            'name': f"{zone_name}_AirLoop",
            'design_supply_air_flow_rate': sizing_params['supply_air_flow'],
            'branch_list': f"{zone_name}_BranchList",
            'connector_list': f"{zone_name}_ConnectorList",
            'supply_side_inlet_node_name': f"{zone_name}_SupplyInlet",
            'demand_side_outlet_node_name': f"{zone_name}_DemandOutlet",
            'demand_side_inlet_node_names': [f"{zone_name}_DemandInlet"],
            'supply_side_outlet_node_names': [f"{zone_name}_SupplyOutlet"]
        }
        components.append(air_loop)
        
        # Supply Fan
        fan = {
            'type': 'Fan:VariableVolume',
            'name': f"{zone_name}_SupplyFan",
            'air_inlet_node_name': f"{zone_name}_FanInlet",
            'air_outlet_node_name': f"{zone_name}_FanOutlet",
            'fan_total_efficiency': 0.7,
            'fan_pressure_rise': 600,  # Pa
            'maximum_flow_rate': sizing_params['supply_air_flow'],
            'fan_power_minimum_flow_fraction': 0.3,
            'fan_power_coefficient_1': 0.0013,
            'fan_power_coefficient_2': 0.1470,
            'fan_power_coefficient_3': 0.9506,
            'fan_power_coefficient_4': -0.0998,
            'fan_power_coefficient_5': 0.0
        }
        components.append(fan)
        
        # Heating Coil
        heating_coil = {
            'type': 'Coil:Heating:Electric',
            'name': f"{zone_name}_HeatingCoil",
            'air_inlet_node_name': f"{zone_name}_HeatingCoilInlet",
            'air_outlet_node_name': f"{zone_name}_HeatingCoilOutlet",
            'nominal_capacity': sizing_params['heating_load'],
            'efficiency': hvac_template.efficiency['heating_cop']
        }
        components.append(heating_coil)
        
        # Cooling Coil
        cooling_coil = {
            'type': 'Coil:Cooling:DX:SingleSpeed',
            'name': f"{zone_name}_CoolingCoil",
            'air_inlet_node_name': f"{zone_name}_CoolingCoilInlet",
            'air_outlet_node_name': f"{zone_name}_CoolingCoilOutlet",
            'availability_schedule_name': 'Always On',
            'gross_rated_total_cooling_capacity': sizing_params['cooling_load'],
            'gross_rated_sensible_heat_ratio': 0.75,
            'gross_rated_cooling_cop': hvac_template.efficiency['cooling_eer'] / 3.412,
            'rated_air_flow_rate': sizing_params['supply_air_flow'],
            'condenser_air_inlet_node_name': f"{zone_name}_CondenserInlet",
            'condenser_type': 'AirCooled',
            'evaporator_fan_power_included_in_rated_cop': True,
            'condenser_fan_power_ratio': 0.2
        }
        components.append(cooling_coil)
        
        # Zone Equipment
        zone_equipment = {
            'type': 'ZoneHVAC:AirDistributionUnit',
            'name': f"{zone_name}_ADU",
            'air_distribution_unit_outlet_node_name': f"{zone_name}_ADUOutlet",
            'air_terminal_object_type': 'AirTerminal:SingleDuct:VAV:Reheat',
            'air_terminal_name': f"{zone_name}_VAVTerminal",
            'nominal_supply_air_flow_rate': sizing_params['supply_air_flow']
        }
        components.append(zone_equipment)
        
        # VAV Terminal
        vav_terminal = {
            'type': 'AirTerminal:SingleDuct:VAV:Reheat',
            'name': f"{zone_name}_VAVTerminal",
            'availability_schedule_name': 'Always On',
            'damper_heating_action': 'Normal',
            'maximum_flow_fraction_during_reheat': 0.5,
            'maximum_flow_per_zone_floor_area_during_reheat': 0.003,
            'maximum_flow_fraction_before_reheat': 0.2,
            'reheat_coil_name': f"{zone_name}_ReheatCoil",
            'maximum_hot_water_or_steam_flow_rate': sizing_params['heating_load'] / 1000,
            'minimum_hot_water_or_steam_flow_rate': 0.0,
            'convergence_tolerance': 0.001,
            'damper_air_outlet_node_name': f"{zone_name}_TerminalOutlet",
            'air_inlet_node_name': f"{zone_name}_TerminalInlet",
            'reheat_coil_air_inlet_node_name': f"{zone_name}_ReheatInlet",
            'reheat_coil_air_outlet_node_name': f"{zone_name}_ReheatOutlet"
        }
        components.append(vav_terminal)
        
        # Reheat Coil
        reheat_coil = {
            'type': 'Coil:Heating:Electric',
            'name': f"{zone_name}_ReheatCoil",
            'air_inlet_node_name': f"{zone_name}_ReheatInlet",
            'air_outlet_node_name': f"{zone_name}_ReheatOutlet",
            'nominal_capacity': sizing_params['heating_load'] * 0.3,  # 30% of total heating
            'efficiency': hvac_template.efficiency['heating_cop']
        }
        components.append(reheat_coil)
        
        return components
    
    def _generate_rtu_system(self, zone_name: str, sizing_params: Dict, 
                           hvac_template: HVACSystem) -> List[Dict]:
        """Generate RTU system components"""
        components = []
        
        # Packaged Terminal Air Conditioner
        ptac = {
            'type': 'ZoneHVAC:PackagedTerminalAirConditioner',
            'name': f"{zone_name}_RTU",
            'availability_schedule_name': 'Always On',
            'air_inlet_node_name': f"{zone_name}_RTUInlet",
            'air_outlet_node_name': f"{zone_name}_RTUOutlet",
            'cooling_supply_air_flow_rate': sizing_params['supply_air_flow'],
            'heating_supply_air_flow_rate': sizing_params['supply_air_flow'],
            'no_load_supply_air_flow_rate': sizing_params['supply_air_flow'] * 0.3,
            'cooling_outdoor_air_flow_rate': sizing_params['ventilation_rate'],
            'heating_outdoor_air_flow_rate': sizing_params['ventilation_rate'],
            'no_load_outdoor_air_flow_rate': sizing_params['ventilation_rate'] * 0.3,
            'supply_air_fan_object_type': 'Fan:ConstantVolume',
            'supply_air_fan_name': f"{zone_name}_RTUFan",
            'cooling_coil_object_type': 'Coil:Cooling:DX:SingleSpeed',
            'cooling_coil_name': f"{zone_name}_RTUCoolingCoil",
            'heating_coil_object_type': 'Coil:Heating:Gas',
            'heating_coil_name': f"{zone_name}_RTUHeatingCoil",
            'fan_placement': 'BlowThrough',
            'outdoor_air_mixer_object_type': 'OutdoorAir:Mixer',
            'outdoor_air_mixer_name': f"{zone_name}_RTUMixer"
        }
        components.append(ptac)
        
        # Fan
        fan = {
            'type': 'Fan:ConstantVolume',
            'name': f"{zone_name}_RTUFan",
            'air_inlet_node_name': f"{zone_name}_RTUFanInlet",
            'air_outlet_node_name': f"{zone_name}_RTUFanOutlet",
            'fan_total_efficiency': 0.6,
            'fan_pressure_rise': 500,  # Pa
            'maximum_flow_rate': sizing_params['supply_air_flow']
        }
        components.append(fan)
        
        # Cooling Coil
        cooling_coil = {
            'type': 'Coil:Cooling:DX:SingleSpeed',
            'name': f"{zone_name}_RTUCoolingCoil",
            'air_inlet_node_name': f"{zone_name}_RTUCoolingInlet",
            'air_outlet_node_name': f"{zone_name}_RTUCoolingOutlet",
            'availability_schedule_name': 'Always On',
            'gross_rated_total_cooling_capacity': sizing_params['cooling_load'],
            'gross_rated_sensible_heat_ratio': 0.75,
            'gross_rated_cooling_cop': hvac_template.efficiency['cooling_eer'] / 3.412,
            'rated_air_flow_rate': sizing_params['supply_air_flow'],
            'condenser_air_inlet_node_name': f"{zone_name}_RTUCondenserInlet",
            'condenser_type': 'AirCooled',
            'evaporator_fan_power_included_in_rated_cop': True,
            'condenser_fan_power_ratio': 0.2
        }
        components.append(cooling_coil)
        
        # Heating Coil
        heating_coil = {
            'type': 'Coil:Heating:Gas',
            'name': f"{zone_name}_RTUHeatingCoil",
            'air_inlet_node_name': f"{zone_name}_RTUHeatingInlet",
            'air_outlet_node_name': f"{zone_name}_RTUHeatingOutlet",
            'availability_schedule_name': 'Always On',
            'gas_burner_efficiency': hvac_template.efficiency['heating_efficiency'],
            'nominal_capacity': sizing_params['heating_load'],
            'parasitic_electric_load': sizing_params['heating_load'] * 0.01  # 1% parasitic
        }
        components.append(heating_coil)
        
        # Outdoor Air Mixer
        mixer = {
            'type': 'OutdoorAir:Mixer',
            'name': f"{zone_name}_RTUMixer",
            'outdoor_air_stream_node_name': f"{zone_name}_RTUOAMixerInlet",
            'relief_air_stream_node_name': f"{zone_name}_RTUOAMixerOutlet",
            'mixed_air_node_name': f"{zone_name}_RTUMixedAir",
            'outdoor_air_node_name': f"{zone_name}_RTUOutdoorAir"
        }
        components.append(mixer)
        
        return components
    
    def _generate_ptac_system(self, zone_name: str, sizing_params: Dict, 
                            hvac_template: HVACSystem) -> List[Dict]:
        """Generate PTAC system components"""
        components = []
        
        # Packaged Terminal Air Conditioner
        ptac = {
            'type': 'ZoneHVAC:PackagedTerminalAirConditioner',
            'name': f"{zone_name}_PTAC",
            'availability_schedule_name': 'Always On',
            'air_inlet_node_name': f"{zone_name}_PTACInlet",
            'air_outlet_node_name': f"{zone_name}_PTACOutlet",
            'cooling_supply_air_flow_rate': sizing_params['supply_air_flow'],
            'heating_supply_air_flow_rate': sizing_params['supply_air_flow'],
            'no_load_supply_air_flow_rate': sizing_params['supply_air_flow'] * 0.3,
            'cooling_outdoor_air_flow_rate': sizing_params['ventilation_rate'],
            'heating_outdoor_air_flow_rate': sizing_params['ventilation_rate'],
            'no_load_outdoor_air_flow_rate': sizing_params['ventilation_rate'] * 0.3,
            'supply_air_fan_object_type': 'Fan:ConstantVolume',
            'supply_air_fan_name': f"{zone_name}_PTACFan",
            'cooling_coil_object_type': 'Coil:Cooling:DX:SingleSpeed',
            'cooling_coil_name': f"{zone_name}_PTACCoolingCoil",
            'heating_coil_object_type': 'Coil:Heating:Electric',
            'heating_coil_name': f"{zone_name}_PTACHeatingCoil",
            'fan_placement': 'BlowThrough',
            'outdoor_air_mixer_object_type': 'OutdoorAir:Mixer',
            'outdoor_air_mixer_name': f"{zone_name}_PTACMixer"
        }
        components.append(ptac)
        
        # Fan
        fan = {
            'type': 'Fan:ConstantVolume',
            'name': f"{zone_name}_PTACFan",
            'air_inlet_node_name': f"{zone_name}_PTACFanInlet",
            'air_outlet_node_name': f"{zone_name}_PTACFanOutlet",
            'fan_total_efficiency': 0.6,
            'fan_pressure_rise': 400,  # Pa
            'maximum_flow_rate': sizing_params['supply_air_flow']
        }
        components.append(fan)
        
        # Cooling Coil
        cooling_coil = {
            'type': 'Coil:Cooling:DX:SingleSpeed',
            'name': f"{zone_name}_PTACCoolingCoil",
            'air_inlet_node_name': f"{zone_name}_PTACCoolingInlet",
            'air_outlet_node_name': f"{zone_name}_PTACCoolingOutlet",
            'availability_schedule_name': 'Always On',
            'gross_rated_total_cooling_capacity': sizing_params['cooling_load'],
            'gross_rated_sensible_heat_ratio': 0.75,
            'gross_rated_cooling_cop': hvac_template.efficiency['cooling_eer'] / 3.412,
            'rated_air_flow_rate': sizing_params['supply_air_flow'],
            'condenser_air_inlet_node_name': f"{zone_name}_PTACCondenserInlet",
            'condenser_type': 'AirCooled',
            'evaporator_fan_power_included_in_rated_cop': True,
            'condenser_fan_power_ratio': 0.2
        }
        components.append(cooling_coil)
        
        # Heating Coil
        heating_coil = {
            'type': 'Coil:Heating:Electric',
            'name': f"{zone_name}_PTACHeatingCoil",
            'air_inlet_node_name': f"{zone_name}_PTACHeatingInlet",
            'air_outlet_node_name': f"{zone_name}_PTACHeatingOutlet",
            'availability_schedule_name': 'Always On',
            'efficiency': hvac_template.efficiency['heating_cop'],
            'nominal_capacity': sizing_params['heating_load']
        }
        components.append(heating_coil)
        
        # Outdoor Air Mixer
        mixer = {
            'type': 'OutdoorAir:Mixer',
            'name': f"{zone_name}_PTACMixer",
            'outdoor_air_stream_node_name': f"{zone_name}_PTACOAMixerInlet",
            'relief_air_stream_node_name': f"{zone_name}_PTACOAMixerOutlet",
            'mixed_air_node_name': f"{zone_name}_PTACMixedAir",
            'outdoor_air_node_name': f"{zone_name}_PTACOutdoorAir"
        }
        components.append(mixer)
        
        return components
    
    def _generate_heatpump_system(self, zone_name: str, sizing_params: Dict, 
                                hvac_template: HVACSystem) -> List[Dict]:
        """Generate heat pump system components"""
        # Similar to VAV but with heat pump coils
        components = []
        
        # Air Loop
        air_loop = {
            'type': 'AirLoopHVAC',
            'name': f"{zone_name}_HeatPumpLoop",
            'design_supply_air_flow_rate': sizing_params['supply_air_flow'],
            'branch_list': f"{zone_name}_HeatPumpBranchList",
            'connector_list': f"{zone_name}_HeatPumpConnectorList",
            'supply_side_inlet_node_name': f"{zone_name}_HeatPumpSupplyInlet",
            'demand_side_outlet_node_name': f"{zone_name}_HeatPumpDemandOutlet",
            'demand_side_inlet_node_names': [f"{zone_name}_HeatPumpDemandInlet"],
            'supply_side_outlet_node_names': [f"{zone_name}_HeatPumpSupplyOutlet"]
        }
        components.append(air_loop)
        
        # Heat Pump Coils (DX)
        heat_pump_coil = {
            'type': 'Coil:Heating:DX:SingleSpeed',
            'name': f"{zone_name}_HeatPumpCoil",
            'availability_schedule_name': 'Always On',
            'air_inlet_node_name': f"{zone_name}_HeatPumpCoilInlet",
            'air_outlet_node_name': f"{zone_name}_HeatPumpCoilOutlet",
            'rated_total_heating_capacity': sizing_params['heating_load'],
            'rated_sensible_heat_ratio': 0.8,
            'rated_cop': hvac_template.efficiency['heating_cop'],
            'rated_air_flow_rate': sizing_params['supply_air_flow'],
            'condenser_air_inlet_node_name': f"{zone_name}_HeatPumpCondenserInlet",
            'condenser_type': 'AirCooled',
            'evaporator_fan_power_included_in_rated_cop': True,
            'condenser_fan_power_ratio': 0.2
        }
        components.append(heat_pump_coil)
        
        return components
    
    def _generate_chilledwater_system(self, zone_name: str, sizing_params: Dict, 
                                    hvac_template: HVACSystem) -> List[Dict]:
        """Generate chilled water system components"""
        components = []
        
        # Air Loop
        air_loop = {
            'type': 'AirLoopHVAC',
            'name': f"{zone_name}_ChilledWaterLoop",
            'design_supply_air_flow_rate': sizing_params['supply_air_flow'],
            'branch_list': f"{zone_name}_ChilledWaterBranchList",
            'connector_list': f"{zone_name}_ChilledWaterConnectorList",
            'supply_side_inlet_node_name': f"{zone_name}_ChilledWaterSupplyInlet",
            'demand_side_outlet_node_name': f"{zone_name}_ChilledWaterDemandOutlet",
            'demand_side_inlet_node_names': [f"{zone_name}_ChilledWaterDemandInlet"],
            'supply_side_outlet_node_names': [f"{zone_name}_ChilledWaterSupplyOutlet"]
        }
        components.append(air_loop)
        
        # Water Coils
        heating_coil = {
            'type': 'Coil:Heating:Water',
            'name': f"{zone_name}_ChilledWaterHeatingCoil",
            'air_inlet_node_name': f"{zone_name}_ChilledWaterHeatingInlet",
            'air_outlet_node_name': f"{zone_name}_ChilledWaterHeatingOutlet",
            'water_inlet_node_name': f"{zone_name}_ChilledWaterHeatingWaterInlet",
            'water_outlet_node_name': f"{zone_name}_ChilledWaterHeatingWaterOutlet",
            'heating_design_capacity': sizing_params['heating_load'],
            'water_flow_rate': sizing_params['heating_load'] / 1000,  # L/s
            'performance_input_method': 'NominalCapacity'
        }
        components.append(heating_coil)
        
        cooling_coil = {
            'type': 'Coil:Cooling:Water',
            'name': f"{zone_name}_ChilledWaterCoolingCoil",
            'air_inlet_node_name': f"{zone_name}_ChilledWaterCoolingInlet",
            'air_outlet_node_name': f"{zone_name}_ChilledWaterCoolingOutlet",
            'water_inlet_node_name': f"{zone_name}_ChilledWaterCoolingWaterInlet",
            'water_outlet_node_name': f"{zone_name}_ChilledWaterCoolingWaterOutlet",
            'design_water_flow_rate': sizing_params['cooling_load'] / 1000,  # L/s
            'design_air_flow_rate': sizing_params['supply_air_flow'],
            'design_inlet_water_temperature': 7.0,  # °C
            'design_inlet_air_temperature': 24.0,  # °C
            'design_outlet_air_temperature': 12.0,  # °C
            'design_inlet_air_humidity_ratio': 0.008,
            'design_outlet_air_humidity_ratio': 0.008,
            'type_of_analysis': 'SimpleAnalysis',
            'heat_exchanger_configuration': 'CrossFlow'
        }
        components.append(cooling_coil)
        
        return components
    
    def _generate_radiant_system(self, zone_name: str, sizing_params: Dict, 
                               hvac_template: HVACSystem) -> List[Dict]:
        """Generate radiant system components"""
        components = []
        
        # Low Temperature Radiant System
        radiant = {
            'type': 'ZoneHVAC:LowTemperatureRadiant:VariableFlow',
            'name': f"{zone_name}_Radiant",
            'availability_schedule_name': 'Always On',
            'zone_name': zone_name,
            'surface_name_or_radiant_surface_group_name': f"{zone_name}_RadiantSurface",
            'hydronic_tubing_inside_diameter': 0.016,  # m
            'hydronic_tubing_outside_diameter': 0.020,  # m
            'hydronic_tubing_conductivity': 0.4,  # W/m-K
            'hydronic_tubing_length': zone_name,  # Will be calculated
            'temperature_control_type': 'MeanAirTemperature',
            'heating_water_inlet_node_name': f"{zone_name}_RadiantHeatingWaterInlet",
            'heating_water_outlet_node_name': f"{zone_name}_RadiantHeatingWaterOutlet",
            'heating_high_water_temperature_schedule_name': 'RadiantHeatingHighTemp',
            'heating_low_water_temperature_schedule_name': 'RadiantHeatingLowTemp',
            'heating_high_control_temperature_schedule_name': 'RadiantHeatingHighControlTemp',
            'heating_low_control_temperature_schedule_name': 'RadiantHeatingLowControlTemp',
            'cooling_water_inlet_node_name': f"{zone_name}_RadiantCoolingWaterInlet",
            'cooling_water_outlet_node_name': f"{zone_name}_RadiantCoolingWaterOutlet",
            'cooling_high_water_temperature_schedule_name': 'RadiantCoolingHighTemp',
            'cooling_low_water_temperature_schedule_name': 'RadiantCoolingLowTemp',
            'cooling_high_control_temperature_schedule_name': 'RadiantCoolingHighControlTemp',
            'cooling_low_control_temperature_schedule_name': 'RadiantCoolingLowControlTemp',
            'condensation_control_type': 'SimpleOff',
            'condensation_control_dewpoint_offset': 1.0
        }
        components.append(radiant)
        
        return components
    
    def generate_control_objects(self, zone_name: str, hvac_type: str, 
                               climate_zone: str) -> List[Dict]:
        """Generate HVAC control objects"""
        hvac_template = self.hvac_templates.get(hvac_type)
        if not hvac_template:
            hvac_template = self.hvac_templates['VAV']
        
        control_template = self.control_templates.get(hvac_template.controls)
        if not control_template:
            control_template = self.control_templates['Basic']
        
        controls = []
        
        # Thermostat
        if control_template['thermostat_type'] == 'ThermostatSetpoint:DualSetpoint':
            thermostat = {
                'type': 'ThermostatSetpoint:DualSetpoint',
                'name': f"{zone_name}_Thermostat",
                'heating_setpoint_temperature_schedule_name': f"{zone_name}_HeatingSetpoint",
                'cooling_setpoint_temperature_schedule_name': f"{zone_name}_CoolingSetpoint"
            }
        else:
            thermostat = {
                'type': 'Thermostat',
                'name': f"{zone_name}_Thermostat",
                'heating_setpoint_temperature_schedule_name': f"{zone_name}_HeatingSetpoint",
                'cooling_setpoint_temperature_schedule_name': f"{zone_name}_CoolingSetpoint"
            }
        controls.append(thermostat)
        
        # Setpoint Manager
        if control_template['setpoint_manager'] == 'SetpointManager:OutdoorAirReset':
            setpoint_manager = {
                'type': 'SetpointManager:OutdoorAirReset',
                'name': f"{zone_name}_SetpointManager",
                'control_variable': 'Temperature',
                'setpoint_at_outdoor_low_temperature': 21.0,  # °C
                'outdoor_low_temperature': 15.6,  # °C
                'setpoint_at_outdoor_high_temperature': 24.0,  # °C
                'outdoor_high_temperature': 23.3,  # °C
                'setpoint_node_or_nodelist_name': f"{zone_name}_SupplyAir"
            }
        else:
            setpoint_manager = {
                'type': 'SetpointManager:Scheduled',
                'name': f"{zone_name}_SetpointManager",
                'control_variable': 'Temperature',
                'schedule_name': f"{zone_name}_SupplyAirTemp",
                'setpoint_node_or_nodelist_name': f"{zone_name}_SupplyAir"
            }
        controls.append(setpoint_manager)
        
        return controls
