#!/usr/bin/env python3
"""
Generate IDF for Chicago or Austin building and run EnergyPlus simulation with available weather file
"""
import sys
import os
import glob
from main import IDFCreator
from src.validation import (
    validate_simulation,
    EnergyPlusSimulationValidator,
    validate_energy_coherence
)


def find_weather_file():
    """Find available weather file"""
    print("=" * 80)
    print("SEARCHING FOR WEATHER FILES")
    print("=" * 80)
    
    search_paths = [
        "artifacts/desktop_files/weather/*.epw",
        "weather/*.epw",
        "*.epw",
        "/usr/local/EnergyPlus*/weather/*.epw",
        "/opt/EnergyPlus*/weather/*.epw",
        os.path.expanduser("~/weather/*.epw"),
    ]
    
    found_files = []
    for pattern in search_paths:
        matches = glob.glob(pattern)
        found_files.extend(matches)
    
    # Also check EnergyPlus installation directories
    try:
        import subprocess
        result = subprocess.run(['which', 'energyplus'], capture_output=True, text=True)
        if result.returncode == 0:
            ep_path = os.path.dirname(result.stdout.strip())
            # Look in typical weather locations
            for loc in ['../weather', '../../weather', 'weather']:
                weather_dir = os.path.join(os.path.dirname(ep_path), loc)
                if os.path.exists(weather_dir):
                    epw_files = glob.glob(os.path.join(weather_dir, "*.epw"))
                    found_files.extend(epw_files)
    except:
        pass
    
    # Remove duplicates
    found_files = list(set(found_files))
    
    if found_files:
        print(f"\n   ✓ Found {len(found_files)} weather file(s):")
        for f in found_files[:5]:
            print(f"     - {f}")
        return found_files[0]
    else:
        print(f"\n   ⚠ No weather files found")
        print(f"   Will try to use city-specific default")
        return None


