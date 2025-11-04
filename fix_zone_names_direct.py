#!/usr/bin/env python3
"""
Direct IDF zone name fixer - fixes ALL zone name mismatches in one pass
"""

import re
import sys
from pathlib import Path

def fix_zone_names_in_idf(idf_path: str) -> str:
    """Fix all zone name mismatches in IDF file"""
    content = Path(idf_path).read_text()
    
    # Find all valid zone names
    valid_zones = {}
    for line in content.split('\n'):
        if line.strip().startswith('Zone,'):
            zone_name = line.split(',')[1].strip().split('!')[0].strip()
            if zone_name:
                valid_zones[zone_name.lower()] = zone_name
    
    print(f"Found {len(valid_zones)} valid zones: {list(valid_zones.values())[:5]}")
    
    # Find all ZoneControl:Thermostat objects and fix zone names
    lines = content.split('\n')
    new_lines = []
    i = 0
    fixed_count = 0
    
    while i < len(lines):
        line = lines[i]
        if 'ZoneControl:Thermostat,' in line:
            # Collect thermostat object
            thermostat_lines = [line]
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                thermostat_lines.append(next_line)
                if next_line.strip().endswith(';'):
                    j += 1
                    break
                j += 1
            
            # Extract zone name from second line (zone name field)
            if len(thermostat_lines) >= 2:
                zone_line = thermostat_lines[1]
                zone_ref = zone_line.split(',')[0].strip().split('!')[0].strip()
                zone_ref_lower = zone_ref.lower()
                
                # Check if zone needs fixing
                if zone_ref_lower not in valid_zones:
                    # Remove _z suffix
                    zone_base = re.sub(r'_z\d+$', '', zone_ref_lower, flags=re.IGNORECASE)
                    if zone_base in valid_zones:
                        best_zone = valid_zones[zone_base]
                        # Fix the zone name
                        leading_ws = len(zone_line) - len(zone_line.lstrip())
                        parts = zone_line.split(',')
                        parts[0] = ' ' * leading_ws + best_zone + ','
                        thermostat_lines[1] = ','.join(parts)
                        fixed_count += 1
                        print(f"  Fixed: {zone_ref} -> {best_zone}")
            
            new_lines.extend(thermostat_lines)
            i = j
        else:
            new_lines.append(line)
            i += 1
    
    print(f"\nFixed {fixed_count} zone name references")
    return '\n'.join(new_lines)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python fix_zone_names_direct.py <idf_file>")
        sys.exit(1)
    
    idf_file = sys.argv[1]
    fixed_content = fix_zone_names_in_idf(idf_file)
    
    output_file = idf_file.replace('.idf', '_zone_fixed.idf')
    Path(output_file).write_text(fixed_content)
    print(f"Saved fixed IDF to: {output_file}")

