#!/usr/bin/env python3
"""
Convergence Workflow - Automatically calibrate IDF models to match benchmark targets.
Iteratively adjusts building parameters until energy results converge to target values.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.calibration_system import CalibrationSystem
from src.apply_calibration_to_idf import apply_calibration_to_idf
from tests.test_pdf_benchmark import EnergyPlusSimulator
from main import IDFCreator


class ConvergenceWorkflow:
    """Workflow to converge simulated energy results to target benchmarks"""
    
    def __init__(self, target_tolerance: float = 0.15):
        """
        Initialize convergence workflow.
        
        Args:
            target_tolerance: Target error tolerance (e.g., 0.15 = 15%)
        """
        self.target_tolerance = target_tolerance
        self.calibration_system = CalibrationSystem()
        self.simulator = EnergyPlusSimulator()
        
    def run_convergence(self, test_number: int, test_data: Dict, 
                       initial_idf_path: str, weather_file: str,
                       max_iterations: int = 5) -> Dict:
        """
        Run convergence iterations for a single test.
        
        Args:
            test_number: Test number
            test_data: Test data with target values
            initial_idf_path: Path to initial IDF file
            weather_file: Path to weather file
            max_iterations: Maximum number of calibration iterations
            
        Returns:
            Dictionary with convergence results
        """
        target_energy = test_data.get('annual_electric_kwh', 0)
        target_eui = test_data.get('eui_kbtu_sqft', 0)
        building_type = test_data.get('building_type', 'Office').lower()
        
        if not target_energy and not target_eui:
            return {
                'success': False,
                'error': 'No target values available for convergence'
            }
        
        print(f"\n{'='*70}")
        print(f"CONVERGENCE WORKFLOW - Test {test_number}")
        print(f"{'='*70}")
        print(f"Target Energy: {target_energy:,.0f} kWh")
        print(f"Target EUI: {target_eui:.1f} kBtu/sqft")
        print(f"Tolerance: ±{self.target_tolerance*100:.0f}%")
        
        # Baseline simulation
        print(f"\n[Iteration 0] Baseline simulation...")
        baseline_results = self._simulate_idf(initial_idf_path, weather_file)
        
        if not baseline_results:
            return {'success': False, 'error': 'Baseline simulation failed'}
        
        sim_energy = baseline_results.get('total_site_energy_kwh', 0)
        sim_eui = baseline_results.get('eui_kbtu_sqft', 0)
        
        energy_error = ((sim_energy - target_energy) / target_energy * 100) if target_energy > 0 else 0
        eui_error = ((sim_eui - target_eui) / target_eui * 100) if target_eui > 0 else 0
        
        print(f"  Simulated Energy: {sim_energy:,.0f} kWh (Error: {energy_error:+.1f}%)")
        print(f"  Simulated EUI: {sim_eui:.1f} kBtu/sqft (Error: {eui_error:+.1f}%)")
        
        # Check if already converged
        if abs(energy_error) <= self.target_tolerance * 100 and abs(eui_error) <= self.target_tolerance * 100:
            print(f"\n✅ Already converged within tolerance!")
            return {
                'success': True,
                'converged': True,
                'iterations': 0,
                'final_energy_error': energy_error,
                'final_eui_error': eui_error,
                'final_idf_path': initial_idf_path
            }
        
        # Calibration iterations
        current_idf = initial_idf_path
        iteration = 0
        previous_error = abs(energy_error) + abs(eui_error)
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n[Iteration {iteration}] Calibrating...")
            
            # Calculate calibration factors
            factors = self.calibration_system.calculate_factors_from_benchmark(
                simulated_eui=sim_eui,
                target_eui=target_eui,
                simulated_total=sim_energy,
                target_total=target_energy,
                energy_breakdown=baseline_results.get('end_uses')
            )
            
            print(f"  Calibration factors:")
            for key, value in factors.items():
                if isinstance(value, float):
                    print(f"    {key}: {value:.3f}")
            
            # Apply calibration to IDF
            output_dir = Path(initial_idf_path).parent
            calibrated_idf = str(output_dir / f"building_iter{iteration}.idf")
            apply_calibration_to_idf(current_idf, factors, calibrated_idf)
            
            # Simulate calibrated IDF
            calibrated_results = self._simulate_idf(calibrated_idf, weather_file)
            
            if not calibrated_results:
                print(f"  ⚠️  Calibrated simulation failed, using previous iteration")
                break
            
            new_sim_energy = calibrated_results.get('total_site_energy_kwh', 0)
            new_sim_eui = calibrated_results.get('eui_kbtu_sqft', 0)
            
            new_energy_error = ((new_sim_energy - target_energy) / target_energy * 100) if target_energy > 0 else 0
            new_eui_error = ((new_sim_eui - target_eui) / target_eui * 100) if target_eui > 0 else 0
            
            new_total_error = abs(new_energy_error) + abs(new_eui_error)
            
            print(f"  Simulated Energy: {new_sim_energy:,.0f} kWh (Error: {new_energy_error:+.1f}%)")
            print(f"  Simulated EUI: {new_sim_eui:.1f} kBtu/sqft (Error: {new_eui_error:+.1f}%)")
            
            # Check convergence
            if abs(new_energy_error) <= self.target_tolerance * 100 and abs(new_eui_error) <= self.target_tolerance * 100:
                print(f"\n✅ CONVERGED after {iteration} iteration(s)!")
                return {
                    'success': True,
                    'converged': True,
                    'iterations': iteration,
                    'final_energy_error': new_energy_error,
                    'final_eui_error': new_eui_error,
                    'final_idf_path': calibrated_idf,
                    'calibration_factors': factors
                }
            
            # Check if improving
            if new_total_error >= previous_error * 1.1:  # Getting worse
                print(f"  ⚠️  Error increased, stopping calibration")
                break
            
            # Update for next iteration
            current_idf = calibrated_idf
            sim_energy = new_sim_energy
            sim_eui = new_sim_eui
            previous_error = new_total_error
            baseline_results = calibrated_results
        
        # Did not converge within iterations
        print(f"\n⚠️  Did not converge within {max_iterations} iterations")
        print(f"  Final Energy Error: {energy_error:+.1f}%")
        print(f"  Final EUI Error: {eui_error:+.1f}%")
        
        return {
            'success': True,
            'converged': False,
            'iterations': iteration,
            'final_energy_error': energy_error,
            'final_eui_error': eui_error,
            'final_idf_path': current_idf,
            'improved': True
        }
    
    def _simulate_idf(self, idf_path: str, weather_file: str) -> Dict:
        """Run simulation and extract results"""
        output_dir = Path(idf_path).parent / 'convergence_sim'
        output_dir.mkdir(exist_ok=True)
        
        result = self.simulator.run_simulation(idf_path, weather_file, str(output_dir))
        
        if not result.get('success'):
            return None
        
        energy_results = self.simulator.extract_energy_results(str(output_dir))
        return energy_results


def main():
    """Run convergence workflow on all passing tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run convergence workflow on benchmark tests')
    parser.add_argument('--test', type=int, help='Run convergence on specific test number')
    parser.add_argument('--tolerance', type=float, default=0.15, help='Target error tolerance (default: 0.15 = 15%)')
    parser.add_argument('--max-iterations', type=int, default=5, help='Maximum calibration iterations')
    
    args = parser.parse_args()
    
    # Load test data
    test_file = Path('artifacts/leed_benchmark_tests/benchmark_tests_combined_validated.json')
    summary_file = Path('artifacts/leed_benchmark_5_tests/summary.json')
    
    if not test_file.exists() or not summary_file.exists():
        print("❌ Test data files not found. Please run benchmark tests first.")
        return 1
    
    with open(test_file) as f:
        test_data = json.load(f)
    
    with open(summary_file) as f:
        summary = json.load(f)
    
    tests = test_data['tests']
    results = summary['results']
    
    # Initialize workflow
    workflow = ConvergenceWorkflow(target_tolerance=args.tolerance)
    
    # Determine which tests to process
    if args.test:
        test_indices = [args.test - 1]  # Convert to 0-based
    else:
        # Process all passing tests
        test_indices = [i for i, r in enumerate(results) if r.get('success')]
    
    print(f"\n{'='*70}")
    print(f"CONVERGENCE WORKFLOW - Processing {len(test_indices)} test(s)")
    print(f"{'='*70}")
    
    convergence_results = []
    
    for i in test_indices:
        test_num = i + 1
        result = results[i]
        test_info = tests[i]
        
        if not result.get('success'):
            print(f"\n⏭️  Skipping Test {test_num} (not passing)")
            continue
        
        idf_path = result.get('idf_path')
        if not idf_path or not Path(idf_path).exists():
            print(f"\n⏭️  Skipping Test {test_num} (no IDF file)")
            continue
        
        weather_file = test_info.get('weather_file')
        if not weather_file:
            print(f"\n⏭️  Skipping Test {test_num} (no weather file)")
            continue
        
        # Find weather file path
        weather_path = None
        for root in [Path('/Applications'), Path('/usr/local'), Path('artifacts/desktop_files/weather')]:
            if not root.exists():
                continue
            for ep_dir in root.glob('EnergyPlus*'):
                weather_dirs = [
                    ep_dir / 'WeatherData',
                    ep_dir / 'EnergyPlus installation files' / 'WeatherData',
                ]
                for wd in weather_dirs:
                    if wd.exists():
                        candidate = wd / weather_file
                        if candidate.exists():
                            weather_path = str(candidate)
                            break
                if weather_path:
                    break
            if weather_path:
                break
        
        if not weather_path:
            print(f"\n⏭️  Skipping Test {test_num} (weather file not found)")
            continue
        
        # Run convergence
        conv_result = workflow.run_convergence(
            test_number=test_num,
            test_data=test_info,
            initial_idf_path=idf_path,
            weather_file=weather_path,
            max_iterations=args.max_iterations
        )
        
        conv_result['test_number'] = test_num
        convergence_results.append(conv_result)
    
    # Save results
    output_file = Path('artifacts/leed_benchmark_5_tests/convergence_results.json')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(convergence_results, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"CONVERGENCE SUMMARY")
    print(f"{'='*70}")
    
    converged_count = sum(1 for r in convergence_results if r.get('converged'))
    print(f"\n✅ Converged: {converged_count}/{len(convergence_results)}")
    
    for r in convergence_results:
        status = "✅" if r.get('converged') else "⚠️"
        print(f"{status} Test {r['test_number']}: Energy Error: {r.get('final_energy_error', 0):+.1f}%, EUI Error: {r.get('final_eui_error', 0):+.1f}%")
    
    print(f"\nResults saved to: {output_file}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

