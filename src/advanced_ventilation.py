"""
Advanced Ventilation Module
Implements Demand Control Ventilation (DCV) and Energy Recovery Ventilation (ERV/HRV)

Features:
- DCV controllers with CO2-based ventilation
- Energy Recovery Ventilation (sensible and latent)
- ASHRAE 62.1 compliance
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class VentilationConfig:
    """Configuration for ventilation systems"""
    dcv_enabled: bool = True
    dcv_method: str = 'CO2'  # 'CO2' or 'Occupancy'
    erv_enabled: bool = False
    erv_type: str = 'sensible_and_latent'  # 'sensible_only' or 'sensible_and_latent'
    sensible_effectiveness: float = 0.7  # 70% typical
    latent_effectiveness: float = 0.65  # 65% typical
    

class AdvancedVentilation:
    """
    Advanced ventilation systems: DCV and Energy Recovery
    """
    
    def __init__(self):
        """Initialize with default configurations"""
        self.default_config = VentilationConfig()
    
    def generate_dcv_controller(
        self,
        oa_controller_name: str,
        zone_name: str,
        method: str = 'CO2',
        space_type: Optional[str] = None
    ) -> str:
        """
        Generate Demand Control Ventilation (DCV) controller.
        
        Args:
            oa_controller_name: Name of Controller:OutdoorAir
            zone_name: Zone name
            method: 'CO2' or 'Occupancy'
        
        Returns:
            IDF string with Controller:MechanicalVentilation and related objects
        """
        if method == 'CO2':
            # ASHRAE 62.1 Ventilation Rate Procedure with CO2-based DCV
            # For CO2 DCV, DCV is controlled by ContaminantController, not in DesignSpecification
            dcv_idf = f"""DesignSpecification:OutdoorAir,
  {zone_name}_DCV_OA_Spec,              !- Name
  Sum,                                   !- Outdoor Air Method
  ,                                       !- Outdoor Air Flow per Person {{m3/s-person}}
  ,                                       !- Outdoor Air Flow per Zone Floor Area {{m3/s-m2}}
  ,                                       !- Outdoor Air Flow per Zone {{m3/s}}
  ,                                       !- Outdoor Air Flow Air Changes per Hour {{ACH}}
  ,                                       !- Outdoor Air Flow Rate per Person {{m3/s-person}}
  ,                                       !- Outdoor Air Flow Rate per Zone Floor Area {{m3/s-m2}}
  ,                                       !- Outdoor Air Flow Rate per Zone {{m3/s}}
  ,                                       !- Outdoor Air Flow Rate per Air Changes per Hour {{ACH}}
  ;                                       !- End of object (DCV via ZoneControl:ContaminantController)

ZoneControl:ContaminantController,
  {zone_name}_CO2_Controller,            !- Name
  {zone_name},                           !- Zone Name
  CarbonDioxide,                         !- Controller 1 Control Variable
  Yes,                                   !- Controller 1 Controlling Zone or ZoneList Name
  ,                                       !- Controller 1 Name
  ,                                       !- Controller 1 Setpoint Schedule Name
  ;

Controller:MechanicalVentilation,
  {zone_name}_MechVent,                  !- Name
  {oa_controller_name},                  !- Controller:OutdoorAir Name
  ,                                       !- Ventilation Calculation Method (blank = use DesignSpecification)
  ,                                       !- Zone Maximum Outdoor Air Fraction
  ,                                       !- Zone Primary Outdoor Air Fraction
  {zone_name}_DCV_OA_Spec;               !- Design Specification Outdoor Air Object Name

Schedule:Compact,
  {zone_name}_DCV_Schedule,              !- Name
  AnyNumber,                             !- Schedule Type Limits Name
  Through: 12/31,                        !- Field 1
  For: AllDays,                          !- Field 2
  Until: 24:00,                          !- Field 3
  1.0;                                   !- Field 4 (Always available)

