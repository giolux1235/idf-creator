#!/usr/bin/env python3
"""
Test VAV system with fixed node connections
"""
import sys
from main import IDFCreator

def test_vav_system():
    """Test VAV system generation and simulation"""
    print("=" * 80)
    print("Testing VAV System with Fixed Node Connections")
    print("=" * 80)
    
    # Create IDF Creator with professional mode
    creator = IDFCreator(professional=True, enhanced=True)
    
    # Generate IDF for a small office building
    print("\n1. Generating IDF for Willis Tower, Chicago, IL")
    try:
        # Get location and params
        data = creator.process_inputs(
            address="Willis Tower, Chicago, IL",
            user_params={
                'building_type': 'office',
                'stories': 3,
                'floor_area': 5000
            }
        )
        
        # Generate IDF with advanced HVAC
        idf_content = creator.generate_advanced_idf(
            data,
            hvac_type='vav',
            simple_hvac=False
        )
        print("   ✓ IDF generated successfully")
    except Exception as e:
        print(f"   ✗ IDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Save IDF
    idf_file = "test_vav_final.idf"
    with open(idf_file, 'w') as f:
        f.write(idf_content)
    print(f"   ✓ IDF saved to {idf_file}")
    
    # Run simulation
    print("\n2. Running EnergyPlus simulation")
    try:
        from src.utils.idf_utils import run_energyplus
        success, output_dir = run_energyplus(
            idf_file,
            weather_file="artifacts/desktop_files/weather/Chicago.epw",
            output_directory="test_vav_final_run"
        )
        
        if success:
            print("   ✓ Simulation completed successfully")
            
            # Check for errors
            err_file = f"{output_dir}/eplusout.err"
            with open(err_file, 'r') as f:
                err_content = f.read()
                
            # Count severe errors
            severe_count = err_content.count("** Severe  **")
            fatal_count = err_content.count("**  Fatal  **")
            
            print(f"   ✓ Fatal errors: {fatal_count}")
            print(f"   ⚠ Severe errors: {severe_count}")
            
            if severe_count > 0:
                # Show first few severe errors
                severe_lines = [line for line in err_content.split('\n') if '** Severe  **' in line]
                print("\n   First few severe errors:")
                for line in severe_lines[:5]:
                    print(f"   {line}")
            
            # Check energy results
            csv_file = f"{output_dir}/eplustbl.csv"
            print(f"\n3. Checking energy results from {csv_file}")
            try:
                import pandas as pd
                df = pd.read_csv(csv_file)
                print(f"   ✓ Loaded {len(df)} rows")
                
                # Try to find energy consumption
                if 'Electricity' in df.columns:
                    total_elec = df['Electricity'].sum()
                    print(f"   ✓ Total Electricity: {total_elec:.2f} kWh")
                
                # Look for HVAC-specific energy
                for col in df.columns:
                    if 'heating' in col.lower() or 'cooling' in col.lower() or 'fan' in col.lower():
                        print(f"   - {col}: {df[col].sum():.2f}")
                        
            except Exception as e:
                print(f"   ⚠ Could not read energy results: {e}")
            
            return True
        else:
            print("   ✗ Simulation failed")
            return False
            
    except Exception as e:
        print(f"   ✗ Simulation error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_vav_system()
    sys.exit(0 if success else 1)

