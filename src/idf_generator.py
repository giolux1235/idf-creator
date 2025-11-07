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
  Yes,                     !- Do System Sizing Calculation
  Yes,                     !- Do Plant Sizing Calculation
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
        
        for story in range(1, stories + 1):
            zone_name = f"{building_name}_Zone_{story}"
            zones.append(f"""Zone,
  {zone_name},             !- Name
  {building_params.get('zone_area', 500):.2f},           !- Direction of Relative North
  0,                       !- X Origin
  0,                       !- Y Origin
  {(story - 1) * 3:.2f},                       !- Z Origin
  1,                       !- Type
  1,                       !- Multiplier
  {building_params.get('zone_area', 500) / 2.7:.2f},           !- Ceiling Height
  {building_params.get('zone_area', 500) * 2.7:.2f},           !- Volume
  autocalculate,           !- Floor Area
  ;                        !- Zone Inside Convection Algorithm
""")
        
        return zones
    
    def generate_surface_objects(self, building_params: Dict) -> List[str]:
        """Generate Surface objects for building envelope."""
        surfaces = []
        stories = building_params.get('stories', 3)
        length = building_params.get('length', 25)
        width = building_params.get('width', 20)
        height_per_story = building_params.get('height_per_story', 3)
        wwr = building_params.get('window_to_wall_ratio', 0.4)
        
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
  {length/2:.4f},0,{z_base:.4f}, !- Vertex 1
  -{length/2:.4f},0,{z_base:.4f}, !- Vertex 2
  -{length/2:.4f},{width:.4f},{z_base:.4f}, !- Vertex 3
  {length/2:.4f},{width:.4f},{z_base:.4f}; !- Vertex 4
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
  -{length/2:.4f},{width:.4f},{z_top:.4f}, !- Vertex 1
  -{length/2:.4f},0,{z_top:.4f}, !- Vertex 2
  {length/2:.4f},0,{z_top:.4f}, !- Vertex 3
  {length/2:.4f},{width:.4f},{z_top:.4f}; !- Vertex 4
""")
            
            # Four walls
            walls = [
                ("North", 0, 0, 0, width),
                ("South", length, 0, length, width),
                ("East", length, 0, 0, 0),
                ("West", 0, width, length, width)
            ]
            
            for wall_name, x1, y1, x2, y2 in walls:
                wall_area = abs((x2-x1) + (y2-y1)) * height_per_story
                window_area = wall_area * wwr
                
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
  {x1:.4f},{y1:.4f},{z_base:.4f}, !- Vertex 1
  {x1:.4f},{y1:.4f},{z_top:.4f}, !- Vertex 2
  {x2:.4f},{y2:.4f},{z_top:.4f}, !- Vertex 3
  {x2:.4f},{y2:.4f},{z_base:.4f}; !- Vertex 4
""")
                
                # Add window
                if window_area > 0:
                    window_name = f"{zone_name}_Window_{wall_name}"
                    win_z_bottom = z_base + height_per_story * 0.2
                    win_z_top = z_base + height_per_story * 0.8
                    
                    surfaces.append(f"""FenestrationSurface:Detailed,
  {window_name},           !- Name
  Window,                  !- Surface Type
  Building_Window,         !- Construction Name
  {zone_name}_Wall_{wall_name}, !- Building Surface Name
  ,                        !- Outside Boundary Condition Object
  AutoCalculate,           !- View Factor to Ground
  ,                        !- Frame and Divider Name
  1.0000,                  !- Multiplier
  4,                       !- Number of Vertices
  {x1:.4f},{y1:.4f},{win_z_bottom:.4f}, !- Vertex 1
  {x1:.4f},{y1:.4f},{win_z_top:.4f}, !- Vertex 2
  {x2:.4f},{y2:.4f},{win_z_top:.4f}, !- Vertex 3
  {x2:.4f},{y2:.4f},{win_z_bottom:.4f}; !- Vertex 4
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
        return f"""Lights,
  {zone_name}_Lights,      !- Name
  {zone_name},             !- Zone or ZoneList Name
  Lighting Schedule,       !- Schedule Name
  Watts/Area,              !- Design Level Calculation Method
  ,                        !- Lighting Level
  ,                        !- Watts per Zone Floor Area
  {zone_params.get('lighting_power', 5000):.1f},         !- Watts per Person
  ,                        !- Return Air Fraction
  ,                        !- Fraction Radiant
  0.7,                     !- Fraction Visible
  ,                        !- Fraction Replaceable
  GeneralLights;           !- End-Use Subcategory

"""
    
    def generate_equipment_objects(self, zone_params: Dict, zone_name: str) -> str:
        """Generate ElectricEquipment objects."""
        return f"""ElectricEquipment,
  {zone_name}_Equipment,   !- Name
  {zone_name},             !- Zone or ZoneList Name
  Equipment Schedule,      !- Schedule Name
  Watts/Area,              !- Design Level Calculation Method
  ,                        !- Design Level
  ,                        !- Watts per Zone Floor Area
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
  0;                       !- Field 11

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
  0.1;                     !- Field 11

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

        weather_file_days = """SizingPeriod:WeatherFileDays,
  Winter Sizing Weather File Day,  !- Name
  1,                          !- Begin Month
  21,                         !- Begin Day of Month
  1,                          !- End Month
  21,                         !- End Day of Month
  ,                           !- Day of Week for Start Day
  Yes,                        !- Use Weather File Daylight Saving Period
  No,                         !- Apply Weekend Holiday Rule
  Yes,                        !- Use Weather File Rain Indicators
  Yes;                        !- Use Weather File Snow Indicators

SizingPeriod:WeatherFileDays,
  Summer Sizing Weather File Day,  !- Name
  7,                          !- Begin Month
  21,                         !- Begin Day of Month
  7,                          !- End Month
  21,                         !- End Day of Month
  ,                           !- Day of Week for Start Day
  Yes,                        !- Use Weather File Daylight Saving Period
  No,                         !- Apply Weekend Holiday Rule
  Yes,                        !- Use Weather File Rain Indicators
  No;                         !- Use Weather File Snow Indicators
"""

        return "\n".join([heating_dd.strip("\n"), "", cooling_dd.strip("\n"), "", weather_file_days.strip("\n"), ""]) + "\n"

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

Output:Meter,
  NaturalGas:Facility,                     !- Key Name
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
        
        # Schedules
        idf_content.append(self.generate_schedules())
        
        # Weather
        idf_content.append(self.generate_weather_file_object(
            location.get('weather_file', 'USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw')
        ))
        
        # Output requests
        idf_content.append(self.generate_output_requests())
        
        return "".join(idf_content)



