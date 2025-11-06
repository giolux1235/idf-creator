#!/usr/bin/env python3
"""
Script to test Railway EnergyPlus service and verify SQLite extraction is working.
"""

import sys
import requests
import json
import time
from pathlib import Path

# Railway service URL
RAILWAY_SERVICE_URL = "https://web-production-1d1be.up.railway.app/simulate"

def test_service_health():
    """Test if Railway service is responding"""
    print("=" * 80)
    print("TESTING RAILWAY ENERGYPLUS SERVICE")
    print("=" * 80)
    
    print(f"\n1. Checking service health...")
    print("-" * 80)
    
    try:
        # Try to get root endpoint
        root_url = RAILWAY_SERVICE_URL.replace('/simulate', '')
        response = requests.get(root_url, timeout=10)
        print(f"   Service URL: {root_url}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Service is responding")
        else:
            print(f"   ⚠️  Service returned status {response.status_code}")
    except requests.exceptions.SSLError as e:
        print(f"   ❌ SSL Error: {e}")
        print(f"   ⚠️  This might be a temporary connection issue")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection Error: {e}")
        print(f"   ⚠️  Service might be down or restarting")
        return False
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return False
    
    return True

def test_with_minimal_idf():
    """Test with a minimal IDF file"""
    print(f"\n2. Testing with minimal IDF...")
    print("-" * 80)
    
    # Create a minimal IDF that includes Output:SQLite
    minimal_idf = """Version,
    22.1;                    !- Version Identifier

Output:SQLite,
    SimpleAndTabular;        !- Option Type

Output:Meter,
    Electricity:Facility,                    !- Key Name
    RunPeriod;                               !- Reporting Frequency

Output:Meter,
    NaturalGas:Facility,                     !- Key Name
    RunPeriod;                               !- Reporting Frequency

Timestep,4;

RunPeriod,
    1,                       !- Begin Month
    1,                       !- Begin Day of Month
    12,                      !- End Month
    31,                      !- End Day of Month
    Tuesday,                 !- Day of Week for Start Day
    Yes,                     !- Use Weather File Holidays and Special Days
    Yes,                     !- Use Weather File Daylight Saving Period
    No,                      !- Apply Weekend Holiday Rule
    Yes,                     !- Use Weather File Rain Indicators
    Yes;                     !- Use Weather File Snow Indicators

Building,
    Test Building,           !- Name
    0.0,                     !- North Axis {deg}
    Suburbs,                 !- Terrain
    0.04,                     !- Loads Convergence Tolerance Value
    0.4,                     !- Temperature Convergence Tolerance Value {deltaC}
    FullInteriorAndExterior, !- Solar Distribution
    25,                      !- Maximum Number of Warmup Days
    6;                       !- Minimum Number of Warmup Days

Zone,
    Zone 1,                  !- Name
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
    Yes;                     !- Part of Total Floor Area

GlobalGeometryRules,
    UpperLeftCorner,         !- Starting Vertex Position
    CounterClockWise,       !- Vertex Entry Direction
    Relative;                !- Coordinate System

Site:Location,
    Chicago IL USA,          !- Name
    41.98,                   !- Latitude {deg}
    -87.92,                  !- Longitude {deg}
    -6.0,                    !- Time Zone {hr}
    190.0;                   !- Elevation {m}

Material,
    R13LAYER,                !- Name
    MediumRough,             !- Roughness
    0.1014984,               !- Thickness {m}
    0.09,                    !- Conductivity {W/m-K}
    513.0,                   !- Density {kg/m3}
    837.0;                   !- Specific Heat {J/kg-K}

Construction,
    ExtWall,                 !- Name
    R13LAYER;                !- Outside Layer

BuildingSurface:Detailed,
    Wall 1,                  !- Name
    Wall,                    !- Surface Type
    ExtWall,                 !- Construction Name
    Zone 1,                  !- Zone Name
    ,                        !- Space Name
    Outdoors,                !- Outside Boundary Condition
    ,                        !- Outside Boundary Condition Object
    SunExposed,              !- Sun Exposure
    WindExposed,             !- Wind Exposure
    0.5000000,               !- View Factor to Ground
    4,                       !- Number of Vertices
    0.0,0.0,3.0,             !- X,Y,Z ==> Vertex 1 {m}
    10.0,0.0,3.0,            !- X,Y,Z ==> Vertex 2 {m}
    10.0,0.0,0.0,            !- X,Y,Z ==> Vertex 3 {m}
    0.0,0.0,0.0;             !- X,Y,Z ==> Vertex 4 {m}

FenestrationSurface:Detailed,
    Window 1,                !- Name
    Window,                  !- Surface Type
    ,                        !- Construction Name
    Wall 1,                  !- Building Surface Name
    ,                        !- Outside Boundary Condition Object
    0.5000000,               !- View Factor to Ground
    ,                        !- Frame and Divider Name
    1,                       !- Multiplier
    4,                       !- Number of Vertices
    2.0,0.0,2.5,             !- X,Y,Z ==> Vertex 1 {m}
    8.0,0.0,2.5,             !- X,Y,Z ==> Vertex 2 {m}
    8.0,0.0,0.5,             !- X,Y,Z ==> Vertex 3 {m}
    2.0,0.0,0.5;             !- X,Y,Z ==> Vertex 4 {m}

ScheduleTypeLimits,
    Any Number;              !- Name

Schedule:Compact,
    Always On,               !- Name
    Any Number,              !- Schedule Type Limits Name
    Through: 12/31,          !- Field 1
    For: AllDays,             !- Field 2
    Until: 24:00,             !- Field 3
    1.0;                     !- Field 4

Lights,
    Zone 1 Lights,           !- Name
    Zone 1,                  !- Zone or ZoneList Name
    Always On,               !- Schedule Name
    Watts/Area,              !- Design Level Calculation Method
    ,                        !- Lighting Level {W}
    ,                        !- Watts per Zone Floor Area {W/m2}
    10.0,                    !- Watts per Person {W/person}
    ,                        !- Return Air Fraction
    ,                        !- Fraction Radiant
    ,                        !- Fraction Visible
    ,                        !- Fraction Replaceable
    GeneralLights;           !- End-Use Subcategory

ElectricEquipment,
    Zone 1 Equipment,        !- Name
    Zone 1,                  !- Zone or ZoneList Name
    Always On,               !- Schedule Name
    Watts/Area,              !- Design Level Calculation Method
    ,                        !- Design Level {W}
    ,                        !- Watts per Zone Floor Area {W/m2}
    ,                        !- Watts per Person {W/person}
    ,                        !- Fraction Latent
    ,                        !- Fraction Radiant
    ,                        !- Fraction Lost
    General;                 !- End-Use Subcategory

People,
    Zone 1 People,           !- Name
    Zone 1,                  !- Zone or ZoneList Name
    Always On,               !- Number of People Schedule Name
    people,                  !- Number of People Calculation Method
    ,                        !- Number of People
    ,                        !- People per Zone Floor Area {person/m2}
    0.1,                     !- Zone Floor Area per Person {m2/person}
    ,                        !- Fraction Radiant
    ,                        !- Sensible Heat Fraction
    Office Occupancy;        !- Activity Level Schedule Name
"""
    
    print("   Sending minimal IDF to Railway service...")
    
    payload = {
        'idf_content': minimal_idf,
        'idf_filename': 'test_minimal.idf'
    }
    
    try:
        response = requests.post(
            RAILWAY_SERVICE_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n3. Analyzing Results...")
            print("-" * 80)
            
            sim_status = result.get('simulation_status', 'unknown')
            print(f"   Simulation Status: {sim_status}")
            
            if sim_status == 'success':
                energy_results = result.get('energy_results', {})
                
                if energy_results:
                    extraction_method = energy_results.get('extraction_method', 'unknown')
                    total_energy = energy_results.get('total_site_energy_kwh', 0)
                    eui = energy_results.get('eui_kwh_m2', 0)
                    
                    print(f"\n   ✅ Energy Results Found!")
                    print(f"   Extraction Method: {extraction_method}")
                    print(f"   Total Energy: {total_energy:,.2f} kWh")
                    print(f"   EUI: {eui:.2f} kWh/m²")
                    
                    if extraction_method == 'sqlite':
                        print(f"\n   ✅ SUCCESS: SQLite extraction is working!")
                    elif extraction_method == 'standard':
                        print(f"\n   ⚠️  Using standard extraction (not SQLite)")
                        print(f"      This may indicate SQLite extraction is not being used")
                    else:
                        print(f"\n   ⚠️  Extraction method not specified")
                    
                    # Check if values are reasonable
                    if total_energy > 0 and total_energy < 1000:
                        print(f"\n   ⚠️  Energy value seems low for a building ({total_energy:,.0f} kWh)")
                        print(f"      This might indicate incomplete extraction")
                    elif total_energy > 0:
                        print(f"\n   ✅ Energy value looks reasonable")
                else:
                    print(f"\n   ❌ No energy_results in response")
                    print(f"   Available keys: {list(result.keys())}")
            else:
                error_msg = result.get('error_message', 'Unknown error')
                print(f"\n   ❌ Simulation failed: {error_msg}")
                
        else:
            print(f"   ❌ API returned status {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            
    except requests.exceptions.SSLError as e:
        print(f"   ❌ SSL Error: {e}")
        print(f"\n   💡 TIP: The Railway service might be restarting.")
        print(f"      Wait a few minutes and try again.")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Main function"""
    print("\n" + "=" * 80)
    print("RAILWAY SERVICE TEST")
    print("=" * 80)
    print("\nThis script tests the Railway EnergyPlus service to verify:")
    print("1. Service is responding")
    print("2. SQLite extraction is working")
    print("3. Energy results are being returned")
    print("\n" + "=" * 80)
    
    # Test service health
    if not test_service_health():
        print("\n⚠️  Service health check failed. Service might be down or restarting.")
        print("   If you just pushed code, wait 2-5 minutes for Railway to deploy.")
        return
    
    # Test with minimal IDF
    test_with_minimal_idf()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nNext Steps:")
    print("1. If SQLite extraction is not working, check Railway logs")
    print("2. Verify the latest code is deployed to Railway")
    print("3. Check that Output:SQLite is in IDF files being sent")
    print("4. Verify SQLite extraction code is using MAX() for RunPeriod meters")
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()

