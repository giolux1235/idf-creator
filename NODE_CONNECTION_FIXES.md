# Node Connection Fixes Applied

**Date**: 2025-11-06  
**Issue**: "Node connection errors not checked - most system input has not been read"

## Root Cause Analysis

The warning "Node connection errors not checked - most system input has not been read" appears because EnergyPlus stops reading the input file when it encounters fatal errors (like missing weather file). This prevents EnergyPlus from validating node connections.

However, analysis of the code revealed actual node connection mismatches that would cause errors even with a valid weather file.

## Fixes Applied

### 1. AirLoopHVAC Supply Outlet Node Mismatch ✅

**Problem**: The AirLoopHVAC `supply_side_outlet_node_names` was set to `{zn}_SupplyEquipmentOutletNode`, but the SupplyPath `supply_air_path_inlet_node_name` was set to `{zn}_ZoneEquipmentInlet`. These must match for the supply side to connect to the demand side.

**Fix**: Updated `src/advanced_hvac_systems.py` line 310:
```python
# Before:
'supply_side_outlet_node_names': [f"{zn}_SupplyEquipmentOutletNode"]

# After:
'supply_side_outlet_node_names': [f"{zn}_ZoneEquipmentInlet"]  # Must match SupplyPath inlet!
```

### 2. Fan Outlet Node Mismatch ✅

**Problem**: The Fan outlet node was set to `{zn}_SupplyEquipmentOutletNode`, but it must match the AirLoopHVAC supply outlet node.

**Fix**: Updated `src/advanced_hvac_systems.py` line 320:
```python
# Before:
'air_outlet_node_name': f"{zn}_SupplyEquipmentOutletNode"

# After:
'air_outlet_node_name': f"{zn}_ZoneEquipmentInlet"  # Must match AirLoopHVAC supply outlet!
```

### 3. Branch Fan Outlet Node Mismatch ✅

**Problem**: The Branch object for the Fan component had an outlet node that didn't match the actual Fan outlet node.

**Fix**: Updated `src/professional_idf_generator.py` line 825:
```python
# Before:
{'type': 'Fan:VariableVolume', 'name': fan_name,
 'inlet': f"{zone_name}_HeatC-FanNode", 'outlet': f"{zone_name}_SupplyEquipmentOutletNode"}

# After:
{'type': 'Fan:VariableVolume', 'name': fan_name,
 'inlet': f"{zone_name}_HeatC-FanNode", 'outlet': f"{zone_name}_ZoneEquipmentInlet"}
```

## Node Connection Flow (After Fixes)

The correct node connection flow for VAV systems is now:

1. **Supply Side**:
   - AirLoopHVAC Supply Inlet: `{zn}_SupplyInlet`
   - Cooling Coil Inlet: `{zn}_SupplyInlet`
   - Cooling Coil Outlet: `{zn}_CoolC-HeatCNode`
   - Heating Coil Inlet: `{zn}_CoolC-HeatCNode`
   - Heating Coil Outlet: `{zn}_HeatC-FanNode`
   - Fan Inlet: `{zn}_HeatC-FanNode`
   - Fan Outlet: `{zn}_ZoneEquipmentInlet` ✅ (Fixed)
   - AirLoopHVAC Supply Outlet: `{zn}_ZoneEquipmentInlet` ✅ (Fixed)

2. **Demand Side**:
   - SupplyPath Inlet: `{zn}_ZoneEquipmentInlet` ✅ (Matches AirLoopHVAC outlet)
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

## Files Modified

1. `src/advanced_hvac_systems.py`
   - Line 310: Fixed AirLoopHVAC supply outlet node
   - Line 320: Fixed Fan outlet node

2. `src/professional_idf_generator.py`
   - Line 825: Fixed Branch Fan outlet node

## Verification

The node connection warning "Node connection errors not checked - most system input has not been read" will still appear when running without a weather file because EnergyPlus stops reading input after the weather file error. However, the actual node connection issues have been fixed.

**To fully verify the fixes**, run a simulation with a valid weather file. The node connection errors should be resolved.

## Expected Result

Once a weather file is provided:
- ✅ AirLoopHVAC supply outlet correctly connects to SupplyPath inlet
- ✅ Fan outlet correctly matches AirLoopHVAC supply outlet
- ✅ All node connections are consistent throughout the HVAC system
- ✅ No node connection errors should appear in the error file

## Notes

- The ConnectorList is correctly left empty for single-zone systems (handled by formatter)
- All node names are now consistent between AirLoopHVAC, Branch, and component objects
- The fixes ensure proper connection between supply side and demand side of the air loop


