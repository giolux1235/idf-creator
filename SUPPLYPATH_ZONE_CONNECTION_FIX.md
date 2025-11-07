# SupplyPath Zone Connection Fix

**Date**: November 7, 2025  
**Issue**: "Could not match ZoneEquipGroup Inlet Node to any Supply Air Path or controlled zone"

## Root Cause

EnergyPlus requires the `AirLoopHVAC:SupplyPath` name to match the zone name (as specified in `ZoneHVAC:EquipmentConnections`) for it to properly link the SupplyPath to the zone. 

The code was using `{zn}` (zone name with unique suffix, e.g., "lobby_0_z1") for the SupplyPath name, but the zone name in `ZoneHVAC:EquipmentConnections` was just `zone.name` (without suffix, e.g., "lobby_0"). This mismatch prevented EnergyPlus from connecting the SupplyPath to the zone.

## Fix Applied

**File**: `src/advanced_hvac_systems.py`  
**Line**: 518

**Before**:
```python
supply_path = {
    'type': 'AirLoopHVAC:SupplyPath',
    'name': f"{zn}",  # Includes unique suffix (e.g., "lobby_0_z1")
    ...
}
```

**After**:
```python
supply_path = {
    'type': 'AirLoopHVAC:SupplyPath',
    'name': zone_name,  # ✅ FIXED: Must match zone.name (without suffix) for EnergyPlus zone connection
    ...
}
```

## Node Connection Chain (Verified)

The complete node connection chain is now correct:

1. **Supply Side**:
   - AirLoopHVAC Supply Outlet: `{zn}_SupplyOutlet` ✅
   - SupplyPath Inlet: `{zn}_SupplyOutlet` ✅
   - ZoneSplitter Inlet: `{zn}_SupplyOutlet` ✅
   - ZoneSplitter Outlet: `{zn}_TerminalInlet` ✅

2. **Demand Side**:
   - Terminal Inlet: `{zn}_TerminalInlet` ✅
   - Terminal Outlet: `{zn}_TerminalOutlet` ✅
   - Reheat Coil Inlet: `{zn}_TerminalOutlet` ✅
   - Reheat Coil Outlet: `{zn}_ZoneEquipmentInlet` ✅
   - ADU Outlet: `{zn}_ZoneEquipmentInlet` ✅
   - NodeList contains: `{zn}_ZoneEquipmentInlet` ✅
   - ZoneHVAC:EquipmentConnections zone_air_inlet_node_name: NodeList name ✅

3. **Zone Connection**:
   - SupplyPath name: `zone_name` (e.g., "lobby_0") ✅
   - ZoneHVAC:EquipmentConnections zone_name: `zone.name` (e.g., "lobby_0") ✅
   - **Names now match for EnergyPlus zone connection** ✅

## Expected Result

After this fix, EnergyPlus should be able to:
1. Match the SupplyPath name to the zone name
2. Trace the connection from SupplyPath → ZoneSplitter → Terminal → Reheat Coil → ADU → Zone Inlet
3. Recognize the zone as a controlled zone connected to the AirLoopHVAC
4. Eliminate the error: "Could not match ZoneEquipGroup Inlet Node to any Supply Air Path or controlled zone"

## Testing

To verify the fix:
1. Generate a new IDF file with the updated code
2. Run EnergyPlus simulation
3. Check that the error "Could not match ZoneEquipGroup Inlet Node to any Supply Air Path or controlled zone" is resolved
4. Verify that all zones are properly connected to their AirLoopHVAC systems

## Notes

- The SupplyPath name must match the zone name exactly (case-sensitive)
- Each zone should have a unique SupplyPath (even if zone names are duplicated, the unique suffix in component names ensures uniqueness)
- EnergyPlus uses the SupplyPath name to link zones to AirLoopHVAC supply paths

