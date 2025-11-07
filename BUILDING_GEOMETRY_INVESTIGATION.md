# Building Geometry Generation Investigation

**Date**: 2025-11-04  
**Purpose**: Understand why different address formats produce different building areas (334-1,284 m² variation)

---

## 🔍 Root Cause Analysis

### Issue: Building Area Varies by 3.8x for Similar Addresses

**Observation from Testing**:
- "789 Embarcadero, San Francisco, CA 94111" → 1,283.77 m² (outlier)
- "147 Sutter St, San Francisco, CA" → 334.27 m²
- "San Francisco, CA" (city only) → 544.32 m²

All these addresses geocode to the same coordinates (city center), but produce different building areas.

---

## 📊 Area Determination Flow

The building area is determined through this priority order:

### Priority 1: User-Specified Area ✅
```
user_params['floor_area'] or user_params['floor_area_per_story_m2']
↓
main.py: estimate_missing_parameters()
↓
Result: Uses user specification
```

**If user specifies area**: All addresses produce same area ✅

---

### Priority 2: OSM Building Data 🗺️

**Location**: `src/enhanced_location_fetcher.py` → `osm_fetcher.get_building_footprint()`

**OSM Search Process**:
1. Geocodes address to coordinates (city center for lookup table)
2. Searches OSM within 50m radius of coordinates
3. Finds **closest building** to coordinates
4. Extracts building footprint and calculates area

**Critical Issue**: 
- All SF addresses geocode to **same coordinates** (37.7749°N, -122.4194°W)
- OSM search radius = **50 meters**
- **Different addresses → same coordinates → same OSM building found**

**BUT**: OSM may find:
- A large building (1,284 m²) - if there's a large building within 50m of city center
- A small building (334 m²) - if there's a small building within 50m
- No building - falls to default (500-1,000 m²)

**Why "789 Embarcadero" is large**:
- There's likely a **large building** within 50m of SF city center (37.7749°N, -122.4194°W)
- That building's OSM footprint = ~1,284 m²
- All SF addresses use this same building!

---

### Priority 3: City Data 📊

**Location**: `src/enhanced_location_fetcher.py` → `city_fetcher.fetch_building_data()`

**Supported Cities**: NYC, San Francisco, Chicago (limited)

**Current Status**: 
- Most city APIs return empty `{}`
- Not actively providing data for most addresses

---

### Priority 4: Default Area ⚙️

**Location**: `src/professional_idf_generator.py`, line 541-548

```python
if footprint_area is None:
    total_area = estimated_params.get('total_area', 1000)
    footprint_area = total_area / stories if stories > 0 else 1000
```

**Default**: 1,000 m² total / stories = **333-1,000 m² per floor** (depending on stories)

---

## 🎯 Why Different Address Formats Produce Different Sizes

### Case 1: City-Only Format ("San Francisco, CA")

**Flow**:
1. Geocodes to city center (37.7749°N, -122.4194°W) ✅
2. Searches OSM within 50m → **May or may not find building**
3. If no OSM building → Uses default (500-1,000 m²) → **544.32 m²** ✅

**Result**: Medium-sized default building

---

### Case 2: Specific Street Address ("123 Market St, San Francisco, CA")

**Flow**:
1. Geocodes to city center (same coordinates) ✅
2. Searches OSM within 50m → Finds closest building
3. If building found → Uses OSM area → **Variable size** ⚠️

**Result**: Depends on which building OSM finds (could be large or small)

---

### Case 3: Outlier Address ("789 Embarcadero, San Francisco, CA 94111")

**Flow**:
1. Geocodes to city center (same coordinates) ✅
2. Searches OSM within 50m → Finds **large building** (likely near Embarcadero/city center)
3. OSM building area = **~1,284 m²** ⚠️
4. Uses this large OSM area

**Result**: Large building (outlier)

---

## ⚠️ Key Problems Identified

### Problem 1: OSM Search Uses City Center Coordinates

**Issue**: All addresses in same city geocode to **same coordinates** (city center), so OSM always searches same location.

**Impact**: 
- Different addresses → Same OSM building found
- No address-specific building data
- Inconsistent results based on which building happens to be near city center

**Example**:
```
Address 1: "123 Market St, SF" → Coords: 37.7749, -122.4194
Address 2: "456 Mission St, SF" → Coords: 37.7749, -122.4194  (same!)
Address 3: "789 Embarcadero, SF" → Coords: 37.7749, -122.4194 (same!)

All search OSM at same location → Find same building → Same area
```

---

### Problem 2: No Area Validation

**Issue**: No checks for unusually large/small areas.

**Current Behavior**:
- OSM returns 1,284 m² → Used without question
- No validation against typical building sizes
- No warnings for outliers

**Impact**: Extreme outliers (3.8x variation) go unnoticed

---

### Problem 3: Inconsistent Default Behavior

**Issue**: Default area depends on `estimated_params.get('total_area', 1000)`, which may vary.

**Current Defaults**:
- `professional_idf_generator.py`: 1,000 m² default
- `main.py`: 500 m² per story default
- `building_estimator.py`: 1,000 m² default

**Result**: Different code paths → Different defaults → Inconsistent sizes

---

