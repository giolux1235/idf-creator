# How to Fix the EnergyPlus API Issue

## Current Problem

The API reports: **"EnergyPlus ran but produced no energy results. Simulation ran for 0 days"**

## Root Cause Analysis

The API successfully:
- ✅ Receives the IDF file
- ✅ Runs EnergyPlus
- ✅ Processes the simulation

But fails to extract energy results because:
- The simulation may be running for 0 days (RunPeriod issue)
- The output files may not contain the expected data format
- The API's result extraction logic may not find the expected data

## Fixes Already Applied

### 1. ✅ Version Compatibility
- Updated to EnergyPlus 25.1 (matches API)

### 2. ✅ Output Objects Enhanced
- Added `Output:Table:SummaryReports` with `AnnualBuildingUtilityPerformanceSummary`
- Added multiple `Output:Variable` objects for energy data
- Added `Output:Meter` objects for facility-level meters

### 3. ✅ RunPeriod Configuration
- Configured to use weather file year
- Added all weather file flags (holidays, DST, etc.)

## Potential Solutions

### Solution 1: Verify RunPeriod is Working
The error "Simulation ran for 0 days" suggests the RunPeriod might not be matching the weather file.

**Check:**
```bash
grep -A 15 "RunPeriod," test_outputs/api_test/*.idf
```

**Fix:** Ensure RunPeriod dates match weather file year. Try setting explicit year:
```python
# In generate_run_period()
2024,                    !- Begin Year
2024,                    !- End Year
```

### Solution 2: Ensure Schedules Are Complete
Incomplete schedules can cause simulation to run but produce no results.

**Check:**
```bash
grep -c "Schedule:Compact" test_outputs/api_test/*.idf
```

**Fix:** Ensure all schedules have complete day types (Weekdays, Weekends, Holidays, etc.)

### Solution 3: Add Required Output Format
The API might need a specific output format. Try adding:

```python
Output:Table:Monthly,
  AllSummary;              !- Report 1 Name

Output:Table:TimeBins,
  AllSummary;              !- Report 1 Name
```

### Solution 4: Test with Minimal Valid IDF
Create a minimal IDF that definitely works, then compare:

```bash
python test_minimal_api.py
```

### Solution 5: Check API Documentation
The API might have specific requirements:
- Check if API expects specific meter names
- Check if API needs specific variable names
- Check if API requires specific output file formats

### Solution 6: Contact API Provider
Since the simulation runs but produces no results, the issue might be:
- API's result extraction logic
- API's file parsing expectations
- API-specific requirements not documented

## Recommended Next Steps

1. **Test with a known-working IDF** from EnergyPlus examples
2. **Compare working vs non-working IDFs** to identify differences
3. **Check API response** for detailed error logs or warnings
4. **Review API documentation** for specific requirements
5. **Test locally** to verify simulation produces results:
   ```bash
   energyplus -w weather.epw -d output_dir idf_file.idf
   ```

## Verification Commands

```bash
# Check RunPeriod
grep -A 15 "RunPeriod," test_outputs/api_test/*.idf

# Check Output objects
grep "^Output:" test_outputs/api_test/*.idf

# Check Schedules completeness
grep "Schedule:Compact" test_outputs/api_test/*.idf | wc -l

# Check if simulation runs locally
energyplus -w artifacts/desktop_files/weather/Chicago.epw \
  -d test_local_sim \
  test_outputs/api_test/api_test_233_S_Wacker_Dr__Chicago__IL_60606.idf
```

## Expected Output Files

When EnergyPlus runs successfully, it should produce:
- `eplustbl.csv` - Tabular output with energy summaries
- `eplusout.sql` - SQLite database with time-series data
- `eplusout.err` - Error/warning file

The API likely looks for energy totals in `eplustbl.csv` under "AnnualBuildingUtilityPerformanceSummary" section.

## Summary

**What's Fixed:**
- ✅ Version compatibility
- ✅ Output objects added
- ✅ RunPeriod configured

**What Might Still Need Fixing:**
- ⚠️ RunPeriod year matching weather file
- ⚠️ Schedule completeness
- ⚠️ API-specific output format requirements
- ⚠️ API's result extraction logic

The IDF file should now be correct. If the issue persists, it's likely an API-side issue with how it extracts results from the simulation output files.









