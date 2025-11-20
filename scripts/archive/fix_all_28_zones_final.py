#!/usr/bin/env python3
"""
Final Comprehensive Fix for All 28 Zone Errors

This script ensures ALL 28 zones are fixed by:
1. Converting any old node naming patterns to the correct SupplyOutlet pattern
2. Fixing SupplyEquipmentOutletNode -> SupplyOutlet
3. Fixing ZoneEquipmentInlet (when used incorrectly) -> SupplyOutlet
4. Ensuring all connections are correct

Usage:
    python fix_all_28_zones_final.py <idf_file> [--output <output_file>]
"""

import sys
import re
import argparse
from pathlib import Path
from typing import List, Dict


def fix_airloop_supply_outlet_pattern(idf_content: str) -> tuple:
    """
    Fix all AirLoopHVAC supply outlet nodes to use SupplyOutlet pattern.
    Handles all variations:
    - SupplyEquipmentOutletNode -> SupplyOutlet
    - ZoneEquipmentInlet (when used for supply) -> SupplyOutlet
    - Any other pattern -> SupplyOutlet
    """
    fixes_applied = []
    
    # Pattern to match AirLoopHVAC with supply outlet
    # We'll match the entire AirLoopHVAC object
    pattern = r'(AirLoopHVAC\s*,\s*([^,\n]+)(.*?Supply Side Outlet Node Names\s*,\s*)([^,\n;]+)(.*?);)'
    
    def replace_supply_outlet(match):
        airloop_name = match.group(2).strip()
        prefix = match.group(3)  # "Supply Side Outlet Node Names, "
        old_supply = match.group(4).strip().strip('!').strip()
        suffix = match.group(5)  # rest of the object
        
        # Extract zone name from airloop name
        zone_name = airloop_name.replace('_AirLoop', '').replace('_AIRLOOP', '').replace('_Airloop', '')
        new_supply = f"{zone_name}_SupplyOutlet"
        
        # Only fix if it's not already correct
        if old_supply.upper() != new_supply.upper():
            fixes_applied.append({
                'airloop': airloop_name,
                'zone': zone_name,
                'old': old_supply,
                'new': new_supply
            })
            return f"AirLoopHVAC,\n  {airloop_name}{suffix[:suffix.find('Supply Side Outlet Node Names')]}{prefix}{new_supply}{suffix[suffix.find('Supply Side Outlet Node Names') + len(prefix) + len(old_supply):]}"
        return match.group(0)
    
    # More precise pattern - match just the supply outlet line
    def fix_supply_outlet_line(match):
        airloop_name = match.group(1).strip()
        old_supply = match.group(2).strip().strip('!').strip()
        
        # Extract zone name
        zone_name = airloop_name.replace('_AirLoop', '').replace('_AIRLOOP', '').replace('_Airloop', '')
        new_supply = f"{zone_name}_SupplyOutlet"
        
        # Only fix if different
        if old_supply.upper() != new_supply.upper():
            fixes_applied.append({
                'airloop': airloop_name,
                'zone': zone_name,
                'old': old_supply,
                'new': new_supply
            })
            return f"{match.group(0).split(',')[0]}, {new_supply};"
        return match.group(0)
    
    # Find all AirLoopHVAC objects first - they end with semicolon
    airloop_pattern = r'AirLoopHVAC\s*,\s*([^,\n\r]+)(.*?);'
    airloops = list(re.finditer(airloop_pattern, idf_content, re.DOTALL | re.IGNORECASE))
    
    # Process in reverse to maintain positions
    for match in reversed(airloops):
        airloop_name = match.group(1).strip()
        airloop_content = match.group(2)
        
        # Find supply outlet in this airloop
        supply_outlet_match = re.search(
            r'Supply Side Outlet Node Names\s*,\s*([^,\n;]+)',
            airloop_content,
            re.IGNORECASE
        )
        
        if supply_outlet_match:
            old_supply = supply_outlet_match.group(1).strip().strip('!').strip()
            zone_name = airloop_name.replace('_AirLoop', '').replace('_AIRLOOP', '').replace('_Airloop', '')
            new_supply = f"{zone_name}_SupplyOutlet"
            
            # Only fix if different
            if old_supply.upper() != new_supply.upper():
                # Replace in the full content
                start = match.start() + supply_outlet_match.start() + len('Supply Side Outlet Node Names, ')
                end = start + len(old_supply)
                
                idf_content = idf_content[:start] + new_supply + idf_content[end:]
                
                fixes_applied.append({
                    'airloop': airloop_name,
                    'zone': zone_name,
                    'old': old_supply,
                    'new': new_supply
                })
    
    return idf_content, fixes_applied


