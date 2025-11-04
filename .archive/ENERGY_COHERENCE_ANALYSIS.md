# Energy Coherence Analysis & Validation

**Date**: 2025-10-31  
**Status**: ✅ **Validation Framework Complete**

---

## Summary

Created comprehensive energy coherence validation system that:
1. ✅ Checks if energy values are physically realistic
2. ✅ Compares against CBECS benchmarks
3. ✅ Diagnoses zero/low/high energy issues
4. ✅ Provides fix suggestions

---

## Key Findings

### ✅ HVAC Systems Are Correct

**Checked IDF Files:**
- ✅ Empire State Building: **Real VAV System** (not Ideal Loads)
- ✅ Professional test 1: **Real VAV System**
- ✅ Professional test 2: **Real VAV System**

**Internal Loads:**
- ✅ Lights objects: Present (6-42 per building)
- ✅ Equipment objects: Present (3-21 per building)
- ✅ People objects: Present (9-63 per building)
- ✅ Schedules: Present (11-21 per building)

**Conclusion**: System is generating real HVAC systems correctly. If energy is zero, it's due to:
1. Simulation not completing (weather file missing)
2. Output meters not configured
3. CSV parsing issues

---

## Energy Coherence Validation

### What Gets Checked

1. **Zero Energy Detection**
   - ✅ Flags if total energy = 0
   - ✅ Checks if using Ideal Loads (doesn't report energy)
   - ✅ Verifies internal loads are defined

2. **EUI Benchmarking**
   - ✅ Compares against CBECS typical ranges
   - ✅ Flags if EUI < 30% of typical (too low)
   - ✅ Flags if EUI > 200% of typical (too high)
   - ✅ Warns if EUI 30-70% of typical (low but explainable)

3. **Component Analysis**
   - ✅ Checks lighting energy (should be > 0)
   - ✅ Checks equipment energy (should be > 0)
   - ✅ Checks HVAC/fan energy (expected if real HVAC)
   - ✅ Identifies missing components

4. **Physical Coherence**
   - ✅ Validates energy scales with building size
   - ✅ Checks energy distribution makes sense
   - ✅ Verifies no negative values

---

## CBECS Benchmark Ranges

### Typical EUI by Building Type (kBtu/ft²/year)

| Building Type | Typical EUI | Range (Acceptable) |
|---------------|-------------|-------------------|
| **Office** | 58.6 | 30-120 |
| **Retail** | 43.5 | 20-90 |
| **School** | 69.3 | 35-140 |
| **Hospital** | 214.0 | 100-430 |
| **Warehouse** | 28.1 | 15-60 |
| **Residential** | ~40 | 20-80 |

### Conversion: kBtu/ft²/year → kWh/m²/year
- **1 kBtu/ft²/year = 3.16 kWh/m²/year**
- Office: **185 kWh/m²/year** typical
- Range: 95-380 kWh/m²/year acceptable

---

## Common Issues & Fixes

### Issue 1: Zero Energy Consumption

**Symptoms:**
- Total energy = 0 kWh
- All component energies = 0
- EUI = 0

**Root Causes:**

1. **Using Ideal Loads HVAC** (not our case - we use VAV)
   - Fix: Already using real HVAC ✅
   
2. **Simulation Didn't Complete**
   - Symptom: Fatal errors in simulation
   - Common cause: Missing weather file
   - Fix: Download weather file or check error log

3. **Output Meters Not Configured**
   - Symptom: Simulation runs but CSV is empty
   - Fix: Add explicit output meters to IDF

4. **CSV Parsing Issues**
   - Symptom: Energy exists but not extracted
   - Fix: Check CSV column names and parsing logic

### Issue 2: Energy Too Low (< 30% of Typical)

**Symptoms:**
- EUI = 20-40 kWh/m²/year (expected: 100-150)
- Lighting energy present
- Equipment energy present
- HVAC energy missing or very low

**Possible Causes:**

1. **Missing HVAC Energy Meters**
   - VAV systems exist but energy not metered
   - Fix: Add output meters for fans, coils, pumps

2. **Schedule Issues**
   - Loads defined but schedules keep them off
   - Fix: Check schedule active periods

3. **Partial Simulation**
   - Only some zones simulated
   - Fix: Verify all zones included

### Issue 3: Energy Too High (> 200% of Typical)

**Symptoms:**
- EUI = 300+ kWh/m²/year
- All components very high

**Possible Causes:**

1. **Excessive Loads**
   - Lighting power density too high
   - Equipment loads excessive
   - Fix: Check load definitions against ASHRAE 90.1

2. **HVAC Efficiency Issues**
   - Low COP compressors
   - Inefficient fans
   - Fix: Verify HVAC efficiency settings

3. **Weather File Issues**
   - Extreme weather data
   - Wrong location
   - Fix: Verify weather file matches location

---

## Validation Framework

### Usage

```python
from src.validation import validate_energy_coherence

# Get energy results from simulation
from src.validation import EnergyPlusSimulationValidator
validator = EnergyPlusSimulationValidator()
energy_results = validator.get_energy_results(output_directory)

# Validate coherence
coherence = validate_energy_coherence(
    energy_results=energy_results,
    building_type='office',
    total_area_m2=5000,
    stories=3,
    idf_content=idf_content  # Optional, for HVAC checking
)

# Check results
if coherence['is_coherent']:
    print("✅ Energy results are physically coherent!")
else:
    print(f"❌ Found {coherence['issue_count']} issues")
    for issue in coherence['issues']:
        print(f"  - {issue.metric}: {issue.reason}")
        print(f"    Fix: {issue.fix_suggestion}")
```

### Output Example

```
Energy Coherence Validation Results:
  - Issues: 1
  - Warnings: 0
  
  Critical Issues:
    ❌ eui: 12.5 kBtu/ft²
      Reason: EUI 12.5 kBtu/ft² is very low (typical office: 58.6 kBtu/ft²)
      Fix: Check if HVAC systems are reporting energy. Verify internal loads are defined.
```

---

## Recommended Testing Workflow

### Step 1: Generate IDF with Real HVAC
```python
creator = IDFCreator(professional=True, enhanced=True)
idf_file = creator.create_idf(
    address="Empire State Building, New York, NY",
    user_params={
        'building_type': 'Office',
        'stories': 3,
        'floor_area': 5000,
        # simple_hvac=False is default in professional mode
    }
)
```

### Step 2: Verify HVAC System Type
```bash
python check_hvac_and_energy.py
```

Should show:
- ✅ Real VAV System detected
- ✅ Lights objects present
- ✅ Equipment objects present

### Step 3: Run Simulation
```python
from src.validation import validate_simulation
result = validate_simulation(
    idf_file=idf_file,
    weather_file='weather.epw',  # Download if needed
    output_directory='output'
)
```

### Step 4: Extract and Validate Energy
```python
from src.validation import EnergyPlusSimulationValidator, validate_energy_coherence

validator = EnergyPlusSimulationValidator()
energy_results = validator.get_energy_results(result.output_directory)

coherence = validate_energy_coherence(
    energy_results=energy_results,
    building_type='office',
    total_area_m2=5000 * 3,  # Total area
    stories=3
)
```

---

## Next Steps

### Immediate Actions

1. **Get Weather File**
   ```bash
   # Download New York weather file
   curl -O https://energyplus.net/weather/north_and_central_america_wmo_region_4/USA/NY/USA_NY_New.York.LaGuardia.AP.725030_TMY3/USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw
   ```

2. **Re-run Simulation with Weather**
   ```python
   python test_energy_coherence.py
   ```

3. **Check Energy Results**
   - Should show non-zero energy
   - Should match CBECS ranges
   - All components should be present

### Future Enhancements

1. **Auto-Configure Output Meters**
   - Add meters automatically in IDF generation
   - Ensure all HVAC energy is tracked

2. **Enhanced Diagnostics**
   - Check schedule active periods
   - Verify load calculations
   - Compare to DOE reference buildings

3. **Automated Reporting**
   - Generate coherence report
   - Flag issues before simulation
   - Suggest fixes automatically

---

## Conclusion

✅ **System Status**: Energy coherence validation framework complete

✅ **HVAC Systems**: Using real VAV systems (correct)

✅ **Internal Loads**: Properly defined (Lights, Equipment, People)

⚠️ **Current Issue**: Simulation requires weather file to complete and produce energy results

✅ **Solution**: Download weather file and re-run simulation to get realistic energy values

---

**Files Created:**
- `src/validation/energy_coherence_validator.py` - Validation framework
- `test_energy_coherence.py` - Testing script
- `check_hvac_and_energy.py` - HVAC system checker
- `ENERGY_COHERENCE_ANALYSIS.md` - This document



