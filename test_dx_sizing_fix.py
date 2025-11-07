#!/usr/bin/env python3
"""
Quick test to verify DX coil sizing fixes work correctly.
Tests the shared sizing function to ensure it produces valid EnergyPlus ratios.
"""

from src.utils.common import calculate_dx_supply_air_flow

def test_dx_sizing():
    """Test DX coil sizing function produces valid EnergyPlus ratios."""
    
    # EnergyPlus valid range: 2.684e-5 to 6.713e-5 m³/s/W
    min_ratio = 2.684e-5
    max_ratio = 6.713e-5
    
    test_cases = [
        (10000, "Small zone"),      # 10 kW
        (35000, "Medium zone"),     # 35 kW
        (100000, "Large zone"),     # 100 kW
        (500000, "Very large"),     # 500 kW
    ]
    
    print("Testing DX Coil Sizing Function")
    print("=" * 60)
    
    all_passed = True
    
    for capacity_w, description in test_cases:
        airflow = calculate_dx_supply_air_flow(capacity_w)
        ratio = airflow / capacity_w if capacity_w > 0 else 0
        
        # Check if ratio is within valid range
        is_valid = min_ratio <= ratio <= max_ratio
        
        status = "✅ PASS" if is_valid else "❌ FAIL"
        
        print(f"\n{description}:")
        print(f"  Capacity: {capacity_w:,.0f} W")
        print(f"  Airflow: {airflow:.4f} m³/s")
        print(f"  Ratio: {ratio:.6e} m³/s/W")
        print(f"  Valid Range: [{min_ratio:.6e}, {max_ratio:.6e}]")
        print(f"  Status: {status}")
        
        if not is_valid:
            all_passed = False
            print(f"  ⚠️  Ratio out of range!")
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("✅ All tests passed! DX coil sizing is EnergyPlus compliant.")
    else:
        print("❌ Some tests failed. Check sizing function.")
    
    return all_passed

if __name__ == "__main__":
    success = test_dx_sizing()
    exit(0 if success else 1)

