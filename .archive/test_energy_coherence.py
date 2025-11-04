#!/usr/bin/env python3
"""
Test energy results coherence - check if energy consumption makes physical sense
"""
import sys
import os
from main import IDFCreator
from src.validation import (
    validate_simulation,
    EnergyPlusSimulationValidator,
    validate_energy_coherence
)


def analyze_energy_results(idf_file: str, building_params: dict, output_dir: str, idf_content: str = None):
    """Analyze energy results for physical coherence"""
    print("\n" + "="*80)
    print("ENERGY RESULTS COHERENCE ANALYSIS")
    print("="*80)
    
    validator = EnergyPlusSimulationValidator()
    
    # Extract energy results
    energy_results = validator.get_energy_results(output_dir)
    
    if not energy_results:
        print("   ⚠ No energy results file found")
        return False
    
    if 'error' in energy_results:
        print(f"   ✗ Error extracting results: {energy_results['error']}")
        return False
    
    print(f"\n   ✓ Energy results extracted")
    print(f"   - Rows: {energy_results.get('rows', 'N/A')}")
    print(f"   - Columns: {len(energy_results.get('columns', []))}")
    
    # Get building info
    building_type = building_params.get('building_type', 'Office')
    floor_area = building_params.get('floor_area', 1000)
    stories = building_params.get('stories', 1)
    total_area = floor_area * stories if floor_area else 1000
    
    print(f"\n   Building Info:")
    print(f"   - Type: {building_type}")
    print(f"   - Total Area: {total_area:.0f} m² ({total_area*10.764:.0f} ft²)")
    print(f"   - Stories: {stories}")
    
    # Analyze energy metrics
    columns = energy_results.get('columns', [])
    data = energy_results.get('data', [])
    
    if not data:
        print("   ⚠ No data rows found")
        return False
    
    # Find energy columns
    energy_metrics = {}
    for col in columns:
        col_lower = col.lower()
        
        # Check for various energy metric patterns
        if any(term in col_lower for term in ['electricity', 'total site energy', 'site energy']):
            energy_metrics['electricity'] = col
        elif any(term in col_lower for term in ['gas', 'natural gas']):
            energy_metrics['gas'] = col
        elif any(term in col_lower for term in ['heating', 'heat']):
            energy_metrics['heating'] = col
        elif any(term in col_lower for term in ['cooling', 'cool']):
            energy_metrics['cooling'] = col
        elif any(term in col_lower for term in ['lighting', 'light']):
            energy_metrics['lighting'] = col
        elif any(term in col_lower for term in ['fan', 'ventilation']):
            energy_metrics['fan'] = col
        elif any(term in col_lower for term in ['equipment', 'plug load']):
            energy_metrics['equipment'] = col
    
    print(f"\n   Energy Metrics Found:")
    for metric_name, col_name in energy_metrics.items():
        print(f"   - {metric_name}: {col_name}")
    
    # Calculate totals from first row (annual totals)
    annual_totals = {}
    issues = []
    warnings = []
    
    if data:
        first_row = data[0]
        
        for metric_name, col_name in energy_metrics.items():
            if col_name in first_row:
                value = first_row[col_name]
                try:
                    # Handle different formats
                    if isinstance(value, str):
                        value = float(value.replace(',', ''))
                    else:
                        value = float(value)
                    
                    annual_totals[metric_name] = value
                    
                    # Check for zeros
                    if value == 0:
                        issues.append(f"   ❌ {metric_name}: {value} (ZERO - unrealistic!)")
                    elif value < 0:
                        issues.append(f"   ❌ {metric_name}: {value} (NEGATIVE - impossible!)")
                    elif value < 1:
                        warnings.append(f"   ⚠ {metric_name}: {value} (Very low)")
                        
                except (ValueError, TypeError):
                    warnings.append(f"   ⚠ {metric_name}: Could not parse value: {value}")
    
    # Calculate EUI (Energy Use Intensity)
    print(f"\n   Annual Energy Consumption:")
    total_energy = 0
    for metric_name, value in annual_totals.items():
        print(f"   - {metric_name}: {value:.2f} kWh/year")
        if value > 0:
            total_energy += value
    
    # Calculate EUI
    if total_area > 0 and total_energy > 0:
        eui_kbtu_ft2 = (total_energy * 3.412) / (total_area * 10.764)  # Convert to kBtu/ft²
        eui_kwh_m2 = total_energy / total_area  # kWh/m²/year
        
        print(f"\n   Energy Use Intensity (EUI):")
        print(f"   - {eui_kwh_m2:.1f} kWh/m²/year")
        print(f"   - {eui_kbtu_ft2:.1f} kBtu/ft²/year")
        
        # Compare to CBECS typical ranges
        # Typical office building EUI: 50-150 kBtu/ft²/year
        cbecs_ranges = {
            'Office': (50, 150),
            'Retail': (40, 120),
            'School': (40, 100),
            'Hospital': (100, 200),
            'Residential': (30, 80),
            'Warehouse': (20, 60),
        }
        
        typical_range = cbecs_ranges.get(building_type, (50, 150))
        
        if eui_kbtu_ft2 < typical_range[0] * 0.5:
            issues.append(f"   ❌ EUI {eui_kbtu_ft2:.1f} kBtu/ft² is VERY LOW (typical: {typical_range[0]}-{typical_range[1]})")
        elif eui_kbtu_ft2 < typical_range[0]:
            warnings.append(f"   ⚠ EUI {eui_kbtu_ft2:.1f} kBtu/ft² is LOW (typical: {typical_range[0]}-{typical_range[1]})")
        elif eui_kbtu_ft2 > typical_range[1] * 1.5:
            issues.append(f"   ❌ EUI {eui_kbtu_ft2:.1f} kBtu/ft² is VERY HIGH (typical: {typical_range[0]}-{typical_range[1]})")
        elif eui_kbtu_ft2 > typical_range[1]:
            warnings.append(f"   ⚠ EUI {eui_kbtu_ft2:.1f} kBtu/ft² is HIGH (typical: {typical_range[0]}-{typical_range[1]})")
        else:
            print(f"   ✓ EUI {eui_kbtu_ft2:.1f} kBtu/ft² is within typical range for {building_type}")
    else:
        if total_energy == 0:
            issues.append("   ❌ Total energy consumption is ZERO (unrealistic!)")
        if total_area == 0:
            issues.append("   ❌ Building area is ZERO (invalid!)")
    
    # Report issues
    print(f"\n   Issues Found:")
    if issues:
        for issue in issues:
            print(issue)
    else:
        print("   ✓ No critical issues found")
    
    print(f"\n   Warnings:")
    if warnings:
        for warn in warnings:
            print(warn)
    else:
        print("   ✓ No warnings")
    
    # Use energy coherence validator
    print(f"\n4. Running energy coherence validation...")
    try:
        coherence_results = validate_energy_coherence(
            energy_results=energy_results,
            building_type=building_params.get('building_type', 'Office'),
            total_area_m2=total_area,
            stories=building_params.get('stories', 1),
            idf_content=idf_content
        )
        
        print(f"   ✓ Coherence validation completed")
        print(f"   - Issues: {coherence_results['issue_count']}")
        print(f"   - Warnings: {coherence_results['warning_count']}")
        
        if coherence_results['issues']:
            print(f"\n   Critical Issues:")
            for issue in coherence_results['issues']:
                print(f"     ❌ {issue.metric}: {issue.value}")
                print(f"        Reason: {issue.reason}")
                print(f"        Fix: {issue.fix_suggestion}")
        
        if coherence_results['warnings']:
            print(f"\n   Warnings:")
            for warn in coherence_results['warnings']:
                print(f"     ⚠ {warn.metric}: {warn.value}")
                print(f"        Reason: {warn.reason}")
                print(f"        Fix: {warn.fix_suggestion}")
        
        if coherence_results['is_coherent']:
            print(f"\n   ✅ Energy results are physically coherent!")
        else:
            print(f"\n   ❌ Energy results have coherence issues")
        
        return coherence_results['is_coherent']
        
    except Exception as e:
        print(f"   ⚠ Coherence validation error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Diagnose zero energy issue
    if total_energy == 0 or all(v == 0 for v in annual_totals.values()):
        print(f"\n   DIAGNOSIS: Zero Energy Consumption")
        print(f"   This typically happens when:")
        print(f"   1. Using Ideal Loads HVAC (doesn't report equipment energy)")
        print(f"   2. No internal loads defined properly")
        print(f"   3. Simulation didn't run completely")
        print(f"   Solution: Use real HVAC systems (VAV/PTAC/RTU) instead of Ideal Loads")
    
    return len(issues) == 0


def test_empire_state_energy_coherence():
    """Test Empire State Building energy results"""
    print("=" * 80)
    print("EMPIRE STATE BUILDING - ENERGY COHERENCE TEST")
    print("=" * 80)
    
    # Step 1: Generate IDF
    print("\n1. Generating IDF...")
    location_data = None
    building_params = {
        'building_type': 'Office',
        'stories': 3,  # Reduced for faster simulation
        'floor_area': 5000,
    }
    
    try:
        creator = IDFCreator(professional=True, enhanced=True)
        location_data = creator.process_inputs(
            address="Empire State Building, New York, NY",
            user_params=building_params
        )
        
        idf_file = creator.create_idf(
            address="Empire State Building, New York, NY",
            user_params=building_params,
            output_path="artifacts/desktop_files/idf/empire_state_energy_test.idf"
        )
        
        print(f"   ✓ IDF generated: {idf_file}")
        
    except Exception as e:
        print(f"   ✗ IDF generation failed: {e}")
        return False
    
    # Step 2: Run simulation
    print("\n2. Running EnergyPlus simulation...")
    output_dir = "artifacts/desktop_files/simulation/empire_state_energy"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        validator = EnergyPlusSimulationValidator()
        result = validator.validate_by_simulation(
            idf_file=os.path.abspath(idf_file),
            weather_file=None,
            output_directory=os.path.abspath(output_dir),
            timeout=600
        )
        
        print(f"   Simulation Status: {'✅ Success' if result.success else '❌ Failed'}")
        print(f"   - Fatal errors: {result.fatal_errors}")
        print(f"   - Severe errors: {result.severe_errors}")
        
        if not result.success:
            print(f"\n   ⚠ Simulation had errors - checking partial results anyway")
        
    except Exception as e:
        print(f"   ⚠ Simulation error: {e}")
        print(f"   This is expected if EnergyPlus/weather file not available")
        return False
    
    # Step 3: Read IDF content for HVAC checking
    print("\n3. Reading IDF content for HVAC analysis...")
    try:
        with open(idf_file, 'r') as f:
            idf_content = f.read()
        print(f"   ✓ IDF content loaded")
    except Exception as e:
        print(f"   ⚠ Could not read IDF: {e}")
        idf_content = None
    
    # Step 4: Analyze energy results
    print("\n4. Analyzing energy results coherence...")
    try:
        is_coherent = analyze_energy_results(
            idf_file,
            building_params,
            output_dir,
            idf_content
        )
        
        if is_coherent:
            print(f"\n✅ Energy results are physically coherent!")
        else:
            print(f"\n⚠ Energy results have issues - see analysis above")
        
        return is_coherent
        
    except Exception as e:
        print(f"   ✗ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_empire_state_energy_coherence()
    sys.exit(0 if success else 1)

