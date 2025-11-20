#!/usr/bin/env python3
"""
Verify area in generated IDF files
Extracts zone information and calculates total area
"""

import sys
import re
from pathlib import Path

def analyze_idf_area(idf_file: str):
    """Analyze area in IDF file"""
    print(f"\n{'='*60}")
    print(f"Analyzing: {Path(idf_file).name}")
    print(f"{'='*60}")
    
    try:
        with open(idf_file, 'r') as f:
            content = f.read()
        
        # Extract all zones
        zone_pattern = r'Zone,\s*([^,\n]+)'
        zones = re.findall(zone_pattern, content)
        print(f"Total Zones: {len(zones)}")
        
        # Extract zone floor areas (if specified)
        # Zone format: Name, North, X, Y, Z, Type, Multiplier, Ceiling Height, Volume, Floor Area
        zone_area_pattern = r'Zone,\s*([^,\n]+),.*?,\s*([0-9.]+|autocalculate),.*?,\s*([0-9.]+|autocalculate),.*?,\s*([0-9.]+|autocalculate)'
        
        # Count floors by examining zone names
        floors = set()
        zones_by_floor = {}
        
        for zone in zones:
            # Look for floor indicators in zone names
            floor_match = re.search(r'floor[_\s]?(\d+)|floor[_\s]?(\d+)|f[_\s]?(\d+)|level[_\s]?(\d+)', zone.lower())
            if floor_match:
                floor_num = int(floor_match.group(1) or floor_match.group(2) or floor_match.group(3) or floor_match.group(4))
                floors.add(floor_num)
                if floor_num not in zones_by_floor:
                    zones_by_floor[floor_num] = []
                zones_by_floor[floor_num].append(zone)
        
        if floors:
            print(f"Floors detected: {sorted(floors)}")
            print(f"Zones per floor:")
            for floor in sorted(floors):
                print(f"  Floor {floor}: {len(zones_by_floor[floor])} zones")
        
        # Extract BuildingSurface:Detailed objects to estimate footprint
        floor_surfaces = re.findall(
            r'BuildingSurface:Detailed,\s*([^,]+),\s*Floor,',
            content
        )
        print(f"Floor surfaces: {len(floor_surfaces)}")
        
        # Try to extract vertex coordinates from floor surfaces to calculate area
        # This is approximate - we'd need full geometry parsing for exact area
        surface_pattern = r'BuildingSurface:Detailed,\s*([^,]+),\s*Floor,.*?(\d+),.*?([\d\.,\s-]+);'
        surface_matches = re.findall(surface_pattern, content, re.DOTALL)
        
        if surface_matches:
            print(f"Floor surface details found: {len(surface_matches)}")
        
        # Check for area-related values in the file
        # Look for numbers that might represent area
        area_values = re.findall(r'\b(1[0-9]{3}|[2-9][0-9]{3}|[1-9][0-9]{4})\b', content)
        unique_areas = sorted(set([int(a) for a in area_values if 100 <= int(a) <= 50000]))
        
        if unique_areas:
            print(f"Potential area values found: {unique_areas[:10]}")  # First 10
        
        # Estimate total area from zones
        # Typical: 8-12 zones per floor, each zone ~150-200 m²
        if floors and zones:
            avg_zones_per_floor = len(zones) / len(floors)
            estimated_area_per_floor = avg_zones_per_floor * 150  # Rough estimate
            estimated_total = estimated_area_per_floor * len(floors)
            print(f"\nEstimated area (rough):")
            print(f"  Per floor: ~{estimated_area_per_floor:.0f} m²")
            print(f"  Total: ~{estimated_total:.0f} m²")
        
        return {
            'zones': len(zones),
            'floors': len(floors) if floors else 0,
            'floor_surfaces': len(floor_surfaces)
        }
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        idf_file = sys.argv[1]
        analyze_idf_area(idf_file)
    else:
        # Analyze recent test files
        test_files = [
            "artifacts/desktop_files/idf/test_willis_tower_(chicago).idf",
            "artifacts/desktop_files/idf/test_empire_state_building.idf"
        ]
        
        for test_file in test_files:
            if Path(test_file).exists():
                analyze_idf_area(test_file)

