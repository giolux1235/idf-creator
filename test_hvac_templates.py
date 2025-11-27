#!/usr/bin/env python3
"""
Test script to verify HVAC Templates are being used automatically.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.professional_idf_generator import ProfessionalIDFGenerator
from src.enhanced_location_fetcher import EnhancedLocationFetcher

def test_hvac_templates():
    """Test that HVAC Templates are generated automatically"""
    
    print("=" * 70)
    print("Testing HVAC Template System")
    print("=" * 70)
    
    # Initialize components
    generator = ProfessionalIDFGenerator()
    location_fetcher = EnhancedLocationFetcher()
    
    # Test with Chicago address (we have weather file for it)
    test_address = "Willis Tower, Chicago, IL"
    print(f"\n📍 Testing with address: {test_address}")
    
    # Fetch location data
    print("\n🔍 Fetching location data...")
    location_data = location_fetcher.fetch_comprehensive_location_data(test_address)
    print(f"✓ Location: {location_data.get('address', 'N/A')}")
    print(f"✓ Coordinates: {location_data.get('latitude', 'N/A'):.4f}, {location_data.get('longitude', 'N/A'):.4f}")
    print(f"✓ Climate Zone: {location_data.get('climate_zone', 'N/A')}")
    print(f"✓ Weather File: {location_data.get('weather_file', 'N/A')}")
    
    # Building parameters - small office building
    building_params = {
        'name': 'Test Office Building',
        'building_type': 'office',
        'stories': 2,
        'floor_area': 800,  # 800 m² total (400 m² per floor)
        'window_to_wall_ratio': 0.4,
        'use_hvac_templates': False  # Should use templates automatically
    }
    
    print(f"\n🏗️  Building Parameters:")
    print(f"   Type: {building_params['building_type']}")
    print(f"   Stories: {building_params['stories']}")
    print(f"   Total Area: {building_params['floor_area']} m²")
    
    # Generate IDF
    print("\n⚙️  Generating IDF with HVAC Templates...")
    try:
        idf_content = generator.generate_professional_idf(
            address=test_address,
            building_params=building_params,
            location_data=location_data
        )
        
        # Save to file for inspection
        output_file = Path("artifacts/test_hvac_templates.idf")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(idf_content)
        print(f"✓ IDF generated: {output_file}")
        
        # Check for HVAC Template objects
        print("\n🔍 Checking for HVAC Template objects in IDF...")
        
        template_objects_found = []
        template_types = [
            'HVACTemplate:Thermostat',
            'HVACTemplate:Zone:IdealLoadsAirSystem',
            'HVACTemplate:Zone:PTAC',
            'HVACTemplate:Zone:PTHP',
            'HVACTemplate:Zone:VAV',
            'HVACTemplate:Zone:FanCoil',
            'HVACTemplate:System:VAV',
            'HVACTemplate:System:PackagedVAV',
            'HVACTemplate:Plant:ChilledWaterLoop',
            'HVACTemplate:Plant:HotWaterLoop',
            'HVACTemplate:Plant:Chiller',
            'HVACTemplate:Plant:Boiler',
            'HVACTemplate:Plant:Tower'
        ]
        
        for template_type in template_types:
            if template_type in idf_content:
                count = idf_content.count(template_type)
                template_objects_found.append((template_type, count))
                print(f"   ✓ Found {count} x {template_type}")
        
        if template_objects_found:
            print(f"\n✅ SUCCESS: Found {len(template_objects_found)} HVAC Template object types!")
            print("\n📋 Template Objects Found:")
            for obj_type, count in template_objects_found:
                print(f"   - {obj_type}: {count}")
        else:
            print("\n⚠️  WARNING: No HVAC Template objects found!")
            print("   Checking if detailed HVAC objects are present instead...")
            
            # Check for detailed HVAC objects
            detailed_objects = [
                'AirLoopHVAC',
                'ZoneHVAC:PackagedTerminalAirConditioner',
                'Coil:Cooling:DX:SingleSpeed',
                'Fan:VariableVolume'
            ]
            
            found_detailed = []
            for obj_type in detailed_objects:
                if obj_type in idf_content:
                    count = idf_content.count(obj_type)
                    found_detailed.append((obj_type, count))
            
            if found_detailed:
                print(f"   Found {len(found_detailed)} detailed HVAC object types:")
                for obj_type, count in found_detailed:
                    print(f"   - {obj_type}: {count}")
                print("\n   Note: Detailed HVAC objects found instead of templates.")
                print("   This might be because force_detailed_hvac is set or templates aren't being used.")
        
        # Extract a sample of template content
        print("\n📄 Sample HVAC Template Content:")
        lines = idf_content.split('\n')
        in_template = False
        template_sample = []
        for i, line in enumerate(lines):
            if any(template_type in line for template_type in template_types):
                in_template = True
                template_sample = []
            if in_template:
                template_sample.append(line)
                if len(template_sample) > 15:  # Show first 15 lines
                    break
        
        if template_sample:
            print('\n'.join(template_sample[:15]))
            if len(template_sample) > 15:
                print("   ...")
        
        return len(template_objects_found) > 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_hvac_templates()
    sys.exit(0 if success else 1)









