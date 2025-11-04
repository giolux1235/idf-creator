#!/usr/bin/env python3
"""
Test Empire State Building simulation with EnergyPlus API
"""
import sys
import os
from main import IDFCreator
from src.validation import validate_simulation, EnergyPlusSimulationValidator


def test_empire_state_simulation():
    """Generate IDF for Empire State Building and run EnergyPlus simulation"""
    print("=" * 80)
    print("EMPIRE STATE BUILDING - ENERGYPLUS SIMULATION TEST")
    print("=" * 80)
    
    # Step 1: Generate IDF
    print("\n1. Generating IDF for Empire State Building...")
    location_data = None
    try:
        creator = IDFCreator(professional=True, enhanced=True)
        
        # Get location data first
        location_data = creator.process_inputs(
            address="Empire State Building, New York, NY",
            user_params={
                'building_type': 'Office',
                'stories': 5,  # Use fewer stories for faster simulation
                'floor_area': 10000,  # 10,000 m² for reasonable simulation time
            }
        )
        
        # Generate IDF
        idf_file = creator.create_idf(
            address="Empire State Building, New York, NY",
            user_params={
                'building_type': 'Office',
                'stories': 5,
                'floor_area': 10000,
            },
            output_path="artifacts/desktop_files/idf/empire_state_test.idf"
        )
        
        print(f"   ✓ IDF generated: {idf_file}")
        
    except Exception as e:
        print(f"   ✗ IDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 2: Get weather file info from location data
    print("\n2. Preparing simulation...")
    try:
        # Get weather file name from location data
        weather_file_name = location_data['location'].get('weather_file', 'USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw') if location_data else 'USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw'
        print(f"   Weather file: {weather_file_name}")
        
        # Try to find weather file in common locations
        weather_file = None
        weather_dirs = [
            "artifacts/desktop_files/weather",
            "weather",
            "/usr/share/EnergyPlus/weather",
            "/opt/EnergyPlus/weather",
        ]
        
        for weather_dir in weather_dirs:
            if os.path.exists(weather_dir):
                for file in os.listdir(weather_dir):
                    if file.endswith('.epw'):
                        # Check if it matches our weather file name or is close
                        if weather_file_name.lower() in file.lower() or 'new.york' in file.lower() or 'laguardia' in file.lower():
                            weather_file = os.path.join(weather_dir, file)
                            print(f"   ✓ Found weather file: {weather_file}")
                            break
                if weather_file:
                    break
        
        if not weather_file:
            print(f"   ⚠ Weather file not found locally")
            print(f"   EnergyPlus will try to use: {weather_file_name}")
            print(f"   (You can download weather files from https://energyplus.net/weather)")
        
        # Run simulation
        print("\n3. Running EnergyPlus simulation...")
        validator = EnergyPlusSimulationValidator()
        
        # Create output directory
        output_dir = "artifacts/desktop_files/simulation/empire_state"
        os.makedirs(output_dir, exist_ok=True)
        
        # Use absolute paths
        idf_file_abs = os.path.abspath(idf_file)
        output_dir_abs = os.path.abspath(output_dir)
        
        print(f"   IDF file: {idf_file_abs}")
        print(f"   Output directory: {output_dir_abs}")
        if weather_file:
            print(f"   Weather file: {weather_file}")
        else:
            print(f"   Weather file: None (EnergyPlus may use default or fail)")
        
        result = validator.validate_by_simulation(
            idf_file=idf_file_abs,
            weather_file=weather_file,  # None means EnergyPlus will look for default
            output_directory=output_dir_abs,
            timeout=600  # 10 minutes timeout
        )
        
        print(f"\n   Simulation Results:")
        print(f"   - Success: {result.success}")
        print(f"   - Fatal Errors: {result.fatal_errors}")
        print(f"   - Severe Errors: {result.severe_errors}")
        print(f"   - Warnings: {result.warnings}")
        
        if result.elapsed_time:
            print(f"   - Elapsed Time: {result.elapsed_time:.1f} seconds")
        
        if result.output_directory:
            print(f"   - Output Directory: {result.output_directory}")
        
        # Show errors if any
        if result.fatal_errors > 0:
            print(f"\n   Fatal Errors:")
            fatal_errors = [e for e in result.errors if e.severity == 'fatal']
            for err in fatal_errors[:5]:
                print(f"     • {err.message}")
        
        if result.severe_errors > 0:
            print(f"\n   Severe Errors:")
            severe_errors = [e for e in result.errors if e.severity == 'severe']
            for err in severe_errors[:5]:
                print(f"     • {err.message}")
        
        # Step 4: Extract energy results
        if result.success and result.output_directory:
            print("\n3. Extracting energy results...")
            try:
                energy_results = validator.get_energy_results(result.output_directory)
                
                if energy_results and 'error' not in energy_results:
                    print(f"   ✓ Energy results extracted")
                    print(f"   - Rows: {energy_results.get('rows', 'N/A')}")
                    print(f"   - Columns: {len(energy_results.get('columns', []))}")
                    
                    if 'total_electricity' in energy_results:
                        print(f"   - Total Electricity: {energy_results['total_electricity']:.2f} kWh")
                    
                    if 'total_gas' in energy_results:
                        print(f"   - Total Gas: {energy_results['total_gas']:.2f} kWh")
                    
                    # Show available columns
                    columns = energy_results.get('columns', [])
                    energy_columns = [c for c in columns if any(x in c.lower() for x in 
                                ['electricity', 'gas', 'energy', 'heating', 'cooling', 'fan', 'lighting'])]
                    
                    if energy_columns:
                        print(f"\n   Available Energy Columns:")
                        for col in energy_columns[:10]:
                            print(f"     - {col}")
                    
                    # Try to extract more detailed metrics
                    if 'data' in energy_results:
                        print(f"\n   Sample Data (first row):")
                        if energy_results['data']:
                            first_row = energy_results['data'][0]
                            for key, value in list(first_row.items())[:5]:
                                print(f"     - {key}: {value}")
                    
                elif energy_results and 'error' in energy_results:
                    print(f"   ⚠ Could not extract energy results: {energy_results['error']}")
                else:
                    print(f"   ⚠ No energy results file found (eplustbl.csv)")
                    
            except Exception as e:
                print(f"   ⚠ Error extracting energy results: {e}")
        
        # Summary
        print("\n" + "=" * 80)
        print("SIMULATION SUMMARY")
        print("=" * 80)
        
        if result.success:
            print("✅ Simulation completed successfully!")
            print(f"   - No fatal or severe errors")
            print(f"   - {result.warnings} warning(s)")
            
            if result.output_directory:
                print(f"\n   Results available in: {result.output_directory}")
                print(f"   - eplusout.err: Error log")
                print(f"   - eplustbl.csv: Energy results table")
                print(f"   - eplusout.sql: SQL results database")
                print(f"   - eplusout.rdd: Report data dictionary")
        else:
            print("❌ Simulation had errors")
            print(f"   - {result.fatal_errors} fatal error(s)")
            print(f"   - {result.severe_errors} severe error(s)")
            print(f"   - {result.warnings} warning(s)")
            
            if result.output_directory and result.error_file_path:
                print(f"\n   Check error log: {result.error_file_path}")
        
        return result.success
        
    except Exception as e:
        print(f"   ✗ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_empire_state_simulation()
    sys.exit(0 if success else 1)

