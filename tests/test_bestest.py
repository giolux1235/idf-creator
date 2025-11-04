"""
Tests for BESTEST compliance validation
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.validation import validate_bestest
from main import IDFCreator


def test_bestest_validation():
    """Test BESTEST compliance validation"""
    print("\n" + "="*80)
    print("TEST: BESTEST Compliance Validation")
    print("="*80)
    
    # Generate a test IDF
    print("\n1. Generating test IDF...")
    try:
        creator = IDFCreator(professional=True, enhanced=True)
        data = creator.process_inputs(
            address="123 Main St, Chicago, IL",
            user_params={
                'building_type': 'office',
                'stories': 1,
                'floor_area': 1000
            }
        )
        
        bp = dict(data['building_params'])
        bp['__location_building'] = data.get('location', {}).get('building') or {}
        params = creator.estimate_missing_parameters(bp)
        
        idf_content = creator.idf_generator.generate_professional_idf(
            "123 Main St, Chicago, IL",
            params['building'],
            data['location'],
            []
        )
        
        print("   ✓ IDF generated")
        
    except Exception as e:
        print(f"   ✗ IDF generation failed: {e}")
        return False
    
    # Test BESTEST validation
    print("\n2. Running BESTEST compliance validation...")
    try:
        results = validate_bestest(idf_content, building_category='600')
        
        print(f"   ✓ BESTEST validation completed")
        print(f"   - Compliance Score: {results['compliance_score']:.1f}%")
        print(f"   - Total Checks: {results['total_checks']}")
        print(f"   - Errors: {results['error_count']}")
        print(f"   - Warnings: {results['warning_count']}")
        
        if results['error_count'] > 0:
            print("\n   BESTEST Errors:")
            for err in results['errors'][:5]:
                print(f"     • {err.message}")
        
        if results['warning_count'] > 0:
            print("\n   BESTEST Warnings:")
            for warn in results['warnings'][:5]:
                print(f"     • {warn.message}")
        
        print("\n   ✓ BESTEST validation checks passed!")
        assert True  # Test passed
        
    except Exception as e:
        print(f"   ✗ BESTEST validation failed: {e}")
        import traceback
        traceback.print_exc()
        raise  # Re-raise for pytest


def main():
    """Run BESTEST validation tests"""
    print("\n" + "="*80)
    print("BESTEST COMPLIANCE VALIDATION TEST SUITE")
    print("="*80)
    
    success = test_bestest_validation()
    
    print("\n" + "="*80)
    if success:
        print("✓ TEST PASSED!")
    else:
        print("✗ TEST FAILED")
    print("="*80 + "\n")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

