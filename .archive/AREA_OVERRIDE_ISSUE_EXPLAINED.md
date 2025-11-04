# Why Area Was So Small - Explained

**Problem**: When specifying `floor_area_per_story_m2`, the actual generated building area was much smaller than expected.

**Expected**: 1,500 m²/floor × 10 floors = 15,000 m²  
**Actual**: ~4,070 m² (27% of expected)

---

## Root Cause

### Issue #1: OSM Data Override

**Location**: `src/professional_idf_generator.py`, lines 467-486

```python
# Prefer real area from OSM if available
try:
    osm_area = building_info.get('osm_area_m2')
    if osm_area and float(osm_area) > 10:
        footprint_area = float(osm_area)  # ← OVERRIDE!
except Exception:
    pass
```

**What Happens**:
1. User specifies `floor_area_per_story_m2: 1500`
2. OSM returns area for "1 Market St" = 9,218 m² (single floor)
3. Code **prefers OSM area** over user specification
4. Result: OSM footprint (9,218 m²) used instead of calculated (15,000 m²)

---

### Issue #2: Zone Generation Efficiency

Even when OSM provides the footprint, **only partial zones are created**.

**Expected**: 9,218 m² × 10 floors = 92,180 m²  
**Actual EnergyPlus**: 4,070 m²

**Why**:
The zone generation creates small zones from the OSM polygon:
- OSM polygon (9,218 m²) passed directly
- Zone generation tries to fill it
- **Only** creates zones that fit the geometry
- Complex OSM polygons may not fill completely
- Result: ~44% of footprint actually used for zones

---

## The Flow

```
User Input:
  floor_area_per_story_m2: 1500
  stories: 10
  
↓

main.py estimate_missing_parameters() → FAILS (line 134-141)
  - Checks if 'floor_area' exists → NO
  - Falls back to OSM area × stories
  - OSM = 9,218 m² × 10 = 92,180 m² total

↓

professional_idf_generator.py _generate_complex_footprint() (line 467-486)
  - **Prefer OSM area** if available → YES
  - **IGNORE** user floor_area_per_story
  - Use OSM = 9,218 m² as single-floor footprint

↓

advanced_geometry_engine.py generate_zone_layout()
  - Create zones for OSM footprint
  - Only 44% of footprint becomes actual zones
  - Result: 4,070 m²

↓

EnergyPlus calculates energy based on:
  - Actual zone areas = 4,070 m²
  - NOT the specified 15,000 m²
```

---

## Fix Required

**Priority**: High - affects all simulations with real addresses

**Solution**: Add parameter to **ignore OSM area** when user specifies floor area

**Location**: `src/professional_idf_generator.py`, line 467

**Change needed**:
```python
# CURRENT (line 467-486):
footprint_area = None

# Prefer real area from OSM if available
try:
    osm_area = building_info.get('osm_area_m2')
    if osm_area and float(osm_area) > 10:
        footprint_area = float(osm_area)
except Exception:
    pass

# SHOULD BE:
footprint_area = None

# Only use OSM if user didn't specify floor_area
user_specified_area = estimated_params.get('floor_area')
if not user_specified_area:
    # Prefer real area from OSM if available
    try:
        osm_area = building_info.get('osm_area_m2')
        if osm_area and float(osm_area) > 10:
            footprint_area = float(osm_area)
    except Exception:
        pass
else:
    footprint_area = user_specified_area  # Use user specification
```

---

## Current Workaround

**Use a synthetic address** (no OSM data):
```python
creator.create_idf(
    address='123 Fake St, Chicago, IL',  # No real OSM data
    user_params={'floor_area_per_story_m2': 1500, 'stories': 10}
)
```

**OR** specify total area directly:
```python
user_params={
    'total_area': 15000,  # Direct specification
    'stories': 10
}
```

---

## Why This Matters

- **Energy results scale with area**: 4,070 m² vs 15,000 m² = **3.7× difference**
- **EUI calculation wrong**: Dividing by wrong area
- **Calibration fails**: Comparing wrong building sizes
- **Retrofit analysis off**: Wrong baseline

This explains why some simulations show surprisingly low energy use - **they're modeling smaller buildings than specified!**


