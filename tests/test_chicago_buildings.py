"""
Chicago Buildings Accuracy Test - Expert Features Validation
Tests 5 major Chicago buildings with known energy consumption data
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.professional_idf_generator import ProfessionalIDFGenerator
from src.validation.simulation_validator import EnergyPlusSimulationValidator
from src.enhanced_location_fetcher import EnhancedLocationFetcher

# Chicago weather file paths found on system
CHICAGO_WEATHER_FILES = [
    "/Users/giovanniamenta/IDF - CREATOR /artifacts/desktop_files/weather/Chicago.epw",
    "/Users/giovanniamenta/IDF - CREATOR /artifacts/desktop_files/weather/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw",
    "/Users/giovanniamenta/energyplus test/EnergyPlus-MCP/energyplus-mcp-server/illustrative examples/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw"
]

class ChicagoBuildingsTest:
    """Test suite for Chicago buildings with expert features"""
    
    def __init__(self):
        self.idf_generator = ProfessionalIDFGenerator()
        self.location_fetcher = EnhancedLocationFetcher()
        self.validator = EnergyPlusSimulationValidator()
        
        # Find available Chicago weather file
        self.chicago_weather = None
        for weather_path in CHICAGO_WEATHER_FILES:
            if os.path.exists(weather_path):
                self.chicago_weather = weather_path
                print(f"✓ Found Chicago weather file: {weather_path}")
                break
        
        if not self.chicago_weather:
            print("⚠️  Warning: No Chicago weather file found, simulations may fail")
        
        self.test_buildings = [
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
                'name': 'Aon Center',
                'address': '200 E Randolph St, Chicago, IL 60601',
                'building_type': 'office',
                'year_built': 1973,
                'stories': 83,
                'floor_area_m2': 140000,
                'actual_eui_kwh_m2': 150,
                'climate_zone': 'ASHRAE_C5'
            },
            {
                'name': 'Trump International Hotel',
                'address': '401 N Wabash Ave, Chicago, IL 60611',
                'building_type': 'hotel',
                'year_built': 2009,
                'stories': 98,
                'floor_area_m2': 270000,
                'actual_eui_kwh_m2': 120,
                'climate_zone': 'ASHRAE_C5'
            },
            {
                'name': 'Aqua Tower',
                'address': '225 N Columbus Dr, Chicago, IL 60601',
                'building_type': 'residential_multi',
                'year_built': 2009,
                'stories': 82,
                'floor_area_m2': 195000,
                'actual_eui_kwh_m2': 110,
                'climate_zone': 'ASHRAE_C5'
            }
        ]
        
        self.results = []
    
    def generate_idf(self, building: Dict) -> Tuple[str, Optional[str]]:
        """Generate IDF file with expert features"""
        try:
            print(f"\n📍 Generating IDF for {building['name']}...")
            location_data = self.location_fetcher.fetch_comprehensive_location_data(building['address'])
            
            building_params = {
                'building_type': building['building_type'],
                'year_built': building.get('year_built'),
                'stories': building.get('stories', 10),
                'floor_area_m2': building.get('floor_area_m2', 5000),
                'simple_hvac': False,
                'leed_level': building.get('leed_level')
            }
            
            idf_content = self.idf_generator.generate_professional_idf(
                address=building['address'],
                building_params=building_params,
                location_data=location_data
            )
            
            output_dir = Path('test_outputs')
            output_dir.mkdir(exist_ok=True)
            idf_path = output_dir / f"{building['name'].replace(' ', '_')}_chicago.idf"
            
            with open(idf_path, 'w') as f:
                f.write(idf_content)
            
            print(f"  ✅ IDF generated: {idf_path}")
            return str(idf_path), self.chicago_weather
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def run_simulation(self, idf_path: str, weather_file: Optional[str] = None) -> Dict:
        """Run EnergyPlus simulation"""
        try:
            output_dir = Path(idf_path).parent / f"sim_{Path(idf_path).stem}"
            output_dir.mkdir(exist_ok=True)
            
            print(f"  🔄 Running simulation...")
            result = self.validator.validate_by_simulation(
                idf_file=idf_path,
                weather_file=weather_file,
                output_directory=str(output_dir),
                timeout=600
            )
            
            return {
                'success': result.success,
                'fatal_errors': result.fatal_errors,
                'severe_errors': result.severe_errors,
                'warnings': result.warnings,
                'output_dir': str(output_dir),
                'errors': [e.message for e in result.errors[:5]]
            }
            
        except Exception as e:
            print(f"  ❌ Simulation error: {e}")
            return {
                'success': False,
                'fatal_errors': 1,
                'severe_errors': 0,
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
                
                # Find annual energy columns
                energy_data = {}
                for col in df.columns:
                    col_lower = col.lower()
                    if any(x in col_lower for x in ['electricity', 'energy', 'kwh', 'total site']):
                        try:
                            energy_data[col] = float(df[col].sum())
                        except:
                            pass
                
                return energy_data
            
            # Try tabular summary
            tab_path = Path(output_dir) / 'eplusout.tab'
            if tab_path.exists():
                # Parse tabular output for annual energy
                with open(tab_path, 'r') as f:
                    content = f.read()
                    # Look for annual energy values
                    import re
                    energy_match = re.search(r'Total Site Energy\s+([\d,]+\.\d+)', content)
                    if energy_match:
                        return {'Total Site Energy (kWh)': float(energy_match.group(1).replace(',', ''))}
            
            return None
            
        except Exception as e:
            print(f"  ⚠️  Could not extract energy: {e}")
            return None
    
    def calculate_eui(self, total_energy_kwh: float, floor_area_m2: float) -> float:
        """Calculate Energy Use Intensity"""
        if floor_area_m2 > 0:
            return total_energy_kwh / floor_area_m2
        return 0.0
    
    def run_all_tests(self):
        """Run tests for all Chicago buildings"""
        print("="*80)
        print("CHICAGO BUILDINGS EXPERT FEATURES TEST")
        print("="*80)
        print(f"Weather file: {self.chicago_weather}")
        print(f"Buildings to test: {len(self.test_buildings)}")
        print("="*80)
        
        summary = {
            'test_date': datetime.now().isoformat(),
            'weather_file': self.chicago_weather,
            'buildings_tested': 0,
            'buildings_simulated': 0,
            'buildings_with_results': 0,
            'results': []
        }
        
        for building in self.test_buildings:
            print(f"\n{'='*80}")
            print(f"Testing: {building['name']}")
            print(f"{'='*80}")
            
            # Generate IDF
            idf_path, weather = self.generate_idf(building)
            if not idf_path:
                continue
            
            summary['buildings_tested'] += 1
            
            # Run simulation
            sim_result = self.run_simulation(idf_path, weather)
            
            if not sim_result['success']:
                print(f"  ❌ Simulation failed:")
                print(f"     Fatal: {sim_result['fatal_errors']}, Severe: {sim_result['severe_errors']}")
                if sim_result.get('errors'):
                    for err in sim_result['errors'][:2]:
                        print(f"     - {err[:100]}")
                summary['results'].append({
                    'building': building['name'],
                    'status': 'simulation_failed',
                    'errors': sim_result['errors'][:3]
                })
                continue
            
            summary['buildings_simulated'] += 1
            print(f"  ✅ Simulation completed (Warnings: {sim_result['warnings']})")
            
            # Extract energy results
            energy_results = self.extract_energy_results(sim_result['output_dir'])
            
            if energy_results:
                summary['buildings_with_results'] += 1
                
                # Calculate EUI
                total_energy = sum(v for v in energy_results.values() if isinstance(v, (int, float)))
                simulated_eui = self.calculate_eui(total_energy, building['floor_area_m2'])
                actual_eui = building['actual_eui_kwh_m2']
                
                error_percent = ((simulated_eui - actual_eui) / actual_eui * 100) if actual_eui > 0 else 0
                
                print(f"  📊 Energy Results:")
                print(f"     Simulated EUI: {simulated_eui:.1f} kWh/m²/year")
                print(f"     Actual EUI: {actual_eui:.1f} kWh/m²/year")
                print(f"     Error: {error_percent:+.1f}%")
                
                summary['results'].append({
                    'building': building['name'],
                    'status': 'success',
                    'simulated_eui': simulated_eui,
                    'actual_eui': actual_eui,
                    'error_percent': error_percent,
                    'total_energy_kwh': total_energy,
                    'energy_breakdown': energy_results
                })
            else:
                print(f"  ⚠️  Could not extract energy results")
                summary['results'].append({
                    'building': building['name'],
                    'status': 'no_energy_data'
                })
        
        # Summary
        print(f"\n{'='*80}")
        print("TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Buildings tested: {summary['buildings_tested']}/{len(self.test_buildings)}")
        print(f"Buildings simulated: {summary['buildings_simulated']}/{len(self.test_buildings)}")
        print(f"Buildings with results: {summary['buildings_with_results']}/{len(self.test_buildings)}")
        
        if summary['buildings_with_results'] > 0:
            successful = [r for r in summary['results'] if r.get('status') == 'success']
            if successful:
                avg_error = sum(r['error_percent'] for r in successful) / len(successful)
                print(f"\n📊 Accuracy Results:")
                print(f"   Average Error: {avg_error:.1f}%")
                print(f"   ASHRAE 14 Target: ≤10.0%")
                print(f"   Meets Target: {'✅ YES' if abs(avg_error) <= 10.0 else '⚠️  NO'}")
                
                print(f"\n📋 Building-by-Building:")
                for result in successful:
                    print(f"   • {result['building']}: {result['error_percent']:+.1f}% error")
        
        # Save results
        output_file = Path('test_outputs') / 'chicago_buildings_results.json'
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n✅ Results saved to: {output_file}")
        
        return summary


def main():
    """Run Chicago buildings test"""
    tester = ChicagoBuildingsTest()
    summary = tester.run_all_tests()
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()














