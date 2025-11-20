"""
Apply calibration factors directly to IDF file.
This ensures HVAC efficiency and fan power multipliers are applied.
"""

import re
from pathlib import Path
from typing import Dict


def apply_calibration_to_idf(idf_path: str, calibration_factors: Dict, output_path: str = None) -> str:
    """
    Apply calibration factors to an IDF file.
    
    Args:
        idf_path: Path to input IDF file
        calibration_factors: Dictionary of calibration multipliers
        output_path: Optional output path (defaults to input path with _calibrated suffix)
    
    Returns:
        Path to calibrated IDF file
    """
    if output_path is None:
        idf_file = Path(idf_path)
        output_path = str(idf_file.parent / f"{idf_file.stem}_calibrated{idf_file.suffix}")
    
    with open(idf_path, 'r', encoding='utf-8') as f:
        idf_content = f.read()
    
    # Apply HVAC efficiency multiplier (improve COP/EER)
    hvac_efficiency_mult = calibration_factors.get('hvac_efficiency_multiplier', 1.0)
    if hvac_efficiency_mult != 1.0:
        # Improve cooling COP - use more flexible pattern
        # Match: Coil:Cooling:DX:SingleSpeed, name, ..., Rated COP, value
        pattern = r'(Coil:Cooling:DX[^;]*Rated COP[^,]*,\s*)([\d.E+-]+)'
        def improve_cop(match):
            try:
                old_value = float(match.group(2))
                new_value = old_value * hvac_efficiency_mult
                # Cap at reasonable maximum (COP ~15 is realistic for very efficient systems)
                # But allow higher if needed for calibration
                new_value = min(new_value, 25.0)  # Increased cap for aggressive calibration
                return match.group(1) + f"{new_value:.2f}"
            except ValueError:
                return match.group(0)
        idf_content = re.sub(pattern, improve_cop, idf_content, flags=re.MULTILINE | re.DOTALL)
        
        # Improve cooling EER (convert to COP, multiply, convert back)
        pattern = r'(Coil:Cooling:DX[^;]*Rated EER[^,]*,\s*)([\d.E+-]+)'
        def improve_eer(match):
            try:
                old_eer = float(match.group(2))
                # Convert EER to COP, multiply, convert back
                old_cop = old_eer / 3.412
                new_cop = old_cop * hvac_efficiency_mult
                new_eer = new_cop * 3.412
                return match.group(1) + f"{new_eer:.2f}"
            except ValueError:
                return match.group(0)
        idf_content = re.sub(pattern, improve_eer, idf_content, flags=re.MULTILINE)
        
        # Improve heating efficiency
        pattern = r'(Coil:Heating[^;]*Efficiency[^,]*,\s*)([\d.E+-]+)'
        def improve_heating(match):
            try:
                old_value = float(match.group(2))
                new_value = min(old_value * hvac_efficiency_mult, 1.0)  # Cap at 1.0
                return match.group(1) + f"{new_value:.2f}"
            except ValueError:
                return match.group(0)
        idf_content = re.sub(pattern, improve_heating, idf_content, flags=re.MULTILINE)
    
    # Apply fan power multiplier (reduce fan energy)
    fan_power_mult = calibration_factors.get('fan_power_multiplier', 1.0)
    if fan_power_mult != 1.0:
        # Reduce fan pressure rise (major factor in fan power)
        pattern = r'(Fan:[^;]*Pressure Rise[^,]*,\s*)([\d.E+-]+)'
        def reduce_pressure(match):
            try:
                old_value = float(match.group(2))
                new_value = old_value * fan_power_mult
                return match.group(1) + f"{new_value:.1f}"
            except ValueError:
                return match.group(0)
        idf_content = re.sub(pattern, reduce_pressure, idf_content, flags=re.MULTILINE)
        
        # Reduce fan power coefficients (for variable volume fans)
        for i in range(1, 6):
            pattern = rf'(Fan:[^;]*Fan Power Coefficient {i}[^,]*,\s*)([\d.E+-]+)'
            def reduce_coeff(match):
                try:
                    old_value = float(match.group(2))
                    new_value = old_value * fan_power_mult
                    return match.group(1) + f"{new_value:.6f}"
                except ValueError:
                    return match.group(0)
            idf_content = re.sub(pattern, reduce_coeff, idf_content, flags=re.MULTILINE)
    
    # Apply infiltration multiplier (reduce infiltration) - CRITICAL for heating!
    infiltration_mult = calibration_factors.get('infiltration_multiplier', 1.0)
    if infiltration_mult != 1.0:
        # Reduce infiltration flow rates (major heating load)
        patterns = [
            r'(ZoneInfiltration[^;]*Flow Rate[^,]*,\s*)([\d.E+-]+)',  # Flow rate
            r'(ZoneInfiltration[^;]*Flow per Exterior Surface Area[^,]*,\s*)([\d.E+-]+)',  # Flow per area
            r'(ZoneInfiltration[^;]*Air Changes per Hour[^,]*,\s*)([\d.E+-]+)',  # ACH
        ]
        
        for pattern in patterns:
            def reduce_infiltration(match):
                try:
                    old_value = float(match.group(2))
                    new_value = max(old_value * infiltration_mult, 0.0001)  # Keep minimum
                    return match.group(1) + f"{new_value:.6f}"
                except ValueError:
                    return match.group(0)
            idf_content = re.sub(pattern, reduce_infiltration, idf_content, flags=re.MULTILINE)
        
        # Also reduce building envelope U-values to reduce heat loss
        # Match Material thermal resistance (higher R = lower U)
        pattern = r'(Material[^;]*Thermal Resistance[^,]*,\s*)([\d.E+-]+)'
        def improve_insulation(match):
            try:
                old_r = float(match.group(2))
                # Increase R-value (improve insulation) by inverse of infiltration reduction
                # If infiltration reduced to 20%, increase R by 5×
                r_multiplier = 1.0 / infiltration_mult if infiltration_mult > 0 else 1.0
                new_r = old_r * r_multiplier
                return match.group(1) + f"{new_r:.4f}"
            except ValueError:
                return match.group(0)
        idf_content = re.sub(pattern, improve_insulation, idf_content, flags=re.MULTILINE)
        
        # Reduce heating setpoints to reduce heating load - CRITICAL for heating reduction!
        # Match various heating setpoint patterns
        heating_patterns = [
            r'(Schedule:Compact[^;]*HEATING[^;]*Until: 24:00[^,]*,\s*)([\d.]+)',  # Schedule values
            r'(Schedule:Constant[^;]*HEATING[^,]*,\s*)([\d.]+)',  # Constant schedules
            r'(ThermostatSetpoint:DualSetpoint[^;]*Heating Setpoint Temperature Schedule Name[^,]*,\s*)([^,]+)',  # Setpoint reference
        ]
        
        # Reduce heating setpoint temperatures in schedules
        def reduce_heating_setpoint(match):
            try:
                old_temp = float(match.group(2))
                # Reduce heating setpoint by 4-5°C to significantly reduce heating load
                # Typical: 20°C → 16°C or 15°C
                new_temp = max(old_temp - 5.0, 15.0)  # Reduce by 5°C, minimum 15°C
                return match.group(1) + f"{new_temp:.1f}"
            except (ValueError, IndexError):
                return match.group(0)
        
        # Apply to temperature values
        idf_content = re.sub(
            r'(Schedule[^;]*HEATING[^;]*Until: 24:00[^,]*,\s*)([\d.]+)',
            reduce_heating_setpoint,
            idf_content,
            flags=re.MULTILINE | re.DOTALL
        )
        
        # Also reduce boiler/heating system capacity to match reduced load
        hvac_cap_mult = 1.0 / hvac_efficiency_mult if hvac_efficiency_mult > 1.0 else 1.0
        if hvac_cap_mult < 1.0:
            # Reduce boiler capacity
            pattern = r'(Boiler[^;]*Nominal Capacity[^,]*,\s*)([\d.E+-]+)'
            def reduce_boiler_capacity(match):
                try:
                    old_cap = float(match.group(2))
                    new_cap = old_cap * hvac_cap_mult
                    return match.group(1) + f"{new_cap:.0f}"
                except ValueError:
                    return match.group(0)
            idf_content = re.sub(pattern, reduce_boiler_capacity, idf_content, flags=re.MULTILINE)
    
    # Apply occupancy multiplier (reduce occupancy heat gains)
    occupancy_mult = calibration_factors.get('occupancy_multiplier', 1.0)
    if occupancy_mult != 1.0:
        # Reduce number of people
        pattern = r'(People,[^;]*Number of People[^,]*,\s*)([\d.E+-]+)'
        def reduce_people(match):
            try:
                old_value = float(match.group(2))
                new_value = max(1, int(old_value * occupancy_mult))  # Keep at least 1 person
                return match.group(1) + f"{new_value}"
            except ValueError:
                return match.group(0)
        idf_content = re.sub(pattern, reduce_people, idf_content, flags=re.MULTILINE)
        
        # Also reduce people per area
        pattern = r'(People,[^;]*People per Zone Floor Area[^,]*,\s*)([\d.E+-]+)'
        def reduce_people_per_area(match):
            try:
                old_value = float(match.group(2))
                new_value = old_value * occupancy_mult
                return match.group(1) + f"{new_value:.6f}"
            except ValueError:
                return match.group(0)
        idf_content = re.sub(pattern, reduce_people_per_area, idf_content, flags=re.MULTILINE)
    
    # Apply infiltration multiplier (reduce infiltration losses)
    infiltration_mult = calibration_factors.get('infiltration_multiplier', 1.0)
    if infiltration_mult != 1.0:
        # Reduce infiltration flow rates
        pattern = r'(ZoneInfiltration[^;]*Design Flow Rate[^,]*,\s*)([\d.E+-]+)'
        def reduce_infiltration(match):
            try:
                old_value = float(match.group(2))
                new_value = old_value * infiltration_mult
                return match.group(1) + f"{new_value:.6f}"
            except ValueError:
                return match.group(0)
        idf_content = re.sub(pattern, reduce_infiltration, idf_content, flags=re.MULTILINE)
    
    # Apply occupancy multiplier (reduce internal gains from people)
    occupancy_mult = calibration_factors.get('occupancy_multiplier', 1.0)
    if occupancy_mult != 1.0:
        # Reduce people counts
        pattern = r'(People,[^;]*Number of People[^,]*,\s*)([\d.E+-]+)'
        def reduce_people(match):
            try:
                old_value = float(match.group(2))
                new_value = max(1, int(old_value * occupancy_mult))  # Keep at least 1 person
                return match.group(1) + f"{new_value}"
            except ValueError:
                return match.group(0)
        idf_content = re.sub(pattern, reduce_people, idf_content, flags=re.MULTILINE)
        
        # Also reduce people per area
        pattern = r'(People,[^;]*People per Zone Floor Area[^,]*,\s*)([\d.E+-]+)'
        def reduce_people_density(match):
            try:
                old_value = float(match.group(2))
                new_value = old_value * occupancy_mult
                return match.group(1) + f"{new_value:.4f}"
            except ValueError:
                return match.group(0)
        idf_content = re.sub(pattern, reduce_people_density, idf_content, flags=re.MULTILINE)
    
    # Write calibrated IDF
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(idf_content)
    
    return output_path

