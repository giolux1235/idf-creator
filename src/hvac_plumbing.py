"""
HVAC Plumbing and Wiring Module
Connects catalog equipment to HVAC systems with proper node connections
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from .equipment_catalog.schema import EquipmentSpec


@dataclass
class NodeConnection:
    """Represents a node connection in HVAC system"""
    node_name: str
    component_name: str
    inlet_outlet: str  # 'inlet' or 'outlet'
    connection_order: int


@dataclass
class BranchSegment:
    """Represents a segment of an air/water branch"""
    component_type: str
    component_name: str
    inlet_node: str
    outlet_node: str
    component_object: Optional[Dict] = None


class HVACPlumbing:
    """Manages HVAC system plumbing and node connections"""
    
    def __init__(self):
        self.unique_nodes = set()
        self.node_counter = 0
    
    def generate_unique_node_name(self, base_name: str) -> str:
        """Generate unique node name"""
        if base_name not in self.unique_nodes:
            self.unique_nodes.add(base_name)
            return base_name
        
        counter = 1
        while f"{base_name}_{counter}" in self.unique_nodes:
            counter += 1
        
        unique_name = f"{base_name}_{counter}"
        self.unique_nodes.add(unique_name)
        return unique_name
    
    def wire_catalog_equipment_to_vav(self, zone_name: str, equipment_spec: EquipmentSpec, 
                                     sizing_params: Dict) -> List[Dict]:
        """Wire catalog equipment into VAV system with proper node connections"""
        components = []
        
        # Generate unique component names
        coil_name = f"{zone_name}_CatalogCoil"
        
        # Extract coil nodes from equipment spec
        inlet_node = self.generate_unique_node_name(f"{coil_name}_Inlet")
        outlet_node = self.generate_unique_node_name(f"{coil_name}_Outlet")
        
        # Add coil object with proper node connections
        if equipment_spec.equipment_type == 'DX_COIL':
            # Validate and fix air flow rate to ensure it's within acceptable range
            # EnergyPlus expects air volume flow rate per watt in range [2.684E-005--6.713E-005] m³/s/W
            cooling_capacity = equipment_spec.rated_capacity_w or 35000.0
            airflow = equipment_spec.rated_airflow_m3s or 1.2
            
            min_flow_per_watt = 2.684e-5  # m³/s per W
            max_flow_per_watt = 6.713e-5  # m³/s per W
            target_flow_per_watt = 4.7e-5  # Middle of range
            
            if cooling_capacity > 0:
                actual_flow_per_watt = airflow / cooling_capacity
                if actual_flow_per_watt < min_flow_per_watt:
                    # Increase to meet minimum
                    airflow = cooling_capacity * min_flow_per_watt
                elif actual_flow_per_watt > max_flow_per_watt:
                    # Decrease to meet maximum
                    airflow = cooling_capacity * max_flow_per_watt
                # If airflow is None or 0, calculate from capacity
                if not airflow or airflow <= 0:
                    airflow = cooling_capacity * target_flow_per_watt
            else:
                # If no capacity, use default airflow
                airflow = airflow or 1.2
            
            coil_obj = {
                'type': 'Coil:Cooling:DX:SingleSpeed',
                'name': coil_name,
                'availability_schedule_name': 'Always On',
                'air_inlet_node_name': inlet_node,
                'air_outlet_node_name': outlet_node,
                'gross_rated_total_cooling_capacity': cooling_capacity,
                'gross_rated_sensible_heat_ratio': 0.75,
                'gross_rated_cooling_cop': equipment_spec.rated_cop,
                'rated_air_flow_rate': airflow,
                'condenser_air_inlet_node_name': self.generate_unique_node_name(f"{coil_name}_CondenserInlet"),
                'condenser_type': 'AirCooled',
                'evaporator_fan_power_included_in_rated_cop': True,
                'condenser_fan_power_ratio': 0.2
            }
            components.append(coil_obj)
        
        # Create branch list connecting the coil
        branch_name = f"{zone_name}_SupplyBranch"
        branch_list = {
            'type': 'BranchList',
            'name': branch_name,
            'branches': [
                f"{zone_name}_SupplyInletBranch",
                f"{zone_name}_FanBranch",
                f"{zone_name}_HeatingCoilBranch",
                f"{coil_name}_Branch",
                f"{zone_name}_SupplyOutletBranch"
            ]
        }
        components.append(branch_list)
        
        # Create individual branches with proper node connections
        branches = self._create_branches_with_catalog_coil(
            zone_name, coil_name, inlet_node, outlet_node, sizing_params
        )
        components.extend(branches)
        
        # Create connector list
        connector_list = {
            'type': 'ConnectorList',
            'name': f"{zone_name}_ConnectorList",
            'connector_type': 'Connector:Splitter',
            'outlet_branch_name': branch_name
        }
        components.append(connector_list)
        
        return components
    
    def _create_branches_with_catalog_coil(self, zone_name: str, coil_name: str,
                                          coil_inlet: str, coil_outlet: str,
                                          sizing_params: Dict) -> List[Dict]:
        """Create branches connecting catalog coil properly"""
        branches = []
        
        # Supply inlet branch
        branches.append({
            'type': 'Branch',
            'name': f"{zone_name}_SupplyInletBranch",
            'components': [
                {'component_type': 'Node', 'component_name': f"{zone_name}_SupplyInlet"}
            ]
        })
        
        # Fan branch
        fan_name = f"{zone_name}_SupplyFan"
        fan_inlet = self.generate_unique_node_name(f"{fan_name}_Inlet")
        fan_outlet = self.generate_unique_node_name(f"{fan_name}_Outlet")
        
        branches.append({
            'type': 'Branch',
            'name': f"{zone_name}_FanBranch",
            'components': [
                {
                    'component_type': 'Fan:VariableVolume',
                    'component_name': fan_name,
                    'inlet_node': fan_inlet,
                    'outlet_node': fan_outlet
                }
            ]
        })
        
        # Heating coil branch (before cooling coil)
        heating_coil_name = f"{zone_name}_HeatingCoil"
        heating_inlet = self.generate_unique_node_name(f"{heating_coil_name}_Inlet")
        heating_outlet = self.generate_unique_node_name(f"{heating_coil_name}_Outlet")
        
        branches.append({
            'type': 'Branch',
            'name': f"{zone_name}_HeatingCoilBranch",
            'components': [
                {
                    'component_type': 'Coil:Heating:Electric',
                    'component_name': heating_coil_name,
                    'inlet_node': heating_inlet,
                    'outlet_node': heating_outlet
                }
            ]
        })
        
        # Catalog cooling coil branch
        branches.append({
            'type': 'Branch',
            'name': f"{coil_name}_Branch",
            'components': [
                {
                    'component_type': 'Coil:Cooling:DX:SingleSpeed',
                    'component_name': coil_name,
                    'inlet_node': coil_inlet,
                    'outlet_node': coil_outlet
                }
            ]
        })
        
        # Supply outlet branch
        branches.append({
            'type': 'Branch',
            'name': f"{zone_name}_SupplyOutletBranch",
            'components': [
                {'component_type': 'Node', 'component_name': f"{zone_name}_SupplyOutlet"}
            ]
        })
        
        return branches
    
    def create_air_loop_with_plumbing(self, zone_name: str, sizing_params: Dict,
                                     components: List[Dict]) -> str:
        """Create complete air loop with proper plumbing"""
        idf_objects = []
        
        # Air loop
        air_loop = f"""AirLoopHVAC,
  {zone_name}_AirLoop,               !- Name
  ,                                  !- Controller List Name
  {zone_name}_SupplyComponents,      !- Availability Manager List Name
  {zone_name}_SupplyInlet,           !- Return Air Node Name
  ,                                  !- Return Air Bypass Duct Type
  {zone_name}_SupplyOutlet;          !- Outlet Node Name

