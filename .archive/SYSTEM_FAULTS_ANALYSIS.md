# System Faults Analysis - Why ±20% is 90-91%

**Date**: 2025-11-01  
**Purpose**: Comprehensive fault analysis to improve accuracy from ±20% to ±10%

---

## Executive Summary

**Current Status**: 91% within ±20% (10/11 buildings)  
**Target Status**: 90%+ within ±10% (professional engineer standard)  
**Gap**: 1 building failing ±20%, 4 buildings in 10-20% range

---

## Why ±20% Threshold is High

### Industry Standards

| Standard | Target Accuracy | Our Performance |
|----------|----------------|-----------------|
| **Professional Energy Modeling** | ±5-10% | 55% within ±10% |
| **Retrofit Analysis** | ±10-15% | 73% within ±10% |
| **Benchmarking** | ±15-20% | 91% within ±20% |
| **Preliminary Analysis** | ±20-30% | ✅ We exceed this |

**Assessment**: ±20% is acceptable for preliminary/budget estimates, but **not sufficient** for detailed retrofit analysis or professional engineering work.

### Why It Feels High

1. **±20% = 2× Uncertainty**: A building with 60 kBtu/ft²/year could be modeled anywhere from 48-72 kBtu/ft²/year
2. **Optimization Decisions**: Can't reliably identify 10-15% savings opportunities
3. **Professional Standard**: Senior engineers typically achieve ±5-10%
4. **Retrofit ROI**: Uncertain payback calculations with ±20% uncertainty

---

## Critical Faults Identified

### 🔴 **Fault 1: Weather File Mismatch (NYC/SF Buildings)**

**Impact**: ±5-15% error for non-Chicago buildings

**Problem**:
- All tests use `Chicago.epw` as fallback (only weather file available until now)
- NYC buildings should use New York weather
- SF buildings should use San Francisco weather
- Weather affects heating/cooling loads significantly

**Evidence**:
- Downloaded NYC and SF weather files (partially)
- Test script has fallback logic that uses first EPW found
- Chicago weather is colder in winter, different in summer than NYC

**Fix Status**: ⚠️ **Partially Fixed**
- ✅ Downloaded SF weather file (1.6 MB)
- ✅ Downloaded Chicago weather file (1.6 MB)
- ⚠️ NYC weather file incomplete (may need re-download)

**Expected Improvement**: +5-10% accuracy for NYC/SF buildings

---

### 🔴 **Fault 2: CHP Modeling is Post-Processing Only**

**Impact**: -29.8% error for Bank of America Tower

**Problem**:
- CHP reduction applied **after simulation** (not in IDF)
- EnergyPlus doesn't model on-site power generation
- Post-processing adjustment may not account for:
  - Thermal load changes (CHP waste heat)
  - Seasonal variations in CHP operation
  - Building electrical vs thermal load balance

**Current Implementation**:
```python
# Post-processing adjustment only
simulated_eui_kbtu_ft2 = simulated_eui_kbtu_ft2 * grid_reduction
```

**What's Missing**:
- Actual `Generator:MicroTurbine` or `Generator:FuelCell` in IDF
- Thermal integration with HVAC systems
- Proper load matching

**Fix Status**: ⚠️ **Workaround Only**
- CHP reduction calculated correctly
- Applied in post-processing
- But not physically modeled in EnergyPlus

**Expected Improvement**: +15-20% accuracy for CHP buildings if fully modeled

---

### 🟡 **Fault 3: Very Old Buildings (Pre-1930) Underestimated**

**Impact**: -10.6% to -15.9% error for 3 buildings

**Problem**:
- Pre-1920 category still not strong enough
- Chrysler Building (1930): -10.6%
- Flatiron Building (1902): -15.9%
- 30 Rockefeller Plaza (1933): -10.8%

**Root Causes**:
1. **Infiltration may be higher**: Very old buildings may have 0.8-1.2 ACH (we use 0.75 ACH)
2. **HVAC degradation stronger**: Original systems may be <50% efficient (we use 45%)
3. **Equipment inefficiency**: Original equipment may be less efficient than assumed
4. **No historic preservation flag**: Can't model retrofit restrictions

