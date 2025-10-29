# How IDF Creator Works: From Address to Complete Building Model

## 🎯 Overview

You give an **address**, and IDF Creator builds a **complete energy model** by making intelligent decisions at each step. Here's how the magic happens:

---

## 🔄 The Pipeline: Address → IDF File

### Step 1: **Address → Location Data** 
```
Input: "Willis Tower, Chicago, IL"
       ↓
       [OpenStreetMap Geocoding]
       ↓
Output: {
  latitude: 41.879,
  longitude: -87.636,
  climate_zone: "5A",  ← KEY for everything else!
  weather_file: "USA_IL_Chicago-OHare.epw"
}
```

**Why this matters**: Climate zone determines insulation levels, HVAC sizing, and building code compliance!

---

### Step 2: **Address + OSM → Building Footprint**
```
Input: Latitude/Longitude
       ↓
       [OpenStreetMap Building Data]
       ↓
Output: {
  footprint_area: 14,090 m²,
  building_type: "commercial",  ← Gets mapped to "office"
  stories: 3,
  roof_type: "flat"
}
```

**Why this matters**: Real building shape → realistic geometry

---

### Step 3: **Building Type → Template Selection** 🎯
```
--building-type Office
       ↓
Templates in multi_building_types.py:
{
  'office': {
    hvac_system_type: 'VAV',          ← THIS determines HVAC!
    construction_standard: 'ASHRAE 90.1',
    lighting_power_density: 10.8 W/m²,
    occupancy_density: 0.05 people/m²,
    window_wall_ratio: 0.4,
    space_types: ['office_open', 'conference', 'break_room', 'lobby']
  }
}
```

**THIS IS THE KEY**: Each building type has a hardcoded template with all the defaults!

---

### Step 4: **Building Type + Climate Zone → Materials**
```
Building: Office
Climate: 5A
       ↓
Materials Library picks:
- Wall: R-19 insulation (5A needs more than 3A)
- Roof: R-30 insulation (ASHRAE 90.1 compliant)
- Window: Double-pane Low-E (heating dominated climate)
- Floor: R-20 insulation
```

**Code Location**: `src/professional_material_library.py`
- Office in Zone 3A → R-13 walls
- Office in Zone 5A → R-19 walls  
- Office in Zone 8A → R-30 walls

---

### Step 5: **Building Type → HVAC System Type** 🎯
```
Building Type → HVAC System Mapping:

'office'         → VAV (Variable Air Volume)
'retail'         → RTU (Rooftop Unit)
'residential'    → HeatPump
'residential_multi' → PTAC (Packaged Terminal AC)
'hospital'       → ChilledWater
'warehouse'      → RTU
```

**Code Location**: Lines 274-275 in `professional_idf_generator.py`:
```python
building_template = self.building_types.get_building_type_template(building_type)
hvac_type = building_template.hvac_system_type  # Gets 'VAV' for office
```

Then this `hvac_type` gets passed to `generate_hvac_system()` which generates all the coils, fans, controls, etc.

---

### Step 6: **Zone Area + Building Type → HVAC Sizing**
```
Zone Area: 1666 m²
Building Type: Office
       ↓
[Calculate loads from ASHRAE standards]
       ↓
Cooling Load: 100 W/m² × 1666 = 166,600 W
Heating Load: 80 W/m² × 1666 = 133,280 W
Airflow: 1666 m² × 0.5 L/s/m² = 833 L/s
       ↓
[Select equipment sized for these loads]
```

**Code Location**: `src/advanced_hvac_systems.py` lines 173-227

---

### Step 7: **Space Type → Loads**
```
Zone Name: "office_open_1" 
       ↓
determine_space_type() returns: 'office_open'
       ↓
Space Template:
{
  occupancy_density: 0.05 people/m²,
  lighting_power_density: 10.8 W/m²,
  equipment_power_density: 8.1 W/m²
}
       ↓
For 1666 m² zone:
- 1666 × 0.05 = 83 people
- 1666 × 10.8 = 18,000 W lighting
- 1666 × 8.1 = 13,500 W equipment
```

**Code Location**: `src/multi_building_types.py` lines 238-358

---

### Step 8: **All Data → Complete IDF**
```
Combine:
- Surfaces (walls, floors, roofs, windows)
- Materials (R-values, U-factors)
- HVAC (coils, fans, controls)
- Loads (people, lights, equipment)
- Schedules (occupancy, lighting, equipment)
- Controls (thermostats, economizers)
       ↓
Write: Complete IDF file (5,949 lines)
```

---

## 🎯 Key Decision Points

