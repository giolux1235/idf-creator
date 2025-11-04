# Missing IDF Features - What Senior Engineers Include

**Date**: 2025-10-31  
**Focus**: IDF file content features that senior engineers use but IDF Creator doesn't

---

## Executive Summary

**Current IDF Creator**: Generates basic, functional IDF files  
**Senior Engineer IDF**: Includes advanced features for accuracy and realism  
**Gap**: Missing 15-20 advanced IDF features

---

## 🔴 Critical Missing Features (Priority 1)

### **1. Economizer Controls** ⚠️ HIGH PRIORITY

**What Senior Engineers Include**:
```idf
Controller:OutdoorAir,
  Main OA Controller,           !- Name
  Main OA System,                !- AirLoopHVAC Name
  ,                              !- Controller Outdoor Air 1 Name
  ,                              !- Controller Mechanical Ventilation 1 Name
  FixedMinimumMaximum,          !- Economizer Control Type
  Lockout,                      !- Economizer Control Action Type
  12.8,                         !- Economizer Maximum Limit Dry-Bulb Temperature
  ,                              !- Economizer Maximum Limit Enthalpy
  ,                              !- Economizer Maximum Limit Dewpoint Temperature
  NoLockout,                    !- Economizer Minimum Limit Dry-Bulb Temperature
  ZoneDryBulb,                  !- Economizer High Limit Control Signal Type
  ,                              !- Economizer Control Method
  Enthalpy,                     !- High Humidity Control
  ,                              !- Low Humidity Control Schedule Name
  MinimumFlowWithScroll,        !- Night Ventilation
  NoLockout,                    !- Heat Recovery Bypass Control Type
  ;
```

**Current Status**: ❌ Not implemented  
**Impact**: Missing 5-15% energy savings from free cooling  
**Priority**: HIGH - Very common in modern buildings

---

### **2. Demand Control Ventilation (DCV)** ⚠️ HIGH PRIORITY

**What Senior Engineers Include**:
```idf
Controller:MechanicalVentilation,
  Main OA Controller Mech Vent 1,  !- Name
  Main OA Controller,              !- Controller:OutdoorAir Name
  Standard62.1VentilationRateProcedure, !- Ventilation Calculation Method
  ,                                 !- Zone Maximum Outdoor Air Fraction
  ,                                 !- Zone Primary Outdoor Air Fraction
  ZoneSum,                         !- Design Specification Outdoor Air Object 1 Name
  DesignSpecification:OutdoorAir,
    DCV_OA_Spec,                   !- Name
    Sum,                            !- Outdoor Air Method
    ,                               !- Outdoor Air Flow per Person
    ,                               !- Outdoor Air Flow per Zone Floor Area
    ,                               !- Outdoor Air Flow per Zone
    ,                               !- Outdoor Air Flow Air Changes per Hour
    ,                               !- Outdoor Air Flow Rate per Person
    ,                               !- Outdoor Air Flow Rate per Zone Floor Area
    ,                               !- Outdoor Air Flow Rate per Zone
    ,                               !- Outdoor Air Flow Rate per Air Changes per Hour
    ,                               !- CO2 Concentration
    Yes,                            !- Demand Controlled Ventilation Type
    ZoneControl:CO2,                !- Demand Controlled Ventilation Availability Schedule Name
    ;
```

**Current Status**: ❌ Not implemented  
**Impact**: Missing 10-30% HVAC energy savings from reduced ventilation  
**Priority**: HIGH - Required in most modern codes

---

### **3. Advanced Setpoint Managers** ⚠️ HIGH PRIORITY

**What Senior Engineers Include**:
```idf
SetpointManager:Scheduled:DualSetpoint,
  Main Supply Air Dual SP Manager,  !- Name
  Temperature,                     !- Control Variable
  Supply Air Temp Heating Schedule, !- High Setpoint Schedule Name
  Supply Air Temp Cooling Schedule, !- Low Setpoint Schedule Name
  Main Supply Air Outlet Node;      !- Setpoint Node or NodeList Name

SetpointManager:OutdoorAirReset,
  Main OA Reset Manager,            !- Name
  Temperature,                     !- Control Variable
  15.6,                            !- Setpoint at Outdoor Low Temperature
  -6.7,                            !- Outdoor Low Temperature
  21.1,                            !- Setpoint at Outdoor High Temperature
  26.7,                            !- Outdoor High Temperature
  Main Supply Air Outlet Node;      !- Setpoint Node or NodeList Name
```

