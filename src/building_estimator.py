"""Module for estimating building parameters from minimal input."""
from typing import Dict, Optional
from .building_age_adjustments import BuildingAgeAdjuster
from .utils.config_manager import ConfigManager


class BuildingEstimator:
    """Estimates missing building parameters using defaults and typical values."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize building estimator.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_manager = ConfigManager.get_instance(config_path)
        self.age_adjuster = BuildingAgeAdjuster()
    
    def get_defaults(self) -> Dict:
        """Get default building parameters from config."""
        return self.config_manager.get_defaults()
    
    def estimate_from_type(self, building_type: str, year_built: Optional[int] = None) -> Dict:
        """
        Estimate typical parameters based on building type.
        
        Args:
            building_type: Type of building (Office, Residential, etc.)
            
        Returns:
            Dictionary with typical parameters for the building type
        """
        typical_params = {
            'Office': {
                'people_per_m2': 0.07,
                'lighting_w_per_m2': 10.0,
                'equipment_w_per_m2': 15.0,
                'infiltration_ach': 0.25,
                'occupancy_schedule': 'Office'
            },
            'Residential': {
                'people_per_m2': 0.05,
                'lighting_w_per_m2': 8.0,
                'equipment_w_per_m2': 5.0,
                'infiltration_ach': 0.5,
                'occupancy_schedule': 'Residential'
            },
            'Retail': {
                'people_per_m2': 0.15,
                'lighting_w_per_m2': 15.0,
                'equipment_w_per_m2': 8.0,
                'infiltration_ach': 0.3,
                'occupancy_schedule': 'Retail'
            },
            'Warehouse': {
                'people_per_m2': 0.005,
                'lighting_w_per_m2': 8.0,
                'equipment_w_per_m2': 2.0,
                'infiltration_ach': 0.5,
                'occupancy_schedule': 'Warehouse'
            },
            'School': {
                'people_per_m2': 0.2,
                'lighting_w_per_m2': 12.0,
                'equipment_w_per_m2': 5.0,
                'infiltration_ach': 0.4,
                'occupancy_schedule': 'School'
            },
            'Hospital': {
                'people_per_m2': 0.1,
                'lighting_w_per_m2': 12.0,
                'equipment_w_per_m2': 20.0,
                'infiltration_ach': 0.2,
                'occupancy_schedule': 'Hospital'
            }
        }
        
        base_params = typical_params.get(building_type, typical_params['Office'])
        
        # Adjust for building age
        # NOTE: Only apply HVAC efficiency and infiltration adjustments by default.
        # Internal load adjustments (lighting/equipment) are opt-in to avoid over-correction.
        if year_built is not None:
            age_params = self.age_adjuster.adjust_parameters(year_built)
            # Adjust infiltration (this works well)
            base_params['infiltration_ach'] = base_params['infiltration_ach'] * age_params.infiltration_multiplier
            
            # Internal load adjustments are now opt-in via apply_internal_load_adjustments flag
            # These are disabled by default as they can over-correct
            # Users can enable them if they know the building hasn't been retrofitted
        
        return base_params
    
    def calculate_zone_parameters(self, floor_area: float, 
                                   building_type: str = "Office",
                                   stories: int = 3) -> Dict:
        """
        Calculate zone-level parameters based on building geometry.
        
        Args:
            floor_area: Total floor area in m²
            building_type: Type of building
            stories: Number of stories
            
        Returns:
            Dictionary with zone parameters
        """
        type_params = self.estimate_from_type(building_type)
        
        # Handle None or zero stories (check None first to avoid TypeError)
        if stories is None:
            stories = 3  # Default to 3 stories
        elif stories <= 0:
            stories = 3
        
        # Handle None or zero floor_area (check None first to avoid TypeError)
        if floor_area is None:
            floor_area = 1000.0  # Default to 1000 m²
        elif floor_area <= 0:
            floor_area = 1000.0
        
        zone_area = floor_area / stories
        
        return {
            'zone_area': zone_area,
            'zone_volume': zone_area * 2.7,  # Assume 2.7m ceiling height
            'number_of_people': int(zone_area * type_params['people_per_m2']),
            'lighting_power': zone_area * type_params['lighting_w_per_m2'],
            'equipment_power': zone_area * type_params['equipment_w_per_m2'],
            'infiltration_ach': type_params['infiltration_ach'],
            'occupancy_schedule': type_params['occupancy_schedule']
        }
    
    def estimate_building_dimensions(self, floor_area: float) -> Dict:
        """
        Estimate building length, width, and shape from floor area.
        Assumes roughly square footprint.
        
        Args:
            floor_area: Floor area in m²
            
        Returns:
            Dictionary with length and width estimates
        """
        width = (floor_area ** 0.5) * 0.8
        length = floor_area / width
        
        return {
            'length': length,
            'width': width,
            'height_per_story': 3.0  # Typical story height
        }






