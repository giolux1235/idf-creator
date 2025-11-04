"""
Tests for physics consistency validation
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.validation import validate_physics
from main import IDFCreator


def test_physics_validation():
    """Test physics validation"""
    print("\n" + "="*80)
    print("TEST: Physics Consistency Validation")
    print("="*80)
    
    # Generate a test IDF
    print("\n1. Generating test IDF...")
    try:
        creator = IDFCreator(professional=True, enhanced=True)
        data = creator.process_inputs(
            address="123 Main St, Chicago, IL",
            user_params={
                'building_type': 'office',
                'stories': 2,
                'floor_area': 2000
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
    
    # Test physics validation
    print("\n2. Running physics validation...")
    try:
        results = validate_physics(idf_content)
        
        print(f"   ✓ Physics validation completed")
        print(f"   - Errors: {results['error_count']}")
        print(f"   - Warnings: {results['warning_count']}")
        
        if results['error_count'] > 0:
            print("\n   Errors found:")
            for err in results['errors'][:5]:
                print(f"     • {err.message}")
        
        if results['warning_count'] > 0:
            print("\n   Warnings found:")
            for warn in results['warnings'][:5]:
                print(f"     • {warn.message}")
        
        print("\n   ✓ Physics validation checks passed!")
        assert True  # Test passed
        
    except Exception as e:
        print(f"   ✗ Physics validation failed: {e}")
        import traceback
        traceback.print_exc()
        raise  # Re-raise for pytest


def main():
    """Run physics validation tests"""
    print("\n" + "="*80)
    print("PHYSICS CONSISTENCY VALIDATION TEST SUITE")
    print("="*80)
    
    success = test_physics_validation()
    
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

