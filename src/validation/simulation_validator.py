"""
EnergyPlus Simulation Validator
Runs EnergyPlus simulations and validates results
"""
import os
import subprocess
import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SimulationError:
    """Represents a simulation error from EnergyPlus"""
    severity: str  # 'fatal', 'severe', 'warning'
    message: str
    line_number: Optional[int] = None


@dataclass
class SimulationResult:
    """Results from EnergyPlus simulation"""
    success: bool
    fatal_errors: int
    severe_errors: int
    warnings: int
    errors: List[SimulationError]
    elapsed_time: Optional[float] = None
    output_directory: Optional[str] = None
    error_file_path: Optional[str] = None


class EnergyPlusSimulationValidator:
    """Validates IDF files by running EnergyPlus simulations"""
    
    def __init__(self, energyplus_path: Optional[str] = None):
        """
        Initialize validator.
        
        Args:
            energyplus_path: Path to EnergyPlus executable (if None, uses 'energyplus' from PATH)
        """
        self.energyplus_path = energyplus_path or self._find_energyplus()
    
    def _find_energyplus(self) -> str:
        """Find EnergyPlus executable in PATH"""
        # Try common EnergyPlus paths
        common_paths = [
            'energyplus',
            '/usr/local/bin/energyplus',
            '/opt/EnergyPlus/energyplus',
            'C:\\EnergyPlusV24-2-0\\energyplus.exe',
            'C:\\EnergyPlusV25-1-0\\energyplus.exe',
        ]
        
        for path in common_paths:
            try:
                result = subprocess.run(
                    [path, '--version'],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return path
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        # Default to 'energyplus' - will fail gracefully if not found
        return 'energyplus'
    
    def validate_by_simulation(self, idf_file: str, weather_file: Optional[str] = None,
                              output_directory: Optional[str] = None,
                              timeout: int = 300) -> SimulationResult:
        """
        Validate IDF file by running EnergyPlus simulation.
        
        Args:
            idf_file: Path to IDF file
            weather_file: Path to EPW weather file (optional)
            output_directory: Directory for simulation output (auto-created if None)
            timeout: Maximum simulation time in seconds
            
        Returns:
            SimulationResult with error counts and details
        """
        if not os.path.exists(idf_file):
            return SimulationResult(
                success=False,
                fatal_errors=1,
                severe_errors=0,
                warnings=0,
                errors=[SimulationError('fatal', f'IDF file not found: {idf_file}')]
            )
        
        # Create output directory
        if output_directory is None:
            output_directory = os.path.join(os.path.dirname(idf_file), 'simulation_output')
        os.makedirs(output_directory, exist_ok=True)
        
        # Prepare EnergyPlus command
        # EnergyPlus syntax: energyplus -w weather_file -d output_dir idf_file
        cmd = [self.energyplus_path]
        
        if weather_file and os.path.exists(weather_file):
            # Use absolute path for weather file
            weather_file_abs = os.path.abspath(weather_file)
            cmd.extend(['-w', weather_file_abs])
        elif weather_file:
            # Weather file specified but doesn't exist - try to use it anyway (EnergyPlus will error clearly)
            cmd.extend(['-w', weather_file])
        
        # Output directory
        output_directory_abs = os.path.abspath(output_directory)
        cmd.extend(['-d', output_directory_abs])
        
        # IDF file (must be absolute or relative to cwd)
        idf_file_abs = os.path.abspath(idf_file)
        cmd.append(idf_file_abs)
        
        # Run simulation
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.path.dirname(idf_file) if os.path.dirname(idf_file) else '.'
            )
        except subprocess.TimeoutExpired:
            return SimulationResult(
                success=False,
                fatal_errors=1,
                severe_errors=0,
                warnings=0,
                errors=[SimulationError('fatal', f'Simulation timed out after {timeout} seconds')],
                output_directory=output_directory
            )
        except FileNotFoundError:
            return SimulationResult(
                success=False,
                fatal_errors=1,
                severe_errors=0,
                warnings=0,
                errors=[SimulationError('fatal', f'EnergyPlus executable not found: {self.energyplus_path}')],
                output_directory=output_directory
            )
        
        # Parse error file
        error_file = os.path.join(output_directory, 'eplusout.err')
        return self._parse_error_file(error_file, output_directory)
    
    def _parse_error_file(self, error_file: str, output_directory: str) -> SimulationResult:
        """Parse EnergyPlus error file"""
        errors = []
        fatal_count = 0
        severe_count = 0
        warning_count = 0
        elapsed_time = None
        success = False
        
        if not os.path.exists(error_file):
            return SimulationResult(
                success=False,
                fatal_errors=1,
                severe_errors=0,
                warnings=0,
                errors=[SimulationError('fatal', 'Error file not generated')],
                output_directory=output_directory,
                error_file_path=error_file
            )
        
        with open(error_file, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Parse errors
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            if '**  Fatal  **' in line:
                fatal_count += 1
                errors.append(SimulationError('fatal', line_stripped, i))
            elif '** Severe  **' in line:
                severe_count += 1
                errors.append(SimulationError('severe', line_stripped, i))
            elif '** Warning **' in line:
                warning_count += 1
                errors.append(SimulationError('warning', line_stripped, i))
            
            # Extract elapsed time
            if 'Elapsed Time=' in line:
                time_match = re.search(r'Elapsed Time=(\d+hr)\s+(\d+min)\s+([\d.]+sec)', line)
                if time_match:
                    hours = int(time_match.group(1).replace('hr', ''))
                    minutes = int(time_match.group(2).replace('min', ''))
                    seconds = float(time_match.group(3).replace('sec', ''))
                    elapsed_time = hours * 3600 + minutes * 60 + seconds
            
            # Check for successful completion
            if 'EnergyPlus Completed Successfully' in line:
                success = (fatal_count == 0 and severe_count == 0)
        
        return SimulationResult(
            success=success,
            fatal_errors=fatal_count,
            severe_errors=severe_count,
            warnings=warning_count,
            errors=errors,
            elapsed_time=elapsed_time,
            output_directory=output_directory,
            error_file_path=error_file
        )
    
    def get_energy_results(self, output_directory: str) -> Optional[Dict]:
        """Extract energy results from simulation output"""
        csv_file = os.path.join(output_directory, 'eplustbl.csv')
        if not os.path.exists(csv_file):
            return None
        
        try:
            import pandas as pd
            df = pd.read_csv(csv_file)
            
            results = {
                'rows': len(df),
                'columns': list(df.columns),
                'data': df.to_dict('records')
            }
            
            # Extract key metrics if available
            for col in df.columns:
                col_lower = col.lower()
                if 'electricity' in col_lower or 'total site energy' in col_lower:
                    results['total_electricity'] = float(df[col].sum())
                elif 'gas' in col_lower or 'natural gas' in col_lower:
                    results['total_gas'] = float(df[col].sum())
            
            return results
        except Exception as e:
            return {'error': str(e)}


def validate_simulation(idf_file: str, weather_file: Optional[str] = None,
                       output_directory: Optional[str] = None) -> SimulationResult:
    """
    Convenience function to validate IDF by simulation.
    
    Args:
        idf_file: Path to IDF file
        weather_file: Path to EPW weather file (optional)
        output_directory: Output directory for simulation
        
    Returns:
        SimulationResult
    """
    validator = EnergyPlusSimulationValidator()
    return validator.validate_by_simulation(idf_file, weather_file, output_directory)