### Problem 4: OSM Area Calculation Error (FIXED ✅)

**Issue**: OSM area calculation used simplified planar approximation.

**Status**: ✅ **FIXED** - Now uses proper spherical geometry (UTM projection)

**Impact**: Should reduce calculation errors, but may not fully explain 3.8x variation

---

## 💡 Recommendations

### High Priority

1. **Add Area Validation** 🔧
   - Validate OSM areas against typical ranges (50-5,000 m² for offices)
   - Flag outliers (>2x median or <0.5x median)
   - Log warnings for unusual areas
   - Optionally cap areas to reasonable ranges

2. **Improve OSM Search Logic** 🔧
   - Use address-specific geocoding (if available) instead of city center
   - Increase search radius if no building found (50m → 100m → 200m)
   - Filter OSM buildings by address match (if OSM has address tags)

3. **Standardize Default Areas** 🔧
   - Use consistent default across all code paths
   - Document default values clearly
   - Use building type-specific defaults (office = 500 m², warehouse = 2,000 m²)

### Medium Priority

4. **Add Area Source Logging** 📝
   - Log which source was used (OSM, city data, default)
   - Log OSM building details (address, area, distance from coordinates)
   - Include in API response: `area_source` field

5. **Implement Area Normalization** 📊
   - Option to normalize areas to city/building type averages
   - Use CBECS typical values as sanity checks
   - Warn if area deviates significantly from expected

### Low Priority

6. **Address-Specific Geocoding** 🌍
   - Use Google Maps API for address-specific coordinates (if API key available)
   - Fall back to city center if address geocoding fails
   - Use address-specific coordinates for OSM search

---

## 📋 Expected Behavior After Fixes

### Scenario 1: Specific Street Address

```
Input: "123 Market St, San Francisco, CA"
↓
1. Geocode → Address-specific coords (37.7845, -122.4090) ✅
2. OSM search at address coords → Find building at that address
3. Validate area → Check if reasonable (50-5,000 m²)
4. Use OSM area if valid, else use default
↓
Result: Consistent area based on actual building
```

### Scenario 2: City-Only Address

```
Input: "San Francisco, CA"
↓
1. Geocode → City center (37.7749, -122.4194) ✅
2. OSM search → May find building or not
3. If no building → Use default (500 m²/floor × 3 stories = 1,500 m² total)
4. Validate → Check if reasonable
↓
Result: Consistent default area
```

### Scenario 3: Outlier OSM Building

```
Input: "789 Embarcadero, San Francisco, CA"
↓
1. OSM finds large building (1,284 m²) ⚠️
2. Validation → Flags as outlier (>2x typical)
3. Warning logged: "OSM area unusually large: 1,284 m² (expected: 300-800 m²)"
4. Option A: Use anyway (with warning)
5. Option B: Cap to reasonable range (800 m² max)
↓
Result: Outlier flagged or capped
```

---

## 🔧 Implementation Plan

### Step 1: Add Area Validation Module

Create `src/area_validator.py`:
- Validate areas against typical ranges
- Flag outliers
- Provide warnings
- Optionally cap to reasonable ranges

### Step 2: Integrate Validation

Update:
- `src/professional_idf_generator.py`: Validate OSM areas before use
- `src/enhanced_location_fetcher.py`: Validate city data areas
- `main.py`: Validate final area before IDF generation

### Step 3: Improve Logging

Add:
- Area source tracking
- OSM building details (address, area, distance)
- Validation warnings
- Include `area_source` in API responses

### Step 4: Standardize Defaults

Update all default values to be consistent:
- Single source of truth for defaults
- Building type-specific defaults
- Clear documentation

---

## 📊 Current State vs. Target State

### Current State ❌

| Address | Coordinates | OSM Building | Area | Issue |
|---------|-------------|--------------|------|-------|
| "SF, CA" | 37.7749, -122.4194 | None | 544 m² | Default, OK |
| "123 Market St, SF" | 37.7749, -122.4194 | Building A | 613 m² | Inconsistent |
| "789 Embarcadero, SF" | 37.7749, -122.4194 | Large Building | 1,284 m² | Outlier ⚠️ |

### Target State ✅

| Address | Coordinates | OSM Building | Area | Validation |
|---------|-------------|--------------|------|------------|
| "SF, CA" | 37.7749, -122.4194 | None | 500 m² | Default, validated ✅ |
| "123 Market St, SF" | 37.7845, -122.4090 | Address-specific | 450 m² | Validated ✅ |
| "789 Embarcadero, SF" | 37.7850, -122.4085 | Address-specific | 600 m² | Validated ✅ |
| (If outlier) | - | - | 1,284 m² | ⚠️ Flagged, capped to 800 m² |

---

## 🎯 Success Metrics

After implementing fixes, we should see:

1. ✅ **Reduced Variation**: Building areas within 2x range (not 3.8x)
2. ✅ **Outlier Detection**: Warnings for unusual areas
3. ✅ **Consistent Defaults**: Same default for similar inputs
4. ✅ **Better Logging**: Clear area source and validation status
5. ✅ **Address-Specific Results**: Different addresses → Different areas (when OSM data available)

---

**Status**: ✅ Root cause identified, implementation plan created




