"""Module for validating building areas and flagging outliers."""
from typing import Dict, Optional, Tuple, List
import logging
import statistics

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
    
    def cap_area(self, area_m2: float, building_type: str = 'office', max_area: Optional[float] = None) -> float:
        """
        Cap area to reasonable maximum for building type.
        
        Args:
            area_m2: Building area in square meters
            building_type: Building type
            max_area: Optional custom maximum area (overrides typical_max if provided)
            
        Returns:
            Capped area (original if within range, or capped to max)
        """
        if max_area is not None:
            # Use custom max_area if provided
            if area_m2 > max_area:
                logger.warning(f"Capping area from {area_m2:.1f} m² to {max_area:.1f} m² (custom max)")
                return max_area
            return area_m2
        
        range_data = self.TYPICAL_AREA_RANGES.get(building_type.lower(), self.DEFAULT_RANGE)
        max_area_default = range_data['typical_max']
        
        if area_m2 > max_area_default:
            logger.warning(f"Capping area from {area_m2:.1f} m² to {max_area_default} m² (typical max for {building_type})")
            return max_area_default
        
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
                        stories: Optional[int] = None, auto_cap: bool = False,
                        max_area: Optional[float] = None) -> Tuple[float, Dict]:
        """
        Validate area, log result, and optionally cap.
        
        Args:
            area_m2: Building area in square meters
            building_type: Building type
            area_source: Source of area
            address: Building address (optional)
            stories: Number of stories (optional)
            auto_cap: If True, cap area to max if outlier
            max_area: Optional custom maximum area for capping (overrides typical_max)
            
        Returns:
            Tuple of (final_area, validation_result)
        """
        validation_result = self.validate_area(area_m2, building_type, area_source, stories)
        
        self.log_validation_result(area_m2, validation_result, area_source, address)
        
        final_area = area_m2
        if auto_cap and validation_result['is_outlier']:
            # Only cap extreme outliers that likely indicate calculation errors
            # Don't cap legitimate large buildings - respect real data
            should_cap = False
            
            # Get range data for building type
            range_data = self.TYPICAL_AREA_RANGES.get(building_type.lower(), self.DEFAULT_RANGE)
            
            if max_area is not None:
                # Custom max_area provided - cap if area exceeds it (for specific outlier cases)
                should_cap = area_m2 > max_area
            elif validation_result['deviation_factor']:
                # Get absolute max for building type
                abs_max = range_data.get('max', 10000)
                
                # Only cap if:
                # 1. Area exceeds absolute maximum (likely calculation error)
                # 2. AND deviation_factor > 2.0 (extreme outlier, suggesting error)
                # This respects legitimate large buildings while catching calculation errors
                if area_m2 > abs_max and validation_result['deviation_factor'] > 2.0:
                    should_cap = True
                    logger.warning(f"Extreme outlier detected: {area_m2:.1f} m² ({validation_result['deviation_factor']:.1f}x typical_max, exceeds abs_max {abs_max} m²) - likely calculation error")
            
            if should_cap:
                # Cap to typical_max (reasonable upper bound) or custom max_area
                cap_value = max_area if max_area is not None else range_data.get('typical_max', 2000)
                final_area = self.cap_area(area_m2, building_type, cap_value)
                validation_result['capped'] = True
                validation_result['original_area'] = area_m2
                validation_result['capped_area'] = final_area
                logger.info(f"Capped area from {area_m2:.1f} m² to {final_area:.1f} m² (extreme outlier correction)")
        
        return final_area, validation_result
    
    def verify_multiple_sources(self, area_sources: Dict[str, Optional[float]], 
                                building_type: str = 'office',
                                stories: Optional[int] = None) -> Dict:
        """
        Verify area from multiple sources and determine the most reliable value.
        
        Args:
            area_sources: Dictionary of area values from different sources, e.g.:
                {
                    'osm': 1060.85,      # OSM area
                    'city': 850.0,       # City data area
                    'estimated': 750.0,  # Estimated/default area
                    'user': None         # User-specified (if any)
                }
            building_type: Building type
            stories: Number of stories (optional)
            
        Returns:
            Dictionary with verification results:
            {
                'recommended_area': float,  # Best area to use
                'confidence': str,           # 'high', 'medium', 'low'
                'sources_agreement': str,   # 'excellent', 'good', 'poor', 'conflicting'
                'source_used': str,         # Which source was selected
                'all_sources': Dict,         # All available sources with validation
                'discrepancies': List,       # List of discrepancies found
                'explanation': str            # Human-readable explanation
            }
        """
        # Filter out None values and get valid areas
        valid_sources = {name: value for name, value in area_sources.items() 
                        if value is not None and value > 0}
        
        if not valid_sources:
            # No valid sources - use default
            range_data = self.TYPICAL_AREA_RANGES.get(building_type.lower(), self.DEFAULT_RANGE)
            default_area = (range_data['typical_min'] + range_data['typical_max']) / 2
            return {
                'recommended_area': default_area,
                'confidence': 'low',
                'sources_agreement': 'none',
                'source_used': 'default',
                'all_sources': {},
                'discrepancies': ['No valid area sources available'],
                'explanation': f'No valid area sources provided, using default: {default_area:.1f} m²'
            }
        
        # Validate each source
        source_validations = {}
        for source_name, area_value in valid_sources.items():
            validation = self.validate_area(area_value, building_type, source_name, stories)
            source_validations[source_name] = {
                'area': area_value,
                'is_valid': validation['is_valid'],
                'warning_level': validation['warning_level'],
                'is_outlier': validation['is_outlier'],
                'deviation_factor': validation['deviation_factor'],
                'within_typical_range': not validation['is_outlier'] or validation['deviation_factor'] <= 1.0
            }
        
        # Calculate statistics
        areas = list(valid_sources.values())
        if len(areas) == 1:
            # Single source
            source_name = list(valid_sources.keys())[0]
            validation = source_validations[source_name]
            confidence = 'high' if validation['within_typical_range'] else 'medium'
            return {
                'recommended_area': areas[0],
                'confidence': confidence,
                'sources_agreement': 'single_source',
                'source_used': source_name,
                'all_sources': source_validations,
                'discrepancies': [] if validation['within_typical_range'] else [
                    f"{source_name} area is outside typical range"
                ],
                'explanation': f'Single source ({source_name}): {areas[0]:.1f} m²'
            }
        
        # Multiple sources - calculate agreement
        median_area = statistics.median(areas)
        mean_area = statistics.mean(areas)
        std_dev = statistics.stdev(areas) if len(areas) > 1 else 0
        
        # Coefficient of variation (CV) - lower is better agreement
        cv = (std_dev / mean_area * 100) if mean_area > 0 else 0
        
        # Determine agreement level
        if cv < 10:
            agreement = 'excellent'
        elif cv < 25:
            agreement = 'good'
        elif cv < 50:
            agreement = 'poor'
        else:
            agreement = 'conflicting'
        
        # Find discrepancies
        discrepancies = []
        for source_name, validation in source_validations.items():
            area = validation['area']
            # Check if significantly different from median
            if abs(area - median_area) > median_area * 0.3:  # More than 30% difference
                discrepancies.append(
                    f"{source_name}: {area:.1f} m² ({abs(area - median_area) / median_area * 100:.1f}% from median)"
                )
        
        # Determine best source (priority order)
        # 1. User-specified (if available and valid)
        # 2. Source within typical range and closest to median
        # 3. Source closest to median
        # 4. Median of all sources
        
        recommended_area = None
        source_used = None
        confidence = 'medium'
        
        # Priority 1: User-specified
        if 'user' in valid_sources:
            user_area = valid_sources['user']
            user_validation = source_validations['user']
            if user_validation['within_typical_range']:
                recommended_area = user_area
                source_used = 'user'
                confidence = 'high'
        
        # Priority 2: Find source within typical range, closest to median
        if recommended_area is None:
            candidates = [(name, val['area']) for name, val in source_validations.items() 
                         if val['within_typical_range']]
            if candidates:
                # Choose closest to median
                closest = min(candidates, key=lambda x: abs(x[1] - median_area))
                recommended_area = closest[1]
                source_used = closest[0]
                confidence = 'high' if agreement in ['excellent', 'good'] else 'medium'
        
        # Priority 3: Use source closest to median (even if outlier)
        if recommended_area is None:
            closest = min(valid_sources.items(), key=lambda x: abs(x[1] - median_area))
            recommended_area = closest[1]
            source_used = closest[0]
            confidence = 'low'
        
        # Priority 4: Use median of all sources
        if recommended_area is None:
            recommended_area = median_area
            source_used = 'median_consensus'
            confidence = 'medium' if agreement in ['excellent', 'good'] else 'low'
        
        # Build explanation
        source_list = ', '.join([f"{name}: {area:.1f} m²" for name, area in valid_sources.items()])
        explanation = f"Multiple sources available: {source_list}. "
        if agreement == 'excellent':
            explanation += f"Excellent agreement (CV: {cv:.1f}%). Using {source_used}: {recommended_area:.1f} m²"
        elif agreement == 'good':
            explanation += f"Good agreement (CV: {cv:.1f}%). Using {source_used}: {recommended_area:.1f} m²"
        elif discrepancies:
            explanation += f"Conflicting sources detected. Using {source_used}: {recommended_area:.1f} m²"
        else:
            explanation += f"Using {source_used}: {recommended_area:.1f} m²"
        
        return {
            'recommended_area': recommended_area,
            'confidence': confidence,
            'sources_agreement': agreement,
            'source_used': source_used,
            'all_sources': source_validations,
            'discrepancies': discrepancies,
            'explanation': explanation,
            'statistics': {
                'median': median_area,
                'mean': mean_area,
                'std_dev': std_dev,
                'coefficient_of_variation': cv,
                'source_count': len(valid_sources)
            }
        }