**Current Status**: ⚠️ Basic setpoint managers only (fixed temperatures)  
**Impact**: Missing reset strategies save 5-10% energy  
**Priority**: HIGH - Standard practice for efficiency

---

### **4. Internal Mass Objects** ⚠️ MEDIUM PRIORITY

**What Senior Engineers Include**:
```idf
InternalMass,
  Zone1_InternalMass,          !- Name
  Zone1,                       !- Construction Name
  Zone1,                       !- Zone or ZoneList Name
  ,                            !- Surface Area
  ,                            !- Surface Area per Zone Floor Area
  0.5,                         !- Surface Area per Person
  ,                            !- Thermally Active
  ,                            !- Material Name
  ,                            !- Solar and Visible Absorptance
  ,                            !- Surface Roughness
  ;
```

**Current Status**: ❌ Not implemented  
**Impact**: Missing thermal mass effects (10-20% load differences)  
**Priority**: MEDIUM - Important for accuracy, especially in heavy construction

---

### **5. Daylighting Controls** ⚠️ MEDIUM PRIORITY

**What Senior Engineers Include**:
```idf
Daylighting:Controls,
  Zone1_Daylighting,           !- Name
  Zone1,                       !- Zone Name
  Continuous,                  !- Daylighting Method
  1,                           !- Availability Schedule Name
  500,                         !- Lighting Control Type
  1.0,                         !- Minimum Input Power Fraction for Continuous Dimming Control
  0.2,                         !- Minimum Light Output Fraction for Continuous Dimming Control
  ,                            !- Number of Stepped Control Steps
  ,                            !- Probability Lighting will be Reset When Needed in Manual Stepped Control
  ,                            !- Glare Calculation Daylighting Reference Point Index
  ,                            !- Glare Calculation Azimuth Angle of View Direction Clockwise from Zone y-Axis
  ,                            !- Maximum Allowable Discomfort Glare Index
  1.0,                         !- Illuminance Setpoint at Reference Point
  DaylRefPt1;                  !- Daylighting Reference Point 1 Name

Daylighting:ReferencePoint,
  DaylRefPt1,                  !- Name
  Zone1_Daylighting,           !- Zone Name
  2.0,                         !- X-Coordinate of Reference Point
  2.0,                         !- Y-Coordinate of Reference Point
  0.8,                         !- Z-Coordinate of Reference Point
  0.5;                         !- Fraction of Zone Controlled by Reference Point
```

**Current Status**: ❌ Not implemented  
**Impact**: Missing 20-40% lighting energy savings  
**Priority**: MEDIUM-HIGH - Significant savings potential

---

### **6. Window Shades/Blinds** ⚠️ MEDIUM PRIORITY

**What Senior Engineers Include**:
```idf
WindowMaterial:Shade,
  Interior Shade,              !- Name
  OnIfScheduleAllows,          !- Shade Control Type
  Interior Shade Schedule,     !- Schedule Name
  0.6,                         !- Transmittance
  0.2,                         !- Reflectance
  0.6,                         !- Visible Transmittance
  0.2,                         !- Visible Reflectance
  0.9,                         !- Infrared Transmittance
  0.1,                         !- Infrared Emissivity
  0.05;                        !- Thickness

FenestrationSurface:Detailed,
  Zone1_Window_1,               !- Name
  Window,                       !- Surface Type
  Clear 3mm,                    !- Construction Name
  Zone1_Wall_1,                 !- Building Surface Name
  ,                             !- Outside Boundary Condition Object
  0,                            !- View Factor to Ground
  Interior Shade,               !- Shading Control Name
  ,                             !- Frame and Divider Name
  1.0,                          !- Multiplier
  4,                            !- Number of Vertices
  ...                           !- Vertices

ShadingControl,
  Interior Shade Control,       !- Name
  Zone1_Window_1,               !- Zone Name
  OnIfHighSolarOnWindow,       !- Shading Control Type
  Interior Shade Schedule,      !- Schedule Name
  200,                          !- Setpoint
  W/m2,                         !- Shading Control Is Scheduled
  Glare,                        !- Shading Control Type
  ,                             !- Multiple Surface Control Type
  Zone1_Window_1;               !- Fenestration Surface 1 Name
```

**Current Status**: ❌ Not implemented  
**Impact**: Missing solar heat gain control (5-15% cooling load reduction)  
**Priority**: MEDIUM - Important for cooling-dominated climates

