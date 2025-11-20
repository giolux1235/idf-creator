#!/usr/bin/env python3
"""
Test IDF Creator with real buildings that have known energy data.
Compare simulation results to actual building energy consumption.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess
import json
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import IDFCreator
from src.validation.simulation_validator import EnergyPlusSimulationValidator

# Known buildings with published energy data
# Sources: ENERGY STAR Portfolio Manager, public reports, academic studies
KNOWN_BUILDINGS = [
    {
        'name': 'Willis Tower (Sears Tower)',
        'address': '233 S Wacker Dr, Chicago, IL 60606',
        'city': 'Chicago',
        'weather_file': 'artifacts/desktop_files/weather/Chicago.epw',
        'building_type': 'Office',
        'stories': 110,
        'floor_area_total_m2': 416000,  # 4.5M sq ft
        'year_built': 1974,
        'known_data': {
            'eui_kwh_m2': 155,  # From ENERGY STAR
            'eui_kbtu_ft2': 48.9,  # Converted
            'source': 'ENERGY STAR Portfolio Manager (public data)',
            'notes': 'One of the largest office buildings in the world'
        }
    },
    {
        'name': 'Empire State Building',
        'address': '350 5th Ave, New York, NY 10118',
        'city': 'New York',
        'weather_file': 'artifacts/desktop_files/weather/artifacts/desktop_files/weather/USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw',  # Use existing
        'building_type': 'Office',
        'stories': 102,
        'floor_area_total_m2': 208000,  # 2.2M sq ft
        'year_built': 1931,
        'retrofit_year': 2011,
        'known_data': {
            'eui_kwh_m2': 180,  # Pre-retrofit baseline
            'eui_kbtu_ft2': 57.0,
            'source': 'Empire State Building Retrofit Report (2011)',
            'notes': 'Major retrofit in 2011 reduced EUI by 38%'
        }
    },
    {
        'name': 'John Hancock Center',
        'address': '875 N Michigan Ave, Chicago, IL 60611',
        'city': 'Chicago',
        'weather_file': 'artifacts/desktop_files/weather/Chicago.epw',
        'building_type': 'Office',
        'stories': 100,
        'floor_area_total_m2': 260000,  # 2.8M sq ft
        'year_built': 1969,
        'known_data': {
            'eui_kwh_m2': 165,
            'eui_kbtu_ft2': 52.2,
            'source': 'ENERGY STAR Portfolio Manager',
            'notes': 'Mixed-use: office and residential'
        }
    },
    {
        'name': 'Transamerica Pyramid',
        'address': '600 Montgomery St, San Francisco, CA 94111',
        'city': 'San Francisco',
        'weather_file': 'artifacts/desktop_files/weather/artifacts/desktop_files/weather/USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw',  # Use existing
        'building_type': 'Office',
        'stories': 48,
        'floor_area_total_m2': 56000,  # 600K sq ft
        'year_built': 1972,
        'known_data': {
            'eui_kwh_m2': 140,
            'eui_kbtu_ft2': 44.3,
            'source': 'San Francisco Building Benchmarking',
            'notes': 'Distinctive pyramid shape'
        }
    },
    {
        'name': 'Bank of America Tower (Seattle)',
        'address': '800 5th Ave, Seattle, WA 98104',
        'city': 'Seattle',
        'weather_file': 'artifacts/desktop_files/weather/USA_WA_Seattle-Tacoma.Intl.AP.727930_TMY3.epw',
        'building_type': 'Office',
        'stories': 44,
        'floor_area_total_m2': 125000,  # 1.35M sq ft
        'year_built': 1985,
        'known_data': {
            'eui_kwh_m2': 120,
            'eui_kbtu_ft2': 38.0,
            'source': 'Seattle Building Benchmarking',
            'notes': 'LEED Gold certified'
        }
    },
    {
        'name': 'Prudential Tower (Boston)',
        'address': '800 Boylston St, Boston, MA 02199',
        'city': 'Boston',
        'weather_file': 'artifacts/desktop_files/weather/USA_MA_Boston-Logan.Intl.AP.725090_TMY3.epw',
        'building_type': 'Office',
        'stories': 52,
        'floor_area_total_m2': 93000,  # 1M sq ft
        'year_built': 1965,
        'known_data': {
            'eui_kwh_m2': 185,
            'eui_kbtu_ft2': 58.5,
            'source': 'Boston Building Benchmarking',
            'notes': 'Historic building, less efficient'
        }
    }
]

def find_energyplus() -> Optional[str]:
    """Find EnergyPlus installation"""
    # Try common locations
    possible_paths = [
        '/Applications/EnergyPlus-9-6-0/energyplus',
        '/Applications/EnergyPlus-9-5-0/energyplus',
        '/usr/local/bin/energyplus',
        'energyplus'  # If in PATH
    ]
    
    for path in possible_paths:
        if os.path.exists(path) or path == 'energyplus':
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, 
                                      timeout=5)
                if result.returncode == 0:
                    return path
            except:
                pass
    
    return None

def extract_energy_from_sqlite(sqlite_path: str) -> Optional[Dict]:
    """Extract annual energy consumption from EnergyPlus SQLite output"""
    try:
        import sqlite3
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        # Get total electricity consumption
        cursor.execute("""
            SELECT SUM(Value) 
            FROM ReportData 
            WHERE ReportDataDictionaryIndex IN (
                SELECT ReportDataDictionaryIndex 
                FROM ReportDataDictionary 
                WHERE Name LIKE '%Electricity%' 
                AND ReportingFrequency = 'RunPeriod'
            )
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return {'annual_kwh': result[0]}
    except Exception as e:
        print(f"  ⚠️  SQLite extraction error: {e}")
    
    return None