### Where Does HVAC Type Come From?
**FROM BUILDING TYPE TEMPLATE** (line 50 in `multi_building_types.py`):
```python
'office': BuildingTypeTemplate(
    hvac_system_type='VAV',  ← Hardcoded!
    ...
)
```

You can override with `--building-type`:
```bash
python main.py "address" --building-type Retail
# → Gets RTU system (line 95)
```

### Where Does Window Size Come From?
**FROM BUILDING TYPE TEMPLATE** (line 44):
```python
'office': BuildingTypeTemplate(
    window_wall_ratio=0.4,  ← 40% glazing
    ...
)
```

You can override with `--wwr`:
```bash
python main.py "address" --wwr 0.5  # 50% glazing
```

### Where Does Insulation Level Come From?
**FROM CLIMATE ZONE**:
```python
# src/professional_material_library.py
CZ 1-2: R-13 walls
CZ 3-4: R-19 walls
CZ 5-8: R-30 walls
```

Automatically selected based on geographic location!

### Where Does Occupancy Come From?
**FROM SPACE TYPE TEMPLATE**:
```python
'office_open': {
    occupancy_density: 0.05,  # people/m²
    lighting_power_density: 10.8,  # W/m²
    equipment_power_density: 8.1,  # W/m²
}
```

Automatically applied based on zone name patterns (office_open, conference, break_room, etc.)

---

## 🧠 Intelligence vs. Randomness

### What's Intelligent ✅
- **Climate-appropriate materials** (cold climates → more insulation)
- **Building-type appropriate systems** (offices → VAV, retail → RTU)
- **Code-compliant defaults** (ASHRAE 90.1, IECC)
- **Real-world geometries** (OSM building footprints)
- **Proper HVAC sizing** (loads-based, not random)

### What's Not Intelligent (Simplified) ⚠️
- **Zone layouts**: Random polygon placement within footprint
- **Room assignments**: Based on keyword matching in zone names
- **Window placement**: Centered on walls, no real window placement logic
- **Equipment selection**: Generic equipment, not specific model numbers (unless using catalog)

---

## 📊 Example: Complete Flow for Willis Tower

```bash
python main.py "Willis Tower, Chicago" --professional --building-type Office
```

**What happens**:

1. ✅ Geocodes → 41.879, -87.636
2. ✅ Climate zone → 5A (colder climate)
3. ✅ OSM lookup → Commercial building, 14,090 m² footprint
4. ✅ Building type: `office` → Template loads:
   - HVAC: VAV system
   - Window ratio: 40%
   - Occupancy: 0.05 people/m²
   - Lighting: 10.8 W/m²
5. ✅ Materials → R-19 walls, R-30 roof (Zone 5A needs more insulation)
6. ✅ Zones → Creates multiple office zones
7. ✅ HVAC → Generates VAV system with:
   - Variable speed fan
   - DX cooling coil
   - Electric heating coil
   - VAV terminal with reheat
8. ✅ Loads → Each zone gets 116 people, 18 kW lighting, 13.5 kW equipment
9. ✅ Output → 5,949 line IDF file ✅

---

## 🎛️ What You Can Override

### Via Command Line:
```bash
--building-type Office     # Choose HVAC system type
--stories 5                # Number of floors
--floor-area 5000          # Total square meters
--wwr 0.35                 # Window-to-wall ratio
--wwr-s 0.5                # South facade WWR
--equip-source bcl         # Use catalog equipment
--equip-capacity 3ton      # Equipment size
```

### What You CAN'T Override (Hardcoded in Templates):
- HVAC system efficiency (defaults in `advanced_hvac_systems.py`)
- Occupancy densities (building type specific)
- Material properties (fixed in `professional_material_library.py`)
- Space type naming conventions

---

## 🔧 To Add Custom HVAC or Materials

### Add New Building Type:
Edit `src/multi_building_types.py`:
```python
'data_center': BuildingTypeTemplate(
    hvac_system_type='ChilledWater',
    equipment_power_density=800.0,  # W/m² (servers!)
    ...
)
```

### Add New HVAC System:
Edit `src/advanced_hvac_systems.py`:
```python
def _generate_radiant_system(self, ...):
    # Your custom radiant cooling system
```

---

## 💡 Summary

**The address doesn't directly pick HVAC systems.** Instead:

1. Address → **Location** (lat/lng, climate zone)
2. Location → **Climate-appropriate materials**
3. Building type → **HVAC type** (VAV, RTU, PTAC, etc.)
4. Zone area → **HVAC sizing** (loads-based)
5. Space name → **Occupancy & loads**

It's a **decision tree** built from industry standards (ASHRAE, IECC) and building-type templates. The intelligence is in the **templates**, not the address!

