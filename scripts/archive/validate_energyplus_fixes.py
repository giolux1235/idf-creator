#!/usr/bin/env python3
"""
EnergyPlus IDF Fix Validation Script

This script programmatically validates that all critical fixes from the error analysis
have been properly applied to IDF files.

Fixes validated:
1. AirLoopHVAC duplicate node names (SupplyOutlet vs ZoneEquipmentInlet)
2. Version mismatch (should be 24.2, not 25.1)
3. Ceiling tilt angles (should be ~0°, not 180°)
4. Zone floor area consistency
5. Node connection validation

Usage:
    python validate_energyplus_fixes.py <idf_file_path>
    python validate_energyplus_fixes.py <idf_file_path> --fix  # Auto-fix issues
"""

import re
import sys
import argparse
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import warnings


class IDFValidator:
    """Validates and fixes EnergyPlus IDF files"""
    
    def __init__(self, idf_path: str):
        self.idf_path = Path(idf_path)
        if not self.idf_path.exists():
            raise FileNotFoundError(f"IDF file not found: {idf_path}")
        
        self.content = self.idf_path.read_text()
        self.errors = []
        self.warnings = []
        self.fixes_applied = []
        
    def validate_all(self, auto_fix: bool = False) -> Dict:
        """Run all validation checks"""
        results = {
            'file': str(self.idf_path),
            'errors': [],
            'warnings': [],
            'fixes_applied': [],
            'passed': True
        }
        
        # Run all validations
        self.validate_version()
        self.validate_airloop_nodes()
        self.validate_ceiling_tilts()
        self.validate_zone_floor_areas()
        self.validate_node_connections()
        
        results['errors'] = self.errors
        results['warnings'] = self.warnings
        
        if self.errors:
            results['passed'] = False
        
        # Apply fixes if requested (check if there are fixable errors)
        if auto_fix and self.errors:
            self.apply_fixes()
            results['fixes_applied'] = self.fixes_applied
            results['fixes_applied_count'] = len(self.fixes_applied)
        else:
            results['fixes_applied'] = []
        
        return results
    
    def validate_version(self):
        """Check that version is 24.2 (not 25.1)"""
        version_pattern = r'Version\s*,\s*([\d.]+)'
        match = re.search(version_pattern, self.content, re.IGNORECASE)
        
        if match:
            version = match.group(1).strip()
            if version != '24.2':
                self.errors.append({
                    'type': 'version_mismatch',
                    'message': f'Version is {version}, should be 24.2',
                    'line': self._get_line_number(match.start()),
                    'fix': f'Version,\n  {24.2};'
                })
        else:
            self.warnings.append({
                'type': 'version_missing',
                'message': 'Version object not found in IDF'
            })
    
    def validate_airloop_nodes(self):
        """Check for duplicate node names in AirLoopHVAC objects"""
        # Pattern to match AirLoopHVAC objects
        airloop_pattern = r'AirLoopHVAC\s*,\s*([^,\n]+)(?:[^;]*?)(?:Supply Side Outlet Node Names|supply_side_outlet_node_names)\s*[=:]\s*([^,\n;]+)(?:[^;]*?)(?:Demand Side Inlet Node Names|demand_side_inlet_node_names)\s*[=:]\s*([^,\n;]+)'
        
        # More robust pattern - find AirLoopHVAC blocks
        airloop_blocks = re.finditer(
            r'AirLoopHVAC\s*,\s*([^,\n]+)(.*?);',
            self.content,
            re.DOTALL | re.IGNORECASE
        )
        
        for match in airloop_blocks:
            airloop_name = match.group(1).strip()
            airloop_content = match.group(2)
            
            # Extract supply outlet and demand inlet nodes
            supply_outlet_match = re.search(
                r'(?:Supply Side Outlet Node Names|supply_side_outlet_node_names)\s*[=:]\s*([^,\n;]+)',
                airloop_content,
                re.IGNORECASE
            )
            demand_inlet_match = re.search(
                r'(?:Demand Side Inlet Node Names|demand_side_inlet_node_names)\s*[=:]\s*([^,\n;]+)',
                airloop_content,
                re.IGNORECASE
            )
            
            if supply_outlet_match and demand_inlet_match:
                supply_outlet = supply_outlet_match.group(1).strip().strip('!').strip()
                demand_inlet = demand_inlet_match.group(1).strip().strip('!').strip()
                
                # Check if they're the same (case-insensitive)
                if supply_outlet.upper() == demand_inlet.upper():
                    # Check if supply outlet is ZoneEquipmentInlet (wrong)
                    if 'ZONEEQUIPMENTINLET' in supply_outlet.upper():
                        self.errors.append({
                            'type': 'duplicate_node',
                            'message': f'AirLoopHVAC "{airloop_name}": Supply outlet and demand inlet both use "{supply_outlet}"',
                            'airloop': airloop_name,
                            'supply_outlet': supply_outlet,
                            'demand_inlet': demand_inlet,
                            'line': self._get_line_number(match.start()),
                            'fix': self._generate_airloop_fix(airloop_name, supply_outlet, demand_inlet)
                        })
    
    def _generate_airloop_fix(self, airloop_name: str, current_supply: str, demand_inlet: str) -> str:
        """Generate fix for AirLoopHVAC duplicate node"""
        # Extract zone name from airloop name (e.g., "LOBBY_0_Z1_AirLoop" -> "LOBBY_0_Z1")
        zone_name = airloop_name.replace('_AirLoop', '').replace('_AIRLOOP', '').replace('_Airloop', '')
        new_supply_outlet = f"{zone_name}_SupplyOutlet"
        
        return {
            'old_supply_outlet': current_supply,
            'new_supply_outlet': new_supply_outlet,
            'demand_inlet': demand_inlet
        }
    
    def validate_ceiling_tilts(self):
        """Check ceiling surfaces have tilt ~0° (not 180°)"""
        # Find BuildingSurface:Detailed objects with type Ceiling or Roof
        ceiling_pattern = r'BuildingSurface:Detailed\s*,\s*([^,\n]+)(.*?);'
        
        for match in re.finditer(ceiling_pattern, self.content, re.DOTALL | re.IGNORECASE):
            surface_name = match.group(1).strip()
            surface_content = match.group(2)
            
            # Check if it's a ceiling
            if re.search(r'(?:Surface Type|surface_type)\s*[=:]\s*(?:Ceiling|ceiling)', surface_content, re.IGNORECASE):
                # Find tilt angle
                tilt_match = re.search(r'(\d+\.?\d*)\s*[,\n]', surface_content)
                if tilt_match:
                    # Tilt is usually one of the numeric fields - need to find the right one
                    # In BuildingSurface:Detailed, tilt is typically after boundary condition
                    # Let's look for a number that's 180.0 or close to it
                    numbers = re.findall(r'(\d+\.?\d*)', surface_content)
                    for num_str in numbers:
                        try:
                            num = float(num_str)
                            if 170.0 <= num <= 190.0:  # Likely a tilt angle of 180°
                                # Check if this is actually the tilt field
                                # Tilt comes after boundary conditions, before number of vertices
                                tilt_pos = surface_content.find(num_str)
                                before_tilt = surface_content[:tilt_pos]
                                
                                # If we see boundary condition keywords before this number, it might be tilt
                                if any(keyword in before_tilt.lower() for keyword in ['outdoors', 'ground', 'surface', 'zone']):
                                    self.warnings.append({
                                        'type': 'ceiling_tilt',
                                        'message': f'Ceiling surface "{surface_name}" has tilt angle {num}° (should be ~0°)',
                                        'surface': surface_name,
                                        'current_tilt': num,
                                        'expected_tilt': 0.0
                                    })
                        except ValueError:
                            continue
    
    def validate_zone_floor_areas(self):
        """Check zone floor areas are explicitly set (not autocalculate)"""
        zone_pattern = r'Zone\s*,\s*([^,\n]+)(.*?);'
        
        for match in re.finditer(zone_pattern, self.content, re.DOTALL | re.IGNORECASE):
            zone_name = match.group(1).strip()
            zone_content = match.group(2)
            
            # Find floor area field (8th field in Zone object)
            # Zone fields: Name, Direction, X, Y, Z, Type, Multiplier, Ceiling Height, Volume, Floor Area, ...
            fields = [f.strip() for f in re.split(r',', zone_content)]
            
            if len(fields) >= 10:
                floor_area = fields[9].strip().strip('!').strip()
                
                if floor_area.lower() in ['autocalculate', 'autosize', '']:
                    self.warnings.append({
                        'type': 'zone_floor_area',
                        'message': f'Zone "{zone_name}" has floor area set to "{floor_area}" (should be explicit value)',
                        'zone': zone_name,
                        'current_value': floor_area
                    })
    
    def validate_node_connections(self):
        """Validate node connections are consistent"""
        # Check that SupplyPath inlet matches AirLoopHVAC supply outlet
        airloops = {}
        
        # Extract all AirLoopHVAC supply outlets
        for match in re.finditer(
            r'AirLoopHVAC\s*,\s*([^,\n]+)(.*?);',
            self.content,
            re.DOTALL | re.IGNORECASE
        ):
            airloop_name = match.group(1).strip()
            content = match.group(2)
            
            supply_outlet_match = re.search(
                r'(?:Supply Side Outlet Node Names|supply_side_outlet_node_names)\s*[=:]\s*([^,\n;]+)',
                content,
                re.IGNORECASE
            )
            
            if supply_outlet_match:
                supply_outlet = supply_outlet_match.group(1).strip().strip('!').strip()
                airloops[airloop_name] = supply_outlet
        
        # Check SupplyPath objects
        for match in re.finditer(
            r'AirLoopHVAC:SupplyPath\s*,\s*([^,\n]+)(.*?);',
            self.content,
            re.DOTALL | re.IGNORECASE
        ):
            supply_path_name = match.group(1).strip()
            content = match.group(2)
            
            inlet_match = re.search(
                r'(?:Supply Air Path Inlet Node Name|supply_air_path_inlet_node_name)\s*[=:]\s*([^,\n;]+)',
                content,
                re.IGNORECASE
            )
            
            if inlet_match:
                inlet_node = inlet_match.group(1).strip().strip('!').strip()
                
                # Find corresponding AirLoopHVAC (name might match zone name)
                # SupplyPath name often matches zone name or airloop name
                matching_airloop = None
                for airloop_name, supply_outlet in airloops.items():
                    if supply_path_name in airloop_name or airloop_name.replace('_AirLoop', '') in supply_path_name:
                        matching_airloop = (airloop_name, supply_outlet)
                        break
                
                if matching_airloop:
                    airloop_name, expected_inlet = matching_airloop
                    if inlet_node.upper() != expected_inlet.upper():
                        self.warnings.append({
                            'type': 'node_mismatch',
                            'message': f'SupplyPath "{supply_path_name}" inlet ({inlet_node}) does not match AirLoopHVAC "{airloop_name}" supply outlet ({expected_inlet})',
                            'supply_path': supply_path_name,
                            'airloop': airloop_name,
                            'current_inlet': inlet_node,
                            'expected_inlet': expected_inlet
                        })
    
    def apply_fixes(self):
        """Apply all fixes to the IDF content"""
        # Apply version fix
        for error in self.errors:
            if error['type'] == 'version_mismatch':
                # Fix version number
                self.content = re.sub(
                    r'Version\s*,\s*[\d.]+',
                    f'Version,\n  {24.2}',
                    self.content,
                    flags=re.IGNORECASE
                )
                self.fixes_applied.append('version_fixed')
        
        # Apply AirLoopHVAC node fixes
        for error in self.errors:
            if error['type'] == 'duplicate_node' and 'fix' in error:
                fix = error['fix']
                old_supply = fix['old_supply_outlet']
                new_supply = fix['new_supply_outlet']
                
                # Replace in AirLoopHVAC object - need to match the actual format in IDF
                # The format is: Supply Side Outlet Node Names, NODENAME;
                pattern = rf'(Supply Side Outlet Node Names|supply_side_outlet_node_names)\s*,\s*{re.escape(old_supply)}'
                replacement = rf'\1,\n  {new_supply}'
                self.content = re.sub(pattern, replacement, self.content, flags=re.IGNORECASE)
                self.fixes_applied.append(f'airloop_node_fixed_{error["airloop"]}')
    
    def _get_line_number(self, position: int) -> int:
        """Get line number for a character position"""
        return self.content[:position].count('\n') + 1
    
    def save(self, output_path: Optional[str] = None):
        """Save the fixed IDF content"""
        if output_path:
            Path(output_path).write_text(self.content)
        else:
            # Save to same file with .fixed extension
            fixed_path = self.idf_path.with_suffix('.idf.fixed')
            fixed_path.write_text(self.content)
            return str(fixed_path)


