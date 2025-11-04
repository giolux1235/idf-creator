"""
Advanced Ground Coupling Module
Includes climate-specific ground temperatures and detailed ground modeling
Expert-level feature for basement and slab-on-grade buildings
"""

from typing import Dict, Optional


class AdvancedGroundCoupling:
    """Manages advanced ground coupling features"""
    
    def __init__(self):
        self.climate_templates = self._load_climate_templates()
    
    def _load_climate_templates(self) -> Dict:
        """Load climate-specific ground temperature templates"""
        # Based on ASHRAE climate zone ground temperature data
        return {
            'C1': {  # Very Hot-Humid
                'building_surface': [24.0, 23.0, 22.0, 21.0, 22.0, 24.0,
                                     26.0, 27.0, 27.0, 26.0, 25.0, 24.0],
                'shallow': [22.0, 21.0, 20.0, 19.0, 20.0, 22.0,
                           24.0, 25.0, 25.0, 24.0, 23.0, 22.0],
                'deep': [20.0, 19.0, 18.0, 17.0, 18.0, 20.0,
                        22.0, 23.0, 23.0, 22.0, 21.0, 20.0]
            },
            'C2': {  # Hot-Humid
                'building_surface': [22.0, 21.0, 20.0, 19.0, 20.0, 22.0,
                                     24.0, 25.0, 25.0, 24.0, 23.0, 22.0],
                'shallow': [20.0, 19.0, 18.0, 17.0, 18.0, 20.0,
                           22.0, 23.0, 23.0, 22.0, 21.0, 20.0],
                'deep': [18.0, 17.0, 16.0, 15.0, 16.0, 18.0,
                        20.0, 21.0, 21.0, 20.0, 19.0, 18.0]
            },
            'C3': {  # Hot-Dry
                'building_surface': [20.0, 19.0, 18.0, 17.0, 18.0, 20.0,
                                     22.0, 23.0, 23.0, 22.0, 21.0, 20.0],
                'shallow': [18.0, 17.0, 16.0, 15.0, 16.0, 18.0,
                           20.0, 21.0, 21.0, 20.0, 19.0, 18.0],
                'deep': [16.0, 15.0, 14.0, 13.0, 14.0, 16.0,
                        18.0, 19.0, 19.0, 18.0, 17.0, 16.0]
            },
            'C4': {  # Mixed-Dry
                'building_surface': [16.0, 15.0, 14.0, 13.0, 14.0, 16.0,
                                     18.0, 19.0, 19.0, 18.0, 17.0, 16.0],
                'shallow': [14.0, 13.0, 12.0, 11.0, 12.0, 14.0,
                           16.0, 17.0, 17.0, 16.0, 15.0, 14.0],
                'deep': [12.0, 11.0, 10.0, 9.0, 10.0, 12.0,
                        14.0, 15.0, 15.0, 14.0, 13.0, 12.0]
            },
            'C5': {  # Mixed (default)
                'building_surface': [13.0, 12.0, 11.0, 10.0, 11.0, 13.0,
                                     15.0, 16.0, 16.0, 15.0, 14.0, 13.0],
                'shallow': [11.0, 10.0, 9.0, 8.0, 9.0, 11.0,
                           13.0, 14.0, 14.0, 13.0, 12.0, 11.0],
                'deep': [9.0, 8.0, 7.0, 6.0, 7.0, 9.0,
                        11.0, 12.0, 12.0, 11.0, 10.0, 9.0]
            },
            'C6': {  # Cold
                'building_surface': [10.0, 9.0, 8.0, 7.0, 8.0, 10.0,
                                     12.0, 13.0, 13.0, 12.0, 11.0, 10.0],
                'shallow': [8.0, 7.0, 6.0, 5.0, 6.0, 8.0,
                           10.0, 11.0, 11.0, 10.0, 9.0, 8.0],
                'deep': [6.0, 5.0, 4.0, 3.0, 4.0, 6.0,
                        8.0, 9.0, 9.0, 8.0, 7.0, 6.0]
            },
            'C7': {  # Very Cold
                'building_surface': [7.0, 6.0, 5.0, 4.0, 5.0, 7.0,
                                     9.0, 10.0, 10.0, 9.0, 8.0, 7.0],
                'shallow': [5.0, 4.0, 3.0, 2.0, 3.0, 5.0,
                           7.0, 8.0, 8.0, 7.0, 6.0, 5.0],
                'deep': [3.0, 2.0, 1.0, 0.0, 1.0, 3.0,
                        5.0, 6.0, 6.0, 5.0, 4.0, 3.0]
            },
            'C8': {  # Subarctic
                'building_surface': [4.0, 3.0, 2.0, 1.0, 2.0, 4.0,
                                     6.0, 7.0, 7.0, 6.0, 5.0, 4.0],
                'shallow': [2.0, 1.0, 0.0, -1.0, 0.0, 2.0,
                           4.0, 5.0, 5.0, 4.0, 3.0, 2.0],
                'deep': [0.0, -1.0, -2.0, -3.0, -2.0, 0.0,
                        2.0, 3.0, 3.0, 2.0, 1.0, 0.0]
            }
        }
    
    def generate_ground_temperatures(self, climate_zone: str) -> str:
        """Generate climate-specific ground temperature objects"""
        # Extract climate zone number (e.g., 'C5' -> 'C5')
        zone_key = climate_zone if climate_zone in self.climate_templates else 'C5'
        template = self.climate_templates[zone_key]
        
        # Clamp ground temperatures to EnergyPlus recommended range (15-25°C for building surface)
        # EnergyPlus warns if values fall outside this range
        building_surface_clamped = [max(15.0, min(25.0, t)) for t in template['building_surface']]
        # For shallow and deep, use original values (they don't have the same restriction)
        # But we can still ensure building_surface is in range
        
        # Format monthly temperatures (Jan-Dec)
        building_surface_temps = ', '.join([f"{t:.1f}" for t in building_surface_clamped])
        shallow_temps = ', '.join([f"{t:.1f}" for t in template['shallow']])
        deep_temps = ', '.join([f"{t:.1f}" for t in template['deep']])
        
        ground_temps = f"""Site:GroundTemperature:BuildingSurface,
  {building_surface_temps};  !- January through December Ground Temperatures {{C}}

Site:GroundTemperature:Shallow,
  {shallow_temps};  !- January through December Ground Temperatures at 0.5m Depth {{C}}

Site:GroundTemperature:Deep,
  {deep_temps};  !- January through December Ground Temperatures at 3.0m Depth {{C}}

"""
        return ground_temps
    
    def should_add_ground_coupling(self, building_type: str, has_basement: bool = False,
                                  has_slab: bool = True) -> bool:
        """Determine if ground coupling should be added"""
        # Always add for basements
        if has_basement:
            return True
        
        # Add for slab-on-grade in cold climates (C6, C7, C8)
        # In warmer climates, ground coupling less critical for slabs
        return has_slab
    
    def generate_ground_surface(self, surface_name: str, zone_name: str,
                               surface_type: str = 'Floor',
                               construction_name: str = 'Ground_Construction') -> str:
        """Generate ground-coupled surface (for basements or slabs)"""
        
        # Ground surface object
        ground_surface = f"""Surface,
  {surface_name},                      !- Name
  {surface_type},                      !- Surface Type
  {construction_name},                 !- Construction Name
  {zone_name},                         !- Zone Name
  ,                                    !- Space Name
  Ground,                              !- Outside Boundary Condition
  ,                                    !- Outside Boundary Condition Object
  NoSun,                               !- Sun Exposure
  NoWind,                              !- Wind Exposure
  1.0,                                 !- View Factor to Ground
  4,                                   !- Number of Vertices
  0.0, 0.0, 0.0,                       !- Vertex 1 X, Y, Z {{m}}
  10.0, 0.0, 0.0,                      !- Vertex 2 X, Y, Z {{m}}
  10.0, 10.0, 0.0,                     !- Vertex 3 X, Y, Z {{m}}
  0.0, 10.0, 0.0;                      !- Vertex 4 X, Y, Z {{m}}

"""
        return ground_surface












