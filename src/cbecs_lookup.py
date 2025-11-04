"""
CBECS Lookup Module
Provides typical building energy consumption and characteristics from DOE CBECS data
"""

from typing import Dict, Optional, List


class CBECSLookup:
    """
    Lookup typical building characteristics from Commercial Buildings 
    Energy Consumption Survey (CBECS) data
    
    Source: U.S. Energy Information Administration
    https://www.eia.gov/consumption/commercial
    """
    
    def __init__(self):
        self.cbecs_data = self._load_cbecs_data()
    
    def _load_cbecs_data(self) -> Dict:
        """
        Load CBECS 2018 data (most recent)
        
        Data structure:
        - Building type → EUI (site energy use intensity)
        - Building size category → Typical characteristics
        """
        return {
            # Site EUI by building type (kBtu/ft²/year)
            'site_eui': {
                'office': 58.6,
                'retail': 43.5,
                'grocery_store': 145.7,
                'warehouse': 28.1,
                'school': 69.3,
                'hospital': 214.0,
                'hotel': 70.5,
                'restaurant': 238.2,
                'warehouse': 28.1,
                'manufacturing': 118.3,
                'data_center': 350.0,
                'education': 69.3,
                'healthcare': 156.8,
                'lodging': 70.5,
                'food_service': 238.2,
                'mercantile': 53.4,
                'public_assembly': 71.9,
                'religious_worship': 38.1,
                'service': 50.0,
                'storage': 28.1
            },
            
            # Source EUI by building type (kBtu/ft²/year)
            'source_eui': {
                'office': 135.2,
                'retail': 99.7,
                'grocery_store': 334.1,
                'warehouse': 64.3,
                'school': 159.5,
                'hospital': 490.2,
                'hotel': 161.7,
                'restaurant': 546.1,
                'manufacturing': 271.0,
                'data_center': 802.5,
                'education': 159.5,
                'healthcare': 359.4,
                'lodging': 161.7,
                'food_service': 546.1,
                'mercantile': 122.4,
                'public_assembly': 165.0,
                'religious_worship': 87.3,
                'service': 114.7,
                'storage': 64.3
            },
            
            # Typical building characteristics by size category
            'building_characteristics': {
                'small': {  # < 10,000 ft²
                    'typical_area_ft2': 5000,
                    'typical_stories': 1,
                    'typical_hvac': 'PTAC',
                    'occupancy_density': 0.08,  # people per 100 ft²
                },
                'medium': {  # 10,000 - 100,000 ft²
                    'typical_area_ft2': 50000,
                    'typical_stories': 3,
                    'typical_hvac': 'VAV',
                    'occupancy_density': 0.06,
                },
                'large': {  # > 100,000 ft²
                    'typical_area_ft2': 250000,
                    'typical_stories': 10,
                    'typical_hvac': 'ChilledWater',
                    'occupancy_density': 0.05,
                }
            },
            
            # Typical HVAC distribution by building type
            'hvac_distribution': {
                'office': {'packaged': 0.38, 'chilled_water': 0.27, 'individual': 0.19, 'other': 0.16},
                'retail': {'packaged': 0.65, 'chilled_water': 0.11, 'individual': 0.10, 'other': 0.14},
                'school': {'central': 0.58, 'packaged': 0.30, 'individual': 0.12},
                'hospital': {'central': 0.72, 'chilled_water': 0.20, 'other': 0.08},
                'hotel': {'packaged': 0.48, 'central': 0.25, 'individual': 0.27}
            },
            
            # Typical operating hours by building type
            'operating_hours': {
                'office': {'weekdays': 10, 'weekends': 0, 'total_per_week': 50},
                'retail': {'weekdays': 12, 'weekends': 12, 'total_per_week': 84},
                'school': {'weekdays': 8, 'weekends': 0, 'total_per_week': 40},
                'hospital': {'weekdays': 24, 'weekends': 24, 'total_per_week': 168},
                'hotel': {'weekdays': 24, 'weekends': 24, 'total_per_week': 168},
                'warehouse': {'weekdays': 10, 'weekends': 0, 'total_per_week': 50}
            }
        }
    
    def get_site_eui(self, building_type: str) -> Optional[float]:
        """
        Get typical site energy use intensity (kBtu/ft²/year)
        
        Args:
            building_type: Building type (office, retail, etc.)
            
        Returns:
            Site EUI or None
        """
        # Handle None building_type
        if not building_type:
            building_type = 'office'  # Default
        
        # Normalize building type (safe handling of None)
        if building_type is None:
            building_type = 'office'
        btype = building_type.lower().replace(' ', '_')
        
        # Map common variations
        type_mapping = {
            'office_building': 'office',
            'residential_single': 'lodging',
            'residential_multi': 'lodging',
            'healthcare_hospital': 'hospital',
            'healthcare_clinic': 'healthcare',
            'education_school': 'education',
            'education_university': 'education',
            'hospitality_hotel': 'lodging',
            'hospitality_restaurant': 'food_service',
            'retail': 'mercantile',
            'industrial_warehouse': 'storage',
            'industrial_manufacturing': 'manufacturing'
        }
        
        btype = type_mapping.get(btype, btype)
        
        return self.cbecs_data['site_eui'].get(btype)
    
    def get_source_eui(self, building_type: str) -> Optional[float]:
        """Get typical source energy use intensity (kBtu/ft²/year)"""
        # Handle None building_type
        if not building_type:
            building_type = 'office'  # Default
        
        # Safe handling of None
        if building_type is None:
            building_type = 'office'
        btype = building_type.lower().replace(' ', '_')
        
        type_mapping = {
            'office_building': 'office',
            'residential_single': 'lodging',
            'residential_multi': 'lodging',
            'healthcare_hospital': 'hospital',
            'healthcare_clinic': 'healthcare',
            'education_school': 'education',
            'hospitality_hotel': 'lodging',
            'hospitality_restaurant': 'food_service',
            'retail': 'mercantile',
            'industrial_warehouse': 'storage',
            'industrial_manufacturing': 'manufacturing'
        }
        
        btype = type_mapping.get(btype, btype)
        
        return self.cbecs_data['source_eui'].get(btype)
    
    def get_eui_si(self, building_type: str) -> Optional[Dict[str, float]]:
        """
        Get EUI in SI units (kWh/m²/year)
        
        Conversion: 1 kBtu/ft²/year = 3.16 kWh/m²/year
        
        Args:
            building_type: Building type
            
        Returns:
            Dictionary with 'site' and 'source' EUI in kWh/m²/year
        """
        # Handle None building_type
        if not building_type:
            building_type = 'office'  # Default
        
        site_eui_kbtu = self.get_site_eui(building_type)
        source_eui_kbtu = self.get_source_eui(building_type)
        
        if site_eui_kbtu and source_eui_kbtu:
            return {
                'site_eui': site_eui_kbtu * 3.16,  # kWh/m²/year
                'source_eui': source_eui_kbtu * 3.16  # kWh/m²/year
            }
        
        return None
    
    def get_building_characteristics(self, total_area_sqft: float) -> Dict:
        """
        Get typical building characteristics based on size
        
        Args:
            total_area_sqft: Total building area in square feet
            
        Returns:
            Typical characteristics dictionary
        """
        if total_area_sqft < 10000:
            size_category = 'small'
        elif total_area_sqft < 100000:
            size_category = 'medium'
        else:
            size_category = 'large'
        
        return self.cbecs_data['building_characteristics'][size_category].copy()
    
    def get_hvac_distribution(self, building_type: str) -> Dict:
        """Get typical HVAC system distribution for building type"""
        # Handle None building_type
        if not building_type:
            building_type = 'office'  # Default
        
        # Safe handling of None
        if building_type is None:
            building_type = 'office'
        btype = building_type.lower().replace(' ', '_')
        
        type_mapping = {
            'office_building': 'office',
            'healthcare_hospital': 'hospital',
            'education_school': 'school',
            'hospitality_hotel': 'hotel',
            'retail': 'retail'
        }
        
        btype = type_mapping.get(btype, btype)
        
        return self.cbecs_data['hvac_distribution'].get(btype, {})
    
    def get_operating_hours(self, building_type: str) -> Dict:
        """Get typical operating hours for building type"""
        # Handle None building_type
        if not building_type:
            building_type = 'office'  # Default
        
        # Safe handling of None
        if building_type is None:
            building_type = 'office'
        btype = building_type.lower().replace(' ', '_')
        
        type_mapping = {
            'office_building': 'office',
            'healthcare_hospital': 'hospital',
            'education_school': 'school',
            'hospitality_hotel': 'hotel',
            'hospitality_restaurant': 'food_service',
            'retail': 'retail',
            'industrial_warehouse': 'warehouse'
        }
        
        btype = type_mapping.get(btype, btype)
        
        return self.cbecs_data['operating_hours'].get(btype, {
            'weekdays': 10,
            'weekends': 0,
            'total_per_week': 50
        })
    
    def estimate_year_built(self, building_type: str, total_area_sqft: float) -> int:
        """
        Estimate typical year built based on building characteristics
        
        This is a rough estimate based on CBECS data
        """
        # Very rough estimates based on CBECS age distribution
        import random
        
        # Typical age ranges by building size
        if total_area_sqft < 10000:
            # Small buildings tend to be older
            return random.randint(1960, 2000)
        elif total_area_sqft < 100000:
            # Medium buildings span wider range
            return random.randint(1970, 2010)
        else:
            # Large buildings often newer
            return random.randint(1980, 2020)
    
    def validate_simulation_results(self, building_type: str, simulated_eui: float) -> Dict:
        """
        Validate simulation EUI against CBECS typical values
        
        Args:
            building_type: Building type
            simulated_eui: Simulated EUI (kWh/m²/year)
            
        Returns:
            Validation results dictionary
        """
        typical_eui = self.get_eui_si(building_type)
        
        if not typical_eui:
            return {'valid': False, 'reason': 'No CBECS data for building type'}
        
        typical_site_eui = typical_eui['site_eui']
        
        # Calculate percentage difference
        percent_diff = ((simulated_eui - typical_site_eui) / typical_site_eui) * 100
        
        # Reasonable range: ±30% of typical
        is_valid = abs(percent_diff) < 30
        
        return {
            'valid': is_valid,
            'simulated_eui': simulated_eui,
            'typical_eui': typical_site_eui,
            'percent_difference': percent_diff,
            'recommendation': 'Check inputs' if not is_valid else 'Within typical range'
        }

