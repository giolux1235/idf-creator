"""
Building Age Adjustment Module

Provides age-based adjustments to building parameters including HVAC efficiency,
envelope properties, infiltration, and internal loads.
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class AgeParams:
    """Parameters adjusted for building age"""
    hvac_efficiency_multiplier: float
    infiltration_multiplier: float
    window_u_multiplier: float
    insulation_r_multiplier: float


class BuildingAgeAdjuster:
    """Adjusts building parameters based on construction era"""
    
    def __init__(self):
        pass
    
    def adjust_parameters(self, year_built: int) -> AgeParams:
        """
        Get age-based multiplier adjustments for building parameters.
        
        Args:
            year_built: Year building was constructed
            
        Returns:
            AgeParams with adjustment multipliers
        """
        # Age categories based on energy code evolution
        if year_built < 1980:
            # Pre-ASHRAE 90, single pane, minimal insulation
            return AgeParams(
                hvac_efficiency_multiplier=0.65,
                infiltration_multiplier=1.4,
                window_u_multiplier=1.5,
                insulation_r_multiplier=0.60
            )
        elif year_built < 2000:
            # 1980s-1990s, ASHRAE 90 and 90.1
            return AgeParams(
                hvac_efficiency_multiplier=0.80,
                infiltration_multiplier=1.2,
                window_u_multiplier=1.2,
                insulation_r_multiplier=0.75
            )
        elif year_built < 2010:
            # 2000s, ASHRAE 90.1-2001/2004
            return AgeParams(
                hvac_efficiency_multiplier=0.90,
                infiltration_multiplier=1.1,
                window_u_multiplier=1.1,
                insulation_r_multiplier=0.90
            )
        else:
            # Modern 2011+, ASHRAE 90.1-2010+
            return AgeParams(
                hvac_efficiency_multiplier=1.0,
                infiltration_multiplier=1.0,
                window_u_multiplier=1.0,
                insulation_r_multiplier=1.0
            )
    
    def adjust_infiltration(self, ach: float, year_built: int) -> float:
        """
        Adjust infiltration rate based on building age.
        
        Args:
            ach: Base air changes per hour
            year_built: Year building was constructed
            
        Returns:
            Adjusted infiltration rate
        """
        age_params = self.adjust_parameters(year_built)
        return ach * age_params.infiltration_multiplier
    
    def get_hvac_efficiency_values(self, year_built: Optional[int], 
                                   hvac_type: str, 
                                   leed_level: Optional[str] = None) -> Dict[str, float]:
        """
        Get HVAC efficiency values adjusted for age and LEED certification.
        
        Args:
            year_built: Year building was constructed
            hvac_type: Type of HVAC system (VAV, PTAC, etc.)
            leed_level: Optional LEED certification level (Certified, Silver, Gold, Platinum)
            
        Returns:
            Dictionary with efficiency values (COP, EER, efficiency)
        """
        # Base efficiencies by system type
        base_efficiencies = {
            'VAV': {'heating_cop': 3.5, 'cooling_eer': 12.0},
            'PTAC': {'heating_cop': 3.0, 'cooling_eer': 9.0},
            'RTU': {'heating_efficiency': 0.8, 'cooling_eer': 10.0},
            'HeatPump': {'heating_cop': 4.0, 'cooling_eer': 14.0},
            'ChilledWater': {'heating_efficiency': 0.85, 'cooling_cop': 5.0},
            'Radiant': {'heating_cop': 4.5, 'cooling_cop': 6.0}
        }
        
        # Get base efficiency
        base = base_efficiencies.get(hvac_type, base_efficiencies['VAV']).copy()
        
        # Apply age adjustment
        if year_built is not None:
            age_params = self.adjust_parameters(year_built)
            for key in base.keys():
                if 'cop' in key.lower() or 'eer' in key.lower():
                    base[key] *= age_params.hvac_efficiency_multiplier
                elif 'efficiency' in key.lower():
                    base[key] *= age_params.hvac_efficiency_multiplier
        
        # Apply LEED bonuses
        if leed_level:
            leed_bonus = self.get_leed_efficiency_bonus(leed_level)
            hvac_bonus = leed_bonus.get('hvac_efficiency_improvement', 1.0)
            for key in base.keys():
                base[key] *= hvac_bonus
        
        return base
    
    def get_window_properties(self, year_built: int) -> Dict[str, float]:
        """
        Get window properties adjusted for building age.
        
        Args:
            year_built: Year building was constructed
            
        Returns:
            Dictionary with window properties (u_factor, shgc)
        """
        age_params = self.adjust_parameters(year_built)
        
        # Base modern window properties
        base_u = 2.0  # W/m²-K
        base_shgc = 0.4
        
        return {
            'u_factor': base_u * age_params.window_u_multiplier,
            'shgc': base_shgc,
            'multiplier': age_params.window_u_multiplier
        }
    
    def get_lighting_power_density(self, year_built: int, 
                                   retrofit_year: Optional[int] = None) -> float:
        """
        Get lighting power density adjusted for building age and retrofits.
        
        Args:
            year_built: Year building was constructed
            retrofit_year: Optional year of lighting retrofit
            
        Returns:
            Lighting power density in W/m²
        """
        # Use retrofit year if provided, otherwise use construction year
        adjust_year = retrofit_year if retrofit_year else year_built
        
        # Base modern LPD
        base_lpd = 10.8  # W/m² for offices
        
        # Adjust for age
        age_params = self.adjust_parameters(adjust_year)
        # Lighting typically improves with age due to energy codes
        lpd_multiplier = 1 / age_params.hvac_efficiency_multiplier
        
        return base_lpd * lpd_multiplier
    
    def get_equipment_power_density(self, year_built: int,
                                    retrofit_year: Optional[int] = None) -> float:
        """
        Get equipment power density adjusted for building age.
        
        Args:
            year_built: Year building was constructed
            retrofit_year: Optional year of equipment retrofit
            
        Returns:
            Equipment power density in W/m²
        """
        # Use retrofit year if provided
        adjust_year = retrofit_year if retrofit_year else year_built
        
        # Base modern EPD
        base_epd = 10.8  # W/m² for offices
        
        # Equipment power has increased over time due to more electronics
        # But efficiency has also improved
        age_params = self.adjust_parameters(adjust_year)
        epd_multiplier = 1.2 - (age_params.hvac_efficiency_multiplier * 0.2)
        
        return base_epd * epd_multiplier
    
    def get_occupancy_density(self, year_built: int) -> float:
        """
        Get occupancy density adjusted for building age.
        
        Args:
            year_built: Year building was constructed
            
        Returns:
            Occupancy density in m²/person
        """
        # Occupancy density has increased over time (less space per person)
        base_occ_density = 9.3  # m²/person for offices
        
        if year_built < 1980:
            occ_multiplier = 1.3  # More space per person
        elif year_built < 2000:
            occ_multiplier = 1.1
        elif year_built < 2010:
            occ_multiplier = 1.05
        else:
            occ_multiplier = 1.0
        
        return base_occ_density * occ_multiplier
    
    def get_leed_efficiency_bonus(self, leed_level: str) -> Dict[str, float]:
        """
        Get efficiency bonus multipliers for LEED certification.
        
        Args:
            leed_level: LEED certification level (Certified, Silver, Gold, Platinum)
            
        Returns:
            Dictionary with bonus multipliers
        """
        leed_level = leed_level.lower()
        
        if leed_level == 'certified':
            return {
                'hvac_efficiency_improvement': 1.05,
                'envelope_improvement': 1.02,
                'lighting_efficiency_improvement': 1.03
            }
        elif leed_level == 'silver':
            return {
                'hvac_efficiency_improvement': 1.08,
                'envelope_improvement': 1.04,
                'lighting_efficiency_improvement': 1.05
            }
        elif leed_level == 'gold':
            return {
                'hvac_efficiency_improvement': 1.12,
                'envelope_improvement': 1.08,
                'lighting_efficiency_improvement': 1.08
            }
        elif leed_level == 'platinum':
            return {
                'hvac_efficiency_improvement': 1.15,
                'envelope_improvement': 1.10,
                'lighting_efficiency_improvement': 1.10
            }
        else:
            # No bonus for unrecognized levels
            return {
                'hvac_efficiency_improvement': 1.0,
                'envelope_improvement': 1.0,
                'lighting_efficiency_improvement': 1.0
            }
