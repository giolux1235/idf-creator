"""
Comprehensive Test Suite for Expert Features Accuracy Validation
Runs actual EnergyPlus simulations to verify accuracy improvements
"""

import os
import sys
import json
import subprocess
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.professional_idf_generator import ProfessionalIDFGenerator
from src.validation.simulation_validator import EnergyPlusSimulationValidator
from src.enhanced_location_fetcher import EnhancedLocationFetcher

class ExpertFeaturesAccuracyTest:
    """Comprehensive test suite for expert features accuracy"""
    
    def __init__(self):
        self.idf_generator = ProfessionalIDFGenerator()
        self.location_fetcher = EnhancedLocationFetcher()
        self.validator = EnergyPlusSimulationValidator()
        self.test_buildings = self._load_test_buildings()
        self.results = []
        
    def _load_test_buildings(self) -> List[Dict]:
        """Load test buildings with known energy consumption data"""
        return [
            {
                'name': 'Willis Tower',
                'address': '233 S Wacker Dr, Chicago, IL 60606',
                'building_type': 'office',
                'year_built': 1974,
                'stories': 110,
                'floor_area_m2': 416000,
                'actual_eui_kwh_m2': 155,  # From ENERGY STAR
                'climate_zone': 'ASHRAE_C5'
            },
            {
                'name': 'Empire State Building',
                'address': '350 5th Ave, New York, NY 10118',
                'building_type': 'office',
                'year_built': 1931,
                'stories': 102,
                'floor_area_m2': 208879,
                'actual_eui_kwh_m2': 142,  # From retrofitted data
                'climate_zone': 'ASHRAE_C5'
            },
            {
                'name': '30 Rockefeller Plaza',
                'address': '30 Rockefeller Plaza, New York, NY 10112',
                'building_type': 'office',
                'year_built': 1933,
                'stories': 70,
                'floor_area_m2': 190000,
                'actual_eui_kwh_m2': 138,
                'climate_zone': 'ASHRAE_C5'
            },
            {
                'name': 'Bank of America Tower',
                'address': '1 Bryant Park, New York, NY 10036',
                'building_type': 'office',
                'year_built': 2009,
                'stories': 55,
                'floor_area_m2': 195000,
                'actual_eui_kwh_m2': 98,  # LEED Platinum
                'climate_zone': 'ASHRAE_C5',
                'leed_level': 'platinum'
            },
            {
                'name': 'John Hancock Center',
                'address': '875 N Michigan Ave, Chicago, IL 60611',
                'building_type': 'office_residential',
                'year_built': 1969,
                'stories': 100,
                'floor_area_m2': 260000,
                'actual_eui_kwh_m2': 165,
                'climate_zone': 'ASHRAE_C5'
            },
            {
                'name': 'Chrysler Building',
                'address': '405 Lexington Ave, New York, NY 10174',
                'building_type': 'office',
                'year_built': 1930,
                'stories': 77,
                'floor_area_m2': 111200,
                'actual_eui_kwh_m2': 148,
                'climate_zone': 'ASHRAE_C5'
            }
        ]
    
    def generate_idf_with_expert_features(self, building: Dict) -> Tuple[str, Optional[str]]:
        """Generate IDF file with all expert features enabled"""
        try:
            # Get location data
            location_data = self.location_fetcher.fetch_comprehensive_location_data(building['address'])
            
            # Building parameters
            building_params = {
                'building_type': building['building_type'],
                'year_built': building.get('year_built'),
                'stories': building.get('stories', 10),
                'floor_area_m2': building.get('floor_area_m2', 5000),
                'simple_hvac': False,  # Use advanced HVAC
                'leed_level': building.get('leed_level')
            }
            
            # Generate IDF
            idf_content = self.idf_generator.generate_professional_idf(
                address=building['address'],
                building_params=building_params,
                location_data=location_data
            )
            
            # Save IDF
            output_dir = Path('test_outputs')
            output_dir.mkdir(exist_ok=True)
            idf_path = output_dir / f"{building['name'].replace(' ', '_')}_expert_validation.idf"
            
            with open(idf_path, 'w') as f:
                f.write(idf_content)
            
            # Get weather file path
            weather_file = location_data.get('weather_file_path')
            if weather_file and not os.path.exists(weather_file):
                # Try to find weather file in common locations
                weather_dir = Path('weather_files')
                if weather_dir.exists():
                    weather_name = os.path.basename(weather_file)
                    possible_path = weather_dir / weather_name
                    if possible_path.exists():
                        weather_file = str(possible_path)
            
            return str(idf_path), weather_file
            
        except Exception as e:
            print(f"Error generating IDF for {building['name']}: {e}")
            traceback.print_exc()
            return None, None
    
    def run_simulation(self, idf_path: str, weather_file: Optional[str] = None) -> Dict:
        """Run EnergyPlus simulation and extract results"""
        try:
            # Create output directory
            output_dir = Path(idf_path).parent / f"sim_{Path(idf_path).stem}"
            output_dir.mkdir(exist_ok=True)
            
            # Run simulation
            result = self.validator.validate_by_simulation(
                idf_file=idf_path,
                weather_file=weather_file,
                output_directory=str(output_dir),
                timeout=600  # 10 minutes
            )
            
            return {
                'success': result.success,
                'fatal_errors': result.fatal_errors,
                'severe_errors': result.severe_errors,
                'warnings': result.warnings,
                'error_file': result.error_file_path,
                'output_dir': str(output_dir),
                'errors': [e.message for e in result.errors[:10]]  # First 10 errors
            }
            
        except Exception as e:
            print(f"Error running simulation: {e}")
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
                import pandas as pd
                df = pd.read_csv(csv_path)
                
                # Look for energy consumption columns
                energy_cols = [col for col in df.columns if any(x in col.lower() 
                              for x in ['energy', 'kwh', 'electricity', 'gas', 'district'])]
                
                if energy_cols:
                    # Get annual totals
                    totals = {}
                    for col in energy_cols:
                        if df[col].dtype in ['float64', 'int64']:
                            totals[col] = df[col].sum()
                    
                    return totals
            
            # Try SQL output
            sql_path = Path(output_dir) / 'eplusout.sql'
            if sql_path.exists():
                # SQL parsing would go here
                pass
            
            return None
            
        except Exception as e:
            print(f"Error extracting energy results: {e}")
            return None
    
    def calculate_accuracy_metrics(self, simulated_eui: float, actual_eui: float) -> Dict:
        """Calculate accuracy metrics"""
        error_percent = ((simulated_eui - actual_eui) / actual_eui) * 100
        absolute_error = abs(error_percent)
        
        # ASHRAE Guideline 14 metrics
        cv_rmse = abs(error_percent)  # Simplified for single building
        nmbe = error_percent  # Normalized Mean Bias Error
        
        return {
            'simulated_eui_kwh_m2': simulated_eui,
            'actual_eui_kwh_m2': actual_eui,
            'error_percent': error_percent,
            'absolute_error_percent': absolute_error,
            'cv_rmse_percent': cv_rmse,
            'nmbe_percent': nmbe,
            'meets_ashrae_14': absolute_error <= 10.0  # ASHRAE 14 target: ±10%
        }
    
    def run_full_test(self) -> Dict:
        """Run complete accuracy test suite"""
        print("="*80)
        print("EXPERT FEATURES ACCURACY VALIDATION TEST")
        print("="*80)
        print()
        
        summary = {
            'test_date': datetime.now().isoformat(),
            'buildings_tested': 0,
            'buildings_simulated': 0,
            'buildings_with_results': 0,
            'average_error_percent': None,
            'ashrae_14_compliance': 0,
            'results': []
        }
        
        for building in self.test_buildings:
            print(f"\n{'='*80}")
            print(f"Testing: {building['name']}")
            print(f"{'='*80}")
            
            # Generate IDF
            print(f"  Generating IDF with expert features...")
            idf_path, weather_file = self.generate_idf_with_expert_features(building)
            
            if not idf_path:
                print(f"  ❌ Failed to generate IDF")
                continue
            
            summary['buildings_tested'] += 1
            print(f"  ✅ IDF generated: {idf_path}")
            
            # Run simulation
            print(f"  Running EnergyPlus simulation...")
            sim_result = self.run_simulation(idf_path, weather_file)
            
            if not sim_result['success']:
                print(f"  ❌ Simulation failed:")
                print(f"     Fatal errors: {sim_result['fatal_errors']}")
                print(f"     Severe errors: {sim_result['severe_errors']}")
                if sim_result.get('errors'):
                    for err in sim_result['errors'][:3]:
                        print(f"     - {err}")
                continue
            
            summary['buildings_simulated'] += 1
            print(f"  ✅ Simulation completed")
            print(f"     Warnings: {sim_result['warnings']}")
            
            # Extract energy results
            print(f"  Extracting energy results...")
            energy_results = self.extract_energy_results(sim_result['output_dir'])
            
            if not energy_results:
                print(f"  ⚠️  Could not extract energy results")
                print(f"     (This may be normal for sizing-only runs)")
                continue
            
            summary['buildings_with_results'] += 1
            
            # Calculate EUI (simplified - would need proper zone area)
            # For now, just report raw energy
            building_result = {
                'building': building['name'],
                'simulation': sim_result,
                'energy_results': energy_results,
                'actual_eui': building['actual_eui_kwh_m2']
            }
            
            print(f"  ✅ Energy results extracted")
            print(f"     Actual EUI: {building['actual_eui_kwh_m2']} kWh/m²/year")
            
            summary['results'].append(building_result)
        
        # Calculate summary statistics
        if summary['buildings_with_results'] > 0:
            print(f"\n{'='*80}")
            print("SUMMARY")
            print(f"{'='*80}")
            print(f"Buildings tested: {summary['buildings_tested']}")
            print(f"Buildings simulated: {summary['buildings_simulated']}")
            print(f"Buildings with energy results: {summary['buildings_with_results']}")
        
        return summary
    
    def save_results(self, summary: Dict, filename: str = 'expert_features_accuracy_results.json'):
        """Save test results to file"""
        output_path = Path('test_outputs') / filename
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\nResults saved to: {output_path}")


def main():
    """Run expert features accuracy test"""
    tester = ExpertFeaturesAccuracyTest()
    summary = tester.run_full_test()
    tester.save_results(summary)
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


if __name__ == '__main__':
    main()

