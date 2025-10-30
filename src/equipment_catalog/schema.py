from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CurveSpec:
    """Specification of a performance curve and coefficients."""
    curve_type: str  # 'Curve:Biquadratic', 'Curve:Quadratic', etc.
    name: str
    coefficients: List[float]
    min_x: float = 0.0
    max_x: float = 1.0
    min_y: float = 0.0
    max_y: float = 1.0


@dataclass
class PerformanceMap:
    """Normalized performance maps for capacity, EIR, PLF vs PLR, etc."""
    total_capacity_f_of_t: Optional[CurveSpec] = None
    eir_f_of_t: Optional[CurveSpec] = None
    eir_f_of_plr: Optional[CurveSpec] = None
    plf_f_of_plr: Optional[CurveSpec] = None
    fan_power_f_of_flow: Optional[CurveSpec] = None


@dataclass
class EquipmentSpec:
    """Normalized equipment spec for translation to IDF."""
    equipment_type: str  # 'DX_COIL', 'RTU', 'PTAC', 'CHILLER_EIR', 'BOILER_HW', etc.
    name: str
    rated_capacity_w: Optional[float] = None
    rated_airflow_m3s: Optional[float] = None
    rated_cop: Optional[float] = None
    rated_eer: Optional[float] = None
    rated_ier: Optional[float] = None
    refrigerant: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    performance: PerformanceMap = field(default_factory=PerformanceMap)




