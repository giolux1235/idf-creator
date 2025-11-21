#!/usr/bin/env python3
"""
Test script to benchmark IDF Creator against PDF report data.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, List
import PyPDF2

from main import IDFCreator


class PDFReportExtractor:
    """Extract building and energy data from PDF report"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.data = {}
        
    def extract_all_data(self) -> Dict:
        """Extract all relevant data from PDF"""
        pdf = open(self.pdf_path, 'rb')
        reader = PyPDF2.PdfReader(pdf)
        
        full_text = ''
        for page in reader.pages:
            full_text += page.extract_text() + '\n'
        
        pdf.close()
        
        data = {
            'address': '1234 Sample Way, Chicago, IL 60601',
            'building_name': 'Large Office Building',
            'built_year': 2004,
            'area_sqft': 100000,
            'area_m2': 9290.3,
            'floors': 12,
            'building_type': 'Office'
        }
        
        # Extract EUI
        eui_match = re.search(r'(\d+)\s*kBtu/sqft', full_text)
        if eui_match:
            data['current_eui_kbtu_sqft'] = float(eui_match.group(1))
        
        site_eui_match = re.search(r'(\d+)\s*kBtu/ft2', full_text)
        if site_eui_match:
            data['site_eui_kbtu_sqft'] = float(site_eui_match.group(1))
        
        # Extract energy consumption
        savings_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*kWh', full_text)
        if savings_match and '16%' in full_text:
            savings_kwh = float(savings_match.group(1).replace(',', ''))
            baseline_kwh = savings_kwh / 0.16
            data['baseline_annual_electric_kwh'] = baseline_kwh
        
        # Calculate total site energy from EUI
        if 'site_eui_kbtu_sqft' in data:
            site_eui = data['site_eui_kbtu_sqft']
            total_site_energy_kbtu = site_eui * data['area_sqft']
            data['baseline_total_site_energy_kwh'] = total_site_energy_kbtu * 0.293071
        
        # Extract breakdown
        breakdown = {}
        for pattern, category in [
            (r'(\d+)\s*%\s*Lighting', 'Lighting'),
            (r'(\d+)\s*%\s*Plug Loads', 'Plug Loads'),
        ]:
            match = re.search(pattern, full_text)
            if match:
                breakdown[category] = int(match.group(1))
        
        data['energy_breakdown_percent'] = breakdown
        self.data = data
        return data


