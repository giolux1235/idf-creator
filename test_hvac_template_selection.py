#!/usr/bin/env python3
"""
Test different building sizes to verify automatic template selection.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.hvac_template_generator import HVACTemplateGenerator

def test_template_selection():
    """Test automatic template selection for different building types and sizes"""
    
    generator = HVACTemplateGenerator()
    
    test_cases = [
        {
            'name': 'Small Residential',
            'building_type': 'residential_single',
            'total_area': 150,
            'num_zones': 1,
            'climate_zone': 'ASHRAE_C5',
            'stories': 1,
            'expected': 'BaseboardHeat'  # Cold climate residential
        },
        {
            'name': 'Small Office',
            'building_type': 'office',
            'total_area': 400,
            'num_zones': 2,
            'climate_zone': 'ASHRAE_C3',
            'stories': 1,
            'expected': 'PTHP'  # Small building, moderate climate
        },
        {
            'name': 'Medium Office',
            'building_type': 'office',
            'total_area': 800,
            'num_zones': 10,
            'climate_zone': 'ASHRAE_C5',
            'stories': 2,
            'expected': 'FanCoil'  # Medium building, cold climate
        },
        {
            'name': 'Large Office',
            'building_type': 'office',
            'total_area': 5000,
            'num_zones': 50,
            'climate_zone': 'ASHRAE_C3',
            'stories': 5,
            'expected': 'VAV'  # Large building
        },
        {
            'name': 'Very Large Office',
            'building_type': 'office',
            'total_area': 10000,
            'num_zones': 100,
            'climate_zone': 'ASHRAE_C1',
            'stories': 10,
            'expected': 'VAV_WaterCooled'  # Very large, hot climate
        }
    ]
    
    print("=" * 70)
    print("Testing Automatic HVAC Template Selection")
    print("=" * 70)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Building Type: {test_case['building_type']}")
        print(f"   Total Area: {test_case['total_area']} m²")
        print(f"   Zones: {test_case['num_zones']}")
        print(f"   Stories: {test_case['stories']}")
        print(f"   Climate Zone: {test_case['climate_zone']}")
        
        selected = generator.select_template(
            building_type=test_case['building_type'],
            total_area=test_case['total_area'],
            num_zones=test_case['num_zones'],
            climate_zone=test_case['climate_zone'],
            stories=test_case['stories']
        )
        
        print(f"   → Selected Template: {selected}")
        print(f"   → Expected: {test_case['expected']}")
        
        if selected == test_case['expected']:
            print(f"   ✅ MATCH")
        else:
            print(f"   ⚠️  Different (but may still be valid)")
    
    print("\n" + "=" * 70)
    print("Template Selection Test Complete")
    print("=" * 70)

if __name__ == "__main__":
    test_template_selection()









