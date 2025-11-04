#!/usr/bin/env python3
"""
Check HVAC system type and diagnose energy reporting issues
"""
import sys
import os
from main import IDFCreator


def check_idf_hvac_type(idf_file: str):
    """Check what HVAC system type is used in IDF"""
    print("=" * 80)
    print("HVAC SYSTEM TYPE CHECK")
    print("=" * 80)
    
    with open(idf_file, 'r') as f:
        content = f.read()
    
    # Check for Ideal Loads
    ideal_loads = 'ZoneHVAC:IdealLoadsAirSystem' in content
    vav_found = 'AirLoopHVAC' in content or 'VAV' in content
    ptac_found = 'ZoneHVAC:PackagedTerminalAirConditioner' in content
    rtu_found = 'AirLoopHVAC:UnitarySystem' in content or 'UnitarySystem' in content
    
    print(f"\nHVAC System Analysis:")
    print(f"  - Ideal Loads: {'✅ YES' if ideal_loads else '❌ NO'}")
    print(f"  - VAV System: {'✅ YES' if vav_found else '❌ NO'}")
    print(f"  - PTAC System: {'✅ YES' if ptac_found else '❌ NO'}")
    print(f"  - RTU/Unitary: {'✅ YES' if rtu_found else '❌ NO'}")
    
    if ideal_loads:
        print(f"\n⚠ WARNING: Using Ideal Loads HVAC System")
        print(f"   - Ideal Loads do NOT report equipment energy consumption")
        print(f"   - Energy will appear as ZERO for HVAC components")
        print(f"   - Only lighting and equipment loads will be reported")
        print(f"   - This explains why energy consumption might be low")
        print(f"\n   Solution:")
        print(f"   - Use professional=True mode (VAV/PTAC)")
        print(f"   - Or set simple_hvac=False")
        print(f"   - Real HVAC systems report fan, coil, and pump energy")
    
    # Check for Lights objects
    lights_count = content.count('Lights,')
    equipment_count = content.count('ElectricEquipment,')
    people_count = content.count('People,')
    
    print(f"\nInternal Loads:")
    print(f"  - Lights objects: {lights_count}")
    print(f"  - Equipment objects: {equipment_count}")
    print(f"  - People objects: {people_count}")
    
    if lights_count == 0:
        print(f"  ❌ NO LIGHTS - energy will be zero for lighting!")
    if equipment_count == 0:
        print(f"  ❌ NO EQUIPMENT - energy will be zero for equipment!")
    
    # Check schedules
    schedule_count = content.count('Schedule:')
    print(f"\nSchedules:")
    print(f"  - Schedule objects: {schedule_count}")
    
    # Summary
    print(f"\n" + "=" * 80)
    print("DIAGNOSIS:")
    print("=" * 80)
    
    if ideal_loads:
        print("❌ IDEAL LOADS DETECTED")
        print("   Energy results will show:")
        print("   - Lighting energy: YES (if Lights defined)")
        print("   - Equipment energy: YES (if Equipment defined)")
        print("   - HVAC energy: NO (by design of Ideal Loads)")
        print("   - Fan energy: NO")
        print("   - Total energy will be ~30-50% of typical")
    elif vav_found or ptac_found or rtu_found:
        print("✅ REAL HVAC SYSTEM DETECTED")
        print("   Energy results should show:")
        print("   - Lighting energy: YES")
        print("   - Equipment energy: YES")
        print("   - HVAC energy: YES (fans, coils)")
        print("   - Fan energy: YES")
        print("   - Total energy should match CBECS ranges")
    else:
        print("⚠ UNKNOWN HVAC SYSTEM")
        print("   Could not detect HVAC system type")
    
    return {
        'ideal_loads': ideal_loads,
        'vav': vav_found,
        'ptac': ptac_found,
        'real_hvac': vav_found or ptac_found or rtu_found,
        'lights_count': lights_count,
        'equipment_count': equipment_count
    }


def main():
    """Check multiple IDF files"""
    
    # Check Empire State IDF
    idf_file = "artifacts/desktop_files/idf/empire_state_energy_test.idf"
    if os.path.exists(idf_file):
        print("\n1. Checking Empire State Building IDF:")
        results = check_idf_hvac_type(idf_file)
        print(f"\n   Results: {results}")
    else:
        print(f"   IDF file not found: {idf_file}")
    
    # Check other test IDFs
    test_files = [
        "output/professional_test_1_office.idf",
        "output/professional_test_2_mixed_use.idf",
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n2. Checking {test_file}:")
            check_idf_hvac_type(test_file)


if __name__ == "__main__":
    main()



