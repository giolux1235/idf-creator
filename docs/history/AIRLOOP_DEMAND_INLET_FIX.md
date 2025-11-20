# AirLoopHVAC Demand Side Inlet Node Fix

**Date**: November 7, 2025  
**Issue**: "An outlet node in AirLoopHVAC is not connected to any zone" and "Could not match ZoneEquipGroup Inlet Node to any Supply Air Path or controlled zone"

## Root Cause

The `AirLoopHVAC` object's `demand_side_inlet_node_names` was incorrectly set to `{zn}_ZoneEquipmentInlet` (the zone inlet node). However, this field should specify where air **ENTERS** the demand side from the supply side, which is the **ZoneSplitter outlet** (`{zn}_TerminalInlet`), not the zone inlet.

EnergyPlus uses `demand_side_inlet_node_names` to trace the connection from the supply side to the demand side. When it's set to the zone inlet node (which is at the END of the demand side), EnergyPlus cannot trace the connection path and reports that the outlet node is not connected to any zone.

## Fix Applied

**File**: `src/advanced_hvac_systems.py`  
**Line**: 315

**Before**:
```python
'demand_side_inlet_node_names': [normalize_node_name(f"{zn}_ZoneEquipmentInlet")],  # Demand side inlet (from zones)
```

**After**:
```python
'demand_side_inlet_node_names': [normalize_node_name(f"{zn}_TerminalInlet")],  # ✅ FIXED: Must be ZoneSplitter outlet (TerminalInlet), not zone inlet!
```

## Correct Node Connection Flow

The complete connection chain is now correct:

1. **Supply Side**:
   - AirLoopHVAC Supply Outlet: `{zn}_SupplyOutlet` ✅
   - SupplyPath Inlet: `{zn}_SupplyOutlet` ✅
   - ZoneSplitter Inlet: `{zn}_SupplyOutlet` ✅
   - ZoneSplitter Outlet: `{zn}_TerminalInlet` ✅

2. **Demand Side** (where air ENTERS from supply side):
   - AirLoopHVAC Demand Side Inlet: `{zn}_TerminalInlet` ✅ (ZoneSplitter outlet - where air enters demand side)
   - Terminal Inlet: `{zn}_TerminalInlet` ✅
   - Terminal Outlet: `{zn}_TerminalOutlet` ✅
   - Reheat Coil Inlet: `{zn}_TerminalOutlet` ✅
   - Reheat Coil Outlet: `{zn}_ZoneEquipmentInlet` ✅
   - ADU Outlet: `{zn}_ZoneEquipmentInlet` ✅
   - Zone Inlet (NodeList): `{zn}_ZoneEquipmentInlet` ✅

3. **Return Side**:
   - Zone Return: `{zn}_ReturnAir` ✅
   - ZoneMixer Inlet: `{zn}_ReturnAir` ✅
   - ZoneMixer Outlet: `{zn}_ZoneEquipmentOutletNode` ✅
   - AirLoopHVAC Demand Side Outlet: `{zn}_ZoneEquipmentOutletNode` ✅

## Key Understanding

The `demand_side_inlet_node_names` field in `AirLoopHVAC` specifies:
- **WHERE air ENTERS the demand side** (from the supply side)
- This is the **ZoneSplitter outlet** (`TerminalInlet`), not the zone inlet
- EnergyPlus uses this to trace the connection from supply to demand side

The zone inlet node (`ZoneEquipmentInlet`) is at the **END** of the demand side path, not the beginning.

## Expected Result

After this fix, EnergyPlus should be able to:
1. Trace the connection from AirLoopHVAC supply outlet → SupplyPath → ZoneSplitter → Demand side inlet
2. Recognize that the supply outlet is connected to zones through the demand side
3. Match the zone equipment inlet node to the SupplyPath
4. Eliminate both errors:
   - "An outlet node in AirLoopHVAC is not connected to any zone"
   - "Could not match ZoneEquipGroup Inlet Node to any Supply Air Path or controlled zone"

## Testing

To verify the fix:
1. Generate a new IDF file with the updated code
2. Run EnergyPlus simulation
3. Check that both errors are resolved
4. Verify that all zones are properly connected to their AirLoopHVAC systems

## Related Fixes

This fix works together with:
- SupplyPath name matching zone name (from `SUPPLYPATH_ZONE_CONNECTION_FIX.md`)
- Proper node connection chain throughout the system

Both fixes are required for EnergyPlus to properly connect zones to AirLoopHVAC systems.