def print_results(results: Dict):
    """Print validation results in a readable format"""
    print(f"\n{'='*80}")
    print(f"IDF Validation Results: {results['file']}")
    print(f"{'='*80}\n")
    
    if results['passed']:
        print("✅ VALIDATION PASSED - No critical errors found\n")
    else:
        print("❌ VALIDATION FAILED - Critical errors found\n")
    
    # Print errors
    if results['errors']:
        print(f"🔴 ERRORS ({len(results['errors'])}):")
        for i, error in enumerate(results['errors'], 1):
            print(f"\n  {i}. {error['type'].upper()}")
            print(f"     {error['message']}")
            if 'line' in error:
                print(f"     Line: {error['line']}")
            if 'airloop' in error:
                print(f"     AirLoopHVAC: {error['airloop']}")
        print()
    
    # Print warnings
    if results['warnings']:
        print(f"⚠️  WARNINGS ({len(results['warnings'])}):")
        for i, warning in enumerate(results['warnings'], 1):
            print(f"\n  {i}. {warning['type'].upper()}")
            print(f"     {warning['message']}")
        print()
    
    # Print fixes applied
    if results.get('fixes_applied'):
        print(f"🔧 FIXES APPLIED ({len(results['fixes_applied'])}):")
        for fix in results['fixes_applied']:
            print(f"     - {fix}")
        print()
    
    # Summary
    print(f"{'='*80}")
    print(f"Summary:")
    print(f"  Errors: {len(results['errors'])}")
    print(f"  Warnings: {len(results['warnings'])}")
    print(f"  Fixes Applied: {len(results.get('fixes_applied', []))}")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Validate EnergyPlus IDF files for critical fixes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate only
  python validate_energyplus_fixes.py building.idf
  
  # Validate and auto-fix
  python validate_energyplus_fixes.py building.idf --fix
  
  # Validate and save fixed file
  python validate_energyplus_fixes.py building.idf --fix --output building_fixed.idf
        """
    )
    parser.add_argument('idf_file', help='Path to IDF file to validate')
    parser.add_argument('--fix', action='store_true', help='Automatically fix issues')
    parser.add_argument('--output', help='Output path for fixed file (only used with --fix)')
    parser.add_argument('--quiet', action='store_true', help='Suppress output')
    
    args = parser.parse_args()
    
    try:
        validator = IDFValidator(args.idf_file)
        results = validator.validate_all(auto_fix=args.fix)
        
        if args.fix and results.get('fixes_applied'):
            output_path = args.output or None
            fixed_path = validator.save(output_path)
            if fixed_path:
                results['fixed_file'] = fixed_path
        
        if not args.quiet:
            print_results(results)
        
        # Return exit code based on results
        sys.exit(0 if results['passed'] else 1)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