"""
        else:
            # Occupancy-based DCV (simpler, no CO2 sensor needed)
            # Determine space type to get correct schedule name
            # Format will be {space_type}_Occupancy (e.g., office_open_Occupancy)
            if space_type:
                occupancy_schedule = f"{space_type}_Occupancy"
            else:
                # Fallback: derive from zone name
                derived_type = zone_name.split('_z')[0] if '_z' in zone_name else zone_name
                occupancy_schedule = f"{derived_type}_Occupancy"
            
            # Simplified DesignSpecification:OutdoorAir - only required fields
            # EnergyPlus 24.2 expects minimal fields when using Sum method
            dcv_idf = f"""DesignSpecification:OutdoorAir,
  {zone_name}_DCV_OA_Spec,              !- Name
  Sum,                                   !- Outdoor Air Method
  ,                                       !- Outdoor Air Flow per Person {{m3/s-person}}
  ,                                       !- Outdoor Air Flow per Zone Floor Area {{m3/s-m2}}
  ,                                       !- Outdoor Air Flow per Zone {{m3/s}}
  ,                                       !- Outdoor Air Flow Air Changes per Hour {{ACH}}
  ,                                       !- Outdoor Air Flow Rate per Person {{m3/s-person}}
  ,                                       !- Outdoor Air Flow Rate per Zone Floor Area {{m3/s-m2}}
  ,                                       !- Outdoor Air Flow Rate per Zone {{m3/s}}
  ,                                       !- Outdoor Air Flow Rate per Air Changes per Hour {{ACH}}
  ;                                       !- End of object (DCV via Controller:MechanicalVentilation)

Controller:MechanicalVentilation,
  {zone_name}_MechVent,                  !- Name
  {oa_controller_name},                  !- Controller:OutdoorAir Name
  ,                                       !- Ventilation Calculation Method (blank = use DesignSpecification)
  ,                                       !- Zone Maximum Outdoor Air Fraction
  ,                                       !- Zone Primary Outdoor Air Fraction
  {zone_name}_DCV_OA_Spec;               !- Design Specification Outdoor Air Object Name

"""
        
        return dcv_idf
    
    def generate_energy_recovery_ventilation(
        self,
        zone_name: str,
        supply_inlet_node: str,
        supply_outlet_node: str,
        exhaust_inlet_node: str,
        exhaust_outlet_node: str,
        supply_air_flow_rate: float,
        exhaust_air_flow_rate: Optional[float] = None,
        sensible_effectiveness: float = 0.7,
        latent_effectiveness: float = 0.65
    ) -> str:
        """
        Generate Energy Recovery Ventilation (ERV/HRV) system.
        
        Args:
            zone_name: Zone name for naming
            supply_inlet_node: Outdoor air inlet node
            supply_outlet_node: Conditioned outdoor air outlet node
            exhaust_inlet_node: Exhaust air inlet node
            exhaust_outlet_node: Exhaust air outlet node
            supply_air_flow_rate: Supply air flow rate (m3/s)
            exhaust_air_flow_rate: Exhaust air flow rate (m3/s, defaults to supply)
            sensible_effectiveness: Sensible heat recovery effectiveness (0-1)
            latent_effectiveness: Latent heat recovery effectiveness (0-1)
        
        Returns:
            IDF string with HeatExchanger:AirToAir object
        """
        if exhaust_air_flow_rate is None:
            exhaust_air_flow_rate = supply_air_flow_rate
        
        erv_idf = f"""HeatExchanger:AirToAir:SensibleAndLatent,
  {zone_name}_ERV,                       !- Name
  {supply_inlet_node},                   !- Primary Air Stream Inlet Node Name
  {supply_outlet_node},                  !- Primary Air Stream Outlet Node Name
  {exhaust_inlet_node},                  !- Secondary Air Stream Inlet Node Name
  {exhaust_outlet_node},                 !- Secondary Air Stream Outlet Node Name
  {zone_name}_ERV_Availability,          !- Availability Schedule Name
  {supply_air_flow_rate:.4f},            !- Nominal Supply Air Flow Rate {{m3/s}}
  {exhaust_air_flow_rate:.4f},          !- Nominal Exhaust Air Flow Rate {{m3/s}}
  {sensible_effectiveness:.2f},           !- Sensible Effectiveness at 100% Heating Air Flow
  {latent_effectiveness:.2f},            !- Latent Effectiveness at 100% Heating Air Flow
  {sensible_effectiveness:.2f},          !- Sensible Effectiveness at 75% Heating Air Flow
  {latent_effectiveness:.2f},            !- Latent Effectiveness at 75% Heating Air Flow
  {sensible_effectiveness:.2f},          !- Sensible Effectiveness at 100% Cooling Air Flow
  {latent_effectiveness:.2f},            !- Latent Effectiveness at 100% Cooling Air Flow
  {sensible_effectiveness:.2f},          !- Sensible Effectiveness at 75% Cooling Air Flow
  {latent_effectiveness:.2f},            !- Latent Effectiveness at 75% Cooling Air Flow
  {supply_air_flow_rate:.4f},            !- Nominal Supply Air Flow Rate at Rated Conditions {{m3/s}}
  {exhaust_air_flow_rate:.4f},          !- Nominal Exhaust Air Flow Rate at Rated Conditions {{m3/s}}
  {sensible_effectiveness:.2f},          !- Sensible Effectiveness at 100% Heating Air Flow at Rated Conditions
  {latent_effectiveness:.2f},           !- Latent Effectiveness at 100% Heating Air Flow at Rated Conditions
  0.0,                                   !- Supply Air Sensible Heat Transfer Rate at Heating Flow at Rated Conditions {{W}}
  0.0,                                   !- Supply Air Latent Heat Transfer Rate at Heating Flow at Rated Conditions {{W}}
  0.0,                                   !- Supply Air Sensible Heat Transfer Rate at Cooling Flow at Rated Conditions {{W}}
  0.0;                                   !- Supply Air Latent Heat Transfer Rate at Cooling Flow at Rated Conditions {{W}}

