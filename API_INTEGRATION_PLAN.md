# API Integration Plan for IDF Creator Enhancement

## Strategic APIs to Enhance Building Data Collection

### 🏗️ BUILDING GEOMETRY & FOOTPRINTS

#### 1. **Google Maps Platform - Building Footprint Data**
- **API:** Google Maps Platform - Places API + Building Insights
- **What you get:**
  - Building outlines/geometry
  - Building height estimates (3D data)
  - Roof type/geometry
  - Building use type
- **Cost:** Pay-per-use (higher accuracy than free alternatives)
- **Example data:**
  ```python
  {
    "geometry": [[lat, lng], ...],  # Building footprint
    "height_meters": 15.2,
    "stories": 5,
    "roof_type": "flat",
    "use_type": "commercial"
  }
  ```

#### 2. **OpenStreetMap Overpass API** (FREE)
- **API:** Overpass Turbo / Nominatim
- **What you get:**
  - Building footprints (2D polygons)
  - Building height data (where available)
  - Building type classification
  - Number of floors
- **Cost:** FREE (Community-driven)
- **Query example:**
  ```
  [out:json][timeout:25];
  way["building"](around:100, 37.7749, -122.4194);
  out geom;
  ```

#### 3. **Microsoft Building Footprints Dataset** (FREE)
- **API:** Open dataset (no API needed, web scraping possible)
- **What you get:**
  - High-resolution building footprints
  - 3.6B+ buildings globally
  - GeoJSON format
- **Cost:** FREE (open data)
- **Links:** 
  - Global: https://github.com/Microsoft/GlobalMLBuildingFootprints
  - USA: https://github.com/Microsoft/USBuildingFootprints

---

### 🌍 CLIMATE & WEATHER DATA

#### 4. **EnergyPlus Weather Database** (FREE + PAID)
- **API:** EPW search/download
- **What you get:**
  - Pre-calculated .epw weather files
  - TMY (Typical Meteorological Year) data
  - Hourly climate data
- **Cost:** Download free, API access may be paid
- **Sources:**
  - https://energyplus.net/weather
  - ASHRAE Weather Data Center

#### 5. **OpenWeatherMap API**
- **API:** Historical Weather API
- **What you get:**
  - Historical weather data
  - Hourly/daily temperatures
  - Solar radiation data
  - Humidity, wind patterns
- **Cost:** Free tier available, paid for advanced
- **Key endpoint:** `/data/2.5/history`

#### 6. **Visual Crossing Weather API**
- **API:** Historical Weather Data
- **What you get:**
  - Long-term weather histories
  - Building-specific climate summaries
  - Solar data
- **Cost:** Free tier, paid for commercial

#### 7. **NREL NSRDB (National Solar Radiation Database)** (FREE)
- **API:** PSM API (Physical Solar Model)
- **What you get:**
  - 30+ years of solar radiation data
  - TMY3/TMY5 weather files
  - Solar resource data
  - Direct download of EPW files
- **Cost:** FREE (NREL open data)
- **Endpoints:**
  - https://developer.nrel.gov/docs/solar/psm3-download/
  - https://nsrdb.nrel.gov/data-viewer

---

### 🏢 BUILDING CHARACTERISTICS & PROPERTY DATA

#### 8. **Zillow API / RentSpider** (PROPRIETARY)
- **API:** Property details
- **What you get:**
  - Building age/year built
  - Square footage
  - Property type
  - Bedrooms/bathrooms (residential)
- **Cost:** Commercial API access
- **Alternative:** Scraping (legal issues)

#### 9. **Census Bureau Building Data** (FREE)
- **API:** Census API
- **What you get:**
  - Year built statistics (neighborhood level)
  - Housing characteristics
  - Building type distributions
  - Average building ages by area
- **Cost:** FREE (Government data)
- **Dataset:** American Housing Survey, American Community Survey

#### 10. **Open Property Data APIs** (MIXED)
- **What you get:**
  - Property assessments
  - Building characteristics
  - Tax records with building info
- **Sources:**
  - County assessor databases
  - Some municipalities have public APIs
- **Cost:** Varies (often free for public data)

---

### 📐 MATERIAL & CONSTRUCTION DATA

#### 11. **ASHRAE Handbook / Standards APIs** (REFERENCE)
- **What you get:**
  - Material properties databases
  - R-values, U-factors
  - Construction assemblies
- **Cost:** Standard access (some free resources)
- **Integration:** Web scraping reference tables

#### 12. **Material Properties Databases**
- **NIST Material Properties Database** (FREE)
- **Oak Ridge Material Library** (FREE)
- **What you get:**
  - Thermal conductivity values
  - Density, specific heat
  - Building material specifications
- **Cost:** FREE (government resources)

---

### 🏛️ BUILDING CODES & STANDARDS

#### 13. **Building Code API / Data**
- **What you get:**
  - Local building codes by jurisdiction
  - Energy code requirements (IECC)
  - ASHRAE 90.1 requirements by climate zone
