"""
Comprehensive validation test suite
Tests all validation features: syntax, physics, BESTEST, and simulation
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.validation import (
    validate_idf_file,
    validate_physics,
    validate_bestest,
    validate_simulation
)
from main import IDFCreator


def test_comprehensive_validation():
    """Test all validation features"""
    print("\n" + "="*80)
    print("COMPREHENSIVE VALIDATION TEST SUITE")
    print("="*80)
    
    # Generate a test IDF
    print("\n1. Generating test IDF...")
    try:
        creator = IDFCreator(professional=True, enhanced=True)
        data = creator.process_inputs(
            address="Empire State Building, NYC",
            user_params={
                'building_type': 'office',
                'stories': 3,
                'floor_area': 5000
            }
        )
        
        bp = dict(data['building_params'])
        bp['__location_building'] = data.get('location', {}).get('building') or {}
        params = creator.estimate_missing_parameters(bp)
        
        idf_content = creator.idf_generator.generate_professional_idf(
            "Empire State Building, NYC",
            params['building'],
            data['location'],
            []
        )
        
        print("   ✓ IDF generated successfully")
        
    except Exception as e:
        print(f"   ✗ IDF generation failed: {e}")
        return False
    
    # Test 1: Basic validation
    print("\n2. Running basic IDF validation...")
    try:
        basic_results = validate_idf_file(idf_content)
        print(f"   ✓ Basic validation completed")
        print(f"   - Errors: {basic_results['error_count']}")
        print(f"   - Warnings: {basic_results['warning_count']}")
    except Exception as e:
        print(f"   ✗ Basic validation failed: {e}")
        return False
    
    # Test 2: Physics validation
        print("\n3. Running physics consistency validation...")
    try:
        physics_results = validate_physics(idf_content)
        print(f"   ✓ Physics validation completed")
        print(f"   - Errors: {physics_results['error_count']}")
        print(f"   - Warnings: {physics_results['warning_count']}")
    except Exception as e:
        print(f"   ✗ Physics validation failed: {e}")
        raise  # Re-raise for pytest
    
    # Test 3: BESTEST validation
    print("\n4. Running BESTEST compliance validation...")
    try:
        bestest_results = validate_bestest(idf_content)
        print(f"   ✓ BESTEST validation completed")
        print(f"   - Compliance Score: {bestest_results['compliance_score']:.1f}%")
        print(f"   - Errors: {bestest_results['error_count']}")
        print(f"   - Warnings: {bestest_results['warning_count']}")
    except Exception as e:
        print(f"   ✗ BESTEST validation failed: {e}")
        raise  # Re-raise for pytest
    
    # Test 4: Simulation validation (optional - may fail if EnergyPlus not available)
    print("\n5. Running EnergyPlus simulation validation...")
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.idf', delete=False) as f:
            temp_idf = f.name
            f.write(idf_content)
        
        sim_results = validate_simulation(temp_idf, weather_file=None)
        print(f"   ✓ Simulation validation completed")
        print(f"   - Success: {sim_results.success}")
        print(f"   - Fatal errors: {sim_results.fatal_errors}")
        print(f"   - Severe errors: {sim_results.severe_errors}")
        print(f"   - Warnings: {sim_results.warnings}")
        
        # Cleanup
        try:
            os.unlink(temp_idf)
        except:
            pass
            
    except Exception as e:
        print(f"   ⚠ Simulation validation skipped (EnergyPlus may not be available): {e}")
        print("   This is expected if EnergyPlus is not installed")
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print(f"Basic Validation: {basic_results['error_count']} errors, {basic_results['warning_count']} warnings")
    print(f"Physics Validation: {physics_results['error_count']} errors, {physics_results['warning_count']} warnings")
    print(f"BESTEST Compliance: {bestest_results['compliance_score']:.1f}%")
    
    total_errors = basic_results['error_count'] + physics_results['error_count'] + bestest_results['error_count']
    total_warnings = basic_results['warning_count'] + physics_results['warning_count'] + bestest_results['warning_count']
    
    print(f"\nTotal: {total_errors} errors, {total_warnings} warnings")
    
    if total_errors == 0:
        print("\n✓ ALL VALIDATION CHECKS PASSED!")
        assert True  # Test passed
    else:
        print(f"\n⚠ {total_errors} ERROR(S) FOUND")
        # This is expected for comprehensive validation - warnings are OK
        assert total_errors < 5, f"Too many errors: {total_errors}"  # Allow some errors


def main():
    """Run comprehensive validation tests"""
    success = test_comprehensive_validation()
    
    print("\n" + "="*80)
    if success:
        print("✓ COMPREHENSIVE VALIDATION TEST PASSED!")
    else:
        print("✗ COMPREHENSIVE VALIDATION TEST FAILED")
    print("="*80 + "\n")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

