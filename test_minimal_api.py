#!/usr/bin/env python3
"""
Test with minimal IDF to see what API actually needs
"""

import requests
import json
import base64
from pathlib import Path

API_URL = "https://web-production-1d1be.up.railway.app/simulate"

# Minimal valid IDF
minimal_idf = """Version,
  25.1;                    !- Version Identifier

SimulationControl,
  No,                      !- Do Zone Sizing Calculation
  No,                      !- Do System Sizing Calculation
  No,                      !- Do Plant Sizing Calculation
  No,                      !- Run Simulation for Sizing Periods
  Yes,                     !- Run Simulation for Weather File Run Periods
  No,                      !- Do HVAC Sizing Simulation for Sizing Periods
  1;                       !- Maximum Number of HVAC Sizing Simulation Passes

Building,
  Test Building,           !- Name
  0.0,                     !- North Axis
  Suburbs,                 !- Terrain
  0.04,                    !- Loads Convergence Tolerance Value {W}
  0.2,                     !- Temperature Convergence Tolerance Value {deltaC}
  FullInteriorAndExterior, !- Solar Distribution
  15,                      !- Maximum Number of Warmup Days
  6;                       !- Minimum Number of Warmup Days

GlobalGeometryRules,
  UpperLeftCorner,         !- Starting Vertex Position
  CounterClockWise,        !- Vertex Entry Direction
  Relative;                !- Coordinate System

Site:Location,
  Test Location,           !- Name
  41.879,                  !- Latitude
  -87.636,                 !- Longitude
  -6.0,                    !- Time Zone
  100.0;                   !- Elevation {m}

RunPeriod,
  Year Round,              !- Name
  1,                       !- Begin Month
  1,                       !- Begin Day of Month
  ,                        !- Begin Year
  12,                      !- End Month
  31,                      !- End Day of Month
  ,                        !- End Year
  ,                        !- Day of Week for Start Day
  Yes,                     !- Use Weather File Holidays and Special Days
  Yes,                     !- Use Weather File Daylight Saving Period
  Yes,                     !- Apply Weekend Holiday Rule
  Yes,                     !- Use Weather File Rain Indicators
  Yes;                     !- Use Weather File Snow Indicators

Timestep,
  6;                       !- Number of Timesteps per Hour

Zone,
  Zone1,                   !- Name
  0.0,                     !- Direction of Relative North {deg}
  0.0,                     !- X Origin {m}
  0.0,                     !- Y Origin {m}
  0.0,                     !- Z Origin {m}
  1,                       !- Type
  1,                       !- Multiplier
  autocalculate,           !- Ceiling Height {m}
  autocalculate,           !- Volume {m3}
  ,                        !- Floor Area {m2}
  ,                        !- Zone Inside Convection Algorithm
  ,                        !- Zone Outside Convection Algorithm
  ,                        !- Part of Total Floor Area;

BuildingSurface:Detailed,
  Wall1,                   !- Name
  Wall,                    !- Surface Type
  WallConstruction,        !- Construction Name
  Zone1,                   !- Zone Name
  Outdoors,                !- Outside Boundary Condition
  ,                        !- Outside Boundary Condition Object
  SunExposed,              !- Sun Exposure
  WindExposed,             !- Wind Exposure
  0.5000000,               !- View Factor to Ground
  4,                       !- Number of Vertices
  0.0,0.0,3.0,             !- X,Y,Z Vertex 1
  0.0,0.0,0.0,             !- X,Y,Z Vertex 2
  10.0,0.0,0.0,            !- X,Y,Z Vertex 3
  10.0,0.0,3.0;            !- X,Y,Z Vertex 4

BuildingSurface:Detailed,
  Wall2,                   !- Name
  Wall,                    !- Surface Type
  WallConstruction,        !- Construction Name
  Zone1,                   !- Zone Name
  Outdoors,                !- Outside Boundary Condition
  ,                        !- Outside Boundary Condition Object
  SunExposed,              !- Sun Exposure
  WindExposed,             !- Wind Exposure
  0.5000000,               !- View Factor to Ground
  4,                       !- Number of Vertices
  10.0,0.0,3.0,            !- X,Y,Z Vertex 1
  10.0,0.0,0.0,            !- X,Y,Z Vertex 2
  10.0,10.0,0.0,           !- X,Y,Z Vertex 3
  10.0,10.0,3.0;           !- X,Y,Z Vertex 4

BuildingSurface:Detailed,
  Wall3,                   !- Name
  Wall,                    !- Surface Type
  WallConstruction,        !- Construction Name
  Zone1,                   !- Zone Name
  Outdoors,                !- Outside Boundary Condition
  ,                        !- Outside Boundary Condition Object
  SunExposed,              !- Sun Exposure
  WindExposed,             !- Wind Exposure
  0.5000000,               !- View Factor to Ground
  4,                       !- Number of Vertices
  10.0,10.0,3.0,           !- X,Y,Z Vertex 1
  10.0,10.0,0.0,           !- X,Y,Z Vertex 2
  0.0,10.0,0.0,            !- X,Y,Z Vertex 3
  0.0,10.0,3.0;            !- X,Y,Z Vertex 4

BuildingSurface:Detailed,
  Wall4,                   !- Name
  Wall,                    !- Surface Type
  WallConstruction,        !- Construction Name
  Zone1,                   !- Zone Name
  Outdoors,                !- Outside Boundary Condition
  ,                        !- Outside Boundary Condition Object
  SunExposed,              !- Sun Exposure
  WindExposed,             !- Wind Exposure
  0.5000000,               !- View Factor to Ground
  4,                       !- Number of Vertices
  0.0,10.0,3.0,            !- X,Y,Z Vertex 1
  0.0,10.0,0.0,            !- X,Y,Z Vertex 2
  0.0,0.0,0.0,             !- X,Y,Z Vertex 3
  0.0,0.0,3.0;             !- X,Y,Z Vertex 4

BuildingSurface:Detailed,
  Floor,                   !- Name
  Floor,                   !- Surface Type
  FloorConstruction,       !- Construction Name
  Zone1,                   !- Zone Name
  Ground,                  !- Outside Boundary Condition
  ,                        !- Outside Boundary Condition Object
  NoSun,                   !- Sun Exposure
  NoWind,                  !- Wind Exposure
  1.0,                     !- View Factor to Ground
  4,                       !- Number of Vertices
  0.0,0.0,0.0,             !- X,Y,Z Vertex 1
  10.0,0.0,0.0,            !- X,Y,Z Vertex 2
  10.0,10.0,0.0,           !- X,Y,Z Vertex 3
  0.0,10.0,0.0;            !- X,Y,Z Vertex 4

BuildingSurface:Detailed,
  Roof,                    !- Name
  Roof,                    !- Surface Type
  RoofConstruction,        !- Construction Name
  Zone1,                   !- Zone Name
  Outdoors,                !- Outside Boundary Condition
  ,                        !- Outside Boundary Condition Object
  SunExposed,              !- Sun Exposure
  WindExposed,             !- Wind Exposure
  0.0,                     !- View Factor to Ground
  4,                       !- Number of Vertices
  0.0,10.0,3.0,            !- X,Y,Z Vertex 1
  10.0,10.0,3.0,           !- X,Y,Z Vertex 2
  10.0,0.0,3.0,            !- X,Y,Z Vertex 3
  0.0,0.0,3.0;             !- X,Y,Z Vertex 4

Material:NoMass,
  WallConstruction,        !- Name
  MediumRough,             !- Roughness
  0.5;                     !- Thermal Resistance {m2-K/W}

Construction,
  WallConstruction,       !- Name
  WallConstruction;        !- Layer 1

Material:NoMass,
  FloorConstruction,       !- Name
  MediumRough,             !- Roughness
  0.5;                     !- Thermal Resistance {m2-K/W}

Construction,
  FloorConstruction,       !- Name
  FloorConstruction;       !- Layer 1

Material:NoMass,
  RoofConstruction,        !- Name
  MediumRough,             !- Roughness
  0.3;                     !- Thermal Resistance {m2-K/W}

Construction,
  RoofConstruction,        !- Name
  RoofConstruction;        !- Layer 1

ZoneHVAC:IdealLoadsAirSystem,
  Zone1 Ideal Loads,       !- Name
  ,                        !- Availability Schedule Name
  Zone1,                   !- Zone Name
  ,                        !- System Inlet Node Name
  ,                        !- System Exhaust Air Node Name
  ,                        !- Supply Air Fan Operating Mode Schedule Name
  0.0,                     !- Maximum Heating Supply Air Temperature {C}
  50.0,                    !- Minimum Cooling Supply Air Temperature {C}
  0.001,                   !- Maximum Heating Supply Air Humidity Ratio {kgWater/kgDryAir}
  0.015,                   !- Minimum Cooling Supply Air Humidity Ratio {kgWater/kgDryAir}
  NoLimit,                 !- Heating Limit
  autocalculate,           !- Maximum Sensible Heating Capacity {W}
  NoLimit,                 !- Cooling Limit
  autocalculate,           !- Maximum Total Cooling Capacity {W}
  ,                        !- Heating Availability Schedule Name
  ,                        !- Cooling Availability Schedule Name
  ConstantSupplyHumidityRatio,  !- Dehumidification Control Type
  ConstantSupplyHumidityRatio,  !- Humidification Control Type
  ,                        !- Design Specification Outdoor Air Object Name
  ,                        !- Outdoor Air Inlet Node Name
  ,                        !- Demand Controlled Ventilation Type
  ,                        !- Outdoor Air Economizer Type
  ,                        !- Heat Recovery Type
  ,                        !- Sensible Heat Recovery Effectiveness {dimensionless}
  ,                        !- Latent Heat Recovery Effectiveness {dimensionless};

Output:VariableDictionary,
  Regular;

Output:SQLite,
  SimpleAndTabular;

Output:Table:SummaryReports,
  AllSummary;

Output:Variable,
  *,                      !- Key Value
  Site Electricity Net Energy,  !- Variable Name
  RunPeriod;              !- Reporting Frequency

Output:Variable,
  *,                      !- Key Value
  Site Total Electricity Energy,  !- Variable Name
  RunPeriod;              !- Reporting Frequency

Output:Meter,
  Electricity:Facility,   !- Name
  RunPeriod;              !- Reporting Frequency

Site:GroundTemperature:BuildingSurface,
  20.0,                   !- January Ground Temperature {C}
  20.0,                   !- February Ground Temperature {C}
  20.0,                   !- March Ground Temperature {C}
  20.0,                   !- April Ground Temperature {C}
  20.0,                   !- May Ground Temperature {C}
  20.0,                   !- June Ground Temperature {C}
  20.0,                   !- July Ground Temperature {C}
  20.0,                   !- August Ground Temperature {C}
  20.0,                   !- September Ground Temperature {C}
  20.0,                   !- October Ground Temperature {C}
  20.0,                   !- November Ground Temperature {C}
  20.0;                   !- December Ground Temperature {C}
"""

# Load weather file
weather_file = Path('artifacts/desktop_files/weather/Chicago.epw')
if weather_file.exists():
    with open(weather_file, 'rb') as f:
        weather_content_b64 = base64.b64encode(f.read()).decode('utf-8')
    weather_filename = weather_file.name
else:
    print("Weather file not found, testing without weather file")
    weather_content_b64 = None
    weather_filename = None

# Prepare request
payload = {
    'idf_content': minimal_idf,
    'idf_filename': 'minimal_test.idf'
}

if weather_content_b64:
    payload['weather_content'] = weather_content_b64
    payload['weather_filename'] = weather_filename

print("Testing minimal IDF with API...")
print(f"IDF size: {len(minimal_idf)} characters")
print(f"Weather file: {weather_filename}")

response = requests.post(
    API_URL,
    json=payload,
    headers={'Content-Type': 'application/json'},
    timeout=300
)

print(f"\nStatus: {response.status_code}")
print(f"Response:\n{json.dumps(response.json(), indent=2)}")











