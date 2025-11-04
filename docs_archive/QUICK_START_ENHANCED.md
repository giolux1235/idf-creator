# Quick Start Guide - Enhanced Features

This guide shows you how to use the newly added enhanced features in IDF Creator.

## What's New

The IDF Creator now includes 6 major enhancement modules:

1. ✅ **Catalog Equipment Wiring** - BCL/AHRI equipment integration
2. ✅ **Air Loop Node Plumbing** - Complete HVAC system connections  
3. ✅ **Advanced HVAC Controls** - PID, economizers, VAV controls
4. ✅ **Shading & Daylighting** - External/internal shading, daylight controls
5. ✅ **Infiltration & Natural Ventilation** - Air leakage and natural cooling
6. ✅ **Renewable Energy Systems** - PV, solar thermal, wind

---

## Getting Started

### Basic Usage with Enhanced Features

The enhanced features are automatically available when using **professional mode**:

```bash
python main.py "123 Main St, San Francisco, CA" --professional
```

### With Building Type

```bash
python main.py "456 Oak Ave, Chicago, IL" \
  --professional \
  --building-type office \
  --stories 5 \
  --floor-area 3000
```

### With Custom Window Configuration

```bash
python main.py "789 Pine Rd, New York, NY" \
  --professional \
  --wwr 0.35 \
  --wwr-s 0.50  # Higher glazing on south facade
```

---

## Module-Specific Usage

### 1. HVAC Plumbing & Controls

All HVAC systems automatically include:
- Complete node connections
- Economizer controls (where applicable)
- Advanced setpoint management
- Proper branch lists

### 2. Shading & Daylighting

Shading is automatically generated based on:
- Building type
- Window orientation
- Climate zone

To customize, access the shading engine programmatically:

```python
from src.shading_daylighting import ShadingDaylightingEngine

engine = ShadingDaylightingEngine()
shading = engine.generate_window_shading(
    window_name="Window_1",
    window_surface_name="Wall_1",
    building_type="office",
    orientation="South"
)
```

### 3. Infiltration & Natural Ventilation

Infiltration rates are automatically set based on:
- Building type
- Climate zone

Natural ventilation can be enabled programmatically:

```python
from src.infiltration_ventilation import InfiltrationVentilationEngine

engine = InfiltrationVentilationEngine()
ventilation = engine.generate_natural_ventilation(
    zone_name="Zone_1",
    ventilation_type="single_zone"
)
```

### 4. Renewable Energy

Add renewable systems to your building:

```python
from src.renewable_energy import RenewableEnergyEngine

engine = RenewableEnergyEngine()

# Add rooftop PV
pv = engine.generate_pv_system(
    name="Building_PV",
    surface_name="Roof_1",
    system_type="rooftop"
)

# Add solar thermal
solar_thermal = engine.generate_solar_thermal_collector(
    name="Building_Solar",
    surface_name="Roof_1"
)
```

---

## Building Type Recommendations

Different building types get optimized configurations:

### Office Buildings
- VAV systems with economizers
- External overhangs on south, east, west
- Daylighting controls
- Moderate infiltration rates

### Residential
- Internal window shades
- Natural ventilation strategies
- Higher infiltration rates
- Rooftop PV potential

### Retail
- Minimal shading (maximize storefront visibility)
- High-lighting power density
- Large infiltration areas
- Solar thermal for hot water

### Industrial/Warehouse
- High infiltration (large doors)
- Limited daylighting (skylights)
- Minimal HVAC controls
- Wind generation potential

---

## Climate Zone Optimizations

The system automatically adjusts based on climate zone:

### Hot Climates (Zones 1-2)
- Reduced infiltration
- Maximum shading
- Economizer for free cooling
- High solar PV potential

### Moderate Climates (Zones 3-4)
- Balanced infiltration
- Selective shading
- Night precooling strategies
- Hybrid ventilation

### Cold Climates (Zones 5-8)
- Increased infiltration (wind-driven)
- Minimal shading
- Advanced heating controls
- Solar thermal for domestic hot water

---

## Programmatic Access

### Full Programmatic Control

```python
from src.professional_idf_generator import ProfessionalIDFGenerator
from src.equipment_catalog.adapters import bcl

# Create generator
generator = ProfessionalIDFGenerator()

# Access new modules
plumbing = generator.hvac_plumbing
controls = generator.advanced_controls
shading = generator.shading_daylighting
ventilation = generator.infiltration_ventilation
renewables = generator.renewable_energy

# Generate comprehensive IDF
idf_content = generator.generate_professional_idf(
    address="123 Main St, City, State",
    building_params={
        'building_type': 'office',
        'stories': 5,
        'total_area': 5000
    },
    location_data={
        'latitude': 37.7749,
        'longitude': -122.4194,
        'climate_zone': '3C',
        'weather_file': 'USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw'
    }
)
```

---

## Output Structure

When you generate an IDF with professional mode, you'll get:

```
artifacts/desktop_files/idf/
  └── YourBuilding.idf       # Complete IDF with all features
```

The IDF includes:
- ✅ All surfaces with proper constructions
- ✅ HVAC systems with complete node connections
- ✅ Advanced controls (economizers, PID, etc.)
- ✅ Shading devices
- ✅ Infiltration modeling
- ✅ Daylighting controls
- ✅ Schedules for all loads
- ✅ Weather file reference

---

## Next Steps

1. **Generate an IDF** using the examples above
2. **Run in EnergyPlus** to see the results
3. **Review outputs** for energy consumption, thermal comfort, daylighting
4. **Iterate** by adjusting parameters (WWR, shading, ventilation)

---

## Troubleshooting

### Module Import Errors
```bash
# Make sure you're in the project root
cd "/path/to/IDF - CREATOR"
python main.py ...
```

### Missing Features
Ensure you're using `--professional` flag:
```bash
python main.py "address" --professional
```

### Validation Errors
Check EnergyPlus version compatibility (24.2+):
```bash
energyplus --version
```

---

## Documentation

For detailed documentation, see:
- `ENHANCED_CAPABILITIES.md` - Complete feature documentation
- `README.md` - General usage guide
- `src/*.py` - Source code with docstrings

---

## Examples

See the `artifacts/desktop_files/idf/` directory for example IDF files generated with various configurations.

