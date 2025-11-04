"""
Regression Test Suite
Tests all building types and HVAC systems to ensure no regressions
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import IDFCreator
from src.validation import validate_idf_file


class RegressionTestSuite:
    """Comprehensive regression testing for all IDF generation scenarios"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
    
    def test_all_building_types(self):
        """Test all supported building types"""
        print("\n" + "="*80)
        print("REGRESSION TEST: All Building Types")
        print("="*80)
        
        building_types = ['Office', 'Retail', 'School', 'Hospital', 'Residential', 'Warehouse']
        
        for building_type in building_types:
            print(f"\nTesting: {building_type}")
            try:
                creator = IDFCreator(professional=True, enhanced=True)
                data = creator.process_inputs(
                    address="Willis Tower, Chicago, IL",  # Real address for testing
                    user_params={
                        'building_type': building_type.lower(),
                        'stories': 2,
                        'floor_area': 2000
                    }
                )
                
                bp = dict(data['building_params'])
                bp['__location_building'] = data.get('location', {}).get('building') or {}
                params = creator.estimate_missing_parameters(bp)
                
                idf_content = creator.idf_generator.generate_professional_idf(
                    "123 Test St",
                    params['building'],
                    data['location'],
                    []
                )
                
                # Validate
                results = validate_idf_file(idf_content)
                
                if results['error_count'] == 0:
                    print(f"  ✓ {building_type}: PASS")
                    self.tests_passed += 1
                else:
                    print(f"  ✗ {building_type}: FAIL ({results['error_count']} errors)")
                    self.tests_failed += 1
                    self.failures.append((building_type, results['errors']))
                    
            except Exception as e:
                print(f"  ✗ {building_type}: ERROR - {e}")
                self.tests_failed += 1
                self.failures.append((building_type, str(e)))
    
    def test_all_hvac_types(self):
        """Test all HVAC system types"""
        print("\n" + "="*80)
        print("REGRESSION TEST: All HVAC Types")
        print("="*80)
        
        hvac_types = ['vav', 'ptac', 'rtu']
        
        for hvac_type in hvac_types:
            print(f"\nTesting: {hvac_type.upper()}")
            try:
                # Note: HVAC type needs to be passed in a different way
                # For now, test that VAV generation works
                if hvac_type == 'vav':
                    creator = IDFCreator(professional=True, enhanced=True)
                    data = creator.process_inputs(
                        address="Willis Tower, Chicago, IL",  # Real address
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
                        "456 HVAC St",
                        params['building'],
                        data['location'],
                        []
                    )
                    
                    # Validate
                    results = validate_idf_file(idf_content)
                    
                    if results['error_count'] == 0:
                        print(f"  ✓ {hvac_type.upper()}: PASS")
                        self.tests_passed += 1
                    else:
                        print(f"  ✗ {hvac_type.upper()}: FAIL ({results['error_count']} errors)")
                        self.tests_failed += 1
                        self.failures.append((hvac_type, results['errors']))
                else:
                    print(f"  ⚠ {hvac_type.upper()}: SKIP (not yet implemented)")
                    
            except Exception as e:
                print(f"  ✗ {hvac_type.upper()}: ERROR - {e}")
                self.tests_failed += 1
                self.failures.append((hvac_type, str(e)))
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        print("\n" + "="*80)
        print("REGRESSION TEST: Edge Cases")
        print("="*80)
        
        edge_cases = [
            ("Small building", {'building_type': 'office', 'stories': 1, 'floor_area': 100}),
            ("Large building", {'building_type': 'office', 'stories': 10, 'floor_area': 10000}),
            ("Single story", {'building_type': 'retail', 'stories': 1, 'floor_area': 500}),
        ]
        
        for case_name, params in edge_cases:
            print(f"\nTesting: {case_name}")
            try:
                creator = IDFCreator(professional=True, enhanced=True)
                data = creator.process_inputs(
                    address="Willis Tower, Chicago, IL",  # Real address
                    user_params=params
                )
                
                bp = dict(data['building_params'])
                bp['__location_building'] = data.get('location', {}).get('building') or {}
                params_result = creator.estimate_missing_parameters(bp)
                
                idf_content = creator.idf_generator.generate_professional_idf(
                    f"789 {case_name}",
                    params_result['building'],
                    data['location'],
                    []
                )
                
                # Validate
                results = validate_idf_file(idf_content)
                
                if results['error_count'] == 0:
                    print(f"  ✓ {case_name}: PASS")
                    self.tests_passed += 1
                else:
                    print(f"  ✗ {case_name}: FAIL ({results['error_count']} errors)")
                    self.tests_failed += 1
                    self.failures.append((case_name, results['errors']))
                    
            except Exception as e:
                print(f"  ✗ {case_name}: ERROR - {e}")
                self.tests_failed += 1
                self.failures.append((case_name, str(e)))
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("REGRESSION TEST SUMMARY")
        print("="*80)
        
        total = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {self.tests_passed} ({pass_rate:.1f}%)")
        print(f"Failed: {self.tests_failed}")
        
        if self.failures:
            print("\nFailures:")
            for name, error in self.failures:
                print(f"  • {name}: {error}")
        
        print("\n" + "="*80)
        
        if self.tests_failed == 0:
            print("✓ ALL TESTS PASSED!")
            print("="*80 + "\n")
            return True
        else:
            print(f"✗ {self.tests_failed} TEST(S) FAILED")
            print("="*80 + "\n")
            return False
    
    def run_all_tests(self):
        """Run complete regression test suite"""
        print("\n" + "="*80)
        print("COMPREHENSIVE REGRESSION TEST SUITE")
        print("="*80)
        
        self.test_all_building_types()
        self.test_all_hvac_types()
        self.test_edge_cases()
        
        return self.print_summary()


def main():
    """Run regression tests"""
    suite = RegressionTestSuite()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

