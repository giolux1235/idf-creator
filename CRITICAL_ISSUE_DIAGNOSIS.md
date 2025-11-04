# Critical Issue: EnergyPlus Segmentation Fault

## Problem Identified

**EnergyPlus is crashing with exit code -11 (segmentation fault)**

### Log Evidence:
```
INFO:__main__:📊 EnergyPlus exit code: -11
INFO:__main__:📊 Error file content (0 chars)
INFO:__main__:📊 MTR lines: 0
INFO:__main__:📊 ESO content: 0 chars
```

## Root Cause

EnergyPlus is crashing before it can complete the simulation. This explains:
- Why error file is empty (0 chars)
- Why MTR file has no data (0 lines)
- Why ESO file is empty (0 chars)
- Why SQLite extraction can't find data

## Why This Happens

Exit code -11 (SIGSEGV) typically indicates:
1. **Memory issues** - IDF file too large (5.2 MB)
2. **Invalid IDF structure** - Corrupted or malformed IDF
3. **Resource limits** - Railway container running out of memory
4. **IDF file issues** - Missing required objects or invalid geometry

## The IDF File

- **Size**: 5,250,487 bytes (5.2 MB)
- **Generated**: By IDF Creator API
- **Status**: May have issues causing crash

## Solutions

### 1. Check IDF File Validity
- Verify all required objects are present
- Check for invalid geometry
- Validate RunPeriod configuration
- Ensure all schedules are complete

### 2. Check Memory Limits
- Railway container may have memory limits
- Large IDF files may exceed available memory
- Consider increasing container resources

### 3. Add Error Handling
- Check exit code before trying to parse
- If exit code != 0, return proper error
- Don't try to extract from crashed simulation

### 4. Test with Smaller IDF
- Try with minimal IDF first
- Verify EnergyPlus works with smaller files
- Gradually increase complexity

## Immediate Actions

1. **Check IDF File Quality**
   - Validate the generated IDF file
   - Check for missing required objects
   - Verify geometry is valid

2. **Check Railway Resources**
   - Verify container memory limits
   - Check if 5.2 MB IDF is too large
   - Consider resource upgrades

3. **Improve Error Handling**
   - Check exit code before parsing
   - Return clear error when EnergyPlus crashes
   - Don't attempt extraction from crashed simulation

## Expected Fix

The external API should:
1. Check EnergyPlus exit code
2. If exit code != 0, return error immediately
3. Only attempt extraction if simulation succeeded
4. Provide clear error message about crash

## Code Fix Needed

```python
# Check exit code first
if result.returncode != 0:
    return jsonify({
        'simulation_status': 'error',
        'error_message': f'EnergyPlus crashed with exit code {result.returncode}. This may indicate memory issues or invalid IDF file.',
        'energyplus_exit_code': result.returncode
    }), 200

# Only try extraction if exit code is 0
if result.returncode == 0:
    # Try SQLite extraction
    energy_results = extract_energy_from_sqlite(sql_file)
```

## Next Steps

1. Fix the IDF file generation to avoid crashes
2. Add exit code checking to external API
3. Test with smaller IDF files
4. Check Railway resource limits

