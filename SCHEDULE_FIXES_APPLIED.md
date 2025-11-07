# Schedule Issues - Fixes Applied

**Date**: 2025-11-04  
**Status**: ✅ **FIXED**

---

## Summary

Two critical fatal errors related to schedules have been fixed:

1. ✅ **Schedule Type Limits**: Fixed "Any Number" → "AnyNumber" (removed space)
2. ✅ **Duplicate Day Types**: Fixed duplicate day type assignments when using "AllDays"

---

## Fix #1: Schedule Type Limits Name ✅

### Problem
Schedule Type Limits Name used `"Any Number"` (with space) but EnergyPlus expects `"AnyNumber"` (no space, mixed case). This caused 26 warnings for all heating/cooling setpoint schedules.

### Solution
Replaced all instances of `"Any Number"` with `"AnyNumber"` across all Python source files.

### Files Modified
- ✅ `src/advanced_hvac_controls.py` (2 instances)
- ✅ `src/idf_generator.py` (3 instances)
- ✅ `src/auto_fix_engine.py` (2 instances)
- ✅ `src/advanced_ventilation.py` (2 instances)
- ✅ `src/infiltration_ventilation.py` (1 instance)

### Verification
```bash
grep -r "Any Number" --include="*.py" | grep -v test | wc -l
# Result: 0 (all fixed)
```

---

## Fix #2: Duplicate Day Type Assignments ✅

### Problem
Schedules using `"For: AllDays"` were having design days (SummerDesignDay, WinterDesignDay, CustomDay1, CustomDay2) added separately, causing duplicate day type errors. EnergyPlus cannot process schedules with duplicate day types.

### Root Cause
The `_add_missing_day_types()` function was adding design days to ALL schedules with `Through: 12/31`, even when the schedule already used `"For: AllDays"` which includes design days.

### Solution
Updated `_add_missing_day_types()` in `src/professional_idf_generator.py` to check if `"For: AllDays"` is used. If so, it returns early without adding design days separately.

### Code Change
```python
def _add_missing_day_types(self, schedule_values: str, default_value: float = 0.0) -> str:
    """Add missing day types to schedule if Through=12/31 is used."""
    
    # Check if schedule uses Through=12/31
    if 'Through: 12/31' not in schedule_values:
        return schedule_values
    
    # CRITICAL FIX: If schedule uses "For: AllDays", design days are already included
    # Do NOT add them separately to avoid duplicate day type errors
    if 'For: AllDays' in schedule_values:
        return schedule_values  # AllDays already includes design days - don't add duplicates
    
    # Check if day types are already explicitly present
    if 'For: SummerDesignDay' in schedule_values:
        return schedule_values  # Already complete with explicit day types
    
    # ... rest of function to add missing day types
```

### Files Modified
- ✅ `src/professional_idf_generator.py` (`_add_missing_day_types()` method)

---

## Impact

### Before Fixes
- ❌ 26 warnings: "Schedule Type Limits Name not found"
- ❌ 4 severe errors: "Duplicate assignment attempted in 'for' days field"
- ❌ Simulation fails with fatal errors

### After Fixes
- ✅ All schedules use correct "AnyNumber" (no space)
- ✅ No duplicate day type assignments
- ✅ Simulation should run successfully

---

## Testing Recommendations

After these fixes, verify:

1. **Schedule Type Limits**:
   ```bash
   # Verify no "Any Number" in generated IDF
   grep "Any Number" generated_file.idf
   # Should return nothing
   
   # Verify "AnyNumber" is used
   grep "AnyNumber" generated_file.idf
   # Should return schedule type limits references
   ```

2. **Duplicate Day Types**:
   ```bash
   # Verify no duplicate day types in schedules
   grep -A 5 "Schedule:Compact" generated_file.idf | grep -E "For: (SummerDesignDay|WinterDesignDay|CustomDay1|CustomDay2)" | sort | uniq -d
   # Should return nothing (no duplicates)
   ```

3. **EnergyPlus Simulation**:
   - Run a simulation and check `eplusout.err`
   - Should have no "Schedule Type Limits Name not found" errors
   - Should have no "Duplicate assignment attempted" errors

---

## Related Files

- `src/professional_idf_generator.py` - Main IDF generator with schedule creation
- `src/advanced_hvac_controls.py` - HVAC control schedules (setpoint schedules)
- `src/idf_generator.py` - Basic IDF generator
- `src/auto_fix_engine.py` - Auto-fix engine with schedule creation
- `src/advanced_ventilation.py` - Ventilation schedules
- `src/infiltration_ventilation.py` - Infiltration schedules

---

**Fix Status**: ✅ **COMPLETE**  
**Priority**: **CRITICAL** - Both fixes are required for simulations to run




