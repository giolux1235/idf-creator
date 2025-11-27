"""
Output Variable Manager for IDF Files
Manages output variables similar to BESTEST reporting measures.
Automatically injects required output variables for comprehensive analysis.
"""

from typing import List, Dict, Set
import re


class OutputVariableManager:
    """
    Manages output variables for IDF files.
    Similar to BESTEST reporting measures that inject output variables.
    """
    
    # BESTEST-required output variables (from ASHRAE Standard 140)
    BESTEST_REQUIRED_OUTPUTS = [
        # Zone-level outputs
        'Zone Mean Air Temperature',
        'Zone Air Temperature',
        'Zone Total Heating Energy',
        'Zone Total Cooling Energy',
        'Zone Ideal Loads Zone Total Heating Energy',
        'Zone Ideal Loads Zone Total Cooling Energy',
        'Zone Ideal Loads Zone Sensible Heating Energy',
        'Zone Ideal Loads Zone Sensible Cooling Energy',
        'Zone Ideal Loads Zone Latent Heating Energy',
        'Zone Ideal Loads Zone Latent Cooling Energy',
        
        # Surface-level outputs
        'Surface Inside Face Temperature',
        'Surface Outside Face Temperature',
        'Surface Inside Face Conduction Heat Transfer Rate',
        'Surface Outside Face Conduction Heat Transfer Rate',
        'Surface Window Heat Gain Rate',
        'Surface Window Heat Loss Rate',
        
        # HVAC system outputs
        'Air System Total Cooling Energy',
        'Air System Total Heating Energy',
        'Air System Electric Energy',
        'Air System DX Cooling Coil Electric Energy',
        'Air System Fan Electric Energy',
        'Unitary System Total Cooling Rate',
        'Unitary System Total Heating Rate',
        
        # Environmental outputs
        'Site Outdoor Air Drybulb Temperature',
        'Site Outdoor Air Relative Humidity',
        'Site Direct Solar Radiation Rate per Area',
        'Site Diffuse Solar Radiation Rate per Area',
        'Site Sky Temperature',
        'Site Wind Speed',
        'Site Wind Direction',
        
        # Building-level outputs
        'Building Total Heating Energy',
        'Building Total Cooling Energy',
        'Building Total Electricity Energy',
        'Building Total Natural Gas Energy',
    ]
    
    # Additional useful outputs for comprehensive analysis
    COMPREHENSIVE_OUTPUTS = [
        # Infiltration and ventilation
        'Zone Infiltration Sensible Heat Gain Energy',
        'Zone Infiltration Sensible Heat Loss Energy',
        'Zone Mechanical Ventilation Sensible Heat Gain Energy',
        'Zone Mechanical Ventilation Sensible Heat Loss Energy',
        
        # Internal loads
        'Zone Lights Electric Energy',
        'Zone Electric Equipment Electric Energy',
        'Zone People Sensible Heating Energy',
        'Zone People Latent Gain Energy',
        
        # System performance
        'System Node Temperature',
        'System Node Mass Flow Rate',
        'System Node Relative Humidity',
    ]
    
    def __init__(self, include_comprehensive: bool = False):
        """
        Initialize the output variable manager.
        
        Args:
            include_comprehensive: If True, include comprehensive outputs beyond BESTEST requirements
        """
        self.include_comprehensive = include_comprehensive
        self.added_variables: Set[str] = set()
    
    def get_required_outputs(self) -> List[str]:
        """Get list of required output variables"""
        outputs = list(self.BESTEST_REQUIRED_OUTPUTS)
        if self.include_comprehensive:
            outputs.extend(self.COMPREHENSIVE_OUTPUTS)
        return outputs
    
    def add_output_variables(self, idf_content: str, 
                           zone_names: List[str] = None,
                           surface_names: List[str] = None,
                           hvac_system_names: List[str] = None) -> str:
        """
        Add output variables to IDF content.
        Similar to how BESTEST reporting measures inject outputs.
        
        Args:
            idf_content: IDF file content as string
            zone_names: List of zone names (if None, will extract from IDF)
            surface_names: List of surface names (if None, will extract from IDF)
            hvac_system_names: List of HVAC system names (if None, will extract from IDF)
            
        Returns:
            IDF content with output variables added
        """
        if zone_names is None:
            zone_names = self._extract_zone_names(idf_content)
        if surface_names is None:
            surface_names = self._extract_surface_names(idf_content)
        if hvac_system_names is None:
            hvac_system_names = self._extract_hvac_system_names(idf_content)
        
        # Check what outputs already exist
        existing_outputs = self._extract_existing_outputs(idf_content)
        
        # Generate new output variable objects
        new_outputs = []
        required_outputs = self.get_required_outputs()
        
        for var_name in required_outputs:
            # Skip if already exists
            if var_name in existing_outputs:
                continue
            
            # Determine reporting frequency and key value
            frequency, key_value = self._determine_output_parameters(var_name, zone_names, 
                                                                     surface_names, hvac_system_names)
            
            if key_value:
                # Create Output:Variable object
                output_obj = self._create_output_variable(var_name, key_value, frequency)
                new_outputs.append(output_obj)
                self.added_variables.add(var_name)
        
        # Insert output variables before the end of the file
        # BESTEST measures typically add outputs before simulation
        if new_outputs:
            # Find a good insertion point (before Output:Table:SummaryReports or at end)
            insertion_point = self._find_insertion_point(idf_content)
            
            if insertion_point > 0:
                idf_content = (idf_content[:insertion_point] + 
                             '\n'.join(new_outputs) + '\n' + 
                             idf_content[insertion_point:])
            else:
                # Append at end
                idf_content += '\n' + '\n'.join(new_outputs) + '\n'
        
        return idf_content
    
    def _extract_zone_names(self, idf_content: str) -> List[str]:
        """Extract zone names from IDF content"""
        pattern = r'Zone,\s*\n\s*([^,\n]+),'
        zones = re.findall(pattern, idf_content, re.MULTILINE)
        return [z.strip() for z in zones]
    
    def _extract_surface_names(self, idf_content: str) -> List[str]:
        """Extract surface names from IDF content"""
        pattern = r'BuildingSurface:Detailed,\s*\n\s*([^,\n]+),'
        surfaces = re.findall(pattern, idf_content, re.MULTILINE)
        return [s.strip() for s in surfaces]
    
    def _extract_hvac_system_names(self, idf_content: str) -> List[str]:
        """Extract HVAC system names from IDF content"""
        systems = []
        
        # Check for various HVAC system types
        patterns = [
            r'ZoneHVAC:IdealLoadsAirSystem,\s*\n\s*([^,\n]+),',
            r'AirLoopHVAC,\s*\n\s*([^,\n]+),',
            r'ZoneHVAC:EquipmentList,\s*\n\s*([^,\n]+),',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, idf_content, re.MULTILINE)
            systems.extend([m.strip() for m in matches])
        
        return systems
    
    def _extract_existing_outputs(self, idf_content: str) -> Set[str]:
        """Extract existing output variable names"""
        pattern = r'Output:Variable[^;]*?Variable Name\s*,\s*\n\s*([^,\n]+)'
        outputs = re.findall(pattern, idf_content, re.DOTALL | re.IGNORECASE)
        return {o.strip() for o in outputs}
    
    def _determine_output_parameters(self, var_name: str, 
                                   zone_names: List[str],
                                   surface_names: List[str],
                                   hvac_system_names: List[str]) -> tuple:
        """
        Determine reporting frequency and key value for an output variable.
        Returns (frequency, key_value)
        """
        # Default frequency
        frequency = 'Hourly'
        
        # Determine key value based on variable type
        if 'Zone' in var_name and not 'ZoneHVAC' in var_name:
            # Zone-level variable
            if zone_names:
                return frequency, zone_names[0]  # Use first zone, or could use '*'
            return None, None
        elif 'Surface' in var_name:
            # Surface-level variable
            if surface_names:
                return frequency, surface_names[0]  # Use first surface, or could use '*'
            return None, None
        elif 'Air System' in var_name or 'Unitary System' in var_name:
            # HVAC system variable
            if hvac_system_names:
                return frequency, hvac_system_names[0]
            return None, None
        elif 'Site' in var_name or 'Building' in var_name:
            # Site or building-level variable
            return frequency, '*'
        else:
            # Default: use first zone
            if zone_names:
                return frequency, zone_names[0]
            return None, None
    
    def _create_output_variable(self, var_name: str, key_value: str, frequency: str) -> str:
        """Create an Output:Variable object string"""
        return f"""Output:Variable,
  {key_value},                    !- Key Value
  {var_name},                     !- Variable Name
  {frequency};                    !- Reporting Frequency"""
    
    def _find_insertion_point(self, idf_content: str) -> int:
        """Find best insertion point for output variables"""
        # Try to find Output:Table:SummaryReports or similar
        patterns = [
            r'(Output:Table:SummaryReports[^;]*?;)',
            r'(Output:SQLite[^;]*?;)',
            r'(Output:Table:Monthly[^;]*?;)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, idf_content, re.DOTALL | re.IGNORECASE)
            if match:
                return match.end()
        
        # If no output objects found, insert before last line
        lines = idf_content.split('\n')
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() and not lines[i].strip().startswith('!'):
                return sum(len(line) + 1 for line in lines[:i+1])
        
        return -1
    
    def get_summary(self) -> Dict:
        """Get summary of added output variables"""
        return {
            'total_added': len(self.added_variables),
            'variables': sorted(list(self.added_variables)),
            'includes_comprehensive': self.include_comprehensive
        }


def add_bestest_outputs(idf_content: str, include_comprehensive: bool = False) -> str:
    """
    Convenience function to add BESTEST-required output variables to IDF.
    
    Args:
        idf_content: IDF file content as string
        include_comprehensive: If True, include comprehensive outputs
        
    Returns:
        IDF content with output variables added
    """
    manager = OutputVariableManager(include_comprehensive=include_comprehensive)
    return manager.add_output_variables(idf_content)


if __name__ == "__main__":
    # Test the output variable manager
    test_idf = """
Version,
  9.2;                    !- Version Identifier

Building,
  Test Building;          !- Name

Zone,
  ZONE_1,                 !- Name
  0.0000,                 !- Direction of Relative North {deg}
  0.0000,                 !- X Origin {m}
  0.0000,                 !- Y Origin {m}
  0.0000,                 !- Z Origin {m}
  1,                       !- Type
  1,                       !- Multiplier
  autocalculate,           !- Ceiling Height {m}
  autocalculate,           !- Volume {m3}
  ,                        !- Floor Area {m2}
  ,                        !- Zone Inside Convection Algorithm
  ,                        !- Zone Outside Convection Algorithm
  ,                        !- Part of Total Floor Area
  Yes;                     !- Ceiling Height Entered If No
"""
    
    manager = OutputVariableManager(include_comprehensive=True)
    result = manager.add_output_variables(test_idf)
    
    print("Added Output Variables:")
    print("=" * 80)
    print(manager.get_summary())
    print("\n" + "=" * 80)
    print("\nIDF with Output Variables:")
    print("=" * 80)
    print(result)

