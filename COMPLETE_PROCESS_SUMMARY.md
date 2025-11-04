# Complete Process: IDF Generation to Energy Results

## Overview

The complete auto-fix process now includes:

1. **Weather File Discovery** - Finds or downloads weather files
2. **IDF Generation** - Creates EnergyPlus IDF files from addresses
3. **EnergyPlus Simulation** - Runs simulations (local or API)
4. **Automatic Error Fixing** - Iteratively fixes errors until 0 errors
5. **Internet Research** - Searches for solutions when stuck
6. **Energy Results Extraction** - Extracts comprehensive energy data
7. **Energy Validation** - Validates energy data consistency

## Features Added

### Internet Research Capabilities

- **EnergyPlus Documentation Search** - Finds solutions from official docs
- **Weather File Download** - Downloads missing weather files from NREL
- **Example Code Lookup** - Finds example IDF patterns for common errors
- **Automatic Research** - Triggers when stuck on errors

### Comprehensive Energy Extraction

- **SQLite Database** - Extracts from `eplusout.sql`
- **CSV Tabular Output** - Extracts from `eplustbl.csv`
- **Fallback Methods** - Multiple extraction strategies
- **Energy Metrics** - Total site energy, EUI, end uses

### Enhanced Error Fixing

- **Duplicate Name Fixes** - Handles duplicate object names
- **Zone Name Matching** - Improved zone name resolution
- **Schedule Detection** - Better schedule existence checking
- **Iterative Improvement** - Runs until 0 errors

## Usage

### Basic Usage

```bash
python test_full_process_with_research.py
```

This will:
1. Find weather files (or download if missing)
2. Generate IDF for Chicago, IL
3. Run simulation
4. Fix errors automatically
5. Extract energy results
6. Display comprehensive results

### Full Process Script

```python
from src.auto_fix_engine import AutoFixEngine

engine = AutoFixEngine(
    max_iterations=50,    # Run until 0 errors
    use_research=True,    # Enable internet research
    use_api=True         # Enable API fallback
)

result = engine.process_single_location(weather_info, "output")
```

## Process Flow

```
Address → IDF Generation
    ↓
Simulation (Local or API)
    ↓
Error Detection
    ↓
Automatic Fixing
    ↓
Internet Research (if stuck)
    ↓
Re-simulate
    ↓
Repeat until 0 errors
    ↓
Energy Extraction
    ↓
Energy Validation
    ↓
Final Results
```

## Output

The system provides:

1. **IDF File** - Fixed IDF ready for EnergyPlus
2. **Simulation Results** - Error counts, warnings
3. **Energy Data** - Total energy, EUI, end uses
4. **Validation Results** - Energy consistency check
5. **Fix History** - All fixes applied

## Research Capabilities

When the system gets stuck, it automatically:

- Searches EnergyPlus documentation
- Downloads missing weather files
- Finds example IDF patterns
- Provides structured research results

## Energy Results Format

```json
{
  "total_site_energy_kwh": 150000.0,
  "columns": ["Total Site Energy (kWh)", "Heating (kWh)", ...],
  "data": [
    {
      "Total Site Energy (kWh)": 150000.0,
      "Heating (kWh)": 45000.0,
      ...
    }
  ]
}
```

## Files Created

- `src/auto_fix_engine.py` - Main engine with research capabilities
- `test_full_process_with_research.py` - Complete test script
- `output/test_complete/` - All output files

## Status

✅ **Fully Functional** - Complete process from address to energy results
✅ **Internet Research** - Automatic research when needed
✅ **Energy Extraction** - Multiple extraction methods
✅ **Iterative Fixing** - Runs until 0 errors or stuck