---

## 🟡 Important Missing Features (Priority 2)

### **7. Advanced Schedules (Seasonal Variations)**

**Current**: Fixed schedules year-round  
**Engineers Use**: Seasonal variations, occupancy-based, demand response

```idf
Schedule:Compact,
  Occupancy_Summer,             !- Name
  Any Number,                   !- Schedule Type Limits Name
  Through: 6/30,                !- Field 1
  For: Weekdays,                !- Field 2
  Until: 07:00,0.0,
  Until: 08:00,0.5,
  Until: 18:00,1.0,
  Until: 24:00,0.1,
  For: Weekends,                !- Field 3
  Until: 24:00,0.1,
  Through: 12/31,               !- Field 4
  For: Weekdays,
  Until: 07:00,0.0,
  Until: 08:00,0.3,              !- Lower occupancy in winter
  Until: 17:00,1.0,
  Until: 24:00,0.1;
```

**Status**: ⚠️ Basic schedules only  
**Impact**: Missing seasonal accuracy (5-10% differences)

---

### **8. Chilled Water Central Plant**

**Current**: Only DX cooling coils  
**Engineers Use**: Full central plant with chillers, cooling towers, pumps

```idf
Chiller:Electric:EIR,
  Main Chiller,                 !- Name
  Main Chiller ChW Loop Inlet Node, !- Chilled Water Inlet Node Name
  Main Chiller ChW Loop Outlet Node, !- Chilled Water Outlet Node Name
  500000,                       !- Reference Capacity {W}
  5.0,                          !- Reference COP
  7.0,                          !- Reference Leaving Chilled Water Temperature
  29.4,                         !- Reference Leaving Condenser Water Temperature
  0.66,                         !- Reference Chilled Water Flow Rate
  0.85,                         !- Reference Condenser Water Flow Rate
  Chiller CAPFT,                !- Cooling Capacity Function of Temperature Curve Name
  Chiller EIRFT,                !- Electric Input to Cooling Output Ratio Function of Temperature Curve Name
  Chiller EIRFPLR,              !- Electric Input to Cooling Output Ratio Function of PLR Curve Name
  0.1,                          !- Minimum Part Load Ratio
  1.0,                          !- Maximum Part Load Ratio
  1.0,                          !- Optimum Part Load Ratio
  0.1,                          !- Minimum Unloading Ratio
  Chilled Water Loop;           !- Chilled Water Loop Name
```

**Status**: ❌ Not implemented (mentioned but not working)  
**Impact**: Missing for large buildings (hospitals, offices >50,000 ft²)

---

### **9. Energy Recovery Ventilation (ERV/HRV)**

**What Engineers Include**:
```idf
HeatExchanger:AirToAir:SensibleAndLatent,
  Main ERV,                     !- Name
  Main OA System,               !- Primary Air Stream Inlet Node Name
  Main ERV Supply Outlet,       !- Primary Air Stream Outlet Node Name
  Main ERV Exhaust Inlet,       !- Secondary Air Stream Inlet Node Name
  Main ERV Exhaust Outlet,       !- Secondary Air Stream Outlet Node Name
  Main ERV Availability Schedule, !- Availability Schedule Name
  0.75,                         !- Nominal Supply Air Flow Rate
  0.75,                         !- Nominal Exhaust Air Flow Rate
  0.7,                          !- Nominal Sensible Effectiveness
  0.65,                         !- Nominal Latent Effectiveness
  1000,                         !- Supply Air Stream Rated Flow Rate
  1000,                         !- Exhaust Air Stream Rated Flow Rate
  0.7,                          !- Supply Air Stream Rated Sensible Effectiveness
  0.65,                         !- Exhaust Air Stream Rated Latent Effectiveness
  0,                            !- Supply Air Stream Rated Electric Power
  0;                            !- Exhaust Air Stream Rated Electric Power
```

**Status**: ❌ Not implemented  
**Impact**: Missing 20-40% ventilation energy recovery (significant for cold climates)

---

### **10. Advanced Performance Curves**

**Current**: Basic curves only  
**Engineers Use**: Realistic part-load curves, degradation curves

