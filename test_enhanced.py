"""Test script for enhanced IDF Creator with multiple APIs."""

from main import IDFCreator


def test_enhanced_mode():
    """Test the enhanced IDF Creator."""
    print("=" * 70)
    print("🧪 Testing ENHANCED IDF Creator with Multiple Free APIs")
    print("=" * 70)
    print()
    
    # Create creator in enhanced mode
    creator = IDFCreator(enhanced=True)
    
    # Test with a real address
    test_address = "Empire State Building, New York, NY"
    
    try:
        # Process the address
        data = creator.process_inputs(
            address=test_address,
            user_params={
                'building_type': 'Office',
                'stories': 102,
                'floor_area': 50000
            }
        )
        
        print("\n" + "=" * 70)
        print("✅ Enhanced mode working!")
        print("=" * 70)
        
        # Show what data we got
        if 'building' in data:
            building = data['building']
            print("\n📊 Building Data Retrieved:")
            if 'osm_building_type' in building:
                print(f"  - OSM Building Type: {building['osm_building_type']}")
            if 'osm_levels' in building:
                print(f"  - OSM Levels: {building['osm_levels']}")
            if 'osm_area_m2' in building:
                print(f"  - OSM Area: {building['osm_area_m2']:.1f} m²")
            if 'osm_height_m' in building:
                print(f"  - OSM Height: {building['osm_height_m']:.1f} m")
            if 'osm_roof_shape' in building:
                print(f"  - Roof Shape: {building['osm_roof_shape']}")
        
        if 'weather_description' in data:
            print(f"\n🌤️  Weather: {data['weather_description']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def test_basic_mode():
    """Test the basic IDF Creator."""
    print("\n" + "=" * 70)
    print("🧪 Testing BASIC IDF Creator")
    print("=" * 70)
    print()
    
    # Create creator in basic mode
    creator = IDFCreator(enhanced=False)
    
    # Test with an address
    test_address = "Times Square, New York, NY"
    
    try:
        data = creator.process_inputs(
            address=test_address,
            user_params={
                'building_type': 'Retail',
                'stories': 2
            }
        )
        
        print("\n" + "=" * 70)
        print("✅ Basic mode working!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    test_enhanced_mode()
    # test_basic_mode()  # Uncomment to test basic mode too










