#!/usr/bin/env python3
"""
Calibration script to adjust IDF Creator parameters to match PDF report benchmarks.
Iteratively adjusts building parameters until results match report within tolerance.
"""

import json
import os
import sys
from pathlib import Path
from test_pdf_benchmark import PDFReportExtractor, EnergyPlusSimulator, BenchmarkComparator
from main import IDFCreator
from src.calibration_system import CalibrationSystem


class BuildingCalibrator:
    """Calibrate building parameters to match report benchmarks"""
    
    def __init__(self, report_data: dict, target_eui_tolerance: float = 0.10):
        self.report_data = report_data
        self.target_eui = report_data.get('site_eui_kbtu_sqft', report_data.get('current_eui_kbtu_sqft', 90))
        self.target_total_kwh = report_data.get('baseline_total_site_energy_kwh', 0)
        self.target_eui_tolerance = target_eui_tolerance
        self.simulator = EnergyPlusSimulator()
        
        # Universal calibration system (works for all building types)
        self.calibration_system = CalibrationSystem()
        building_type = report_data.get('building_type', 'Office').lower()
        
        # Get base parameters from building type templates
        # These are ASHRAE 90.1 defaults that will be calibrated
        self.params = {
            'lighting_power_density': 10.8,  # W/m² (ASHRAE 90.1 office default)
            'equipment_power_density': 8.1,  # W/m² (ASHRAE 90.1 office default)
            'occupancy_density': 0.05,  # people/m² (ASHRAE 90.1 office default)
            'hvac_efficiency_multiplier': 1.0,
            'infiltration_rate': 0.0003,
            'window_to_wall_ratio': 0.3,
        }
        
        # Apply any existing calibration factors for this building type
        existing_factors = self.calibration_system.get_calibration_factors(building_type)
        if existing_factors:
            print(f"📊 Using existing calibration factors for {building_type}:")
            for key, value in existing_factors.items():
                if 'multiplier' in key:
                    print(f"   {key}: {value:.3f}")
        
    def generate_idf_with_params(self, base_params: dict, calibration_params: dict) -> str:
        """Generate IDF with calibrated parameters"""
        creator = IDFCreator(enhanced=True, professional=True)
        
        # Merge parameters
        user_params = {
            'building_type': base_params.get('building_type', 'Office'),
            'stories': base_params.get('floors', 12),
            'floor_area_per_story_m2': base_params.get('area_m2', 9290.3) / base_params.get('floors', 12),
            'force_area': True,
            # Add calibration parameters
            'lighting_power_density': calibration_params.get('lighting_power_density', 10.0),
            'equipment_power_density': calibration_params.get('equipment_power_density', 8.0),
            'occupancy_density': calibration_params.get('occupancy_density', 0.05),
        }
        
        output_dir = Path('artifacts/calibration_test')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        idf_path = creator.create_idf(
            address=base_params['address'],
            user_params=user_params,
            output_path=str(output_dir / 'calibrated_building.idf')
        )
        
        return idf_path
    
    def run_calibration_iteration(self, iteration: int, params: dict) -> dict:
        """Run one calibration iteration"""
        print(f"\n{'='*80}")
        print(f"ITERATION {iteration}")
        print(f"{'='*80}")
        
        # Generate IDF
        print("\n[1/4] Generating IDF with calibrated parameters...")
        idf_path = self.generate_idf_with_params(self.report_data, params)
        
        if not idf_path or not os.path.exists(idf_path):
            return {'error': 'Failed to generate IDF'}
        
        print(f"✓ IDF generated: {idf_path}")
        
        # Run simulation
        print("\n[2/4] Running simulation...")
        sim_output_dir = Path('artifacts/calibration_test') / f'simulation_iter_{iteration}'
        sim_result = self.simulator.run_simulation(
            idf_path=str(idf_path),
            output_dir=str(sim_output_dir)
        )
        
        if 'error' in sim_result or not sim_result.get('success'):
            return {'error': f"Simulation failed: {sim_result.get('error', 'Unknown error')}"}
        
        print(f"✓ Simulation completed")
        
        # Extract results
        print("\n[3/4] Extracting energy results...")
        energy_results = self.simulator.extract_energy_results(str(sim_output_dir))
        
        if not energy_results or 'error' in energy_results:
            return {'error': 'Failed to extract energy results'}
        
        sim_eui = energy_results.get('eui_kbtu_sqft', 0)
        sim_total_kwh = energy_results.get('total_site_energy_kwh', 0)
        
        print(f"✓ Simulated EUI: {sim_eui:.1f} kBtu/sqft")
        print(f"✓ Simulated Total: {sim_total_kwh:,.0f} kWh")
        
        # Compare with targets
        print("\n[4/4] Comparing with targets...")
        eui_error = ((sim_eui - self.target_eui) / self.target_eui) * 100
        total_error = ((sim_total_kwh - self.target_total_kwh) / self.target_total_kwh) * 100 if self.target_total_kwh > 0 else 0
        
        print(f"  Target EUI: {self.target_eui:.1f} kBtu/sqft")
        print(f"  EUI Error: {eui_error:+.1f}%")
        print(f"  Target Total: {self.target_total_kwh:,.0f} kWh")
        print(f"  Total Error: {total_error:+.1f}%")
        
        return {
            'iteration': iteration,
            'params': params.copy(),
            'simulated_eui': sim_eui,
            'simulated_total_kwh': sim_total_kwh,
            'eui_error_percent': eui_error,
            'total_error_percent': total_error,
            'energy_results': energy_results,
            'converged': abs(eui_error) <= self.target_eui_tolerance * 100
        }
    
    def adjust_parameters(self, current_result: dict, previous_result: dict = None) -> dict:
        """Adjust parameters based on current results - uses intelligent calibration"""
        new_params = current_result['params'].copy()
        eui_error = current_result['eui_error_percent']
        total_error = current_result['total_error_percent']
        
        # Calculate adjustment factor based on error magnitude
        # More aggressive for larger errors
        if abs(eui_error) > 50:
            adjustment_factor = 0.6  # Large error - big adjustment
        elif abs(eui_error) > 20:
            adjustment_factor = 0.75  # Medium error
        else:
            adjustment_factor = 0.85  # Small error - fine tuning
        
        # If EUI is too high, reduce loads or improve efficiency
        if eui_error > 10:  # More than 10% too high
            # Calculate target reduction - more conservative
            # Don't reduce more than 50% per iteration
            max_reduction = 0.5
            target_reduction = max(1.0 - (abs(eui_error) / 100) * adjustment_factor, max_reduction)
            
            # Reduce lighting power density (but keep minimum of 3 W/m²)
            new_params['lighting_power_density'] = max(
                new_params['lighting_power_density'] * target_reduction,
                3.0  # Minimum reasonable value
            )
            # Reduce equipment power density (but keep minimum of 2 W/m²)
            new_params['equipment_power_density'] = max(
                new_params['equipment_power_density'] * target_reduction,
                2.0  # Minimum reasonable value
            )
            # Improve HVAC efficiency (inverse relationship, but cap at 2.0)
            new_params['hvac_efficiency_multiplier'] = min(
                new_params['hvac_efficiency_multiplier'] * (2.0 - target_reduction),
                2.0  # Maximum reasonable multiplier
            )
            
            print(f"\n📉 Reducing loads (EUI {eui_error:+.1f}% too high):")
            print(f"  Adjustment factor: {adjustment_factor:.2f}")
            print(f"  Lighting: {current_result['params']['lighting_power_density']:.2f} → {new_params['lighting_power_density']:.2f} W/m²")
            print(f"  Equipment: {current_result['params']['equipment_power_density']:.2f} → {new_params['equipment_power_density']:.2f} W/m²")
            print(f"  HVAC Efficiency: {current_result['params']['hvac_efficiency_multiplier']:.3f} → {new_params['hvac_efficiency_multiplier']:.3f}")
        
        elif eui_error < -10:  # More than 10% too low
            # Calculate target increase
            target_increase = 1.0 + (abs(eui_error) / 100) * adjustment_factor
            
            # Increase loads
            new_params['lighting_power_density'] *= target_increase
            new_params['equipment_power_density'] *= target_increase
            # Reduce HVAC efficiency
            new_params['hvac_efficiency_multiplier'] *= (2.0 - target_increase)
            
            print(f"\n📈 Increasing loads (EUI {eui_error:+.1f}% too low):")
            print(f"  Adjustment factor: {adjustment_factor:.2f}")
            print(f"  Lighting: {current_result['params']['lighting_power_density']:.2f} → {new_params['lighting_power_density']:.2f} W/m²")
            print(f"  Equipment: {current_result['params']['equipment_power_density']:.2f} → {new_params['equipment_power_density']:.2f} W/m²")
        
        # Fine-tuning based on previous iteration
        if previous_result:
            prev_eui_error = previous_result['eui_error_percent']
            # If error is getting worse, use smaller steps
            if abs(eui_error) > abs(prev_eui_error):
                print(f"  ⚠️  Error increasing, using smaller adjustment steps")
                # Reduce adjustment by 50%
                if eui_error > 0:
                    new_params['lighting_power_density'] *= 0.95
                    new_params['equipment_power_density'] *= 0.95
                else:
                    new_params['lighting_power_density'] *= 1.05
                    new_params['equipment_power_density'] *= 1.05
        
        return new_params
    
    def calibrate(self, max_iterations: int = 10) -> dict:
        """Run calibration iterations until convergence"""
        results = []
        current_params = self.params.copy()
        
        for iteration in range(1, max_iterations + 1):
            result = self.run_calibration_iteration(iteration, current_params)
            
            if 'error' in result:
                print(f"\n❌ Error in iteration {iteration}: {result['error']}")
                break
            
            results.append(result)
            
            # Check convergence
            if result['converged']:
                print(f"\n✅ CONVERGED! EUI error: {result['eui_error_percent']:.1f}%")
                break
            
            # Adjust parameters for next iteration
            previous_result = results[-2] if len(results) > 1 else None
            current_params = self.adjust_parameters(result, previous_result)
        
        return {
            'results': results,
            'final_params': current_params,
            'converged': results[-1]['converged'] if results else False
        }


