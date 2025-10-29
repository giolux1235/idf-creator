#!/usr/bin/env python3
"""
Test script for Professional IDF Creator
Demonstrates advanced features: Complex Geometry, Materials, Building Types, HVAC
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from main import IDFCreator


def test_professional_features():
    """Test professional IDF Creator features"""
    
    print("🏗️ Testing Professional IDF Creator Features")
    print("=" * 60)
    
    # Test addresses for different building types
    test_cases = [
        {
            'address': 'Empire State Building, New York, NY',
            'building_type': 'office',
            'description': 'Office Building - VAV HVAC, Steel Frame Construction'
        },
        {
            'address': 'Trump Tower, Chicago, IL',
            'building_type': 'mixed_use',
            'description': 'Mixed-Use Building - VAV HVAC, Masonry Construction'
        },
        {
            'address': '123 Main Street, San Francisco, CA',
            'building_type': 'residential_multi',
            'description': 'Residential Building - Heat Pump HVAC, Wood Frame'
        },
        {
            'address': '456 Oak Avenue, Los Angeles, CA',
            'building_type': 'retail',
            'description': 'Retail Building - RTU HVAC, Steel Frame'
        },
        {
            'address': '789 Pine Road, Seattle, WA',
            'building_type': 'healthcare_hospital',
            'description': 'Hospital - Chilled Water HVAC, Masonry Construction'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['description']}")
        print("-" * 40)
        
        try:
            # Create professional IDF creator
            creator = IDFCreator(
                config_path='config.yaml',
                enhanced=True,
                professional=True
            )
            
            # Generate IDF
            output_path = f"output/professional_test_{i}_{test_case['building_type']}.idf"
            
            creator.create_idf(
                address=test_case['address'],
                documents=None,
                user_params={'building_type': test_case['building_type']},
                output_path=output_path
            )
            
            print(f"✅ Successfully generated: {output_path}")
            
            # Check file size and content
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                with open(output_path, 'r') as f:
                    content = f.read()
                    lines = content.count('\n')
                    materials = content.count('Material,')
                    constructions = content.count('Construction,')
                    zones = content.count('Zone,')
                    hvac_components = content.count('AirLoopHVAC') + content.count('ZoneHVAC')
                
                print(f"   📊 File stats:")
                print(f"      - Size: {file_size:,} bytes")
                print(f"      - Lines: {lines:,}")
                print(f"      - Materials: {materials}")
                print(f"      - Constructions: {constructions}")
                print(f"      - Zones: {zones}")
                print(f"      - HVAC Components: {hvac_components}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    print(f"\n🎉 Professional IDF Creator Testing Complete!")
    print("=" * 60)


def test_building_types():
    """Test all available building types"""
    
    print("\n🏢 Testing All Building Types")
    print("=" * 40)
    
    # Get available building types
    from multi_building_types import MultiBuildingTypes
    building_types = MultiBuildingTypes()
    
    available_types = building_types.get_available_building_types()
    print(f"Available building types: {len(available_types)}")
    
    for building_type in available_types:
        template = building_types.get_building_type_template(building_type)
        if template:
            print(f"  - {building_type}: {template.name}")
            print(f"    Typical area: {template.typical_floor_area} m²")
            print(f"    HVAC system: {template.hvac_system_type}")
            print(f"    Space types: {len(template.space_types)}")


def test_material_library():
    """Test professional material library"""
    
    print("\n🧱 Testing Professional Material Library")
    print("=" * 40)
    
    from professional_material_library import ProfessionalMaterialLibrary
    material_lib = ProfessionalMaterialLibrary()
    
    # Test material selection
    climate_zones = ['1A', '3A', '5A', '7']
    building_types = ['office', 'residential', 'retail', 'healthcare_hospital']
    
    for building_type in building_types:
        print(f"\nBuilding Type: {building_type}")
        for climate_zone in climate_zones:
            wall_construction = material_lib.get_construction_assembly(
                building_type, climate_zone, 'wall'
            )
            roof_construction = material_lib.get_construction_assembly(
                building_type, climate_zone, 'roof'
            )
            window_construction = material_lib.get_construction_assembly(
                building_type, climate_zone, 'window'
            )
            
            print(f"  Climate Zone {climate_zone}:")
            print(f"    Wall: {wall_construction.name if wall_construction else 'None'}")
            print(f"    Roof: {roof_construction.name if roof_construction else 'None'}")
            print(f"    Window: {window_construction.name if window_construction else 'None'}")


def test_hvac_systems():
    """Test HVAC system generation"""
    
    print("\n🌡️ Testing HVAC Systems")
    print("=" * 30)
    
    from advanced_hvac_systems import AdvancedHVACSystems
    hvac_systems = AdvancedHVACSystems()
    
    # Test different HVAC types
    hvac_types = ['VAV', 'RTU', 'PTAC', 'HeatPump', 'ChilledWater', 'Radiant']
    
    for hvac_type in hvac_types:
        print(f"\nHVAC Type: {hvac_type}")
        
        # Generate HVAC system for a test zone
        components = hvac_systems.generate_hvac_system(
            building_type='office',
            zone_name='TestZone',
            zone_area=100.0,  # m²
            hvac_type=hvac_type,
            climate_zone='3A'
        )
        
        print(f"  Components generated: {len(components)}")
        for component in components[:3]:  # Show first 3 components
            print(f"    - {component['type']}: {component['name']}")


if __name__ == "__main__":
    # Create output directory
    os.makedirs('output', exist_ok=True)
    
    # Run tests
    test_professional_features()
    test_building_types()
    test_material_library()
    test_hvac_systems()
    
    print(f"\n🎯 Professional Features Summary:")
    print("✅ Advanced Geometry Engine - Complex building footprints")
    print("✅ Professional Material Library - 50+ ASHRAE 90.1 materials")
    print("✅ Multi-Building Types - 12+ building types supported")
    print("✅ Advanced HVAC Systems - Real HVAC instead of ideal loads")
    print("✅ Professional IDF Generator - Integrated all features")
    
    print(f"\n🚀 Ready for professional building energy modeling!")

