# LEED Benchmark Tests - Summary

## Overview

Successfully extracted building and energy data from 5 real LEED energy audit reports and created benchmark tests for the IDF Creator.

## Extraction Process

1. **PDF Processing**: Processed PDFs page-by-page using PyPDF2
2. **Data Extraction**: Extracted comprehensive building and energy data:

### Basic Building Information
   - Building addresses
   - Building names
   - Floor areas (sqft and m²)
   - Number of floors/stories
   - Year built
   - Building types

### Energy Metrics
   - Energy Use Intensity (EUI) in kBtu/sqft
   - Annual energy consumption (kWh)
   - Energy breakdowns by end use (Lighting, HVAC, Heating, Cooling, Equipment, etc.)

### Detailed Building Parameters (for accurate simulation)
   - **Lighting Power Density** (W/sqft, W/m²)
   - **Equipment Power Density** (W/sqft, W/m²)
   - **Occupancy Density** (people/sqft, people/m²)
   - **Total Number of People**
   - **HVAC System Types** (VAV, CAV, PTAC, RTU, Chiller, Boiler, Heat Pump, etc.)
   - **HVAC Capacity** (tons, MBH)
   - **Operating Schedule** (hours per day, days per week)
   - **Window-to-Wall Ratio** (percentage)

3. **Report Selection**: Selected 5 diverse reports with the most complete data:
   - Arbutus Park Manor (Restaurant)
   - Franklin Towers (Residential)
   - Madison Town Building (Fire Station)
   - MTES School
   - Peekskill Office Building

## Test Cases Created

### Test 1: Arbutus Park Manor
- **Location**: 207 Ottawa Street, Johnstown, PA 15904
- **Type**: Restaurant
- **Area**: 29,250 sqft (2,717 m²)
- **Year Built**: 1972
- **Target EUI**: 117.1 kBtu/sqft
- **Annual Electric**: 1,481,172 kWh

### Test 2: Franklin Towers
- **Location**: Tarrytown, NY
- **Type**: Residential
- **Floors**: 1
- **Year Built**: 1951
- **Target EUI**: 78.0 kBtu/sqft (Site), 95.7 kBtu/sqft (Source)
- **Annual Electric**: 10,875 kWh
- **Energy Breakdown**: Lighting 10%, Cooling 12%

### Test 3: Madison Town Building
- **Type**: Fire Station
- **Year Built**: 2010
- **Energy Breakdown**: Lighting 11.7%, Heating 59.0%, Cooling 15.5%

### Test 4: MTES School
- **Type**: School
- **Year Built**: 1954
- **Annual Electric**: 542,760 kWh
- **Annual Gas**: 41,540 therms (1,217,122 kWh equivalent)

### Test 5: Peekskill Office
- **Location**: 807 Main Street, Peekskill, NY 10566
- **Type**: Office
- **Area**: 190 sqft (18 m²)
- **Floors**: 5
- **Year Built**: 2020
- **Annual Electric**: 1,330 kWh

## Files Created

1. **Extraction Scripts**:
   - `scripts/extract_leed_reports.py` - Main extraction engine
   - `scripts/extract_selected_reports.py` - Extract from selected reports
   - `scripts/extract_best_reports.py` - Score and select best reports

2. **Test Data**:
   - `artifacts/leed_benchmark_tests/benchmark_test_1.json` through `benchmark_test_5.json`
   - `artifacts/leed_benchmark_tests/benchmark_tests_combined.json`

3. **Benchmark Test Script**:
   - `test_leed_benchmark_5_tests.py` - Run all 5 benchmark tests

4. **Documentation**:
   - `artifacts/leed_benchmark_tests/README.md` - Test documentation
   - `LEED_BENCHMARK_TESTS.md` - This file

## Running the Tests

To run the benchmark tests:

```bash
python3 test_leed_benchmark_5_tests.py
```

The script will:
1. Load the 5 test cases
2. Generate IDF files for each building
3. Apply calibration factors
4. Run EnergyPlus simulations
5. Compare simulated results with reported data
6. Generate a summary report

## Expected Output

Each test will show:
- Building details (address, type, area, floors)
- Target energy metrics (EUI, annual consumption)
- Simulated energy metrics
- Comparison and error percentage
- Status (EXCELLENT/GOOD/NEEDS IMPROVEMENT)

## Data Quality

- **Complete Data**: Tests 1 and 2 have the most complete data (address, area, EUI, consumption)
- **Partial Data**: Tests 3, 4, and 5 have some missing fields (filled with reasonable defaults)
- **Energy Data**: All tests have some energy data (EUI or annual consumption)

## Enhanced Benchmarking Accuracy

The enhanced extraction now captures detailed building parameters that directly impact energy simulation accuracy:

### Lighting Details
- **Power Density**: Extracted from reports (W/m²)
- **Impact**: Lighting typically accounts for 20-30% of building energy use
- **Usage**: Directly sets `lighting_power_density` parameter in IDF generation

### Equipment Details
- **Power Density**: Extracted from reports (W/m²)
- **Impact**: Equipment/plug loads account for 25-35% of energy use
- **Usage**: Directly sets `equipment_power_density` parameter

### Occupancy Details
- **Density**: Extracted from reports (people/m²)
- **Total People**: Extracted when available
- **Impact**: Affects internal heat gains, ventilation requirements
- **Usage**: Sets `occupancy_density` parameter

### HVAC System Details
- **System Types**: Identified from reports (VAV, RTU, Chiller, Boiler, etc.)
- **Capacity**: Extracted when available (tons, MBH)
- **Impact**: HVAC accounts for 35-45% of building energy use
- **Usage**: Can inform HVAC system selection in IDF generation

### Operating Schedule
- **Hours per Day**: Extracted from reports
- **Days per Week**: Extracted when available
- **Impact**: Significantly affects energy consumption patterns
- **Usage**: Can be used to create realistic operating schedules

### Window Details
- **Window-to-Wall Ratio**: Extracted from reports (%)
- **Impact**: Affects solar heat gain, daylighting, heating/cooling loads
- **Usage**: Sets `window_to_wall_ratio` parameter

## Benchmark Test Process

The benchmark test script (`test_leed_benchmark_5_tests.py`) now:

1. **Loads extracted data** with all detailed parameters
2. **Prioritizes extracted values** over defaults:
   - Uses extracted lighting power density if available
   - Uses extracted equipment power density if available
   - Uses extracted occupancy density if available
   - Falls back to calibration factors if extraction data not available
3. **Generates IDF files** with accurate parameters
4. **Runs EnergyPlus simulations**
5. **Compares results** with reported energy data
6. **Provides detailed analysis** of accuracy

## Next Steps

1. Run the benchmark tests to validate IDF Creator accuracy
2. Analyze results and identify areas for improvement
3. Refine calibration factors based on results
4. Extract additional data from more reports if needed
5. Enhance HVAC system selection based on extracted HVAC details
6. Create operating schedules based on extracted schedule data

## Notes

- Some PDFs had incomplete or unclear data
- Address extraction sometimes includes OCR errors
- Area extraction may need manual verification for some reports
- Energy breakdowns are not always available in all reports
- Building types were inferred from report content

