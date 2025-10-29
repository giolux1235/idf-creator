"""Translate normalized equipment specs into EnergyPlus IDF object strings."""

from typing import List
from ..schema import EquipmentSpec, CurveSpec


def _format_curve(curve: CurveSpec) -> str:
    if curve.curve_type == 'Curve:Biquadratic':
        a,b,c,d,e,f = curve.coefficients + [0]*(6-len(curve.coefficients))
        return f"""Curve:Biquadratic,
  {curve.name},
  {a:.6f}, {b:.6f}, {c:.6f}, {d:.6f}, {e:.6f}, {f:.6f},
  {curve.min_x:.6f}, {curve.max_x:.6f}, {curve.min_y:.6f}, {curve.max_y:.6f};
"""
    if curve.curve_type == 'Curve:Quadratic':
        a,b,c = curve.coefficients + [0]*(3-len(curve.coefficients))
        return f"""Curve:Quadratic,
  {curve.name},
  {a:.6f}, {b:.6f}, {c:.6f},
  {curve.min_x:.6f}, {curve.max_x:.6f};
"""
    return f"! Unsupported curve type {curve.curve_type} for {curve.name}\n"


def translate_dx_coil(spec: EquipmentSpec, name_suffix: str = "") -> List[str]:
    out: List[str] = []
    # Curves
    cap_curve_name = eir_curve_name = plf_curve_name = ""
    if spec.performance.total_capacity_f_of_t:
        c = spec.performance.total_capacity_f_of_t
        c = CurveSpec(curve_type=c.curve_type, name=f"{c.name}{name_suffix}", coefficients=c.coefficients, min_x=c.min_x, max_x=c.max_x, min_y=c.min_y, max_y=c.max_y)
        out.append(_format_curve(c))
        cap_curve_name = c.name
    if spec.performance.eir_f_of_t:
        c = spec.performance.eir_f_of_t
        c = CurveSpec(curve_type=c.curve_type, name=f"{c.name}{name_suffix}", coefficients=c.coefficients, min_x=c.min_x, max_x=c.max_x, min_y=c.min_y, max_y=c.max_y)
        out.append(_format_curve(c))
        eir_curve_name = c.name
    if spec.performance.plf_f_of_plr:
        c = spec.performance.plf_f_of_plr
        c = CurveSpec(curve_type=c.curve_type, name=f"{c.name}{name_suffix}", coefficients=c.coefficients, min_x=c.min_x, max_x=c.max_x)
        out.append(_format_curve(c))
        plf_curve_name = c.name

    # Coil object (simple single-speed)
    cap = spec.rated_capacity_w or 35000.0
    shrs = 0.75
    cop = spec.rated_cop or 3.0
    airflow = spec.rated_airflow_m3s or 1.2
    out.append(f"""Coil:Cooling:DX:SingleSpeed,
  {spec.name}{name_suffix},
  Always On,
  {cap:.2f},
  {shrs:.3f},
  {cop:.3f},
  {airflow:.3f},
  , , , ,
  {cap_curve_name},
  {eir_curve_name},
  ,
  {plf_curve_name},
  , , , ;
""")
    return out


def translate(spec: EquipmentSpec, name_suffix: str = "") -> List[str]:
    if spec.equipment_type == 'DX_COIL':
        return translate_dx_coil(spec, name_suffix)
    return [f"! Unsupported equipment type {spec.equipment_type} for {spec.name}\n"]


