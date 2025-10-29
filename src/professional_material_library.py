"""
Professional Material Library for IDF Creator
ASHRAE 90.1 compliant materials and construction assemblies
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class Material:
    """Represents a building material with thermal properties"""
    name: str
    material_type: str  # 'Material', 'Material:NoMass', 'WindowMaterial:SimpleGlazingSystem'
    roughness: str = "MediumRough"
    thickness: float = 0.0  # m
    conductivity: float = 0.0  # W/m-K
    density: float = 0.0  # kg/m³
    specific_heat: float = 0.0  # J/kg-K
    thermal_absorptance: float = 0.9
    solar_absorptance: float = 0.7
    visible_absorptance: float = 0.7
    u_factor: float = 0.0  # W/m²-K (for windows)
    solar_heat_gain_coefficient: float = 0.0  # (for windows)
    thermal_resistance: float = 0.0  # m²-K/W (for no-mass materials)


@dataclass
class Construction:
    """Represents a construction assembly"""
    name: str
    materials: List[str]  # List of material names in order
    u_factor: float  # Overall U-factor
    r_value: float  # Overall R-value
    climate_zone: str = "All"
    building_type: str = "All"


class ProfessionalMaterialLibrary:
    """Comprehensive material library with ASHRAE 90.1 compliance"""
    
    def __init__(self):
        self.materials = self._load_materials()
        self.constructions = self._load_constructions()
        self.climate_zones = self._load_climate_zones()
    
    def _load_materials(self) -> Dict[str, Material]:
        """Load comprehensive material database"""
        materials = {}
        
        # === CONCRETE MATERIALS ===
        materials['Concrete_Heavy'] = Material(
            name='Concrete_Heavy',
            material_type='Material',
            thickness=0.2032,  # 8 inches
            conductivity=1.95,  # W/m-K
            density=2242,  # kg/m³
            specific_heat=900,  # J/kg-K
            thermal_absorptance=0.9,
            solar_absorptance=0.65,
            visible_absorptance=0.65
        )
        
        materials['Concrete_Medium'] = Material(
            name='Concrete_Medium',
            material_type='Material',
            thickness=0.1524,  # 6 inches
            conductivity=1.95,
            density=2242,
            specific_heat=900,
            thermal_absorptance=0.9,
            solar_absorptance=0.65,
            visible_absorptance=0.65
        )
        
        materials['Concrete_Light'] = Material(
            name='Concrete_Light',
            material_type='Material',
            thickness=0.1016,  # 4 inches
            conductivity=1.95,
            density=2242,
            specific_heat=900,
            thermal_absorptance=0.9,
            solar_absorptance=0.65,
            visible_absorptance=0.65
        )
        
        # === INSULATION MATERIALS ===
        materials['Insulation_Fiberglass_R13'] = Material(
            name='Insulation_Fiberglass_R13',
            material_type='Material',
            thickness=0.1016,  # 4 inches
            conductivity=0.043,  # W/m-K
            density=12,  # kg/m³
            specific_heat=840,  # J/kg-K
            thermal_absorptance=0.9,
            solar_absorptance=0.7,
            visible_absorptance=0.7
        )
        
        materials['Insulation_Fiberglass_R19'] = Material(
            name='Insulation_Fiberglass_R19',
            material_type='Material',
            thickness=0.1524,  # 6 inches
            conductivity=0.043,
            density=12,
            specific_heat=840,
            thermal_absorptance=0.9,
            solar_absorptance=0.7,
            visible_absorptance=0.7
        )
        
        materials['Insulation_Fiberglass_R30'] = Material(
            name='Insulation_Fiberglass_R30',
            material_type='Material',
            thickness=0.2286,  # 9 inches
            conductivity=0.043,
            density=12,
            specific_heat=840,
            thermal_absorptance=0.9,
            solar_absorptance=0.7,
            visible_absorptance=0.7
        )
        
        materials['Insulation_SprayFoam_R20'] = Material(
            name='Insulation_SprayFoam_R20',
            material_type='Material',
            thickness=0.127,  # 5 inches
            conductivity=0.035,  # W/m-K
            density=24,  # kg/m³
            specific_heat=1000,  # J/kg-K
            thermal_absorptance=0.9,
            solar_absorptance=0.7,
            visible_absorptance=0.7
        )
        
        materials['Insulation_Cellulose_R21'] = Material(
            name='Insulation_Cellulose_R21',
            material_type='Material',
            thickness=0.1524,  # 6 inches
            conductivity=0.040,  # W/m-K
            density=35,  # kg/m³
            specific_heat=1380,  # J/kg-K
            thermal_absorptance=0.9,
            solar_absorptance=0.7,
            visible_absorptance=0.7
        )
        
        # === GYPSUM BOARD ===
        materials['Gypsum_Board_1_2'] = Material(
            name='Gypsum_Board_1_2',
            material_type='Material',
            thickness=0.0127,  # 1/2 inch
            conductivity=0.16,  # W/m-K
            density=800,  # kg/m³
            specific_heat=1090,  # J/kg-K
            thermal_absorptance=0.9,
            solar_absorptance=0.7,
            visible_absorptance=0.7
        )
        
        materials['Gypsum_Board_5_8'] = Material(
            name='Gypsum_Board_5_8',
            material_type='Material',
            thickness=0.0159,  # 5/8 inch
            conductivity=0.16,
            density=800,
            specific_heat=1090,
            thermal_absorptance=0.9,
            solar_absorptance=0.7,
            visible_absorptance=0.7
        )
        
        # === STEEL FRAMING ===
        materials['Steel_Stud_25ga'] = Material(
            name='Steel_Stud_25ga',
            material_type='Material',
            thickness=0.0005,  # 25 gauge
            conductivity=50.0,  # W/m-K
            density=7850,  # kg/m³
            specific_heat=450,  # J/kg-K
            thermal_absorptance=0.9,
            solar_absorptance=0.7,
            visible_absorptance=0.7
        )
        
        materials['Steel_Stud_20ga'] = Material(
            name='Steel_Stud_20ga',
            material_type='Material',
            thickness=0.001,  # 20 gauge
            conductivity=50.0,
            density=7850,
            specific_heat=450,
            thermal_absorptance=0.9,
            solar_absorptance=0.7,
            visible_absorptance=0.7
        )
        
        # === WOOD MATERIALS ===
        materials['Wood_Stud_2x4'] = Material(
            name='Wood_Stud_2x4',
            material_type='Material',
            thickness=0.0889,  # 3.5 inches
            conductivity=0.12,  # W/m-K
            density=530,  # kg/m³
            specific_heat=1630,  # J/kg-K
            thermal_absorptance=0.9,
            solar_absorptance=0.7,
            visible_absorptance=0.7
        )
        
        materials['Wood_Stud_2x6'] = Material(
            name='Wood_Stud_2x6',
            material_type='Material',
            thickness=0.1397,  # 5.5 inches
            conductivity=0.12,
            density=530,
            specific_heat=1630,
            thermal_absorptance=0.9,
            solar_absorptance=0.7,
            visible_absorptance=0.7
        )
        
        materials['Plywood_1_2'] = Material(
            name='Plywood_1_2',
            material_type='Material',
            thickness=0.0127,  # 1/2 inch
            conductivity=0.12,  # W/m-K
            density=530,  # kg/m³
            specific_heat=1630,  # J/kg-K
            thermal_absorptance=0.9,
            solar_absorptance=0.7,
            visible_absorptance=0.7
        )
        
        # === MASONRY MATERIALS ===
        materials['Brick_Common'] = Material(
            name='Brick_Common',
            material_type='Material',
            thickness=0.1016,  # 4 inches
            conductivity=0.77,  # W/m-K
            density=1920,  # kg/m³
            specific_heat=840,  # J/kg-K
            thermal_absorptance=0.9,
            solar_absorptance=0.65,
            visible_absorptance=0.65
        )
        
        materials['CMU_8in'] = Material(
            name='CMU_8in',
            material_type='Material',
            thickness=0.2032,  # 8 inches
            conductivity=1.4,  # W/m-K
            density=1920,  # kg/m³
            specific_heat=840,  # J/kg-K
            thermal_absorptance=0.9,
            solar_absorptance=0.65,
            visible_absorptance=0.65
        )
        
        # === ROOFING MATERIALS ===
        materials['Roof_Membrane'] = Material(
            name='Roof_Membrane',
            material_type='Material',
            thickness=0.003,  # 3mm
            conductivity=0.16,  # W/m-K
            density=1100,  # kg/m³
            specific_heat=1460,  # J/kg-K
            thermal_absorptance=0.9,
            solar_absorptance=0.7,
            visible_absorptance=0.7
        )
        
        materials['Roof_Insulation_R20'] = Material(
            name='Roof_Insulation_R20',
            material_type='Material',
            thickness=0.127,  # 5 inches
            conductivity=0.035,  # W/m-K
            density=24,  # kg/m³
            specific_heat=1000,  # J/kg-K
            thermal_absorptance=0.9,
            solar_absorptance=0.7,
            visible_absorptance=0.7
        )
        
        # === WINDOW MATERIALS ===
        materials['Window_Single_Clear'] = Material(
            name='Window_Single_Clear',
            material_type='WindowMaterial:SimpleGlazingSystem',
            u_factor=5.7,  # W/m²-K
            solar_heat_gain_coefficient=0.86
        )
        
        materials['Window_Double_Clear'] = Material(
            name='Window_Double_Clear',
            material_type='WindowMaterial:SimpleGlazingSystem',
            u_factor=2.7,  # W/m²-K
            solar_heat_gain_coefficient=0.78
        )
        
        materials['Window_Double_LowE'] = Material(
            name='Window_Double_LowE',
            material_type='WindowMaterial:SimpleGlazingSystem',
            u_factor=1.7,  # W/m²-K
            solar_heat_gain_coefficient=0.45
        )
        
        materials['Window_Triple_LowE'] = Material(
            name='Window_Triple_LowE',
            material_type='WindowMaterial:SimpleGlazingSystem',
            u_factor=1.1,  # W/m²-K
            solar_heat_gain_coefficient=0.35
        )
        
        # === NO-MASS MATERIALS (Air spaces, etc.) ===
        materials['Air_Space_3_4'] = Material(
            name='Air_Space_3_4',
            material_type='Material:NoMass',
            thermal_resistance=0.17,  # m²-K/W
            thermal_absorptance=0.9,
            solar_absorptance=0.7,
            visible_absorptance=0.7
        )
        
        materials['Air_Space_1_2'] = Material(
            name='Air_Space_1_2',
            material_type='Material:NoMass',
            thermal_resistance=0.15,  # m²-K/W
            thermal_absorptance=0.9,
            solar_absorptance=0.7,
            visible_absorptance=0.7
        )
        
        return materials
    
    def _load_constructions(self) -> Dict[str, Construction]:
        """Load ASHRAE 90.1 compliant construction assemblies"""
        constructions = {}
        
        # === WALL CONSTRUCTIONS ===
        # Steel Frame Wall - Climate Zone 1-2
        constructions['Wall_SteelFrame_R13_CZ1_2'] = Construction(
            name='Wall_SteelFrame_R13_CZ1_2',
            materials=['Gypsum_Board_1_2', 'Steel_Stud_25ga', 'Insulation_Fiberglass_R13', 'Gypsum_Board_1_2'],
            u_factor=0.35,  # W/m²-K
            r_value=2.86,  # m²-K/W
            climate_zone='1-2',
            building_type='All'
        )
        
        # Steel Frame Wall - Climate Zone 3-4
        constructions['Wall_SteelFrame_R19_CZ3_4'] = Construction(
            name='Wall_SteelFrame_R19_CZ3_4',
            materials=['Gypsum_Board_1_2', 'Steel_Stud_25ga', 'Insulation_Fiberglass_R19', 'Gypsum_Board_1_2'],
            u_factor=0.25,  # W/m²-K
            r_value=4.0,  # m²-K/W
            climate_zone='3-4',
            building_type='All'
        )
        
        # Steel Frame Wall - Climate Zone 5-8
        constructions['Wall_SteelFrame_R30_CZ5_8'] = Construction(
            name='Wall_SteelFrame_R30_CZ5_8',
            materials=['Gypsum_Board_1_2', 'Steel_Stud_25ga', 'Insulation_Fiberglass_R30', 'Gypsum_Board_1_2'],
            u_factor=0.18,  # W/m²-K
            r_value=5.56,  # m²-K/W
            climate_zone='5-8',
            building_type='All'
        )
        
        # Wood Frame Wall - Climate Zone 1-2
        constructions['Wall_WoodFrame_R13_CZ1_2'] = Construction(
            name='Wall_WoodFrame_R13_CZ1_2',
            materials=['Gypsum_Board_1_2', 'Wood_Stud_2x4', 'Insulation_Fiberglass_R13', 'Gypsum_Board_1_2'],
            u_factor=0.35,  # W/m²-K
            r_value=2.86,  # m²-K/W
            climate_zone='1-2',
            building_type='Residential'
        )
        
        # Wood Frame Wall - Climate Zone 3-4
        constructions['Wall_WoodFrame_R19_CZ3_4'] = Construction(
            name='Wall_WoodFrame_R19_CZ3_4',
            materials=['Gypsum_Board_1_2', 'Wood_Stud_2x6', 'Insulation_Fiberglass_R19', 'Gypsum_Board_1_2'],
            u_factor=0.25,  # W/m²-K
            r_value=4.0,  # m²-K/W
            climate_zone='3-4',
            building_type='Residential'
        )
        
        # Masonry Wall - Climate Zone 1-2
        constructions['Wall_Masonry_R13_CZ1_2'] = Construction(
            name='Wall_Masonry_R13_CZ1_2',
            materials=['Brick_Common', 'Air_Space_3_4', 'Insulation_Fiberglass_R13', 'Gypsum_Board_1_2'],
            u_factor=0.35,  # W/m²-K
            r_value=2.86,  # m²-K/W
            climate_zone='1-2',
            building_type='All'
        )
        
        # Masonry Wall - Climate Zone 3-8
        constructions['Wall_Masonry_R19_CZ3_8'] = Construction(
            name='Wall_Masonry_R19_CZ3_8',
            materials=['Brick_Common', 'Air_Space_3_4', 'Insulation_Fiberglass_R19', 'Gypsum_Board_1_2'],
            u_factor=0.25,  # W/m²-K
            r_value=4.0,  # m²-K/W
            climate_zone='3-8',
            building_type='All'
        )
        
        # === ROOF CONSTRUCTIONS ===
        # Flat Roof - Climate Zone 1-2
        constructions['Roof_Flat_R20_CZ1_2'] = Construction(
            name='Roof_Flat_R20_CZ1_2',
            materials=['Roof_Membrane', 'Roof_Insulation_R20', 'Concrete_Medium'],
            u_factor=0.20,  # W/m²-K
            r_value=5.0,  # m²-K/W
            climate_zone='1-2',
            building_type='All'
        )
        
        # Flat Roof - Climate Zone 3-8
        constructions['Roof_Flat_R30_CZ3_8'] = Construction(
            name='Roof_Flat_R30_CZ3_8',
            materials=['Roof_Membrane', 'Insulation_Fiberglass_R30', 'Concrete_Medium'],
            u_factor=0.15,  # W/m²-K
            r_value=6.67,  # m²-K/W
            climate_zone='3-8',
            building_type='All'
        )
        
        # === FLOOR CONSTRUCTIONS ===
        # Concrete Floor - All Climate Zones
        constructions['Floor_Concrete_R20'] = Construction(
            name='Floor_Concrete_R20',
            materials=['Concrete_Heavy', 'Insulation_SprayFoam_R20', 'Gypsum_Board_1_2'],
            u_factor=0.20,  # W/m²-K
            r_value=5.0,  # m²-K/W
            climate_zone='All',
            building_type='All'
        )
        
        # Wood Floor - Residential
        constructions['Floor_Wood_R20'] = Construction(
            name='Floor_Wood_R20',
            materials=['Plywood_1_2', 'Wood_Stud_2x6', 'Insulation_SprayFoam_R20', 'Gypsum_Board_1_2'],
            u_factor=0.20,  # W/m²-K
            r_value=5.0,  # m²-K/W
            climate_zone='All',
            building_type='Residential'
        )
        
        # === WINDOW CONSTRUCTIONS ===
        # Single Glazing - Climate Zone 1-2
        constructions['Window_Single_CZ1_2'] = Construction(
            name='Window_Single_CZ1_2',
            materials=['Window_Single_Clear'],
            u_factor=5.7,  # W/m²-K
            r_value=0.18,  # m²-K/W
            climate_zone='1-2',
            building_type='All'
        )
        
        # Double Glazing - Climate Zone 3-4
        constructions['Window_Double_CZ3_4'] = Construction(
            name='Window_Double_CZ3_4',
            materials=['Window_Double_Clear'],
            u_factor=2.7,  # W/m²-K
            r_value=0.37,  # m²-K/W
            climate_zone='3-4',
            building_type='All'
        )
        
        # Double Low-E - Climate Zone 5-6
        constructions['Window_DoubleLowE_CZ5_6'] = Construction(
            name='Window_DoubleLowE_CZ5_6',
            materials=['Window_Double_LowE'],
            u_factor=1.7,  # W/m²-K
            r_value=0.59,  # m²-K/W
            climate_zone='5-6',
            building_type='All'
        )
        
        # Triple Low-E - Climate Zone 7-8
        constructions['Window_TripleLowE_CZ7_8'] = Construction(
            name='Window_TripleLowE_CZ7_8',
            materials=['Window_Triple_LowE'],
            u_factor=1.1,  # W/m²-K
            r_value=0.91,  # m²-K/W
            climate_zone='7-8',
            building_type='All'
        )
        
        return constructions
    
    def _load_climate_zones(self) -> Dict[str, str]:
        """Load climate zone mapping"""
        return {
            '1A': '1-2',  # Very Hot - Humid
            '1B': '1-2',  # Very Hot - Dry
            '2A': '1-2',  # Hot - Humid
            '2B': '1-2',  # Hot - Dry
            '3A': '3-4',  # Warm - Humid
            '3B': '3-4',  # Warm - Dry
            '3C': '3-4',  # Warm - Marine
            '4A': '3-4',  # Mixed - Humid
            '4B': '3-4',  # Mixed - Dry
            '4C': '3-4',  # Mixed - Marine
            '5A': '5-8',  # Cool - Humid
            '5B': '5-8',  # Cool - Dry
            '5C': '5-8',  # Cool - Marine
            '6A': '5-8',  # Cold - Humid
            '6B': '5-8',  # Cold - Dry
            '7': '5-8',   # Very Cold
            '8': '5-8'    # Subarctic
        }
    
    def get_construction_assembly(self, building_type: str, climate_zone: str, 
                                surface_type: str, year_built: int = 2020) -> Construction:
        """Get appropriate construction assembly based on building type and climate zone"""
        
        # Map climate zone to construction category
        cz_category = self.climate_zones.get(climate_zone, '3-4')
        
        # Determine if building meets current code (post-2010)
        code_era = 'current' if year_built >= 2010 else 'legacy'
        
        # Select construction based on parameters
        construction_key = f"{surface_type}_{building_type}_{cz_category}_{code_era}"
        
        # Fallback to generic constructions if specific not found
        fallback_key = f"{surface_type}_{cz_category}"
        
        # Try specific construction first, then fallback
        for key in [construction_key, fallback_key]:
            for construction_name, construction in self.constructions.items():
                if (construction.climate_zone == cz_category and 
                    construction.building_type in [building_type, 'All'] and
                    surface_type.lower() in construction_name.lower()):
                    return construction
        
        # Ultimate fallback - return first matching construction
        for construction in self.constructions.values():
            if surface_type.lower() in construction.name.lower():
                return construction
        
        # If nothing found, return a basic construction
        return self._get_basic_construction(surface_type)
    
    def _get_basic_construction(self, surface_type: str) -> Construction:
        """Get basic construction as fallback"""
        if 'wall' in surface_type.lower():
            return Construction(
                name='Basic_Wall',
                materials=['Gypsum_Board_1_2', 'Insulation_Fiberglass_R13', 'Gypsum_Board_1_2'],
                u_factor=0.35,
                r_value=2.86,
                climate_zone='All',
                building_type='All'
            )
        elif 'roof' in surface_type.lower():
            return Construction(
                name='Basic_Roof',
                materials=['Roof_Membrane', 'Roof_Insulation_R20', 'Concrete_Medium'],
                u_factor=0.20,
                r_value=5.0,
                climate_zone='All',
                building_type='All'
            )
        elif 'floor' in surface_type.lower():
            return Construction(
                name='Basic_Floor',
                materials=['Concrete_Heavy', 'Insulation_Fiberglass_R20'],
                u_factor=0.20,
                r_value=5.0,
                climate_zone='All',
                building_type='All'
            )
        else:
            return Construction(
                name='Basic_Window',
                materials=['Window_Double_Clear'],
                u_factor=2.7,
                r_value=0.37,
                climate_zone='All',
                building_type='All'
            )
    
    def generate_material_objects(self, materials_used: List[str]) -> str:
        """Generate EnergyPlus material objects for used materials"""
        material_objects = []
        
        for material_name in materials_used:
            if material_name in self.materials:
                material = self.materials[material_name]
                material_objects.append(self._format_material_object(material))
        
        return '\n\n'.join(material_objects)
    
    def _format_material_object(self, material: Material) -> str:
        """Format material as EnergyPlus object"""
        if material.material_type == 'Material':
            return f"""Material,
         {material.name},                !- Name
         {material.roughness},           !- Roughness
         {material.thickness:.6f},       !- Thickness {{m}}
         {material.conductivity:.6f},    !- Conductivity {{W/m-K}}
         {material.density:.1f},         !- Density {{kg/m3}}
         {material.specific_heat:.1f},   !- Specific Heat {{J/kg-K}}
         {material.thermal_absorptance:.6f}, !- Thermal Absorptance
         {material.solar_absorptance:.6f},   !- Solar Absorptance
         {material.visible_absorptance:.6f}; !- Visible Absorptance"""
        
        elif material.material_type == 'Material:NoMass':
            return f"""Material:NoMass,
         {material.name},                !- Name
         {material.roughness},           !- Roughness
         {material.thermal_resistance:.6f}, !- Thermal Resistance {{m2-K/W}}
         {material.thermal_absorptance:.6f}, !- Thermal Absorptance
         {material.solar_absorptance:.6f},   !- Solar Absorptance
         {material.visible_absorptance:.6f}; !- Visible Absorptance"""
        
        elif material.material_type == 'WindowMaterial:SimpleGlazingSystem':
            return f"""WindowMaterial:SimpleGlazingSystem,
         {material.name},                !- Name
         {material.u_factor:.6f},        !- U-Factor {{W/m2-K}}
         {material.solar_heat_gain_coefficient:.6f}; !- Solar Heat Gain Coefficient"""
        
        return ""
    
    def generate_construction_objects(self, constructions_used: List[str]) -> str:
        """Generate EnergyPlus construction objects for used constructions"""
        construction_objects = []
        
        for construction_name in constructions_used:
            if construction_name in self.constructions:
                construction = self.constructions[construction_name]
                construction_objects.append(self._format_construction_object(construction))
        
        return '\n\n'.join(construction_objects)
    
    def _format_construction_object(self, construction: Construction) -> str:
        """Format construction as EnergyPlus object
        Layers must be separated by commas with a single semicolon at the end.
        """
        material_list = ',\n         '.join(construction.materials)
        return f"""Construction,
         {construction.name},            !- Name
         {material_list};                !- Layer 1 through {len(construction.materials)}"""
    
    def get_construction_materials(self, construction_name: str) -> List[str]:
        """Get list of materials used in a construction"""
        if construction_name in self.constructions:
            return self.constructions[construction_name].materials
        return []
    
    def get_all_materials(self) -> List[str]:
        """Get list of all available materials"""
        return list(self.materials.keys())
    
    def get_all_constructions(self) -> List[str]:
        """Get list of all available constructions"""
        return list(self.constructions.keys())
    
    def get_constructions_by_type(self, surface_type: str) -> List[str]:
        """Get constructions filtered by surface type"""
        return [name for name, construction in self.constructions.items() 
                if surface_type.lower() in name.lower()]
    
    def get_constructions_by_climate_zone(self, climate_zone: str) -> List[str]:
        """Get constructions filtered by climate zone"""
        cz_category = self.climate_zones.get(climate_zone, '3-4')
        return [name for name, construction in self.constructions.items() 
                if construction.climate_zone == cz_category or construction.climate_zone == 'All']
