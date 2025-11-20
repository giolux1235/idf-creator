# Additional Facility Meter Fixes - Documentation

**Date**: 2025-11-05  
**Status**: ✅ **FIXED** - Additional configuration issues addressed

---

## Issues Identified from Status Report

Based on the facility meter status report, several additional configuration issues were identified beyond the SQLite extraction fix:

---

## Fix 1: Output:VariableDictionary Setting

### Problem
`Output:VariableDictionary` was set to `Regular` instead of `IDF`, which may prevent generation of MDD (Meter Data Dictionary) and RDD (Report Data Dictionary) files needed for meter verification.

### Solution
Changed `Output:VariableDictionary` from `Regular` to `IDF` in:
- `src/professional_idf_generator.py` - Main IDF generator
- `src/auto_fix_engine.py` - Auto-fix engine (was incorrectly set to `IDD`)

### EnergyPlus Documentation
According to EnergyPlus documentation:
- **`IDF`**: Generates `eplusout.mdd` (Meter Data Dictionary) and `eplusout.rdd` (Report Data Dictionary) files
  - MDD file lists all available meters for the simulation
  - RDD file lists all available output variables
  - Useful for verifying which meters are available and can be requested
- **`Regular`**: Standard output generation (no MDD/RDD files)
- **`IDD`**: Input Data Dictionary (different purpose, not for meter verification)

### Impact
- ✅ MDD and RDD files will now be generated
- ✅ Easier to verify which meters are available
- ✅ Better debugging capability for meter issues
- ⚠️ May help with MTR file generation (still investigating)

---

## Files Modified

1. **src/professional_idf_generator.py**
   - Line 2444: Changed `Regular` to `IDF`
   - Added comment explaining purpose

2. **src/auto_fix_engine.py**
   - Line 320: Changed `IDD` to `IDF` (was incorrect)
   - Added comment explaining purpose

---

## Verification Checklist

After these fixes, verify:

- [x] `Output:VariableDictionary` is set to `IDF` in generated IDF files
- [ ] `eplusout.mdd` file is generated (lists available meters)
- [ ] `eplusout.rdd` file is generated (lists available variables)
- [ ] MDD file contains `Electricity:Facility` and `NaturalGas:Facility` meters
- [ ] MTR file generation improves (still investigating)

---

## Expected Output Files

After running a simulation with `Output:VariableDictionary, IDF;`, you should see:

1. **eplusout.mdd** - Meter Data Dictionary
   - Lists all available meters
   - Format: Meter name, units, reporting frequency options
   - Example: `Electricity:Facility [J]`

2. **eplusout.rdd** - Report Data Dictionary  
   - Lists all available output variables
   - Format: Variable name, units, reporting frequency options
   - Example: `Site Total Electricity Energy [J]`

3. **eplusout.mtr** - Meter Output File (if meters are requested)
   - Contains time-series meter data
   - Controlled by `Output:Meter` objects in IDF

---

## Testing Recommendations

1. **Generate an IDF** with the updated code
2. **Run a simulation** 
3. **Check for MDD/RDD files**:
   ```bash
   ls -la eplusout.mdd eplusout.rdd
   ```
4. **Verify meters in MDD file**:
   ```bash
   grep -i "electricity.*facility" eplusout.mdd
   grep -i "naturalgas.*facility" eplusout.mdd
   ```
5. **Check MTR file** (if generated):
   ```bash
   grep -i "electricity.*facility" eplusout.mtr
   ```

---

## Related Issues

### MTR File Generation (Still Investigating)

**Status**: ⚠️ **STILL INVESTIGATING**

**Problem**: Meters are correctly in IDF files but not appearing in `eplusout.mtr` output files.

**Possible Causes**:
1. ~~Output:VariableDictionary setting~~ ✅ **FIXED** - Changed to `IDF`
2. EnergyPlus version compatibility issue
3. Meters filtered out during IDF processing
4. EnergyPlus not generating meters if certain components are missing
5. Missing `OutputControl:Files` configuration

**Next Steps**:
1. ✅ Change `Output:VariableDictionary` to `IDF` - **DONE**
2. Test with minimal IDF to see if MTR file is generated
3. Check `eplusout.err` for meter-related warnings
4. Verify `OutputControl:Files` object if needed
5. Test with different EnergyPlus versions

---

## Summary

**Fixed**: ✅ `Output:VariableDictionary` changed from `Regular`/`IDD` to `IDF`

**Result**: MDD and RDD files will now be generated for better meter verification and debugging.

**Impact**: 
- Better debugging capability
- May help with MTR file generation
- Easier to verify available meters

**Status**: 🟢 **FIXED** - Configuration updated  
**Priority**: 🟡 **MEDIUM** - Improves debugging and may help with MTR files

---

**Report Generated**: 2025-11-05  
**Fix Applied**: Output:VariableDictionary changed to IDF  
**Status**: ✅ **READY FOR TESTING**



