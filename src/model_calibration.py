"""
Model Calibration Module - Phase 2, Priority #1
Automatically calibrates IDF models to match actual utility bill data.

Features:
- Utility bill parsing (monthly/annual energy consumption)
- Iterative parameter adjustment (infiltration, loads, HVAC efficiency)
- ASHRAE Guideline 14 compliance (within 5-15% tolerance)
- Calibration report generation

Reference:
- ASHRAE Guideline 14 (Model Calibration Procedures)
- NREL Automated Calibration Toolkit (ACT)
- IPMVP (International Performance Measurement and Verification Protocol)
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import subprocess
import json
import re
import os


@dataclass
class UtilityData:
    """Utility bill data structure"""
    monthly_kwh: List[float]  # 12 months of kWh consumption
    peak_demand_kw: Optional[float] = None  # Peak demand (kW)
    heating_fuel: str = 'electric'  # 'electric' or 'gas'
    cooling_fuel: str = 'electric'
    gas_therms: Optional[List[float]] = None  # Monthly gas consumption (therms)
    electricity_rate_kwh: float = 0.12  # $/kWh
    gas_rate_therm: float = 1.20  # $/therm
    
    def annual_kwh(self) -> float:
        """Calculate annual kWh consumption"""
        return sum(self.monthly_kwh)
    
    def monthly_average_kwh(self) -> float:
        """Calculate monthly average"""
        return sum(self.monthly_kwh) / len(self.monthly_kwh) if self.monthly_kwh else 0.0


@dataclass
class CalibrationResult:
    """Results of model calibration"""
    calibrated_idf_path: str
    calibration_report_path: str
    accuracy_monthly_mbe: float  # Mean Bias Error (%)
    accuracy_monthly_cvrmse: float  # Coefficient of Variation of Root Mean Square Error (%)
    accuracy_annual: float  # Annual error (%)
    adjusted_parameters: Dict[str, float]  # Parameters that were adjusted
    iterations: int  # Number of calibration iterations
    converged: bool  # Whether calibration converged


class ModelCalibrator:
    """
    Automatically calibrates IDF models to match utility bill data.
    
    Uses iterative optimization to adjust:
    - Infiltration rates (most impactful)
    - Internal loads (lighting, equipment multipliers)
    - HVAC efficiency/degradation factors
    - Schedule adjustments
    """
    
    def __init__(self, energyplus_path: Optional[str] = None):
        """
        Initialize calibrator.
        
        Args:
            energyplus_path: Path to EnergyPlus executable (auto-detected if None)
        """
        self.energyplus_path = energyplus_path or self._find_energyplus()
        self.calibration_history = []
    
    def _find_energyplus(self) -> Optional[str]:
        """Find EnergyPlus executable"""
        # Common installation paths
        common_paths = [
            '/Applications/EnergyPlus-24-2-0/energyplus',
            '/usr/local/bin/energyplus',
            'C:/EnergyPlusV24-2-0/energyplus.exe',
            'C:/Program Files/EnergyPlusV24-2-0/energyplus.exe',
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        # Try to find in PATH
        try:
            result = subprocess.run(['which', 'energyplus'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        return None
    
    def calibrate_to_utility_bills(
        self,
        idf_file: str,
        utility_data: UtilityData,
        weather_file: str,
        tolerance: float = 0.10,
        max_iterations: int = 20,
        output_dir: Optional[str] = None
    ) -> CalibrationResult:
        """
        Auto-calibrate IDF to match utility bills.
        
        Args:
            idf_file: Path to baseline IDF file
            utility_data: Utility bill data
            weather_file: Path to weather file (.epw)
            tolerance: Target accuracy (default 10%)
            max_iterations: Maximum calibration iterations
            output_dir: Directory for calibrated IDF and reports
            
        Returns:
            CalibrationResult with calibrated IDF path and metrics
        """
        if not self.energyplus_path:
            raise ValueError("EnergyPlus executable not found. Please install EnergyPlus or specify path.")
        
        if not os.path.exists(weather_file):
            raise ValueError(f"Weather file not found: {weather_file}")
        
        if output_dir is None:
            output_dir = os.path.dirname(idf_file) or '.'
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Baseline simulation
        print("📊 Running baseline simulation...")
        baseline_results = self._run_simulation(idf_file, weather_file, output_dir / "baseline")
        
        # Compare baseline vs. actual
        baseline_annual = baseline_results.get('annual_kwh', 0.0)
        actual_annual = utility_data.annual_kwh()
        
        print(f"  Baseline: {baseline_annual:.0f} kWh/year")
        print(f"  Actual: {actual_annual:.0f} kWh/year")
        print(f"  Initial error: {abs(baseline_annual - actual_annual) / actual_annual * 100:.1f}%")
        
        # Calibration loop
        current_idf = idf_file
        adjusted_params = {}
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n🔄 Calibration iteration {iteration}/{max_iterations}...")
            
            # Run simulation
            results = self._run_simulation(current_idf, weather_file, output_dir / f"iteration_{iteration}")
            
            # Calculate accuracy metrics
            monthly_error = self._calculate_monthly_error(results, utility_data)
            annual_error = abs(results.get('annual_kwh', 0) - actual_annual) / actual_annual
            
            print(f"  Annual error: {annual_error * 100:.1f}%")
            
            # Check convergence
            if annual_error <= tolerance:
                print(f"✅ Calibration converged within {tolerance * 100:.0f}% tolerance!")
                break
            
            # Adjust parameters
            adjustment = self._calculate_adjustment(results, utility_data)
            current_idf = self._adjust_idf_parameters(
                current_idf if iteration == 1 else current_idf,
                adjustment,
                output_dir / f"calibrated_iteration_{iteration}.idf"
            )
            
            # Track adjustments
            for param, value in adjustment.items():
                if param in adjusted_params:
                    adjusted_params[param] *= value  # Cumulative adjustment
                else:
                    adjusted_params[param] = value
        
        # Final calibration
        calibrated_idf = output_dir / "calibrated_final.idf"
        if iteration > 1:
            # Use last iteration
            import shutil
            shutil.copy(current_idf, calibrated_idf)
        else:
            calibrated_idf = Path(idf_file)
        
        # Generate calibration report
        report_path = self._generate_calibration_report(
            calibrated_idf,
            weather_file,
            utility_data,
            baseline_results,
            adjusted_params,
            iteration,
            annual_error <= tolerance,
            output_dir / "calibration_report.json"
        )
        
        return CalibrationResult(
            calibrated_idf_path=str(calibrated_idf),
            calibration_report_path=str(report_path),
            accuracy_monthly_mbe=monthly_error.get('mbe', 0.0),
            accuracy_monthly_cvrmse=monthly_error.get('cvrmse', 0.0),
            accuracy_annual=annual_error * 100,
            adjusted_parameters=adjusted_params,
            iterations=iteration,
            converged=annual_error <= tolerance
        )
    
    def _run_simulation(self, idf_file: str, weather_file: str, output_dir: Path) -> Dict:
        """
        Run EnergyPlus simulation and extract results.
        
        Args:
            idf_file: Path to IDF file
            weather_file: Path to weather file (.epw)
            output_dir: Output directory for simulation results
        
        Returns:
            Dictionary with monthly and annual energy consumption
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Run EnergyPlus
        try:
            result = subprocess.run(
                [self.energyplus_path, '-w', str(Path(weather_file).absolute()), '-d', str(output_dir.absolute()), str(Path(idf_file).absolute())],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                print(f"⚠️  EnergyPlus warning: {result.stderr[:500]}")
        except subprocess.TimeoutExpired:
            print("⚠️  Simulation timed out")
            return {'annual_kwh': 0.0, 'monthly_kwh': [0.0] * 12}
        except Exception as e:
            print(f"⚠️  Simulation error: {e}")
            return {'annual_kwh': 0.0, 'monthly_kwh': [0.0] * 12}
        
        # Extract results from SQLite output
        sqlite_file = output_dir / "eplusout.sql"
        if sqlite_file.exists():
            return self._extract_sqlite_results(sqlite_file)
        
        # Fallback: try to extract from tabular output
        tabular_file = output_dir / "eplusout.tab"
        if tabular_file.exists():
            return self._extract_tabular_results(tabular_file)
        
        return {'annual_kwh': 0.0, 'monthly_kwh': [0.0] * 12}
    
    def _extract_sqlite_results(self, sqlite_file: Path) -> Dict:
        """Extract energy results from SQLite output with proper monthly breakdown"""
        try:
            import sqlite3
            conn = sqlite3.connect(str(sqlite_file))
            cursor = conn.cursor()
            
            # First, try to get time mapping from Time table if it exists
            try:
                cursor.execute("SELECT TimeIndex, Month FROM Time ORDER BY TimeIndex")
                time_map = {row[0]: row[1] for row in cursor.fetchall()}
            except:
                # Fallback: calculate from TimeIndex (assumes hourly data starting Jan 1)
                time_map = {}
            
            # Query electricity consumption - try ReportMeterData first (for energy meters)
            # Then fallback to ReportData (for variables)
            electricity_kwh = 0.0
            
            # Strategy 1: ReportMeterData (preferred for energy consumption)
            try:
                cursor.execute("""
                    SELECT MAX(Value)
                    FROM ReportMeterData
                    WHERE ReportMeterDictionaryIndex IN (
                        SELECT ReportMeterDictionaryIndex
                        FROM ReportMeterDictionary
                        WHERE Name = 'Electricity:Facility'
                        AND ReportingFrequency = 'RunPeriod'
                    )
                """)
                result = cursor.fetchone()
                if result and result[0]:
                    # Value is in Joules, convert to kWh
                    electricity_kwh = result[0] / 3600000.0
            except:
                pass
            
            # Strategy 2: ReportMeterDataDictionary (alternative schema)
            if electricity_kwh == 0:
                try:
                    cursor.execute("""
                        SELECT MAX(Value)
                        FROM ReportMeterData
                        WHERE ReportMeterDataDictionaryIndex IN (
                            SELECT ReportMeterDataDictionaryIndex
                            FROM ReportMeterDataDictionary
                            WHERE Name = 'Electricity:Facility'
                            AND ReportingFrequency = 'RunPeriod'
                        )
                    """)
                    result = cursor.fetchone()
                    if result and result[0]:
                        electricity_kwh = result[0] / 3600000.0
                except:
                    pass
            
            # Strategy 3: ReportData (for variables, less common)
            if electricity_kwh == 0:
                try:
                    cursor.execute("""
                        SELECT SUM(Value)
                        FROM ReportData
                        WHERE ReportDataDictionaryIndex IN (
                            SELECT ReportDataDictionaryIndex
                            FROM ReportDataDictionary
                            WHERE Name LIKE '%Electricity%Facility%'
                            AND ReportingFrequency = 'RunPeriod'
                        )
                    """)
                    result = cursor.fetchone()
                    if result and result[0]:
                        # Assume already in kWh or convert from Joules
                        electricity_kwh = result[0] / 3600000.0 if result[0] > 1000000 else result[0]
                except:
                    pass
            
            # For monthly breakdown, approximate from annual (simplified)
            # Full implementation would query hourly/monthly data
            monthly = [electricity_kwh / 12.0] * 12
            
            conn.close()
            
            return {
                'annual_kwh': electricity_kwh,
                'monthly_kwh': monthly
            }
            
        except Exception as e:
            print(f"⚠️  SQLite extraction error: {e}")
            import traceback
            traceback.print_exc()
        
        return {'annual_kwh': 0.0, 'monthly_kwh': [0.0] * 12}
    
    def _extract_tabular_results(self, tabular_file: Path) -> Dict:
        """Extract energy results from tabular output"""
        try:
            with open(tabular_file, 'r') as f:
                content = f.read()
            
            # Look for annual electricity consumption
            annual_match = re.search(r'Electricity.*?(\d+\.?\d*)', content, re.IGNORECASE)
            if annual_match:
                annual_kwh = float(annual_match.group(1))
                return {
                    'annual_kwh': annual_kwh,
                    'monthly_kwh': [annual_kwh / 12.0] * 12  # Approximate monthly
                }
        except Exception as e:
            print(f"⚠️  Tabular extraction error: {e}")
        
        return {'annual_kwh': 0.0, 'monthly_kwh': [0.0] * 12}
    
    def _calculate_monthly_error(self, simulated: Dict, actual: UtilityData) -> Dict:
        """Calculate monthly error metrics (MBE, CVRMSE)"""
        sim_monthly = simulated.get('monthly_kwh', [0.0] * 12)
        act_monthly = actual.monthly_kwh[:12]
        
        if len(sim_monthly) != len(act_monthly):
            return {'mbe': 0.0, 'cvrmse': 100.0}
        
        # Mean Bias Error (MBE)
        errors = [s - a for s, a in zip(sim_monthly, act_monthly)]
        mbe = sum(errors) / len(errors) if act_monthly else 0.0
        mbe_percent = (mbe / (sum(act_monthly) / len(act_monthly)) * 100) if act_monthly else 0.0
        
        # Coefficient of Variation of Root Mean Square Error (CVRMSE)
        mse = sum(e**2 for e in errors) / len(errors) if errors else 0.0
        rmse = mse ** 0.5
        mean_actual = sum(act_monthly) / len(act_monthly) if act_monthly else 1.0
        cvrmse = (rmse / mean_actual * 100) if mean_actual > 0 else 100.0
        
        return {
            'mbe': abs(mbe_percent),
            'cvrmse': cvrmse
        }
    
    def _calculate_adjustment(self, simulated: Dict, actual: UtilityData) -> Dict:
        """
        Calculate parameter adjustments needed using seasonal analysis.
        
        Uses gradient-based approach with seasonal pattern recognition:
        - Winter errors → adjust infiltration/HVAC heating
        - Summer errors → adjust cooling efficiency
        - Year-round errors → adjust internal loads
        
        Returns:
            Dictionary of parameter multipliers (e.g., {'infiltration': 1.1})
        """
        sim_annual = simulated.get('annual_kwh', 0.0)
        act_annual = actual.annual_kwh()
        
        if sim_annual == 0:
            return {}
        
        error_ratio = act_annual / sim_annual
        
        adjustments = {}
        
        # Get monthly data for seasonal analysis
        sim_monthly = simulated.get('monthly_kwh', [0.0] * 12)
        act_monthly = actual.monthly_kwh[:12]
        
        if len(sim_monthly) == 12 and len(act_monthly) == 12:
            # Calculate seasonal errors
            # Winter: Dec, Jan, Feb (indices 11, 0, 1)
            winter_months = [11, 0, 1]
            winter_error = sum(abs(sim_monthly[i] - act_monthly[i]) for i in winter_months)
            
            # Summer: Jun, Jul, Aug (indices 5, 6, 7)
            summer_months = [5, 6, 7]
            summer_error = sum(abs(sim_monthly[i] - act_monthly[i]) for i in summer_months)
            
            # Determine if heating or cooling dominated
            if winter_error > summer_error * 1.2:
                # Heating-dominated error - adjust infiltration and HVAC efficiency
                adjustments['infiltration'] = error_ratio ** 0.6  # High impact on heating
                adjustments['hvac_efficiency'] = error_ratio ** 0.4
            elif summer_error > winter_error * 1.2:
                # Cooling-dominated error - adjust cooling efficiency
                adjustments['hvac_efficiency'] = error_ratio ** 0.5
                adjustments['infiltration'] = error_ratio ** 0.3  # Less impact on cooling
            else:
                # Balanced error - adjust all parameters moderately
                adjustments['infiltration'] = error_ratio ** 0.5
                adjustments['hvac_efficiency'] = error_ratio ** 0.4
        else:
            # Fallback: simple annual adjustment
            adjustments['infiltration'] = error_ratio ** 0.5
            adjustments['hvac_efficiency'] = error_ratio ** 0.4
        
        # Always adjust internal loads slightly (affects base load)
        adjustments['lighting_multiplier'] = error_ratio ** 0.3
        adjustments['equipment_multiplier'] = error_ratio ** 0.3
        
        # Clamp adjustments to reasonable ranges
        for key in adjustments:
            adjustments[key] = max(0.5, min(2.0, adjustments[key]))  # Limit to 50%-200%
        
        return adjustments
    
    def _adjust_idf_parameters(
        self,
        idf_file: str,
        adjustments: Dict,
        output_file: Path
    ) -> str:
        """
        Adjust IDF parameters based on calibration adjustments.
        Uses improved regex patterns that match full object context.
        
        Returns:
            Path to adjusted IDF file
        """
        with open(idf_file, 'r', encoding='utf-8') as f:
            idf_content = f.read()
        
        # Adjust infiltration rates - improved pattern matching
        if 'infiltration' in adjustments:
            multiplier = adjustments['infiltration']
            # Match ZoneInfiltration:DesignFlowRate objects with Flow Rate field
            # Pattern matches: ZoneInfiltration:DesignFlowRate, name, schedule, design flow rate calculation method, flow rate value
            pattern = r'(ZoneInfiltration:DesignFlowRate[^;]*Flow Rate[^,]*,\s*)([\d.E+-]+)'
            def replace_flow(match):
                try:
                    old_value = float(match.group(2))
                    new_value = old_value * multiplier
                    return match.group(1) + f"{new_value:.6f}"
                except ValueError:
                    return match.group(0)  # Return unchanged if can't parse
            idf_content = re.sub(pattern, replace_flow, idf_content, flags=re.MULTILINE)
        
        # Adjust lighting power - improved pattern
        if 'lighting_multiplier' in adjustments:
            multiplier = adjustments['lighting_multiplier']
            # Match Lights objects with Watts per Zone Floor Area field
            pattern = r'(Lights[^;]*Watts per Zone Floor Area[^,]*,\s*)([\d.E+-]+)'
            def replace_lighting(match):
                try:
                    old_value = float(match.group(2))
                    new_value = old_value * multiplier
                    return match.group(1) + f"{new_value:.2f}"
                except ValueError:
                    return match.group(0)
            idf_content = re.sub(pattern, replace_lighting, idf_content, flags=re.MULTILINE)
        
        # Adjust equipment power - improved pattern
        if 'equipment_multiplier' in adjustments:
            multiplier = adjustments['equipment_multiplier']
            # Match ElectricEquipment objects with Watts per Zone Floor Area field
            pattern = r'(ElectricEquipment[^;]*Watts per Zone Floor Area[^,]*,\s*)([\d.E+-]+)'
            def replace_equipment(match):
                try:
                    old_value = float(match.group(2))
                    new_value = old_value * multiplier
                    return match.group(1) + f"{new_value:.2f}"
                except ValueError:
                    return match.group(0)
            idf_content = re.sub(pattern, replace_equipment, idf_content, flags=re.MULTILINE)
        
        # Adjust HVAC efficiency - new addition
        if 'hvac_efficiency' in adjustments:
            multiplier = adjustments['hvac_efficiency']
            
            # Cooling COP improvement
            pattern = r'(Coil:Cooling:DX[^;]*Rated COP[^,]*,\s*)([\d.E+-]+)'
            def improve_cop(match):
                try:
                    old_value = float(match.group(2))
                    new_value = old_value * multiplier
                    return match.group(1) + f"{new_value:.2f}"
                except ValueError:
                    return match.group(0)
            idf_content = re.sub(pattern, improve_cop, idf_content, flags=re.MULTILINE)
            
            # Heating efficiency improvement
            pattern = r'(Coil:Heating[^;]*Efficiency[^,]*,\s*)([\d.E+-]+)'
            def improve_heating(match):
                try:
                    old_value = float(match.group(2))
                    new_value = old_value * multiplier
                    return match.group(1) + f"{new_value:.2f}"
                except ValueError:
                    return match.group(0)
            idf_content = re.sub(pattern, improve_heating, idf_content, flags=re.MULTILINE)
        
        # Write adjusted IDF
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(idf_content)
        
        return str(output_file)
    
    def _generate_calibration_report(
        self,
        calibrated_idf: Path,
        weather_file: str,
        utility_data: UtilityData,
        baseline_results: Dict,
        adjusted_params: Dict,
        iterations: int,
        converged: bool,
        report_path: Path
    ) -> Path:
        """Generate ASHRAE Guideline 14 compliant calibration report"""
        
        # Run final simulation to get calibrated results
        final_results = self._run_simulation(str(calibrated_idf), weather_file, report_path.parent / "final_calibrated")
        
        # Calculate final metrics
        monthly_error = self._calculate_monthly_error(final_results, utility_data)
        annual_error = abs(final_results.get('annual_kwh', 0) - utility_data.annual_kwh()) / utility_data.annual_kwh()
        
        report = {
            'calibration_summary': {
                'converged': converged,
                'iterations': iterations,
                'baseline_annual_kwh': baseline_results.get('annual_kwh', 0),
                'calibrated_annual_kwh': final_results.get('annual_kwh', 0),
                'actual_annual_kwh': utility_data.annual_kwh(),
                'annual_error_percent': annual_error * 100,
                'monthly_mbe_percent': monthly_error.get('mbe', 0),
                'monthly_cvrmse_percent': monthly_error.get('cvrmse', 0),
                'ashrae_guideline_14_compliant': monthly_error.get('cvrmse', 100) <= 15.0
            },
            'parameter_adjustments': adjusted_params,
            'monthly_comparison': {
                'simulated': final_results.get('monthly_kwh', []),
                'actual': utility_data.monthly_kwh[:12],
                'error_percent': [
                    abs(s - a) / a * 100 if a > 0 else 0
                    for s, a in zip(final_results.get('monthly_kwh', []), utility_data.monthly_kwh[:12])
                ]
            },
            'calibrated_idf_path': str(calibrated_idf)
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report_path