class EnergyPlusSimulator:
    """Run EnergyPlus simulation and extract results"""
    
    def __init__(self):
        self.energyplus_path = self.find_energyplus()
        
    def find_energyplus(self) -> Optional[str]:
        """Find EnergyPlus executable"""
        import shutil
        ep_path = shutil.which('energyplus')
        if ep_path:
            return ep_path
        
        paths = [
            '/Applications/EnergyPlus-23-2-0/energyplus',
            '/usr/local/bin/energyplus',
        ]
        
        for path in paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def find_weather_file(self) -> Optional[str]:
        """Find weather file for Chicago"""
        weather_dirs = [
            'artifacts/desktop_files/weather',
            'artifacts/weather',
        ]
        
        for weather_dir in weather_dirs:
            if os.path.exists(weather_dir):
                for file in os.listdir(weather_dir):
                    if file.endswith('.epw') and ('Chicago' in file or '725300' in file):
                        return os.path.join(weather_dir, file)
        
        return None
    
    def run_simulation(self, idf_path: str, weather_file: Optional[str] = None, 
                      output_dir: Optional[str] = None) -> Dict:
        """Run EnergyPlus simulation"""
        if not self.energyplus_path:
            return {'error': 'EnergyPlus not found'}
        
        if not weather_file:
            weather_file = self.find_weather_file()
            if not weather_file:
                return {'error': 'Weather file not found'}
        
        if not output_dir:
            output_dir = os.path.join(os.path.dirname(idf_path), 'simulation_output')
        
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            cmd = [
                self.energyplus_path,
                '-w', weather_file,
                '-d', output_dir,
                idf_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=900
            )
            
            return {
                'success': result.returncode == 0,
                'output_dir': output_dir,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def extract_energy_results(self, output_dir: str) -> Optional[Dict]:
        """Extract energy consumption from simulation output"""
        csv_file = os.path.join(output_dir, 'eplustbl.csv')
        
        if not os.path.exists(csv_file):
            return None
        
        try:
            with open(csv_file, 'r') as f:
                content = f.read()
            
            results = {}
            
            # Extract total site energy (GJ)
            site_energy_match = re.search(r'Total Site Energy,([\d.]+)', content)
            if site_energy_match:
                site_energy_gj = float(site_energy_match.group(1))
                results['total_site_energy_gj'] = site_energy_gj
                results['total_site_energy_kwh'] = site_energy_gj * 277.778
            
            # Extract building area
            area_match = re.search(r'Total Building Area,([\d.]+)', content)
            if area_match:
                results['building_area_m2'] = float(area_match.group(1))
            
            # Extract end uses
            end_uses = {}
            end_use_patterns = [
                ('Interior Lighting', r'Interior Lighting,([\d.]+),([\d.]+)'),
                ('Interior Equipment', r'Interior Equipment,([\d.]+),([\d.]+)'),
                ('Fans', r'Fans,([\d.]+),([\d.]+)'),
                ('Cooling', r'Cooling,([\d.]+),([\d.]+)'),
                ('Heating', r'Heating,([\d.]+),([\d.]+)'),
            ]
            
            for end_use, pattern in end_use_patterns:
                match = re.search(pattern, content)
                if match:
                    elec_gj = float(match.group(1))
                    gas_gj = float(match.group(2))
                    if elec_gj > 0 or gas_gj > 0:
                        end_uses[end_use] = {
                            'electricity_kwh': elec_gj * 277.778,
                            'natural_gas_gj': gas_gj,
                        }
            
            results['end_uses'] = end_uses
            
            # Calculate EUI
            if 'total_site_energy_kwh' in results and 'building_area_m2' in results:
                area_m2 = results['building_area_m2']
                total_site_energy_kbtu = results['total_site_energy_kwh'] * 3.41214
                area_sqft = area_m2 * 10.7639
                results['eui_kbtu_sqft'] = total_site_energy_kbtu / area_sqft
            
            return results
            
        except Exception as e:
            return {'error': str(e)}


# Import the proper calibration function
from src.apply_calibration_to_idf import apply_calibration_to_idf


def main():
    """Main test function"""
    print("="*80)
    print("PDF REPORT BENCHMARK TEST")
    print("="*80)
    
    # Step 1: Extract data from PDF
    print("\n[1/5] Extracting data from PDF report...")
    pdf_path = '/Users/giovanniamenta/Downloads/COMreportSample20160127 (1).pdf'
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return 1
    
    extractor = PDFReportExtractor(pdf_path)
    report_data = extractor.extract_all_data()
    
    print(f"✓ Address: {report_data['address']}")
    print(f"✓ Area: {report_data['area_sqft']} sqft ({report_data['area_m2']:.1f} m²)")
    print(f"✓ Floors: {report_data['floors']}")
    target_eui = report_data.get('site_eui_kbtu_sqft', report_data.get('current_eui_kbtu_sqft', 146))
    print(f"✓ Target EUI: {target_eui:.1f} kBtu/sqft")
    
    # Save extracted data
    output_dir = Path('artifacts/benchmark_test')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 2: Generate IDF with calibration factors
    print("\n[2/5] Generating IDF file...")
    
    # Load calibration factors
    from src.calibration_system import CalibrationSystem
    calibration_system = CalibrationSystem()
    building_type = report_data['building_type'].lower()
    calibration_factors = calibration_system.get_calibration_factors(building_type)
    
    area_per_story = report_data['area_m2'] / report_data['floors']
    
    user_params = {
        'building_type': report_data['building_type'],
        'stories': report_data['floors'],
        'floor_area_per_story_m2': area_per_story,
        'force_area': True,
    }
    
    # Apply calibration factors
    if calibration_factors:
        print(f"📊 Applying calibration factors for {building_type}:")
        base_lighting = 10.8
        base_equipment = 8.1
        
        user_params.update({
            'lighting_power_density': base_lighting * calibration_factors.get('lighting_multiplier', 1.0),
            'equipment_power_density': base_equipment * calibration_factors.get('equipment_multiplier', 1.0),
            'occupancy_density': 0.05 * calibration_factors.get('occupancy_multiplier', 1.0),
        })
        print(f"   Lighting: {user_params['lighting_power_density']:.2f} W/m²")
        print(f"   Equipment: {user_params['equipment_power_density']:.2f} W/m²")
    
    creator = IDFCreator(enhanced=True, professional=True)
    
    idf_path = creator.create_idf(
        address=report_data['address'],
        user_params=user_params,
        output_path=str(output_dir / 'benchmark_building.idf')
    )
    
    if not idf_path or not os.path.exists(idf_path):
        print("❌ Failed to generate IDF file")
        return 1
    
    print(f"✓ IDF generated: {idf_path}")
    
    # Apply HVAC calibration
    if calibration_factors:
        print("\n[2.5/5] Applying HVAC calibration factors...")
        calibrated_idf_path = apply_calibration_to_idf(
            idf_path=str(idf_path),
            calibration_factors=calibration_factors,
            output_path=str(output_dir / 'benchmark_building_calibrated.idf')
        )
        idf_path = calibrated_idf_path
        print(f"✓ Calibrated IDF: {idf_path}")
    
    # Step 3: Run simulation
    print("\n[3/5] Running EnergyPlus simulation...")
    simulator = EnergyPlusSimulator()
    
    if not simulator.energyplus_path:
        print("❌ EnergyPlus not found")
        return 1
    
    sim_output_dir = output_dir / 'simulation'
    sim_result = simulator.run_simulation(
        idf_path=str(idf_path),
        output_dir=str(sim_output_dir)
    )
    
    if 'error' in sim_result or not sim_result.get('success'):
        print(f"❌ Simulation failed: {sim_result.get('error', 'Unknown error')}")
        return 1
    
    print(f"✓ Simulation completed")
    
    # Step 4: Extract results
    print("\n[4/5] Extracting energy results...")
    energy_results = simulator.extract_energy_results(str(sim_output_dir))
    
    if not energy_results:
        print("❌ Failed to extract energy results")
        return 1
    
    sim_eui = energy_results.get('eui_kbtu_sqft', 0)
    sim_total_kwh = energy_results.get('total_site_energy_kwh', 0)
    
    print(f"✓ Simulated EUI: {sim_eui:.1f} kBtu/sqft")
    print(f"✓ Simulated Total: {sim_total_kwh:,.0f} kWh")
    
    # Step 5: Compare
    print("\n[5/5] Comparing with report benchmarks...")
    
    target_total = report_data.get('baseline_total_site_energy_kwh', 0)
    
    eui_error = ((sim_eui - target_eui) / target_eui) * 100 if target_eui > 0 else 0
    total_error = ((sim_total_kwh - target_total) / target_total) * 100 if target_total > 0 else 0
    
    print("\n" + "="*80)
    print("COMPARISON RESULTS")
    print("="*80)
    print(f"\nEUI:")
    print(f"  Report:    {target_eui:.1f} kBtu/sqft")
    print(f"  Simulated: {sim_eui:.1f} kBtu/sqft")
    print(f"  Error:     {eui_error:+.1f}%")
    
    if target_total > 0:
        print(f"\nTotal Energy:")
        print(f"  Report:    {target_total:,.0f} kWh")
        print(f"  Simulated: {sim_total_kwh:,.0f} kWh")
        print(f"  Error:     {total_error:+.1f}%")
    
    # Check if we're close
    if abs(eui_error) < 15:
        print(f"\n✅ EXCELLENT! Within 15% of target!")
    elif abs(eui_error) < 30:
        print(f"\n✅ GOOD! Within 30% of target")
    elif abs(eui_error) < 50:
        print(f"\n⚠️  Getting closer - {abs(eui_error):.1f}% off")
    else:
        print(f"\n⚠️  Still needs calibration - {abs(eui_error):.1f}% off")
    
    # Save results
    comparison = {
        'eui_comparison': {
            'report_eui_kbtu_sqft': target_eui,
            'simulated_eui_kbtu_sqft': sim_eui,
            'difference_percent': eui_error
        },
        'energy_comparison': {
            'report_total_kwh': target_total,
            'simulated_total_kwh': sim_total_kwh,
            'difference_percent': total_error
        },
        'energy_results': energy_results
    }
    
    with open(output_dir / 'comparison.json', 'w') as f:
        json.dump(comparison, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_dir}")
    print("="*80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