"""
        idf_objects.append(air_loop)
        
        # Supply side inlet node
        idf_objects.append(f"""Node,
  {zone_name}_SupplyInlet,           !- Name
  {zone_name}_SupplyFan_Outlet;      !- Node Name(s)

""")
        
        # Supply side outlet node
        idf_objects.append(f"""Node,
  {zone_name}_SupplyOutlet,          !- Name
  {zone_name}_DemandInlet;           !- Node Name(s)

""")
        
        # Generate branch objects
        for component in components:
            if isinstance(component, dict):
                branch_obj = self._format_branch(component)
                if branch_obj:
                    idf_objects.append(branch_obj)
        
        return '\n'.join(idf_objects)
    
    def _format_branch(self, branch: Dict) -> str:
        """Format branch as EnergyPlus object"""
        if branch.get('type') != 'Branch':
            return ""
        
        branch_lines = [f"Branch,\n  {branch['name']},"]
        
        components = branch.get('components', [])
        for comp in components:
            if comp['component_type'] == 'Node':
                branch_lines.append(f"  {comp['component_type']},\n  {comp['component_name']};")
            else:
                comp_type = comp['component_type']
                comp_name = comp['component_name']
                branch_lines.append(f"  {comp_type},\n  {comp_name},\n  {comp.get('inlet_node', '')},\n  {comp.get('outlet_node', '')};")
        
        branch_lines.append("\n")
        return '\n'.join(branch_lines)
    
    def generate_water_loop_plumbing(self, zone_name: str, sizing_params: Dict) -> List[Dict]:
        """Generate water loop plumbing for chilled water systems"""
        components = []
        
        # Plant loop
        plant_loop = {
            'type': 'PlantLoop',
            'name': f"{zone_name}_PlantLoop",
            'fluid_type': 'Water',
            'demand_side_outlet_node_name': f"{zone_name}_DemandOutlet",
            'supply_side_inlet_node_name': f"{zone_name}_SupplyInlet"
        }
        components.append(plant_loop)
        
        # Supply side inlet node
        components.append({
            'type': 'NodeList',
            'name': f"{zone_name}_SupplySideInletNodes",
            'nodes': [f"{zone_name}_SupplyInlet"]
        })
        
        # Supply side branch list
        supply_branch_list = {
            'type': 'BranchList',
            'name': f"{zone_name}_SupplySideBranchList",
            'branches': [
                f"{zone_name}_SupplyInletBranch",
                f"{zone_name}_ChillerBranch",
                f"{zone_name}_SupplyOutletBranch"
            ]
        }
        components.append(supply_branch_list)
        
        # Demand side outlet node
        components.append({
            'type': 'NodeList',
            'name': f"{zone_name}_DemandSideOutletNodes",
            'nodes': [f"{zone_name}_DemandOutlet"]
        })
        
        return components


