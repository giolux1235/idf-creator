# EnergyPlus Fix Validation Scripts

This directory contains validation scripts to ensure all critical EnergyPlus fixes have been properly applied.

## Scripts Overview

### 1. `validate_code_fixes.py`
Validates that all fixes are properly implemented in the source code.

**Checks:**
- ✅ AirLoopHVAC uses `SupplyOutlet` (not `ZoneEquipmentInlet`) for supply outlet
- ✅ Version is set to 24.2 in `ProfessionalIDFGenerator`
- ✅ Ceiling tilt fix is implemented (`fix_vertex_ordering_for_ceiling`)
- ✅ Zone floor area is explicitly set
- ✅ Duplicate node validation exists
- ✅ Branch Fan outlet uses correct fallback

**Usage:**
```bash
python validate_code_fixes.py
```

### 2. `validate_energyplus_fixes.py`
Validates generated IDF files for critical errors.

**Checks:**
- ✅ AirLoopHVAC duplicate node names (SupplyOutlet vs ZoneEquipmentInlet)
- ✅ Version mismatch (should be 24.2, not 25.1)
- ✅ Ceiling tilt angles (should be ~0°, not 180°)
- ✅ Zone floor area consistency
- ✅ Node connection validation

**Usage:**
```bash
# Validate only
python validate_energyplus_fixes.py building.idf

# Validate and auto-fix
python validate_energyplus_fixes.py building.idf --fix

# Validate and save fixed file
python validate_energyplus_fixes.py building.idf --fix --output building_fixed.idf
```

### 3. `validate_all_fixes.py`
Master script that runs both code and IDF validation.

**Usage:**
```bash
# Validate code only
python validate_all_fixes.py --code

# Validate IDF file only
python validate_all_fixes.py --idf building.idf

# Validate both
python validate_all_fixes.py --code --idf building.idf

# Validate and fix IDF
python validate_all_fixes.py --idf building.idf --fix
```

## Fixes Validated

### 1. AirLoopHVAC Duplicate Node Fix (CRITICAL)
**Problem:** Same node used for both Supply Side Outlet and Demand Side Inlet.

**Fix:**
- Supply Side Outlet: `{ZONE}_SupplyOutlet`
- Demand Side Inlet: `{ZONE}_ZoneEquipmentInlet`

**Validation:**
- Code: Checks `advanced_hvac_systems.py` uses `SupplyOutlet`
- IDF: Checks AirLoopHVAC objects don't have duplicate nodes

### 2. Version Mismatch Fix
**Problem:** IDF version 25.1 doesn't match EnergyPlus 24.2.0.

**Fix:**
- Set version to 24.2 in `ProfessionalIDFGenerator`

**Validation:**
- Code: Checks `__init__` uses `version="24.2"`
- IDF: Checks Version object is 24.2

### 3. Ceiling Tilt Fix
**Problem:** Ceiling surfaces have tilt 180° (upside down).

**Fix:**
- Use `fix_vertex_ordering_for_ceiling()` to ensure tilt ~0°

**Validation:**
- Code: Checks function exists and is used
- IDF: Checks ceiling surfaces don't have tilt ~180°

### 4. Zone Floor Area Fix
**Problem:** Zone floor area not explicitly set, causing mismatches.

**Fix:**
- Explicitly set floor area from `zone.area` in `generate_zone_object()`

**Validation:**
- Code: Checks floor area is set explicitly
- IDF: Checks Zone objects have explicit floor area (not autocalculate)

### 5. Duplicate Node Validation
**Problem:** No validation to prevent duplicate nodes.

**Fix:**
- Added validation in `format_hvac_object()` to detect and fix duplicates

**Validation:**
- Code: Checks validation logic exists
- IDF: Checks no duplicate nodes in AirLoopHVAC objects

## Running Validation

### Quick Check (Code Only)
```bash
python validate_code_fixes.py
```

### Full Validation (Code + IDF)
```bash
# First, generate an IDF file
python main.py create_idf --address "123 Main St, Chicago, IL" --output test.idf

# Then validate
python validate_all_fixes.py --code --idf test.idf
```

### Continuous Integration
Add to your CI/CD pipeline:
```bash
# Validate code before commit
python validate_code_fixes.py || exit 1

# Validate generated IDFs in tests
python validate_energyplus_fixes.py test_outputs/*.idf || exit 1
```

## Expected Results

### Code Validation
```
✅ ALL CHECKS PASSED

✅ PASSED CHECKS (7):
   ✅ AirLoopHVAC uses SupplyOutlet for supply outlet
   ✅ ProfessionalIDFGenerator uses version 24.2
   ✅ Ceiling tilt fix function is used
   ✅ Ceiling tilt fix ensures tilt ~0° (not 180°)
   ✅ Duplicate node validation exists
   ✅ Duplicate node check logic is implemented
   ✅ Branch Fan outlet fallback uses SupplyOutlet
```

### IDF Validation (Passing)
```
✅ VALIDATION PASSED - No critical errors found
```

### IDF Validation (With Issues)
```
❌ VALIDATION FAILED - Critical errors found

🔴 ERRORS (1):
  1. DUPLICATE_NODE
     AirLoopHVAC "LOBBY_0_Z1_AirLoop": Supply outlet and demand inlet both use "LOBBY_0_Z1_ZONEEQUIPMENTINLET"
     Line: 1234
```

## Auto-Fixing Issues

The IDF validator can automatically fix some issues:

```bash
python validate_energyplus_fixes.py building.idf --fix
```

**Fixes Applied:**
- Version mismatch (changes 25.1 → 24.2)
- Duplicate nodes (changes supply outlet to SupplyOutlet)

**Note:** Auto-fix creates a new file (`.idf.fixed` by default) and does not modify the original.

## Integration with Testing

### Pre-commit Hook
Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
python validate_code_fixes.py || exit 1
```

### Test Suite Integration
```python
import subprocess
import pytest

def test_code_fixes():
    """Test that all code fixes are properly implemented"""
    result = subprocess.run(
        ['python', 'validate_code_fixes.py'],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "Code validation failed"

def test_idf_validation(idf_file):
    """Test that generated IDF passes validation"""
    result = subprocess.run(
        ['python', 'validate_energyplus_fixes.py', idf_file],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"IDF validation failed: {result.stdout}"
```

## Troubleshooting

### "File not found" errors
Make sure you're running from the project root directory.

### Validation fails but code looks correct
- Check for case sensitivity issues
- Verify regex patterns match your code style
- Check for whitespace differences

### IDF validation shows false positives
- Some warnings are informational only
- Check if the issue actually affects simulation
- Use `--fix` to auto-correct if safe

## Contributing

When adding new fixes:
1. Update the relevant validator script
2. Add test cases
3. Update this README
4. Run validation to ensure it passes

## References

- [Error Analysis Report](./CURRENT_STATUS_FINAL.md) - Original error analysis
- [EnergyPlus Documentation](https://energyplus.net/documentation) - Official EnergyPlus docs

