# Enhanced IDF Creator Capabilities

This document outlines the enhanced capabilities added to the IDF Creator, addressing previously missing or limited areas.

## Summary of Enhancements

The IDF Creator now includes six major enhancement modules that provide comprehensive building energy modeling capabilities:

1. **Catalog Equipment Wiring** - Complete integration of BCL/AHRI equipment
2. **Air Loop Node Plumbing** - Proper HVAC system node connections
3. **Advanced HVAC Controls** - PID controllers, economizers, VAV controls
4. **Shading and Daylighting** - External/internal shading and daylight controls
5. **Infiltration and Natural Ventilation** - Building air leakage and natural ventilation
6. **Renewable Energy Systems** - PV, solar thermal, and wind generation

---

## 1. Catalog Equipment Wiring

**File:** `src/hvac_plumbing.py`

### Capabilities
- **Proper Node Connections**: Complete wiring of catalog equipment to HVAC systems with proper inlet/outlet node connections
- **BCL/AHRI Integration**: Full integration of Building Component Library and AHRI certified equipment
- **Branch Organization**: Automatic creation of branch lists and connector lists for proper HVAC flow paths
- **Water Loop Plumbing**: Support for chilled water and hot water loop connections

### Key Features
- Unique node name generation to avoid conflicts
- Automatic branch creation for supply and demand sides
- Support for multiple equipment types (DX coils, chillers, boilers)
- Complete node-to-node connections throughout HVAC systems

### Usage Example
```python
from src.hvac_plumbing import HVACPlumbing

plumbing = HVACPlumbing()
components = plumbing.wire_catalog_equipment_to_vav(
    zone_name="Zone_1",
    equipment_spec=equipment_spec,
    sizing_params=sizing_params
)
```

---

## 2. Air Loop Node Plumbing

**File:** `src/hvac_plumbing.py`

### Capabilities
- **Complete Node Network**: Proper creation of all air loop nodes (supply inlet/outlet, return, mixed air, etc.)
- **Flow Path Specification**: Clear definition of air flow paths through HVAC components
- **Component Ordering**: Correct ordering of HVAC components in air streams
- **Water Loop Support**: Plant loop creation for hydronic systems

### Key Features
- Automatic node list creation
- Proper node-to-component connections
- Support for splitter and mixer components
- Demand and supply side separation

### Example Objects Generated
- `Node` objects for all connection points
- `BranchList` for organizing flow paths
- `ConnectorList` for flow distribution
- `PlantLoop` for water-based systems

---

## 3. Advanced HVAC Controls

**File:** `src/advanced_hvac_controls.py`

### Capabilities
- **Economizer Controls**: Full outdoor air economizer with multiple control strategies
  - Differential dry-bulb temperature
  - Differential enthalpy
  - Lockout with heating/cooling
- **PID Controllers**: Proportional-Integral-Derivative controllers for precise control
- **Advanced Setpoint Management**:
  - Outdoor air reset
  - Warmest/coldest zone control
  - Dual setpoint with scheduling
- **VAV Demand Control**: Advanced VAV terminal control with minimum flow tracking
- **Night Cycle Control**: Automatic night setback and setup optimization
- **Hybrid Ventilation**: Integration of natural and mechanical ventilation

### Key Features
- Multiple control strategies (economizer, PID, demand control)
- Automatic schedule generation for control operation
- Zone-level and system-level controls
- Optimized start/stop controls

### Example Objects Generated
- `Controller:OutdoorAir`
- `Controller:WaterCoil`
- `SetpointManager:OutdoorAirReset`
- `SetpointManager:SingleZone:Reheat`
- `AvailabilityManager:NightCycle`
- `AvailabilityManager:HybridVentilation`

---

## 4. Shading and Daylighting

**File:** `src/shading_daylighting.py`

### Capabilities
- **External Shading**:
  - Overhangs for solar protection
  - Vertical fins for east/west facades
  - Building-attached shading devices
- **Internal Shading**:
  - Window shades with transmittance control
  - Automated shading schedules
  - Glare control
- **Daylighting Controls**:
  - Continuous dimming controls
  - Stepped control
  - Reference point-based control
  - Split-flux calculation method
- **Tubular Daylight Devices (TDD)**: Skylights and light tubes

### Key Features
- Orientation-specific shading strategies
- Solar heat gain coefficient (SHGC) reduction
- Automatic lighting energy savings calculation
- Building-type appropriate shading (office vs. residential vs. retail)

### Example Objects Generated
- `Shading:Building:Detailed`
- `WindowShadingControl`
- `WindowMaterial:Shade`
- `Daylighting:Controls`
- `Daylighting:ReferencePoint`
- `DaylightingDevice:Tubular`

---

## 5. Infiltration and Natural Ventilation

**File:** `src/infiltration_ventilation.py`