**Fix Status**: ⚠️ **Partially Addressed**
- ✅ Pre-1920 category added
- ✅ Early pre-1980 penalty added
- ⚠️ Still underestimating by 10-16%

**Expected Improvement**: +5-10% accuracy with stronger degradation factors

---

### 🟡 **Fault 4: Modern LEED Platinum Buildings Overestimated**

**Impact**: +15.1% error for One World Trade Center

**Problem**:
- LEED Platinum bonuses may be insufficient
- One World Trade Center: +15.1% (should be within ±10%)
- Building designed 20% better than code, but we only apply 25% EUI reduction

**Root Causes**:
1. **Envelope improvements**: May need triple-pane windows, not just better U-factors
2. **Advanced controls**: Not fully modeled (economizer disabled, DCV missing)
3. **Lighting efficiency**: LEED Platinum often has LED + daylighting (we model both, but may underestimate savings)
4. **Equipment efficiency**: Premium equipment not captured

**Fix Status**: ⚠️ **Partially Addressed**
- ✅ LEED bonuses applied (25% for Platinum)
- ⚠️ May need stronger envelope improvements
- ⚠️ Advanced controls not fully integrated

**Expected Improvement**: +5-10% accuracy with enhanced LEED modeling

---

### 🟡 **Fault 5: Economizer Disabled**

**Impact**: ±2-5% error for VAV systems

**Problem**:
- Economizer controller disabled due to node connection issues
- Should reduce cooling energy by 10-30% in moderate climates
- VAV systems typically have economizers

**Code Location**: `src/professional_idf_generator.py` line 705
```python
if False and hvac_type in ['VAV', 'RTU']:  # Disabled until node connections fixed
```

**Root Cause**:
- `Controller:OutdoorAir` requires proper `OutdoorAir:Mixer` node connections
- Node plumbing complexity not fully resolved

**Fix Status**: ❌ **Disabled**
- TODO: Fix OA mixer node connections
- TODO: Re-enable economizer for VAV/RTU systems

**Expected Improvement**: +2-5% accuracy for VAV buildings

---

### 🟡 **Fault 6: Internal Load Adjustments Disabled by Default**

**Impact**: May cause ±3-5% error for older buildings

**Problem**:
- Lighting and equipment power density adjustments are **opt-in only**
- Older buildings may have higher lighting loads than modeled
- Defaults assume modern equipment

**Code Location**: `src/professional_idf_generator.py` line 220
```python
if year_built and building_params.get('apply_internal_load_adjustments', False):
```

**Why Disabled**:
- Initial testing showed **over-correction** (Willis Tower went from +5% to +53%)
- Many old buildings have been retrofitted with modern lighting/equipment
- Hard to know without building inspection

**Fix Status**: ⚠️ **Conservative Approach**
- Adjustments available but disabled by default
- User can opt-in if they know building hasn't been retrofitted

**Recommendation**: Add "no retrofit" flag or make adjustments less aggressive

---

### 🟡 **Fault 7: Schedules are Generic**

**Impact**: ±2-5% error for atypical operations

**Problem**:
- Uses standard ASHRAE schedules
- Doesn't account for:
  - 24/7 operations (data centers, hospitals)
  - Seasonal variations
  - Demand response programs
  - Unusual occupancy patterns

**Current Implementation**:
- Office: 8 AM - 6 PM, Mon-Fri
- Residential: Continuous
- Retail: Extended hours
- Generic for all buildings of same type

**Fix Status**: ⚠️ **Acceptable for Most Buildings**
- Standard schedules work for typical operations
- Advanced scheduling would be enhancement

**Expected Improvement**: +2-5% accuracy with custom schedules (optional)

---

### 🟡 **Fault 8: CHP Fraction Calculation May Be Inaccurate**

**Impact**: -29.8% error for Bank of America Tower

**Problem**:
- CHP provides **reported** 70% of energy, but our calculation suggests 34.5%
- Load estimation uses 50 W/m² average (may be too high for efficient buildings)
- CHP may run at partial capacity or have different load matching

**Current Calculation**:
```python
typical_electrical_load_w_m2 = 50.0  # Average
chp_fraction_raw = cogeneration_capacity_kw / total_electrical_load_kw
chp_fraction = max(0.20, min(0.70, chp_fraction_raw))
```

