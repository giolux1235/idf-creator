"""
Universal Calibration System for IDF Creator
Applies calibration factors based on building type and can learn from multiple benchmarks.
"""

import json
from pathlib import Path
from typing import Dict, Optional


class CalibrationSystem:
    """Universal calibration system that works across building types"""
    
    def __init__(self, calibration_file: str = "artifacts/calibration_factors.json"):
        self.calibration_file = Path(calibration_file)
        self.calibration_factors = self._load_calibration_factors()
        
        # Default calibration factors (will be updated based on benchmarks)
        self.default_factors = {
            'office': {
                'lighting_multiplier': 1.0,
                'equipment_multiplier': 1.0,
                'occupancy_multiplier': 1.0,
                'hvac_efficiency_multiplier': 1.0,
                'infiltration_multiplier': 1.0,
                'fan_power_multiplier': 1.0,
            },
            'retail': {
                'lighting_multiplier': 1.0,
                'equipment_multiplier': 1.0,
                'occupancy_multiplier': 1.0,
                'hvac_efficiency_multiplier': 1.0,
                'infiltration_multiplier': 1.0,
                'fan_power_multiplier': 1.0,
            },
            'residential': {
                'lighting_multiplier': 1.0,
                'equipment_multiplier': 1.0,
                'occupancy_multiplier': 1.0,
                'hvac_efficiency_multiplier': 1.0,
                'infiltration_multiplier': 1.0,
                'fan_power_multiplier': 1.0,
            },
        }
    
    def _load_calibration_factors(self) -> Dict:
        """Load saved calibration factors"""
        if self.calibration_file.exists():
            try:
                with open(self.calibration_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def save_calibration_factors(self):
        """Save calibration factors to file"""
        self.calibration_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.calibration_file, 'w') as f:
            json.dump(self.calibration_factors, f, indent=2)
    
    def get_calibration_factors(self, building_type: str) -> Dict:
        """Get calibration factors for a building type"""
        building_type_lower = building_type.lower()
        
        # Check if we have saved factors for this building type
        if building_type_lower in self.calibration_factors:
            return self.calibration_factors[building_type_lower]
        
        # Use default factors
        if building_type_lower in self.default_factors:
            return self.default_factors[building_type_lower]
        
        # Fallback to office defaults
        return self.default_factors['office']
    
    def update_calibration_factors(self, building_type: str, factors: Dict, 
                                   learning_rate: float = 0.5):
        """
        Update calibration factors based on new benchmark data.
        
        Args:
            building_type: Type of building (office, retail, etc.)
            factors: New calibration factors from benchmark
            learning_rate: How much to weight new factors vs existing (0-1)
        """
        building_type_lower = building_type.lower()
        
        # Get existing factors
        existing = self.get_calibration_factors(building_type_lower)
        
        # Update with weighted average
        updated = {}
        for key in factors:
            if key in existing:
                # Weighted average: blend old and new
                updated[key] = (existing[key] * (1 - learning_rate) + 
                               factors[key] * learning_rate)
            else:
                updated[key] = factors[key]
        
        # Save to calibration factors
        if building_type_lower not in self.calibration_factors:
            self.calibration_factors[building_type_lower] = {}
        
        self.calibration_factors[building_type_lower].update(updated)
        self.save_calibration_factors()
        
        return updated
    
    def apply_calibration(self, building_type: str, base_params: Dict) -> Dict:
        """
        Apply calibration factors to base parameters.
        
        Args:
            building_type: Type of building
            base_params: Base parameters from IDF generator
            
        Returns:
            Calibrated parameters
        """
        factors = self.get_calibration_factors(building_type)
        calibrated = base_params.copy()
        
        # Apply multipliers to power densities
        if 'lighting_power_density' in calibrated:
            calibrated['lighting_power_density'] *= factors.get('lighting_multiplier', 1.0)
        
        if 'equipment_power_density' in calibrated:
            calibrated['equipment_power_density'] *= factors.get('equipment_multiplier', 1.0)
        
        if 'occupancy_density' in calibrated:
            calibrated['occupancy_density'] *= factors.get('occupancy_multiplier', 1.0)
        
        # Store multipliers for HVAC adjustments
        calibrated['_calibration_factors'] = factors
        
        return calibrated
    
    def calculate_factors_from_benchmark(self, simulated_eui: float, target_eui: float,
                                        simulated_total: float, target_total: float,
                                        energy_breakdown: Optional[Dict] = None) -> Dict:
        """
        Calculate calibration factors from benchmark comparison.
        
        Args:
            simulated_eui: Simulated EUI
            target_eui: Target EUI from benchmark
            simulated_total: Simulated total energy
            target_total: Target total energy
            energy_breakdown: Optional breakdown of energy by end use
            
        Returns:
            Dictionary of calibration factors
        """
        # Calculate overall energy multiplier needed
        eui_ratio = target_eui / simulated_eui if simulated_eui > 0 else 1.0
        total_ratio = target_total / simulated_total if simulated_total > 0 else 1.0
        
        # Use average of EUI and total ratios
        overall_multiplier = (eui_ratio + total_ratio) / 2
        
        # Calculate factors based on energy breakdown if available
        factors = {
            'lighting_multiplier': overall_multiplier * 0.4,  # Lighting typically 15-30% of load
            'equipment_multiplier': overall_multiplier * 0.4,  # Equipment typically 30-40% of load
            'hvac_efficiency_multiplier': 1.0 / overall_multiplier,  # Improve efficiency
            'fan_power_multiplier': overall_multiplier * 0.6,  # Fans typically 15-20% of load
            'occupancy_multiplier': 1.0,  # Keep occupancy same
            'infiltration_multiplier': overall_multiplier * 0.3,  # Infiltration smaller impact
        }
        
        # Adjust based on breakdown if available
        if energy_breakdown:
            lighting_pct = energy_breakdown.get('Lighting', {}).get('simulated_percent', 0)
            if lighting_pct > 0:
                # If lighting is too high percentage, reduce it more
                target_lighting_pct = energy_breakdown.get('Lighting', {}).get('report_percent', 15)
                if lighting_pct > target_lighting_pct * 1.5:
                    factors['lighting_multiplier'] *= 0.7
        
        return factors