def extract_energy_from_tabular(tabular_path: str) -> Optional[Dict]:
    """Extract annual energy consumption from EnergyPlus tabular output"""
    try:
        with open(tabular_path, 'r') as f:
            content = f.read()
        
        # Look for annual electricity consumption
        # Pattern: "Electricity:Facility" or similar
        patterns = [
            r'Electricity:Facility\s+[\d.]+\s+([\d.]+)',
            r'Total Electricity\s+[\d.]+\s+([\d.]+)',
            r'Annual Electricity\s+([\d.]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return {'annual_kwh': float(match.group(1))}
    except Exception as e:
        print(f"  ⚠️  Tabular extraction error: {e}")
    
    return None

def run_simulation(idf_path: str, weather_file: str, output_dir: str) -> Optional[Dict]:
    """Run EnergyPlus simulation and extract results"""
    energyplus_path = find_energyplus()
    
    if not energyplus_path:
        print("  ⚠️  EnergyPlus not found. Skipping simulation.")
        print("     Install EnergyPlus or add to PATH to run simulations.")
        return None
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"  🔄 Running EnergyPlus simulation...")
    print(f"     IDF: {idf_path}")
    print(f"     Weather: {weather_file}")
    
    try:
        # Run EnergyPlus
        cmd = [
            energyplus_path,
            '-w', str(Path(weather_file).absolute()),
            '-d', str(output_path.absolute()),
            str(Path(idf_path).absolute())
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes
        )
        
        if result.returncode != 0:
            print(f"  ⚠️  Simulation errors (check {output_path}/eplusout.err)")
            # Still try to extract results if available
        
        # Try to extract results
        sqlite_file = output_path / "eplusout.sql"
        if sqlite_file.exists():
            energy_data = extract_energy_from_sqlite(str(sqlite_file))
            if energy_data:
                return energy_data
        
        tabular_file = output_path / "eplusout.tab"
        if tabular_file.exists():
            energy_data = extract_energy_from_tabular(str(tabular_file))
            if energy_data:
                return energy_data
        
        # Try parsing eplusout.err for summary
        err_file = output_path / "eplusout.err"
        if err_file.exists():
            with open(err_file, 'r') as f:
                err_content = f.read()
                if 'Fatal' in err_content or 'Severe' in err_content:
                    print(f"  ❌ Simulation failed - check errors")
                else:
                    print(f"  ⚠️  Simulation completed but couldn't extract energy data")
        
        return None
        
    except subprocess.TimeoutExpired:
        print(f"  ⚠️  Simulation timed out (>30 minutes)")
        return None
    except Exception as e:
        print(f"  ❌ Simulation error: {e}")
        return None

def calculate_eui(annual_kwh: float, floor_area_m2: float) -> float:
    """Calculate Energy Use Intensity (EUI) in kWh/m²"""
    if floor_area_m2 > 0:
        return annual_kwh / floor_area_m2
    return 0.0

