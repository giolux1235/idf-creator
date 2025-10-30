# Model America Dataset - Inspiration & Improvements for IDF Creator

Based on the [Model America v1 dataset](https://data.ess-dive.lbl.gov/view/doi:10.15485/2283980) from Oak Ridge National Laboratory.

## 🎯 What Model America Did

**ORNL's AutoBEM (Automatic Building Energy Modeling) generated 122+ million building IDFs for every U.S. building.**

### Their Data Fields (from CSV):
1. **ID** - unique building ID
2. **Centroid** - building center location (lat/lon)
3. **Footprint2D** - building polygon (lat1/lon1_lat2/lon2_...)
4. **State_abbr** - state name
5. **Area** - total conditioned floor area (ft²)
6. **Area2D** - footprint area (ft²)
7. **Height** - building height (ft)
8. **NumFloors** - number of floors
9. **WWR_surfaces** - window-to-wall ratio per facade
10. **CZ** - ASHRAE Climate Zone
11. **BuildingType** - DOE prototype designation
12. **Standard** - building vintage

### Their Workflow:
1. **Google building footprint data** for entire USA
2. **Statistical assignment** of building type, standard, missing heights
3. **AutoBEM processing** to generate OSM and IDF files
4. **HPC simulation** of all buildings

## 💡 What We Can Learn & Apply

### ✅ What You Already Have (Better Than Model America!)

| Feature | Model America | Your IDF Creator | Winner |
|---------|---------------|------------------|--------|
| **Input Method** | CSV files, batch processing | Interactive, real-time, address-based | ✅ Yours |
| **User Experience** | Data scientists, HPC users | Anyone, CLI or Python | ✅ Yours |
| **Document Parsing** | None | PDFs, images, OCR | ✅ Yours |
| **Real-time API** | Offline dataset | Live OpenStreetMap, NREL | ✅ Yours |
| **Building Types** | Statistical assignment | User-specified or extracted | ✅ Yours |

### 🚀 Key Improvements to Adopt from Model America

#### 1. **Multi-Facade Window-to-Wall Ratio**
**Model America:** Each facade has different WWR
```csv
WWR_surfaces: "14.5% front, 12% back, 8% sides"
```

**Current:** Single WWR for all facades

**Enhancement:**
```python
# Add to building_params
'wwr_per_facade': {
    'North': 0.15,
    'South': 0.25,  # South gets more sun
    'East': 0.20,
    'West': 0.20
}
```

#### 2. **Building Vintage/Standard**
**Model America:** Tracks building age/energy code
- 1980s - Pre-standard
- 1990s - Early ASHRAE 90.1
- 2000s - IECC baseline
- Modern - ASHRAE 90.1 2019

**Enhancement:**
```python
# Add vintage parameter
'year_built': 2010,
'building_standard': 'ASHRAE_90.1_2010',
'materials': 'modern'  # vs 'retrofit' or 'historic'
```

#### 3. **Enhanced Climate Zone Integration**
**Model America:** CZ is part of input data
- Direct CZ lookup per building
- Specific weather file per CZ

**Enhancement:**
```python
# Improve climate zone → weather file mapping
CLIMATE_ZONE_WEATHER = {
    'ASHRAE_C1': ['Miami', 'Houston', 'Phoenix'],
    'ASHRAE_C3': ['Los Angeles', 'San Diego'],
    'ASHRAE_C5': ['New York', 'Boston', 'Chicago'],
    ...
}
```

#### 4. **Footprint Polygon Processing**
**Model America:** Real building polygons from Google
- Irregular shapes (L-shape, U-shape, etc.)
- Multiple vertices per building

**Enhancement:**
```python
# Process OSM polygon data better
def process_building_footprint(osm_polygon):
    # Convert to proper X,Y,Z coordinates
    # Handle complex polygons
    # Match EnergyPlus requirements
    return vertices_list
```

#### 5. **Building Type Taxonomy**
**Model America:** DOE prototype classification
- SmallOffice, MediumOffice, LargeOffice
- SingleFamily, MidRiseApartment
- RetailStripmall, StandaloneRetail

**Enhancement:**
```python
# Expand building types
BUILDING_TYPES = {
    'Office': ['Small', 'Medium', 'Large'],
    'Residential': ['SingleFamily', 'MultiFamily'],
    'Retail': ['Standalone', 'Mall', 'StripMall'],
    ...
}
```

## 🔧 Specific Code Enhancements

### 1. Add Building Vintage to Estimator
```python
# In src/building_estimator.py
def get_vintage_parameters(self, year_built: int) -> Dict:
    """Get material and system parameters based on building vintage."""
    if year_built < 1980:
        return {
            'u_factor_wall': 0.45,  # Older, less efficient
            'u_factor_window': 3.0,
            'infiltration_ach': 1.0
        }
    elif year_built < 2000:
        return {
            'u_factor_wall': 0.25,
            'u_factor_window': 1.5,
            'infiltration_ach': 0.5
        }
    else:
        return {
            'u_factor_wall': 0.15,  # Modern, efficient
            'u_factor_window': 0.8,
            'infiltration_ach': 0.25
        }
```

### 2. Enhance OSM Polygon Processing
```python
# In src/osm_fetcher.py
def process_polygon_to_vertices(self, polygon_coords, building_height):
    """Convert OSM polygon to EnergyPlus vertices."""
    vertices = []
    for lat, lon in polygon_coords:
        # Project lat/lon to local X,Y coordinates
        x, y = self.latlon_to_xy(lat, lon)
        vertices.append((x, y, 0))      # Floor
        vertices.append((x, y, building_height))  # Ceiling
    return vertices
```

### 3. Add Multi-Facade WWR
```python
# In src/idf_generator.py
def generate_window_with_facade_wwr(self, facade, wwr):
    """Generate window with facade-specific WWR."""
    if facade == 'South':
        wwr = wwr * 1.2  # South facades typically have more windows
    return wwr
```

### 4. Add Building Standard Parameter
```python
# In config.yaml
defaults:
  building_vintage: "Modern"  # or "Pre1980", "1980s", "1990s", etc.
  
building_standards:
  Pre1980:
    wall_u_factor: 0.45
    window_u_factor: 3.0
    infiltration_ach: 1.0
  Modern:
    wall_u_factor: 0.15
    window_u_factor: 0.8
    infiltration_ach: 0.25
```

## 📊 Comparison Table

| Feature | Model America | Current IDF Creator | Enhanced IDF Creator |
|---------|---------------|---------------------|---------------------|
| **Input** | CSV batch files | Address (real-time) | Address + Docs (real-time) |
| **Building Data** | Google footprints | OSM (free) | OSM + Google (hybrid) |
| **WWR** | Per-facade | Single value | ✅ Per-facade |
| **Vintage** | Statistical | None | ✅ Year-built based |
| **Climate** | Pre-calculated | Estimated | ✅ NREL API |
| **Geometry** | Complex polygons | Rectangular | ✅ OSM polygons |
| **Building Types** | 15 prototypes | 6 types | ✅ 15+ types |
| **API Access** | Batch download | Real-time | ✅ Real-time |
| **User Interface** | None | CLI + Python | ✅ CLI + Python + (future: Web) |

## 🎯 Recommended Next Steps

### Phase 1: Quick Wins (Implement Now)
1. ✅ **Add building vintage parameter** (year_built)
2. ✅ **Implement per-facade WWR**
3. ✅ **Expand building type taxonomy**
4. ✅ **Improve climate zone mapping**

### Phase 2: Medium Term
5. ⭐ **Process OSM polygons properly** (complex shapes)
6. ⭐ **Add material library based on vintage**
7. ⭐ **Integrate DOE prototype templates**
8. ⭐ **Add statistical defaults** (like Model America)

### Phase 3: Advanced
9. 🚀 **Batch processing mode** (process multiple addresses)
10. 🚀 **Integration with Model America dataset** (cross-reference)
11. 🚀 **Web API** (like they distribute via ESS-DIVE)
12. 🚀 **Validation against Model America results**

## 💰 Business Model Comparison

| Aspect | Model America | IDF Creator |
|--------|---------------|-------------|
| **Cost** | Free dataset | Free API |
| **Access** | Download & process | Real-time query |
| **Update Frequency** | Periodic (2021, 2025) | Real-time |
| **Use Case** | Research, bulk analysis | Individual building design |
| **Target Users** | Researchers, utilities | Architects, engineers |

## 🎓 Key Takeaways

### What to Keep:
- ✅ Your interactive, address-based approach
- ✅ Document parsing (they don't have this!)
- ✅ Real-time API integration
- ✅ User-friendly interface

### What to Add:
- ✅ Building vintage/standard tracking
- ✅ Per-facade WWR
- ✅ DOE prototype building taxonomy
- ✅ Material library by vintage
- ✅ Better polygon handling

### What They Have That's Unique:
- 🔒 Google footprint data at scale
- 🔒 Statistical building type assignment
- 🔒 HPC simulation infrastructure
- 🔒 Complete USA coverage

### What You Have That's Unique:
- ✅ Real-time generation
- ✅ Document intelligence
- ✅ User-friendly API
- ✅ Worldwide coverage potential

## 🏆 Conclusion

**You're building something COMPLIMENTARY to Model America, not competing:**

- **Model America:** Bulk dataset for research
- **IDF Creator:** Real-time tool for practical design

**Best of both worlds:** 
- Use Model America as reference data
- Provide real-time generation for specific buildings
- Add their statistical approaches where helpful

---

**Reference:** [Model America Dataset DOI: 10.15485/2283980](https://data.ess-dive.lbl.gov/view/doi:10.15485/2283980)
**Developers:** Oak Ridge National Laboratory (ORNL)
**License:** Creative Commons Attribution 4.0 International