Schedule:Compact,
  {zone_name}_ERV_Availability,         !- Name
  AnyNumber,                             !- Schedule Type Limits Name
  Through: 12/31,                        !- Field 1
  For: AllDays,                          !- Field 2
  Until: 24:00,                          !- Field 3
  1.0;                                   !- Field 4 (Always available)

"""
        return erv_idf
    
    def should_add_erv(self, climate_zone: str) -> bool:
        """
        Determine if ERV should be added based on climate zone.
        
        ERV is most beneficial in:
        - Cold climates (heating dominated) - C6, C7, C8
        - Hot and humid climates (cooling/dehumidification) - C1, C2, C3
        
        Args:
            climate_zone: ASHRAE climate zone (e.g., 'ASHRAE_C5')
        
        Returns:
            True if ERV recommended for this climate
        """
        # Extract zone number
        zone_num = None
        try:
            if 'C' in climate_zone:
                zone_num = int(climate_zone.split('C')[1])
            elif '1' in climate_zone or '2' in climate_zone or '3' in climate_zone:
                zone_num = int(climate_zone[-1])
        except:
            pass
        
        # ERV recommended for:
        # - Very cold (C6, C7, C8) - heating dominated
        # - Hot humid (C1, C2, C3) - cooling/dehumidification
        if zone_num:
            return zone_num >= 6 or zone_num <= 3
        
        # Default: add ERV for cold climates (conservative)
        return 'C6' in climate_zone or 'C7' in climate_zone or 'C8' in climate_zone


def generate_dcv_for_zone(
    oa_controller_name: str,
    zone_name: str,
    method: str = 'CO2'
) -> str:
    """
    Convenience function for DCV generation.
    
    Args:
        oa_controller_name: Controller:OutdoorAir name
        zone_name: Zone name
        method: 'CO2' or 'Occupancy'
    
    Returns:
        DCV controller IDF string
    """
    ventilation = AdvancedVentilation()
    return ventilation.generate_dcv_controller(oa_controller_name, zone_name, method)


def generate_erv_for_zone(
    zone_name: str,
    supply_inlet_node: str,
    supply_outlet_node: str,
    exhaust_inlet_node: str,
    exhaust_outlet_node: str,
    supply_air_flow_rate: float,
    sensible_effectiveness: float = 0.7,
    latent_effectiveness: float = 0.65
) -> str:
    """
    Convenience function for ERV generation.
    
    Args:
        zone_name: Zone name
        supply_inlet_node: Outdoor air inlet
        supply_outlet_node: Conditioned OA outlet
        exhaust_inlet_node: Exhaust inlet
        exhaust_outlet_node: Exhaust outlet
        supply_air_flow_rate: Supply flow rate (m3/s)
        sensible_effectiveness: Sensible effectiveness
        latent_effectiveness: Latent effectiveness
    
    Returns:
        ERV IDF string
    """
    ventilation = AdvancedVentilation()
    return ventilation.generate_energy_recovery_ventilation(
        zone_name, supply_inlet_node, supply_outlet_node,
        exhaust_inlet_node, exhaust_outlet_node,
        supply_air_flow_rate,
        sensible_effectiveness=sensible_effectiveness,
        latent_effectiveness=latent_effectiveness
    )

