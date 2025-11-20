#!/usr/bin/env python3
"""
Test the full auto-fix process from address to API results
Tests a single location end-to-end
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.auto_fix_engine import AutoFixEngine, WeatherFileInfo

def main():
    """Test full process with a single location"""
    print("="*70)
    print("FULL PROCESS TEST - Address to API Results")
    print("="*70)
    print("\nThis test will:")
    print("1. Find a weather file")
    print("2. Extract address from weather file")
    print("3. Generate IDF file")
    print("4. Run simulation (local or API)")
    print("5. Fix errors automatically")
    print("6. Validate energy results")
    print("7. Show final results")
    print("\n" + "="*70 + "\n")
    
    # Initialize auto-fix engine
    print("🔧 Initializing Auto-Fix Engine...")
    engine = AutoFixEngine(max_iterations=50)  # Run until 0 errors or max 50 iterations
    
    if engine.energyplus_path:
        print(f"✓ Found local EnergyPlus: {engine.energyplus_path}")
    else:
        print("⚠️  Local EnergyPlus not found")
    
    if engine.use_api:
        print(f"✓ API fallback enabled: {engine.api_url}")
    
    print()
    
    # Find weather files
    print("🔍 Finding weather files...")
    weather_files = engine.weather_finder.find_weather_files()
    
    if not weather_files:
        print("❌ No weather files found!")
        print("   Please ensure weather files are in:")
        print("   - artifacts/desktop_files/weather/")
        return 1
    
    print(f"✓ Found {len(weather_files)} weather file(s)")
    
    # Use first weather file for testing
    test_weather = weather_files[0]
    print(f"\n📍 Testing with: {test_weather.address}")
    print(f"   Weather file: {test_weather.filename}")
    print(f"   Path: {test_weather.path}")
    print()
    
    # Process the location
    print("🚀 Starting auto-fix process...\n")
    result = engine.process_single_location(test_weather, "output/test_process")
    
    # Print results
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    print()
    
    if result.get('success'):
        print("✅ SUCCESS!")
        print(f"   Location: {test_weather.address}")
        print(f"   Iterations: {result.get('iterations', 0)}")
        
        final_sim = result.get('final_simulation', {})
        print(f"   Fatal errors: {final_sim.get('fatal_errors', 0)}")
        print(f"   Severe errors: {final_sim.get('severe_errors', 0)}")
        print(f"   Warnings: {final_sim.get('warnings', 0)}")
        
        # Energy validation
        energy_val = result.get('final_energy_validation')
        if energy_val:
            if energy_val.get('is_coherent'):
                print(f"   Energy consistency: ✅ Valid")
            else:
                print(f"   Energy consistency: ⚠️  {energy_val.get('issue_count', 0)} issues")
                print(f"   Warnings: {energy_val.get('warning_count', 0)}")
        
        # Fix history
        fix_history = result.get('fix_history', [])
        if fix_history:
            print(f"\n   Fixes applied ({len(fix_history)}):")
            for fix in fix_history:
                print(f"      Iteration {fix['iteration']}: {fix['type']} - {fix['description']}")
        
        print(f"\n   IDF file: {result.get('idf_path', 'N/A')}")
        
        # Energy results
        energy_results = result.get('energy_results')
        if energy_results:
            print(f"\n   Energy Results:")
            if isinstance(energy_results, dict):
                for key, value in list(energy_results.items())[:10]:
                    print(f"      {key}: {value}")
        
        return 0
    else:
        print("❌ FAILED")
        print(f"   Location: {test_weather.address}")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        
        # Show what we got
        if result.get('iterations', 0) > 0:
            print(f"   Iterations completed: {result.get('iterations', 0)}")
        
        final_sim = result.get('final_simulation', {})
        if final_sim:
            print(f"   Final status: {final_sim.get('success', False)}")
            print(f"   Fatal errors: {final_sim.get('fatal_errors', 0)}")
            print(f"   Severe errors: {final_sim.get('severe_errors', 0)}")
        
        return 1


if __name__ == '__main__':
    sys.exit(main())

