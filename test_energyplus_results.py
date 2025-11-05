#!/usr/bin/env python3
"""
Test script to run EnergyPlus simulations and extract results.
This script creates a couple of test buildings, runs simulations,
and shows what results we get from EnergyPlus.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Optional
import subprocess
import sqlite3
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import IDFCreator

def find_energyplus() -> Optional[str]:
    """Find EnergyPlus installation"""
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

def extract_results_from_csv(csv_path: str) -> Dict:
    """Extract energy results from CSV tabular output"""
    results = {}
    
    try:
        with open(csv_path, 'r') as f:
            content = f.read()
        
        # Extract total site energy (GJ)
        import re
        site_energy_match = re.search(r'Total Site Energy,([\d.]+)', content)
        if site_energy_match:
            site_energy_gj = float(site_energy_match.group(1))
            results['total_site_energy_gj'] = site_energy_gj
            results['total_site_energy_kwh'] = site_energy_gj * 277.778  # Convert GJ to kWh
        
        # Extract source energy
        source_energy_match = re.search(r'Total Source Energy,([\d.]+)', content)
        if source_energy_match:
            source_energy_gj = float(source_energy_match.group(1))
            results['total_source_energy_gj'] = source_energy_gj
            results['total_source_energy_kwh'] = source_energy_gj * 277.778
        
        # Extract building area
        area_match = re.search(r'Total Building Area,([\d.]+)', content)
        if area_match:
            results['building_area_m2'] = float(area_match.group(1))
        
        # Extract end uses
        end_uses = {}
        for end_use in ['Heating', 'Cooling', 'Interior Lighting', 'Interior Equipment', 'Fans', 'Pumps']:
            pattern = rf',{re.escape(end_use)},([\d.]+),([\d.]+)'
            match = re.search(pattern, content)
            if match:
                elec_gj = float(match.group(1))
                gas_gj = float(match.group(2))
                if elec_gj > 0 or gas_gj > 0:
                    end_uses[end_use] = {
                        'electricity_gj': elec_gj,
                        'electricity_kwh': elec_gj * 277.778,
                        'natural_gas_gj': gas_gj,
                        'natural_gas_kwh': gas_gj * 277.778
                    }
        
        results['end_uses'] = end_uses
        
        # Calculate EUI if we have area and energy
        if 'total_site_energy_kwh' in results and 'building_area_m2' in results:
            results['eui_kwh_m2'] = results['total_site_energy_kwh'] / results['building_area_m2']
        
    except Exception as e:
        results['error'] = str(e)
    
    return results

def extract_results_from_sqlite(sqlite_path: str) -> Dict:
    """Extract energy results from SQLite output"""
    results = {}
    
    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        # Get annual electricity consumption from ReportMeterData
        cursor.execute("""
            SELECT 
                m.Name,
                SUM(d.Value) as Total
            FROM ReportMeterData d
            JOIN ReportMeterDictionary m ON d.ReportMeterDictionaryIndex = m.ReportMeterDictionaryIndex
            WHERE m.ReportingFrequency = 'RunPeriod'
            AND m.Name LIKE '%Electricity%'
            GROUP BY m.Name
            ORDER BY Total DESC
        """)
        
        electricity_data = cursor.fetchall()
        if electricity_data:
            results['electricity_meters'] = {}
            for name, total in electricity_data:
                results['electricity_meters'][name] = total
        
        # Get total facility electricity
        cursor.execute("""
            SELECT SUM(Value)
            FROM ReportMeterData
            WHERE ReportMeterDictionaryIndex IN (
                SELECT ReportMeterDictionaryIndex
                FROM ReportMeterDictionary
                WHERE Name = 'Electricity:Facility'
                AND ReportingFrequency = 'RunPeriod'
            )
        """)
        
        facility_elec = cursor.fetchone()
        if facility_elec and facility_elec[0]:
            results['total_electricity_kwh'] = facility_elec[0]
        
        # Get natural gas
        cursor.execute("""
            SELECT SUM(Value)
            FROM ReportMeterData
            WHERE ReportMeterDictionaryIndex IN (
                SELECT ReportMeterDictionaryIndex
                FROM ReportMeterDictionary
                WHERE Name = 'NaturalGas:Facility'
                AND ReportingFrequency = 'RunPeriod'
            )
        """)
        
        facility_gas = cursor.fetchone()
        if facility_gas and facility_gas[0]:
            results['total_natural_gas_kwh'] = facility_gas[0]
        
        # Get building area if available
        cursor.execute("""
            SELECT Value
            FROM ReportData
            WHERE ReportDataDictionaryIndex IN (
                SELECT ReportDataDictionaryIndex
                FROM ReportDataDictionary
                WHERE Name LIKE '%Building Area%'
                AND ReportingFrequency = 'RunPeriod'
            )
            LIMIT 1
        """)
        
        area_result = cursor.fetchone()
        if area_result and area_result[0]:
            results['building_area_m2'] = area_result[0]
        
        conn.close()
        
    except Exception as e:
        results['error'] = str(e)
    
    return results

def run_simulation(idf_path: str, weather_file: Optional[str], output_dir: str) -> Dict:
    """Run EnergyPlus simulation and extract results"""
    energyplus_path = find_energyplus()
    
    if not energyplus_path:
        return {'error': 'EnergyPlus not found'}
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"  🔄 Running EnergyPlus simulation...")
    
    try:
        cmd = [energyplus_path]
        
        if weather_file and Path(weather_file).exists():
            cmd.extend(['-w', str(Path(weather_file).absolute())])
        
        cmd.extend(['-d', str(output_path.absolute())])
        cmd.append(str(Path(idf_path).absolute()))
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes
        )
        
        # Check if simulation completed
        err_file = output_path / "eplusout.err"
        if err_file.exists():
            with open(err_file, 'r') as f:
                err_content = f.read()
                if 'EnergyPlus Completed Successfully' in err_content:
                    print(f"  ✅ Simulation completed successfully")
                else:
                    print(f"  ⚠️  Simulation completed with warnings/errors")
        
        # Extract results from CSV
        csv_file = output_path / "eplustbl.csv"
        csv_results = {}
        if csv_file.exists():
            csv_results = extract_results_from_csv(str(csv_file))
        
        # Extract results from SQLite
        sqlite_file = output_path / "eplusout.sql"
        sqlite_results = {}
        if sqlite_file.exists():
            sqlite_results = extract_results_from_sqlite(str(sqlite_file))
        
        # Combine results
        combined_results = {
            'csv': csv_results,
            'sqlite': sqlite_results,
            'output_directory': str(output_path)
        }
        
        return combined_results
        
    except subprocess.TimeoutExpired:
        return {'error': 'Simulation timed out'}
    except Exception as e:
        return {'error': str(e)}

def test_building(name: str, address: str, params: Dict) -> Dict:
    """Test a single building"""
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"Address: {address}")
    print(f"{'='*70}")
    
    try:
        # Create IDF
        creator = IDFCreator(professional=True, enhanced=True)
        output_filename = f"test_{name.lower().replace(' ', '_')}.idf"
        output_path = Path("test_outputs") / output_filename
        
        print(f"\n📝 Generating IDF...")
        idf_path = creator.create_idf(
            address=address,
            user_params=params,
            output_path=str(output_path)
        )
        
        print(f"✅ IDF generated: {idf_path}")
        
        # Find weather file
        weather_file = None
        # Try to find weather file based on location
        city = params.get('city', 'Chicago')
        weather_paths = [
            f"artifacts/desktop_files/weather/{city}.epw",
            f"artifacts/desktop_files/weather/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw",
            f"artifacts/desktop_files/weather/USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw",
        ]
        
        for wp in weather_paths:
            if Path(wp).exists():
                weather_file = wp
                break
        
        if weather_file:
            print(f"🌤️  Using weather file: {weather_file}")
        else:
            print(f"⚠️  No weather file found, using EnergyPlus default")
        
        # Run simulation
        sim_output_dir = Path("test_outputs") / f"sim_{name.lower().replace(' ', '_')}"
        results = run_simulation(idf_path, weather_file, str(sim_output_dir))
        
        return {
            'name': name,
            'idf_path': idf_path,
            'weather_file': weather_file,
            'simulation_results': results
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'name': name,
            'error': str(e)
        }

def print_results_summary(test_results: Dict):
    """Print a summary of simulation results"""
    print(f"\n{'='*70}")
    print("ENERGYPLUS RESULTS SUMMARY")
    print(f"{'='*70}")
    
    if 'error' in test_results:
        print(f"\n❌ Error: {test_results['error']}")
        return
    
    sim_results = test_results.get('simulation_results', {})
    
    if 'error' in sim_results:
        print(f"\n❌ Simulation error: {sim_results['error']}")
        return
    
    # CSV results
    csv_results = sim_results.get('csv', {})
    if csv_results and 'error' not in csv_results:
        print(f"\n📊 RESULTS FROM CSV TABULAR OUTPUT:")
        print(f"  Building Area: {csv_results.get('building_area_m2', 'N/A'):.2f} m²")
        
        if 'total_site_energy_kwh' in csv_results:
            print(f"  Total Site Energy: {csv_results['total_site_energy_kwh']:,.2f} kWh")
            print(f"  Total Site Energy: {csv_results.get('total_site_energy_gj', 0):.2f} GJ")
        
        if 'total_source_energy_kwh' in csv_results:
            print(f"  Total Source Energy: {csv_results['total_source_energy_kwh']:,.2f} kWh")
        
        if 'eui_kwh_m2' in csv_results:
            print(f"  EUI (Energy Use Intensity): {csv_results['eui_kwh_m2']:.2f} kWh/m²")
        
        end_uses = csv_results.get('end_uses', {})
        if end_uses:
            print(f"\n  End Uses:")
            for end_use, data in end_uses.items():
                if data.get('electricity_kwh', 0) > 0:
                    print(f"    {end_use}:")
                    print(f"      Electricity: {data['electricity_kwh']:,.2f} kWh")
                if data.get('natural_gas_kwh', 0) > 0:
                    print(f"      Natural Gas: {data['natural_gas_kwh']:,.2f} kWh")
    
    # SQLite results
    sqlite_results = sim_results.get('sqlite', {})
    if sqlite_results and 'error' not in sqlite_results:
        print(f"\n📊 RESULTS FROM SQLITE OUTPUT:")
        
        if 'total_electricity_kwh' in sqlite_results:
            print(f"  Total Electricity: {sqlite_results['total_electricity_kwh']:,.2f} kWh")
        
        if 'total_natural_gas_kwh' in sqlite_results:
            print(f"  Total Natural Gas: {sqlite_results['total_natural_gas_kwh']:,.2f} kWh")
        
        if 'building_area_m2' in sqlite_results:
            print(f"  Building Area: {sqlite_results['building_area_m2']:.2f} m²")
        
        if 'electricity_meters' in sqlite_results:
            print(f"  Electricity Meters:")
            for meter_name, value in sqlite_results['electricity_meters'].items():
                print(f"    {meter_name}: {value:,.2f} kWh")
    
    print(f"\n  Output Directory: {sim_results.get('output_directory', 'N/A')}")

def main():
    """Run tests"""
    print("="*70)
    print("ENERGYPLUS SIMULATION RESULTS TEST")
    print("="*70)
    
    # Ensure output directory exists
    Path("test_outputs").mkdir(exist_ok=True)
    
    # Test 1: Small office building
    test1 = test_building(
        name="Small Office",
        address="123 Main St, Chicago, IL 60601",
        params={
            'building_type': 'Office',
            'stories': 3,
            'floor_area_per_story_m2': 500,
            'city': 'Chicago'
        }
    )
    
    print_results_summary(test1)
    
    # Test 2: Medium office building
    test2 = test_building(
        name="Medium Office",
        address="456 Broadway, New York, NY 10013",
        params={
            'building_type': 'Office',
            'stories': 10,
            'floor_area_per_story_m2': 800,
            'city': 'New York'
        }
    )
    
    print_results_summary(test2)
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    
    tests = [test1, test2]
    successful = [t for t in tests if 'error' not in t]
    simulated = [t for t in successful if 'simulation_results' in t and 'error' not in t.get('simulation_results', {})]
    
    print(f"\n✅ Successful IDF Generation: {len(successful)}/{len(tests)}")
    print(f"🔄 Simulations Completed: {len(simulated)}/{len(successful)}")
    
    # Save results to JSON
    results_file = Path("test_outputs") / "energyplus_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            'tests': tests,
            'summary': {
                'total_tests': len(tests),
                'successful_idfs': len(successful),
                'successful_simulations': len(simulated)
            }
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    print(f"\n{'='*70}")

if __name__ == "__main__":
    main()