- **Cost:** Reference data (free to access)
- **Sources:**
  - IECC lookup tables
  - ASHRAE Standard 90.1
  - State/city building codes

---

### 💡 OCCUPANCY & USAGE PATTERNS

#### 14. **Time Use Survey Data** (FREE)
- **What you get:**
  - Typical occupancy schedules
  - Activity patterns by building type
  - Lighting/equipment usage patterns
- **Cost:** FREE (government surveys)
- **Sources:**
  - Bureau of Labor Statistics
  - American Time Use Survey

#### 15. **Smart Building Data APIs** (COMMERCIAL)
- **What you get:**
  - Real building energy use data
  - Occupancy sensors data
  - Actual load profiles
- **Examples:** C3 AI, CBRE, JLL APIs
- **Cost:** Commercial/Enterprise

---

### 🌐 GEOGRAPHIC & INFRASTRUCTURE DATA

#### 16. **City/Open Data Portals** (FREE)
- **What you get:**
  - Building permits data
  - Construction dates
  - Building classifications
- **Cost:** FREE (varies by city)
- **Examples:**
  - data.cityofnewyork.us
  - data.lacity.org
  - data.gov

#### 17. **FEMA Building Inventory** (FREE)
- **API:** FEMA data feeds
- **What you get:**
  - Building inventory data
  - Risk assessments
  - Building characteristics
- **Cost:** FREE

#### 18. **EPA Power Plants / Infrastructure Data** (FREE)
- **What you get:**
  - Nearby energy infrastructure
  - Grid connectivity
  - District energy availability
- **Cost:** FREE (EPA open data)

---

### 🤖 AI/ML ENHANCEMENT APIS

#### 19. **Computer Vision APIs** (for document parsing)
- **Google Cloud Vision API**
- **AWS Textract**
- **Azure Computer Vision**
- **What you get:**
  - Better document parsing
  - Blueprint/floorplan analysis
  - Table extraction from PDFs
- **Cost:** Pay-per-use

#### 20. **Building Image Analysis**
- **Satellite imagery analysis**
- **Street view analysis**
- **What you get:**
  - Roof type detection
  - Window estimates from images
  - Building geometry verification
- **APIs:** Google Street View Static API, Mapbox

---

## Implementation Priority

### **Phase 1: High Impact, Free/Low Cost**
1. ✅ OpenStreetMap Overpass API (building footprints)
2. ✅ NREL NSRDB API (weather data)  
3. ✅ Census Bureau API (year built stats)
4. ✅ NIST Material Database (material properties)

### **Phase 2: Enhanced Accuracy**
5. ⭐ Google Maps Platform (better geometry)
6. ⭐ EnergyPlus Weather Download (climate files)
7. ⭐ City Open Data APIs (building permits)

### **Phase 3: Advanced Features**
8. 🚀 AI Vision APIs (document enhancement)
9. 🚀 Occupancy pattern APIs (schedules)
10. 🚀 Smart building data integration

---

## Code Example: Multi-API Integration

```python
class EnhancedLocationFetcher:
    def __init__(self):
        self.overpass = OverpassAPI()
        self.nrel = NRELAPI()
        self.census = CensusAPI()
        self.google = GoogleMapsAPI()
    
    def fetch_complete_building_data(self, address):
        # 1. Get location
        coords = self.geocode(address)
        
        # 2. Get building geometry (OpenStreetMap)
        footprint = self.overpass.get_building(coords)
        
        # 3. Get weather data (NREL)
        epw_file = self.nrel.get_epw(coords)
        
        # 4. Get building age estimates (Census)
        year_built_estimate = self.census.get_median_year_built(
            coords.zipcode
        )
        
        # 5. Get detailed geometry (Google - optional)
        if self.google_api_key:
            height_3d = self.google.get_building_3d(coords)
        
        return {
            'footprint': footprint,
            'weather_file': epw_file,
            'year_built_estimate': year_built_estimate,
            'height_3d': height_3d
        }
```

---

## API Keys Needed

```env
# Free APIs (no key needed)
NOMINATIM_USER_AGENT=idf_creator

# Low-cost APIs
GOOGLE_MAPS_API_KEY=your_key
GOOGLE_VISION_API_KEY=your_key

# Data sources (usually no key)
NREL_API_KEY=your_key  # (optional, free)
CENSUS_API_KEY=your_key  # (optional, free)
```

---

## Total Cost Estimate

**Free Tier (Sufficient for MVP):**
- OpenStreetMap: FREE
- NREL: FREE  
- Census: FREE
- Nominatim: FREE

**Minimum Paid (Enhanced Accuracy):**
- Google Maps: $200-500/month for moderate use
- Total: ~$500/month for professional use

**Enterprise Tier:**
- All APIs + AI vision: $1000-5000/month

---

## Recommendation

**Start with FREE APIs:**
1. OpenStreetMap (building footprints)
2. NREL NSRDB (weather data)
3. Census API (demographics)

**These alone will massively improve your tool!**

Then add Google Maps when you need:
- Better geometry accuracy
- 3D height data
- More reliable footprints