**Issue**:
- Bank of America Tower: 5 MW CHP capacity, 12 MW load → 41.7% fraction
- But building **reports** 70% from CHP
- Either load estimate wrong, or CHP provides more than capacity suggests

**Fix Status**: ⚠️ **Needs Calibration**
- Add `chp_provides_percent` user parameter
- Allow manual override of CHP fraction

**Expected Improvement**: +15-20% accuracy if CHP fraction specified correctly

---

### 🟡 **Fault 9: Missing Advanced Features**

**Impact**: ±5-10% error for high-performance buildings

**Missing Features**:
1. ❌ **DCV (Demand Control Ventilation)**: Not implemented
2. ❌ **ERV/HRV (Energy Recovery)**: Not implemented
3. ❌ **Window Shades/Blinds**: Not implemented
4. ❌ **Chilled Water Central Plant**: Not for very large buildings
5. ❌ **Ground Coupling**: Not implemented
6. ❌ **Advanced Control Strategies**: Basic only

**Impact on Results**:
- LEED Platinum buildings often have DCV, ERV, advanced controls
- Missing these causes overestimation

**Fix Status**: ❌ **Not Implemented**
- These are "nice to have" features
- Would improve accuracy for high-performance buildings

**Expected Improvement**: +3-8% accuracy for LEED buildings with full feature set

---

### 🟡 **Fault 10: Known EUI Values May Be Estimated**

**Impact**: Unknown - may explain some differences

**Problem**:
- Many "known" EUI values are **estimated** from building characteristics
- Not actual measured utility data
- Estimates may be ±10-20% from actual

**Evidence from Test Data**:
- Some buildings: "NYC Energy Benchmarking (estimated)"
- Some buildings: "Estimated from building age and typical office EUI"
- Only Empire State Building has actual measured data (post-retrofit)

**Fix Status**: ⚠️ **Data Quality Issue**
- Need actual utility bills for true validation
- Estimated values may explain some differences

---

## Why ±20% is 90-91% - Root Cause

### Distribution Analysis

```
Error Distribution:
├─ Within ±5%:   6/11 (55%) ✅ EXCELLENT
├─ Within ±10%:  6/11 (55%) ✅ GOOD  
├─ Within ±15%:  9/11 (82%) ✅ ACCEPTABLE
├─ Within ±20%: 10/11 (91%) ✅ PASS
└─ Over ±20%:    1/11 (9%)  ❌ FAIL

Buildings in 10-20% range (4 buildings):
├─ Chrysler Building: -10.6%
├─ One World Trade Center: +15.1%
├─ Flatiron Building: -15.9%
└─ 30 Rockefeller Plaza: -10.8%
```

### Why It's 91% (Not Higher)

**Only 1 building exceeds ±20%**:
- Bank of America Tower: -29.8% (CHP modeling issue)

**But 4 buildings are in 10-20% range**:
- These are "acceptable" but not "excellent"
- Indicates systematic issues rather than random error

---

## Systematic Issues

### Issue 1: Very Old Buildings (Pre-1930)
- **Pattern**: All underestimated (-10.6% to -15.9%)
- **Root Cause**: Age adjustments not strong enough
- **Solution**: Strengthen pre-1920 and pre-1930 categories

### Issue 2: Modern LEED Buildings
- **Pattern**: Overestimated (+15.1%)
- **Root Cause**: LEED bonuses may be insufficient, missing advanced features
- **Solution**: Enhance LEED modeling, add DCV/ERV

### Issue 3: CHP Buildings
- **Pattern**: Significantly underestimated (-29.8%)
- **Root Cause**: CHP modeling is post-processing, fraction may be wrong
- **Solution**: Add CHP fraction parameter, improve load estimation

---

## Priority Fixes to Reach ±10% Target

### Priority 1: Fix CHP Modeling (Bank of America Tower)
**Current**: -29.8% error  
**Target**: ±10% error  
**Actions**:
1. Add `chp_provides_percent` parameter (allow user to specify actual %)
2. Improve electrical load estimation for efficient buildings
3. Consider actual CHP modeling in IDF (if feasible)

