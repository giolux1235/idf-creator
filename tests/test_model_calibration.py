#!/usr/bin/env python3
"""
Test Model Calibration Module
Tests the enhanced model calibration features
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.model_calibration import ModelCalibrator, UtilityData
import tempfile
import shutil

def test_model_calibration():
    """Test model calibration with sample data"""
    print("="*70)
    print("TEST: Model Calibration")
    print("="*70)
    
    # Find EnergyPlus
    calibrator = ModelCalibrator()
    
    if not calibrator.energyplus_path:
        print("❌ EnergyPlus not found. Skipping simulation tests.")
        print("   Install EnergyPlus or set ENERGYPLUS_PATH environment variable.")
        return False
    
    print(f"✅ EnergyPlus found: {calibrator.energyplus_path}")
    
    # Check for test IDF and weather files
    test_idf = None
    test_weather = None
    
    # Look for test files in common locations
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
    
    # Find IDF file - prefer existing files over minimal
    for loc in possible_idf_locations:
        if os.path.exists(loc):
            for file in Path(loc).glob('*.idf'):
                # Skip minimal test files
                if 'minimal' not in str(file).lower():
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
            # Try to find EnergyPlus weather directory
            result = subprocess.run(['which', 'energyplus'], capture_output=True, text=True)
            if result.returncode == 0:
                energyplus_bin = result.stdout.strip()
                # Common weather locations relative to binary
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
    
    if not test_weather:
        print("❌ No weather file found. Cannot run calibration test.")
        print("   Please provide a .epw weather file.")
        print("   You can download one from: https://energyplus.net/weather")
        return False
    
    # Create sample utility data
    print("\n📊 Creating sample utility data...")
    utility_data = UtilityData(
        monthly_kwh=[
            45000, 42000, 38000, 35000,  # Winter (high heating)
            32000, 30000, 28000, 30000,   # Spring/Summer
            32000, 35000, 40000, 44000     # Fall/Winter
        ],
        peak_demand_kw=850,
        heating_fuel='electric',
        cooling_fuel='electric',
        electricity_rate_kwh=0.12
    )
    
    print(f"   Annual consumption: {utility_data.annual_kwh():,.0f} kWh")
    print(f"   Monthly average: {utility_data.monthly_average_kwh():,.0f} kWh")
    
    # Create temporary output directory
    output_dir = Path(tempfile.mkdtemp(prefix='calibration_test_'))
    print(f"\n📁 Output directory: {output_dir}")
    
    try:
        print("\n🔄 Running calibration test...")
        print("   (This may take a few minutes)")
        
        result = calibrator.calibrate_to_utility_bills(
            idf_file=test_idf,
            utility_data=utility_data,
            weather_file=test_weather,
            tolerance=0.15,  # 15% tolerance for testing
            max_iterations=5,  # Limit iterations for testing
            output_dir=str(output_dir)
        )
        
        print("\n" + "="*70)
        print("CALIBRATION RESULTS")
        print("="*70)
        print(f"✅ Calibrated IDF: {result.calibrated_idf_path}")
        print(f"✅ Report: {result.calibration_report_path}")
        print(f"📊 Annual Error: {result.accuracy_annual:.2f}%")
        print(f"📊 Monthly MBE: {result.accuracy_monthly_mbe:.2f}%")
        print(f"📊 Monthly CVRMSE: {result.accuracy_monthly_cvrmse:.2f}%")
        print(f"🔄 Iterations: {result.iterations}")
        print(f"✅ Converged: {result.converged}")
        
        # Check ASHRAE Guideline 14 compliance
        ashrae_compliant = result.accuracy_monthly_cvrmse <= 15.0
        print(f"\n📋 ASHRAE Guideline 14 Compliance:")
        print(f"   CVRMSE < 15%: {ashrae_compliant} ({result.accuracy_monthly_cvrmse:.2f}%)")
        
        if result.adjusted_parameters:
            print(f"\n🔧 Adjusted Parameters:")
            for param, value in result.adjusted_parameters.items():
                print(f"   {param}: {value:.3f}")
        
        # Read and display report summary
        if os.path.exists(result.calibration_report_path):
            import json
            with open(result.calibration_report_path, 'r') as f:
                report = json.load(f)
            
            print(f"\n📄 Report Summary:")
            summary = report.get('calibration_summary', {})
            print(f"   Baseline: {summary.get('baseline_annual_kwh', 0):,.0f} kWh")
            print(f"   Calibrated: {summary.get('calibrated_annual_kwh', 0):,.0f} kWh")
            print(f"   Actual: {summary.get('actual_annual_kwh', 0):,.0f} kWh")
        
        print("\n✅ Model Calibration Test: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Model Calibration Test: FAILED")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if os.path.exists(output_dir):
            print(f"\n🧹 Cleaning up: {output_dir}")
            shutil.rmtree(output_dir, ignore_errors=True)

def create_minimal_test_idf():
    """Create a minimal test IDF file"""
    test_idf = Path('test_minimal.idf')
    
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
    success = test_model_calibration()
    sys.exit(0 if success else 1)

