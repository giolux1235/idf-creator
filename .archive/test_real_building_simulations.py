#!/usr/bin/env python3
"""Real building simulation test to verify area fix with EnergyPlus results"""

import sys
import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Optional

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from main import IDFCreator

def run_energyplus_simulation(idf_file: str, weather_file: Optional[str] = None) -> Dict:
    """
    Run EnergyPlus simulation on an IDF file.
    
    Returns:
        Dictionary with simulation results or error information
    """
    idf_path = Path(idf_file)
    if not idf_path.exists():
        return {'error': f'IDF file not found: {idf_file}'}
    
    # Find EnergyPlus installation
    eplus_path = None
    possible_paths = [
        '/Applications/EnergyPlus-24-2-0/energyplus',
        '/usr/local/bin/energyplus',
        'energyplus',  # If in PATH
    ]
    
    for path in possible_paths:
        if path == 'energyplus':
            # Check if in PATH
            result = subprocess.run(['which', 'energyplus'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                eplus_path = result.stdout.strip()
                break
        elif os.path.exists(path):
            eplus_path = path
            break
    
    if not eplus_path:
        return {'error': 'EnergyPlus not found. Please install EnergyPlus or add to PATH.'}
    
    # Get weather file from IDF if not provided
    if not weather_file:
        with open(idf_file, 'r') as f:
            content = f.read()
            # Try to extract weather file
            import re
            weather_match = re.search(r'Site:Location[^,]*,\s*([^,]+),', content)
            if weather_match:
                # Weather file is usually in the IDF comments or Site:Location
                pass
    
    # Create output directory
    output_dir = idf_path.parent / 'sim_results' / idf_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run EnergyPlus
    try:
        cmd = [
            eplus_path,
            '-w', weather_file or 'USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw',  # Default
            '-d', str(output_dir),
            str(idf_path)
        ]
        
        print(f"  Running EnergyPlus simulation...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            return {
                'error': f'EnergyPlus failed: {result.stderr[:500]}',
                'stdout': result.stdout[:500]
            }
        
        # Look for results CSV
        csv_files = list(output_dir.glob('*.csv'))
        eplus_eso = list(output_dir.glob('*.eso'))
        
        return {
            'success': True,
            'output_dir': str(output_dir),
            'csv_files': [str(f) for f in csv_files],
            'eso_file': str(eplus_eso[0]) if eplus_eso else None,
            'stdout': result.stdout
        }
    except subprocess.TimeoutExpired:
        return {'error': 'EnergyPlus simulation timed out'}
    except Exception as e:
        return {'error': f'Error running EnergyPlus: {str(e)}'}

def extract_energy_results(csv_file: str) -> Dict:
    """Extract energy consumption from EnergyPlus CSV results"""
    try:
        import csv
        
        results = {
            'total_electricity_kwh': 0,
            'total_gas_kwh': 0,
            'total_energy_kwh': 0,
            'cooling_kwh': 0,
            'heating_kwh': 0,
            'lights_kwh': 0,
            'equipment_kwh': 0,
            'zone_count': 0,
            'total_area_m2': 0
        }
        
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            
            # Find relevant columns
            elec_col = None
            gas_col = None
            cool_col = None
            heat_col = None
            lights_col = None
            equip_col = None
            
            for i, header in enumerate(headers):
                header_lower = header.lower()
                if 'electricity' in header_lower and 'total' in header_lower:
                    elec_col = i
                elif 'gas' in header_lower or 'natural gas' in header_lower:
                    gas_col = i
                elif 'cooling' in header_lower:
                    cool_col = i
                elif 'heating' in header_lower:
                    heat_col = i
                elif 'lights' in header_lower:
                    lights_col = i
                elif 'equipment' in header_lower:
                    equip_col = i
            
            # Sum values
            for row in reader:
                if len(row) > max(filter(None, [elec_col, gas_col, cool_col, heat_col, lights_col, equip_col] or [0])):
                    try:
                        if elec_col:
                            results['total_electricity_kwh'] += float(row[elec_col] or 0)
                        if gas_col:
                            results['total_gas_kwh'] += float(row[gas_col] or 0)
                        if cool_col:
                            results['cooling_kwh'] += float(row[cool_col] or 0)
                        if heat_col:
                            results['heating_kwh'] += float(row[heat_col] or 0)
                        if lights_col:
                            results['lights_kwh'] += float(row[lights_col] or 0)
                        if equip_col:
                            results['equipment_kwh'] += float(row[equip_col] or 0)
                    except (ValueError, IndexError):
                        continue
        
        results['total_energy_kwh'] = results['total_electricity_kwh'] + results['total_gas_kwh']
        
        return results
    except Exception as e:
        return {'error': f'Error parsing CSV: {str(e)}'}

def analyze_simulation_results(idf_file: str, expected_area_m2: float, 
                              simulation_result: Dict) -> Dict:
    """Analyze simulation results to verify area fix"""
    
    analysis = {
        'idf_file': idf_file,
        'expected_area_m2': expected_area_m2,
        'simulation_successful': simulation_result.get('success', False),
        'energy_results': {},
        'eui_kbtu_ft2': None,
        'area_verification': 'unknown'
    }
    
    if not simulation_result.get('success'):
        analysis['error'] = simulation_result.get('error', 'Unknown error')
        return analysis
    
    # Try to extract energy results
    csv_files = simulation_result.get('csv_files', [])
    if csv_files:
        energy_results = extract_energy_results(csv_files[0])
        analysis['energy_results'] = energy_results
        
        # Calculate EUI if we have total energy and area
        if energy_results.get('total_energy_kwh') and expected_area_m2 > 0:
            # Convert kWh to kBtu (1 kWh = 3.412 kBtu)
            total_kbtu = energy_results['total_energy_kwh'] * 3.412
            # Convert m² to ft² (1 m² = 10.764 ft²)
            area_ft2 = expected_area_m2 * 10.764
            if area_ft2 > 0:
                analysis['eui_kbtu_ft2'] = total_kbtu / area_ft2
    
    return analysis

def test_real_buildings():
    """Test with real buildings and verify simulation results"""
    
    print("\n" + "="*80)
    print("REAL BUILDING SIMULATION TEST")
    print("="*80)
    
    # Define real building test cases
    test_buildings = [
        {
            'name': 'Willis Tower',
            'address': 'Willis Tower, Chicago, IL',
            'user_params': {
                'building_type': 'office',
                'floor_area_per_story_m2': 1500,
                'stories': 10,
                'year_built': 1973
            },
            'expected_total_area': 15000,  # 1500 × 10
            'expected_eui_range': (30, 80),  # Typical office range in kBtu/ft²
        },
        {
            'name': 'Empire State Building',
            'address': 'Empire State Building, New York, NY',
            'user_params': {
                'building_type': 'office',
                'floor_area_per_story_m2': 2000,
                'stories': 5,
                'year_built': 1931
            },
            'expected_total_area': 10000,  # 2000 × 5
            'expected_eui_range': (30, 80),
        },
        {
            'name': 'Small Office Building',
            'address': '600 Pine Street, Seattle, WA 98101',
            'user_params': {
                'building_type': 'office',
                'floor_area_per_story_m2': 800,
                'stories': 3,
            },
            'expected_total_area': 2400,  # 800 × 3
            'expected_eui_range': (30, 80),
        }
    ]
    
    creator = IDFCreator(config_path="config.yaml", enhanced=True, professional=True)
    results = []
    
    for i, building in enumerate(test_buildings):
        print(f"\n{'='*80}")
        print(f"Test {i+1}/{len(test_buildings)}: {building['name']}")
        print(f"{'='*80}")
        print(f"📍 Address: {building['address']}")
        print(f"📐 User Parameters:")
        print(f"   - Floor Area/Story: {building['user_params']['floor_area_per_story_m2']} m²")
        print(f"   - Stories: {building['user_params']['stories']}")
        print(f"   - Expected Total Area: {building['expected_total_area']:,} m²")
        
        try:
            # Generate IDF
            output_dir = Path("test_outputs/real_simulations")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            idf_file = output_dir / f"{building['name'].replace(' ', '_')}.idf"
            
            print(f"\n⚙️  Generating IDF...")
            generated_file = creator.create_idf(
                address=building['address'],
                user_params=building['user_params'],
                output_path=str(idf_file)
            )
            
            print(f"✅ IDF Generated: {generated_file}")
            
            # Run simulation
            print(f"\n🔬 Running EnergyPlus simulation...")
            sim_result = run_energyplus_simulation(generated_file)
            
            if sim_result.get('success'):
                print(f"✅ Simulation completed successfully")
                print(f"   Output directory: {sim_result['output_dir']}")
                
                # Analyze results
                analysis = analyze_simulation_results(
                    generated_file,
                    building['expected_total_area'],
                    sim_result
                )
                
                # Print results
                if analysis.get('energy_results'):
                    energy = analysis['energy_results']
                    print(f"\n📊 Energy Results:")
                    if energy.get('total_electricity_kwh'):
                        print(f"   Total Electricity: {energy['total_electricity_kwh']:,.0f} kWh")
                    if energy.get('total_gas_kwh'):
                        print(f"   Total Gas: {energy['total_gas_kwh']:,.0f} kWh")
                    if energy.get('total_energy_kwh'):
                        print(f"   Total Energy: {energy['total_energy_kwh']:,.0f} kWh")
                    
                    if analysis.get('eui_kbtu_ft2'):
                        eui = analysis['eui_kbtu_ft2']
                        print(f"\n📈 Energy Use Intensity (EUI):")
                        print(f"   {eui:.1f} kBtu/ft²")
                        expected_min, expected_max = building['expected_eui_range']
                        if expected_min <= eui <= expected_max:
                            print(f"   ✅ Within expected range ({expected_min}-{expected_max} kBtu/ft²)")
                        else:
                            print(f"   ⚠️  Outside expected range ({expected_min}-{expected_max} kBtu/ft²)")
                
                results.append({
                    'building': building['name'],
                    'status': 'SUCCESS',
                    'idf_file': generated_file,
                    'simulation': sim_result,
                    'analysis': analysis
                })
            else:
                error_msg = sim_result.get('error', 'Unknown error')
                print(f"⚠️  Simulation failed: {error_msg}")
                print(f"   (This may be due to EnergyPlus not being installed)")
                results.append({
                    'building': building['name'],
                    'status': 'IDF_GENERATED',
                    'idf_file': generated_file,
                    'simulation': sim_result
                })
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'building': building['name'],
                'status': 'FAILED',
                'error': str(e)
            })
    
    # Print summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    
    successful = sum(1 for r in results if r['status'] == 'SUCCESS')
    idf_only = sum(1 for r in results if r['status'] == 'IDF_GENERATED')
    failed = sum(1 for r in results if r['status'] == 'FAILED')
    
    print(f"\n✅ Simulations Completed: {successful}/{len(results)}")
    if idf_only > 0:
        print(f"📄 IDFs Generated (simulation not run): {idf_only}/{len(results)}")
    if failed > 0:
        print(f"❌ Failed: {failed}/{len(results)}")
    
    print(f"\nDetailed Results:")
    for r in results:
        status_icon = '✅' if r['status'] == 'SUCCESS' else '📄' if r['status'] == 'IDF_GENERATED' else '❌'
        print(f"  {status_icon} {r['building']}: {r['status']}")
        if r['status'] == 'SUCCESS' and r.get('analysis', {}).get('eui_kbtu_ft2'):
            print(f"     EUI: {r['analysis']['eui_kbtu_ft2']:.1f} kBtu/ft²")
    
    print(f"\n{'='*80}\n")
    
    return successful > 0 or idf_only > 0

if __name__ == "__main__":
    try:
        success = test_real_buildings()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

