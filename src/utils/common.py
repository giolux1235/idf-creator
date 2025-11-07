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


def calculate_dx_supply_air_flow(cooling_capacity: float) -> float:
    """
    Calculate DX coil air flow using EnergyPlus recommended ratios.
    
    EnergyPlus requires air volume flow rate per watt to be in the range
    [2.684E-005 -- 6.713E-005] m³/s/W. This function calculates the air flow
    rate using the midpoint of this range (4.0E-5 m³/s/W) as recommended
    by the EnergyPlus Engineering Reference.
    
    Args:
        cooling_capacity: Cooling capacity in watts (W)
        
    Returns:
        Air flow rate in m³/s, constrained to valid EnergyPlus range
        
    References:
        - EnergyPlus Input Output Reference: Coil:Cooling:DX:SingleSpeed
        - EnergyPlus Engineering Reference: DX Cooling Coil Model
    """
    min_ratio = 2.684e-5  # m³/s per W (EnergyPlus minimum)
    max_ratio = 6.713e-5  # m³/s per W (EnergyPlus maximum)
    target_ratio = 4.0e-5  # Recommended midpoint per Engineering Reference guidance

    if cooling_capacity is None or cooling_capacity <= 0:
        return 0.1  # Maintain minimum air flow for stability

    air_flow = cooling_capacity * target_ratio

    # Enforce EnergyPlus bounds
    air_flow = max(air_flow, cooling_capacity * min_ratio)
    air_flow = min(air_flow, cooling_capacity * max_ratio)

    return max(air_flow, 0.1)

