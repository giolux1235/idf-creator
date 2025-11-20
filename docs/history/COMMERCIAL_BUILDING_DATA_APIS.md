# Commercial Building Data APIs for IDF Enhancement

## Overview

While there's no perfect "Zillow for commercial buildings" with free public access, there are several APIs that can provide building characteristics useful for IDF generation. Here's what's available and how to integrate them.

---

## 🏢 Commercial Real Estate APIs

### 1. **CompStak API** (Best for Commercial Building Data)
**Website**: https://compstak.com/data-api

**What It Provides**:
- Property details (building class, year built, square footage)
- Lease comparables (rent, terms, tenant info)
- Building characteristics (stories, lot size, parking)
- Submarket analysis
- Over 60,000 monthly comps nationwide

**Data Useful for IDF**:
- Building age → construction era → material quality assumptions
- Square footage → validation of calculated area
- Building class → better building type classification
- Stories → confirmation of floor count

**Access**: Paid API (contact for pricing)
**Authentication**: API key based

---

### 2. **ATTOM Data Solutions**
**Website**: https://rapidapi.com/attom-data-solutions

**What It Provides**:
- Tax records → building characteristics
- Assessor data → square footage, property type
- Building permits → renovation history, HVAC upgrades
- Over 155 million properties (residential + commercial)

**Data Useful for IDF**:
- Assessor data → floor area validation
- Permits → recent HVAC upgrades
- Property classification → building type
- Year built → construction standards to apply

**Access**: Paid API via RapidAPI
**Authentication**: RapidAPI subscription

---

### 3. **PropertyRadar API**
**Website**: https://developers.propertyradar.com

**What It Provides**:
- Commercial property classifications
- Property attributes (age, size, type)
- Ownership records
- Market analysis

**Data Useful for IDF**:
- Building type classification
- Size validation
- Age for construction standards

**Access**: Paid API
**Authentication**: API key

---

### 4. **Cotality Commercial API**
**Website**: https://www.cotality.com/au/products/commercial-api

**What It Provides**:
- Current commercial property data
- Market trends
- Comparable sales
- Property valuations

**Data Useful for IDF**:
- Property characteristics
- Size data
- Building type classifications

**Access**: Paid API
**Authentication**: OAuth 2.0

---

## 🏛️ Government & Public Data Sources

### 1. **EPA ENERGY STAR Portfolio Manager** (Free)
**Website**: https://www.energystar.gov/buildings/benchmark

**What It Provides**:
- Energy performance benchmarks for commercial buildings
- Site energy use intensity (EUI)
- Comparative performance data
- Building characteristic data (optional disclosure)

**Data Useful for IDF**:
- Energy benchmarks → validation target for simulation
- EUI by building type → expected energy performance
- Climate-specific benchmarks → location-specific expectations

**Access**: Free, public data
**API**: Limited API access (data sharing only)

**Integration**: Web scraping or manual data entry (no public API yet)

---

### 2. **DOE Commercial Buildings Energy Consumption Survey (CBECS)**
**Website**: https://www.eia.gov/consumption/commercial

**What It Provides**:
- National building energy consumption statistics
- Building characteristics database
- End-use consumption patterns
- Survey data every 5 years

**Data Useful for IDF**:
- Typical EUI by building type
- Average HVAC system types
- Typical operating hours
- Lighting power densities

**Access**: Free, public data
**API**: No API, downloadable CSV/Excel files

**Integration**: Download and parse CSV, create lookup tables

---

### 3. **Open Data Portals** (City/State Level)
**Examples**:
- NYC Open Data: https://data.cityofnewyork.us
- San Francisco Open Data: https://datasf.org
- Chicago Open Data: https://data.cityofchicago.org

**What They Provide**:
- Building energy benchmarking (NYC, SF required disclosure)
- Building characteristics (age, size, type)
- Permit data (HVAC installations, renovations)
- Building inspection records

**Data Useful for IDF**:
- Energy benchmarking → validation targets
- Building age → construction standards
- HVAC permits → actual system information
- Size and type → building characteristics

**Access**: Free, public data
**API**: RESTful APIs typically available

**Best Examples**:
- **NYC Energy Benchmarking**: 26,000+ buildings with EUI data
- **SF Building Energy Performance**: Detailed building data

---

## 🔌 Integration Strategies

### Strategy 1: Free + Open Data (Recommended for MVP)

**Use**:
1. OpenStreetMap (already integrated ✅)
2. City open data portals (NYC, SF, Chicago benchmarks)
3. CBECS survey data (static lookups)

