"""
Chicago Buildings Expert Features Test
Tests 5 Chicago buildings with actual weather file to validate accuracy
"""

import os
import sys
import json
import subprocess
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.professional_idf_generator import ProfessionalIDFGenerator
from src.validation.simulation_validator import EnergyPlusSimulationValidator
from src.enhanced_location_fetcher import EnhancedLocationFetcher

class ChicagoExpertFeaturesTest:
    """Test expert features with Chicago buildings"""
    
    def __init__(self, weather_file: str):
        self.idf_generator = ProfessionalIDFGenerator()
        self.location_fetcher = EnhancedLocationFetcher()
        self.validator = EnergyPlusSimulationValidator()
        self.weather_file = weather_file
        
        # Chicago buildings with known energy data
        self.chicago_buildings = [
            {
                'name': 'Willis Tower',
                'address': '233 S Wacker Dr, Chicago, IL 60606',
                'building_type': 'office',
                'year_built': 1974,
                'stories': 110,
                'floor_area_m2': 416000,
                'actual_eui_kwh_m2': 155,  # From ENERGY STAR
            },
            {
                'name': 'John Hancock Center',
                'address': '875 N Michigan Ave, Chicago, IL 60611',
                'building_type': 'office_residential',
                'year_built': 1969,
                'stories': 100,
                'floor_area_m2': 260000,
                'actual_eui_kwh_m2': 165,
            },
            {
                'name': 'Aon Center',
                'address': '200 E Randolph St, Chicago, IL 60601',
                'building_type': 'office',
                'year_built': 1973,
                'stories': 83,
                'floor_area_m2': 280000,
                'actual_eui_kwh_m2': 158,
            },
            {
                'name': 'Prudential Plaza',
                'address': '130 E Randolph St, Chicago, IL 60601',
                'building_type': 'office',
                'year_built': 1955,
                'stories': 41,
                'floor_area_m2': 120000,
                'actual_eui_kwh_m2': 175,
            },
            {
                'name': 'Water Tower Place',
                'address': '835 N Michigan Ave, Chicago, IL 60611',
                'building_type': 'mixed_use',
                'year_built': 1975,
                'stories': 74,
                'floor_area_m2': 220000,
                'actual_eui_kwh_m2': 160,
            }
        ]
    
    def generate_idf_with_expert_features(self, building: Dict) -> Tuple[str, Optional[str]]:
        """Generate IDF file with all expert features enabled"""
        try:
            print(f"\n{'='*80}")
            print(f"Generating IDF for: {building['name']}")
            print(f"{'='*80}")
            
            # Get location data
            location_data = self.location_fetcher.fetch_comprehensive_location_data(building['address'])
            
            # Building parameters
            building_params = {
                'building_type': building['building_type'],
                'year_built': building.get('year_built'),
                'stories': building.get('stories', 10),
                'floor_area_m2': building.get('floor_area_m2', 5000),
                'simple_hvac': False,  # Use advanced HVAC
            }
            
            # Generate IDF
            idf_content = self.idf_generator.generate_professional_idf(
                address=building['address'],
                building_params=building_params,
                location_data=location_data
            )
            
            # Save IDF
            output_dir = Path('test_outputs/chicago')
            output_dir.mkdir(parents=True, exist_ok=True)
            idf_path = output_dir / f"{building['name'].replace(' ', '_')}_expert.idf"
            
            with open(idf_path, 'w') as f:
                f.write(idf_content)
            
            print(f"✅ IDF generated: {idf_path}")
            print(f"   Building: {building['name']}")
            print(f"   Area: {building['floor_area_m2']:,} m²")
            print(f"   Stories: {building['stories']}")
            
            return str(idf_path), self.weather_file
            
        except Exception as e:
            print(f"❌ Error generating IDF for {building['name']}: {e}")
            traceback.print_exc()
            return None, None
    
    def run_simulation(self, idf_path: str, weather_file: Optional[str] = None) -> Dict:
        """Run EnergyPlus simulation and extract results"""
        try:
            # Create output directory
            output_dir = Path(idf_path).parent / f"sim_{Path(idf_path).stem}"
            output_dir.mkdir(exist_ok=True)
            
            print(f"   Running simulation...")
            
            # Run simulation
            result = self.validator.validate_by_simulation(
                idf_file=idf_path,
                weather_file=weather_file,
                output_directory=str(output_dir),
                timeout=900  # 15 minutes per building
            )
            
            print(f"   Simulation result:")
            print(f"     Success: {result.success}")
            print(f"     Fatal: {result.fatal_errors}, Severe: {result.severe_errors}, Warnings: {result.warnings}")
            
            return {
                'success': result.success,
                'fatal_errors': result.fatal_errors,
                'severe_errors': result.severe_errors,
                'warnings': result.warnings,
                'error_file': result.error_file_path,
                'output_dir': str(output_dir),
                'errors': [e.message for e in result.errors[:5]]  # First 5 errors
            }
            
        except Exception as e:
            print(f"❌ Error running simulation: {e}")
            traceback.print_exc()
            return {
                'success': False,
                'fatal_errors': 1,
                'severe_errors': 0,
                'warnings': 0,
                'error': str(e)
            }
    
    def extract_energy_results(self, output_dir: str) -> Optional[Dict]:
        """Extract energy consumption from simulation output"""
        try:
            # Try CSV first
            csv_path = Path(output_dir) / 'eplustbl.csv'
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                
                # Look for energy consumption columns
                results = {}
                
                # Total site energy
                site_energy_cols = [col for col in df.columns if 'site' in col.lower() and 'energy' in col.lower()]
                if site_energy_cols:
                    results['total_site_energy_kwh'] = float(df[site_energy_cols[0]].sum() / 1000) if df[site_energy_cols[0]].dtype in ['float64', 'int64'] else None
                
                # Electricity
                elec_cols = [col for col in df.columns if 'electricity' in col.lower() or 'electric' in col.lower()]
                if elec_cols:
                    results['electricity_kwh'] = float(df[elec_cols[0]].sum() / 1000) if df[elec_cols[0]].dtype in ['float64', 'int64'] else None
                
                # Gas
                gas_cols = [col for col in df.columns if 'gas' in col.lower() and 'natural' in col.lower()]
                if gas_cols:
                    results['gas_kwh'] = float(df[gas_cols[0]].sum() / 1000) if df[gas_cols[0]].dtype in ['float64', 'int64'] else None
                
                # Get building area from first row if available
                if 'Building Area' in df.columns:
                    results['building_area_m2'] = float(df['Building Area'].iloc[0])
                elif 'Conditioned Floor Area {m2}' in df.columns:
                    results['building_area_m2'] = float(df['Conditioned Floor Area {m2}'].iloc[0])
                
                return results
            
            return None
            
        except Exception as e:
            print(f"   ⚠️  Error extracting energy results: {e}")
            return None
    
    def calculate_accuracy_metrics(self, simulated_eui: float, actual_eui: float) -> Dict:
        """Calculate accuracy metrics"""
        error_percent = ((simulated_eui - actual_eui) / actual_eui) * 100
        absolute_error = abs(error_percent)
        
        return {
            'simulated_eui_kwh_m2': simulated_eui,
            'actual_eui_kwh_m2': actual_eui,
            'error_percent': error_percent,
            'absolute_error_percent': absolute_error,
            'meets_ashrae_14': absolute_error <= 10.0  # ASHRAE 14 target: ±10%
        }
    
    def run_chicago_test_suite(self) -> Dict:
        """Run complete test suite for Chicago buildings"""
        print("\n" + "="*80)
        print("CHICAGO BUILDINGS EXPERT FEATURES TEST")
        print("="*80)
        print(f"Weather File: {self.weather_file}")
        print(f"Buildings: {len(self.chicago_buildings)}")
        print("="*80)
        
        summary = {
            'test_date': datetime.now().isoformat(),
            'weather_file': self.weather_file,
            'buildings_tested': 0,
            'buildings_simulated': 0,
            'buildings_with_results': 0,
            'results': []
        }
        
        for building in self.chicago_buildings:
            # Generate IDF
            idf_path, weather_file = self.generate_idf_with_expert_features(building)
            
            if not idf_path:
                print(f"❌ Failed to generate IDF for {building['name']}")
                continue
            
            summary['buildings_tested'] += 1
            
            # Run simulation
            sim_result = self.run_simulation(idf_path, weather_file or self.weather_file)
            
            if not sim_result['success']:
                print(f"❌ Simulation failed for {building['name']}")
                if sim_result.get('errors'):
                    for err in sim_result['errors'][:2]:
                        print(f"     {err[:100]}")
                continue
            
            summary['buildings_simulated'] += 1
            
            # Extract energy results
            energy_results = self.extract_energy_results(sim_result['output_dir'])
            
            building_result = {
                'building': building['name'],
                'address': building['address'],
                'floor_area_m2': building['floor_area_m2'],
                'actual_eui_kwh_m2': building['actual_eui_kwh_m2'],
                'simulation': {
                    'fatal_errors': sim_result['fatal_errors'],
                    'severe_errors': sim_result['severe_errors'],
                    'warnings': sim_result['warnings'],
                },
                'energy_results': energy_results
            }
            
            if energy_results and 'total_site_energy_kwh' in energy_results:
                # Calculate EUI
                total_energy = energy_results.get('total_site_energy_kwh') or energy_results.get('electricity_kwh', 0)
                floor_area = energy_results.get('building_area_m2') or building['floor_area_m2']
                
                if total_energy and floor_area:
                    simulated_eui = total_energy / floor_area
                    
                    # Calculate accuracy
                    accuracy = self.calculate_accuracy_metrics(simulated_eui, building['actual_eui_kwh_m2'])
                    building_result['accuracy'] = accuracy
                    building_result['simulated_eui_kwh_m2'] = simulated_eui
                    
                    summary['buildings_with_results'] += 1
                    
                    print(f"\n   📊 Energy Results:")
                    print(f"     Simulated EUI: {simulated_eui:.1f} kWh/m²/year")
                    print(f"     Actual EUI: {building['actual_eui_kwh_m2']:.1f} kWh/m²/year")
                    print(f"     Error: {accuracy['error_percent']:.1f}%")
                    print(f"     ASHRAE 14 Compliant: {'✅' if accuracy['meets_ashrae_14'] else '❌'}")
            
            summary['results'].append(building_result)
        
        # Calculate summary statistics
        if summary['buildings_with_results'] > 0:
            errors = [r['accuracy']['absolute_error_percent'] for r in summary['results'] 
                     if 'accuracy' in r]
            if errors:
                summary['average_error_percent'] = sum(errors) / len(errors)
                summary['ashrae_14_compliant'] = sum(1 for e in errors if e <= 10.0)
        
        return summary
    
    def save_results(self, summary: Dict, filename: str = 'chicago_expert_features_results.json'):
        """Save test results to file"""
        output_path = Path('test_outputs/chicago') / filename
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\n✅ Results saved to: {output_path}")


def main():
    """Run Chicago expert features test"""
    # Find Chicago weather file
    weather_file = './artifacts/desktop_files/weather/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'
    
    if not os.path.exists(weather_file):
        # Try alternative
        weather_file = './artifacts/desktop_files/weather/Chicago.epw'
    
    if not os.path.exists(weather_file):
        print(f"❌ Weather file not found. Looking for:")
        print(f"   {weather_file}")
        return
    
    print(f"✅ Using weather file: {weather_file}")
    
    tester = ChicagoExpertFeaturesTest(weather_file)
    summary = tester.run_chicago_test_suite()
    tester.save_results(summary)
    
    # Print summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Buildings tested: {summary['buildings_tested']}/5")
    print(f"Buildings simulated: {summary['buildings_simulated']}/5")
    print(f"Buildings with energy results: {summary['buildings_with_results']}/5")
    
    if summary.get('average_error_percent'):
        print(f"\nAverage Error: {summary['average_error_percent']:.1f}%")
        print(f"ASHRAE 14 Compliant: {summary.get('ashrae_14_compliant', 0)}/{summary['buildings_with_results']}")
    
    print("="*80)


if __name__ == '__main__':
    main()