def main():
    """Main calibration function"""
    print("="*80)
    print("BUILDING CALIBRATION TO PDF REPORT")
    print("="*80)
    
    # Extract report data
    pdf_path = '/Users/giovanniamenta/Downloads/COMreportSample20160127 (1).pdf'
    extractor = PDFReportExtractor(pdf_path)
    report_data = extractor.extract_all_data()
    
    print(f"\nTarget EUI: {report_data.get('site_eui_kbtu_sqft', 90):.1f} kBtu/sqft")
    print(f"Target Total Energy: {report_data.get('baseline_total_site_energy_kwh', 0):,.0f} kWh")
    
    # Run calibration
    calibrator = BuildingCalibrator(report_data, target_eui_tolerance=0.15)  # 15% tolerance
    calibration_results = calibrator.calibrate(max_iterations=8)  # Limit iterations
    
    # Save results
    output_dir = Path('artifacts/calibration_test')
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / 'calibration_results.json', 'w') as f:
        json.dump(calibration_results, f, indent=2)
    
    # Calculate and save calibration factors for future use
    if calibration_results['results']:
        final = calibration_results['results'][-1]
        building_type = report_data.get('building_type', 'Office')
        
        # Calculate calibration factors from final results
        factors = calibrator.calibration_system.calculate_factors_from_benchmark(
            simulated_eui=final['simulated_eui'],
            target_eui=calibrator.target_eui,
            simulated_total=final['simulated_total_kwh'],
            target_total=calibrator.target_total_kwh,
            energy_breakdown=final.get('energy_results', {}).get('end_uses', {})
        )
        
        # Update calibration system with learned factors
        calibrator.calibration_system.update_calibration_factors(
            building_type=building_type,
            factors=factors,
            learning_rate=0.7  # Weight new factors heavily
        )
        
        print("\n" + "="*80)
        print("CALIBRATION COMPLETE")
        print("="*80)
        print(f"\nResults saved to: {output_dir}")
        print(f"\n📊 Calibration factors saved for future {building_type} buildings:")
        for key, value in factors.items():
            print(f"   {key}: {value:.3f}")
        
        if calibration_results['converged']:
            print(f"\n✅ CONVERGED! EUI error: {final['eui_error_percent']:+.1f}%")
            print(f"✅ Final EUI: {final['simulated_eui']:.1f} kBtu/sqft (target: {calibrator.target_eui:.1f})")
            print(f"✅ Final Total: {final['simulated_total_kwh']:,.0f} kWh (target: {calibrator.target_total_kwh:,.0f})")
        else:
            print("\n⚠️  Calibration did not fully converge")
            print(f"   Final EUI: {final['simulated_eui']:.1f} kBtu/sqft (target: {calibrator.target_eui:.1f})")
            print(f"   EUI Error: {final['eui_error_percent']:+.1f}%")
            print(f"   Final Total: {final['simulated_total_kwh']:,.0f} kWh")
        
        print(f"\n💾 Calibration factors saved to: {calibrator.calibration_system.calibration_file}")
        print("   These factors will be automatically applied to future buildings of the same type!")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

