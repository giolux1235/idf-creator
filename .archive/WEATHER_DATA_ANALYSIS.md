# Weather Data Analysis for Tests

**Date**: 2025-11-01  
**Status**: ⚠️ **Potential Accuracy Issue Identified**

---

## Summary

The test script **attempts to use location-appropriate weather files**, but **falls back to using Chicago.epw for all buildings** because other weather files are not available locally.

---

## Weather Files Suggested by Location

The `EnhancedLocationFetcher` correctly suggests weather files based on building location:

| Building Location | Suggested Weather File |
|------------------|------------------------|
| **Chicago, IL** | `USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw` |
| **New York, NY** | `USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw` |
| **San Francisco, CA** | `USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw` |

**Source**: `src/nrel_fetcher.py` - maps coordinates to appropriate TMY3 weather files

---

## Weather Files Actually Available

**Only 1 weather file exists locally**:
- ✅ `artifacts/desktop_files/weather/Chicago.epw` (1.6 MB)

**Missing weather files** (suggested but not available):
- ❌ `USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw` (Chicago - close match to Chicago.epw)
- ❌ `USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw` (New York)
- ❌ `USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw` (San Francisco)

---

## Test Script Fallback Logic

From `test_10_real_buildings.py` (lines 232-259):

1. **First**: Try to find the suggested weather file in common directories
2. **If not found**: Fall back to **any** `.epw` file found in common directories
3. **Result**: All tests end up using `Chicago.epw` because it's the only file available

```python
# Find weather file
weather_file = data['location'].get('weather_file')  # e.g., "USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw"
weather_path = None

# Try to find suggested file
if weather_file:
    weather_name = os.path.basename(weather_file)
    for path in common_paths:
        test_path = os.path.join(path, weather_name)
        if os.path.exists(test_path):
            weather_path = test_path
            break

# FALLBACK: Use any EPW file if suggested one not found
if not weather_path:
    for path in common_paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith('.epw'):
                    weather_path = os.path.join(path, file)  # ← Uses Chicago.epw
                    break
            if weather_path:
                break
```

---

## Impact on Test Accuracy

### Expected Impact

Using Chicago weather for all buildings may cause:

1. **NYC Buildings** (Empire State, Bank of America, Flatiron):
   - **Expected**: New York weather (hotter summers, colder winters than Chicago)
   - **Actual**: Chicago weather
   - **Impact**: Could overestimate cooling and underestimate heating
   - **Estimated Error**: ±5-15% depending on building type

2. **SF Buildings** (Transamerica Pyramid):
   - **Expected**: San Francisco weather (mild, Mediterranean)
   - **Actual**: Chicago weather (continental, more extreme)
   - **Impact**: Could significantly overestimate heating/cooling needs
   - **Estimated Error**: ±10-20%

3. **Chicago Buildings** (Willis Tower, Aon Center, etc.):
   - **Expected**: Chicago weather ✅
   - **Actual**: Chicago weather ✅
   - **Impact**: None (correct weather file)

---

## How to Fix

### Option 1: Download Location-Appropriate Weather Files

Download the suggested weather files from EnergyPlus:

```bash
# Download NYC weather file
wget https://energyplus.net/weather-location/north_and_central_america_wmo_region_4/USA/NY/USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw \
  -O artifacts/desktop_files/weather/USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw

# Download SF weather file  
wget https://energyplus.net/weather-location/north_and_central_america_wmo_region_4/USA/CA/USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw \
  -O artifacts/desktop_files/weather/USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw
```

### Option 2: Manual Download

1. Visit https://energyplus.net/weather
2. Navigate to: North and Central America WMO Region 4 → USA
3. Download:
   - New York → LaGuardia Airport (TMY3)
   - San Francisco → International Airport (TMY3)
4. Place files in `artifacts/desktop_files/weather/`

### Option 3: Use EnergyPlus Weather Manager

If EnergyPlus is installed:
```bash
# EnergyPlus includes weather files in installation
# Typically at: /usr/share/EnergyPlus/weather/ or /opt/EnergyPlus/weather/
# Copy appropriate files to project directory
```

---

## Current Test Results Interpretation

Given that **all non-Chicago buildings are using Chicago weather**:

### Chicago Buildings (Correct Weather)
- ✅ **Willis Tower**: +1.2% (excellent - weather correct)
- ✅ **Aon Center**: +4.3% (excellent - weather correct)
- ✅ **John Hancock Center**: +2.4% (excellent - weather correct)

### NYC Buildings (Incorrect Weather - Chicago Used)
- ✅ **Empire State Building**: -8.9% (good, but could be better with NYC weather)
- ✅ **Bank of America Tower**: -16.9% (acceptable, CHP complexity)
- ✅ **Flatiron Building**: -15.9% (acceptable, very old building)
- ✅ **30 Rockefeller Plaza**: -10.8% (good)

**Note**: These results are **still within acceptable range**, but using correct weather files could improve accuracy by 5-10%.

### SF Buildings (Incorrect Weather - Chicago Used)
- ✅ **Transamerica Pyramid**: -7.0% (good, but SF weather would likely improve)

---

## Recommendation

1. **Immediate**: Download NYC and SF weather files to improve accuracy
2. **Priority**: NYC buildings (7 out of 11 test buildings are in NYC)
3. **Expected Improvement**: ±5-10% better accuracy for non-Chicago buildings

---

## Weather File Sources

- **EnergyPlus Weather Database**: https://energyplus.net/weather
- **NREL NSRDB**: https://nsrdb.nrel.gov/ (for custom locations)
- **Typical Meteorological Year (TMY3)**: Standard format used by EnergyPlus

---

## Code References

- **Weather Selection Logic**: `test_10_real_buildings.py` lines 232-259
- **Location-to-Weather Mapping**: `src/nrel_fetcher.py` lines 42-121
- **Weather File Naming**: `src/enhanced_location_fetcher.py` lines 78-83



