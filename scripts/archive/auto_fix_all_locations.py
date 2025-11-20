#!/usr/bin/env python3
"""
Automatic Fix Script for All Weather File Locations
Finds all weather files, generates IDFs, runs simulations,
and automatically fixes errors iteratively.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

from src.auto_fix_engine import AutoFixEngine


def main():
    """Main function to run auto-fix for all locations"""
    print("="*70)
    print("IDF Creator - Automatic Fix Engine")
    print("="*70)
    print("\nThis script will:")
    print("1. Find all weather files on this machine")
    print("2. Extract location information (city, state, address)")
    print("3. Generate IDF files for each location")
    print("4. Run EnergyPlus simulations")
    print("5. Detect and fix errors automatically")
    print("6. Verify energy data consistency")
    print("7. Iterate until all issues are resolved")
    print("\n" + "="*70 + "\n")
    
    # Initialize auto-fix engine
    engine = AutoFixEngine(max_iterations=10)
    
    # Check if EnergyPlus is available
    if not engine.energyplus_path:
        print("⚠️  WARNING: EnergyPlus not found in PATH")
        if engine.use_api:
            print(f"   Will use EnergyPlus API: {engine.api_url}")
        else:
            print("   Simulations will be skipped, but IDF files will still be generated.")
            print("   Install EnergyPlus or add it to PATH to enable full auto-fix.\n")
    else:
        print(f"✓ Found EnergyPlus: {engine.energyplus_path}")
        if engine.use_api:
            print(f"✓ API fallback available: {engine.api_url}")
        print()
    
    # Process all weather files
    output_dir = "output/auto_fixed"
    print(f"📁 Output directory: {output_dir}\n")
    
    results = engine.process_all_weather_files(output_dir)
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        return 1
    
    success_count = 0
    total_count = len(results)
    
    for address, result in results.items():
        if result.get('success'):
            success_count += 1
            print(f"\n✅ {address}")
            print(f"   Iterations: {result.get('iterations', 0)}")
            print(f"   Fatal errors: {result['final_simulation']['fatal_errors']}")
            print(f"   Severe errors: {result['final_simulation']['severe_errors']}")
            print(f"   Warnings: {result['final_simulation']['warnings']}")
            
            if result.get('final_energy_validation'):
                energy_val = result['final_energy_validation']
                if energy_val.get('is_coherent'):
                    print(f"   Energy consistency: ✅ Valid")
                else:
                    print(f"   Energy consistency: ⚠️  {energy_val.get('issue_count', 0)} issues")
            
            print(f"   IDF file: {result.get('idf_path', 'N/A')}")
        else:
            print(f"\n❌ {address}")
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    print(f"\n{'='*70}")
    print(f"Results: {success_count}/{total_count} locations fixed successfully")
    print(f"{'='*70}\n")
    
    # Save results to JSON
    results_file = Path(output_dir) / "results.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert results to JSON-serializable format
    json_results = {}
    for address, result in results.items():
        json_results[address] = {
            'success': result.get('success', False),
            'iterations': result.get('iterations', 0),
            'fix_history': result.get('fix_history', []),
            'final_simulation': {
                'fatal_errors': result['final_simulation']['fatal_errors'],
                'severe_errors': result['final_simulation']['severe_errors'],
                'warnings': result['final_simulation']['warnings'],
                'success': result['final_simulation']['success']
            },
            'idf_path': result.get('idf_path', ''),
            'error': result.get('error', '')
        }
    
    with open(results_file, 'w') as f:
        json.dump(json_results, f, indent=2)
    
    print(f"📄 Detailed results saved to: {results_file}")
    
    return 0 if success_count == total_count else 1


if __name__ == '__main__':
    sys.exit(main())

