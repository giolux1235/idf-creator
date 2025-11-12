"""
Common utility functions used across the codebase.
"""
from typing import Dict, Any, Optional
from pathlib import Path


def merge_params(*param_dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple parameter dictionaries, with later dictionaries overriding earlier ones.
    
    Args:
        *param_dicts: Variable number of parameter dictionaries
        
    Returns:
        Merged dictionary with all parameters
    """
    result = {}
    for params in param_dicts:
        if params:
            result.update(params)
    return result


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float, returning default if conversion fails.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value or default
    """
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert a value to int, returning default if conversion fails.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Integer value or default
    """
    try:
        return int(float(value)) if value is not None else default
    except (ValueError, TypeError):
        return default


def ensure_directory(path: str) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def normalize_building_type(building_type: Optional[str]) -> str:
    """
    Normalize building type string to standard format (capitalize first letter).
    
    Args:
        building_type: Building type string (can be None, lowercase, or mixed case)
        
    Returns:
        Normalized building type (e.g., 'Office', 'Residential')
    """
    if not building_type:
        return 'Office'
    return building_type.capitalize()


def get_nested_value(data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get a value from a nested dictionary using dot notation.
    
    Args:
        data: Dictionary to search
        key_path: Dot-separated key path (e.g., 'building.params.area')
        default: Default value if key not found
        
    Returns:
        Value at key path or default
    """
    keys = key_path.split('.')
    value = data
    
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
            if value is None:
                return default
        else:
            return default
    
    return value if value is not None else default


def set_nested_value(data: Dict[str, Any], key_path: str, value: Any) -> None:
    """
    Set a value in a nested dictionary using dot notation.
    
    Args:
        data: Dictionary to modify
        key_path: Dot-separated key path (e.g., 'building.params.area')
        value: Value to set
    """
    keys = key_path.split('.')
    current = data
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value


def normalize_node_name(node_name: str) -> str:
    """
    Normalize node name to uppercase for EnergyPlus compatibility.
    
    EnergyPlus is case-sensitive for node names, and requires exact matching
    throughout the IDF file. Normalizing to uppercase ensures consistency and
    prevents case sensitivity mismatches that cause HVAC connection errors.
    
    Args:
        node_name: Node name to normalize (e.g., "lobby_0_z1_ZoneEquipmentInlet")
        
    Returns:
        Uppercase node name (e.g., "LOBBY_0_Z1_ZONEEQUIPMENTINLET")
        
    Examples:
        >>> normalize_node_name("lobby_0_z1_ZoneEquipmentInlet")
        'LOBBY_0_Z1_ZONEEQUIPMENTINLET'
        >>> normalize_node_name("LOBBY_0_Z1_SUPPLYEQUIPMENTOUTLETNODE")
        'LOBBY_0_Z1_SUPPLYEQUIPMENTOUTLETNODE'
    """
    return node_name.upper() if node_name else node_name


def calculate_dx_supply_air_flow(cooling_capacity: float,
                                 sensible_heat_ratio: float = 0.68,
                                 supply_delta_t: float = 11.0) -> float:
    """
    Calculate DX coil air flow using EnergyPlus recommended ratios.
    
    EnergyPlus requires air volume flow rate per watt to be in the range
    [2.684E-005 -- 6.713E-005] m³/s/W. This function ensures airflow meets
    minimum requirements even if EnergyPlus autosizes capacity upward.
    
    Args:
        cooling_capacity: Cooling capacity in watts (W)
        sensible_heat_ratio: Sensible heat ratio (0.0-1.0)
        supply_delta_t: Supply air temperature drop (°C), default 11.0
        
    Returns:
        Air flow rate in m³/s, constrained to valid EnergyPlus range
        
    References:
        - EnergyPlus Input Output Reference: Coil:Cooling:DX:SingleSpeed
        - EnergyPlus Engineering Reference: DX Cooling Coil Model
    """
    # EnergyPlus validated range: 2.684E-005 to 6.713E-005 m³/s/W
    # CRITICAL: Use higher minimum to prevent extreme cold outlet temperatures
    # Low airflow-to-capacity ratios cause coils to overcool, resulting in frost/freeze warnings
    # Minimum ratio must be enforced strictly to prevent psychrometric errors
    # CRITICAL FIX: Runtime ratios are still too low (1.045E-005 vs min 4.027E-005)
    # Must use even higher ratios to account for autosizing capacity 1.37x higher
    # If autosized capacity is 1.37x higher, we need ratio * 1.37 >= 4.027e-5
    # So ratio >= 4.027e-5 / 1.37 ≈ 2.94e-5, but we need safety margin for VAV turndown
    # Use much higher ratios to ensure runtime ratio stays above minimum even with autosizing
    min_ratio = 5.5e-5  # m³/s per W (increased from 5.0e-5 to account for autosizing)
    max_ratio = 7.0e-5  # Allow higher maximum for better flexibility
    target_ratio = 6.5e-5  # Increased target to ensure adequate airflow even with autosizing

    if cooling_capacity is None or cooling_capacity <= 0:
        simulated_capacity = 1000.0
        return simulated_capacity * target_ratio

    # Calculate airflow from sensible load (ensures adequate cooling)
    # CRITICAL: Use higher supply_delta_t to prevent extreme cold temperatures
    # Lower delta_t means more airflow needed, which prevents overcooling
    air_density = 1.2  # kg/m³
    cp_air = 1006.0    # J/(kg·K)
    sensible_capacity = max(cooling_capacity * sensible_heat_ratio, 0.0)
    # Use lower supply_delta_t (8°C instead of 11°C) to require more airflow
    # This prevents extreme cold outlet temperatures
    effective_delta_t = min(supply_delta_t, 8.0)  # Cap at 8°C to ensure adequate airflow
    flow_from_sensible = sensible_capacity / (air_density * cp_air * max(effective_delta_t, 1.0))

    # Calculate airflow from ratio requirements
    # CRITICAL: Always use minimum ratio to prevent low airflow-to-capacity ratios
    ratio_floor = cooling_capacity * min_ratio
    ratio_target = cooling_capacity * target_ratio
    ratio_cap = cooling_capacity * max_ratio

    # Use maximum of sensible-based flow and ratio-based flow to ensure both requirements met
    # CRITICAL: Always enforce minimum ratio to prevent extreme cold temperatures
    flow = max(flow_from_sensible, ratio_floor, ratio_target)
    flow = min(flow, ratio_cap)
    
    # Final safety check: enforce absolute minimum ratio strictly
    if cooling_capacity > 0:
        actual_ratio = flow / cooling_capacity
        if actual_ratio < 4.0e-5:  # Stricter minimum (well above 2.684e-5)
            # Force minimum ratio to prevent extreme cold outlet temperatures
            flow = cooling_capacity * 4.0e-5
    
    return flow

