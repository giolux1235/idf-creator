# IDF Creator Outstanding Issues (EnergyPlus 24.2.0)

**Date:** 7 Nov 2025  
**Prepared by:** EnergyPlus local QA  
**Scope:** Errors and warnings that still originate in the IDF files returned by `https://web-production-3092c.up.railway.app`. Local tooling has been validated; remaining defects are service-side only.

---

## Summary Table

| Priority | Issue | Evidence | Impact | Recommended Action |
| --- | --- | --- | --- | --- |
| Critical | DX coils sized with airflow/ton ratio far below EnergyPlus limits | ~63 000 warnings per coil | Unrealistic coil behavior, cascade failures | Enforce `VolumeFlowPerRatedTotalCapacity` within 2.684e-5–6.713e-5 m³/s·W |
| Critical | Coil frost / outlet air < -80 °C | 24 000–27 000 warnings per coil | Invalid psychrometrics, zero sensible loads | Fix coil sizing (above) + set minimum outlet/operation limits |
| High | Low condenser dry-bulb temperatures (<0 °C) | 100–150 warnings per coil | Model outside spec; requires defrost logic | Add minimum outdoor temperature cutoff or heat-pump model |
| High | Psychrometric failures (`PsyWFnTdbH` invalid) | ~230 000 warnings | Energy results meaningless | Resolved once coils operate in valid regime |
| Medium | EUI ≈ 0.52 kWh/m²·yr | All test cases | Indicates loads not delivered | After sizing fix, review schedules & heating provision |

Each item is detailed below with root cause analysis and recommended remediation.

---

## 1. DX Cooling Coils: Air Volume Flow per Watt Out of Range (Critical)

### Evidence

```
** Warning ** CalcDoe2DXCoil: Coil:Cooling:DX:SingleSpeed="OFFICE_OPEN_0_22_Z28_COOLINGCOILDX" - Air volume flow rate per watt of rated total cooling capacity is out of range at 8.7E-006 m3/s/W.
**   ~~~   ** Expected range for VolumeFlowPerRatedTotalCapacity=[2.684E-005--6.713E-005]
```

Each coil emits approximately 60 000 warnings per annual simulation.

### Root Cause

`Rated Total Cooling Capacity` is set orders of magnitude too high relative to the fixed `Rated Air Flow Rate` (~0.5 m³/s). Resulting airflow per ton is ~8×10⁻⁶ m³/s·W, well below the EnergyPlus minimum (Engineering Reference, *Coil:Cooling:DX:SingleSpeed*).

### Impact

- Coil model operates outside calibrated envelope; downstream psychrometrics diverge.
- Drives frost warnings, negative humidity ratios, and collapses sensible load delivery.
- Subsequent KPIs (EUI, unmet load hours) become meaningless.

### Recommended Action

- Enforce compliant sizing in the generator: when `RatedTotalCoolingCapacity` is solved, set `RatedAirFlowRate = capacity_W * target_ratio` with `target_ratio` in `[2.684e-5, 6.713e-5]`; midpoint 4.5e-5 m³/s·W is recommended for margin.
- If airflow is predetermined, back-calculate capacity from the airflow using the same ratio bounds.
- Include regression/QA check that writes the ratio to logs and fails builds outside the envelope.
- Validate via `eplusout.eio` (`DX Coil Standard Rating Information`) after fix.

```python
MIN_RATIO = 2.684e-5
MAX_RATIO = 6.713e-5
TARGET_RATIO = 4.5e-5

def size_dx_coil_from_capacity(capacity_w, ratio=TARGET_RATIO):
    airflow_m3_s = capacity_w * ratio
    return capacity_w, airflow_m3_s

def size_dx_coil_from_airflow(airflow_m3_s, ratio=TARGET_RATIO):
    capacity_w = airflow_m3_s / ratio
    return capacity_w, airflow_m3_s
```

---

## 2. Coil Frost / Outlet Air Temperatures Below -80 °C (Critical)

### Evidence

```
** Warning ** ... Full load outlet temperature indicates a possibility of frost/freeze error continues.
**   ~~~   ** Outlet air temperature statistics follow:
**   ~~~   **   Max = -51.66 °C, Min = -82.61 °C
```

### Root Cause

- Direct consequence of #1: extreme capacity applied to undersized airflow drives coil leaving air to unphysical temperatures.
- No minimum compressor operating temperature or frost control configured.

### Impact