def get_weather_for_location(location_data, city):
    """Get weather file name from location data"""
    if not location_data:
        return None
    
    weather_info = location_data.get('weather', {})
    weather_file_name = weather_info.get('file_name') or weather_info.get('epw_file')
    
    if weather_file_name:
        # Try to find it locally
        search_paths = [
            f"artifacts/desktop_files/weather/{weather_file_name}",
            f"weather/{weather_file_name}",
            weather_file_name,
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                return path
    
    return None


def test_building_simulation(city: str, building_name: str, address: str):
    """Generate IDF and run simulation for a building"""
    print("=" * 80)
    print(f"{building_name.upper()} - {city.upper()} - ENERGY SIMULATION")
    print("=" * 80)
    
    # Step 1: Find weather file
    print("\n1. Finding weather file...")
    weather_file = find_weather_file()
    
    if not weather_file:
        print("   ⚠ No weather file found - will try to continue anyway")
    else:
        print(f"   ✓ Using weather file: {weather_file}")
    
    # Step 2: Generate IDF
    print(f"\n2. Generating IDF for {building_name}...")
    building_params = {
        'building_type': 'Office',
        'stories': 3,
        'floor_area': 5000,
    }
    
    try:
        creator = IDFCreator(professional=True, enhanced=True)
        
        print(f"   Address: {address}")
        location_data = creator.process_inputs(
            address=address,
            user_params=building_params
        )
        
        # Try to get weather file from location data
        if not weather_file and location_data:
            weather_file = get_weather_for_location(location_data, city)
            if weather_file and os.path.exists(weather_file):
                print(f"   ✓ Found weather file from location data: {weather_file}")
        
        idf_file = creator.create_idf(
            address=address,
            user_params=building_params,
            output_path=f"artifacts/desktop_files/idf/{city.lower()}_test.idf"
        )
        
        print(f"   ✓ IDF generated: {idf_file}")
        
        # Get building info
        total_area = building_params['floor_area'] * building_params['stories']
        print(f"   - Building area: {total_area:,} m² ({total_area*10.764:,.0f} ft²)")
        print(f"   - Stories: {building_params['stories']}")
        print(f"   - Building type: {building_params['building_type']}")
        
    except Exception as e:
        print(f"   ✗ IDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Run simulation
    print(f"\n3. Running EnergyPlus simulation...")
    output_dir = f"artifacts/desktop_files/simulation/{city.lower()}"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        validator = EnergyPlusSimulationValidator()
        
        # Use absolute paths
        idf_abs = os.path.abspath(idf_file)
        output_abs = os.path.abspath(output_dir)
        
        if weather_file:
            weather_abs = os.path.abspath(weather_file) if os.path.exists(weather_file) else weather_file
        else:
            weather_abs = None
        
        print(f"   IDF: {idf_abs}")
        print(f"   Output: {output_abs}")
        if weather_abs:
            print(f"   Weather: {weather_abs}")
        else:
            print(f"   Weather: None (will use default or fail)")
        
        result = validator.validate_by_simulation(
            idf_file=idf_abs,
            weather_file=weather_abs,
            output_directory=output_abs,
            timeout=600  # 10 minutes
        )
        
        print(f"\n   Simulation Results:")
        print(f"   - Success: {result.success}")
        print(f"   - Fatal errors: {result.fatal_errors}")
        print(f"   - Severe errors: {result.severe_errors}")
        print(f"   - Warnings: {result.warnings}")
        
        if result.errors:
            print(f"\n   Errors:")
            for err in result.errors[:5]:
                print(f"     • {err.severity}: {err.message}")
        
        if not result.success:
            print(f"\n   ⚠ Simulation had errors - checking partial results anyway")
        
    except Exception as e:
        print(f"   ✗ Simulation error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Extract and validate energy results
    print(f"\n4. Extracting energy results...")
    try:
        energy_results = validator.get_energy_results(output_abs)
        
        if not energy_results or 'error' in energy_results:
            print(f"   ⚠ No energy results available")
            if not result.success:
                print(f"   Simulation did not complete successfully")
            return False
        
        print(f"   ✓ Energy results extracted")
        print(f"   - Rows: {energy_results.get('rows', 'N/A')}")
        print(f"   - Columns: {len(energy_results.get('columns', []))}")
        
        # Show available columns
        columns = energy_results.get('columns', [])
        energy_cols = [c for c in columns if any(x in c.lower() for x in 
                    ['electricity', 'gas', 'energy', 'heating', 'cooling', 'fan', 'lighting', 'equipment'])]
        
        if energy_cols:
            print(f"\n   Energy Columns Found:")
            for col in energy_cols[:10]:
                print(f"     - {col}")
        
        # Extract total energy
        if 'data' in energy_results and energy_results['data']:
            first_row = energy_results['data'][0]
            
            # Try to find total energy
            total_energy = 0
            for col in columns:
                try:
                    val = first_row.get(col, 0)
                    if isinstance(val, str):
                        val = float(val.replace(',', ''))
                    else:
                        val = float(val) if val else 0
                    if val > 0:
                        # Check if it's an energy column
                        col_lower = col.lower()
                        if any(x in col_lower for x in ['electricity', 'energy', 'kwh', 'total']):
                            total_energy += val
                            print(f"\n   {col}: {val:,.0f} kWh")
                except:
                    pass
            
            if total_energy > 0:
                # Calculate EUI
                total_area_m2 = building_params['floor_area'] * building_params['stories']
                eui_kwh_m2 = total_energy / total_area_m2
                eui_kbtu_ft2 = (eui_kwh_m2 * 3.412) / 10.764  # Convert to kBtu/ft²
                
                print(f"\n   Energy Summary:")
                print(f"   - Total Energy: {total_energy:,.0f} kWh/year")
                print(f"   - EUI: {eui_kwh_m2:.1f} kWh/m²/year")
                print(f"   - EUI: {eui_kbtu_ft2:.1f} kBtu/ft²/year")
                
                # Compare to CBECS
                from src.cbecs_lookup import CBECSLookup
                cbecs = CBECSLookup()
                typical_eui = cbecs.get_site_eui('office')
                if typical_eui:
                    if eui_kbtu_ft2 < typical_eui * 0.7:
                        print(f"   ⚠ EUI is low (typical office: {typical_eui:.1f} kBtu/ft²)")
                    elif eui_kbtu_ft2 > typical_eui * 1.5:
                        print(f"   ⚠ EUI is high (typical office: {typical_eui:.1f} kBtu/ft²)")
                    else:
                        print(f"   ✓ EUI is within typical range (typical: {typical_eui:.1f} kBtu/ft²)")
        
        # Step 5: Validate energy coherence
        print(f"\n5. Validating energy coherence...")
        try:
            # Read IDF content
            with open(idf_file, 'r') as f:
                idf_content = f.read()
            
            coherence_results = validate_energy_coherence(
                energy_results=energy_results,
                building_type=building_params['building_type'],
                total_area_m2=total_area,
                stories=building_params['stories'],
                idf_content=idf_content
            )
            
            print(f"   - Issues: {coherence_results['issue_count']}")
            print(f"   - Warnings: {coherence_results['warning_count']}")
            
            if coherence_results['issues']:
                print(f"\n   Critical Issues:")
                for issue in coherence_results['issues'][:3]:
                    print(f"     ❌ {issue.metric}: {issue.reason}")
            else:
                print(f"   ✓ No critical issues found")
            
            if coherence_results['warnings']:
                print(f"\n   Warnings:")
                for warn in coherence_results['warnings'][:3]:
                    print(f"     ⚠ {warn.metric}: {warn.reason}")
            
            if coherence_results['is_coherent']:
                print(f"\n   ✅ Energy results are physically coherent!")
            else:
                print(f"\n   ⚠ Energy results have coherence issues")
        
        except Exception as e:
            print(f"   ⚠ Coherence validation error: {e}")
            import traceback
            traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"   ✗ Energy extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Test simulations for Chicago and Austin"""
    
    # Try Chicago first (Willis Tower)
    print("\n" + "="*80)
    print("TEST 1: CHICAGO BUILDING")
    print("="*80)
    
    chicago_success = test_building_simulation(
        city="Chicago",
        building_name="Willis Tower",
        address="Willis Tower, Chicago, IL"
    )
    
    # Try Austin second (Capitol Building or Austin Tower)
    print("\n\n" + "="*80)
    print("TEST 2: AUSTIN BUILDING")
    print("="*80)
    
    austin_success = test_building_simulation(
        city="Austin",
        building_name="Austin Tower",
        address="600 Congress Avenue, Austin, TX"
    )
    
    # Summary
    print("\n\n" + "="*80)
    print("SIMULATION SUMMARY")
    print("="*80)
    print(f"Chicago: {'✅ Success' if chicago_success else '❌ Failed'}")
    print(f"Austin: {'✅ Success' if austin_success else '❌ Failed'}")


if __name__ == "__main__":
    main()