```idf
Curve:Biquadratic,
  Chiller CAPFT,                !- Name
  0.042875793,                  !- Coefficient1 Constant
  0.000545216,                  !- Coefficient2 x
  -0.000004048,                 !- Coefficient3 x**2
  0.018596914,                  !- Coefficient4 y
  -0.000153153,                 !- Coefficient5 y**2
  -0.000215764,                 !- Coefficient6 x*y
  5.0,                          !- Minimum Value of x
  10.0,                         !- Maximum Value of x
  24.0,                         !- Minimum Value of y
  35.0,                         !- Maximum Value of y
  0.0,                          !- Minimum Curve Output
  1.5;                          !- Maximum Curve Output
```

**Status**: ⚠️ Basic curves only  
**Impact**: Equipment efficiency accuracy (5-10% energy differences)

---

### **11. Zone Groups and Zone Lists**

**What Engineers Use**:
```idf
ZoneList,
  Office Zones,                 !- Name
  Zone1,
  Zone2,
  Zone3;

ZoneGroup,
  Office Zone Group,            !- Name
  Office Zones,                 !- Zone List Name
  1;                            !- Zone List Multiplier
```

**Status**: ⚠️ Limited (individual zones)  
**Impact**: Efficiency for large buildings, easier management

---

### **12. Ground Coupling**

**What Engineers Include**:
```idf
Site:GroundTemperature:BuildingSurface,
  18.0,                         !- January Ground Temperature
  18.0,                         !- February Ground Temperature
  18.0,                         !- March Ground Temperature
  18.0,                         !- April Ground Temperature
  18.0,                         !- May Ground Temperature
  18.0,                         !- June Ground Temperature
  18.0,                         !- July Ground Temperature
  18.0,                         !- August Ground Temperature
  18.0,                         !- September Ground Temperature
  18.0,                         !- October Ground Temperature
  18.0,                         !- November Ground Temperature
  18.0;                         !- December Ground Temperature
```

**Status**: ❌ Not implemented  
**Impact**: Missing ground heat transfer (important for basements, slabs)

---

### **13. External Shading Devices**

**What Engineers Include**:
```idf
Shading:Building:Detailed,
  South Overhang,               !- Name
  4,                            !- Number of Vertices
  0.0, 0.0, 3.0,                !- Vertex 1
  10.0, 0.0, 3.0,               !- Vertex 2
  10.0, 0.0, 4.0,               !- Vertex 3
  0.0, 0.0, 4.0;                !- Vertex 4

Shading:Site:Detailed,
  Adjacent Building,            !- Name
  4,                            !- Number of Vertices
  ...                           !- Vertices
```

**Status**: ❌ Not implemented  
**Impact**: Missing shading effects (5-15% cooling load)

---

### **14. Energy Management System (EMS)**

**What Engineers Use** (for advanced control):
```idf
EnergyManagementSystem:Sensor,
  Zone1_Temp_Sensor,            !- Name
  Zone1,                        !- Output:Variable or Output:Meter Index Key Name
  Zone Mean Air Temperature;    !- Output:Variable or Output:Meter Name

EnergyManagementSystem:Actuator,
  Zone1_Lights_Actuator,        !- Name
  Zone1_Lights,                 !- Actuated Component Unique Name
  Electric Lighting Power Level, !- Actuated Component Control Type
  Lighting Level;               !- Actuated Component Control Zone

EnergyManagementSystem:Program,
  Occupancy_Control_Program,     !- Name
  IF Zone1_Temp_Sensor > 25.0,
    SET Zone1_Lights_Actuator = 0.5,
  ENDIF;
```

**Status**: ❌ Not implemented  
**Impact**: Missing custom control logic (advanced applications)

---

### **15. Advanced Output Control**

**What Engineers Include**:
```idf
Output:Variable,
  *,                            !- Key Value
  Zone Mean Air Temperature,    !- Variable Name
  Timestep;                     !- Reporting Frequency

Output:Variable,
  *,
  Fan Electric Power,
  Hourly;

Output:Meter,
  Electricity:Facility,
  Hourly;
```

**Status**: ⚠️ Basic outputs only  
**Impact**: Missing detailed diagnostics and component-level analysis

---

### **16. Mixed-Mode Ventilation**

