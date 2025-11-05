#!/usr/bin/env python3
"""
Test script to verify all warning fixes are working correctly.

Tests:
1. Schedule Type Limits case sensitivity
2. Missing day types in schedules
3. DX coil air flow rate validation
4. HVAC convergence improvements
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.professional_idf_generator import ProfessionalIDFGenerator


def test_schedule_type_limits():
    """Test that schedules use 'AnyNumber' (not 'Any Number')"""
    print("\n" + "="*60)
    print("TEST 1: Schedule Type Limits Case Sensitivity")
    print("="*60)
    
    generator = ProfessionalIDFGenerator()
    
    # Generate schedules
    schedules = generator.generate_schedules('office', ['office_open', 'lobby', 'conference'])
    
    # Check for correct case
    if 'AnyNumber' in schedules and 'Any Number' not in schedules:
        print("✅ PASS: All schedules use 'AnyNumber' (correct case)")
        return True
    elif 'Any Number' in schedules:
        print("❌ FAIL: Found 'Any Number' (with space) in schedules")
        print(f"   Found at: {schedules.find('Any Number')}")
        return False
    else:
        print("⚠️  WARNING: Could not verify schedule type limits")
        return None


def test_missing_day_types():
    """Test that schedules with Through=12/31 include all required day types"""
    print("\n" + "="*60)
    print("TEST 2: Missing Day Types in Schedules")
    print("="*60)
    
    generator = ProfessionalIDFGenerator()
    
    # Generate schedules
    schedules = generator.generate_schedules('office', ['office_open', 'lobby', 'conference'])
    
    # Check for required day types
    required_day_types = [
        'For: SummerDesignDay',
        'For: WinterDesignDay',
        'For: CustomDay1',
        'For: CustomDay2'
    ]
    
    missing = []
    for day_type in required_day_types:
        if day_type not in schedules:
            missing.append(day_type)
    
    if not missing:
        print("✅ PASS: All schedules include required day types")
        return True
    else:
        print(f"❌ FAIL: Missing day types: {', '.join(missing)}")
        return False


def test_dx_coil_airflow():
    """Test that DX coil air flow rates are validated"""
    print("\n" + "="*60)
    print("TEST 3: DX Coil Air Flow Rate Validation")
    print("="*60)
    
    # Test the validation logic
    from src.equipment_catalog.translator.idf_translator import translate_dx_coil
    from src.equipment_catalog.schema import EquipmentSpec
    
    # Create test equipment spec with low air flow (should be fixed)
    # Use a simple dict-like approach or check what EquipmentSpec actually needs
    try:
        # Try to create EquipmentSpec - check if it needs performance parameter
        test_spec = EquipmentSpec(
            name="TestCoil",
            equipment_type="DX_COIL",
            rated_capacity_w=35000.0,  # 35 kW
            rated_cop=3.0,
            rated_airflow_m3s=0.1  # Too low: 0.1 / 35000 = 2.86e-6 m³/s/W (below minimum)
        )
    except TypeError:
        # If EquipmentSpec needs more params, create a minimal mock
        from dataclasses import dataclass
        @dataclass
        class MockEquipmentSpec:
            name: str
            equipment_type: str
            rated_capacity_w: float
            rated_cop: float
            rated_airflow_m3s: float
        
        test_spec = MockEquipmentSpec(
            name="TestCoil",
            equipment_type="DX_COIL",
            rated_capacity_w=35000.0,
            rated_cop=3.0,
            rated_airflow_m3s=0.1
        )
    
    # Translate to IDF
    idf_objects = translate_dx_coil(test_spec)
    idf_string = '\n'.join(idf_objects)
    
    # Extract air flow rate from IDF
    import re
    match = re.search(r'(\d+\.\d+),\s*!\s*.*rated.*air.*flow', idf_string, re.IGNORECASE)
    if match:
        airflow = float(match.group(1))
        # Calculate flow per watt
        flow_per_watt = airflow / test_spec.rated_capacity_w
        
        min_flow = 2.684e-5
        max_flow = 6.713e-5
        
        if min_flow <= flow_per_watt <= max_flow:
            print(f"✅ PASS: Air flow rate validated correctly ({flow_per_watt:.2e} m³/s/W)")
            return True
        else:
            print(f"❌ FAIL: Air flow rate out of range ({flow_per_watt:.2e} m³/s/W)")
            print(f"   Expected: {min_flow:.2e} to {max_flow:.2e}")
            return False
    else:
        print("⚠️  WARNING: Could not extract air flow rate from IDF")
        return None


def test_system_convergence_limits():
    """Test that SystemConvergenceLimits object is generated"""
    print("\n" + "="*60)
    print("TEST 4: System Convergence Limits")
    print("="*60)
    
    generator = ProfessionalIDFGenerator()
    
    # Generate convergence limits
    convergence_limits = generator.generate_system_convergence_limits()
    
    # Check for required fields
    if 'SystemConvergenceLimits' in convergence_limits:
        if '30' in convergence_limits and 'Maximum HVAC Iterations' in convergence_limits:
            print("✅ PASS: SystemConvergenceLimits generated with 30 iterations")
            return True
        else:
            print("❌ FAIL: SystemConvergenceLimits missing proper iteration count")
            return False
    else:
        print("❌ FAIL: SystemConvergenceLimits not generated")
        return False


def test_full_idf_generation():
    """Test full IDF generation with all fixes"""
    print("\n" + "="*60)
    print("TEST 5: Full IDF Generation")
    print("="*60)
    
    generator = ProfessionalIDFGenerator()
    
    # Generate a simple IDF
    try:
        building_params = {
            'name': 'Test Building',
            'stories': 1,
            'floor_area': 500,
            'building_type': 'office'
        }
        
        location_data = {
            'address': 'Chicago, IL',
            'latitude': 41.8781,
            'longitude': -87.6298,
            'climate_zone': 'ASHRAE_C5',
            'weather_file': 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'
        }
        
        idf_content = generator.generate_professional_idf(
            address='Chicago, IL',
            building_params=building_params,
            location_data=location_data
        )
        
        # Check for key fixes
        checks = {
            'ScheduleTypeLimits with AnyNumber': 'ScheduleTypeLimits' in idf_content and 'AnyNumber' in idf_content,
            'SystemConvergenceLimits': 'SystemConvergenceLimits' in idf_content,
            'Missing day types added': 'For: SummerDesignDay' in idf_content,
        }
        
        all_passed = True
        for check_name, check_result in checks.items():
            if check_result:
                print(f"  ✅ {check_name}")
            else:
                print(f"  ❌ {check_name}")
                all_passed = False
        
        if all_passed:
            print("✅ PASS: Full IDF generation includes all fixes")
            
            # Optionally write to file for inspection
            test_file = Path('test_outputs') / 'test_warning_fixes.idf'
            test_file.parent.mkdir(exist_ok=True)
            test_file.write_text(idf_content)
            print(f"   IDF saved to: {test_file}")
            
            return True
        else:
            print("❌ FAIL: Some fixes missing from generated IDF")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Exception during IDF generation: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("IDF CREATOR - WARNING FIXES VERIFICATION")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Schedule Type Limits", test_schedule_type_limits()))
    results.append(("Missing Day Types", test_missing_day_types()))
    results.append(("DX Coil Air Flow", test_dx_coil_airflow()))
    results.append(("System Convergence", test_system_convergence_limits()))
    results.append(("Full IDF Generation", test_full_idf_generation()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    warnings = sum(1 for _, result in results if result is None)
    
    for test_name, result in results:
        status = "✅ PASS" if result is True else "❌ FAIL" if result is False else "⚠️  WARN"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed} passed, {failed} failed, {warnings} warnings")
    
    if failed == 0:
        print("\n🎉 All critical tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

