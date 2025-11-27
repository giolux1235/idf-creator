# Convergence Plan - Making IDF Creator Match Real Building Energy Data

## Goal
Calibrate IDF Creator simulations to match actual energy consumption data from LEED PDF reports within ±15% error tolerance.

---

## Current Status

Based on last test run:
- **Test 1**: Energy Error: ~-21% (Good - needs minor tuning)
- **Test 2**: Works individually, segfaults in suite  
- **Test 3**: Passing (no target data)
- **Test 4**: Energy Error: ~+400% (Needs major calibration)
- **Test 5**: Energy Error: ~+3300% (Needs major calibration)

---

## How Convergence Works

### 1. **Calibration Parameters**
The system can adjust these parameters to match target energy:

| Parameter | Impact | Typical Range |
|-----------|--------|---------------|
| **Lighting Power Density** | High | 0.5x - 2.0x base value |
| **Equipment Power Density** | High | 0.5x - 2.0x base value |
| **HVAC Efficiency (COP/EER)** | High | 0.8x - 1.5x efficiency |
| **Fan Power** | Medium | 0.5x - 1.5x base value |
| **Infiltration Rate** | Medium | 0.3x - 1.5x base value |
| **Occupancy Density** | Low | 0.8x - 1.2x base value |

### 2. **Calibration Process**

```
1. Run baseline simulation → Get initial energy results
2. Compare with target energy → Calculate error %
3. If error > tolerance:
   a. Calculate calibration factors based on error
   b. Apply factors to IDF (lighting, equipment, HVAC, etc.)
   c. Re-simulate
   d. Check if converged
   e. Repeat up to 5 iterations
4. Save calibrated IDF and factors
```

### 3. **Calibration Factors Calculation**

For energy that's **too high** (simulated > target):
- **Reduce** lighting/equipment power density
- **Improve** HVAC efficiency (increase COP/EER)
- **Reduce** fan power and infiltration

For energy that's **too low** (simulated < target):
- **Increase** lighting/equipment power density  
- **Reduce** HVAC efficiency (more realistic)
- **Increase** infiltration (older buildings)

---

## Implementation Strategy

### Phase 1: Setup Convergence Infrastructure ✅

1. **Create Convergence Workflow Script** (`scripts/convergence_workflow.py`)
   - Iterative calibration loop
   - Error tracking and reporting
   - Automatic factor calculation

2. **Integrate with Test Suite**
   - Add convergence option to test runner
   - Save calibrated IDFs and factors
   - Track convergence history

### Phase 2: Apply Convergence to Passing Tests

1. **Test 1** (Restaurant, -21% error):
   - Start with minor adjustments
   - Target: ±15% error
   - Expected: 1-2 iterations

2. **Test 4** (Office, +400% error):
   - Major calibration needed
   - Focus on reducing lighting/equipment
   - Improve HVAC efficiency
   - Expected: 3-5 iterations

3. **Test 5** (Office, +3300% error):
   - Extreme calibration needed
   - Check if building area is correct
   - Major parameter reductions
   - Expected: 5+ iterations or data validation

### Phase 3: Learn from Benchmarks

1. **Save Calibration Factors** by building type:
   - Office: `artifacts/calibration_factors.json`
   - Restaurant: Learn from Test 1
   - Residential: Learn from Test 2

2. **Apply Learned Factors** to new buildings:
   - Use average factors for similar building types
   - Speed up convergence for new buildings

---

## Usage

### Run Convergence on All Passing Tests:
```bash
python3 scripts/convergence_workflow.py
```

### Run Convergence on Specific Test:
```bash
python3 scripts/convergence_workflow.py --test 1 --tolerance 0.15
```

### Run with Custom Tolerance:
```bash
python3 scripts/convergence_workflow.py --tolerance 0.10  # 10% tolerance
```

---

## Expected Results

After convergence:
- **Test 1**: Energy Error: -21% → ±15% ✅
- **Test 4**: Energy Error: +400% → ±15% ✅  
- **Test 5**: Energy Error: +3300% → ±15% (or identify data issues)

All tests should converge within 5 iterations or identify data/configuration issues.

---

## Next Steps

1. ✅ Create convergence workflow script
2. ⏭️ Run convergence on Test 1 (easiest - already close)
3. ⏭️ Run convergence on Test 4 (moderate calibration)
4. ⏭️ Run convergence on Test 5 (major calibration)
5. ⏭️ Save learned factors and apply to new buildings
6. ⏭️ Integrate convergence into automated test suite

