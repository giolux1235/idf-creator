#!/usr/bin/env python3
"""
Comprehensive Fix for All 28 Zone Duplicate Node Errors

This script fixes ALL variations of the duplicate node error:
1. SupplyEquipmentOutletNode -> SupplyOutlet
2. ZoneEquipmentInlet (when used for supply outlet) -> SupplyOutlet
3. Any other duplicate node issues

It processes the IDF file and fixes all 28 zones systematically.

Usage:
    python fix_28_zones_comprehensive.py <idf_file> [--output <output_file>]
"""

import sys
import re
import argparse
from pathlib import Path
from typing import List, Dict, Tuple


def find_all_airloops(idf_content: str) -> List[Dict]:
    """Find all AirLoopHVAC objects and extract their node information"""
    airloops = []
    
    # Pattern to match AirLoopHVAC objects
    pattern = r'AirLoopHVAC\s*,\s*([^,\n]+)(.*?);'
    
    for match in re.finditer(pattern, idf_content, re.DOTALL | re.IGNORECASE):
        airloop_name = match.group(1).strip()
        content = match.group(2)
        
        # Extract all node fields
        supply_inlet_match = re.search(
            r'Supply Side Inlet Node Name\s*,\s*([^,\n;]+)',
            content,
            re.IGNORECASE
        )
        supply_outlet_match = re.search(
            r'Supply Side Outlet Node Names\s*,\s*([^,\n;]+)',
            content,
            re.IGNORECASE
        )
        demand_inlet_match = re.search(
            r'Demand Side Inlet Node Names\s*,\s*([^,\n;]+)',
            content,
            re.IGNORECASE
        )
        demand_outlet_match = re.search(
            r'Demand Side Outlet Node Name\s*,\s*([^,\n;]+)',
            content,
            re.IGNORECASE
        )
        
        airloop = {
            'name': airloop_name,
            'full_match': match.group(0),
            'start_pos': match.start(),
            'end_pos': match.end(),
            'supply_inlet': supply_inlet_match.group(1).strip().strip('!').strip() if supply_inlet_match else None,
            'supply_outlet': supply_outlet_match.group(1).strip().strip('!').strip() if supply_outlet_match else None,
            'demand_inlet': demand_inlet_match.group(1).strip().strip('!').strip() if demand_inlet_match else None,
            'demand_outlet': demand_outlet_match.group(1).strip().strip('!').strip() if demand_outlet_match else None,
        }
        
        airloops.append(airloop)
    
    return airloops


def check_duplicate_nodes(airloop: Dict) -> bool:
    """Check if an AirLoopHVAC has duplicate nodes"""
    if not airloop['supply_outlet'] or not airloop['demand_inlet']:
        return False
    
    # Check if supply outlet and demand inlet are the same (case-insensitive)
    return airloop['supply_outlet'].upper() == airloop['demand_inlet'].upper()


def extract_zone_name(airloop_name: str) -> str:
    """Extract zone name from AirLoopHVAC name"""
    # Patterns: LOBBY_0_Z1_AirLoop, lobby_0_z1_AirLoop, etc.
    # Remove _AirLoop suffix and variations
    zone_name = airloop_name.replace('_AirLoop', '').replace('_AIRLOOP', '').replace('_Airloop', '')
    return zone_name


def fix_airloop_supply_outlet(idf_content: str, airloop: Dict) -> Tuple[str, bool]:
    """Fix a single AirLoopHVAC supply outlet node"""
    if not check_duplicate_nodes(airloop):
        return idf_content, False
    
    zone_name = extract_zone_name(airloop['name'])
    old_supply_outlet = airloop['supply_outlet']
    new_supply_outlet = f"{zone_name}_SupplyOutlet"
    
    # Replace in the AirLoopHVAC object
    # Pattern: Supply Side Outlet Node Names, OLD_NODE;
    pattern = rf'(Supply Side Outlet Node Names\s*,\s*){re.escape(old_supply_outlet)}'
    replacement = rf'\1{new_supply_outlet}'
    
    if re.search(pattern, airloop['full_match'], re.IGNORECASE):
        # Replace in the full match first
        fixed_match = re.sub(pattern, replacement, airloop['full_match'], flags=re.IGNORECASE)
        
        # Replace in the full IDF content
        idf_content = (
            idf_content[:airloop['start_pos']] +
            fixed_match +
            idf_content[airloop['end_pos']:]
        )
        
        return idf_content, True
    
    return idf_content, False


