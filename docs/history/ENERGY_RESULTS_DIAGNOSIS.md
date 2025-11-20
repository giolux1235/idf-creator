# Energy Results Diagnosis - Test Results

## Test Date: 2025-11-04 18:04

## Test Configuration
- **Address**: 233 S Wacker Dr, Chicago, IL 60606
- **Building Type**: Office
- **Stories**: 5
- **Floor Area**: 50,000 sq ft
- **Weather File**: Chicago.epw (1.6 MB)
- **IDF Size**: 8.85 MB

---

## Test Results

### ✅ What's Working
1. **IDF Generation**: Success (8.85 MB file generated)
2. **Weather File**: Successfully included (1.6 MB)
3. **External API**: Accepts requests and processes
4. **EnergyPlus Execution**: Runs (version 25.1.0)
5. **SQLite File Generated**: ✅ `eplusout.sql` exists (180,224 bytes / 176 KB)

### ❌ Critical Issues Found

#### 1. **CSV File Missing** ⚠️ **MAIN PROBLEM**
- **Expected**: `eplustbl.csv` should be generated
- **Actual**: File not found in output files list
- **Impact**: Current parsing logic relies on CSV file for energy extraction
- **Why**: The `Output:Table:SummaryReports` with `AnnualBuildingUtilityPerformanceSummary` should generate CSV, but it's not being created

#### 2. **Error File Empty** ⚠️ **UNUSUAL**
- **File**: `eplusout.err` 
- **Size**: 0 bytes
- **Expected**: Should contain warnings, errors, and completion status
- **Impact**: Cannot see what EnergyPlus actually reported
- **Possible Causes**:
  - EnergyPlus didn't run properly
  - Error file not being read/written correctly
  - File path issue

#### 3. **All Other Output Files Empty**
- `eplusout.audit`: 0 bytes
- `eplusout.bnd`: 0 bytes
- `eplusout.dbg`: 0 bytes
- `eplusout.eio`: 0 bytes
- `eplusout.eso`: 0 bytes
- `eplusout.mtr`: 0 bytes
- **Only SQLite file has content**: 180,224 bytes

---

## Root Cause Analysis

### Why No Energy Results?

**Primary Issue**: **CSV file not generated**

The API's result extraction logic (in `web_interface.py`) follows this pattern:
1. ✅ Check if simulation completed
2. ✅ Try to extract from CSV (`eplustbl.csv`)
3. ⚠️ **CSV file doesn't exist** → Skip CSV extraction
4. ✅ Try SQLite (`eplusout.sql`)
5. ❓ SQLite extraction might not be working correctly

**Evidence**:
- SQLite file exists (176 KB) - so simulation did run
- But CSV file missing - suggests output format issue
- Error file empty - can't see what EnergyPlus reported

### Possible Causes

#### 1. **Output:Table:SummaryReports Issue**
The IDF has:
```idf
Output:Table:SummaryReports,
  AnnualBuildingUtilityPerformanceSummary,
  AllSummary;
```

But the CSV file (`eplustbl.csv`) isn't being generated. This could mean:
- The report name is incorrect
- EnergyPlus version 25.1 changed the format
- The output directory isn't being checked correctly

#### 2. **SQLite Extraction Not Working**
The SQLite file exists but results aren't being extracted. Possible issues:
- SQLite queries might not match the actual database schema
- Meter/variable names might be different
- Database might be empty or corrupted

#### 3. **Simulation Incomplete**
Despite SQLite file existing, the simulation might have:
- Failed early but still created SQLite file
- Run for 0 days (despite RunPeriod being set)
- Missing required objects (schedules, HVAC, etc.)

---

## Recommendations

### Immediate Actions

1. **Check SQLite Database Content**
   - The SQLite file exists (176 KB) - it should have data
   - Need to verify what tables/data are actually in it
   - **Action**: Enhance API to return SQLite table list and sample queries

2. **Investigate CSV Generation**
   - Why isn't `eplustbl.csv` being created?
   - Check if `Output:Table:SummaryReports` syntax is correct
   - Verify output directory location
   - **Action**: Add debug output showing where files are being written

3. **Fix Error File Reading**
   - Error file is 0 bytes - this is very unusual
   - Need to see actual EnergyPlus output
   - **Action**: Check file path and ensure error file is being read correctly

4. **Enhance SQLite Extraction**
   - Since CSV doesn't exist, must rely on SQLite
   - Current SQLite extraction logic might not be working
   - **Action**: Test SQLite queries and verify they match the database schema

### Code Changes Needed

#### For External API:
1. **Return SQLite Database Info**:
   - List of tables
   - Sample queries showing available data
   - Record counts

2. **Fix Error File Reading**:
   - Ensure error file is being read correctly
   - Return full error file content

3. **Add CSV Generation Debug**:
   - Show where CSV should be written
   - Check if file exists but in wrong location
   - Verify output directory structure

#### For Main API:
1. **Improve SQLite Extraction**:
   - Add more robust SQLite queries
   - Handle different database schemas
   - Add fallback queries

2. **Add CSV Alternative**:
   - If CSV doesn't exist, try other output formats
   - Check for alternative summary report files

---

## Key Findings Summary

| File | Status | Size | Notes |
|------|--------|------|-------|
| `eplustbl.csv` | ❌ Missing | 0 | **Critical** - Main extraction source |
| `eplusout.sql` | ✅ Exists | 176 KB | Has data but extraction may not work |
| `eplusout.err` | ⚠️ Empty | 0 | Should have content - indicates issue |
| Other files | ❌ Empty | 0 | All output files empty except SQLite |

---

## Next Steps

1. ✅ **Diagnostic Information**: Now available from API
2. ⏳ **SQLite Analysis**: Need to check what's actually in the database
3. ⏳ **CSV Generation Fix**: Investigate why CSV isn't being created
4. ⏳ **Error File Reading**: Fix error file reading to see EnergyPlus output
5. ⏳ **SQLite Extraction**: Improve SQLite query logic

---

## Conclusion

**The main issue is**: The CSV file (`eplustbl.csv`) is not being generated, which is the primary source for energy result extraction. The SQLite file exists but the extraction logic may not be working correctly.

**To fix**:
1. Investigate why CSV isn't being generated
2. Fix SQLite extraction to work with the actual database
3. Fix error file reading to see what EnergyPlus actually reported

The simulation is running (SQLite file proves it), but results aren't being extracted properly.