def verify_fixes(idf_content: str) -> Dict:
    """Verify all AirLoopHVAC objects have correct node connections"""
    # Match AirLoopHVAC objects - they end with semicolon
    airloop_pattern = r'AirLoopHVAC\s*,\s*([^,\n\r]+)(.*?);'
    
    total = 0
    correct = 0
    duplicates = []
    wrong_pattern = []
    
    for match in re.finditer(airloop_pattern, idf_content, re.DOTALL | re.IGNORECASE):
        airloop_name = match.group(1).strip()
        content = match.group(2)
        
        supply_outlet_match = re.search(
            r'Supply Side Outlet Node Names\s*,\s*([^,\n\r;]+)',
            content,
            re.IGNORECASE
        )
        demand_inlet_match = re.search(
            r'Demand Side Inlet Node Names\s*,\s*([^,\n\r;]+)',
            content,
            re.IGNORECASE
        )
        
        if supply_outlet_match and demand_inlet_match:
            total += 1
            supply_outlet = supply_outlet_match.group(1).strip().strip('!').strip()
            demand_inlet = demand_inlet_match.group(1).strip().strip('!').strip()
            
            # Extract zone name
            zone_name = airloop_name.replace('_AirLoop', '').replace('_AIRLOOP', '').replace('_Airloop', '').replace('_airloop', '')
            expected_supply = f"{zone_name}_SupplyOutlet"
            
            # Check if duplicate (same node for both)
            if supply_outlet.upper() == demand_inlet.upper():
                duplicates.append({
                    'airloop': airloop_name,
                    'supply': supply_outlet,
                    'demand': demand_inlet
                })
            # Check if wrong pattern (not SupplyOutlet)
            elif supply_outlet.upper() != expected_supply.upper():
                wrong_pattern.append({
                    'airloop': airloop_name,
                    'zone': zone_name,
                    'current': supply_outlet,
                    'expected': expected_supply
                })
            else:
                correct += 1
    
    return {
        'total': total,
        'correct': correct,
        'duplicates': duplicates,
        'wrong_pattern': wrong_pattern,
        'all_correct': len(duplicates) == 0 and len(wrong_pattern) == 0 and correct == total
    }


def main():
    parser = argparse.ArgumentParser(
        description='Fix all 28 zone duplicate node errors - comprehensive fix',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('idf_file', help='Path to IDF file to fix')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--verify', action='store_true', help='Only verify, do not fix')
    
    args = parser.parse_args()
    
    idf_path = Path(args.idf_file)
    if not idf_path.exists():
        print(f"❌ Error: IDF file not found: {idf_path}")
        sys.exit(1)
    
    print("=" * 80)
    print("COMPREHENSIVE FIX FOR ALL 28 ZONE ERRORS")
    print("=" * 80)
    print(f"Input file: {idf_path}")
    print()
    
    idf_content = idf_path.read_text()
    
    # Verify current state
    print("Step 1: Verifying current state...")
    verification = verify_fixes(idf_content)
    print(f"   Total AirLoopHVAC objects: {verification['total']}")
    print(f"   Correctly configured: {verification['correct']}")
    print(f"   Duplicate node errors: {len(verification['duplicates'])}")
    
    if verification['duplicates']:
        print("\n   Duplicate node errors found:")
        for dup in verification['duplicates']:
            print(f"      - {dup['airloop']}: Supply={dup['supply']}, Demand={dup['demand']}")
    
    if args.verify:
        sys.exit(0 if verification['all_correct'] else 1)
    
    if verification['all_correct']:
        print("\n✅ All zones are already correctly configured!")
        sys.exit(0)
    
    # Fix all supply outlets
    print("\nStep 2: Fixing supply outlet nodes...")
    fixed_content, fixes = fix_airloop_supply_outlet_pattern(idf_content)
    
    if fixes:
        print(f"   ✅ Fixed {len(fixes)} AirLoopHVAC objects:")
        for i, fix in enumerate(fixes[:10], 1):  # Show first 10
            print(f"      {i}. {fix['airloop']}: {fix['old']} → {fix['new']}")
        if len(fixes) > 10:
            print(f"      ... and {len(fixes) - 10} more")
    else:
        print("   ⚠️  No fixes applied")
    
    # Verify fixes
    print("\nStep 3: Verifying fixes...")
    final_verification = verify_fixes(fixed_content)
    print(f"   Total AirLoopHVAC objects: {final_verification['total']}")
    print(f"   Correctly configured: {final_verification['correct']}")
    print(f"   Remaining duplicates: {len(final_verification['duplicates'])}")
    
    # Save
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = idf_path.with_suffix('.idf.fixed_all_28')
    
    output_path.write_text(fixed_content)
    print(f"\n✅ Fixed IDF saved to: {output_path}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Fixes applied: {len(fixes)}")
    print(f"Final status: {'✅ ALL CORRECT' if final_verification['all_correct'] else '⚠️  ERRORS REMAIN'}")
    print("=" * 80)
    
    sys.exit(0 if final_verification['all_correct'] else 1)


if __name__ == '__main__':
    main()