**What Engineers Include**:
```idf
ZoneVentilation:DesignFlowRate,
  Zone1_NaturalVent,            !- Name
  Zone1,                        !- Zone or ZoneList Name
  Natural Ventilation Schedule, !- Schedule Name
  AirChanges/Hour,              !- Design Flow Rate Calculation Method
  ,                             !- Design Flow Rate
  ,                             !- Flow per Zone Floor Area
  ,                             !- Flow per Exterior Surface Area
  4.0,                          !- Air Changes per Hour
  1.0,                          !- Constant Term Coefficient
  0.0,                          !- Temperature Term Coefficient
  0.2242,                       !- Velocity Term Coefficient
  0.0,                          !- Velocity Squared Term Coefficient
  18.0,                         !- Minimum Indoor Temperature
  40.0,                         !- Maximum Indoor Temperature
  -100,                         !- Delta Temperature
  100,                          !- Minimum Outdoor Temperature
  40.0,                         !- Maximum Outdoor Temperature
  0.0,                          !- Maximum Wind Speed;
```

**Status**: ❌ Not implemented  
**Impact**: Missing natural ventilation strategies (20-40% cooling savings in some climates)

---

## 📊 Priority Ranking for IDF Features

### **Tier 1: Critical for Accuracy** (Implement First)

1. **Economizer Controls** - 5-15% HVAC savings
2. **Demand Control Ventilation** - 10-30% ventilation savings  
3. **Advanced Setpoint Managers** - 5-10% from reset strategies
4. **Internal Mass** - 10-20% load accuracy improvement
5. **Daylighting Controls** - 20-40% lighting savings

**Implementation**: 6-8 weeks, $80K-$120K  
**Impact**: Match 85-90% of engineer IDF capabilities

### **Tier 2: Important for Realism** (Implement Second)

6. **Window Shades/Blinds** - 5-15% cooling reduction
7. **Advanced Schedules** - Seasonal accuracy
8. **Chilled Water Systems** - Large buildings
9. **Energy Recovery** - 20-40% ventilation energy
10. **Ground Coupling** - Basement/slab accuracy

**Implementation**: 8-10 weeks, $100K-$150K  
**Impact**: Match 95% of engineer IDF capabilities

### **Tier 3: Advanced Features** (Future)

11. External Shading
12. EMS Programming
13. Mixed-Mode Ventilation
14. Advanced Output Control
15. Zone Groups

---

## 🎯 Implementation Roadmap

### **Phase 1: Core Efficiency Features** (6-8 weeks)

1. Economizer Controls
2. Demand Control Ventilation
3. Advanced Setpoint Managers (outdoor air reset, dual setpoint)
4. Internal Mass Objects

**Result**: IDF files match 80% of engineer capabilities

### **Phase 2: Advanced Controls** (4-6 weeks)

5. Daylighting Controls
6. Window Shades/Blinds
7. Advanced Schedules (seasonal)
8. Energy Recovery Ventilation

**Result**: IDF files match 90% of engineer capabilities

### **Phase 3: Specialized Systems** (6-8 weeks)

9. Chilled Water Central Plant
10. Ground Coupling
11. External Shading
12. Advanced Performance Curves

**Result**: IDF files match 95%+ of engineer capabilities

---

## 💡 The Winning Combination

**To Beat Engineers on IDF Quality, Add**:

1. **Economizers** - Standard in modern buildings
2. **DCV** - Code-required, huge savings
3. **Setpoint Reset** - Standard efficiency practice
4. **Daylighting** - Major lighting savings
5. **Internal Mass** - Accuracy for heavy construction

**These 5 features alone would match 85-90% of what engineers include in professional IDF files.**

---

## 📋 Current vs. Target

| Feature | Current | Engineer | Target |
|---------|---------|----------|--------|
| **HVAC Systems** | VAV, PTAC, RTU | + Chilled Water, Heat Pumps | ✅ Tier 2 |
| **Controls** | Basic | + Economizer, DCV, Reset | ⚠️ Tier 1 |
| **Daylighting** | None | Photocell dimming | ⚠️ Tier 1 |
| **Internal Mass** | None | Furniture, partitions | ⚠️ Tier 1 |
| **Window Shades** | None | Blinds, shades | ⚠️ Tier 2 |
| **Schedules** | Fixed | Seasonal, occupancy-based | ⚠️ Tier 2 |
| **Energy Recovery** | None | ERV, HRV | ⚠️ Tier 2 |
| **Ground Coupling** | None | Basement, slab modeling | ⚠️ Tier 2 |

---

**Conclusion**: Focus on **Economizers, DCV, Setpoint Reset, Daylighting, and Internal Mass** first. These 5 features are the most common additions engineers make to basic IDF files for accuracy and efficiency.







