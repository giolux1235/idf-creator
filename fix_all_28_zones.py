#!/usr/bin/env python3
"""
Fix All 28 Zone Duplicate Node Errors

This script programmatically fixes all 28 duplicate node errors by:
1. Verifying the code fixes are correct
2. Testing with a generated IDF
3. Validating all zones have correct node connections
4. Reporting any remaining issues

Usage:
    python fix_all_28_zones.py
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from validate_code_fixes import CodeFixValidator
from validate_energyplus_fixes import IDFValidator


def check_airloop_nodes_in_idf(idf_content: str) -> List[Dict]:
    """Check all AirLoopHVAC objects for duplicate node errors"""
    errors = []
    
    # Find all AirLoopHVAC objects
    airloop_pattern = r'AirLoopHVAC\s*,\s*([^,\n]+)(.*?);'
    
    for match in re.finditer(airloop_pattern, idf_content, re.DOTALL | re.IGNORECASE):
        airloop_name = match.group(1).strip()
        airloop_content = match.group(2)
        
        # Extract supply outlet and demand inlet nodes
        supply_outlet_match = re.search(
            r'Supply Side Outlet Node Names\s*,\s*([^,\n;]+)',
            airloop_content,
            re.IGNORECASE
        )
        demand_inlet_match = re.search(
            r'Demand Side Inlet Node Names\s*,\s*([^,\n;]+)',
            airloop_content,
            re.IGNORECASE
        )
        
        if supply_outlet_match and demand_inlet_match:
            supply_outlet = supply_outlet_match.group(1).strip().strip('!').strip()
            demand_inlet = demand_inlet_match.group(1).strip().strip('!').strip()
            
            # Check if they're the same (case-insensitive)
            if supply_outlet.upper() == demand_inlet.upper():
                # Check if supply outlet is ZoneEquipmentInlet (wrong)
                if 'ZONEEQUIPMENTINLET' in supply_outlet.upper():
                    errors.append({
                        'airloop': airloop_name,
                        'supply_outlet': supply_outlet,
                        'demand_inlet': demand_inlet,
                        'issue': 'duplicate_node'
                    })
    
    return errors


def fix_idf_airloop_nodes(idf_content: str) -> Tuple[str, List[str]]:
    """Fix all duplicate node errors in IDF content"""
    fixes_applied = []
    
    # Find all AirLoopHVAC objects with duplicate nodes
    errors = check_airloop_nodes_in_idf(idf_content)
    
    for error in errors:
        airloop_name = error['airloop']
        old_supply = error['supply_outlet']
        
        # Extract zone name from airloop name
        # Pattern: LOBBY_0_Z1_AirLoop -> LOBBY_0_Z1
        zone_match = re.match(r'([^_]+(?:_\d+)*_[Z]\d+)', airloop_name, re.IGNORECASE)
        if zone_match:
            zone_name = zone_match.group(1)
        else:
            # Fallback: remove _AirLoop suffix
            zone_name = airloop_name.replace('_AirLoop', '').replace('_AIRLOOP', '').replace('_Airloop', '')
        
        new_supply_outlet = f"{zone_name}_SupplyOutlet"
        
        # Replace in AirLoopHVAC object
        # Pattern: Supply Side Outlet Node Names, OLD_NODE;
        pattern = rf'(Supply Side Outlet Node Names\s*,\s*){re.escape(old_supply)}'
        replacement = rf'\1{new_supply_outlet}'
        
        if re.search(pattern, idf_content, re.IGNORECASE):
            idf_content = re.sub(pattern, replacement, idf_content, flags=re.IGNORECASE)
            fixes_applied.append(f"Fixed {airloop_name}: {old_supply} -> {new_supply_outlet}")
    
    return idf_content, fixes_applied


def main():
    print("=" * 80)
    print("FIXING ALL 28 ZONE DUPLICATE NODE ERRORS")
    print("=" * 80)
    print()
    
    # Step 1: Validate code fixes
    print("Step 1: Validating code fixes...")
    code_validator = CodeFixValidator()
    code_results = code_validator.validate_all()
    
    if not code_results['all_passed']:
        print("❌ Code validation failed! Fix code issues first.")
        code_validator.print_results(code_results)
        sys.exit(1)
    
    print("✅ Code validation passed")
    print()
    
    # Step 2: Check if we have an IDF file to test
    print("Step 2: Looking for IDF files to validate...")
    idf_files = list(Path("test_outputs").glob("**/*.idf")) + \
                list(Path("artifacts/desktop_files/idf").glob("*.idf"))
    
    if not idf_files:
        print("⚠️  No IDF files found to test. Generate a new IDF file first.")
        print("   Run: python main.py create_idf --address '123 Main St, Chicago, IL'")
        sys.exit(0)
    
    # Test with the first IDF file
    test_idf = idf_files[0]
    print(f"Testing with: {test_idf}")
    print()
    
    # Step 3: Check for duplicate node errors
    print("Step 3: Checking for duplicate node errors...")
    idf_content = test_idf.read_text()
    errors = check_airloop_nodes_in_idf(idf_content)
    
    if not errors:
        print("✅ No duplicate node errors found!")
        print("   All zones are correctly configured.")
        sys.exit(0)
    
    print(f"❌ Found {len(errors)} duplicate node errors:")
    for i, error in enumerate(errors, 1):
        print(f"   {i}. {error['airloop']}: Supply={error['supply_outlet']}, Demand={error['demand_inlet']}")
    print()
    
    # Step 4: Fix all errors
    print("Step 4: Fixing all duplicate node errors...")
    fixed_content, fixes = fix_idf_airloop_nodes(idf_content)
    
    if fixes:
        print(f"✅ Fixed {len(fixes)} AirLoopHVAC objects:")
        for fix in fixes:
            print(f"   - {fix}")
        print()
        
        # Save fixed file
        fixed_path = test_idf.with_suffix('.idf.fixed_28_zones')
        fixed_path.write_text(fixed_content)
        print(f"✅ Fixed IDF saved to: {fixed_path}")
        print()
        
        # Step 5: Validate fixed file
        print("Step 5: Validating fixed IDF...")
        validator = IDFValidator(str(fixed_path))
        results = validator.validate_all()
        
        if results['passed']:
            print("✅ Fixed IDF passes validation!")
        else:
            print(f"⚠️  Fixed IDF still has {len(results['errors'])} errors")
            for error in results['errors']:
                print(f"   - {error['message']}")
    else:
        print("⚠️  No fixes were applied. Check the error patterns.")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Code Validation: {'✅ PASSED' if code_results['all_passed'] else '❌ FAILED'}")
    print(f"Duplicate Node Errors Found: {len(errors)}")
    print(f"Fixes Applied: {len(fixes)}")
    print("=" * 80)
    print()
    
    if errors and not fixes:
        print("⚠️  WARNING: Errors found but no fixes applied.")
        print("   This may indicate the IDF was generated with old code.")
        print("   Generate a new IDF file with the fixed code.")
        sys.exit(1)
    
    if not errors:
        print("✅ SUCCESS: All 28 zones are correctly configured!")
        sys.exit(0)
    else:
        print(f"⚠️  {len(errors)} errors remain. Check the fixed file.")
        sys.exit(1)


if __name__ == '__main__':
    main()

