#!/usr/bin/env python3
"""
Master Validation Script

Runs both code validation and IDF file validation to ensure all fixes are properly applied.

Usage:
    # Validate code only
    python validate_all_fixes.py --code
    
    # Validate IDF file
    python validate_all_fixes.py --idf <idf_file>
    
    # Validate both
    python validate_all_fixes.py --code --idf <idf_file>
    
    # Auto-fix IDF issues
    python validate_all_fixes.py --idf <idf_file> --fix
"""

import sys
import argparse
from pathlib import Path

# Import validators
try:
    from validate_code_fixes import CodeFixValidator
    from validate_energyplus_fixes import IDFValidator, print_results
except ImportError as e:
    print(f"Error importing validators: {e}")
    print("Make sure validate_code_fixes.py and validate_energyplus_fixes.py are in the same directory")
    sys.exit(1)


def validate_code():
    """Run code validation"""
    print("=" * 80)
    print("VALIDATING CODE FIXES")
    print("=" * 80)
    print()
    
    validator = CodeFixValidator()
    results = validator.validate_all()
    validator.print_results(results)
    
    return results['all_passed']


def validate_idf(idf_file: str, auto_fix: bool = False, output: str = None):
    """Run IDF validation"""
    print("=" * 80)
    print("VALIDATING IDF FILE")
    print("=" * 80)
    print()
    
    try:
        validator = IDFValidator(idf_file)
        results = validator.validate_all(auto_fix=auto_fix)
        
        if auto_fix and results.get('fixes_applied'):
            output_path = output or None
            fixed_path = validator.save(output_path)
            if fixed_path:
                results['fixed_file'] = fixed_path
                print(f"\n✅ Fixed IDF saved to: {fixed_path}\n")
        
        print_results(results)
        
        return results['passed']
    except Exception as e:
        print(f"❌ Error validating IDF: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Validate all EnergyPlus fixes (code and IDF)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate code only
  python validate_all_fixes.py --code
  
  # Validate IDF file only
  python validate_all_fixes.py --idf building.idf
  
  # Validate both
  python validate_all_fixes.py --code --idf building.idf
  
  # Validate and fix IDF
  python validate_all_fixes.py --idf building.idf --fix
        """
    )
    parser.add_argument('--code', action='store_true', help='Validate source code fixes')
    parser.add_argument('--idf', help='Path to IDF file to validate')
    parser.add_argument('--fix', action='store_true', help='Automatically fix IDF issues')
    parser.add_argument('--output', help='Output path for fixed IDF file')
    
    args = parser.parse_args()
    
    if not args.code and not args.idf:
        parser.print_help()
        sys.exit(1)
    
    code_passed = True
    idf_passed = True
    
    # Validate code
    if args.code:
        code_passed = validate_code()
        print()
    
    # Validate IDF
    if args.idf:
        idf_passed = validate_idf(args.idf, auto_fix=args.fix, output=args.output)
        print()
    
    # Final summary
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    if args.code:
        status = "✅ PASSED" if code_passed else "❌ FAILED"
        print(f"Code Validation: {status}")
    if args.idf:
        status = "✅ PASSED" if idf_passed else "❌ FAILED"
        print(f"IDF Validation: {status}")
    print("=" * 80)
    print()
    
    # Exit with error if any validation failed
    all_passed = code_passed and idf_passed
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()

