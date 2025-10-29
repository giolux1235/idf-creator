"""BCL adapter (placeholder) to retrieve equipment-like specs.

In a future step, this will query NREL BCL and map components to EquipmentSpec.
For now, provide a small mock that returns a reasonable DX coil spec with curves.
"""

from ..schema import EquipmentSpec, PerformanceMap, CurveSpec
import os
import json
from typing import Optional
import urllib.request


def mock_dx_coil(name: str = "Catalog_DX_Coil_3Ton") -> EquipmentSpec:
    cap_curve = CurveSpec(
        curve_type='Curve:Biquadratic',
        name=f"{name}_CapFT",
        coefficients=[0.8, 0.02, 0.0, 0.01, 0.0, -0.0005],
        min_x=15.0, max_x=45.0,  # Tdb
        min_y=10.0, max_y=24.0   # Twb
    )
    eir_curve = CurveSpec(
        curve_type='Curve:Biquadratic',
        name=f"{name}_EIRFT",
        coefficients=[1.2, -0.02, 0.0, -0.01, 0.0, 0.0004],
        min_x=15.0, max_x=45.0,
        min_y=10.0, max_y=24.0
    )
    plf_curve = CurveSpec(
        curve_type='Curve:Quadratic',
        name=f"{name}_PLFFPLR",
        coefficients=[0.90, 0.10, 0.0],
        min_x=0.0, max_x=1.0
    )
    perf = PerformanceMap(
        total_capacity_f_of_t=cap_curve,
        eir_f_of_t=eir_curve,
        plf_f_of_plr=plf_curve
    )
    return EquipmentSpec(
        equipment_type='DX_COIL',
        name=name,
        rated_capacity_w=10500.0,
        rated_airflow_m3s=0.5,
        rated_cop=3.4,
        performance=perf,
        metadata={"source": "mock_bcl"}
    )


def fetch_dx_by_capacity(capacity_label: str, bcl_api_key: Optional[str] = None) -> EquipmentSpec:
    """Placeholder for real BCL query by capacity; falls back to mock.

    capacity_label examples: '3ton', '35000W'
    """
    # TODO: Implement real BCL REST calls; for now, map simple labels
    name = f"Catalog_DX_Coil_{capacity_label}"
    spec = mock_dx_coil(name=name)
    spec.metadata.update({"requested_capacity": capacity_label, "source": "bcl_placeholder"})
    return spec


