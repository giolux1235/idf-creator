#!/usr/bin/env python3
"""
Verify thermostats are created and not commented, and check energy consumption.
This script:
1. Checks IDF files for thermostat objects (not commented)
2. Re-runs simulations to verify energy consumption
3. Validates energy is in realistic range (100-200 kWh/m²/year)
4. Reports warnings if outside expected range
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import IDFCreator
from src.validation.energy_coherence_validator import EnergyCoherenceValidator
from test_energyplus_results import find_energyplus, extract_results_from_csv, run_simulation


def check_thermostats_in_idf(idf_path: str) -> Dict:
    """Check if thermostats are present and not commented in IDF file"""
    results = {
        'thermostat_setpoints': [],
        'zone_controls': [],
        'commented_thermostats': [],
        'missing_thermostats': [],
        'all_zones': []
    }
    
    try:
        with open(idf_path, 'r') as f:
            content = f.read()
        
        # Find all zones (Zone, is on one line, name is on next line)
        # Split content into lines and check each
        lines = content.split('\n')
        zones = []
        for i, line in enumerate(lines):
            # Skip comments and empty lines
            stripped = line.strip()
            if not stripped or stripped.startswith('!'):
                continue
            # Check for Zone object at start of line
            if re.match(r'^Zone,', stripped, re.IGNORECASE):
                # Zone name is on the next non-comment line
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line or next_line.startswith('!'):
                        continue
                    # Extract zone name from first field (before comma)
                    zone_name_match = re.match(r'^([^,!\n]+)', next_line)
                    if zone_name_match:
                        zones.append(zone_name_match.group(1).strip())
                        break
        results['all_zones'] = zones
        
        # Find ThermostatSetpoint:DualSetpoint objects (check line by line to avoid comment matches)
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith('!'):
                continue
            # Check for ThermostatSetpoint at start of line
            thermostat_match = re.match(r'^ThermostatSetpoint:DualSetpoint,\s*([^,!\n]+)', stripped, re.IGNORECASE)
            if thermostat_match:
                name = thermostat_match.group(1).strip()
                results['thermostat_setpoints'].append(name)
            # Check for commented version (line starts with !)
            elif stripped.startswith('!') and 'ThermostatSetpoint:DualSetpoint' in stripped:
                # Extract name from commented line
                comment_match = re.search(r'ThermostatSetpoint:DualSetpoint[,\s]+([^,!\n]+)', stripped, re.IGNORECASE)
                if comment_match:
                    results['commented_thermostats'].append(comment_match.group(1).strip())
        
        # Find ZoneControl:Thermostat objects (name is on next line after the header)
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith('!'):
                continue
            # Check for ZoneControl:Thermostat at start of line
            if re.match(r'^ZoneControl:Thermostat,', stripped, re.IGNORECASE):
                # Read next few lines to find the name (usually on next non-comment line)
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line or next_line.startswith('!'):
                        continue
                    # Extract name from first field (before comma)
                    name_match = re.match(r'^([^,!\n]+)', next_line)
                    if name_match:
                        name = name_match.group(1).strip()
                        results['zone_controls'].append(name)
                        break
        
        # Check for missing thermostats (zones without thermostat controls)
        # Read ZoneControl:Thermostat objects to get zone names (zone name is on line after name)
        zones_with_controls = set()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith('!'):
                continue
            if re.match(r'^ZoneControl:Thermostat,', stripped, re.IGNORECASE):
                # Read the next few lines to find zone_or_zonelist_name
                # Format: ZoneControl:Thermostat,
                #   Name,                    !- Name
                #   ZoneName,                !- Zone or ZoneList Name
                name_found = False
                for j in range(i+1, min(i+6, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line or next_line.startswith('!'):
                        continue
                    if not name_found:
                        # First non-comment line is the name
                        name_found = True
                        continue
                    # Second non-comment line is the zone name
                    zone_name_match = re.match(r'^([^,!\n]+)', next_line)
                    if zone_name_match:
                        zone_name = zone_name_match.group(1).strip()
                        # Check if this matches any zone
                        for zone in results['all_zones']:
                            if zone == zone_name or zone_name == zone:
                                zones_with_controls.add(zone)
                        break
        
        # Also check by matching control names (format: {zone}_ZoneControl)
        for zc in results['zone_controls']:
            # Try to extract zone name from control name
            # Format: {zone}_ZoneControl or {zone}_z1_ZoneControl
            for zone in results['all_zones']:
                # Check various patterns
                if (zone in zc or 
                    zc.replace('_ZoneControl', '') == zone or 
                    zc.replace('_ZoneControl', '') == zone + '_z1' or
                    zc.startswith(zone + '_') and zc.endswith('_ZoneControl')):
                    zones_with_controls.add(zone)
        
        # Zones without controls
        results['missing_thermostats'] = [
            zone for zone in results['all_zones'] 
            if zone not in zones_with_controls
        ]
        
        # Overall status
        results['has_issues'] = (
            len(results['commented_thermostats']) > 0 or
            len(results['missing_thermostats']) > 0 or
            len(results['thermostat_setpoints']) == 0
        )
        results['status'] = 'OK' if not results['has_issues'] else 'ISSUES FOUND'
        
    except Exception as e:
        results['error'] = str(e)
        results['status'] = 'ERROR'
    
    return results


def extract_energy_metrics(simulation_results: Dict) -> Dict:
    """Extract energy metrics from simulation results"""
    metrics = {
        'total_site_energy_kwh': None,
        'building_area_m2': None,
        'eui_kwh_m2': None,
        'end_uses': {}
    }
    
    # Try CSV results first
    csv_results = simulation_results.get('csv', {})
    if csv_results and 'error' not in csv_results:
        metrics['total_site_energy_kwh'] = csv_results.get('total_site_energy_kwh')
        metrics['building_area_m2'] = csv_results.get('building_area_m2')
        metrics['eui_kwh_m2'] = csv_results.get('eui_kwh_m2')
        metrics['end_uses'] = csv_results.get('end_uses', {})
    
    # Fallback to SQLite if available
    if metrics['total_site_energy_kwh'] is None:
        sqlite_results = simulation_results.get('sqlite', {})
        if sqlite_results and 'error' not in sqlite_results:
            if 'total_electricity_kwh' in sqlite_results:
                metrics['total_site_energy_kwh'] = sqlite_results['total_electricity_kwh']
            if 'building_area_m2' in sqlite_results:
                metrics['building_area_m2'] = sqlite_results['building_area_m2']
    
    # If still no data, try to read directly from output directory
    if metrics['total_site_energy_kwh'] is None:
        output_dir = simulation_results.get('output_directory')
        if output_dir:
            import os
            csv_path = os.path.join(output_dir, 'eplustbl.csv')
            if os.path.exists(csv_path):
                csv_results = extract_results_from_csv(csv_path)
                if csv_results and 'error' not in csv_results:
                    metrics['total_site_energy_kwh'] = csv_results.get('total_site_energy_kwh')
                    metrics['building_area_m2'] = csv_results.get('building_area_m2')
                    metrics['eui_kwh_m2'] = csv_results.get('eui_kwh_m2')
                    metrics['end_uses'] = csv_results.get('end_uses', {})
    
    # Calculate EUI if we have energy and area
    if metrics['total_site_energy_kwh'] and metrics['building_area_m2']:
        if metrics['eui_kwh_m2'] is None:
            metrics['eui_kwh_m2'] = metrics['total_site_energy_kwh'] / metrics['building_area_m2']
    
    return metrics


def validate_energy_range(eui_kwh_m2: Optional[float], building_type: str = 'office') -> Dict:
    """Validate energy consumption is in expected range (100-200 kWh/m²/year)"""
    validation = {
        'status': 'UNKNOWN',
        'eui': eui_kwh_m2,
        'expected_range': (100, 200),
        'warnings': [],
        'is_valid': False
    }
    
    if eui_kwh_m2 is None:
        validation['status'] = 'NO_DATA'
        validation['warnings'].append('Energy consumption data not available')
        return validation
    
    if eui_kwh_m2 == 0:
        validation['status'] = 'ZERO_ENERGY'
        validation['warnings'].append(
            'Energy consumption is zero - HVAC systems may not be operating. '
            'Check if thermostats are properly configured.'
        )
        return validation
    
    if eui_kwh_m2 < 100:
        validation['status'] = 'TOO_LOW'
        validation['warnings'].append(
            f'Energy consumption ({eui_kwh_m2:.2f} kWh/m²/year) is below expected range '
            f'(100-200 kWh/m²/year). This suggests HVAC systems may not be operating properly.'
        )
        if eui_kwh_m2 < 50:
            validation['warnings'].append(
                'Very low energy consumption - likely indicates missing thermostat control or HVAC system issues.'
            )
    elif eui_kwh_m2 > 200:
        validation['status'] = 'TOO_HIGH'
        validation['warnings'].append(
            f'Energy consumption ({eui_kwh_m2:.2f} kWh/m²/year) is above expected range '
            f'(100-200 kWh/m²/year). This may indicate excessive loads or HVAC efficiency issues.'
        )
    else:
        validation['status'] = 'VALID'
        validation['is_valid'] = True
    
    return validation


def test_idf_file(idf_path: str, weather_file: Optional[str] = None, 
                  building_type: str = 'office') -> Dict:
    """Test a single IDF file for thermostats and energy consumption"""
    print(f"\n{'='*70}")
    print(f"Testing IDF: {idf_path}")
    print(f"{'='*70}")
    
    results = {
        'idf_path': idf_path,
        'thermostat_check': {},
        'simulation': {},
        'energy_metrics': {},
        'energy_validation': {},
        'status': 'PENDING'
    }
    
    # Step 1: Check thermostats
    print(f"\n1️⃣ Checking thermostats in IDF file...")
    thermostat_check = check_thermostats_in_idf(idf_path)
    results['thermostat_check'] = thermostat_check
    
    if thermostat_check.get('has_issues'):
        print(f"   ⚠️  Issues found:")
        if thermostat_check.get('commented_thermostats'):
            print(f"      - Commented thermostats: {len(thermostat_check['commented_thermostats'])}")
            for t in thermostat_check['commented_thermostats'][:5]:  # Show first 5
                print(f"        * {t}")
        if thermostat_check.get('missing_thermostats'):
            print(f"      - Zones without thermostats: {len(thermostat_check['missing_thermostats'])}")
            for z in thermostat_check['missing_thermostats'][:5]:  # Show first 5
                print(f"        * {z}")
        if len(thermostat_check.get('thermostat_setpoints', [])) == 0:
            print(f"      - No ThermostatSetpoint objects found")
        if len(thermostat_check.get('zone_controls', [])) == 0:
            print(f"      - No ZoneControl:Thermostat objects found (CRITICAL)")
    else:
        print(f"   ✅ All thermostats are properly configured")
        print(f"      - ThermostatSetpoint objects: {len(thermostat_check.get('thermostat_setpoints', []))}")
        print(f"      - ZoneControl objects: {len(thermostat_check.get('zone_controls', []))}")
        print(f"      - Zones: {len(thermostat_check.get('all_zones', []))}")
    
    # Step 2: Run simulation
    print(f"\n2️⃣ Running EnergyPlus simulation...")
    energyplus_path = find_energyplus()
    
    if not energyplus_path:
        print(f"   ⚠️  EnergyPlus not found - skipping simulation")
        results['simulation'] = {'error': 'EnergyPlus not found'}
        results['status'] = 'NO_SIMULATION'
        return results
    
    output_dir = Path("test_outputs") / f"verify_{Path(idf_path).stem}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    sim_results = run_simulation(idf_path, weather_file, str(output_dir))
    results['simulation'] = sim_results
    
    if 'error' in sim_results:
        print(f"   ❌ Simulation error: {sim_results['error']}")
        results['status'] = 'SIMULATION_ERROR'
        return results
    
    print(f"   ✅ Simulation completed")
    
    # Step 3: Extract energy metrics
    print(f"\n3️⃣ Extracting energy metrics...")
    energy_metrics = extract_energy_metrics(sim_results)
    results['energy_metrics'] = energy_metrics
    
    if energy_metrics['eui_kwh_m2']:
        print(f"   Building Area: {energy_metrics['building_area_m2']:.2f} m²")
        print(f"   Total Site Energy: {energy_metrics['total_site_energy_kwh']:,.2f} kWh")
        print(f"   EUI: {energy_metrics['eui_kwh_m2']:.2f} kWh/m²/year")
        
        # Step 4: Validate energy range
        print(f"\n4️⃣ Validating energy consumption range...")
        energy_validation = validate_energy_range(
            energy_metrics['eui_kwh_m2'], 
            building_type
        )
        results['energy_validation'] = energy_validation
        
        if energy_validation['is_valid']:
            print(f"   ✅ Energy consumption is within expected range (100-200 kWh/m²/year)")
        else:
            print(f"   ⚠️  Energy consumption validation:")
            for warning in energy_validation['warnings']:
                print(f"      - {warning}")
        
        results['status'] = 'COMPLETE'
    else:
        print(f"   ⚠️  Could not extract energy metrics")
        results['status'] = 'NO_ENERGY_DATA'
    
    return results


def generate_test_idf(address: str, params: Dict, output_path: str) -> str:
    """Generate a new IDF file for testing"""
    print(f"\n📝 Generating new IDF file...")
    creator = IDFCreator(professional=True, enhanced=True)
    idf_path = creator.create_idf(
        address=address,
        user_params=params,
        output_path=output_path
    )
    print(f"✅ IDF generated: {idf_path}")
    return idf_path


def main():
    """Main test function"""
    print("="*70)
    print("THERMOSTAT AND ENERGY CONSUMPTION VERIFICATION")
    print("="*70)
    
    # Ensure output directory exists
    Path("test_outputs").mkdir(exist_ok=True)
    
    # Test 1: Generate new IDF and verify
    print(f"\n{'='*70}")
    print("TEST 1: Generate new IDF and verify thermostats + energy")
    print(f"{'='*70}")
    
    test_idf_path = Path("test_outputs") / "verify_thermostat_test.idf"
    
    # Generate new IDF
    test_idf = generate_test_idf(
        address="123 Main St, Chicago, IL 60601",
        params={
            'building_type': 'Office',
            'stories': 3,
            'floor_area_per_story_m2': 500,
            'city': 'Chicago'
        },
        output_path=str(test_idf_path)
    )
    
    # Find weather file
    weather_file = None
    weather_paths = [
        "artifacts/desktop_files/weather/Chicago.epw",
        "artifacts/desktop_files/weather/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw",
    ]
    for wp in weather_paths:
        if Path(wp).exists():
            weather_file = wp
            break
    
    if weather_file:
        print(f"🌤️  Using weather file: {weather_file}")
    else:
        print(f"⚠️  No weather file found")
    
    # Test the IDF
    test_results = test_idf_file(test_idf, weather_file, building_type='office')
    
    # Test 2: Check existing IDF files if they exist
    existing_idfs = [
        "output/professional_test_1_office.idf",
        "output/professional_test_2_mixed_use.idf",
        "test_outputs/test_small_office.idf"
    ]
    
    existing_tests = []
    for idf_path_str in existing_idfs:
        idf_path = Path(idf_path_str)
        if idf_path.exists():
            print(f"\n{'='*70}")
            print(f"TEST: Checking existing IDF - {idf_path.name}")
            print(f"{'='*70}")
            result = test_idf_file(str(idf_path), weather_file, building_type='office')
            existing_tests.append(result)
    
    # Summary
    print(f"\n{'='*70}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*70}")
    
    all_tests = [test_results] + existing_tests
    
    print(f"\n📊 Thermostat Checks:")
    for i, test in enumerate(all_tests, 1):
        thermostat_check = test.get('thermostat_check', {})
        status = thermostat_check.get('status', 'UNKNOWN')
        print(f"  Test {i}: {status}")
        if thermostat_check.get('has_issues'):
            print(f"    - Commented: {len(thermostat_check.get('commented_thermostats', []))}")
            print(f"    - Missing: {len(thermostat_check.get('missing_thermostats', []))}")
    
    print(f"\n📊 Energy Consumption:")
    for i, test in enumerate(all_tests, 1):
        energy_metrics = test.get('energy_metrics', {})
        energy_validation = test.get('energy_validation', {})
        eui = energy_metrics.get('eui_kwh_m2')
        if eui is not None:
            status = energy_validation.get('status', 'UNKNOWN')
            print(f"  Test {i}: EUI = {eui:.2f} kWh/m²/year ({status})")
            if not energy_validation.get('is_valid'):
                for warning in energy_validation.get('warnings', []):
                    print(f"    ⚠️  {warning}")
        else:
            print(f"  Test {i}: No energy data available")
    
    print(f"\n{'='*70}")


if __name__ == "__main__":
    main()

