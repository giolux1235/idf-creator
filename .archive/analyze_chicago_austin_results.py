#!/usr/bin/env python3
"""
Analyze Chicago and Austin simulation results
"""
import sys
import os
import pandas as pd
from src.validation import validate_energy_coherence
from src.cbecs_lookup import CBECSLookup


def analyze_simulation_results(output_dir: str, city: str, building_area_m2: float):
    """Analyze simulation results"""
    print(f"\n{'='*80}")
    print(f"{city.upper()} SIMULATION RESULTS ANALYSIS")
    print(f"{'='*80}")
    
    csv_file = os.path.join(output_dir, 'eplustbl.csv')
    
    if not os.path.exists(csv_file):
        print(f"   ❌ CSV file not found: {csv_file}")
        return None
    
    try:
        # EnergyPlus CSV files have headers, need to parse manually
        with open(csv_file, 'r') as f:
            lines = f.readlines()
        
        # Find the data section
        data_start = None
        for i, line in enumerate(lines):
            if 'Total Site Energy' in line:
                data_start = i
                break
        
        if data_start is None:
            print(f"   ⚠ Could not find energy data in CSV")
            return None
        
        # Parse energy values
        energy_data = {}
        
        # Look for Total Site Energy line
        for i in range(max(0, data_start), min(len(lines), data_start + 20)):
            line = lines[i]
            if 'Total Site Energy' in line:
                parts = line.split(',')
                if len(parts) >= 3:
                    try:
                        # Value is typically in GJ, convert to kWh (1 GJ = 277.778 kWh)
                        value_gj = float(parts[2].strip())
                        value_kwh = value_gj * 277.778
                        energy_data['total_site_energy'] = value_kwh
                        
                        # Also get per area value
                        if len(parts) >= 4:
                            eui_mj_m2 = float(parts[3].strip())
                            eui_kwh_m2 = eui_mj_m2 / 3.6  # MJ to kWh
                            energy_data['eui_mj_m2'] = eui_mj_m2
                            energy_data['eui_kwh_m2'] = eui_kwh_m2
                        
                        print(f"   ✓ Found Total Site Energy: {value_kwh:,.0f} kWh/year")
                        print(f"   - EUI: {eui_kwh_m2:.1f} kWh/m²/year")
                    except (ValueError, IndexError):
                        pass
        
        # Also try reading with pandas, skipping header rows
        try:
            df = pd.read_csv(csv_file, skiprows=10, header=None, on_bad_lines='skip')
        
        print(f"\n   ✓ CSV loaded successfully")
        print(f"   - Rows: {len(df)}")
        print(f"   - Columns: {len(df.columns)}")
        
        print(f"\n   Columns:")
        for i, col in enumerate(df.columns[:15]):
            print(f"     {i+1}. {col}")
        
        # Look for energy-related columns
        energy_cols = {}
        for col in df.columns:
            col_lower = col.lower()
            if any(x in col_lower for x in ['electricity', 'energy', 'kwh']):
                if 'electricity' not in energy_cols:
                    energy_cols['electricity'] = []
                energy_cols['electricity'].append(col)
            elif any(x in col_lower for x in ['gas', 'natural']):
                if 'gas' not in energy_cols:
                    energy_cols['gas'] = []
                energy_cols['gas'].append(col)
            elif any(x in col_lower for x in ['heating', 'heat']):
                if 'heating' not in energy_cols:
                    energy_cols['heating'] = []
                energy_cols['heating'].append(col)
            elif any(x in col_lower for x in ['cooling', 'cool']):
                if 'cooling' not in energy_cols:
                    energy_cols['cooling'] = []
                energy_cols['cooling'].append(col)
            elif any(x in col_lower for x in ['lighting', 'light']):
                if 'lighting' not in energy_cols:
                    energy_cols['lighting'] = []
                energy_cols['lighting'].append(col)
            elif any(x in col_lower for x in ['fan', 'ventilation']):
                if 'fan' not in energy_cols:
                    energy_cols['fan'] = []
                energy_cols['fan'].append(col)
            elif any(x in col_lower for x in ['equipment', 'plug']):
                if 'equipment' not in energy_cols:
                    energy_cols['equipment'] = []
                energy_cols['equipment'].append(col)
        
        print(f"\n   Energy Columns Found:")
        total_energy = 0
        component_energy = {}
        
        for comp_type, cols in energy_cols.items():
            print(f"\n   {comp_type.upper()}:")
            comp_total = 0
            for col in cols:
                try:
                    # Try to sum the column
                    col_sum = df[col].sum()
                    if pd.notna(col_sum) and col_sum != 0:
                        print(f"     - {col}: {col_sum:,.2f}")
                        comp_total += abs(col_sum)
                        total_energy += abs(col_sum)
                except:
                    # Try first row value
                    try:
                        val = df[col].iloc[0]
                        if pd.notna(val) and val != 0:
                            print(f"     - {col}: {val:,.2f}")
                            comp_total += abs(float(val))
                            total_energy += abs(float(val))
                    except:
                        pass
            if comp_total > 0:
                component_energy[comp_type] = comp_total
        
        # Calculate EUI
        if total_energy > 0 and building_area_m2 > 0:
            eui_kwh_m2 = total_energy / building_area_m2
            eui_kbtu_ft2 = (eui_kwh_m2 * 3.412) / 10.764
            
            print(f"\n   {'='*80}")
            print(f"   ENERGY SUMMARY")
            print(f"   {'='*80}")
            print(f"   - Total Building Area: {building_area_m2:,.0f} m² ({building_area_m2*10.764:,.0f} ft²)")
            print(f"   - Total Energy: {total_energy:,.0f} kWh/year")
            print(f"   - EUI: {eui_kwh_m2:.1f} kWh/m²/year")
            print(f"   - EUI: {eui_kbtu_ft2:.1f} kBtu/ft²/year")
            
            # Compare to CBECS
            cbecs = CBECSLookup()
            typical_eui = cbecs.get_site_eui('office')
            if typical_eui:
                percent_diff = ((eui_kbtu_ft2 - typical_eui) / typical_eui) * 100
                print(f"\n   CBECS Comparison:")
                print(f"   - Typical Office EUI: {typical_eui:.1f} kBtu/ft²/year")
                print(f"   - Difference: {percent_diff:+.1f}%")
                
                if abs(percent_diff) < 30:
                    print(f"   ✅ EUI is within typical range (±30%)")
                elif percent_diff < -30:
                    print(f"   ⚠ EUI is low (more than 30% below typical)")
                else:
                    print(f"   ⚠ EUI is high (more than 30% above typical)")
            
            # Component breakdown
            if component_energy:
                print(f"\n   Component Breakdown:")
                for comp, energy in sorted(component_energy.items(), key=lambda x: x[1], reverse=True):
                    pct = (energy / total_energy) * 100
                    print(f"     - {comp}: {energy:,.0f} kWh/year ({pct:.1f}%)")
        
        return {
            'total_energy': total_energy,
            'eui_kwh_m2': eui_kwh_m2 if total_energy > 0 else 0,
            'eui_kbtu_ft2': eui_kbtu_ft2 if total_energy > 0 else 0,
            'components': component_energy
        }
        
    except Exception as e:
        print(f"   ❌ Error analyzing CSV: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Analyze both simulations"""
    
    print("=" * 80)
    print("CHICAGO AND AUSTIN SIMULATION RESULTS ANALYSIS")
    print("=" * 80)
    
    # Chicago - Willis Tower
    chicago_results = analyze_simulation_results(
        output_dir="artifacts/desktop_files/simulation/chicago",
        city="Chicago",
        building_area_m2=15000  # 3 stories × 5000 m²
    )
    
    # Austin
    austin_results = analyze_simulation_results(
        output_dir="artifacts/desktop_files/simulation/austin",
        city="Austin",
        building_area_m2=15000  # 3 stories × 5000 m²
    )
    
    # Summary
    print(f"\n\n{'='*80}")
    print("COMPARISON SUMMARY")
    print(f"{'='*80}")
    
    if chicago_results and austin_results:
        print(f"\n   Chicago EUI: {chicago_results['eui_kbtu_ft2']:.1f} kBtu/ft²/year")
        print(f"   Austin EUI:  {austin_results['eui_kbtu_ft2']:.1f} kBtu/ft²/year")
        print(f"   Difference:  {abs(chicago_results['eui_kbtu_ft2'] - austin_results['eui_kbtu_ft2']):.1f} kBtu/ft²/year")
        
        if chicago_results['eui_kbtu_ft2'] > austin_results['eui_kbtu_ft2']:
            print(f"   → Chicago uses {((chicago_results['eui_kbtu_ft2'] / austin_results['eui_kbtu_ft2']) - 1) * 100:.1f}% more energy")
            print(f"     (Expected: Chicago is colder, needs more heating)")


if __name__ == "__main__":
    main()

