"""
Professional IDF Generator for EnergyPlus
Integrates Advanced Geometry, Materials, Building Types, and HVAC Systems
"""

import os
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from .advanced_geometry_engine import AdvancedGeometryEngine, BuildingFootprint, ZoneGeometry
from .professional_material_library import ProfessionalMaterialLibrary
from .multi_building_types import MultiBuildingTypes
from .advanced_hvac_systems import AdvancedHVACSystems
from .hvac_plumbing import HVACPlumbing
from .advanced_hvac_controls import AdvancedHVACControls
from .shading_daylighting import ShadingDaylightingEngine
from .infiltration_ventilation import InfiltrationVentilationEngine
from .renewable_energy import RenewableEnergyEngine
from .equipment_catalog.adapters import bcl as bcl_adapter
from .equipment_catalog.translator.idf_translator import translate as translate_equipment


class ProfessionalIDFGenerator:
    """Professional-grade IDF generator with advanced features"""
    
    def __init__(self):
        self.version = "24.2"
        self.unique_names = set()
        
        # Initialize professional modules
        self.geometry_engine = AdvancedGeometryEngine()
        self.material_library = ProfessionalMaterialLibrary()
        self.building_types = MultiBuildingTypes()
        self.hvac_systems = AdvancedHVACSystems()
        self.hvac_plumbing = HVACPlumbing()
        self.advanced_controls = AdvancedHVACControls()
        self.shading_daylighting = ShadingDaylightingEngine()
        self.infiltration_ventilation = InfiltrationVentilationEngine()
        self.renewable_energy = RenewableEnergyEngine()
        self.construction_map = {}
    
    def _generate_unique_name(self, base_name: str) -> str:
        """Generate a unique object name in the IDF."""
        if base_name not in self.unique_names:
            self.unique_names.add(base_name)
            return base_name
        
        counter = 1
        while f"{base_name}_{counter}" in self.unique_names:
            counter += 1
        
        unique_name = f"{base_name}_{counter}"
        self.unique_names.add(unique_name)
        return unique_name
    
    def generate_professional_idf(self, address: str, building_params: Dict, 
                                location_data: Dict, documents: List[str] = None) -> str:
        """Generate professional-grade IDF with advanced features"""
        
        # Determine building type
        building_type = self._determine_building_type(building_params, documents)
        
        # Get building type template
        building_template = self.building_types.get_building_type_template(building_type)
        if not building_template:
            building_type = 'office'  # Default fallback
            building_template = self.building_types.get_building_type_template(building_type)
        
        # Estimate building parameters
        estimated_params = self.building_types.estimate_building_parameters(
            building_type, 
            building_params.get('total_area', 1000),
            building_params.get('stories', 3)
        )
        
        # Generate complex building footprint
        footprint = self._generate_complex_footprint(
            location_data, building_type, estimated_params
        )
        
        # Generate detailed zone layout
        zones = self.geometry_engine.generate_zone_layout(footprint, building_type)
        if not zones:
            print(f"⚠️  Warning: No zones generated. Footprint area: {footprint.polygon.area:.2f} m²")
        
        # Generate professional materials and constructions
        climate_zone = location_data.get('climate_zone', '3A')
        materials_used, constructions_used = self._select_professional_materials(
            building_type, climate_zone
        )
        # Build construction name mapping for surfaces/windows
        wall_constr = self.material_library.get_construction_assembly(building_type, climate_zone, 'wall').name
        roof_constr = self.material_library.get_construction_assembly(building_type, climate_zone, 'roof').name
        floor_constr = self.material_library.get_construction_assembly(building_type, climate_zone, 'floor').name
        window_constr = self.material_library.get_construction_assembly(building_type, climate_zone, 'window').name
        self.construction_map = {
            'Building_ExteriorWall': wall_constr,
            'Building_ExteriorRoof': roof_constr,
            'Building_ExteriorFloor': floor_constr,
            'Building_Window': window_constr,
            'Window_Double_Clear': window_constr
        }
        
        # Generate advanced HVAC systems
        hvac_components = self._generate_advanced_hvac_systems(
            zones, building_type, location_data.get('climate_zone', '3A'), building_params
        )
        
        # Generate complete IDF
        idf_content = []
        
        # Header
        idf_content.append(self.generate_header())
        
        # Version
        idf_content.append(self.generate_version_section())
        
        # Simulation Control
        idf_content.append(self.generate_simulation_control())
        
        # Building
        idf_content.append(self.generate_building_section(
            building_params.get('name', 'Professional Building')
        ))
        
        # Global Geometry Rules
        idf_content.append(self.generate_global_geometry_rules())
        
        # Timestep
        idf_content.append("Timestep,4;")
        
        # Site Location: omit when a weather file is provided to avoid EPW/location mismatch warnings
        if not location_data.get('weather_file'):
            idf_content.append(self.generate_site_location(location_data))
        
        # Materials
        idf_content.append(self.material_library.generate_material_objects(materials_used))
        
        # Constructions
        idf_content.append(self.material_library.generate_construction_objects(constructions_used))
        
        # Zones
        for zone in zones:
            idf_content.append(self.generate_zone_object(zone))
        
        # Surfaces
        surfaces = self.geometry_engine.generate_building_surfaces(zones, footprint)
        for surface in surfaces:
            idf_content.append(self.format_surface_object(surface))
        
        # Windows
        windows = self._generate_windows(zones, footprint, building_type, building_params)
        for window in windows:
            idf_content.append(self.format_window_object(window))
        
        # Loads (People, Lights, Equipment)
        for zone in zones:
            space_type = self._determine_space_type(zone.name, building_type)
            idf_content.append(self.generate_people_objects(zone, space_type, building_type))
            idf_content.append(self.generate_lighting_objects(zone, space_type, building_type))
            idf_content.append(self.generate_equipment_objects(zone, space_type, building_type))
        
        # HVAC Systems
        for component in hvac_components:
            if component.get('type') == 'IDF_STRING' and 'raw' in component:
                idf_content.append(component['raw'])
            else:
                idf_content.append(self.format_hvac_object(component))
        
        # HVAC Performance Curves
        idf_content.append(self._generate_hvac_performance_curves())
        
        # Schedules (only for used space types)
        used_space_types = set()
        for zone in zones:
            used_space_types.add(self._determine_space_type(zone.name, building_type))
        idf_content.append(self.generate_schedules(building_type, sorted(used_space_types)))
        
        # Run Period
        idf_content.append(self.generate_run_period())
        
        # Outputs
        idf_content.append(self.generate_output_objects())
        
        # Weather File
        idf_content.append(self.generate_weather_file_object(
            location_data.get('weather_file', 'USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw')
        ))
        
        return '\n\n'.join(idf_content)
    
    def _determine_building_type(self, building_params: Dict, documents: List[str]) -> str:
        """Determine building type from parameters and documents"""
        # Check if building type is explicitly specified
        if 'building_type' in building_params:
            return building_params['building_type']
        
        # Analyze documents for building type clues
        if documents:
            # Simple keyword matching (in practice, would use NLP)
            doc_text = ' '.join(documents).lower()
            if any(word in doc_text for word in ['residential', 'apartment', 'house', 'home']):
                return 'residential_multi'
            elif any(word in doc_text for word in ['retail', 'store', 'shop', 'mall']):
                return 'retail'
            elif any(word in doc_text for word in ['hospital', 'clinic', 'medical']):
                return 'healthcare_hospital'
            elif any(word in doc_text for word in ['school', 'university', 'education']):
                return 'education_school'
            elif any(word in doc_text for word in ['hotel', 'restaurant', 'hospitality']):
                return 'hospitality_hotel'
            elif any(word in doc_text for word in ['warehouse', 'industrial', 'manufacturing']):
                return 'industrial_warehouse'
        
        # Default to office
        return 'office'
    
    def _generate_complex_footprint(self, location_data: Dict, building_type: str, 
                                  estimated_params: Dict) -> BuildingFootprint:
        """Generate complex building footprint"""
        # Build OSM-like geometry payload from enhanced location data if present
        building_info = location_data.get('building') or {}
        osm_like = {}
        try:
            footprint_latlon = building_info.get('osm_footprint')
            if footprint_latlon and len(footprint_latlon) >= 3:
                # GeoJSON expects [ [ [x,y], ... ] ] with x=lon, y=lat
                ring = [[lon, lat] for (lat, lon) in footprint_latlon]
                # Ensure closed ring
                if ring[0] != ring[-1]:
                    ring.append(ring[0])
                osm_like['geometry'] = {
                    'type': 'Polygon',
                    'coordinates': [ring]
                }
        except Exception:
            # If anything fails, fall back without geometry
            osm_like = {}

        # Get footprint area (per-floor area from OSM or estimated_params)
        # The footprint polygon represents a single floor, not the entire building
        footprint_area = None
        
        # Prefer real area from OSM if available
        try:
            osm_area = building_info.get('osm_area_m2')
            if osm_area and float(osm_area) > 10:
                footprint_area = float(osm_area)
        except Exception:
            pass
        
        # Fall back to estimated params if no OSM data
        if footprint_area is None:
            # estimated_params has total_area (all floors) and floor_area (one floor)
            footprint_area = estimated_params.get('floor_area')
            if footprint_area is None:
                total_area = estimated_params.get('total_area', 1000)
                stories = max(1, int(estimated_params.get('stories') or 1))
                footprint_area = total_area / stories if stories > 0 else 1000

        # Generate footprint (single floor polygon)
        footprint = self.geometry_engine.generate_complex_footprint(
            osm_data=osm_like,
            building_type=building_type,
            total_area=footprint_area,  # This is actually per-floor area
            stories=estimated_params['stories']
        )

        return footprint
    
    def _select_professional_materials(self, building_type: str, climate_zone: str) -> Tuple[List[str], List[str]]:
        """Select appropriate materials and constructions"""
        materials_used = []
        constructions_used = []
        
        # Get constructions for different surface types
        surface_types = ['wall', 'roof', 'floor', 'window']
        
        for surface_type in surface_types:
            construction = self.material_library.get_construction_assembly(
                building_type, climate_zone, surface_type
            )
            if construction:
                constructions_used.append(construction.name)
                materials_used.extend(construction.materials)
        
        # Remove duplicates
        materials_used = list(set(materials_used))
        constructions_used = list(set(constructions_used))
        
        return materials_used, constructions_used
    
    def _generate_advanced_hvac_systems(self, zones: List[ZoneGeometry],
                                      building_type: str, climate_zone: str,
                                      building_params: Dict) -> List[Dict]:
        """Generate advanced HVAC systems for all zones"""
        hvac_components = []
        
        # Get HVAC system type from building template
        building_template = self.building_types.get_building_type_template(building_type)
        hvac_type = building_template.hvac_system_type if building_template else 'VAV'
        
        # Choose catalog equipment if requested
        equip_source = (building_params or {}).get('equip_source', 'mock')
        equip_type = (building_params or {}).get('equip_type', 'DX_COIL')
        equip_capacity = (building_params or {}).get('equip_capacity', '3ton')

        catalog_idf = []
        catalog_manifest = {}
        # Temporarily disable direct catalog coil injection until node wiring is implemented
        spec = None

        for zone in zones:
            # Generate HVAC system for this zone
            zone_hvac = self.hvac_systems.generate_hvac_system(
                building_type=building_type,
                zone_name=zone.name,
                zone_area=zone.area,
                hvac_type=hvac_type,
                climate_zone=climate_zone,
                catalog_equipment=None
            )
            hvac_components.extend(zone_hvac)

        # Write manifest if any catalog equipment used
        if catalog_manifest:
            try:
                os.makedirs('artifacts/desktop_files/docs', exist_ok=True)
                with open('artifacts/desktop_files/docs/equipment_manifest.json', 'w') as f:
                    import json
                    json.dump(catalog_manifest, f, indent=2)
            except Exception:
                pass
            
            # Generate controls
            controls = self.hvac_systems.generate_control_objects(
                zone_name=zone.name,
                hvac_type=hvac_type,
                climate_zone=climate_zone
            )
            hvac_components.extend(controls)
        
        return hvac_components
    
    def _determine_space_type(self, zone_name: str, building_type: str) -> str:
        """Determine space type from zone name and building type"""
        zone_lower = zone_name.lower()
        
        # Map zone names to space types
        if 'office' in zone_lower or 'open' in zone_lower:
            return 'office_open'
        elif 'conference' in zone_lower or 'meeting' in zone_lower:
            return 'conference'
        elif 'break' in zone_lower or 'lounge' in zone_lower:
            return 'break_room'
        elif 'lobby' in zone_lower or 'reception' in zone_lower:
            return 'lobby'
        elif 'storage' in zone_lower or 'utility' in zone_lower:
            return 'storage'
        elif 'mechanical' in zone_lower or 'equipment' in zone_lower:
            return 'mechanical'
        elif 'living' in zone_lower or 'family' in zone_lower:
            return 'living'
        elif 'kitchen' in zone_lower:
            return 'kitchen'
        elif 'bedroom' in zone_lower:
            return 'bedroom'
        elif 'bathroom' in zone_lower:
            return 'bathroom'
        elif 'sales' in zone_lower or 'retail' in zone_lower:
            return 'sales_floor'
        elif 'classroom' in zone_lower:
            return 'classroom'
        elif 'patient' in zone_lower:
            return 'patient_room'
        elif 'warehouse' in zone_lower:
            return 'warehouse_floor'
        else:
            # Default based on building type
            if building_type.startswith('residential'):
                return 'living'
            elif building_type == 'retail':
                return 'sales_floor'
            elif building_type.startswith('education'):
                return 'classroom'
            elif building_type.startswith('healthcare'):
                return 'patient_room'
            elif building_type.startswith('industrial'):
                return 'warehouse_floor'
            else:
                return 'office_open'
    
    def generate_header(self) -> str:
        """Generate IDF file header."""
        return f"""! EnergyPlus IDF File
! Generated by Professional IDF Creator
! Version: {self.version}
! Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
! Professional Features: Advanced Geometry, Materials, HVAC Systems

"""
    
    def generate_version_section(self) -> str:
        """Generate Version section."""
        return f"""Version,
  {self.version};                    !- Version Identifier

"""
    
    def generate_simulation_control(self) -> str:
        """Generate SimulationControl object."""
        return """SimulationControl,
  No,                      !- Do Zone Sizing Calculation
  No,                      !- Do System Sizing Calculation
  No,                      !- Do Plant Sizing Calculation
  No,                      !- Run Simulation for Sizing Periods
  Yes,                     !- Run Simulation for Weather File Run Periods
  No,                      !- Do HVAC Sizing Simulation for Sizing Periods
  1;                       !- Maximum Number of HVAC Sizing Simulation Passes

"""
    
    def generate_building_section(self, name: str, north_axis: float = 0.0) -> str:
        """Generate Building object."""
        return f"""Building,
  {name},                  !- Name
  {north_axis:.4f},        !- North Axis
  Suburbs,                 !- Terrain
  0.0400,                  !- Loads Convergence Tolerance Value {{W}}
  0.2000,                  !- Temperature Convergence Tolerance Value {{deltaC}}
  FullInteriorAndExterior, !- Solar Distribution
  15,                      !- Maximum Number of Warmup Days
  6;                       !- Minimum Number of Warmup Days

"""
    
    def generate_global_geometry_rules(self) -> str:
        """Generate GlobalGeometryRules object."""
        return """GlobalGeometryRules,
  UpperLeftCorner,        !- Starting Vertex Position
  CounterClockWise,       !- Vertex Entry Direction
  Relative;               !- Coordinate System

"""
    
    def generate_site_location(self, location_data: Dict) -> str:
        """Generate Site:Location object."""
        latitude = location_data.get('latitude', 37.7749)
        longitude = location_data.get('longitude', -122.4194)
        elevation = location_data.get('elevation', 10.0)
        time_zone = location_data.get('time_zone', -8.0)
        city_name = location_data.get('weather_city_name') or location_data.get('city', 'Site')
        
        return f"""Site:Location,
  {city_name}, !- Name
  {latitude:.4f},          !- Latitude
  {longitude:.4f},         !- Longitude
  {time_zone:.1f},         !- Time Zone
  {elevation:.1f};         !- Elevation

"""
    
    def generate_zone_object(self, zone: ZoneGeometry) -> str:
        """Generate Zone object."""
        return f"""Zone,
  {zone.name},             !- Name
  0,                       !- Direction of Relative North {{deg}}
  0,                       !- X Origin {{m}}
  0,                       !- Y Origin {{m}}
  0,                       !- Z Origin {{m}}
  1,                       !- Type
  1,                       !- Multiplier
  autocalculate,           !- Ceiling Height {{m}}
  autocalculate,           !- Volume {{m3}}
  ,                        !- Floor Area {{m2}}
  ,                        !- Zone Inside Convection Algorithm
  ,                        !- Zone Outside Convection Algorithm
  Yes;                     !- Part of Total Floor Area

"""
    
    def format_surface_object(self, surface: Dict) -> str:
        """Format surface object for EnergyPlus."""
        # Vertices must be comma-separated, with a single semicolon at the end
        vertices_str = ',\n  '.join(surface['vertices'])
        
        # Get construction name with fallback
        constr = self.construction_map.get(surface['construction'], surface['construction'])
        if not constr:
            constr = surface['construction'] if surface.get('construction') else 'Default_Construction'
        return f"""{surface['type']},
  {surface['name']},       !- Name
  {surface['surface_type']}, !- Surface Type
  {constr}, !- Construction Name
  {surface['zone']},       !- Zone Name
  ,                        !- Space Name
  {surface['outside_boundary_condition']}, !- Outside Boundary Condition
  ,                        !- Outside Boundary Condition Object
  {surface['sun_exposure']}, !- Sun Exposure
  {surface['wind_exposure']}, !- Wind Exposure
  {surface['view_factor_to_ground']}, !- View Factor to Ground
  {len(surface['vertices'])}, !- Number of Vertices
  {vertices_str};          !- Vertex 1 through {len(surface['vertices'])} X-coordinate, Y-coordinate, Z-coordinate

"""
    
    def format_window_object(self, window: Dict) -> str:
        """Format window object for EnergyPlus."""
        # Vertices must be comma-separated, with a single semicolon at the end
        vertices_str = ',\n  '.join(window['vertices'])
        
        constr = self.construction_map.get(window['construction'], window['construction'])
        return f"""FenestrationSurface:Detailed,
  {window['name']},        !- Name
  Window,                  !- Surface Type
  {constr}, !- Construction Name
  {window['building_surface_name']}, !- Building Surface Name
  ,                        !- Outside Boundary Condition Object
  AutoCalculate,           !- View Factor to Ground
  ,                        !- Frame and Divider Name
  1.0000,                  !- Multiplier
  {len(window['vertices'])}, !- Number of Vertices
  {vertices_str};          !- Vertex 1 through {len(window['vertices'])} X-coordinate, Y-coordinate, Z-coordinate

"""
    
    def format_hvac_object(self, component: Dict) -> str:
        """Format HVAC component object for EnergyPlus."""
        comp_type = component.get('type', '')
        
        if comp_type == 'AirLoopHVAC':
            # EnergyPlus 24.2/25.1 AirLoopHVAC fields (9 fields total)
            return f"""AirLoopHVAC,
  {component['name']},                 !- Name
  ,                                    !- Controller List Name
  ,                                    !- Availability Manager List Name
  {component.get('design_supply_air_flow_rate', 'Autosize')}, !- Design Supply Air Flow Rate {{m3/s}}
  ,                                    !- Branch List Name
  ,                                    !- Connector List Name
  {component['supply_side_inlet_node_name']}, !- Supply Side Inlet Node Name
  {component.get('demand_side_outlet_node_name', '')}, !- Demand Side Outlet Node Name
  {component['supply_side_outlet_node_names'][0] if component.get('supply_side_outlet_node_names') else component['name'] + 'SupplyOutlet'}; !- Supply Side Outlet Node Names

"""
        
        elif comp_type == 'Fan:VariableVolume':
            # Correct field order per EnergyPlus 25.1 schema
            return f"""Fan:VariableVolume,
  {component['name']},                 !- Name
  Always On,                           !- Availability Schedule Name
  {component['fan_total_efficiency']}, !- Fan Total Efficiency
  {component['fan_pressure_rise']},    !- Pressure Rise {{Pa}}
  {component['maximum_flow_rate']},    !- Maximum Flow Rate {{m3/s}}
  {component.get('fan_power_minimum_flow_fraction', 0.3)}, !- Fan Power Minimum Flow Fraction
  1.0,                                 !- Motor Efficiency
  1.0,                                 !- Motor In Airstream Fraction
  {component['air_inlet_node_name']},  !- Air Inlet Node Name
  {component['air_outlet_node_name']}, !- Air Outlet Node Name
  {component.get('fan_power_coefficient_1', 0.0013)}, !- Fan Power Coefficient 1
  {component.get('fan_power_coefficient_2', 0.1470)}, !- Fan Power Coefficient 2
  {component.get('fan_power_coefficient_3', 0.9506)}, !- Fan Power Coefficient 3
  {component.get('fan_power_coefficient_4', -0.0998)}, !- Fan Power Coefficient 4
  {component.get('fan_power_coefficient_5', 0.0)}, !- Fan Power Coefficient 5
  ;                                     !- End

"""
        
        elif comp_type == 'Coil:Heating:Electric':
            # Electric coils are 100% efficient (always 1.0)
            return f"""Coil:Heating:Electric,
  {component['name']},                 !- Name
  Always On,                           !- Availability Schedule Name
  1.0,                                 !- Efficiency
  {component['nominal_capacity']},     !- Nominal Capacity {{W}}
  {component['air_inlet_node_name']},  !- Air Inlet Node Name
  {component['air_outlet_node_name']}; !- Air Outlet Node Name

"""
        
        elif comp_type == 'Coil:Cooling:DX:SingleSpeed':
            # Correct field order per EnergyPlus 24.2/25.1 schema
            return f"""Coil:Cooling:DX:SingleSpeed,
  {component['name']},                 !- Name
  {component['availability_schedule_name']}, !- Availability Schedule Name
  {component['gross_rated_total_cooling_capacity']}, !- Gross Rated Total Cooling Capacity {{W}}
  {component['gross_rated_sensible_heat_ratio']}, !- Gross Rated Sensible Heat Ratio
  {component['gross_rated_cooling_cop']}, !- Gross Rated Cooling COP {{W/W}}
  {component['rated_air_flow_rate']},  !- Rated Air Flow Rate {{m3/s}}
  ,                                    !- Rated Evaporator Fan Power Per Volume Flow Rate {{W/(m3/s)}}
  ,                                    !- 2023 Rated Evaporator Fan Power Per Volume Flow {{W/(m3/s)}}
  {component['air_inlet_node_name']},  !- Air Inlet Node Name
  {component['air_outlet_node_name']}, !- Air Outlet Node Name
  Cooling Coil DX 1-Pass Biquadratic Performance Curve, !- Total Cooling Capacity Function of Temperature Curve Name
  Cooling Coil DX 1-Pass Biquadratic Performance Curve, !- Total Cooling Capacity Function of Flow Fraction Curve Name
  Cooling Coil DX 1-Pass Quadratic Performance Curve, !- Energy Input Ratio Function of Temperature Curve Name
  Cooling Coil DX 1-Pass Quadratic Performance Curve, !- Energy Input Ratio Function of Flow Fraction Curve Name
  Cooling Coil DX 1-Pass Quadratic Performance Curve; !- Part Load Fraction Correlation Curve Name

"""
        
        elif comp_type == 'ZoneHVAC:AirDistributionUnit':
            return f"""ZoneHVAC:AirDistributionUnit,
  {component['name']},                 !- Name
  {component['air_terminal_name']},    !- Air Distribution Unit Outlet Node Name
  {component['air_terminal_object_type']}, !- Air Terminal Object Type
  {component['air_terminal_name']};    !- Air Terminal Object Name

"""
        
        elif comp_type == 'AirTerminal:SingleDuct:VAV:Reheat':
            # Correct field order per EnergyPlus 25.1 schema
            # Total 15 fields only - do not duplicate Air Outlet Node Name
            return f"""AirTerminal:SingleDuct:VAV:Reheat,
  {component['name']},                 !- Name
  {component['availability_schedule_name']}, !- Availability Schedule Name
  {component['damper_air_outlet_node_name']}, !- Damper Air Outlet Node Name
  {component['air_inlet_node_name']},  !- Air Inlet Node Name
  Autosize,                            !- Maximum Air Flow Rate {{m3/s}}
  Constant,                            !- Zone Minimum Air Flow Input Method
  {component.get('maximum_flow_fraction_before_reheat', 0.2)}, !- Constant Minimum Air Flow Fraction
  ,                                    !- Constant Minimum Air Flow Fraction Schedule Name
  {component['reheat_coil_air_inlet_node_name']}, !- Reheat Coil Air Inlet Node Name
  Coil:Heating:Electric,               !- Reheat Coil Object Type
  {component['reheat_coil_name']},     !- Reheat Coil Name
  {component.get('maximum_hot_water_or_steam_flow_rate', 0.0)}, !- Maximum Hot Water or Steam Flow Rate {{m3/s}}
  {component.get('minimum_hot_water_or_steam_flow_rate', 0.0)}, !- Minimum Hot Water or Steam Flow Rate {{m3/s}}
  {component.get('convergence_tolerance', 0.001)}, !- Convergence Tolerance
  {component['damper_heating_action']}; !- Damper Heating Action

"""
        
        elif comp_type == 'ZoneHVAC:PackagedTerminalAirConditioner':
            return f"""ZoneHVAC:PackagedTerminalAirConditioner,
  {component['name']},                 !- Name
  {component['availability_schedule_name']}, !- Availability Schedule Name
  ,                                    !- Cooling Coil Name
  ,                                    !- Heating Coil Name
  {component['fan_total_efficiency']}, !- Fan Total Efficiency
  {component['fan_delta_pressure']},   !- Fan Pressure Rise {{Pa}}
  {component['maximum_supply_air_flow_rate']}, !- Maximum Supply Air Flow Rate {{m3/s}}
  ,                                    !- Fan Placement
  {component.get('heating_coil_inlet_node', component['name'] + 'FanOutlet')}, !- Heating Coil Air Inlet Node Name
  {component.get('cooling_coil_inlet_node', component['name'] + 'HeatingOutlet')}, !- Cooling Coil Air Inlet Node Name
  {component.get('supply_fan_inlet_node', component['name'] + 'Inlet')}, !- Supply Fan Air Inlet Node Name
  {component.get('supply_fan_outlet_node', component['name'] + 'Outlet')}, !- Supply Fan Air Outlet Node Name
  {component.get('supply_air_inlet_node', component['name'] + 'ZoneSupplyNode')}, !- Zone Supply Air Inlet Node Name
  {component.get('exhaust_air_outlet_node', component['name'] + 'ZoneExhaustNode')}; !- Zone Exhaust Air Outlet Node Name

"""
        
        else:
            return f"! {comp_type}: {component.get('name', 'UNKNOWN')}\n"
    
    def _generate_hvac_performance_curves(self) -> str:
        """Generate performance curves for HVAC equipment"""
        return """Curve:Biquadratic,
  Cooling Coil DX 1-Pass Biquadratic Performance Curve, !- Name
  0.942587793,   !- Coefficient1 Constant
  0.009543347,   !- Coefficient2 x
  0.000683770,   !- Coefficient3 x**2
  -0.011042676,  !- Coefficient4 y
  0.000005249,   !- Coefficient5 y**2
  -0.000009720,  !- Coefficient6 x*y
  12.77778,      !- Minimum Value of x
  23.88889,      !- Maximum Value of x
  18.0,          !- Minimum Value of y
  46.11111,      !- Maximum Value of y
  ,              !- Minimum Curve Output
  ,              !- Maximum Curve Output
  Temperature,   !- Input Unit Type for X
  Temperature,   !- Input Unit Type for Y
  Dimensionless; !- Output Unit Type

Curve:Quadratic,
  Cooling Coil DX 1-Pass Quadratic Performance Curve, !- Name
  0.606205495,   !- Coefficient1 Constant
  -0.096596208,  !- Coefficient2 x
  0.001340325,   !- Coefficient3 x**2
  0.0,           !- Minimum Value of x
  10.0,          !- Maximum Value of x
  ,              !- Minimum Curve Output
  ,              !- Maximum Curve Output
  Temperature,   !- Input Unit Type for X
  Dimensionless; !- Output Unit Type

"""
    
    def generate_people_objects(self, zone: ZoneGeometry, space_type: str, building_type: str) -> str:
        """Generate People objects for zone."""
        space_template = self.building_types.get_space_template(space_type)
        if not space_template:
            space_template = self.building_types.get_space_template('office_open')
        
        occupancy_density = space_template['occupancy_density']
        total_people = max(1, int(zone.area * occupancy_density))
        
        return f"""People,
  {zone.name}_People,      !- Name
  {zone.name},             !- Zone or ZoneList Name
  {space_type}_Occupancy,  !- Number of People Schedule Name
  People,                  !- Number of People Calculation Method
  {total_people},          !- Number of People
  ,                        !- People per Zone Floor Area {{person/m2}}
  ,                        !- Zone Floor Area per Person {{m2/person}}
  0.3,                     !- Fraction Radiant
  0.1,                     !- Sensible Heat Fraction
  {space_type}_Activity;   !- Activity Level Schedule Name

"""
    
    def generate_lighting_objects(self, zone: ZoneGeometry, space_type: str, building_type: str) -> str:
        """Generate Lights objects for zone."""
        space_template = self.building_types.get_space_template(space_type)
        if not space_template:
            space_template = self.building_types.get_space_template('office_open')
        
        lighting_power_density = space_template['lighting_power_density']
        total_lighting = zone.area * lighting_power_density
        
        return f"""Lights,
  {zone.name}_Lights,      !- Name
  {zone.name},             !- Zone or ZoneList Name
  {space_type}_Lighting,   !- Schedule Name
  Watts/Area,              !- Design Level Calculation Method
  ,                        !- Lighting Level {{W}}
  {lighting_power_density:.1f}, !- Watts per Zone Floor Area {{W/m2}}
  ,                        !- Watts per Person {{W/person}}
  0.0,                     !- Return Air Fraction
  0.3,                     !- Fraction Radiant
  0.2,                     !- Fraction Visible
  ,                        !- Fraction Replaceable
  General;                 !- End-Use Subcategory

"""
    
    def generate_equipment_objects(self, zone: ZoneGeometry, space_type: str, building_type: str) -> str:
        """Generate ElectricEquipment objects for zone."""
        space_template = self.building_types.get_space_template(space_type)
        if not space_template:
            space_template = self.building_types.get_space_template('office_open')
        
        equipment_power_density = space_template['equipment_power_density']
        
        return f"""ElectricEquipment,
  {zone.name}_Equipment,   !- Name
  {zone.name},             !- Zone or ZoneList Name
  {space_type}_Equipment,  !- Schedule Name
  Watts/Area,              !- Design Level Calculation Method
  ,                        !- Design Level {{W}}
  {equipment_power_density:.1f}, !- Watts per Zone Floor Area {{W/m2}}
  ,                        !- Watts per Person {{W/person}}
  0.1,                     !- Fraction Latent
  0.2,                     !- Fraction Radiant
  0,                       !- Fraction Lost
  General;                 !- End-Use Subcategory

"""
    
    def generate_schedules(self, building_type: str, space_types_filter: List[str] = None) -> str:
        """Generate comprehensive schedules for building type."""
        schedules = []

        # Define schedule type limits
        schedules.append("""ScheduleTypeLimits,
  Fraction,                !- Name
  0.0,                     !- Lower Limit Value
  1.0,                     !- Upper Limit Value
  CONTINUOUS;              !- Numeric Type
""")
        schedules.append("""ScheduleTypeLimits,
  Any Number,              !- Name
  ,                        !- Lower Limit Value
  ,                        !- Upper Limit Value
  CONTINUOUS;              !- Numeric Type
""")

        # Get space types
        building_template = self.building_types.get_building_type_template(building_type)
        if space_types_filter:
            space_types = space_types_filter
        else:
            if building_template:
                space_types = building_template.space_types
            else:
                space_types = ['office_open', 'conference', 'break_room', 'lobby', 'storage', 'mechanical']

        # Simple AllDays schedules (valid syntax) to ensure simulation proceeds
        for space_type in space_types:
            schedules.append(f"""Schedule:Compact,
  {space_type}_Occupancy,  !- Name
  Fraction,                !- Schedule Type Limits Name
  Through: 12/31,
  For: AllDays,
  Until: 24:00,0.80;
""")
            schedules.append(f"""Schedule:Compact,
  {space_type}_Lighting,   !- Name
  Fraction,                !- Schedule Type Limits Name
  Through: 12/31,
  For: AllDays,
  Until: 24:00,1.00;
""")
            schedules.append(f"""Schedule:Compact,
  {space_type}_Equipment,  !- Name
  Fraction,                !- Schedule Type Limits Name
  Through: 12/31,
  For: AllDays,
  Until: 24:00,0.70;
""")

            # People activity level schedule (Watts/person)
            schedules.append(f"""Schedule:Compact,
  {space_type}_Activity,   !- Name
  Any Number,              !- Schedule Type Limits Name
  Through: 12/31,
  For: AllDays,
  Until: 24:00,120.0;
""")

        return '\n'.join(schedules)
    
    def generate_run_period(self) -> str:
        """Generate RunPeriod object."""
        return """RunPeriod,
  Year Round Run Period,   !- Name
  1,                       !- Begin Month
  1,                       !- Begin Day of Month
  ,                        !- Begin Year
  12,                      !- End Month
  31,                      !- End Day of Month
  ,                        !- End Year
  ,                        !- Day of Week for Start Day
  ,                        !- Use Weather File Holidays and Special Days
  ,                        !- Use Weather File Daylight Saving Period
  ,                        !- Apply Weekend Holiday Rule
  ,                        !- Use Weather File Rain Indicators
  ;                        !- Use Weather File Snow Indicators

"""
    
    def generate_output_objects(self) -> str:
        """Generate output objects."""
        return """Output:VariableDictionary,
  Regular;                 !- Key Field

Output:SQLite,
  SimpleAndTabular;        !- Option Type

Output:Table:SummaryReports,
  AllSummary;              !- Report 1 Name

"""
    
    def generate_weather_file_object(self, weather_file: str) -> str:
        """Generate weather file reference."""
        return f"""Site:GroundTemperature:BuildingSurface,
  20,                      !- January Ground Temperature {{C}}
  20,                      !- February Ground Temperature {{C}}
  20,                      !- March Ground Temperature {{C}}
  20,                      !- April Ground Temperature {{C}}
  20,                      !- May Ground Temperature {{C}}
  20,                      !- June Ground Temperature {{C}}
  20,                      !- July Ground Temperature {{C}}
  20,                      !- August Ground Temperature {{C}}
  20,                      !- September Ground Temperature {{C}}
  20,                      !- October Ground Temperature {{C}}
  20,                      !- November Ground Temperature {{C}}
  20;                      !- December Ground Temperature {{C}}

"""
    
    def _get_default_oriented_wwr(self, building_type: str) -> Dict[str, float]:
        """Default per-orientation WWR by building type (can be overridden)."""
        defaults = {
            'office': {'N': 0.20, 'E': 0.35, 'S': 0.50, 'W': 0.35},
            'residential_single': {'N': 0.10, 'E': 0.15, 'S': 0.20, 'W': 0.15},
            'residential_multi': {'N': 0.10, 'E': 0.15, 'S': 0.20, 'W': 0.15},
            'retail': {'N': 0.15, 'E': 0.25, 'S': 0.35, 'W': 0.25},
            'healthcare_hospital': {'N': 0.20, 'E': 0.30, 'S': 0.40, 'W': 0.30},
            'education_school': {'N': 0.20, 'E': 0.30, 'S': 0.40, 'W': 0.30},
            'education_university': {'N': 0.20, 'E': 0.30, 'S': 0.40, 'W': 0.30},
            'industrial_warehouse': {'N': 0.05, 'E': 0.10, 'S': 0.10, 'W': 0.10},
            'industrial_manufacturing': {'N': 0.05, 'E': 0.10, 'S': 0.10, 'W': 0.10},
            'hospitality_hotel': {'N': 0.15, 'E': 0.25, 'S': 0.30, 'W': 0.25},
            'hospitality_restaurant': {'N': 0.10, 'E': 0.20, 'S': 0.25, 'W': 0.20},
            'mixed_use': {'N': 0.20, 'E': 0.30, 'S': 0.40, 'W': 0.30}
        }
        return defaults.get(building_type, {'N': 0.20, 'E': 0.30, 'S': 0.40, 'W': 0.30})

    def _resolve_wwr_overrides(self, base: Dict[str, float], building_params: Dict) -> Dict[str, float]:
        """Apply CLI/user overrides to orientation WWRs, cap at 0.40 (prescriptive typical)."""
        out = dict(base)
        cap = 0.40
        # Global override
        if 'wwr' in building_params and building_params['wwr'] is not None:
            val = max(0.0, min(cap, float(building_params['wwr'])))
            out = {k: val for k in out.keys()}
        # Orientation-specific overrides
        for k_param, ori in [('wwr_n','N'), ('wwr_e','E'), ('wwr_s','S'), ('wwr_w','W')]:
            if k_param in building_params and building_params[k_param] is not None:
                val = max(0.0, min(cap, float(building_params[k_param])))
                out[ori] = val
        return out

    def _orientation_from_vector(self, dx: float, dy: float) -> str:
        """Map wall direction to N/E/S/W using angle of outward normal approximation."""
        # Wall direction angle (radians) relative to +X (east); normal is rotated 90° CCW
        angle = math.atan2(dy, dx) + math.pi/2
        # Normalize to [0, 2pi)
        while angle < 0:
            angle += 2*math.pi
        while angle >= 2*math.pi:
            angle -= 2*math.pi
        # Determine closest cardinal (N=pi/2, E=0, S=3pi/2, W=pi)
        cardinals = {
            'E': 0.0,
            'N': math.pi/2,
            'W': math.pi,
            'S': 3*math.pi/2
        }
        best = min(cardinals.items(), key=lambda kv: abs(kv[1]-angle))
        return best[0]

    def _generate_windows(self, zones: List[ZoneGeometry], footprint: BuildingFootprint, building_type: str, building_params: Dict) -> List[Dict]:
        """Generate windows for zones, targeting building-type Window-to-Wall Ratio (WWR).

        Strategy:
        - Compute each wall area = wall_length * story_height
        - Target window area = WWR * wall area (per building type default)
        - Use a centered ribbon window sized to meet target area, with limits
        - Maintain margins from floor/ceiling and wall edges
        """
        windows = []
        
        # Check if zones exist
        if not zones:
            print("⚠️  Warning: No zones found for window generation")
            return windows

        # Determine orientation-specific WWRs (with overrides)
        base_oriented = self._get_default_oriented_wwr(building_type)
        oriented_wwr = self._resolve_wwr_overrides(base_oriented, building_params)

        for zone in zones:
            coords = list(zone.polygon.exterior.coords[:-1])
            z_bottom = zone.floor_level * 3.0
            z_top = (zone.floor_level + 1) * 3.0
            story_height = max(0.5, z_top - z_bottom)

            for i, (x1, y1) in enumerate(coords):
                x2, y2 = coords[(i + 1) % len(coords)]

                wall_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                if wall_length < 2.0:
                    continue

                # Determine wall orientation and its WWR
                wwr = oriented_wwr[self._orientation_from_vector(x2 - x1, y2 - y1)]

                wall_area = wall_length * story_height
                target_window_area = max(0.0, min(wwr * wall_area, wall_area * 0.8))  # cap at 80% for constructability

                if target_window_area <= 0.01:
                    continue

                # Choose a ribbon window with width fraction and compute height from area
                margin_h = max(0.3, story_height * 0.15)   # top/bottom margins
                max_win_height = max(0.3, story_height - 2 * margin_h)
                width_fraction = 0.7  # 70% of wall length by default
                win_width = max(1.0, min(wall_length * width_fraction, wall_length - 0.6))

                # Compute height from target area, limit to max_win_height
                win_height = min(max_win_height, target_window_area / max(win_width, 0.1))
                if win_height < 0.3:
                    # Too small; try increasing width up to 90%
                    win_width = max(1.0, min(wall_length * 0.9, wall_length - 0.4))
                    win_height = min(max_win_height, target_window_area / max(win_width, 0.1))

                # Vertical placement: center within allowed band
                win_z_bottom = z_bottom + (story_height - win_height) / 2
                win_z_top = win_z_bottom + win_height

                # Horizontal placement: center along wall segment in projected XY
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2

                # Determine local wall direction vector to offset window width along wall axis
                dx = x2 - x1
                dy = y2 - y1
                length = math.sqrt(dx*dx + dy*dy)
                ux = dx / length
                uy = dy / length

                half_w = win_width / 2
                # Endpoints along wall axis from center
                ax = center_x - ux * half_w
                ay = center_y - uy * half_w
                bx = center_x + ux * half_w
                by = center_y + uy * half_w

                # Construct rectangle window vertices (consistent outward normal)
                # Create a small normal vector for thickness in plan (for coordinates only)
                nx = -uy
                ny = ux
                half_t = 0.05  # small offset to give window a finite width in the perpendicular direction

                v1x = ax + nx * half_t
                v1y = ay + ny * half_t
                v2x = ax - nx * half_t
                v2y = ay - ny * half_t
                v3x = bx - nx * half_t
                v3y = by - ny * half_t
                v4x = bx + nx * half_t
                v4y = by + ny * half_t

                window = {
                    'name': f"{zone.name}_Window_{i+1}",
                    'construction': 'Window_Double_Clear',
                    'building_surface_name': f"{zone.name}_Wall_{i+1}",
                    'vertices': [
                        f"{v1x:.4f},{v1y:.4f},{win_z_top:.4f}",
                        f"{v2x:.4f},{v2y:.4f},{win_z_bottom:.4f}",
                        f"{v3x:.4f},{v3y:.4f},{win_z_bottom:.4f}",
                        f"{v4x:.4f},{v4y:.4f},{win_z_top:.4f}"
                    ]
                }
                windows.append(window)

        return windows
