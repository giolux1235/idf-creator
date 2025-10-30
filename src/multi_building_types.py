"""
Multi-Building Types Support for IDF Creator
Supports 10+ building types with specific templates and parameters
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class BuildingTypeTemplate:
    """Template for a specific building type"""
    name: str
    typical_floor_area: float  # m²
    aspect_ratio_range: Tuple[float, float]
    stories_range: Tuple[int, int]
    window_wall_ratio: float
    occupancy_density: float  # people/m²
    lighting_power_density: float  # W/m²
    equipment_power_density: float  # W/m²
    ventilation_rate: float  # L/s-person
    space_types: List[str]
    hvac_system_type: str
    construction_standard: str  # ASHRAE 90.1, IECC, etc.


class MultiBuildingTypes:
    """Manages multiple building types with specific templates"""
    
    def __init__(self):
        self.building_types = self._load_building_type_templates()
        self.space_templates = self._load_space_templates()
        self.hvac_templates = self._load_hvac_templates()
    
    def _load_building_type_templates(self) -> Dict[str, BuildingTypeTemplate]:
        """Load building type templates"""
        return {
            'office': BuildingTypeTemplate(
                name='Office',
                typical_floor_area=2000,  # m²
                aspect_ratio_range=(1.2, 2.5),
                stories_range=(1, 50),
                window_wall_ratio=0.4,
                occupancy_density=0.05,  # 5 people per 100 m²
                lighting_power_density=10.8,  # W/m² (ASHRAE 90.1)
                equipment_power_density=8.1,  # W/m² (ASHRAE 90.1)
                ventilation_rate=2.5,  # L/s-person
                space_types=['office_open', 'office_private', 'conference', 'break_room', 'lobby', 'storage', 'mechanical'],
                hvac_system_type='VAV',
                construction_standard='ASHRAE 90.1'
            ),
            
            'residential_single': BuildingTypeTemplate(
                name='Single-Family Residential',
                typical_floor_area=150,  # m²
                aspect_ratio_range=(1.0, 1.8),
                stories_range=(1, 3),
                window_wall_ratio=0.15,
                occupancy_density=0.04,  # 4 people per 100 m²
                lighting_power_density=6.5,  # W/m² (IECC)
                equipment_power_density=3.2,  # W/m² (IECC)
                ventilation_rate=0.35,  # L/s-m²
                space_types=['living', 'kitchen', 'bedroom', 'bathroom', 'dining', 'storage'],
                hvac_system_type='HeatPump',
                construction_standard='IECC'
            ),
            
            'residential_multi': BuildingTypeTemplate(
                name='Multi-Family Residential',
                typical_floor_area=1000,  # m²
                aspect_ratio_range=(1.0, 2.0),
                stories_range=(2, 20),
                window_wall_ratio=0.25,
                occupancy_density=0.03,  # 3 people per 100 m²
                lighting_power_density=6.5,  # W/m² (IECC)
                equipment_power_density=3.2,  # W/m² (IECC)
                ventilation_rate=0.35,  # L/s-m²
                space_types=['apartment', 'corridor', 'lobby', 'storage', 'mechanical'],
                hvac_system_type='PTAC',
                construction_standard='IECC'
            ),
            
            'retail': BuildingTypeTemplate(
                name='Retail',
                typical_floor_area=5000,  # m²
                aspect_ratio_range=(1.0, 3.0),
                stories_range=(1, 3),
                window_wall_ratio=0.2,
                occupancy_density=0.15,  # 15 people per 100 m²
                lighting_power_density=12.9,  # W/m² (ASHRAE 90.1)
                equipment_power_density=8.1,  # W/m² (ASHRAE 90.1)
                ventilation_rate=2.5,  # L/s-person
                space_types=['sales_floor', 'storage', 'office', 'break_room', 'fitting_room', 'customer_service', 'mechanical'],
                hvac_system_type='RTU',
                construction_standard='ASHRAE 90.1'
            ),
            
            'healthcare_hospital': BuildingTypeTemplate(
                name='Hospital',
                typical_floor_area=3000,  # m²
                aspect_ratio_range=(1.0, 2.0),
                stories_range=(2, 20),
                window_wall_ratio=0.3,
                occupancy_density=0.1,  # 10 people per 100 m²
                lighting_power_density=10.8,  # W/m² (ASHRAE 90.1)
                equipment_power_density=15.0,  # W/m² (ASHRAE 90.1)
                ventilation_rate=2.5,  # L/s-person
                space_types=['patient_room', 'nurse_station', 'operating_room', 'lab', 'radiology', 'pharmacy', 'mechanical'],
                hvac_system_type='ChilledWater',
                construction_standard='ASHRAE 90.1'
            ),
            
            'healthcare_clinic': BuildingTypeTemplate(
                name='Medical Clinic',
                typical_floor_area=1000,  # m²
                aspect_ratio_range=(1.0, 2.0),
                stories_range=(1, 5),
                window_wall_ratio=0.3,
                occupancy_density=0.08,  # 8 people per 100 m²
                lighting_power_density=10.8,  # W/m² (ASHRAE 90.1)
                equipment_power_density=12.0,  # W/m² (ASHRAE 90.1)
                ventilation_rate=2.5,  # L/s-person
                space_types=['exam_room', 'waiting_room', 'office', 'lab', 'storage', 'mechanical'],
                hvac_system_type='VAV',
                construction_standard='ASHRAE 90.1'
            ),
            
            'education_school': BuildingTypeTemplate(
                name='K-12 School',
                typical_floor_area=2500,  # m²
                aspect_ratio_range=(1.0, 2.5),
                stories_range=(1, 3),
                window_wall_ratio=0.25,
                occupancy_density=0.2,  # 20 people per 100 m²
                lighting_power_density=12.9,  # W/m² (ASHRAE 90.1)
                equipment_power_density=3.2,  # W/m² (ASHRAE 90.1)
                ventilation_rate=2.5,  # L/s-person
                space_types=['classroom', 'gymnasium', 'cafeteria', 'library', 'office', 'storage', 'mechanical'],
                hvac_system_type='VAV',
                construction_standard='ASHRAE 90.1'
            ),
            
            'education_university': BuildingTypeTemplate(
                name='University Building',
                typical_floor_area=3000,  # m²
                aspect_ratio_range=(1.0, 2.0),
                stories_range=(2, 10),
                window_wall_ratio=0.3,
                occupancy_density=0.1,  # 10 people per 100 m²
                lighting_power_density=10.8,  # W/m² (ASHRAE 90.1)
                equipment_power_density=8.1,  # W/m² (ASHRAE 90.1)
                ventilation_rate=2.5,  # L/s-person
                space_types=['classroom', 'lecture_hall', 'lab', 'office', 'library', 'storage', 'mechanical'],
                hvac_system_type='VAV',
                construction_standard='ASHRAE 90.1'
            ),
            
            'industrial_warehouse': BuildingTypeTemplate(
                name='Warehouse',
                typical_floor_area=10000,  # m²
                aspect_ratio_range=(1.0, 4.0),
                stories_range=(1, 2),
                window_wall_ratio=0.1,
                occupancy_density=0.01,  # 1 person per 100 m²
                lighting_power_density=5.4,  # W/m² (ASHRAE 90.1)
                equipment_power_density=1.1,  # W/m² (ASHRAE 90.1)
                ventilation_rate=0.2,  # L/s-m²
                space_types=['warehouse_floor', 'office', 'loading_dock', 'storage', 'mechanical'],
                hvac_system_type='RTU',
                construction_standard='ASHRAE 90.1'
            ),
            
            'industrial_manufacturing': BuildingTypeTemplate(
                name='Manufacturing',
                typical_floor_area=5000,  # m²
                aspect_ratio_range=(1.0, 3.0),
                stories_range=(1, 3),
                window_wall_ratio=0.1,
                occupancy_density=0.02,  # 2 people per 100 m²
                lighting_power_density=10.8,  # W/m² (ASHRAE 90.1)
                equipment_power_density=15.0,  # W/m² (ASHRAE 90.1)
                ventilation_rate=0.5,  # L/s-m²
                space_types=['production_floor', 'office', 'storage', 'mechanical'],
                hvac_system_type='RTU',
                construction_standard='ASHRAE 90.1'
            ),
            
            'hospitality_hotel': BuildingTypeTemplate(
                name='Hotel',
                typical_floor_area=2000,  # m²
                aspect_ratio_range=(1.0, 2.0),
                stories_range=(3, 30),
                window_wall_ratio=0.3,
                occupancy_density=0.05,  # 5 people per 100 m²
                lighting_power_density=8.1,  # W/m² (ASHRAE 90.1)
                equipment_power_density=5.4,  # W/m² (ASHRAE 90.1)
                ventilation_rate=2.5,  # L/s-person
                space_types=['guest_room', 'corridor', 'lobby', 'restaurant', 'meeting_room', 'storage', 'mechanical'],
                hvac_system_type='PTAC',
                construction_standard='ASHRAE 90.1'
            ),
            
            'hospitality_restaurant': BuildingTypeTemplate(
                name='Restaurant',
                typical_floor_area=500,  # m²
                aspect_ratio_range=(1.0, 2.0),
                stories_range=(1, 2),
                window_wall_ratio=0.2,
                occupancy_density=0.3,  # 30 people per 100 m²
                lighting_power_density=12.9,  # W/m² (ASHRAE 90.1)
                equipment_power_density=20.0,  # W/m² (ASHRAE 90.1)
                ventilation_rate=2.5,  # L/s-person
                space_types=['dining_room', 'kitchen', 'storage', 'office', 'mechanical'],
                hvac_system_type='RTU',
                construction_standard='ASHRAE 90.1'
            ),
            
            'mixed_use': BuildingTypeTemplate(
                name='Mixed-Use',
                typical_floor_area=3000,  # m²
                aspect_ratio_range=(1.0, 2.0),
                stories_range=(3, 20),
                window_wall_ratio=0.35,
                occupancy_density=0.08,  # 8 people per 100 m²
                lighting_power_density=10.8,  # W/m² (ASHRAE 90.1)
                equipment_power_density=8.1,  # W/m² (ASHRAE 90.1)
                ventilation_rate=2.5,  # L/s-person
                space_types=['office', 'retail', 'residential', 'storage', 'mechanical'],
                hvac_system_type='VAV',
                construction_standard='ASHRAE 90.1'
            )
        }
    
    def _load_space_templates(self) -> Dict[str, Dict]:
        """Load space type templates for detailed space planning"""
        return {
            'office_open': {
                'occupancy_density': 0.05,  # people/m²
                'lighting_power_density': 10.8,  # W/m²
                'equipment_power_density': 8.1,  # W/m²
                'ventilation_rate': 2.5,  # L/s-person
                'typical_area_range': (50, 500),  # m²
                'schedule_type': 'office'
            },
            'office_private': {
                'occupancy_density': 0.05,
                'lighting_power_density': 10.8,
                'equipment_power_density': 8.1,
                'ventilation_rate': 2.5,
                'typical_area_range': (15, 50),
                'schedule_type': 'office'
            },
            'conference': {
                'occupancy_density': 0.2,
                'lighting_power_density': 10.8,
                'equipment_power_density': 8.1,
                'ventilation_rate': 2.5,
                'typical_area_range': (30, 100),
                'schedule_type': 'conference'
            },
            'break_room': {
                'occupancy_density': 0.1,
                'lighting_power_density': 8.1,
                'equipment_power_density': 15.0,
                'ventilation_rate': 2.5,
                'typical_area_range': (20, 80),
                'schedule_type': 'break_room'
            },
            'lobby': {
                'occupancy_density': 0.05,
                'lighting_power_density': 12.9,
                'equipment_power_density': 3.2,
                'ventilation_rate': 2.5,
                'typical_area_range': (50, 200),
                'schedule_type': 'lobby'
            },
            'storage': {
                'occupancy_density': 0.01,
                'lighting_power_density': 5.4,
                'equipment_power_density': 1.1,
                'ventilation_rate': 0.2,  # L/s-m²
                'typical_area_range': (10, 100),
                'schedule_type': 'storage'
            },
            'mechanical': {
                'occupancy_density': 0.0,
                'lighting_power_density': 5.4,
                'equipment_power_density': 0.0,
                'ventilation_rate': 0.0,
                'typical_area_range': (20, 150),
                'schedule_type': 'mechanical'
            },
            'living': {
                'occupancy_density': 0.04,
                'lighting_power_density': 6.5,
                'equipment_power_density': 3.2,
                'ventilation_rate': 0.35,  # L/s-m²
                'typical_area_range': (20, 60),
                'schedule_type': 'residential'
            },
            'kitchen': {
                'occupancy_density': 0.04,
                'lighting_power_density': 8.1,
                'equipment_power_density': 10.0,
                'ventilation_rate': 0.35,  # L/s-m²
                'typical_area_range': (10, 30),
                'schedule_type': 'residential'
            },
            'bedroom': {
                'occupancy_density': 0.04,
                'lighting_power_density': 6.5,
                'equipment_power_density': 2.0,
                'ventilation_rate': 0.35,  # L/s-m²
                'typical_area_range': (12, 25),
                'schedule_type': 'residential'
            },
            'bathroom': {
                'occupancy_density': 0.04,
                'lighting_power_density': 6.5,
                'equipment_power_density': 1.0,
                'ventilation_rate': 0.35,  # L/s-m²
                'typical_area_range': (5, 15),
                'schedule_type': 'residential'
            },
            'sales_floor': {
                'occupancy_density': 0.15,
                'lighting_power_density': 12.9,
                'equipment_power_density': 8.1,
                'ventilation_rate': 2.5,
                'typical_area_range': (500, 3000),
                'schedule_type': 'retail'
            },
            'classroom': {
                'occupancy_density': 0.2,
                'lighting_power_density': 12.9,
                'equipment_power_density': 3.2,
                'ventilation_rate': 2.5,
                'typical_area_range': (50, 100),
                'schedule_type': 'education'
            },
            'patient_room': {
                'occupancy_density': 0.1,
                'lighting_power_density': 10.8,
                'equipment_power_density': 15.0,
                'ventilation_rate': 2.5,
                'typical_area_range': (20, 40),
                'schedule_type': 'healthcare'
            },
            'warehouse_floor': {
                'occupancy_density': 0.01,
                'lighting_power_density': 5.4,
                'equipment_power_density': 1.1,
                'ventilation_rate': 0.2,  # L/s-m²
                'typical_area_range': (1000, 5000),
                'schedule_type': 'industrial'
            }
        }
    
    def _load_hvac_templates(self) -> Dict[str, Dict]:
        """Load HVAC system templates"""
        return {
            'VAV': {
                'system_type': 'Variable Air Volume',
                'heating_fuel': 'Electric',
                'cooling_fuel': 'Electric',
                'efficiency': 'High',
                'controls': 'Advanced',
                'zoning': 'Multiple'
            },
            'RTU': {
                'system_type': 'Rooftop Unit',
                'heating_fuel': 'Gas',
                'cooling_fuel': 'Electric',
                'efficiency': 'Standard',
                'controls': 'Basic',
                'zoning': 'Single'
            },
            'PTAC': {
                'system_type': 'Packaged Terminal Air Conditioner',
                'heating_fuel': 'Electric',
                'cooling_fuel': 'Electric',
                'efficiency': 'Standard',
                'controls': 'Basic',
                'zoning': 'Individual'
            },
            'HeatPump': {
                'system_type': 'Heat Pump',
                'heating_fuel': 'Electric',
                'cooling_fuel': 'Electric',
                'efficiency': 'High',
                'controls': 'Advanced',
                'zoning': 'Multiple'
            },
            'ChilledWater': {
                'system_type': 'Chilled Water',
                'heating_fuel': 'Gas',
                'cooling_fuel': 'Electric',
                'efficiency': 'High',
                'controls': 'Advanced',
                'zoning': 'Multiple'
            }
        }
    
    def get_building_type_template(self, building_type: str) -> Optional[BuildingTypeTemplate]:
        """Get building type template"""
        return self.building_types.get(building_type)
    
    def get_available_building_types(self) -> List[str]:
        """Get list of available building types"""
        return list(self.building_types.keys())
    
    def get_space_template(self, space_type: str) -> Optional[Dict]:
        """Get space type template"""
        return self.space_templates.get(space_type)
    
    def get_hvac_template(self, hvac_type: str) -> Optional[Dict]:
        """Get HVAC system template"""
        return self.hvac_templates.get(hvac_type)
    
    def estimate_building_parameters(self, building_type: str, total_area: float, 
                                   stories: int) -> Dict:
        """Estimate building parameters based on type and size"""
        template = self.get_building_type_template(building_type)
        if not template:
            template = self.get_building_type_template('office')  # Default fallback
        
        # Calculate parameters
        # Handle None stories
        if stories is None or stories <= 0:
            stories = 3
        
        floor_area = total_area / stories
        
        # Adjust for building type
        if building_type in ['residential_single', 'residential_multi']:
            # Residential has different occupancy patterns
            occupancy_density = template.occupancy_density
        else:
            # Commercial buildings
            occupancy_density = template.occupancy_density
        
        return {
            'building_type': building_type,
            'total_area': total_area,
            'floor_area': floor_area,
            'stories': stories,
            'window_wall_ratio': template.window_wall_ratio,
            'occupancy_density': occupancy_density,
            'lighting_power_density': template.lighting_power_density,
            'equipment_power_density': template.equipment_power_density,
            'ventilation_rate': template.ventilation_rate,
            'space_types': template.space_types,
            'hvac_system_type': template.hvac_system_type,
            'construction_standard': template.construction_standard
        }
    
    def generate_space_schedule(self, space_type: str, building_type: str) -> Dict:
        """Generate occupancy schedule for space type"""
        space_template = self.get_space_template(space_type)
        if not space_template:
            space_template = self.get_space_template('office_open')  # Default
        
        schedule_type = space_template['schedule_type']
        
        # Generate schedule based on type
        if schedule_type == 'office':
            return self._generate_office_schedule()
        elif schedule_type == 'residential':
            return self._generate_residential_schedule()
        elif schedule_type == 'retail':
            return self._generate_retail_schedule()
        elif schedule_type == 'education':
            return self._generate_education_schedule()
        elif schedule_type == 'healthcare':
            return self._generate_healthcare_schedule()
        elif schedule_type == 'industrial':
            return self._generate_industrial_schedule()
        else:
            return self._generate_default_schedule()
    
    def _generate_office_schedule(self) -> Dict:
        """Generate office occupancy schedule"""
        return {
            'occupancy': {
                'weekday': [0.0] * 6 + [0.1] * 2 + [0.8] * 8 + [0.1] * 2 + [0.0] * 6,  # 6am-6pm
                'weekend': [0.0] * 24
            },
            'lighting': {
                'weekday': [0.0] * 6 + [0.1] * 2 + [1.0] * 8 + [0.1] * 2 + [0.0] * 6,
                'weekend': [0.0] * 24
            },
            'equipment': {
                'weekday': [0.0] * 6 + [0.1] * 2 + [0.8] * 8 + [0.1] * 2 + [0.0] * 6,
                'weekend': [0.0] * 24
            }
        }
    
    def _generate_residential_schedule(self) -> Dict:
        """Generate residential occupancy schedule"""
        return {
            'occupancy': {
                'weekday': [1.0] * 8 + [0.2] * 8 + [1.0] * 8,  # Sleep, away, home
                'weekend': [1.0] * 12 + [0.8] * 4 + [1.0] * 8  # More time at home
            },
            'lighting': {
                'weekday': [0.1] * 6 + [0.3] * 2 + [0.1] * 8 + [0.5] * 4 + [0.1] * 4,
                'weekend': [0.1] * 8 + [0.4] * 8 + [0.1] * 8
            },
            'equipment': {
                'weekday': [0.1] * 6 + [0.2] * 2 + [0.1] * 8 + [0.3] * 4 + [0.1] * 4,
                'weekend': [0.1] * 8 + [0.3] * 8 + [0.1] * 8
            }
        }
    
    def _generate_retail_schedule(self) -> Dict:
        """Generate retail occupancy schedule"""
        return {
            'occupancy': {
                'weekday': [0.0] * 8 + [0.3] * 2 + [0.8] * 8 + [0.5] * 2 + [0.0] * 4,  # 10am-8pm
                'weekend': [0.0] * 9 + [0.5] * 1 + [0.9] * 8 + [0.6] * 2 + [0.0] * 4  # 10am-8pm, busier
            },
            'lighting': {
                'weekday': [0.0] * 8 + [0.2] * 2 + [1.0] * 8 + [0.3] * 2 + [0.0] * 4,
                'weekend': [0.0] * 9 + [0.3] * 1 + [1.0] * 8 + [0.4] * 2 + [0.0] * 4
            },
            'equipment': {
                'weekday': [0.0] * 8 + [0.2] * 2 + [0.8] * 8 + [0.3] * 2 + [0.0] * 4,
                'weekend': [0.0] * 9 + [0.3] * 1 + [0.9] * 8 + [0.4] * 2 + [0.0] * 4
            }
        }
    
    def _generate_education_schedule(self) -> Dict:
        """Generate education occupancy schedule"""
        return {
            'occupancy': {
                'weekday': [0.0] * 7 + [0.9] * 8 + [0.1] * 1 + [0.0] * 8,  # 7am-4pm
                'weekend': [0.0] * 24  # Closed weekends
            },
            'lighting': {
                'weekday': [0.0] * 7 + [1.0] * 8 + [0.2] * 1 + [0.0] * 8,
                'weekend': [0.0] * 24
            },
            'equipment': {
                'weekday': [0.0] * 7 + [0.8] * 8 + [0.1] * 1 + [0.0] * 8,
                'weekend': [0.0] * 24
            }
        }
    
    def _generate_healthcare_schedule(self) -> Dict:
        """Generate healthcare occupancy schedule"""
        return {
            'occupancy': {
                'weekday': [0.3] * 8 + [0.8] * 8 + [0.5] * 8,  # 24/7 operation
                'weekend': [0.2] * 8 + [0.6] * 8 + [0.3] * 8
            },
            'lighting': {
                'weekday': [0.3] * 8 + [1.0] * 8 + [0.5] * 8,
                'weekend': [0.2] * 8 + [0.8] * 8 + [0.3] * 8
            },
            'equipment': {
                'weekday': [0.2] * 8 + [0.9] * 8 + [0.4] * 8,
                'weekend': [0.1] * 8 + [0.7] * 8 + [0.2] * 8
            }
        }
    
    def _generate_industrial_schedule(self) -> Dict:
        """Generate industrial occupancy schedule"""
        return {
            'occupancy': {
                'weekday': [0.0] * 6 + [0.8] * 12 + [0.0] * 6,  # 6am-6pm
                'weekend': [0.0] * 24  # Closed weekends
            },
            'lighting': {
                'weekday': [0.0] * 6 + [1.0] * 12 + [0.0] * 6,
                'weekend': [0.0] * 24
            },
            'equipment': {
                'weekday': [0.0] * 6 + [0.9] * 12 + [0.0] * 6,
                'weekend': [0.0] * 24
            }
        }
    
    def _generate_default_schedule(self) -> Dict:
        """Generate default occupancy schedule"""
        return {
            'occupancy': {
                'weekday': [0.0] * 6 + [0.5] * 12 + [0.0] * 6,
                'weekend': [0.0] * 24
            },
            'lighting': {
                'weekday': [0.0] * 6 + [0.8] * 12 + [0.0] * 6,
                'weekend': [0.0] * 24
            },
            'equipment': {
                'weekday': [0.0] * 6 + [0.6] * 12 + [0.0] * 6,
                'weekend': [0.0] * 24
            }
        }

