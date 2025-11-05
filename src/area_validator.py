"""Module for validating building areas and flagging outliers."""
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class AreaValidator:
    """Validates building areas against typical ranges and flags outliers."""
    
    # Typical building area ranges (m² per floor) by building type
    # Based on CBECS data and typical office building sizes
    TYPICAL_AREA_RANGES = {
        'office': {
            'min': 50,      # Small office suite
            'typical_min': 200,   # Typical small office
            'typical_max': 2000,  # Typical large office
            'max': 10000,   # Very large office building
        },
        'retail': {
            'min': 50,
            'typical_min': 100,
            'typical_max': 5000,
            'max': 50000,
        },
        'residential': {
            'min': 50,
            'typical_min': 100,
            'typical_max': 500,
            'max': 2000,
        },
        'warehouse': {
            'min': 200,
            'typical_min': 500,
            'typical_max': 10000,
            'max': 50000,
        },
        'school': {
            'min': 500,
            'typical_min': 1000,
            'typical_max': 5000,
            'max': 20000,
        },
        'hospital': {
            'min': 1000,
            'typical_min': 2000,
            'typical_max': 10000,
            'max': 50000,
        },
    }
    
    # Default range if building type unknown
    DEFAULT_RANGE = {
        'min': 50,
        'typical_min': 200,
        'typical_max': 2000,
        'max': 10000,
    }
    
    def __init__(self):
        """Initialize area validator."""
        pass
    
    def validate_area(self, area_m2: float, building_type: str = 'office', 
                     area_source: str = 'unknown', 
                     stories: Optional[int] = None) -> Dict:
        """
        Validate building area against typical ranges.
        
        Args:
            area_m2: Building area in square meters (per floor)
            building_type: Building type (office, retail, etc.)
            area_source: Source of area (osm, city_data, default, user)
            stories: Number of stories (optional, for total area context)
            
        Returns:
            Dictionary with validation results:
            {
                'is_valid': bool,
                'warning_level': str,  # 'none', 'minor', 'major'
                'warning_message': str,
                'typical_range': (min, max),
                'is_outlier': bool,
                'deviation_factor': float,  # How many times larger/smaller than typical
                'recommendation': str
            }
        """
        if area_m2 is None or area_m2 <= 0:
            return {
                'is_valid': False,
                'warning_level': 'major',
                'warning_message': f'Invalid area: {area_m2} m² (must be > 0)',
                'typical_range': None,
                'is_outlier': True,
                'deviation_factor': None,
                'recommendation': 'Use default area or check area calculation'
            }
        
        # Get typical range for building type
        building_type_lower = building_type.lower() if building_type else 'office'
        range_data = self.TYPICAL_AREA_RANGES.get(building_type_lower, self.DEFAULT_RANGE)
        
        typical_min = range_data['typical_min']
        typical_max = range_data['typical_max']
        abs_min = range_data['min']
        abs_max = range_data['max']
        
        # Check if within absolute limits
        if area_m2 < abs_min:
            return {
                'is_valid': False,
                'warning_level': 'major',
                'warning_message': f'Area unusually small: {area_m2:.1f} m² (typical: {typical_min}-{typical_max} m²)',
                'typical_range': (typical_min, typical_max),
                'is_outlier': True,
                'deviation_factor': area_m2 / typical_min if typical_min > 0 else None,
                'recommendation': f'Consider minimum area of {typical_min} m²'
            }
        
        if area_m2 > abs_max:
            return {
                'is_valid': False,
                'warning_level': 'major',
                'warning_message': f'Area unusually large: {area_m2:.1f} m² (typical: {typical_min}-{typical_max} m²)',
                'typical_range': (typical_min, typical_max),
                'is_outlier': True,
                'deviation_factor': area_m2 / typical_max if typical_max > 0 else None,
                'recommendation': f'Consider maximum area of {abs_max} m² or verify OSM data accuracy'
            }
        
        # Check if within typical range
        if area_m2 < typical_min:
            deviation = typical_min / area_m2 if area_m2 > 0 else None
            return {
                'is_valid': True,
                'warning_level': 'minor',
                'warning_message': f'Area below typical: {area_m2:.1f} m² (typical: {typical_min}-{typical_max} m²)',
                'typical_range': (typical_min, typical_max),
                'is_outlier': True,
                'deviation_factor': deviation,
                'recommendation': None
            }
        
        if area_m2 > typical_max:
            deviation = area_m2 / typical_max if typical_max > 0 else None
            return {
                'is_valid': True,
                'warning_level': 'major' if deviation > 2.0 else 'minor',
                'warning_message': f'Area above typical: {area_m2:.1f} m² (typical: {typical_min}-{typical_max} m², {deviation:.1f}x larger)',
                'typical_range': (typical_min, typical_max),
                'is_outlier': True,
                'deviation_factor': deviation,
                'recommendation': 'Verify OSM area calculation or building data accuracy' if deviation > 2.0 else None
            }
        
        # Within typical range
        return {
            'is_valid': True,
            'warning_level': 'none',
            'warning_message': None,
            'typical_range': (typical_min, typical_max),
            'is_outlier': False,
            'deviation_factor': 1.0,
            'recommendation': None
        }
    
    def cap_area(self, area_m2: float, building_type: str = 'office') -> float:
        """
        Cap area to reasonable maximum for building type.
        
        Args:
            area_m2: Building area in square meters
            building_type: Building type
            
        Returns:
            Capped area (original if within range, or capped to max)
        """
        range_data = self.TYPICAL_AREA_RANGES.get(building_type.lower(), self.DEFAULT_RANGE)
        max_area = range_data['typical_max']
        
        if area_m2 > max_area:
            logger.warning(f"Capping area from {area_m2:.1f} m² to {max_area} m² (typical max for {building_type})")
            return max_area
        
        return area_m2
    
    def get_recommended_area(self, building_type: str = 'office', stories: int = 3) -> float:
        """
        Get recommended default area for building type.
        
        Args:
            building_type: Building type
            stories: Number of stories
            
        Returns:
            Recommended area per floor in m²
        """
        range_data = self.TYPICAL_AREA_RANGES.get(building_type.lower(), self.DEFAULT_RANGE)
        # Use middle of typical range
        recommended = (range_data['typical_min'] + range_data['typical_max']) / 2
        return recommended
    
    def log_validation_result(self, area_m2: float, validation_result: Dict, 
                            area_source: str, address: Optional[str] = None):
        """
        Log validation result with appropriate level.
        
        Args:
            area_m2: Building area
            validation_result: Result from validate_area()
            area_source: Source of area
            address: Building address (optional)
        """
        warning_level = validation_result['warning_level']
        message = validation_result['warning_message']
        
        log_prefix = f"Area validation ({area_source}"
        if address:
            log_prefix += f", {address}"
        log_prefix += f"): {area_m2:.1f} m²"
        
        if warning_level == 'major':
            logger.warning(f"{log_prefix} - ⚠️ {message}")
            if validation_result.get('recommendation'):
                logger.warning(f"  Recommendation: {validation_result['recommendation']}")
        elif warning_level == 'minor':
            logger.info(f"{log_prefix} - ℹ️ {message}")
        else:
            logger.debug(f"{log_prefix} - ✓ Valid area")
    
    def validate_and_log(self, area_m2: float, building_type: str = 'office',
                        area_source: str = 'unknown', address: Optional[str] = None,
                        stories: Optional[int] = None, auto_cap: bool = False) -> Tuple[float, Dict]:
        """
        Validate area, log result, and optionally cap.
        
        Args:
            area_m2: Building area in square meters
            building_type: Building type
            area_source: Source of area
            address: Building address (optional)
            stories: Number of stories (optional)
            auto_cap: If True, cap area to max if outlier
            
        Returns:
            Tuple of (final_area, validation_result)
        """
        validation_result = self.validate_area(area_m2, building_type, area_source, stories)
        
        self.log_validation_result(area_m2, validation_result, area_source, address)
        
        final_area = area_m2
        if auto_cap and validation_result['is_outlier']:
            if validation_result['deviation_factor'] and validation_result['deviation_factor'] > 2.0:
                final_area = self.cap_area(area_m2, building_type)
                validation_result['capped'] = True
                validation_result['original_area'] = area_m2
                validation_result['capped_area'] = final_area
                logger.info(f"Capped area from {area_m2:.1f} m² to {final_area:.1f} m²")
        
        return final_area, validation_result
