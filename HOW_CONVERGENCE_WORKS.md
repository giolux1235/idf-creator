# How Convergence Works - Making IDF Creator Match Real Data

## Overview

Convergence automatically adjusts building parameters (lighting, equipment, HVAC efficiency, etc.) so simulated energy consumption matches real building data from PDF reports.

---

## The Problem

When we generate an IDF and simulate it, the energy results often don't match real building data:
- **Test 1**: Simulated 1,185,000 kWh vs Target 1,481,172 kWh = **-20% error**
- **Test 4**: Simulated 533,937 kWh vs Target 100,365 kWh = **+432% error**

## The Solution: Automatic Calibration

The convergence system iteratively adjusts parameters until simulated energy matches targets within ±15%.

---

## What Gets Adjusted

### 1. **Lighting Power Density** (High Impact)
- **What**: Amount of lighting power per square meter
- **How**: Reduce if energy too high, increase if too low
- **Impact**: ~15-30% of total energy consumption

### 2. **Equipment Power Density** (High Impact)  
- **What**: Plug loads, computers, appliances
- **How**: Reduce if energy too high, increase if too low
- **Impact**: ~30-40% of total energy consumption

### 3. **HVAC Efficiency** (High Impact)
- **What**: Cooling COP, heating efficiency
- **How**: Improve efficiency (higher COP) if energy too high
- **Impact**: ~35-45% of total energy consumption

### 4. **Fan Power** (Medium Impact)
- **What**: HVAC fan energy consumption
- **How**: Reduce fan power if energy too high
- **Impact**: ~15-20% of total energy consumption

### 5. **Infiltration Rate** (Medium Impact)
- **What**: Air leakage through building envelope
- **How**: Reduce infiltration if energy too high
- **Impact**: ~5-10% of total energy consumption

### 6. **Occupancy** (Low Impact)
- **What**: Number of people in building
- **How**: Minor adjustments to internal heat gains
- **Impact**: ~5% of total energy consumption

---

## How Convergence Works - Step by Step

### Step 1: Baseline Simulation
```
1. Generate IDF from building data
2. Run EnergyPlus simulation
3. Extract energy results (e.g., 1,200,000 kWh)
4. Compare with target (e.g., 1,000,000 kWh)
5. Calculate error: (1,200,000 - 1,000,000) / 1,000,000 = +20%
```

### Step 2: Calculate Adjustment Factors
```
If error is +20% (too high):
- Need to reduce energy by 20%
- Calculate multipliers:
  - Lighting: 0.85x (reduce by 15%)
  - Equipment: 0.85x (reduce by 15%)
  - HVAC efficiency: 1.15x (improve by 15%)
  - Fan power: 0.90x (reduce by 10%)
```

### Step 3: Apply Calibration to IDF
```
1. Read original IDF file
2. Multiply lighting power densities by 0.85
3. Multiply equipment power densities by 0.85
4. Increase HVAC COP by 15%
5. Reduce fan power by 10%
6. Save calibrated IDF
```

### Step 4: Re-Simulate
```
1. Run EnergyPlus with calibrated IDF
2. Extract new energy results (e.g., 1,050,000 kWh)
3. Compare with target: (1,050,000 - 1,000,000) / 1,000,000 = +5%
4. Check if converged (error < 15%)
```

### Step 5: Iterate If Needed
```
If error still > 15%:
- Repeat Steps 2-4 with new error
- Typically converges in 2-5 iterations
```

---

## Example: Test 1 Convergence

### Baseline:
- Target: 1,481,172 kWh
- Simulated: 1,185,000 kWh
- Error: -20%

### Iteration 1:
- Calibration: Increase lighting/equipment by 15%
- New simulated: 1,350,000 kWh
- Error: -9% ✅ **CONVERGED!**

---

## Running Convergence

### On All Passing Tests:
```bash
python3 scripts/convergence_workflow.py
```

### On Specific Test:
```bash
python3 scripts/convergence_workflow.py --test 1 --tolerance 0.15
```

### What Happens:
1. Runs baseline simulation
2. Calculates calibration factors
3. Applies to IDF and re-simulates
4. Repeats until converged (< 15% error) or max iterations (5)
5. Saves calibrated IDF and factors

---

## Results

After convergence, you get:
- ✅ Calibrated IDF files (`building_iter1.idf`, `building_iter2.idf`, etc.)
- ✅ Final calibrated IDF (`building_iter{final}.idf`)
- ✅ Calibration factors saved to `artifacts/calibration_factors.json`
- ✅ Convergence report with error history

---

## Learning from Benchmarks

Once calibrated, factors are saved by building type:
```json
{
  "office": {
    "lighting_multiplier": 0.85,
    "equipment_multiplier": 0.90,
    "hvac_efficiency_multiplier": 1.15
  },
  "restaurant": {
    "lighting_multiplier": 0.75,
    "equipment_multiplier": 1.20
  }
}
```

These factors are then applied to new buildings of the same type, making convergence faster!

---

## Next Steps

1. **Run convergence on Test 1** (already close at -20%)
   - Should converge in 1-2 iterations
   - Target: ±15% error

2. **Run convergence on Test 4** (+432% error)
   - Needs major calibration
   - Will take 3-5 iterations
   - Target: ±15% error

3. **Run convergence on Test 5** (+3300% error)
   - Extreme calibration or data issue
   - May need data validation first

4. **Save learned factors** for future buildings

