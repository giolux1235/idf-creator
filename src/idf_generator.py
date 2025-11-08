"""Core module for generating EnergyPlus IDF files."""
from typing import Dict, List
import os

from src.core.base_idf_generator import BaseIDFGenerator


class IDFGenerator(BaseIDFGenerator):
    """Generates complete EnergyPlus IDF files from minimal inputs."""
    
    def __init__(self):
        """Initialize IDF generator with EnergyPlus version 24.2."""
        super().__init__(version="24.2")
    
    def generate_header(self) -> str:
        """Generate IDF file header."""
        return super().generate_header(generator_name="IDF Creator")
    
    def generate_simulation_control(self, run_period: Dict) -> str:
        """Generate SimulationControl object."""
        return f"""SimulationControl,
  Yes,                     !- Do Zone Sizing Calculation
  No,                      !- Do System Sizing Calculation
  No,                      !- Do Plant Sizing Calculation
  Yes,                     !- Run Simulation for Sizing Periods
  Yes,                     !- Run Simulation for Weather File Run Periods
  No,                      !- Do HVAC Sizing Simulation for Sizing Periods
  1;                       !- Maximum Number of HVAC Sizing Simulation Passes

"""
    
    def generate_run_period(self, start_date: str, end_date: str) -> str:
        """Generate RunPeriod object."""
        return f"""RunPeriod,
  Year Round Run Period,   !- Name
  1,                       !- Begin Month
  1,                       !- Begin Day of Month
  ,                        !- Begin Year
  12,                      !- End Month
  31,                      !- End Day of Month
  ,                        !- End Year
  ,                        !- Day of Week for Start Day
  ,                        !- Use Weather File Holidays and Special Days
  ,                        !- Use Weather File Daylight Saving Period
  ,                        !- Apply Weekend Holiday Rule
  ,                        !- Use Weather File Rain Indicators
  ;                        !- Use Weather File Snow Indicators

"""
    
    def generate_building_section(self, name: str, north_axis: float = 0.0) -> str:
        """Generate Building object."""
        # Note: Building object for EnergyPlus 24/25 compatibility
        return f"""Building,
  {name},                  !- Name
  {north_axis:.4f},        !- North Axis
  Suburbs,                 !- Terrain
  0.0400,                   !- Loads Convergence Tolerance Value {{W}}
  0.2000,                   !- Temperature Convergence Tolerance Value {{deltaC}}
  FullInteriorAndExterior, !- Solar Distribution
  15,                       !- Maximum Number of Warmup Days
  6;                        !- Minimum Number of Warmup Days

"""
    
    def generate_site_location(self, location: Dict) -> str:
        """Generate Site:Location object."""
        # Get latitude and longitude - REQUIRED, should come from geocoding
        latitude = location.get('latitude')
        longitude = location.get('longitude')
        
        # Validate coordinates are present
        if latitude is None or longitude is None:
            address = location.get('address', 'Unknown Location')
            raise ValueError(
                f"CRITICAL: Missing coordinates in location_data for address '{address}'. "
                f"Geocoding must have failed. Latitude: {latitude}, Longitude: {longitude}"
            )
        
        # Get elevation - check both 'elevation' and 'altitude' keys
        elevation = location.get('elevation') or location.get('altitude')
        if elevation is None:
            elevation = 100.0  # Default elevation
        
        # Get time zone - should be calculated from coordinates
        time_zone = location.get('time_zone')
        if time_zone is None:
            # Calculate timezone from longitude if not provided
            if -125 <= longitude < -102:  # Pacific Time
                time_zone = -8.0
            elif -102 <= longitude < -90:  # Mountain Time
                time_zone = -7.0
            elif -90 <= longitude < -75:  # Central Time (includes Chicago)
                time_zone = -6.0
            elif -75 <= longitude < -60:  # Eastern Time
                time_zone = -5.0
            else:
                time_zone = round(longitude / 15.0, 1)
        
        # Use address as location name, fallback to 'Custom Location'
        address = location.get('address', '')
        location_name = address if address else 'Custom Location'
        location_name = location_name.replace(',', ' -').replace(';', '').replace('\n', ' ').replace('\r', ' ')
        location_name = ' '.join(location_name.split())
        
        return f"""Site:Location,
  {location_name},         !- Name
  {latitude:.3f},                  !- Latitude
  {longitude:.3f},                !- Longitude
  {time_zone:.1f},                  !- Time Zone
  {elevation:.1f};                 !- Elevation

"""
    
    def generate_material_objects(self, materials: Dict) -> str:
        """Generate Material objects with proper ASHRAE properties."""
        return """Material,
  Building_Wall,           !- Name
  MediumRough,             !- Roughness
  0.2032000,               !- Thickness
  0.1152900,               !- Conductivity
  513.0000,                !- Density
  1381.0000,               !- Specific Heat
  0.9000000,               !- Thermal Absorptance
  0.7000000,               !- Solar Absorptance
  0.7000000;               !- Visible Absorptance

Material:NoMass,
  Building_Floor,          !- Name
  MediumRough,             !- Roughness
  2.9074112,               !- Thermal Resistance
  0.9000000,               !- Thermal Absorptance
  0.7000000,               !- Solar Absorptance
  0.7000000;               !- Visible Absorptance

Material:NoMass,
  Building_Roof,           !- Name
  MediumRough,             !- Roughness
  2.0000000,               !- Thermal Resistance
  0.9000000,               !- Thermal Absorptance
  0.7000000,               !- Solar Absorptance
  0.7000000;               !- Visible Absorptance

WindowMaterial:SimpleGlazingSystem,
  Building_Window,         !- Name
  2.9130000,               !- U-Factor
  0.3500000;               !- Solar Heat Gain Coefficient

"""
    
    def generate_construction_objects(self, constructions: Dict) -> str:
        """Generate Construction objects."""
        return """Construction,
  Building_ExteriorWall,   !- Name
  Building_Wall;           !- Layer 1

Construction,
  Building_ExteriorRoof,   !- Name
  Building_Roof;           !- Layer 1

Construction,
  Building_ExteriorFloor,  !- Name
  Building_Floor;          !- Layer 1

Construction,
  Building_Window,         !- Name
  Building_Window;         !- Layer 1

"""
    
    def generate_zone_objects(self, building_params: Dict) -> List[str]:
        """Generate Zone objects for each story."""
        zones = []
        stories = building_params.get('stories', 3)
        building_name = building_params.get('name', 'Building')
        length = building_params.get('length', 25.0)
        width = building_params.get('width', 20.0)
        floor_area = building_params.get('floor_area', length * width * max(stories, 1))
        height_per_story = building_params.get('height_per_story', 3.0)
        north_axis = building_params.get('north_axis', 0.0)
        zone_area = floor_area / max(stories, 1)
        
        for story in range(1, stories + 1):
            zone_name = f"{building_name}_Zone_{story}"
            zones.append(f"""Zone,
  {zone_name},             !- Name
  {north_axis:.2f},        !- Direction of Relative North
  0,                       !- X Origin
  0,                       !- Y Origin
  {(story - 1) * height_per_story:.2f}, !- Z Origin
  1,                       !- Type
  1,                       !- Multiplier
  {height_per_story:.2f},  !- Ceiling Height
  {zone_area * height_per_story:.2f}, !- Volume
  {zone_area:.2f},         !- Floor Area
  ;                        !- Zone Inside Convection Algorithm
""")
        
        return zones
    
    def generate_surface_objects(self, building_params: Dict) -> List[str]:
        """Generate Surface objects for building envelope."""
        surfaces = []
        stories = building_params.get('stories', 3)
        length = building_params.get('length', 25.0)
        width = building_params.get('width', 20.0)
        height_per_story = building_params.get('height_per_story', 3.0)
        wwr = building_params.get('window_to_wall_ratio', 0.4)
        x_min = -length / 2.0
        x_max = length / 2.0
        y_min = -width / 2.0
        y_max = width / 2.0
        
        for story in range(1, stories + 1):
            zone_name = f"{building_params.get('name', 'Building')}_Zone_{story}"
            z_base = (story - 1) * height_per_story
            z_top = story * height_per_story
            
            # Floor
            surfaces.append(f"""BuildingSurface:Detailed,
  {zone_name}_Floor,       !- Name
  Floor,                   !- Surface Type
  Building_ExteriorFloor,  !- Construction Name
  {zone_name},             !- Zone Name
  ,                        !- Space Name
  Outdoors,                !- Outside Boundary Condition
  ,                        !- Outside Boundary Condition Object
  NoSun,                   !- Sun Exposure
  NoWind,                  !- Wind Exposure
  AutoCalculate,           !- View Factor to Ground
  4,                       !- Number of Vertices
  {x_max:.4f},{y_min:.4f},{z_base:.4f}, !- Vertex 1
  {x_min:.4f},{y_min:.4f},{z_base:.4f}, !- Vertex 2
  {x_min:.4f},{y_max:.4f},{z_base:.4f}, !- Vertex 3
  {x_max:.4f},{y_max:.4f},{z_base:.4f}; !- Vertex 4
""")
            
            # Ceiling
            surfaces.append(f"""BuildingSurface:Detailed,
  {zone_name}_Ceiling,     !- Name
  Roof,                    !- Surface Type
  Building_ExteriorRoof,   !- Construction Name
  {zone_name},             !- Zone Name
  ,                        !- Space Name
  Outdoors,                !- Outside Boundary Condition
  ,                        !- Outside Boundary Condition Object
  SunExposed,              !- Sun Exposure
  WindExposed,             !- Wind Exposure
  AutoCalculate,           !- View Factor to Ground
  4,                       !- Number of Vertices
  {x_min:.4f},{y_max:.4f},{z_top:.4f}, !- Vertex 1
  {x_min:.4f},{y_min:.4f},{z_top:.4f}, !- Vertex 2
  {x_max:.4f},{y_min:.4f},{z_top:.4f}, !- Vertex 3
  {x_max:.4f},{y_max:.4f},{z_top:.4f}; !- Vertex 4
""")
            
            wall_definitions = [
                ("North", (x_min, y_max), (x_max, y_max), length),
                ("South", (x_max, y_min), (x_min, y_min), length),
                ("East", (x_max, y_max), (x_max, y_min), width),
                ("West", (x_min, y_min), (x_min, y_max), width),
            ]
            
            for wall_name, (wx1, wy1), (wx2, wy2), wall_width in wall_definitions:
                wall_area = wall_width * height_per_story
                window_area = max(wall_area * wwr, 0.0)
                
                surfaces.append(f"""BuildingSurface:Detailed,
  {zone_name}_Wall_{wall_name}, !- Name
  Wall,                    !- Surface Type
  Building_ExteriorWall,   !- Construction Name
  {zone_name},             !- Zone Name
  ,                        !- Space Name
  Outdoors,                !- Outside Boundary Condition
  ,                        !- Outside Boundary Condition Object
  SunExposed,              !- Sun Exposure
  WindExposed,             !- Wind Exposure
  AutoCalculate,           !- View Factor to Ground
  4,                       !- Number of Vertices
  {wx1:.4f},{wy1:.4f},{z_base:.4f}, !- Vertex 1
  {wx1:.4f},{wy1:.4f},{z_top:.4f}, !- Vertex 2
  {wx2:.4f},{wy2:.4f},{z_top:.4f}, !- Vertex 3
  {wx2:.4f},{wy2:.4f},{z_base:.4f}; !- Vertex 4
""")
                
                if window_area <= 0:
                    continue
                
                usable_wall_height = height_per_story * 0.7
                window_width = wall_width * 0.7
                window_height = min(window_area / max(window_width, 0.1), usable_wall_height)
                vertical_margin = max((height_per_story - window_height) / 2.0, 0.5)
                win_z_bottom = z_base + vertical_margin
                win_z_top = min(win_z_bottom + window_height, z_top - 0.1)
                inset = wall_width * 0.15
                
                if wall_name in ("North", "South"):
                    win_x_min = wx1 + inset if wall_name == "North" else wx2 + inset
                    win_x_max = wx2 - inset if wall_name == "North" else wx1 - inset
                    win_y = wy1
                    surfaces.append(f"""FenestrationSurface:Detailed,
  {zone_name}_Window_{wall_name}, !- Name
  Window,                  !- Surface Type
  Building_Window,         !- Construction Name
  {zone_name}_Wall_{wall_name}, !- Building Surface Name
  ,                        !- Outside Boundary Condition Object
  AutoCalculate,           !- View Factor to Ground
  ,                        !- Frame and Divider Name
  1.0000,                  !- Multiplier
  4,                       !- Number of Vertices
  {win_x_min:.4f},{win_y:.4f},{win_z_bottom:.4f}, !- Vertex 1
  {win_x_min:.4f},{win_y:.4f},{win_z_top:.4f}, !- Vertex 2
  {win_x_max:.4f},{win_y:.4f},{win_z_top:.4f}, !- Vertex 3
  {win_x_max:.4f},{win_y:.4f},{win_z_bottom:.4f}; !- Vertex 4
""")
                else:
                    win_y_min = wy1 + inset if wall_name == "East" else wy2 + inset
                    win_y_max = wy2 - inset if wall_name == "East" else wy1 - inset
                    win_x = wx1
                    surfaces.append(f"""FenestrationSurface:Detailed,
  {zone_name}_Window_{wall_name}, !- Name
  Window,                  !- Surface Type
  Building_Window,         !- Construction Name
  {zone_name}_Wall_{wall_name}, !- Building Surface Name
  ,                        !- Outside Boundary Condition Object
  AutoCalculate,           !- View Factor to Ground
  ,                        !- Frame and Divider Name
  1.0000,                  !- Multiplier
  4,                       !- Number of Vertices
  {win_x:.4f},{win_y_min:.4f},{win_z_bottom:.4f}, !- Vertex 1
  {win_x:.4f},{win_y_min:.4f},{win_z_top:.4f}, !- Vertex 2
  {win_x:.4f},{win_y_max:.4f},{win_z_top:.4f}, !- Vertex 3
  {win_x:.4f},{win_y_max:.4f},{win_z_bottom:.4f}; !- Vertex 4
""")
        
        return surfaces
    
    def generate_people_objects(self, zone_params: Dict, zone_name: str) -> str:
        """Generate People objects."""
        return f"""People,
  {zone_name}_People,      !- Name
  {zone_name},             !- Zone or ZoneList Name
  People Occupancy Schedule, !- Number of People Schedule Name
  People,                  !- Number of People Calculation Method
  {zone_params.get('number_of_people', 35)},              !- Number of People
  ,                        !- People per Zone Floor Area
  ,                        !- Zone Floor Area per Person
  0.3,                     !- Fraction Radiant
  0,                       !- Sensible Heat Fraction
  Activity Schedule;       !- Activity Level Schedule Name

"""
    
    def generate_lighting_objects(self, zone_params: Dict, zone_name: str) -> str:
        """Generate Lights objects."""
        total_lighting_watts = zone_params.get('lighting_power', 0.0)
        return f"""Lights,
  {zone_name}_Lights,      !- Name
  {zone_name},             !- Zone or ZoneList Name
  Lighting Schedule,       !- Schedule Name
  LightingLevel,           !- Design Level Calculation Method
  {total_lighting_watts:.1f},   !- Lighting Level {{W}}
  ,                        !- Watts per Zone Floor Area
  ,                        !- Watts per Person
  ,                        !- Return Air Fraction
  ,                        !- Fraction Radiant
  0.7,                     !- Fraction Visible
  ,                        !- Fraction Replaceable
  GeneralLights;           !- End-Use Subcategory

"""
    
    def generate_equipment_objects(self, zone_params: Dict, zone_name: str) -> str:
        """Generate ElectricEquipment objects."""
        zone_area = max(zone_params.get('zone_area', 1.0), 1.0)
        equipment_density = 0.0
        if zone_area > 0.0:
            equipment_density = zone_params.get('equipment_power', 0.0) / zone_area
        return f"""ElectricEquipment,
  {zone_name}_Equipment,   !- Name
  {zone_name},             !- Zone or ZoneList Name
  Equipment Schedule,      !- Schedule Name
  Watts/Area,              !- Design Level Calculation Method
  ,                        !- Design Level
  {equipment_density:.4f}, !- Watts per Zone Floor Area
  ,                        !- Watts per Person
  0.1,                     !- Fraction Latent
  0.2,                     !- Fraction Radiant
  0,                       !- Fraction Lost
  General;                 !- End-Use Subcategory

"""
    
    def generate_hvac_objects(self, zone_params: Dict, zone_name: str) -> str:
        """Generate HVAC ideal loads system."""
        return f"""ZoneHVAC:IdealLoadsAirSystem,
  {zone_name}_HVAC,        !- Name
  Always On,               !- Availability Schedule Name
  {zone_name} Supply Node, !- Zone Supply Air Node Name
  {zone_name} Exhaust Node,!- Zone Exhaust Air Node Name
  50,                      !- Maximum Heating Supply Air Temperature
  13,                      !- Minimum Cooling Supply Air Temperature
  0.015,                   !- Maximum Heating Supply Air Humidity Ratio
  0.009,                   !- Minimum Cooling Supply Air Humidity Ratio
  ,                        !- Heating Limit
  ,                        !- Maximum Sensible Heating Capacity
  ,                        !- Cooling Limit
  ,                        !- Maximum Total Cooling Capacity
  ,                        !- Heating Supply Air Flow Rate
  ,                        !- Cooling Supply Air Flow Rate
  ,                        !- Heating Outdoor Air Flow Rate
  ,                        !- Cooling Outdoor Air Flow Rate
  ;                        !- Outdoor Air Inlet Node Name

"""

    def generate_zone_equipment_list(self, zone_name: str) -> str:
        """Generate ZoneHVAC equipment list linking the ideal loads system."""
        return f"""ZoneHVAC:EquipmentList,
  {zone_name}_EquipmentList,  !- Name
  SequentialLoad,            !- Load Distribution Scheme
  ZoneHVAC:IdealLoadsAirSystem, !- Zone Equipment 1 Object Type
  {zone_name}_HVAC,          !- Zone Equipment 1 Name
  1,                         !- Zone Equipment 1 Cooling Sequence
  1;                         !- Zone Equipment 1 Heating Sequence

"""

    def generate_zone_equipment_connections(self, zone_name: str) -> str:
        """Generate ZoneHVAC:EquipmentConnections for each zone."""
        return f"""ZoneHVAC:EquipmentConnections,
  {zone_name},               !- Zone Name
  {zone_name}_EquipmentList, !- Zone Conditioning Equipment List Name
  {zone_name} Supply Node,   !- Zone Air Inlet Node or NodeList Name
  {zone_name} Exhaust Node,  !- Zone Air Exhaust Node or NodeList Name
  {zone_name} Supply Node,   !- Zone Air Node Name
  {zone_name} Return Node,   !- Zone Return Air Node Name
  ;                          !- Zone Return Air Node or NodeList Name

"""

    def generate_zone_sizing_object(self, zone_name: str, zone_params: Dict) -> str:
        """Generate Sizing:Zone object so zones can autosize."""
        return f"""Sizing:Zone,
  {zone_name},               !- Zone or ZoneList Name
  SupplyAirTemperature,      !- Zone Cooling Design Supply Air Temperature Input Method
  12.8,                      !- Zone Cooling Design Supply Air Temperature {{C}}
  ,                          !- Zone Cooling Design Supply Air Temperature Difference {{deltaC}}
  SupplyAirTemperature,      !- Zone Heating Design Supply Air Temperature Input Method
  40.0,                      !- Zone Heating Design Supply Air Temperature {{C}}
  ,                          !- Zone Heating Design Supply Air Temperature Difference {{deltaC}}
  0.0085,                    !- Zone Cooling Design Supply Air Humidity Ratio {{kgWater/kgDryAir}}
  0.0080,                    !- Zone Heating Design Supply Air Humidity Ratio {{kgWater/kgDryAir}}
  ,                          !- Design Specification Outdoor Air Object Name
  1.0,                       !- Zone Heating Sizing Factor
  1.0,                       !- Zone Cooling Sizing Factor
  DesignDay,                 !- Cooling Design Air Flow Method
  ,                          !- Cooling Design Air Flow Rate {{m3/s}}
  ,                          !- Cooling Minimum Air Flow per Zone Floor Area {{m3/s-m2}}
  0.0,                       !- Cooling Minimum Air Flow {{m3/s}}
  ,                          !- Cooling Minimum Air Flow Fraction
  DesignDay,                 !- Heating Design Air Flow Method
  ,                          !- Heating Design Air Flow Rate {{m3/s}}
  ,                          !- Heating Maximum Air Flow per Zone Floor Area {{m3/s-m2}}
  ,                          !- Heating Maximum Air Flow {{m3/s}}
  ,                          !- Heating Maximum Air Flow Fraction
  ,                          !- Design Specification Zone Air Distribution Object Name
  No,                        !- Account for Dedicated Outdoor Air System
  NeutralSupplyAir,          !- Dedicated Outdoor Air System Control Strategy
  13.0,                      !- Dedicated Outdoor Air Low Setpoint Temperature for Design {{C}}
  40.0;                      !- Dedicated Outdoor Air High Setpoint Temperature for Design {{C}}

"""
    
    def generate_schedules(self) -> str:
        """Generate Schedule objects."""
        return f"""ScheduleTypeLimits,
  AnyNumber;               !- Name

ScheduleTypeLimits,
  Fraction;                !- Name

Schedule:Compact,
  Always On,               !- Name
  AnyNumber,               !- Schedule Type Limits Name
  Through: 12/31,          !- Field 1
  For: AllDays,            !- Field 2
  Until: 24:00,            !- Field 3
  1.0;                     !- Field 4

Schedule:Compact,
  Always Off,              !- Name
  AnyNumber,               !- Schedule Type Limits Name
  Through: 12/31,          !- Field 1
  For: AllDays,            !- Field 2
  Until: 24:00,            !- Field 3
  0.0;                     !- Field 4

Schedule:Compact,
  People Occupancy Schedule, !- Name
  Fraction,                !- Schedule Type Limits Name
  Through: 12/31,          !- Field 1
  For: Weekdays,           !- Field 2
  Until: 6:00,             !- Field 3
  0,                       !- Field 4
  Until: 22:00,            !- Field 5
  1,                       !- Field 6
  Until: 24:00,            !- Field 7
  0,                       !- Field 8
  For: Weekends,           !- Field 9
  Until: 24:00,            !- Field 10
  0,                       !- Field 11
  For: SummerDesignDay,    !- Field 12
  Until: 24:00,            !- Field 13
  1,                       !- Field 14
  For: WinterDesignDay,    !- Field 15
  Until: 24:00,            !- Field 16
  1,                       !- Field 17
  For: CustomDay1,         !- Field 18
  Until: 24:00,            !- Field 19
  1,                       !- Field 20
  For: CustomDay2,         !- Field 21
  Until: 24:00,            !- Field 22
  1;                       !- Field 23

Schedule:Compact,
  Lighting Schedule,       !- Name
  Fraction,                !- Schedule Type Limits Name
  Through: 12/31,          !- Field 1
  For: AllDays,            !- Field 2
  Until: 7:00,             !- Field 3
  0.1,                     !- Field 4
  Until: 21:00,            !- Field 5
  1,                       !- Field 6
  Until: 24:00,            !- Field 7
  0.1;                     !- Field 8

Schedule:Compact,
  Equipment Schedule,      !- Name
  Fraction,                !- Schedule Type Limits Name
  Through: 12/31,          !- Field 1
  For: Weekdays,           !- Field 2
  Until: 8:00,             !- Field 3
  0.1,                     !- Field 4
  Until: 18:00,            !- Field 5
  1,                       !- Field 6
  Until: 24:00,            !- Field 7
  0.1,                     !- Field 8
  For: Weekends,           !- Field 9
  Until: 24:00,            !- Field 10
  0.1,                     !- Field 11
  For: SummerDesignDay,    !- Field 12
  Until: 24:00,            !- Field 13
  1,                       !- Field 14
  For: WinterDesignDay,    !- Field 15
  Until: 24:00,            !- Field 16
  1,                       !- Field 17
  For: CustomDay1,         !- Field 18
  Until: 24:00,            !- Field 19
  1,                       !- Field 20
  For: CustomDay2,         !- Field 21
  Until: 24:00,            !- Field 22
  1;                       !- Field 23

Schedule:Compact,
  Activity Schedule,       !- Name
  AnyNumber,               !- Schedule Type Limits Name
  Through: 12/31,          !- Field 1
  For: AllDays,            !- Field 2
  Until: 24:00,            !- Field 3
  120;                     !- Field 4

"""
    
    def generate_global_geometry_rules(self) -> str:
        """Generate GlobalGeometryRules object."""
        return """GlobalGeometryRules,
  UpperLeftCorner,        !- Starting Vertex Position
  CounterClockWise,       !- Vertex Entry Direction
  Relative;               !- Coordinate System

"""

    def _sanitize_location_name(self, location: Dict) -> str:
        """Create a sanitized location label for design-day naming."""
        name = location.get('address') or location.get('weather_city_name') or location.get('city') or 'Site'
        name = str(name).replace(',', '_').replace(';', '_').replace('\n', ' ').replace('\r', ' ')
        name = ' '.join(name.split())
        return name[:100] if len(name) > 100 else name

    def generate_design_day_objects(self, location: Dict, config: Dict) -> str:
        """Generate fallback design days and weather-file sizing periods."""
        climate_zone = (config or {}).get('climate_zone') or location.get('climate_zone')
        params = self._default_design_day_parameters(climate_zone)
        elevation = location.get('elevation') or location.get('altitude')
        baro = self._estimate_barometric_pressure(elevation)
        location_name = self._sanitize_location_name(location)

        heating_name = f"{location_name} Winter Design Day"
        cooling_name = f"{location_name} Summer Design Day"

        heating_dd = f"""SizingPeriod:DesignDay,
  {heating_name},             !- Name
  1,                          !- Month
  21,                         !- Day of Month
  WinterDesignDay,            !- Day Type
  {params['heating_dry_bulb']:.1f},  !- Maximum Dry-Bulb Temperature {{C}}
  0.0,                        !- Daily Dry-Bulb Temperature Range {{deltaC}}
  ,                           !- Dry-Bulb Temperature Range Modifier Type
  ,                           !- Dry-Bulb Temperature Range Modifier Day Schedule Name
  WetBulb,                    !- Humidity Condition Type
  {params['heating_wet_bulb']:.1f},  !- Wetbulb or DewPoint at Maximum Dry-Bulb {{C}}
  ,                           !- Humidity Condition Day Schedule Name
  ,                           !- Humidity Ratio at Maximum Dry-Bulb {{kgWater/kgDryAir}}
  ,                           !- Enthalpy at Maximum Dry-Bulb {{J/kg}}
  ,                           !- Daily Wet-Bulb Temperature Range {{deltaC}}
  {baro:.0f},                 !- Barometric Pressure {{Pa}}
  {params['heating_wind_speed']:.1f}, !- Wind Speed {{m/s}}
  {params['heating_wind_direction']:.0f}, !- Wind Direction {{deg}}
  No,                         !- Rain Indicator
  No,                         !- Snow Indicator
  Yes,                        !- Daylight Saving Time Indicator
  ASHRAEClearSky,             !- Solar Model Indicator
  ,                           !- Beam Solar Day Schedule Name
  ,                           !- Diffuse Solar Day Schedule Name
  0.0,                        !- ASHRAE Clear Sky Optical Depth for Beam Irradiance (taub)
  0.0,                        !- ASHRAE Clear Sky Optical Depth for Diffuse Irradiance (taud)
  0.0;                        !- Sky Clearness
"""

        cooling_dd = f"""SizingPeriod:DesignDay,
  {cooling_name},             !- Name
  7,                          !- Month
  21,                         !- Day of Month
  SummerDesignDay,            !- Day Type
  {params['cooling_dry_bulb']:.1f},  !- Maximum Dry-Bulb Temperature {{C}}
  {params['cooling_daily_range']:.1f}, !- Daily Dry-Bulb Temperature Range {{deltaC}}
  ,                           !- Dry-Bulb Temperature Range Modifier Type
  ,                           !- Dry-Bulb Temperature Range Modifier Day Schedule Name
  WetBulb,                    !- Humidity Condition Type
  {params['cooling_wet_bulb']:.1f},  !- Wetbulb or DewPoint at Maximum Dry-Bulb {{C}}
  ,                           !- Humidity Condition Day Schedule Name
  ,                           !- Humidity Ratio at Maximum Dry-Bulb {{kgWater/kgDryAir}}
  ,                           !- Enthalpy at Maximum Dry-Bulb {{J/kg}}
  ,                           !- Daily Wet-Bulb Temperature Range {{deltaC}}
  {baro:.0f},                 !- Barometric Pressure {{Pa}}
  {params['cooling_wind_speed']:.1f}, !- Wind Speed {{m/s}}
  {params['cooling_wind_direction']:.0f}, !- Wind Direction {{deg}}
  No,                         !- Rain Indicator
  No,                         !- Snow Indicator
  Yes,                        !- Daylight Saving Time Indicator
  ASHRAEClearSky,             !- Solar Model Indicator
  ,                           !- Beam Solar Day Schedule Name
  ,                           !- Diffuse Solar Day Schedule Name
  0.0,                        !- ASHRAE Clear Sky Optical Depth for Beam Irradiance (taub)
  0.0,                        !- ASHRAE Clear Sky Optical Depth for Diffuse Irradiance (taud)
  0.0;                        !- Sky Clearness
"""

        return "\n".join([heating_dd.strip("\n"), "", cooling_dd.strip("\n"), ""]) + "\n"

    def generate_weather_file_object(self, weather_file: str) -> str:
        """Generate EPW weather file reference."""
        return f"""Site:GroundTemperature:BuildingSurface,
  20,                      !- January Ground Temperature
  20,                      !- February Ground Temperature
  20,                      !- March Ground Temperature
  20,                      !- April Ground Temperature
  20,                      !- May Ground Temperature
  20,                      !- June Ground Temperature
  20,                      !- July Ground Temperature
  20,                      !- August Ground Temperature
  20,                      !- September Ground Temperature
  20,                      !- October Ground Temperature
  20,                      !- November Ground Temperature
  20;                      !- December Ground Temperature

Site:GroundTemperature:Shallow,
  13,                      !- January Ground Temperature
  13,                      !- February Ground Temperature
  13,                      !- March Ground Temperature
  13,                      !- April Ground Temperature
  13,                      !- May Ground Temperature
  13,                      !- June Ground Temperature
  13,                      !- July Ground Temperature
  13,                      !- August Ground Temperature
  13,                      !- September Ground Temperature
  13,                      !- October Ground Temperature
  13,                      !- November Ground Temperature
  13;                      !- December Ground Temperature

"""
    
    def generate_output_requests(self) -> str:
        """Generate output request objects."""
        return f"""Output:VariableDictionary,
  IDF;                     !- Key Field

Output:SQLite,
  SimpleAndTabular;        !- Option Type

Output:Table:SummaryReports,
  AllSummary;              !- Report Name

Output:Meter,
  Electricity:Facility,                    !- Key Name
  RunPeriod;                               !- Reporting Frequency

"""
    
    def generate_complete_idf(self, location: Dict, building_params: Dict, 
                             zone_params: Dict, config: Dict) -> str:
        """
        Generate complete IDF file from all parameters.
        
        Args:
            location: Location and climate data
            building_params: Building geometry parameters
            zone_params: Zone-level parameters
            config: Configuration settings
            
        Returns:
            Complete IDF file as string
        """
        self.reset_unique_names()
        idf_content = []
        
        # Header
        idf_content.append(self.generate_header())
        idf_content.append(self.generate_version_section())
        
        # Simulation setup
        idf_content.append(self.generate_simulation_control(config.get('simulation', {})))
        idf_content.append("Timestep,4;\n\n")
        idf_content.append(self.generate_run_period("1/1", "12/31"))
        idf_content.append(self.generate_design_day_objects(location, config))
 
        # Building and location
        idf_content.append(self.generate_building_section(
            building_params.get('name', 'Simple Building')
        ))
        idf_content.append(self.generate_site_location(location))
        idf_content.append(self.generate_global_geometry_rules())
        
        # Materials and constructions
        idf_content.append(self.generate_material_objects(config.get('materials', {})))
        idf_content.append(self.generate_construction_objects({}))
        
        # Zones
        zones = self.generate_zone_objects(building_params)
        for zone in zones:
            idf_content.append(zone)
        
        # Surfaces
        surfaces = self.generate_surface_objects(building_params)
        for surface in surfaces:
            idf_content.append(surface)
        
        # Loads for all zones
        for story in range(1, building_params.get('stories', 3) + 1):
            zone_name = f"{building_params.get('name', 'Building')}_Zone_{story}"
            idf_content.append(self.generate_people_objects(zone_params, zone_name))
            idf_content.append(self.generate_lighting_objects(zone_params, zone_name))
            idf_content.append(self.generate_equipment_objects(zone_params, zone_name))
            idf_content.append(self.generate_hvac_objects(zone_params, zone_name))
            idf_content.append(self.generate_zone_equipment_list(zone_name))
            idf_content.append(self.generate_zone_equipment_connections(zone_name))
            idf_content.append(self.generate_zone_sizing_object(zone_name, zone_params))
        
        # Schedules
        idf_content.append(self.generate_schedules())
        
        # Weather
        idf_content.append(self.generate_weather_file_object(
            location.get('weather_file', 'USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw')
        ))
        
        # Output requests
        idf_content.append(self.generate_output_requests())
        
        return "".join(idf_content)



