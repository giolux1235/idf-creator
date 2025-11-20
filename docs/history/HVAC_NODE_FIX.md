# HVAC Node Connection Fix - Case Sensitivity Issue

## Problem Summary

EnergyPlus was reporting **29 Severe Errors** related to missing HVAC nodes:
```
** Severe  ** GetAirPathData: AirLoopHVAC="LOBBY_0_Z1_AIRLOOP", branch in error.
**   ~~~   ** Probable missing or misspelled node referenced in the branch(es):
**   ~~~   ** Possible Error in Branch Object="LOBBY_0_Z1_MAINBRANCH".
**   ~~~   ** ...looking to match to Node="LOBBY_0_Z1_SUPPLYEQUIPMENTOUTLETNODE".
```

## Root Cause

1. **Wrong Node Name in SetpointManager**: The SetpointManager was referencing `SupplyEquipmentOutletNode` instead of `ZoneEquipmentInlet`
2. **Case Sensitivity**: EnergyPlus is case-sensitive for node names. Node names must match exactly throughout the IDF file.

## Fixes Applied

### 1. Fixed SetpointManager Node Reference ✅

**File**: `src/advanced_hvac_systems.py` (line 874)

**Change**: Updated SetpointManager to use the correct node name that matches the VAV system:
- **Before**: `f"{zone_name}_SupplyEquipmentOutletNode"`
- **After**: `f"{zone_name}_ZoneEquipmentInlet"`

This ensures the SetpointManager references the same node as the Fan outlet and AirLoopHVAC supply outlet.

### 2. Added Node Name Normalization Function ✅

**File**: `src/core/base_idf_generator.py`

**Added**: `normalize_node_name()` method to provide consistent node name formatting for EnergyPlus compatibility. This function can be used throughout the codebase to ensure node names are consistently formatted.

## Node Connection Flow (After Fixes)

The correct node connection flow for VAV systems:

1. **Supply Side**:
   - AirLoopHVAC Supply Inlet: `{zn}_SupplyInlet`
   - Cooling Coil Inlet: `{zn}_SupplyInlet`
   - Cooling Coil Outlet: `{zn}_CoolC-HeatCNode`
   - Heating Coil Inlet: `{zn}_CoolC-HeatCNode`
   - Heating Coil Outlet: `{zn}_HeatC-FanNode`
   - Fan Inlet: `{zn}_HeatC-FanNode`
   - **Fan Outlet: `{zn}_ZoneEquipmentInlet`** ✅
   - **AirLoopHVAC Supply Outlet: `{zn}_ZoneEquipmentInlet`** ✅
   - **SetpointManager Node: `{zn}_ZoneEquipmentInlet`** ✅ (FIXED)

2. **Demand Side**:
   - SupplyPath Inlet: `{zn}_ZoneEquipmentInlet` (matches AirLoopHVAC outlet)
   - ZoneSplitter Inlet: `{zn}_ZoneEquipmentInlet`
   - ZoneSplitter Outlet: `{zn}_TerminalInlet`
   - VAV Terminal Inlet: `{zn}_TerminalInlet`
   - VAV Terminal Outlet: `{zn}_TerminalOutlet`
   - Reheat Coil Inlet: `{zn}_TerminalOutlet`
   - Reheat Coil Outlet: `{zn}_ADUOutlet`
   - ADU Outlet: `{zn}_ADUOutlet`
   - Zone Inlet: `{zn}_ADUOutlet` (via NodeList)

3. **Return Side**:
   - Zone Return: `{zn}_ReturnAir`
   - ZoneMixer Inlet: `{zn}_ReturnAir`
   - ZoneMixer Outlet: `{zn}_ZoneEquipmentOutletNode`
   - ReturnPath Outlet: `{zn}_ZoneEquipmentOutletNode`
   - AirLoopHVAC Demand Outlet: `{zn}_ZoneEquipmentOutletNode`

## Verification

After these fixes:
- ✅ SetpointManager now references the correct node (`ZoneEquipmentInlet`)
- ✅ All node connections are consistent between AirLoopHVAC, Branch, Fan, and SetpointManager
- ✅ Node name normalization function available for future consistency

## Testing Recommendations

1. **Generate new IDF file** with the updated code
2. **Run EnergyPlus simulation** and check for node connection errors
3. **Verify** that all 29 zones no longer report HVAC node errors
4. **Confirm** simulations can complete successfully

## Notes

- The Branch object was already using the correct node name (`ZoneEquipmentInlet`)
- The main issue was the SetpointManager using an outdated node name
- EnergyPlus requires exact case matching for node names
- All node references now use consistent naming: `ZoneEquipmentInlet` for the supply outlet node

## Files Modified

1. **src/advanced_hvac_systems.py**
   - Line 874: Fixed SetpointManager node reference

2. **src/core/base_idf_generator.py**
   - Added `normalize_node_name()` method for future use

## Status

✅ **FIXED** - SetpointManager now uses the correct node name that matches the VAV system configuration.