def test_building(building: Dict) -> Dict:
    """Test a single building"""
    print(f"\n{'='*70}")
    print(f"Testing: {building['name']}")
    print(f"{'='*70}")
    print(f"Address: {building['address']}")
    print(f"Known EUI: {building['known_data']['eui_kwh_m2']} kWh/m²")
    print(f"Source: {building['known_data']['source']}")
    
    # Create IDF
    creator = IDFCreator(professional=True)
    
    # Calculate floor area per story
    floor_area_per_story = building['floor_area_total_m2'] / building['stories']
    
    user_params = {
        'building_type': building['building_type'],
        'stories': building['stories'],
        'floor_area_per_story_m2': floor_area_per_story,
        'year_built': building.get('year_built'),
        'retrofit_year': building.get('retrofit_year')
    }
    
    output_filename = f"real_{building['name'].lower().replace(' ', '_').replace('(', '').replace(')', '')}.idf"
    output_path = Path("artifacts/desktop_files/idf") / output_filename
    
    try:
        print(f"\n📝 Generating IDF...")
        idf_path = creator.create_idf(
            address=building['address'],
            user_params=user_params,
            output_path=str(output_path)
        )
        
        print(f"✅ IDF generated: {idf_path}")
        
        # Run simulation if weather file exists
        weather_file = building.get('weather_file')
        
        # Try alternative paths if primary doesn't exist
        if weather_file and not Path(weather_file).exists():
            # Try without nested path
            alt_path = weather_file.replace('artifacts/desktop_files/weather/artifacts/desktop_files/weather/', 'artifacts/desktop_files/weather/')
            if Path(alt_path).exists():
                weather_file = alt_path
            # Try just filename in weather directory
            elif Path(f"artifacts/desktop_files/weather/{Path(weather_file).name}").exists():
                weather_file = f"artifacts/desktop_files/weather/{Path(weather_file).name}"
        
        if weather_file and Path(weather_file).exists():
            print(f"\n🌤️  Weather file found: {weather_file}")
            sim_output_dir = Path("artifacts/desktop_files/simulations") / Path(output_filename).stem
            
            energy_data = run_simulation(idf_path, weather_file, str(sim_output_dir))
            
            if energy_data:
                annual_kwh = energy_data.get('annual_kwh', 0)
                simulated_eui = calculate_eui(annual_kwh, building['floor_area_total_m2'])
                known_eui = building['known_data']['eui_kwh_m2']
                
                error_pct = abs(simulated_eui - known_eui) / known_eui * 100 if known_eui > 0 else 0
                
                print(f"\n📊 SIMULATION RESULTS:")
                print(f"   Annual Energy: {annual_kwh:,.0f} kWh")
                print(f"   Simulated EUI: {simulated_eui:.1f} kWh/m²")
                print(f"   Known EUI: {known_eui:.1f} kWh/m²")
                print(f"   Error: {error_pct:.1f}%")
                
                if error_pct < 20:
                    print(f"   ✅ Good match (within 20%)")
                elif error_pct < 40:
                    print(f"   ⚠️  Moderate match (within 40%)")
                else:
                    print(f"   ❌ Poor match (>40% error)")
                
                return {
                    'name': building['name'],
                    'success': True,
                    'idf_path': idf_path,
                    'simulated_eui': simulated_eui,
                    'known_eui': known_eui,
                    'error_pct': error_pct,
                    'annual_kwh': annual_kwh
                }
            else:
                print(f"\n⚠️  Simulation completed but couldn't extract energy data")
                return {
                    'name': building['name'],
                    'success': True,
                    'idf_path': idf_path,
                    'simulated_eui': None,
                    'known_eui': building['known_data']['eui_kwh_m2'],
                    'error_pct': None,
                    'simulation_error': 'Could not extract energy data'
                }
        else:
            print(f"\n⚠️  Weather file not found: {weather_file}")
            print(f"   Skipping simulation. IDF file generated.")
            return {
                'name': building['name'],
                'success': True,
                'idf_path': idf_path,
                'simulated_eui': None,
                'known_eui': building['known_data']['eui_kwh_m2'],
                'error_pct': None,
                'simulation_error': 'Weather file not found'
            }
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'name': building['name'],
            'success': False,
            'error': str(e)
        }

def main():
    """Run all tests"""
    print("="*70)
    print("REAL BUILDING ENERGY VALIDATION TEST")
    print("="*70)
    print("\nComparing IDF Creator simulations to known building energy data")
    print("Sources: ENERGY STAR, public benchmarking data, retrofit reports")
    
    # Ensure directories exist
    Path("artifacts/desktop_files/idf").mkdir(parents=True, exist_ok=True)
    Path("artifacts/desktop_files/simulations").mkdir(parents=True, exist_ok=True)
    
    results = []
    for building in KNOWN_BUILDINGS:
        result = test_building(building)
        results.append(result)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    successful = [r for r in results if r.get('success')]
    simulated = [r for r in successful if r.get('simulated_eui') is not None]
    
    print(f"\n✅ Successful IDF Generation: {len(successful)}/{len(results)}")
    print(f"🔄 Simulations Completed: {len(simulated)}/{len(successful)}")
    
    if simulated:
        print(f"\n📊 ACCURACY ANALYSIS:")
        print(f"{'Building':<30} {'Known EUI':<12} {'Simulated EUI':<15} {'Error':<10}")
        print("-" * 70)
        
        good_matches = 0
        moderate_matches = 0
        poor_matches = 0
        
        for r in simulated:
            if r['error_pct'] is not None:
                error_pct = r['error_pct']
                status = ""
                if error_pct < 20:
                    status = "✅"
                    good_matches += 1
                elif error_pct < 40:
                    status = "⚠️"
                    moderate_matches += 1
                else:
                    status = "❌"
                    poor_matches += 1
                
                print(f"{r['name'][:29]:<30} {r['known_eui']:>10.1f} {r['simulated_eui']:>14.1f} {error_pct:>9.1f}% {status}")
        
        print(f"\nMatch Quality:")
        print(f"  ✅ Good (<20% error): {good_matches}/{len(simulated)}")
        print(f"  ⚠️  Moderate (20-40% error): {moderate_matches}/{len(simulated)}")
        print(f"  ❌ Poor (>40% error): {poor_matches}/{len(simulated)}")
    
    # Save results
    results_file = Path("artifacts/desktop_files/real_building_test_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")
    print("\n" + "="*70)

if __name__ == "__main__":
    main()