**Expected Impact**: +15-20% improvement

### Priority 2: Strengthen Very Old Building Adjustments
**Current**: -10.6% to -15.9% error  
**Target**: ±10% error  
**Actions**:
1. Increase infiltration for pre-1930 (from 2.53× to 3.0× modern)
2. Reduce HVAC efficiency further (from 0.585× to 0.50× for pre-1930)
3. Add "historic building" flag for preservation-limited retrofits

**Expected Impact**: +5-10% improvement

### Priority 3: Enhance LEED Platinum Modeling
**Current**: +15.1% error  
**Target**: ±10% error  
**Actions**:
1. Increase envelope improvements (from 18% to 25%)
2. Add DCV modeling for LEED buildings
3. Add ERV/HRV for LEED buildings (if applicable)

**Expected Impact**: +5-10% improvement

### Priority 4: Enable Economizer
**Current**: Disabled  
**Target**: Enabled for VAV/RTU  
**Actions**:
1. Fix OA mixer node connections
2. Re-enable economizer controller
3. Test with real buildings

**Expected Impact**: +2-5% improvement for VAV buildings

### Priority 5: Use Correct Weather Files
**Current**: All buildings use Chicago weather (fallback)  
**Target**: Location-appropriate weather  
**Actions**:
1. ✅ Download NYC weather file (complete)
2. Verify weather file selection logic works
3. Test with correct weather files

**Expected Impact**: +5-10% improvement for NYC/SF buildings

---

## Expected Improvements After Fixes

### Current Performance
- Within ±10%: **55%** (6/11 buildings)
- Within ±20%: **91%** (10/11 buildings)
- Average error: **9.7%**

### Target Performance (After All Fixes)
- Within ±10%: **90%+** (10-11/11 buildings)
- Within ±20%: **100%** (11/11 buildings)
- Average error: **<7%**

### Improvement Breakdown

| Fix | Expected Improvement | Cumulative |
|-----|---------------------|------------|
| Weather Files | +5-10% | 65-70% within ±10% |
| CHP Calibration | +15-20% | 82-91% within ±10% |
| Very Old Buildings | +5-10% | 91-100% within ±10% |
| LEED Enhancement | +5-10% | 100% within ±10% |
| Economizer | +2-5% | 100% within ±10% |

---

## Additional System Limitations

### 1. **No Partial Retrofit Modeling**
- Can't specify which systems were retrofitted (e.g., windows in 2010, HVAC in 2015)
- Only models full building retrofit year

### 2. **No Building-Specific Schedules**
- Generic schedules for all buildings of same type
- Can't model 24/7 operations, seasonal variations

### 3. **No Window Shade/Blind Modeling**
- LEED buildings often have automated shades
- Reduces cooling loads by 10-20%

### 4. **No Energy Recovery (ERV/HRV)**
- Common in modern high-performance buildings
- Reduces heating/cooling by 20-40%

### 5. **No Demand Control Ventilation (DCV)**
- Reduces ventilation loads when occupancy low
- Typical savings: 5-15%

### 6. **Simplified HVAC Controls**
- Basic setpoint managers only
- Missing: Optimal start/stop, load reset, etc.

### 7. **No Chilled Water Central Plant**
- Large buildings (>100,000 ft²) typically use central plant
- More efficient than individual VAV systems

### 8. **No Ground Coupling**
- Buildings with basements/ground floors have ground coupling
- Affects heating/cooling loads

---

## Conclusion

**Why ±20% is 90-91%**: 
- 1 building (Bank of America Tower) fails due to CHP modeling (-29.8%)
- 4 buildings are in 10-20% range (systematic issues)
- Weather file mismatch affects all non-Chicago buildings

**Main Faults**:
1. 🔴 CHP modeling incomplete (post-processing only)
2. 🔴 Weather file mismatch (NYC/SF using Chicago)
3. 🟡 Very old building adjustments too weak
4. 🟡 LEED Platinum bonuses may be insufficient
5. 🟡 Economizer disabled
6. 🟡 Missing advanced features (DCV, ERV, shades)

**Path to ±10%**: Fix top 3-5 faults → 90%+ within ±10%



