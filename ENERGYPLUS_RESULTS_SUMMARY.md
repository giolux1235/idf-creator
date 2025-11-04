# EnergyPlus Simulation Results Summary

This document summarizes what we get from EnergyPlus simulation results and how to extract them.

## Test Results

We ran two test simulations:

### Test 1: Small Office Building (Chicago)
- **Address**: 123 Main St, Chicago, IL 60601
- **Building**: 3 stories, 500 m²/floor (1500 m² total)
- **Weather File**: Chicago O'Hare (TMY3)
- **Status**: ✅ Successfully completed

#### Results Extracted:

**From CSV Tabular Output (`eplustbl.csv`):**
- **Building Area**: 1,523.85 m²
- **Total Site Energy**: 261,561.32 kWh (941.62 GJ)
- **Total Source Energy**: 828,364.55 kWh (2,982.11 GJ)
- **EUI (Energy Use Intensity)**: 171.65 kWh/m²

**End Use Breakdown:**
- **Heating**: 161,716.80 kWh (582.18 GJ) - 62% of total
- **Cooling**: 1,263.89 kWh (4.55 GJ) - <1% of total
- **Interior Lighting**: 55,488.93 kWh (199.76 GJ) - 21% of total
- **Interior Equipment**: 39,205.59 kWh (141.14 GJ) - 15% of total
- **Fans**: 3,886.11 kWh (13.99 GJ) - 1.5% of total

**Key Insights:**
- Heating dominates energy consumption (62%), which is expected for Chicago's cold climate
- Very low cooling load (<1%) suggests the building is well-insulated or has minimal cooling needs
- Lighting and equipment together account for ~36% of total energy use
- Total site energy is 261,561 kWh/year, which is reasonable for a 1,524 m² office building
- EUI of 171.65 kWh/m² is typical for office buildings (ASHRAE 90.1 baseline is ~100-200 kWh/m²)

### Test 2: Medium Office Building (New York)
- **Address**: 456 Broadway, New York, NY 10013
- **Building**: 10 stories, 800 m²/floor (8,000 m² total)
- **Weather File**: Not found (simulation failed)
- **Status**: ❌ Failed - No weather file available

**Error**: Simulation failed because no weather file was found. EnergyPlus requires a weather file for annual simulations.

## EnergyPlus Output Files

EnergyPlus generates several output files that contain different types of results:

### 1. **eplustbl.csv** - Tabular Output (Recommended for Quick Analysis)
- **Format**: CSV with structured sections
- **Contains**: 
  - Annual Building Utility Performance Summary
  - Site and Source Energy totals
  - End Use breakdowns (Heating, Cooling, Lighting, Equipment, etc.)
  - Building area information
  - Energy per unit area (EUI)
- **Best For**: Quick extraction of annual totals and end-use breakdowns
- **How to Parse**: Use regex or string parsing to extract values from structured text sections

### 2. **eplusout.sql** - SQLite Database (Recommended for Detailed Analysis)
- **Format**: SQLite database
- **Contains**:
  - Time-series data (hourly, monthly, annual)
  - Meter data (electricity, gas, etc.)
  - Variable data (temperatures, loads, etc.)
  - Multiple reporting frequencies
- **Best For**: Detailed analysis, time-series data, custom queries
- **Key Tables**:
  - `ReportMeterData` / `ReportMeterDataDictionary`: Meter readings (Electricity:Facility, NaturalGas:Facility, etc.)
  - `ReportVariableData` / `ReportVariableDataDictionary`: Individual variables (zone temperatures, loads, etc.)
  - `Time`: Time indices for time-series data
- **How to Query**: Use SQLite to query meter/variable data by name and reporting frequency

### 3. **eplusout.err** - Error/Warning File
- **Format**: Text file
- **Contains**: 
  - Warnings, severe errors, fatal errors
  - Simulation completion status
  - Elapsed time
- **Best For**: Validating simulation success and checking for issues

### 4. **eplusout.rdd** - Report Data Dictionary
- **Format**: Text file
- **Contains**: List of available output variables and meters
- **Best For**: Discovering what data is available in the simulation

## Extraction Methods

### Method 1: CSV Parsing (Simple)
```python
import re

# Extract total site energy
site_energy_match = re.search(r'Total Site Energy,([\d.]+)', csv_content)
if site_energy_match:
    site_energy_gj = float(site_energy_match.group(1))
    site_energy_kwh = site_energy_gj * 277.778  # Convert GJ to kWh
```

### Method 2: SQLite Queries (Comprehensive)
```python
import sqlite3

conn = sqlite3.connect('eplusout.sql')
cursor = conn.cursor()

# Get annual electricity consumption
cursor.execute("""
    SELECT m.VariableName, SUM(d.VariableValue) as Total
    FROM ReportMeterData d
    JOIN ReportMeterDataDictionary m 
        ON d.ReportMeterDataDictionaryIndex = m.ReportMeterDataDictionaryIndex
    WHERE m.ReportingFrequency = 'RunPeriod'
    AND m.VariableName LIKE '%Electricity%'
    GROUP BY m.VariableName
""")
```

## Key Metrics Available

1. **Energy Consumption**:
   - Total Site Energy (kWh, GJ)
   - Total Source Energy (kWh, GJ)
   - Electricity consumption (kWh)
   - Natural Gas consumption (kWh)
   - End-use breakdowns

2. **Building Metrics**:
   - Building Area (m²)
   - Conditioned Area (m²)
   - Energy Use Intensity (EUI) in kWh/m²

3. **Time-Series Data** (from SQLite):
   - Hourly energy consumption
   - Monthly energy consumption
   - Peak demand
   - Zone temperatures
   - HVAC loads

4. **HVAC Performance**:
   - Heating/cooling loads
   - Fan/pump energy
   - System efficiency metrics

## Recommendations

1. **For Quick Annual Totals**: Use CSV parsing from `eplustbl.csv`
2. **For Detailed Analysis**: Use SQLite queries from `eplusout.sql`
3. **For Validation**: Always check `eplusout.err` for errors/warnings
4. **For Discovery**: Check `eplusout.rdd` to see available outputs

## Next Steps

- Fix SQLite extraction code to use correct column names (`VariableName`, `VariableValue`)
- Add monthly time-series extraction
- Add peak demand extraction
- Add zone-level detail extraction
- Create utility functions for common queries










