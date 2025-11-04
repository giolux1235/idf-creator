"""
HVAC object formatters for EnergyPlus IDF.
"""

def format_fan_variable_volume(component: dict) -> str:
    return f"""Fan:VariableVolume,
  {component['name']},                 !- Name
  Always On,                           !- Availability Schedule Name
  {component.get('fan_total_efficiency', 0.7)}, !- Fan Total Efficiency
  {component.get('fan_pressure_rise', 600)},    !- Pressure Rise {{Pa}}
  {component['maximum_flow_rate']},    !- Maximum Flow Rate {{m3/s}}
  FixedFlowRate,                       !- Fan Power Minimum Flow Fraction Input Method
  0.0,                                 !- Fan Power Minimum Flow Fraction
  0.0,                                 !- Fan Power Minimum Air Flow Rate {{m3/s}}
  1.0,                                 !- Motor Efficiency
  1.0,                                 !- Motor In Airstream Fraction
  {component.get('fan_power_coefficient_1', 0.0013)},
  {component.get('fan_power_coefficient_2', 0.1470)},
  {component.get('fan_power_coefficient_3', 0.9506)},
  {component.get('fan_power_coefficient_4', -0.0998)},
  {component.get('fan_power_coefficient_5', 0.0)},
  {component['air_inlet_node_name']},  !- Air Inlet Node Name
  {component['air_outlet_node_name']}; !- Air Outlet Node Name

"""

def format_fan_constant_volume(component: dict) -> str:
    return f"""Fan:ConstantVolume,
  {component['name']},                 !- Name
  Always On,                           !- Availability Schedule Name
  {component.get('fan_total_efficiency', 0.6)}, !- Fan Total Efficiency
  {component.get('fan_pressure_rise', 500)},    !- Pressure Rise {{Pa}}
  {component['maximum_flow_rate']},    !- Maximum Flow Rate {{m3/s}}
  {component.get('motor_efficiency', 0.825)}, !- Motor Efficiency
  {component.get('motor_in_airstream_fraction', 1.0)}, !- Motor In Airstream Fraction
  {component['air_inlet_node_name']},  !- Air Inlet Node Name
  {component['air_outlet_node_name']}; !- Air Outlet Node Name

"""

def format_coil_heating_electric(component: dict) -> str:
    # Optional setpoint node
    setpoint_node = component.get('temperature_setpoint_node_name', '')
    # Use efficiency from component dict if provided, otherwise default to 1.0 (resistance heating)
    # For heat pumps, efficiency should be COP (e.g., 3.5)
    efficiency = component.get('efficiency', 1.0)
    output = f"""Coil:Heating:Electric,
  {component['name']},                 !- Name
  Always On,                           !- Availability Schedule Name
  {efficiency},                        !- Efficiency (COP for heat pumps, 1.0 for resistance)
  {component['nominal_capacity']},     !- Nominal Capacity {{W}}
  {component['air_inlet_node_name']},  !- Air Inlet Node Name
  {component['air_outlet_node_name']}"""
    
    if setpoint_node:
        output += f""",
  {setpoint_node}; !- Temperature Setpoint Node Name
"""
    else:
        output += "; !- Air Outlet Node Name\n\n"
    
    return output

def format_coil_heating_gas(component: dict) -> str:
    """Format natural gas heating coil using Coil:Heating:Fuel"""
    setpoint_node = component.get('temperature_setpoint_node_name', '')
    # Gas efficiency is typically 0.80-0.95 (thermal efficiency)
    efficiency = component.get('efficiency', 0.80)
    output = f"""Coil:Heating:Fuel,
  {component['name']},                 !- Name
  Always On,                           !- Availability Schedule Name
  NaturalGas,                          !- Fuel Type
  {efficiency},                        !- Burner Efficiency
  {component['nominal_capacity']},     !- Nominal Capacity {{W}}
  {component['air_inlet_node_name']},  !- Air Inlet Node Name
  {component['air_outlet_node_name']}"""
    
    if setpoint_node:
        output += f""",
  {setpoint_node}; !- Temperature Setpoint Node Name
"""
    else:
        output += "; !- Air Outlet Node Name\n\n"
    
    return output

