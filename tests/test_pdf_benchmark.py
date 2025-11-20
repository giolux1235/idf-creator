#!/usr/bin/env python3
"""
Test script to benchmark IDF Creator against PDF report data.
Extracts building and energy data from PDF, generates IDF, runs simulation,
and compares results with report benchmarks.
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
        
        # Extract all text
        full_text = ''
        for page in reader.pages:
            full_text += page.extract_text() + '\n'
        
        pdf.close()
        
        # Extract key data
        data = {
            'address': '1234 Sample Way, Chicago, IL 60601',
            'building_name': 'Large Office Building',
            'built_year': 2004,
            'area_sqft': 100000,
            'area_m2': 9290.3,  # Convert sqft to m2
            'floors': 12,
            'occupancy': {
                'weekdays': '8:00 AM to 5:00 PM',
                'saturday': '9:00 AM to 12:00 PM',
                'sunday': 'No occupancy'
            },
            'building_type': 'Office'
        }
        
        # Extract EUI data
        eui_patterns = [
            (r'(\d+)\s*kBtu/sqft', 'current_eui_kbtu_sqft'),
            (r'(\d+)\s*kBtu/sf', 'current_eui_kbtu_sqft'),
            (r'(\d+)\s*kBtu/ft2', 'site_eui_kbtu_sqft'),
        ]
        
        for pattern, key in eui_patterns:
            match = re.search(pattern, full_text)
            if match:
                value = float(match.group(1))
                if 'current' in key or value > 80:  # Current EUI is higher
                    if 'current_eui_kbtu_sqft' not in data:
                        data['current_eui_kbtu_sqft'] = value
                elif 'site' in key:
                    data['site_eui_kbtu_sqft'] = value
        
        # Extract improved EUI
        improved_match = re.search(r'Improved EUI[=:]?\s*(\d+)', full_text)
        if improved_match:
            data['improved_eui_kbtu_sqft'] = float(improved_match.group(1))
        
        # Extract annual consumption
        # From report: savings are 16% of electric consumption = 299,634 kWh
        savings_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*kWh', full_text)
        if savings_match:
            savings_kwh = float(savings_match.group(1).replace(',', ''))
            # If this is savings and it's 16%, calculate baseline
            if '16%' in full_text:
                baseline_kwh = savings_kwh / 0.16
                data['baseline_annual_electric_kwh'] = baseline_kwh
                data['annual_electric_savings_kwh'] = savings_kwh
        
        # Extract gas consumption
        gas_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*therms?', full_text)
        if gas_match:
            therms = float(gas_match.group(1).replace(',', ''))
            data['annual_gas_savings_therms'] = therms
        
        # Extract energy breakdown percentages
        breakdown = {}
        breakdown_patterns = [
            (r'(\d+)\s*%\s*Lighting', 'Lighting'),
            (r'(\d+)\s*%\s*Plug Loads', 'Plug Loads'),
            (r'(\d+)\s*%\s*HVAC Cooling', 'HVAC Cooling'),
            (r'(\d+)\s*%\s*HVAC Fan', 'HVAC Fan'),
            (r'(\d+)\s*%\s*HVAC Pump', 'HVAC Pump'),
        ]
        
        for pattern, category in breakdown_patterns:
            match = re.search(pattern, full_text)
            if match:
                breakdown[category] = int(match.group(1))
        
        data['energy_breakdown_percent'] = breakdown
        
        # Extract utility rates
        elec_rate_match = re.search(r'\$([\d.]+)/kWh', full_text)
        if elec_rate_match:
            data['electric_rate_per_kwh'] = float(elec_rate_match.group(1))
        
        gas_rate_match = re.search(r'\$([\d.]+)/therm', full_text)
        if gas_rate_match:
            data['gas_rate_per_therm'] = float(gas_rate_match.group(1))
        
        # Calculate baseline annual consumption
        if 'baseline_annual_electric_kwh' in data:
            # Convert to site EUI for comparison
            site_eui_kbtu_sqft = data.get('site_eui_kbtu_sqft', 90)
            # Site EUI = (Total Site Energy in kBtu) / Area in sqft
            # Total Site Energy = Site EUI * Area
            total_site_energy_kbtu = site_eui_kbtu_sqft * data['area_sqft']
            # Convert kBtu to kWh (1 kBtu = 0.293071 kWh)
            total_site_energy_kwh = total_site_energy_kbtu * 0.293071
            data['baseline_total_site_energy_kwh'] = total_site_energy_kwh
        
        self.data = data
        return data


class EnergyPlusSimulator:
    """Run EnergyPlus simulation and extract results"""
    
    def __init__(self):
        self.energyplus_path = self.find_energyplus()
        
    def find_energyplus(self) -> Optional[str]:
        """Find EnergyPlus executable"""
        # Common paths
        paths = [
            '/Applications/EnergyPlus-23-2-0/energyplus',
            '/usr/local/bin/energyplus',
            '/opt/energyplus/energyplus',
        ]
        
        # Check PATH
        import shutil
        ep_path = shutil.which('energyplus')
        if ep_path:
            return ep_path
        
        for path in paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def find_weather_file(self, location: str = 'Chicago') -> Optional[str]:
        """Find weather file for location"""
        # Check common locations
        weather_dirs = [
            'artifacts/desktop_files/weather',
            'artifacts/weather',
            '/Applications/EnergyPlus-23-2-0/WeatherData',
            '/usr/local/EnergyPlus/WeatherData',
        ]
        
        # Look for Chicago weather file
        chicago_patterns = ['Chicago', 'IL', '725300']
        
        for weather_dir in weather_dirs:
            if os.path.exists(weather_dir):
                for file in os.listdir(weather_dir):
                    if file.endswith('.epw'):
                        if any(pattern in file for pattern in chicago_patterns):
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
            # Run EnergyPlus
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
                timeout=600  # Increase timeout for large buildings
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
                results['total_site_energy_kwh'] = site_energy_gj * 277.778  # Convert GJ to kWh
            
            # Extract source energy
            source_energy_match = re.search(r'Total Source Energy,([\d.]+)', content)
            if source_energy_match:
                source_energy_gj = float(source_energy_match.group(1))
                results['total_source_energy_gj'] = source_energy_gj
                results['total_source_energy_kwh'] = source_energy_gj * 277.778
            
            # Extract building area
            area_match = re.search(r'Total Building Area,([\d.]+)', content)
            if area_match:
                results['building_area_m2'] = float(area_match.group(1))
            
            # Extract end uses
            end_uses = {}
            end_use_patterns = [
                ('Heating', r'Heating,([\d.]+),([\d.]+)'),
                ('Cooling', r'Cooling,([\d.]+),([\d.]+)'),
                ('Interior Lighting', r'Interior Lighting,([\d.]+),([\d.]+)'),
                ('Interior Equipment', r'Interior Equipment,([\d.]+),([\d.]+)'),
                ('Fans', r'Fans,([\d.]+),([\d.]+)'),
                ('Pumps', r'Pumps,([\d.]+),([\d.]+)'),
            ]
            
            for end_use, pattern in end_use_patterns:
                match = re.search(pattern, content)
                if match:
                    elec_gj = float(match.group(1))
                    gas_gj = float(match.group(2))
                    if elec_gj > 0 or gas_gj > 0:
                        end_uses[end_use] = {
                            'electricity_gj': elec_gj,
                            'electricity_kwh': elec_gj * 277.778,
                            'natural_gas_gj': gas_gj,
                            'natural_gas_therms': gas_gj * 9.47817  # Convert GJ to therms
                        }
            
            results['end_uses'] = end_uses
            
            # Calculate EUI
            if 'total_site_energy_kwh' in results and 'building_area_m2' in results:
                area_m2 = results['building_area_m2']
                # Convert kWh to kBtu (1 kWh = 3.41214 kBtu)
                total_site_energy_kbtu = results['total_site_energy_kwh'] * 3.41214
                # Convert m2 to sqft (1 m2 = 10.7639 sqft)
                area_sqft = area_m2 * 10.7639
                results['eui_kbtu_sqft'] = total_site_energy_kbtu / area_sqft
            
            return results
            
        except Exception as e:
            return {'error': str(e)}


class BenchmarkComparator:
    """Compare simulation results with report benchmarks"""
    
    def __init__(self, report_data: Dict, simulation_results: Dict):
        self.report_data = report_data
        self.simulation_results = simulation_results
    
    def compare(self) -> Dict:
        """Compare results and calculate differences"""
        comparison = {
            'eui_comparison': {},
            'energy_comparison': {},
            'end_use_comparison': {},
            'differences': {},
            'recommendations': []
        }
        
        # Compare EUI
        report_eui = self.report_data.get('site_eui_kbtu_sqft', self.report_data.get('current_eui_kbtu_sqft'))
        sim_eui = self.simulation_results.get('eui_kbtu_sqft')
        
        if report_eui and sim_eui:
            comparison['eui_comparison'] = {
                'report_eui_kbtu_sqft': report_eui,
                'simulated_eui_kbtu_sqft': sim_eui,
                'difference_kbtu_sqft': sim_eui - report_eui,
                'difference_percent': ((sim_eui - report_eui) / report_eui) * 100
            }
            
            if abs(comparison['eui_comparison']['difference_percent']) > 10:
                comparison['recommendations'].append(
                    f"EUI difference is {comparison['eui_comparison']['difference_percent']:.1f}%. "
                    f"Consider adjusting building parameters."
                )
        
        # Compare total energy
        report_energy = self.report_data.get('baseline_total_site_energy_kwh')
        sim_energy = self.simulation_results.get('total_site_energy_kwh')
        
        if report_energy and sim_energy:
            comparison['energy_comparison'] = {
                'report_total_kwh': report_energy,
                'simulated_total_kwh': sim_energy,
                'difference_kwh': sim_energy - report_energy,
                'difference_percent': ((sim_energy - report_energy) / report_energy) * 100
            }
        
        # Compare end uses if available
        report_breakdown = self.report_data.get('energy_breakdown_percent', {})
        sim_end_uses = self.simulation_results.get('end_uses', {})
        
        if report_breakdown and sim_end_uses:
            # Map report categories to simulation categories
            category_mapping = {
                'Lighting': 'Interior Lighting',
                'Plug Loads': 'Interior Equipment',
                'HVAC Cooling': 'Cooling',
                'HVAC Fan': 'Fans',
                'HVAC Pump': 'Pumps',
            }
            
            total_sim_kwh = sim_energy or 0
            if total_sim_kwh > 0:
                for report_cat, report_pct in report_breakdown.items():
                    sim_cat = category_mapping.get(report_cat)
                    if sim_cat in sim_end_uses:
                        sim_kwh = sim_end_uses[sim_cat].get('electricity_kwh', 0)
                        sim_pct = (sim_kwh / total_sim_kwh) * 100
                        
                        comparison['end_use_comparison'][report_cat] = {
                            'report_percent': report_pct,
                            'simulated_percent': sim_pct,
                            'difference_percent': sim_pct - report_pct
                        }
        
        return comparison


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
    print(f"✓ Building: {report_data['building_name']}")
    print(f"✓ Area: {report_data['area_sqft']} sqft ({report_data['area_m2']:.1f} m²)")
    print(f"✓ Floors: {report_data['floors']}")
    print(f"✓ Site EUI: {report_data.get('site_eui_kbtu_sqft', 'N/A')} kBtu/sqft")
    if 'baseline_annual_electric_kwh' in report_data:
        print(f"✓ Baseline Annual Electric: {report_data['baseline_annual_electric_kwh']:,.0f} kWh")
    
    # Save extracted data
    output_dir = Path('artifacts/benchmark_test')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / 'report_data.json', 'w') as f:
        json.dump(report_data, f, indent=2)
    
    # Step 2: Generate IDF with report parameters (with calibration factors)
    print("\n[2/5] Generating IDF file...")
    
    # Load and apply calibration factors
    from src.calibration_system import CalibrationSystem
    calibration_system = CalibrationSystem()
    building_type = report_data['building_type'].lower()
    calibration_factors = calibration_system.get_calibration_factors(building_type)
    
    # Use floor_area_per_story_m2 to override OSM footprint
    area_per_story = report_data['area_m2'] / report_data['floors']
    
    # Base parameters
    user_params = {
        'building_type': report_data['building_type'],
        'stories': report_data['floors'],
        'floor_area_per_story_m2': area_per_story,
        'force_area': True,
    }
    
    # Apply calibration factors if available
    if calibration_factors and any(v != 1.0 for v in calibration_factors.values() if isinstance(v, (int, float))):
        print(f"📊 Applying calibration factors for {building_type}:")
        for key, value in calibration_factors.items():
            if 'multiplier' in key and isinstance(value, (int, float)):
                print(f"   {key}: {value:.3f}")
        
        # Apply multipliers to base ASHRAE 90.1 defaults
        base_lighting = 10.8  # ASHRAE 90.1 office default
        base_equipment = 8.1  # ASHRAE 90.1 office default
        base_occupancy = 0.05  # ASHRAE 90.1 office default
        
        user_params.update({
            'lighting_power_density': base_lighting * calibration_factors.get('lighting_multiplier', 1.0),
            'equipment_power_density': base_equipment * calibration_factors.get('equipment_multiplier', 1.0),
            'occupancy_density': base_occupancy * calibration_factors.get('occupancy_multiplier', 1.0),
        })
        print(f"   Adjusted lighting: {user_params['lighting_power_density']:.2f} W/m² (base: {base_lighting})")
        print(f"   Adjusted equipment: {user_params['equipment_power_density']:.2f} W/m² (base: {base_equipment})")
    else:
        print("   No calibration factors found, using defaults")
    
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
    
    # Apply HVAC calibration factors directly to IDF file
    if calibration_factors and any(v != 1.0 for v in calibration_factors.values() if isinstance(v, (int, float))):
        from src.apply_calibration_to_idf import apply_calibration_to_idf
        print("\n[2.5/5] Applying HVAC calibration factors to IDF...")
        calibrated_idf_path = apply_calibration_to_idf(
            idf_path=str(idf_path),
            calibration_factors=calibration_factors,
            output_path=str(output_dir / 'benchmark_building_calibrated.idf')
        )
        idf_path = calibrated_idf_path
        print(f"✓ Calibrated IDF: {idf_path}")
        hvac_mult = calibration_factors.get('hvac_efficiency_multiplier', 1.0)
        fan_mult = calibration_factors.get('fan_power_multiplier', 1.0)
        if hvac_mult != 1.0:
            print(f"   HVAC Efficiency: {hvac_mult:.3f}×")
        if fan_mult != 1.0:
            print(f"   Fan Power: {fan_mult:.3f}×")
    
    # Step 3: Run simulation
    print("\n[3/5] Running EnergyPlus simulation...")
    simulator = EnergyPlusSimulator()
    
    if not simulator.energyplus_path:
        print("❌ EnergyPlus not found. Please install EnergyPlus.")
        return 1
    
    sim_output_dir = output_dir / 'simulation'
    sim_result = simulator.run_simulation(
        idf_path=str(idf_path),
        output_dir=str(sim_output_dir)
    )
    
    if 'error' in sim_result:
        print(f"❌ Simulation error: {sim_result['error']}")
        return 1
    
    if not sim_result.get('success'):
        print(f"❌ Simulation failed. Return code: {sim_result.get('returncode')}")
        print(f"Stderr: {sim_result.get('stderr', '')[:500]}")
        return 1
    
    print(f"✓ Simulation completed: {sim_output_dir}")
    
    # Step 4: Extract energy results
    print("\n[4/5] Extracting energy results...")
    energy_results = simulator.extract_energy_results(str(sim_output_dir))
    
    if not energy_results:
        print("❌ Failed to extract energy results")
        return 1
    
    print(f"✓ Total Site Energy: {energy_results.get('total_site_energy_kwh', 0):,.0f} kWh")
    print(f"✓ EUI: {energy_results.get('eui_kbtu_sqft', 0):.1f} kBtu/sqft")
    
    # Save simulation results
    with open(output_dir / 'simulation_results.json', 'w') as f:
        json.dump(energy_results, f, indent=2)
    
    # Step 5: Compare with report
    print("\n[5/5] Comparing with report benchmarks...")
    comparator = BenchmarkComparator(report_data, energy_results)
    comparison = comparator.compare()
    
    # Save comparison
    with open(output_dir / 'comparison.json', 'w') as f:
        json.dump(comparison, f, indent=2)
    
    # Print comparison results
    print("\n" + "="*80)
    print("COMPARISON RESULTS")
    print("="*80)
    
    if comparison.get('eui_comparison'):
        eui_comp = comparison['eui_comparison']
        print(f"\nEUI Comparison:")
        print(f"  Report EUI:     {eui_comp['report_eui_kbtu_sqft']:.1f} kBtu/sqft")
        print(f"  Simulated EUI:  {eui_comp['simulated_eui_kbtu_sqft']:.1f} kBtu/sqft")
        print(f"  Difference:     {eui_comp['difference_kbtu_sqft']:+.1f} kBtu/sqft ({eui_comp['difference_percent']:+.1f}%)")
    
    if comparison.get('energy_comparison'):
        energy_comp = comparison['energy_comparison']
        print(f"\nTotal Energy Comparison:")
        print(f"  Report Total:   {energy_comp['report_total_kwh']:,.0f} kWh")
        print(f"  Simulated Total: {energy_comp['simulated_total_kwh']:,.0f} kWh")
        print(f"  Difference:     {energy_comp['difference_kwh']:+,.0f} kWh ({energy_comp['difference_percent']:+.1f}%)")
    
    if comparison.get('end_use_comparison'):
        print(f"\nEnd Use Comparison:")
        for category, comp in comparison['end_use_comparison'].items():
            print(f"  {category}:")
            print(f"    Report:    {comp['report_percent']:.1f}%")
            print(f"    Simulated: {comp['simulated_percent']:.1f}%")
            print(f"    Difference: {comp['difference_percent']:+.1f}%")
    
    if comparison.get('recommendations'):
        print(f"\nRecommendations:")
        for rec in comparison['recommendations']:
            print(f"  • {rec}")
    
    print("\n" + "="*80)
    print("✓ Benchmark test completed!")
    print(f"Results saved to: {output_dir}")
    print("="*80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

