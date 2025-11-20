#!/usr/bin/env python3
"""
Simple Direct Fix for All 28 Zone Errors

Directly replaces SupplyEquipmentOutletNode with SupplyOutlet pattern.
"""

import sys
import re
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_28_zones_simple.py <idf_file> [output_file]")
        sys.exit(1)
    
    idf_path = Path(sys.argv[1])
    if not idf_path.exists():
        print(f"Error: File not found: {idf_path}")
        sys.exit(1)
    
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else idf_path.with_suffix('.idf.fixed_28')
    
    print(f"Reading: {idf_path}")
    content = idf_path.read_text()
    
    # Find all supply outlet nodes - format: NODENAME; !- Supply Side Outlet Node Names
    # Or: Supply Side Outlet Node Names, NODENAME;
    pattern1 = r'([^,\n;]+)\s*;\s*!-\s*Supply Side Outlet Node Names'
    pattern2 = r'Supply Side Outlet Node Names\s*,\s*([^,\n;]+)'
    
    matches1 = list(re.finditer(pattern1, content, re.IGNORECASE))
    matches2 = list(re.finditer(pattern2, content, re.IGNORECASE))
    
    # Combine matches - pattern1 gives node name in group 1, pattern2 also in group 1
    matches = []
    for m in matches1:
        matches.append((m.start(), m.group(1).strip(), m.end()))
    for m in matches2:
        matches.append((m.start(), m.group(1).strip().strip('!').strip(), m.end()))
    
    # Sort by position (reverse for processing)
    matches.sort(key=lambda x: x[0], reverse=True)
    
    print(f"Found {len(matches)} supply outlet nodes")
    
    fixes = 0
    # Process in reverse to maintain positions
    for start_pos, old_node, end_pos in matches:
        # Find the AirLoopHVAC name (look backwards)
        before = content[:start_pos]
        airloop_match = re.search(r'AirLoopHVAC\s*,\s*([^,\n]+)', before[-1000:], re.IGNORECASE)
        
        if airloop_match:
            airloop_name = airloop_match.group(1).strip()
            zone_name = airloop_name.replace('_AirLoop', '').replace('_AIRLOOP', '').replace('_Airloop', '').replace('_airloop', '')
            new_node = f"{zone_name}_SupplyOutlet"
            
            if old_node.upper() != new_node.upper():
                # Replace the node name
                content = content[:start_pos] + new_node + content[end_pos:]
                fixes += 1
                if fixes <= 10:
                    print(f"  Fixed: {airloop_name} - {old_node} -> {new_node}")
    
    if fixes > 10:
        print(f"  ... and {fixes - 10} more")
    
    print(f"\nFixed {fixes} supply outlet nodes")
    output_path.write_text(content)
    print(f"Saved to: {output_path}")

if __name__ == '__main__':
    main()