def format_coil_cooling_dx_single_speed(component: dict) -> str:
    # Get fan power fields if provided
    fan2023 = component.get('rated_evaporator_fan_power_per_volume_flow_rate_2023', 773.3)
    
    # Get curve names if provided, otherwise use defaults
    temp_curve = component.get('total_cooling_capacity_function_of_temperature_curve_name', 'Cool-Cap-fT')
    flow_curve = component.get('total_cooling_capacity_function_of_flow_fraction_curve_name', 'ConstantCubic')
    eir_temp_curve = component.get('energy_input_ratio_function_of_temperature_curve_name', 'Cool-EIR-fT')
    eir_flow_curve = component.get('energy_input_ratio_function_of_flow_fraction_curve_name', 'ConstantCubic')
    plf_curve = component.get('part_load_fraction_correlation_curve_name', 'Cool-PLF-fPLR')
    
    # Return basic coil (no optional fields for now to avoid field order issues)
    return f"""Coil:Cooling:DX:SingleSpeed,
  {component['name']},
  {component['availability_schedule_name']},
  {component['gross_rated_total_cooling_capacity']},
  {component['gross_rated_sensible_heat_ratio']},
  {component['gross_rated_cooling_cop']},
  {component['rated_air_flow_rate']},
  ,                        !- Rated Evaporator Fan Power Per Volume Flow Rate {{W/(m3/s)}}
  {fan2023},               !- 2023 Rated Evaporator Fan Power Per Volume Flow {{W/(m3/s)}}
  {component['air_inlet_node_name']},
  {component['air_outlet_node_name']},
  {temp_curve},
  {flow_curve},
  {eir_temp_curve},
  {eir_flow_curve},
  {plf_curve};
"""

def format_branch_list(component: dict) -> str:
    branches_str = ', '.join(component['branches'])
    return f"""BranchList,
  {component['name']},                 !- Name
  {branches_str};                       !- Branch 1 Name

"""

def format_branch(component: dict) -> str:
    branch_str = f"""Branch,
  {component['name']},                 !- Name
  ,                                    !- Pressure Drop Curve Name
"""
    total = len(component['components'])
    for i, comp in enumerate(component['components'], 1):
        branch_str += f"  {comp['type']},                    !- Component {i} Object Type\n"
        branch_str += f"  {comp['name']},      !- Component {i} Name\n"
        branch_str += f"  {comp['inlet']}, !- Component {i} Inlet Node Name\n"
        if i == total:
            branch_str += f"  {comp['outlet']}; !- Component {i} Outlet Node Name\n"
        else:
            branch_str += f"  {comp['outlet']}, !- Component {i} Outlet Node Name\n"
    return branch_str + "\n"

def format_ptac(component: dict) -> str:
    # Build fan and coil names from PTAC name
    ptac_name = component['name']
    fan_name = ptac_name + 'Fan'
    cooling_coil_name = ptac_name + 'CoolingCoil'
    heating_coil_name = ptac_name + 'HeatingCoil'
    mixer_name = ptac_name + 'Mixer'
    
    # Build node names for zone connections (these connect PTAC to zone)
    air_inlet_node = component.get('air_inlet_node_name', ptac_name + ' Inlet')
    air_outlet_node = component.get('air_outlet_node_name', ptac_name + ' Outlet')
    
    # Build node names for OA mixer
    oa_mixed_node = ptac_name + 'MixedAir'
    oa_inlet_node = ptac_name + 'OAMixerInlet'
    oa_outlet_node = ptac_name + 'OAMixerOutlet'
    oa_air_node = ptac_name + 'OutdoorAir'
    
    # Correct field order for EnergyPlus 24.2/25.1 schema
    return f"""ZoneHVAC:PackagedTerminalAirConditioner,
  {ptac_name},                 !- Name
  {component['availability_schedule_name']}, !- Availability Schedule Name
  {air_inlet_node}, !- Air Inlet Node Name
  {air_outlet_node}, !- Air Outlet Node Name
  OutdoorAir:Mixer, !- Outdoor Air Mixer Object Type
  {mixer_name}, !- Outdoor Air Mixer Name
  {component.get('cooling_supply_air_flow_rate', 'Autosize')}, !- Cooling Supply Air Flow Rate {{m3/s}}
  {component.get('heating_supply_air_flow_rate', 'Autosize')}, !- Heating Supply Air Flow Rate {{m3/s}}
  {component.get('no_load_supply_air_flow_rate', '')}, !- No Load Supply Air Flow Rate {{m3/s}}
  , !- No Load Supply Air Flow Rate Control Set To Low Speed
  {component.get('cooling_outdoor_air_flow_rate', 0)}, !- Cooling Outdoor Air Flow Rate {{m3/s}}
  {component.get('heating_outdoor_air_flow_rate', 0)}, !- Heating Outdoor Air Flow Rate {{m3/s}}
  {component.get('no_load_outdoor_air_flow_rate', 0)}, !- No Load Outdoor Air Flow Rate {{m3/s}}
  {component.get('supply_air_fan_object_type', 'Fan:ConstantVolume')}, !- Supply Air Fan Object Type
  {fan_name}, !- Supply Air Fan Name
  {component.get('heating_coil_object_type', 'Coil:Heating:Electric')}, !- Heating Coil Object Type
  {heating_coil_name}, !- Heating Coil Name
  {component.get('cooling_coil_object_type', 'Coil:Cooling:DX:SingleSpeed')}, !- Cooling Coil Object Type
  {cooling_coil_name}, !- Cooling Coil Name
  {component.get('fan_placement', 'BlowThrough')}, !- Fan Placement
  ; !- Supply Air Fan Operating Mode Schedule Name

"""