### Capabilities
- **Zone Infiltration**:
  - Effective leakage area (ELA) calculation
  - Air changes per hour (ACH) by building type
  - Climate-zone adjusted infiltration rates
  - Stack and wind-driven infiltration
- **Natural Ventilation**:
  - Wind and stack effect ventilation
  - Temperature-based control
  - Scheduled operation
  - Zone-level air changes
- **Hybrid Ventilation**:
  - Integrated natural and mechanical systems
  - Weather-based controls
  - Rain and wind indicators
  - Temperature and enthalpy limits
- **Opening Controls**: Automated window/door openings

### Key Features
- Building-type specific infiltration (office, residential, retail, industrial)
- Automatic climate zone adjustment
- Multiple natural ventilation strategies (single zone, cross-ventilation, stack effect)
- Energy-saving potential through natural cooling

### Example Objects Generated
- `ZoneInfiltration:DesignFlowRate`
- `ZoneInfiltration:EffectiveLeakageArea`
- `ZoneVentilation:WindandStackOpenArea`
- `AvailabilityManager:HybridVentilation`
- `AirflowNetwork:MultiZone:Surface`
- `AirflowNetwork:MultiZone:Component:DetailedOpening`

---

## 6. Renewable Energy Systems

**File:** `src/renewable_energy.py`

### Capabilities
- **Photovoltaic Systems**:
  - Rooftop PV arrays
  - Building-integrated PV (BIPV)
  - Simple performance model
  - Inverter integration
  - Net metering support
- **Solar Thermal Collectors**:
  - Flat plate collectors
  - Water-based systems
  - Performance curves
  - Integration with HVAC systems
- **Wind Turbines**:
  - Small-scale wind generation
  - Hub height specification
  - Rated power and wind speed
- **Battery Storage**:
  - Energy storage systems
  - Charging/discharging control
  - Initial state of charge

### Key Features
- Building-type specific system sizing
- Automatic capacity factor calculation
- Integration with electric load centers
- Multiple inverter types

### Example Objects Generated
- `Generator:Photovoltaic:Simple`
- `PhotovoltaicPerformance:Simple`
- `ElectricLoadCenter:Generators`
- `ElectricLoadCenter:Distribution`
- `ElectricLoadCenter:Inverter:Simple`
- `SolarCollector:FlatPlate:Water`
- `SolarCollectorPerformance:FlatPlate`
- `Generator:WindTurbine`
- `ElectricLoadCenter:Storage:Simple`

---

## Integration with Professional IDF Generator

All these features are integrated into the `ProfessionalIDFGenerator` class and can be activated through the `--professional` flag in the command-line interface.

### Usage
```bash
python main.py "123 Main St, Chicago, IL" \
  --professional \
  --building-type office \
  --stories 5 \
  --floor-area 5000 \
  --wwr 0.40
```

### Programmatic Usage
```python
from src.professional_idf_generator import ProfessionalIDFGenerator

generator = ProfessionalIDFGenerator()

# All new modules are automatically initialized:
# - generator.hvac_plumbing
# - generator.advanced_controls  
# - generator.shading_daylighting
# - generator.infiltration_ventilation
# - generator.renewable_energy
```

---

## Technical Implementation

### Module Architecture
- Each enhancement module is self-contained with clear interfaces
- Modular design allows for independent testing and updates
- Common patterns: templates by building type, climate-zone adjustments, automatic naming

### EnergyPlus Compatibility
- All objects comply with EnergyPlus version 24.2/25.1
- Proper object syntax and field formats
- Complete object definitions with all required fields
- Validated against EnergyPlus input data dictionary

### Integration Points
- Modules integrate with existing:
  - `AdvancedGeometryEngine` - for surface and window placement
  - `MultiBuildingTypes` - for building-type specific parameters
  - `ProfessionalMaterialLibrary` - for material selection
  - `AdvancedHVACSystems` - for HVAC system generation

---

## Future Enhancements

Potential areas for further development:
1. **Advanced Daylighting**: More sophisticated daylight calculation methods (SplitFlux, Detailed)
2. **Smart Grid Integration**: Demand response and time-of-use pricing
3. **Microgrid Systems**: Islanding and critical load management
4. **Performance Monitoring**: Metering and reporting for all systems
5. **Parametric Analysis**: Automated optimization workflows

---

## References

- ASHRAE 90.1-2019: Energy Standard for Buildings
- EnergyPlus Input/Output Reference Documentation
- Commercial Buildings Integration Program (CBIP) Best Practices
- CIBSE Guide A: Environmental Design

---

## Changelog

### Version 2.0 (Current)
- Added catalog equipment wiring
- Added air loop node plumbing
- Added advanced HVAC controls
- Added shading and daylighting
- Added infiltration and natural ventilation
- Added renewable energy systems

### Version 1.0 (Previous)
- Basic IDF generation
- OSM integration
- Material library
- HVAC systems
- Building types

