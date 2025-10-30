#!/usr/bin/env python3
"""Quick test to generate IDF and check for errors"""

from main import IDFCreator
import sys

print("Creating simple 3-story office...")
creator = IDFCreator(enhanced=True, professional=True)

try:
    path = creator.create_idf(
        address="350 5th Ave, New York, NY",
        user_params={
            'building_type': 'office',
            'stories': 3,
            'floor_area': 1500
        },
        output_path="quick_test.idf"
    )
    print(f"✅ Created: {path}")
    print(f"✅ Size: {len(open(path).read()):,} bytes")
    
    # Check first few lines for version
    with open(path) as f:
        for i, line in enumerate(f):
            if i < 20:
                if 'Version' in line:
                    print(f"Version line: {line.strip()}")
            else:
                break
                
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

