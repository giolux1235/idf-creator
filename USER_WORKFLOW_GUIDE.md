# IDF Creator - Complete User Workflow Guide

## 🎯 Overview

IDF Creator takes minimal input (primarily an **address**) and generates a complete EnergyPlus IDF file. Here's how it works from start to finish.

---

## 📥 User Input Options

### **Required Input**
- **Address**: Building street address (any location worldwide)
  - Example: `"233 S Wacker Dr, Chicago, IL 60606"`
  - Example: `"Empire State Building, New York, NY"`

### **Optional Inputs**
1. **Building Parameters** (via command-line flags or Python dict)
2. **Documents** (PDFs, images, floor plans)
3. **Natural Language Description** (via web interface or NLP CLI)

---

## 🔄 Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INPUT                                    │
│  Address + Optional Params/Documents                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: LOCATION PROCESSING                                    │
│  ──────────────────────────────────────────────────────────────│
│  • Geocode address → Get coordinates                           │
│  • Determine ASHRAE climate zone (e.g., C5, 3A)                │
│  • Fetch weather file from NREL                                 │
│  • Get building data from OpenStreetMap (OSM):                  │
│    - Footprint area (if available)                              │
│    - Building type                                              │
│    - Number of stories (if available)                           │
│    - Building geometry                                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: DOCUMENT PARSING (if provided)                         │
│  ──────────────────────────────────────────────────────────────│
│  • Extract text from PDFs                                       │
│  • Perform OCR on images                                        │
│  • Extract: floor area, stories, building type, year built, etc.│
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: PARAMETER MERGING & PRIORITY                           │
│  ──────────────────────────────────────────────────────────────│
│  Priority (highest to lowest):                                  │
│  1. User-provided parameters (--stories, --floor-area, etc.)    │
│  2. Document-extracted parameters                               │
│  3. OSM data (if available and user didn't specify)             │
│  4. Building type defaults (from config.yaml)                   │
│  5. Generic defaults                                            │
│                                                                  │
│  ⚠️  AREA FIX: User-specified floor_area_per_story_m2          │
│      ALWAYS overrides OSM data                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: PARAMETER ESTIMATION                                   │
│  ──────────────────────────────────────────────────────────────│
│  • Calculate missing dimensions from floor area                 │
│  • Estimate zone-level parameters:                              │
│    - People per zone (based on building type)                   │
│    - Lighting power density                                     │
│    - Equipment power density                                    │
│    - Infiltration rates                                         │
│  • Apply building age adjustments (if year_built provided)     │
│  • Apply LEED efficiency bonuses (if LEED level provided)      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: IDF GENERATION                                         │
│  ──────────────────────────────────────────────────────────────│
│  STANDARD MODE:                                                 │
│  • Simple geometry (rectangular zones)                          │
│  • Basic materials and constructions                            │
│  • Ideal loads HVAC system                                      │
│  • Standard schedules                                           │
│                                                                  │
│  PROFESSIONAL MODE (--professional):                            │
│  • Advanced geometry (complex footprints, OSM-based)            │
│  • Professional material library (climate-zone specific)        │
│  • Advanced HVAC systems (VAV, RTU, PTAC)                      │
│  • Multiple zone types (office, conference, lobby, etc.)        │
│  • Advanced controls and schedules                             │
│  • Daylighting and shading                                      │
│  • Infiltration and ventilation modeling                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT                                        │
│  Complete EnergyPlus IDF file ready for simulation              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Usage Methods

### **Method 1: Command Line (Simplest)**

#### Basic - Just Address
```bash
python main.py "Empire State Building, New York, NY"
```
**What happens:**
- Uses default building type (Office)
- Uses default stories (3)
- Uses default floor area (500 m²/floor × 3 = 1,500 m²)
- Uses OSM data if available for footprint geometry
- Generates standard IDF file

#### With Custom Parameters
```bash
python main.py "233 S Wacker Dr, Chicago, IL 60606" \
  --building-type Office \
  --stories 10 \
  --floor-area 15000 \
  --professional
```
**What happens:**
- Uses your specified: Office, 10 stories, 15,000 m² total
- **Even if OSM has different area, YOUR specification is used** ✅
- Generates professional-grade IDF with advanced features

#### With Per-Floor Area Specification
```bash
python main.py "600 Pine Street, Seattle, WA" \
  --building-type Office \
  --stories 8 \
  --professional
```
Then in Python code or config.yaml:
```python
user_params = {
    'floor_area_per_story_m2': 1200,  # 1,200 m² per floor
    'stories': 8
}
# Result: 9,600 m² total (1,200 × 8)
```

#### With Documents
```bash
python main.py "123 Main St, Boston, MA" \
  --documents floorplan.pdf building_specs.pdf \
  --professional
```
**What happens:**
- Parses documents to extract building info
- Merges with user parameters
- Uses document data if user didn't specify

---

### **Method 2: Python API**

```python
from main import IDFCreator

# Create instance
creator = IDFCreator(
    enhanced=True,        # Use multiple APIs for location
    professional=True     # Use advanced features
)

# Generate IDF
idf_path = creator.create_idf(
    address="233 S Wacker Dr, Chicago, IL 60606",
    user_params={
        'building_type': 'Office',
        'stories': 10,
        'floor_area_per_story_m2': 1500,  # Your specification
        'year_built': 1973,
        'window_to_wall_ratio': 0.4
    },
    output_path="my_building.idf"
)

print(f"IDF created: {idf_path}")
```

---

### **Method 3: Web Interface**

```bash
python web_interface.py
# Open browser to http://localhost:5000
```

**Web Interface Features:**
- Upload address and building description
- Upload documents (PDFs, images)
- Natural language parsing (optional LLM)
- Download generated IDF file

---

### **Method 4: Natural Language CLI**

```bash
python nlp_cli.py \
  "5-story office building with 50,000 sq ft, VAV HVAC, built in 2010" \
  --address "San Francisco, CA" \
  --professional
```

**What happens:**
- Parses natural language description
- Extracts: stories, area, building type, HVAC, year built
- Generates IDF with extracted parameters

---

## 📊 Parameter Priority & Defaults

### **Priority Order (Highest to Lowest)**

1. **User Parameters** (command-line flags or Python dict)
   ```python
   user_params = {
       'floor_area_per_story_m2': 1500,  # ← Highest priority
       'stories': 10
   }
   ```

2. **Document-Extracted Parameters**
   - From PDFs, images, floor plans
   - Extracted via OCR and text parsing

3. **OSM Data** (only if user didn't specify)
   - Building footprint area
   - Number of stories
   - Building type

4. **Config.yaml Defaults**
   ```yaml
   defaults:
     building_type: "Office"
     stories: 3
     floor_area_per_story_m2: 500
     window_to_wall_ratio: 0.4
   ```

5. **Hardcoded Defaults**
   - Fallback values if nothing else available

---

## 🎯 Area Calculation Flow

### **With User-Specified `floor_area_per_story_m2`**

```
User Input:
  floor_area_per_story_m2: 1500
  stories: 10
  ↓
main.py estimate_missing_parameters():
  Calculates: 1500 × 10 = 15,000 m² total
  ✅ Sets: floor_area = 15,000
  ✅ Sets: total_area = 15,000
  ↓
professional_idf_generator.py:
  Checks: user_floor_area = 15,000 ✓
  Uses: correct_total_area = 15,000
  Converts to per-floor: 15,000 / 10 = 1,500 m²/floor
  ✅ Generates zones with 1,500 m² per floor
  ↓
OSM Data (if available):
  OSM area: 14,090 m²
  ❌ IGNORED (user specification takes priority)
  ↓
Result: Building with 1,500 m²/floor × 10 floors = 15,000 m² total
```

### **Without User Specification (Uses OSM)**

```
User Input:
  address: "233 S Wacker Dr, Chicago, IL"
  (no floor_area_per_story_m2 specified)
  ↓
main.py:
  No user area specified
  ↓
Location Processing:
  OSM returns: 14,090 m² footprint
  ↓
professional_idf_generator.py:
  No user_floor_area found
  Uses OSM: footprint_area = 14,090 m²
  ✅ Generates zones with OSM footprint
  ↓
Result: Building with OSM footprint (14,090 m² per floor)
```

---

## 🔧 Available Parameters

### **Basic Parameters**
- `--building-type`: Office, Residential, Retail, Warehouse, School, Hospital
- `--stories`: Number of stories
- `--floor-area`: Total floor area (m²) - **OR** use `floor_area_per_story_m2` in Python
- `--window-ratio`: Window-to-wall ratio (0-1)

### **Advanced Parameters (Professional Mode)**
- `--year-built`: Year building was constructed (for efficiency adjustments)
- `--retrofit-year`: Year of major retrofit
- `--leed-level`: LEED certification (Certified, Silver, Gold, Platinum)
- `--wwr`, `--wwr-n`, `--wwr-s`, `--wwr-e`, `--wwr-w`: Window-to-wall ratios per facade
- `--equip-source`, `--equip-type`, `--equip-capacity`: HVAC equipment specifications
- `--cogeneration-capacity-kw`: CHP system capacity
- `--force-area`: Force target area by scaling footprint

---

## 📁 Output

### **Default Location**
```
artifacts/desktop_files/idf/[Building_Name].idf
```

### **Custom Location**
```bash
python main.py "Address" --output my_custom_path.idf
```

### **What's in the IDF File**
- ✅ Building geometry (zones, surfaces, windows)
- ✅ Materials and constructions (climate-zone specific)
- ✅ Internal loads (people, lighting, equipment)
- ✅ HVAC systems (VAV/RTU/PTAC in professional mode)
- ✅ Schedules (occupancy, lighting, equipment)
- ✅ Climate data (weather file reference)
- ✅ Simulation controls (run periods, output requests)

---

## 🎓 Example Scenarios

### **Scenario 1: Quick Test with Minimal Input**
```bash
python main.py "Empire State Building, New York, NY"
```
**Result**: Uses all defaults, OSM data if available

---

### **Scenario 2: Override OSM Area**
```bash
python main.py "Willis Tower, Chicago, IL" \
  --stories 10 \
  --professional
```
```python
# In Python code:
user_params = {
    'floor_area_per_story_m2': 1500  # Overrides OSM 14,090 m²
}
```
**Result**: Uses your 1,500 m²/floor instead of OSM 14,090 m² ✅

---

### **Scenario 3: Real Building with Known Parameters**
```bash
python main.py "350 5th Ave, New York, NY 10118" \
  --building-type Office \
  --stories 5 \
  --year-built 1931 \
  --retrofit-year 2011 \
  --leed-level Gold \
  --professional
```
```python
user_params = {
    'floor_area_per_story_m2': 2000  # 2,000 m²/floor
}
```
**Result**: 
- Uses your 2,000 m²/floor × 5 = 10,000 m² total
- Applies 1931 construction age adjustments
- Applies 2011 retrofit efficiency improvements
- Applies LEED Gold efficiency bonuses

---

## 🔍 Verification

After generation, check console output for:
```
✓ Using user-specified floor area: 1500 m²/floor × 10 floors = 15000 m²
✓ Using user-specified area: 1500 m²/floor (from 15000 m² total)
```

This confirms your specification was used (not OSM data).

---

## 📝 Summary

**Minimum Required**: Just an address  
**Recommended**: Address + building type + stories  
**Best Results**: Address + `floor_area_per_story_m2` + stories + year built

The system will:
1. ✅ Use your specifications when provided
2. ✅ Fall back to OSM data if you don't specify
3. ✅ Apply smart defaults based on building type
4. ✅ Generate a complete, simulation-ready IDF file

---

## 🎯 Quick Reference

| Input Method | Best For |
|-------------|----------|
| Command Line | Quick testing, scripts |
| Python API | Integration, automation |
| Web Interface | Non-technical users, document uploads |
| NLP CLI | Natural language descriptions |

---

**Ready to use!** Just provide an address and optionally specify parameters. The system handles the rest! 🚀

