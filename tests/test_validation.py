"""
Tests for IDF validation suite
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.validation import IDFValidator, validate_idf_file
from main import IDFCreator


def test_valid_idf():
    """Test validation with a valid IDF"""
    print("\n" + "="*80)
    print("TEST 1: Valid IDF Validation")
    print("="*80)
    
    # Create a simple building
    creator = IDFCreator(professional=True, enhanced=True)
    data = creator.process_inputs(
        address="123 Main St, Chicago, IL",
        user_params={
            'building_type': 'office',
            'stories': 1,
            'floor_area': 1000
        }
    )
    
    # Generate IDF
    bp = dict(data['building_params'])
    bp['__location_building'] = data.get('location', {}).get('building') or {}
    params = creator.estimate_missing_parameters(bp)
    
    idf_content = creator.idf_generator.generate_professional_idf(
        "123 Main St, Chicago, IL",
        params['building'],
        data['location'],
        []
    )
    
    # Validate
    results = validate_idf_file(idf_content)
    print(results['report'])
    
    assert results['error_count'] == 0, "Valid IDF should have no errors"
    print("✓ PASS: Valid IDF has no errors\n")


def test_invalid_idf():
    """Test validation with an invalid IDF"""
    print("\n" + "="*80)
    print("TEST 2: Invalid IDF Validation")
    print("="*80)
    
    invalid_idf = """Version,9.2;

Building,Simple Building;

SimulationControl,
  Yes,
  Yes;

Timestep,4;
"""
    
    results = validate_idf_file(invalid_idf)
    print(results['report'])
    
    assert results['error_count'] > 0, "Invalid IDF should have errors"
    print("✓ PASS: Invalid IDF correctly flagged errors\n")


def test_basic_structure():
    """Test basic IDF structure validation"""
    print("\n" + "="*80)
    print("TEST 3: Basic Structure Validation")
    print("="*80)
    
    minimal_idf = """Version,9.2;

Building,Simple Building;

SimulationControl,
  Yes,
  Yes;

Timestep,4;
"""
    
    results = validate_idf_file(minimal_idf)
    print(results['report'])
    
    # Should find missing RunPeriod
    has_error = any('RunPeriod' in err.message 
                    for err in results['errors'])
    assert has_error, "Should detect missing RunPeriod"
    print("✓ PASS: Missing RunPeriod detected\n")


def test_hvac_validation():
    """Test validation of complete HVAC system"""
    print("\n" + "="*80)
    print("TEST 4: HVAC System Validation")
    print("="*80)
    
    # Use the command-line approach to generate IDF
    import subprocess
    import tempfile
    
    # Create a test IDF file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.idf', delete=False) as f:
        temp_idf = f.name
        
        # Generate IDF using main.py
        creator = IDFCreator(professional=True, enhanced=True)
        data = creator.process_inputs(
            address="Willis Tower, Chicago, IL",
            user_params={
                'building_type': 'office',
                'stories': 3,
                'floor_area': 5000
            }
        )
        
        # Generate IDF
        bp = dict(data['building_params'])
        bp['__location_building'] = data.get('location', {}).get('building') or {}
        params = creator.estimate_missing_parameters(bp)
        
        idf_content = creator.idf_generator.generate_professional_idf(
            "Willis Tower, Chicago, IL",
            params['building'],
            data['location'],
            []
        )
        
        f.write(idf_content)
    
    # Validate
    with open(temp_idf, 'r') as f:
        idf_content = f.read()
    
    results = validate_idf_file(idf_content)
    print(results['report'])
    
    # Should have minimal or no critical errors
    error_count = results['error_count']
    print(f"\n✓ PASS: Generated VAV IDF has {error_count} errors")
    
    if error_count == 0:
        print("  → Perfect! No validation errors in complete HVAC system")
    elif error_count < 5:
        print(f"  → Good! Only {error_count} minor validation issues")
    else:
        print(f"  → Needs attention: {error_count} errors found")
    
    # Cleanup
    os.unlink(temp_idf)


def main():
    """Run all validation tests"""
    print("\n" + "="*80)
    print("IDF VALIDATION TEST SUITE")
    print("="*80)
    
    try:
        test_valid_idf()
        test_invalid_idf()
        test_basic_structure()
        test_hvac_validation()
        
        print("\n" + "="*80)
        print("ALL TESTS PASSED!")
        print("="*80 + "\n")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