- Unrealistic discharge conditions render latent/sensible splits meaningless.
- Psychrometric routines receive negative humidity ratios, triggering global warning cascades.
- Simulation reports essentially zero useful cooling service.

### Recommended Action

1. Apply corrective sizing from Issue #1; expect discharge air in 10–14 °C range after fix.
2. Set `Minimum Outdoor Dry-Bulb Temperature for Compressor Operation` ≥ 5 °C on each `Coil:Cooling:DX:SingleSpeed`.
3. If heating mode uses shared outdoor unit, migrate to `CoilSystem:Cooling:DX:HeatPump` or `AirLoopHVAC:UnitarySystem` with frost protection enabled.
4. Add automated regression test that flags any coil outlet `< -5 °C` during design day runs.

---

## 3. Low Condenser Dry-Bulb Temperature (<0 °C) (High)

### Evidence

```
** Warning ** CalcDoe2DXCoil ... - Low condenser dry-bulb temperature error continues...
**   ~~~   ** Max=-0.025 °C, Min=-3.30 °C
```

### Root Cause

Air-cooled DX coils are operated below the validity range of the default performance curves. No defrost or shutdown logic is enforced when ambient < 0 °C.

### Impact

- Curve-fit efficiency/SHR predictions are invalid; coil may report negative capacities.
- Frost accumulation is inevitable; simulation does not reflect real-world limitations.

### Recommended Action

- After implementing #1 and #2, set the outdoor compressor cutoff (5 °C typical) to eliminate the warning.
- If cold-climate operation is required, switch to a heat-pump controller with `Defrost Strategy = ReverseCycle` and provide manufacturer-sourced defrost curves (Engineering Reference, *Heat Pump Coil Defrost*).

---

## 4. Psychrometric Failure – `PsyWFnTdbH` Invalid (High)

### Evidence

```
** Warning ** Calculated Humidity Ratio invalid (PsyWFnTdbH)
**   ~~~   ** This error occurred 228954 total times; Max=-0.000101, Min=-0.009350
```

### Root Cause

Coil exit states from Issues #1–#3 fall far outside the moist-air property envelope (enthalpy/temperature pair implies negative humidity ratio). The psychrometric helper clamps and warns, propagating NaNs through latent load reporting.

### Impact

- Moisture balances, comfort metrics, and any KPI derived from latent loads are unusable.
- Downstream automation treats simulation as failed (`simulation_status = error`).

### Recommended Action

- Resolves automatically once coils are re-sized and bounded. No additional code changes required beyond regression guardrails.

---

## 5. Energy Use Intensity ≈ 0.52 kWh/m²·year (Medium)

### Observation

- All validation addresses return annual EUI ≈ 0.52–0.53 kWh/m²·yr.
- DOE/ASHRAE reference medium offices expect ≥ 50 kWh/m²·yr (Appendix G, 90.1-2019).

### Root Cause Hypotheses

1. Cooling coils deliver near-zero sensible capacity due to upstream sizing error.
2. Generated IDFs lack active heating plant or thermostatic control (no `Coil:Heating:*`, no boiler district energy).
3. Occupancy/internal load schedules may be stuck at unoccupied minimum.

### Recommended Action

1. Re-run the five-address QA suite after implementing Issues #1–#4; expect EUI to rise by two orders of magnitude.
2. Confirm generator emits heating equipment and dual-setpoint thermostats (typical 21 °C occupied / 15 °C setback).
3. Align internal gains and schedules with DOE Reference Building datasets (e.g. `RefBldgMediumOfficeNew2004_Chicago.idf`).
4. Enable and review `Sizing:Zone`, `Sizing:System`, and `Sizing:Plant` autosizing reports to verify design loads are met post-fix.

---

## Next Steps

1. Implement remediation for Issues 1–5 in the IDF generation pipeline.
2. Deploy to Railway and notify QA. We will trigger the five-address validation suite immediately.
3. Acceptance criteria: `eplusout.err` free of DX coil warnings, psychrometric errors eliminated, and annual EUI within 50–200 kWh/m²·yr range for the test set.

---

## Key References

- EnergyPlus Input Output Reference (v24.2.0): `Coil:Cooling:DX:SingleSpeed`, `ThermostatSetpoint:*`, `Sizing:*` objects.
- EnergyPlus Engineering Reference (v24.2.0): DX coil rated conditions, psychrometric routines, heat pump defrost logic.
- DOE Reference Buildings – Medium Office: schedules, loads, and target EUIs.


