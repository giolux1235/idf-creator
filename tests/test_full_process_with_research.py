#!/usr/bin/env python3
"""
Complete test: IDF generation → Simulation → Energy results
With internet research capabilities
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.auto_fix_engine import AutoFixEngine, WeatherFileInfo

def main():
    """Test full process with research capabilities"""
    print("="*70)
    print("COMPLETE PROCESS TEST - IDF Generation to Energy Results")
    print("With Internet Research Capabilities")
    print("="*70)
    print("\nThis test will:")
    print("1. Find weather files (or download if missing)")
    print("2. Generate IDF file from address")
    print("3. Run EnergyPlus simulation")
    print("4. Fix errors automatically (with internet research)")
    print("5. Validate energy data consistency")
    print("6. Extract and display energy results")
    print("7. Continue until 0 errors")
    print("\n" + "="*70 + "\n")
    
    # Initialize auto-fix engine with research enabled
    print("🔧 Initializing Auto-Fix Engine with Research...")
    engine = AutoFixEngine(
        max_iterations=50,  # Run until 0 errors or max 50
        use_research=True   # Enable internet research
    )
    
    if engine.energyplus_path:
        print(f"✓ Found local EnergyPlus: {engine.energyplus_path}")
    else:
        print("⚠️  Local EnergyPlus not found")
    
    if engine.use_api:
        print(f"✓ API fallback available: {engine.api_url}")
    
    if engine.use_research:
        print(f"✓ Internet research enabled")
    
    print()
    
    # Find weather files
    print("🔍 Finding weather files...")
    weather_files = engine.weather_finder.find_weather_files()
    
    if not weather_files:
        print("❌ No weather files found!")
        print("   Research will attempt to download weather files...")
        # Try to download a default weather file
        if engine.use_research:
            downloaded = engine.researcher.download_weather_file("Chicago", "IL")
            if downloaded:
                weather_files = [WeatherFileInfo(
                    path=downloaded,
                    filename=Path(downloaded).name,
                    city="Chicago",
                    state="IL",
                    address="Chicago, IL"
                )]
    
    if not weather_files:
        print("❌ Could not find or download weather files")
        return 1
    
    print(f"✓ Found {len(weather_files)} weather file(s)")
    
    # Use first weather file for testing
    test_weather = weather_files[0]
    print(f"\n📍 Testing with: {test_weather.address}")
    print(f"   Weather file: {test_weather.filename}")
    print(f"   Path: {test_weather.path}")
    print()
    
    # Process the location - this will run until 0 errors
    print("🚀 Starting complete auto-fix process...")
    print("   This will continue until 0 errors are achieved\n")
    result = engine.process_single_location(test_weather, "output/test_complete")
    
    # Print comprehensive results
    print("\n" + "="*70)
    print("COMPLETE PROCESS RESULTS")
    print("="*70)
    print()
    
    if result.get('success'):
        print("✅ SUCCESS - Zero Errors Achieved!")
        print(f"   Location: {test_weather.address}")
        print(f"   Total Iterations: {result.get('iterations', 0)}")
        
        final_sim = result.get('final_simulation', {})
        print(f"\n   Final Simulation Status:")
        print(f"      Fatal errors: {final_sim.get('fatal_errors', 0)}")
        print(f"      Severe errors: {final_sim.get('severe_errors', 0)}")
        print(f"      Warnings: {final_sim.get('warnings', 0)}")
        print(f"      Success: {final_sim.get('success', False)}")
        
        # Energy validation
        energy_val = result.get('final_energy_validation')
        if energy_val:
            print(f"\n   Energy Data Validation:")
            if energy_val.get('is_coherent'):
                print(f"      Status: ✅ Consistent")
            else:
                print(f"      Status: ⚠️  {energy_val.get('issue_count', 0)} issues found")
                print(f"      Warnings: {energy_val.get('warning_count', 0)}")
        
        # Energy results
        energy_results = result.get('energy_results')
        if energy_results:
            print(f"\n   Energy Results:")
            if isinstance(energy_results, dict):
                # Extract key metrics
                total_energy = energy_results.get('total_site_energy_kwh') or \
                             energy_results.get('total_energy_kwh') or \
                             energy_results.get('annual_energy_kwh', 'N/A')
                
                if total_energy != 'N/A':
                    print(f"      Total Site Energy: {total_energy:,.2f} kWh/year")
                
                # Show data columns
                columns = energy_results.get('columns', [])
                data = energy_results.get('data', [])
                if columns and data:
                    print(f"      Available Metrics: {len(columns)}")
                    for col in columns[:10]:  # Show first 10
                        if data and col in data[0]:
                            value = data[0].get(col)
                            if isinstance(value, (int, float)):
                                print(f"         {col}: {value:,.2f}")
                            else:
                                print(f"         {col}: {value}")
        
        # Fix history
        fix_history = result.get('fix_history', [])
        if fix_history:
            print(f"\n   Fixes Applied ({len(fix_history)}):")
            for fix in fix_history:
                print(f"      Iteration {fix['iteration']}: {fix['type']}")
                print(f"         → {fix['description']}")
        
        print(f"\n   Output Files:")
        print(f"      IDF: {result.get('idf_path', 'N/A')}")
        if final_sim.get('output_directory'):
            print(f"      Simulation Output: {final_sim.get('output_directory')}")
        
        return 0
    else:
        print("❌ PROCESS COMPLETED WITH ISSUES")
        print(f"   Location: {test_weather.address}")
        print(f"   Iterations: {result.get('iterations', 0)}")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        
        final_sim = result.get('final_simulation', {})
        if final_sim:
            print(f"\n   Final Status:")
            print(f"      Fatal errors: {final_sim.get('fatal_errors', 0)}")
            print(f"      Severe errors: {final_sim.get('severe_errors', 0)}")
            print(f"      Warnings: {final_sim.get('warnings', 0)}")
        
        # Still show what we accomplished
        fix_history = result.get('fix_history', [])
        if fix_history:
            print(f"\n   Fixes Applied ({len(fix_history)}):")
            for fix in fix_history[:10]:  # Show first 10
                print(f"      Iteration {fix['iteration']}: {fix['description'][:80]}")
        
        return 1


if __name__ == '__main__':
    sys.exit(main())

