# Autistic Analysis: What's Really Wrong

**Date**: November 2, 2025

---

## Executive Summary

🔴 **MAJOR BUGS FOUND**

1. **Inconsistent zone generation** - Only 3 floors get full zones (0-2), rest get minimal zones
2. **Area calculation broken** - 36,032 m² reported vs 15,000 m² expected (240%!)
3. **Zone generation logic broken** - Something causing some floors to skip tiled zone generation

---

## Detailed Analysis

### Test Case
- **User specified**: 1,500 m²/floor × 10 stories = 15,000 m² total
- **Building**: Office, SF, 1995
- **IDF Zones**: 254 zones created

### Zone Distribution by Floor

| Floor | Zones | Status |
|-------|-------|--------|
| 0 | 68 | ✅ Full generation |
| 1 | 66 | ✅ Full generation |
| 2 | 68 | ✅ Full generation |
| 3 | 8 | 🔴 Minimal |
| 4 | 8 | 🔴 Minimal |
| 5 | 6 | 🔴 Minimal |
| 6 | 8 | 🔴 Minimal |
| 7 | 8 | 🔴 Minimal |
| 8 | 8 | 🔴 Minimal |
| 9 | 6 | 🔴 Minimal |

**Problem**: Only floors 0-2 get full tiled zone generation. Floors 3-9 only get core zones (lobby, conference, mechanical, etc.).

### Why?

Looking at `generate_zone_layout` in `src/advanced_geometry_engine.py`:

```python
# Generate zones for each floor
for floor in range(footprint.stories):  # Loops 0-9
    floor_zones = self._generate_floor_zones(
        footprint.polygon,  # Same polygon for ALL floors
        floor, building_type, template, total_area
    )
    zones.extend(floor_zones)
```

Each floor gets the SAME `footprint.polygon`, so geometry should be identical across all floors.

**BUT**: Floors 3-9 only get 6-8 zones vs 68 zones for floor 0!

**Root Cause**: Something in `_generate_typical_zones` is failing for floors 3-9.

---

## Surface Count Issues

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Total zones | 254 | 254 | ✅ Correct count |
| Floor surfaces | 254 (1 per zone) | 127 | 🔴 Only 50% |
| Wall surfaces | ~1000 (4 per zone) | 1056 | ⚠️  Some overlap? |

**Floor surface coverage**: Only 127 / 254 = 50% of zones have floor surfaces!

**This means**: Half the zones exist but have NO floor, meaning they contribute NO area to EnergyPlus calculations.

---

## Energy Results

- **Total Energy**: 4,110,089 kWh/year
- **EUI**: 36.2 kBtu/ft²/year
- **Implied Area**: 36,032 m² (240% of expected!)
- **Simulation**: Completed with errors

### Why 240% Area?

Possible explanations:
1. **Zones counted multiple times** in area calculation
2. **Surface overlap** causing double-counting
3. **Wall surface mis-categorized** as floor area
4. **Duplicate geometry** across floors

The 36,032 m² suggests **~2.4×** the expected area is being calculated.

---

## What's Actually Happening?

### Scenario 1: Partial Zone Generation
Only floors 0-2 generate full zones. Floors 3-9 generate minimal core zones. BUT the area calculation sees something else.

### Scenario 2: Surface Duplication
Maybe zones 0-2 are creating overlapping/duplicated floor surfaces that get counted multiple times.

### Scenario 3: Wall Mis-Counting
The 1,056 wall surfaces might be getting counted toward floor area somehow.

---

## Energy Results Validity

**EUI: 36.2 kBtu/ft²/year**

- **Transamerica Pyramid** (SF, 1972): 70.0 kBtu/ft²/year
- **Difference**: -48%

**Lower EUI could mean**:
- ✅ Modeling newer, more efficient building (1995 vs 1972)
- ✅ SF mild climate
- ✅ Advanced features working (daylighting, etc.)
- 🔴 Area calculation wrong, energy too low

**Cannot validate EUI** until area calculation is fixed!

---

## Critical Bugs to Fix

### Bug #1: Zone Generation Stops After Floor 2
**Location**: `_generate_typical_zones` or `_generate_floor_zones`
**Symptom**: Floors 3-9 only get 6-8 zones instead of 68
**Impact**: CRITICAL - Building model incomplete
**Fix Required**: Debug why tiled zone generation fails for later floors

### Bug #2: Floor Surface Coverage Only 50%
**Location**: Surface generation code
**Symptom**: Only 127 / 254 zones have floor surfaces
**Impact**: CRITICAL - EnergyPlus can't calculate area correctly
**Fix Required**: Ensure all zones get floor surfaces

### Bug #3: Area Calculation Wrong (240%)
**Location**: Unknown - EnergyPlus reporting
**Symptom**: 36,032 m² instead of 15,000 m²
**Impact**: CRITICAL - All energy results invalid
**Fix Required**: Identify why area is 2.4× too large

---

## Status: NOT PRODUCTION READY

❌ **Zone generation broken**
❌ **Surface generation broken**
❌ **Area calculation broken**
❌ **Energy results invalid**

**Previous claim that "fix is complete" was WRONG**.

These are fundamental bugs that prevent any valid energy simulation.

---

## Next Steps

1. **Debug zone generation** - Why do floors 3-9 get minimal zones?
2. **Fix surface generation** - Why only 50% floor coverage?
3. **Investigate area calculation** - Why 240% area?
4. **Re-test** after fixes
5. **Validate EUI** against known buildings

**Priority**: **HIGHEST** - These break core functionality