**Implementation**:
```python
# Example: NYC Energy Benchmarking
def fetch_nyc_building_data(address):
    # Query NYC Open Data API
    # Returns: EUI, building age, square footage
    pass

# Example: CBECS Lookup
def get_cbecs_eui(building_type, size_range):
    # Returns typical EUI from CBECS database
    pass
```

**Pros**:
- Free
- No authentication needed
- Good data for major cities

**Cons**:
- Limited to cities with open data
- May need multiple APIs
- Data quality varies

---

### Strategy 2: Paid API Integration

**Use**: CompStak or ATTOM API

**Implementation**:
```python
import requests

def fetch_compstak_data(address, api_key):
    url = "https://api.compstak.com/v2/properties/search"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"address": address}
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    return {
        'building_age': data.get('year_built'),
        'square_feet': data.get('total_sf'),
        'building_class': data.get('building_class'),
        'stories': data.get('stories'),
        'parking_spots': data.get('parking_spots')
    }

# Integrate into IDF generator
building_data = fetch_compstak_data(address, api_key)
idf_params.update({
    'building_age': building_data['building_age'],
    'total_area': building_data['square_feet']
})
```

**Pros**:
- Comprehensive data
- Nationwide coverage
- Real-time updates
- Commercial-grade accuracy

**Cons**:
- Cost ($100-1000+/month)
- API key management
- Rate limits

---

### Strategy 3: Hybrid Approach (Best Balance)

**Use**:
1. OSM + Open Data (free) for basic info
2. Paid API as enhancement layer (optional)
3. CBECS as fallback for typical values

**Implementation**:
```python
def get_building_data(address, location):
    # Try free sources first
    building_data = {}
    
    # 1. Try city open data (NYC, SF, Chicago)
    if location['city'] in ['New York', 'NYC']:
        building_data.update(fetch_nyc_benchmarking(address))
    
    # 2. Fallback to OSM (already have this)
    if not building_data.get('area'):
        building_data.update(get_osm_data(address))
    
    # 3. Apply CBECS defaults
    building_data.setdefault('eui', get_cbecs_eui(building_type))
    
    # 4. Optional: Enhance with paid API
    if USE_PAID_API and API_KEY:
        building_data.update(fetch_compstak_data(address))
    
    return building_data
```

---

## 📊 What Data Should We Pull?

### High Value Data (Impact IDF Quality)
1. **Building Age** → Construction standards (pre-2010 vs post-2010)
2. **Square Footage** → Validation of calculated area
3. **Actual EUI** → Validation target for simulation
4. **HVAC System Type** → Real system info (not template)
5. **Stories** → Floor count validation

### Medium Value Data
6. **Parking Spots** → Lighting load estimation
7. **Building Class** → Better classification
8. **Renovation Year** → Updated systems
9. **Typical Occupancy** → Real-world schedules

### Low Value Data (Nice to Have)
10. **Tenant Type** → Space use assumptions
11. **Operating Hours** → Schedule adjustments
12. **LEED Status** → Performance expectations

---

## 🛠️ Implementation Plan

### Phase 1: Enhance with Free Data
```python
# Add to src/enhanced_location_fetcher.py
class CityOpenDataFetcher:
    def fetch_nyc_benchmarking(self, address):
        # NYC energy benchmarking data
        pass
    
    def fetch_sf_building_data(self, address):
        # SF building performance
        pass
```

### Phase 2: Add CBECS Lookups
```python
# Create src/cbecs_lookup.py
class CBECSLookup:
    def get_eui_by_type(self, building_type, size):
        # Static lookup table from CBECS
        pass
```

### Phase 3: Optional Paid API Integration
```python
# Create src/commercial_data_fetcher.py
class CommercialDataFetcher:
    def fetch_compstak(self, address):
        # CompStak integration
        pass
```

---

## 💰 Cost Analysis

| Source | Cost | Coverage | Data Quality |
|--------|------|----------|--------------|
| OSM (current) | Free | Global | Medium |
| City Open Data | Free | Major cities only | High |
| CBECS | Free | National stats | Medium |
| CompStak API | $500-2000/mo | Major markets | Very High |
| ATTOM API | $200-1000/mo | National | High |

**Recommendation**: Start with free sources, add paid APIs if budget allows.

---

## 🎯 Next Steps

1. **Immediate**: Add NYC/SF open data integration (free, high quality)
2. **Near-term**: Implement CBECS lookup table (typical EUIs by building type)
3. **Future**: Add CompStak API integration (if budget permits)

Want me to implement any of these? I can start with the free city open data APIs!

