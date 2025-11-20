#!/usr/bin/env python3
"""
Test Retrofit Optimization Module
Tests the enhanced retrofit optimization features
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.retrofit_optimizer import RetrofitOptimizer, UtilityRates
import tempfile
import shutil

def test_retrofit_optimization():
    """Test retrofit optimization with sample data"""
    print("="*70)
    print("TEST: Retrofit Optimization")
    print("="*70)
    
    # Initialize optimizer
    optimizer = RetrofitOptimizer()
    
    if not optimizer.energyplus_path:
        print("⚠️  EnergyPlus not found. Will test scenario generation only.")
        print("   Install EnergyPlus for full simulation testing.")
        energyplus_available = False
    else:
        print(f"✅ EnergyPlus found: {optimizer.energyplus_path}")
        energyplus_available = True
    
    # Find test IDF and weather files
    test_idf = None
    test_weather = None
    
    # Look for test files
    possible_idf_locations = [
        'artifacts/test_simulation',
        'test_outputs',
        'output',
        '.'
    ]
    
    possible_weather_locations = [
        'EnergyPlus-MCP/energyplus-mcp-server/sample_files',
        'artifacts/desktop_files/weather',
        'weather_files',
        '.'
    ]
    
    # Find IDF file
    for loc in possible_idf_locations:
        if os.path.exists(loc):
            for file in Path(loc).glob('*.idf'):
                test_idf = str(file)
                print(f"✅ Found test IDF: {test_idf}")
                break
        if test_idf:
            break
    
    # Find weather file
    for loc in possible_weather_locations:
        if os.path.exists(loc):
            for file in Path(loc).glob('*.epw'):
                test_weather = str(file)
                print(f"✅ Found test weather: {test_weather}")
                break
        if test_weather:
            break
    
    # Also check EnergyPlus installation directory
    if not test_weather:
        import subprocess
        try:
            result = subprocess.run(['which', 'energyplus'], capture_output=True, text=True)
            if result.returncode == 0:
                energyplus_bin = result.stdout.strip()
                weather_dirs = [
                    '/Applications/EnergyPlus-24-2-0/EnergyPlus installation files/WeatherData',
                    '/Applications/EnergyPlus-24-2-0/weather',
                    '/usr/local/EnergyPlus-24-2-0/weather',
                    '/opt/EnergyPlus/weather',
                    str(Path(energyplus_bin).parent.parent / 'weather'),
                ]
                for wdir in weather_dirs:
                    if os.path.exists(wdir):
                        for file in Path(wdir).glob('*.epw'):
                            test_weather = str(file)
                            print(f"✅ Found EnergyPlus weather: {test_weather}")
                            break
                        if test_weather:
                            break
        except:
            pass
    
    if not test_idf:
        print("⚠️  No IDF file found. Creating minimal test IDF...")
        test_idf = create_minimal_test_idf()
    
    # Test 1: Scenario Generation
    print("\n" + "="*70)
    print("TEST 1: Scenario Generation")
    print("="*70)
    
    try:
        scenarios = optimizer.generate_scenarios(
            baseline_energy_kwh=500000,  # 500 MWh/year
            floor_area_sf=50000,  # 50,000 sq ft
            baseline_idf_path=test_idf,
            building_type='office',
            max_measures_per_scenario=3  # Limit for testing
        )
        
        print(f"✅ Generated {len(scenarios)} retrofit scenarios")
        
        # Display first 5 scenarios
        print("\n📋 Sample Scenarios:")
        for i, scenario in enumerate(scenarios[:5], 1):
            print(f"\n  {i}. {scenario.description}")
            print(f"     Measures: {len(scenario.measures)}")
            print(f"     Estimated Savings: {scenario.energy_savings_percent:.1f}%")
            print(f"     Estimated Savings: {scenario.energy_savings_kwh:,.0f} kWh")
            print(f"     Implementation Cost: ${scenario.implementation_cost:,.0f}")
        
        print("\n✅ Scenario Generation Test: PASSED")
        
    except Exception as e:
        print(f"\n❌ Scenario Generation Test: FAILED")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Economic Analysis
    print("\n" + "="*70)
    print("TEST 2: Economic Analysis")
    print("="*70)
    
    try:
        utility_rates = UtilityRates(
            electricity_rate_kwh=0.12,
            demand_rate_kw=15.0,
            escalation_rate=0.03
        )
        
        # Calculate economics for first 5 scenarios
        for scenario in scenarios[:5]:
            scenario.calculate_economics(utility_rates)
        
        print("✅ Economic calculations completed")
        
        print("\n📊 Economic Analysis Results:")
        for i, scenario in enumerate(scenarios[:5], 1):
            print(f"\n  {i}. {scenario.description[:50]}...")
            if scenario.annual_savings:
                print(f"     Annual Savings: ${scenario.annual_savings:,.0f}")
            if scenario.payback_years:
                print(f"     Payback: {scenario.payback_years:.1f} years")
            if scenario.roi:
                print(f"     ROI: {scenario.roi:.1f}%")
            if scenario.npv:
                print(f"     NPV (20-year): ${scenario.npv:,.0f}")
        
        print("\n✅ Economic Analysis Test: PASSED")
        
    except Exception as e:
        print(f"\n❌ Economic Analysis Test: FAILED")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Optimization
    print("\n" + "="*70)
    print("TEST 3: Optimization")
    print("="*70)
    
    try:
        optimized = optimizer.optimize(
            scenarios=scenarios,
            utility_rates=utility_rates,
            budget=500000,  # $500K budget
            max_payback=10.0  # 10 year max payback
        )
        
        print(f"✅ Optimized to {len(optimized)} scenarios within constraints")
        
        print("\n📊 Top 5 Optimized Scenarios (by NPV):")
        for i, scenario in enumerate(optimized[:5], 1):
            print(f"\n  {i}. {scenario.description[:50]}...")
            print(f"     NPV: ${scenario.npv:,.0f}")
            print(f"     ROI: {scenario.roi:.1f}%")
            print(f"     Payback: {scenario.payback_years:.1f} years")
        
        print("\n✅ Optimization Test: PASSED")
        
    except Exception as e:
        print(f"\n❌ Optimization Test: FAILED")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Simulation (if EnergyPlus available)
    if energyplus_available and test_weather:
        print("\n" + "="*70)
        print("TEST 4: Scenario Simulations")
        print("="*70)
        
        # Create temporary output directory
        output_dir = Path(tempfile.mkdtemp(prefix='retrofit_test_'))
        print(f"📁 Output directory: {output_dir}")
        
        try:
            # Test with first 3 scenarios only (to save time)
            test_scenarios = scenarios[:3]
            
            print(f"\n🔄 Running simulations for {len(test_scenarios)} scenarios...")
            print("   (This may take several minutes)")
            
            simulated_scenarios = optimizer.run_scenario_simulations(
                scenarios=test_scenarios,
                baseline_idf_path=test_idf,
                weather_file=test_weather,
                output_dir=str(output_dir),
                max_concurrent=2  # 2 concurrent for testing
            )
            
            print("\n📊 Simulation Results:")
            for i, scenario in enumerate(simulated_scenarios, 1):
                print(f"\n  {i}. {scenario.description[:50]}...")
                if scenario.simulated_energy_kwh:
                    print(f"     Simulated Energy: {scenario.simulated_energy_kwh:,.0f} kWh")
                    print(f"     Energy Savings: {scenario.energy_savings_kwh:,.0f} kWh")
                    print(f"     Savings: {scenario.energy_savings_percent:.1f}%")
                else:
                    print(f"     ⚠️  Simulation failed, using estimated savings")
            
            print("\n✅ Simulation Test: PASSED")
            
        except Exception as e:
            print(f"\n❌ Simulation Test: FAILED")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Cleanup
            if os.path.exists(output_dir):
                print(f"\n🧹 Cleaning up: {output_dir}")
                shutil.rmtree(output_dir, ignore_errors=True)
    else:
        print("\n⚠️  Skipping simulation test (EnergyPlus or weather file not available)")
    
    # Test 5: Report Generation
    print("\n" + "="*70)
    print("TEST 5: Report Generation")
    print("="*70)
    
    try:
        report = optimizer.generate_report(optimized[:10], top_n=5)
        print("✅ Report generated")
        print("\n📄 Report Preview:")
        print(report[:500] + "..." if len(report) > 500 else report)
        
        print("\n✅ Report Generation Test: PASSED")
        
    except Exception as e:
        print(f"\n❌ Report Generation Test: FAILED")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*70)
    print("✅ ALL RETROFIT OPTIMIZATION TESTS: PASSED")
    print("="*70)
    return True

def create_minimal_test_idf():
    """Create a minimal test IDF file"""
    test_idf = Path('test_minimal_retrofit.idf')
    
    minimal_idf_content = """Version,9.6.0;

Building,
  Test Building,
  0.0,
  Suburbs,
  0.04,
  0.4,
  FullExterior,
  25,
  6;

Zone,
  Test Zone,
  0.0,
  0.0,
  0.0,
  0.0,
  1.0,
  100.0,
  ,
  1.0;

Lights,
  Test Lights,
  Test Zone,
  Always On,
  Watts per Zone Floor Area,
  10.0,
  0.2,
  0.0,
  0.0;

ElectricEquipment,
  Test Equipment,
  Test Zone,
  Always On,
  Watts per Zone Floor Area,
  5.0,
  0.0,
  0.0,
  0.0;

ZoneInfiltration:DesignFlowRate,
  Test Infiltration,
  Test Zone,
  Always On,
  Flow/Zone,
  0.1,
  0.0,
  0.0;

Schedule:Constant,
  Always On,
  ,
  1.0;
"""
    
    with open(test_idf, 'w') as f:
        f.write(minimal_idf_content)
    
    print(f"   Created minimal IDF: {test_idf}")
    return str(test_idf)

if __name__ == '__main__':
    success = test_retrofit_optimization()
    sys.exit(0 if success else 1)

