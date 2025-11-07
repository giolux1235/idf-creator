#!/usr/bin/env python3
"""
Analyze EnergyPlus output format to understand why results aren't being extracted
"""

import requests
import json
import base64
import re
from pathlib import Path

IDF_API_BASE = "https://web-production-3092c.up.railway.app"
ENERGYPLUS_API_BASE = "https://web-production-1d1be.up.railway.app"

def test_minimal_idf_with_weather():
    """Test with a minimal but complete IDF to see actual output format"""
    
    # Minimal valid IDF with all required objects
    minimal_idf = """Version,
  25.1;

Building,
  Test Building,
  0.0,
  City,
  0.04,
  0.4,
  FullExterior,
  25,
  6;

GlobalGeometryRules,
  UpperLeftCorner,
  CounterClockWise,
  Relative;

SimulationControl,
  No,
  No,
  No,
  No,
  Yes;

RunPeriod,
  Annual,
  1, 1, 2024,
  12, 31, 2024,
  ,
  Yes,
  Yes,
  No,
  Yes,
  Yes;

Timestep, 6;

Site:Location,
  Chicago,
  41.8787,
  -87.6360,
  -6.0,
  181.0;

Material:NoMass,
  R13LAYER,
  Rough,
  2.290;

Material,
  C5 - 4 IN HW CONCRETE,
  MediumRough,
  0.1016,
  1.729577,
  2242.4,
  836.8,
  0.9,
  0.65,
  0.65;

Construction,
  R13WALL,
  R13LAYER,
  C5 - 4 IN HW CONCRETE;

Zone,
  Zone1,
  0.0,
  0.0,
  0.0,
  0.0,
  1,
  1;

BuildingSurface:Detailed,
  Wall1,
  Wall,
  R13WALL,
  Zone1,
  OutsideBoundaryCondition,
  0.0,
  NoSun,
  NoWind,
  0.5000,
  4,
  0.0, 0.0, 0.0,
  10.0, 0.0, 0.0,
  10.0, 0.0, 3.0,
  0.0, 0.0, 3.0;

BuildingSurface:Detailed,
  Wall2,
  Wall,
  R13WALL,
  Zone1,
  OutsideBoundaryCondition,
  180.0,
  NoSun,
  NoWind,
  0.5000,
  4,
  0.0, 10.0, 0.0,
  0.0, 10.0, 3.0,
  0.0, 10.0, 0.0,
  0.0, 0.0, 0.0;

BuildingSurface:Detailed,
  Wall3,
  Wall,
  R13WALL,
  Zone1,
  OutsideBoundaryCondition,
  90.0,
  NoSun,
  NoWind,
  0.5000,
  4,
  10.0, 10.0, 0.0,
  10.0, 10.0, 3.0,
  10.0, 0.0, 3.0,
  10.0, 0.0, 0.0;

BuildingSurface:Detailed,
  Wall4,
  Wall,
  R13WALL,
  Zone1,
  OutsideBoundaryCondition,
  270.0,
  NoSun,
  NoWind,
  0.5000,
  4,
  0.0, 10.0, 3.0,
  0.0, 10.0, 0.0,
  0.0, 0.0, 0.0,
  0.0, 0.0, 3.0;

BuildingSurface:Detailed,
  Floor,
  Floor,
  R13WALL,
  Zone1,
  Ground,
  0.0,
  NoSun,
  NoWind,
  0.0,
  4,
  0.0, 0.0, 0.0,
  10.0, 0.0, 0.0,
  10.0, 10.0, 0.0,
  0.0, 10.0, 0.0;

BuildingSurface:Detailed,
  Roof,
  Roof,
  R13WALL,
  Zone1,
  OutsideBoundaryCondition,
  0.0,
  NoSun,
  NoWind,
  0.0,
  4,
  0.0, 0.0, 3.0,
  10.0, 0.0, 3.0,
  10.0, 10.0, 3.0,
  0.0, 10.0, 3.0;

Schedule:Constant,
  Always On,
  Any Number,
  1.0;

ZoneControl:Thermostat,
  Zone1 Thermostat,
  Zone1,
  Single Cooling Setpoint,
  Thermostat Setpoint;

ThermostatSetpoint:DualSetpoint,
  Thermostat Setpoint,
  ,
  26.7;

Output:VariableDictionary,
  Regular;

Output:SQLite,
  SimpleAndTabular;

Output:Table:SummaryReports,
  AnnualBuildingUtilityPerformanceSummary,
  AllSummary;

Output:Variable,
  *,
  Site Total Electricity Energy,
  RunPeriod;

Output:Meter,
  Electricity:Facility,
  RunPeriod;
"""

    # Load weather file
    weather_dir = Path('artifacts/desktop_files/weather')
    weather_file = weather_dir / 'Chicago.epw'
    
    if not weather_file.exists():
        print(f"Error: Weather file not found: {weather_file}")
        return
    
    with open(weather_file, 'rb') as f:
        weather_bytes = f.read()
        weather_b64 = base64.b64encode(weather_bytes).decode('utf-8')
    
    print("="*70)
    print("Testing Minimal IDF with Weather File")
    print("="*70)
    print(f"\nIDF Size: {len(minimal_idf):,} characters")
    print(f"Weather File: {weather_file.name} ({len(weather_bytes):,} bytes)")
    print(f"\nSending to: {ENERGYPLUS_API_BASE}/simulate\n")
    
    payload = {
        'idf_content': minimal_idf,
        'idf_filename': 'minimal_test.idf',
        'weather_content': weather_b64,
        'weather_filename': 'Chicago.epw'
    }
    
    response = requests.post(
        f"{ENERGYPLUS_API_BASE}/simulate",
        json=payload,
        headers={'Content-Type': 'application/json'},
        timeout=600
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    
    print("\n" + "="*70)
    print("RESPONSE ANALYSIS")
    print("="*70)
    
    print(f"\nSimulation Status: {data.get('simulation_status')}")
    print(f"EnergyPlus Version: {data.get('energyplus_version')}")
    print(f"Real Simulation: {data.get('real_simulation')}")
    
    if data.get('simulation_status') == 'success':
        print("\n✅ Simulation Successful!")
        energy_results = data.get('energy_results', {})
        if energy_results:
            print("\nEnergy Results:")
            for key, value in energy_results.items():
                print(f"  {key}: {value}")
        else:
            print("\n⚠️ No energy results in response")
    else:
        print(f"\n❌ Simulation Failed")
        print(f"Error: {data.get('error_message', 'Unknown error')}")
        
        # Check for warnings
        warnings = data.get('warnings', [])
        if warnings:
            print(f"\nWarnings ({len(warnings)}):")
            for i, warning in enumerate(warnings[:10], 1):
                print(f"  {i}. {warning[:200]}")
        
        # Check for debug info
        debug_info = data.get('debug_info', {})
        if debug_info:
            print(f"\nDebug Info:")
            for key, value in debug_info.items():
                print(f"  {key}: {value}")
    
    # Save full response
    with open('minimal_test_response.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n\nFull response saved to: minimal_test_response.json")
    print("="*70)

if __name__ == '__main__':
    test_minimal_idf_with_weather()