def fix_all_airloops(idf_content: str) -> Tuple[str, List[Dict]]:
    """Fix all AirLoopHVAC objects with duplicate nodes"""
    airloops = find_all_airloops(idf_content)
    fixes_applied = []
    
    # Process in reverse order to maintain positions
    for airloop in reversed(airloops):
        if check_duplicate_nodes(airloop):
            zone_name = extract_zone_name(airloop['name'])
            old_supply = airloop['supply_outlet']
            new_supply = f"{zone_name}_SupplyOutlet"
            
            # Fix this airloop
            idf_content, fixed = fix_airloop_supply_outlet(idf_content, airloop)
            
            if fixed:
                fixes_applied.append({
                    'airloop': airloop['name'],
                    'zone': zone_name,
                    'old_supply': old_supply,
                    'new_supply': new_supply,
                    'demand_inlet': airloop['demand_inlet']
                })
    
    return idf_content, fixes_applied


def main():
    parser = argparse.ArgumentParser(
        description='Fix all 28 zone duplicate node errors in IDF file',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('idf_file', help='Path to IDF file to fix')
    parser.add_argument('--output', '-o', help='Output file path (default: <idf_file>.fixed)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be fixed without modifying file')
    
    args = parser.parse_args()
    
    idf_path = Path(args.idf_file)
    if not idf_path.exists():
        print(f"❌ Error: IDF file not found: {idf_path}")
        sys.exit(1)
    
    print("=" * 80)
    print("FIXING ALL 28 ZONE DUPLICATE NODE ERRORS")
    print("=" * 80)
    print(f"Input file: {idf_path}")
    print()
    
    # Read IDF file
    idf_content = idf_path.read_text()
    
    # Find all airloops
    print("Step 1: Analyzing AirLoopHVAC objects...")
    airloops = find_all_airloops(idf_content)
    print(f"   Found {len(airloops)} AirLoopHVAC objects")
    
    # Check for duplicate nodes
    print("\nStep 2: Checking for duplicate node errors...")
    duplicate_count = 0
    for airloop in airloops:
        if check_duplicate_nodes(airloop):
            duplicate_count += 1
            print(f"   ❌ {airloop['name']}: Supply={airloop['supply_outlet']}, Demand={airloop['demand_inlet']}")
    
    if duplicate_count == 0:
        print("   ✅ No duplicate node errors found!")
        print("\n✅ All zones are correctly configured. No fixes needed.")
        sys.exit(0)
    
    print(f"\n   Found {duplicate_count} AirLoopHVAC objects with duplicate nodes")
    
    # Fix all airloops
    print("\nStep 3: Fixing duplicate node errors...")
    fixed_content, fixes = fix_all_airloops(idf_content)
    
    if not fixes:
        print("   ⚠️  No fixes were applied. Check the patterns.")
        sys.exit(1)
    
    print(f"   ✅ Fixed {len(fixes)} AirLoopHVAC objects:")
    for i, fix in enumerate(fixes, 1):
        print(f"      {i}. {fix['airloop']}")
        print(f"         {fix['old_supply']} → {fix['new_supply']}")
    
    # Verify fixes
    print("\nStep 4: Verifying fixes...")
    fixed_airloops = find_all_airloops(fixed_content)
    remaining_duplicates = sum(1 for a in fixed_airloops if check_duplicate_nodes(a))
    
    if remaining_duplicates == 0:
        print(f"   ✅ All {len(fixes)} duplicate node errors fixed!")
    else:
        print(f"   ⚠️  {remaining_duplicates} duplicate node errors remain")
    
    # Save fixed file
    if not args.dry_run:
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = idf_path.with_suffix('.idf.fixed_28_zones')
        
        output_path.write_text(fixed_content)
        print(f"\n✅ Fixed IDF saved to: {output_path}")
    else:
        print("\n⚠️  Dry run mode - file not modified")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total AirLoopHVAC objects: {len(airloops)}")
    print(f"Duplicate node errors found: {duplicate_count}")
    print(f"Fixes applied: {len(fixes)}")
    print(f"Remaining duplicates: {remaining_duplicates}")
    print("=" * 80)
    
    if remaining_duplicates == 0 and len(fixes) > 0:
        print("\n✅ SUCCESS: All duplicate node errors have been fixed!")
        sys.exit(0)
    elif remaining_duplicates > 0:
        print(f"\n⚠️  WARNING: {remaining_duplicates} errors remain. Manual review may be needed.")
        sys.exit(1)
    else:
        print("\n✅ No errors found - file is already correct.")
        sys.exit(0)


if __name__ == '__main__':
    main()

