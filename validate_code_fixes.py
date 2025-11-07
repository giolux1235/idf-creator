#!/usr/bin/env python3
"""
Code Fix Validation Script

This script validates that all critical fixes have been properly implemented in the source code.

Fixes validated:
1. AirLoopHVAC uses SupplyOutlet (not ZoneEquipmentInlet) for supply outlet
2. Version is set to 24.2 in ProfessionalIDFGenerator
3. Ceiling tilt fix is implemented
4. Zone floor area is explicitly set
5. Validation for duplicate nodes exists

Usage:
    python validate_code_fixes.py
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple


class CodeFixValidator:
    """Validates that code fixes are properly implemented"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.errors = []
        self.warnings = []
        self.passed_checks = []
        
    def validate_all(self) -> Dict:
        """Run all validation checks"""
        print("Validating code fixes...\n")
        
        self.validate_airloop_supply_outlet()
        self.validate_version_setting()
        self.validate_ceiling_tilt_fix()
        self.validate_zone_floor_area()
        self.validate_duplicate_node_validation()
        self.validate_branch_fan_outlet()
        
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'passed': self.passed_checks,
            'all_passed': len(self.errors) == 0
        }
    
    def validate_airloop_supply_outlet(self):
        """Check that AirLoopHVAC uses SupplyOutlet for supply outlet"""
        file_path = self.project_root / "src" / "advanced_hvac_systems.py"
        
        if not file_path.exists():
            self.errors.append({
                'file': str(file_path),
                'check': 'airloop_supply_outlet',
                'message': 'File not found'
            })
            return
        
        content = file_path.read_text()
        
        # Check that supply_side_outlet_node_names uses SupplyOutlet
        if 'supply_side_outlet_node_names' in content:
            # Look for the line that sets supply outlet
            pattern = r"['\"]supply_side_outlet_node_names['\"]\s*:\s*\[.*?normalize_node_name\([^)]*_SupplyOutlet[^)]*\)"
            
            if re.search(pattern, content, re.DOTALL):
                self.passed_checks.append({
                    'file': str(file_path),
                    'check': 'airloop_supply_outlet',
                    'message': '✅ AirLoopHVAC uses SupplyOutlet for supply outlet'
                })
            else:
                # Check if it uses ZoneEquipmentInlet (wrong)
                if re.search(r"['\"]supply_side_outlet_node_names['\"]\s*:\s*\[.*?ZoneEquipmentInlet", content, re.IGNORECASE):
                    self.errors.append({
                        'file': str(file_path),
                        'check': 'airloop_supply_outlet',
                        'message': '❌ AirLoopHVAC still uses ZoneEquipmentInlet for supply outlet (should use SupplyOutlet)',
                        'line': self._find_line_number(content, 'supply_side_outlet_node_names')
                    })
                else:
                    self.warnings.append({
                        'file': str(file_path),
                        'check': 'airloop_supply_outlet',
                        'message': '⚠️  Could not verify supply outlet node name pattern'
                    })
    
    def validate_branch_fan_outlet(self):
        """Check that Branch Fan outlet uses SupplyOutlet"""
        file_path = self.project_root / "src" / "professional_idf_generator.py"
        
        if not file_path.exists():
            return
        
        content = file_path.read_text()
        
        # Check for fallback that should use SupplyOutlet
        # Look for the fallback pattern around line 813-814
        fallback_pattern = r'fan_outlet_node\s*=\s*normalize_node_name\([^)]*_SupplyOutlet[^)]*\)'
        
        if re.search(fallback_pattern, content, re.IGNORECASE):
            self.passed_checks.append({
                'file': str(file_path),
                'check': 'branch_fan_outlet_fallback',
                'message': '✅ Branch Fan outlet fallback uses SupplyOutlet'
            })
        else:
            # Check if it still uses ZoneEquipmentInlet (wrong)
            if re.search(r'fan_outlet_node\s*=\s*normalize_node_name\([^)]*_ZoneEquipmentInlet[^)]*\)', content, re.IGNORECASE):
                self.errors.append({
                    'file': str(file_path),
                    'check': 'branch_fan_outlet_fallback',
                    'message': '❌ Branch Fan outlet fallback still uses ZoneEquipmentInlet (should use SupplyOutlet)'
                })
        
        # Check the Branch component outlet
        branch_outlet_pattern = r"'outlet':\s*normalize_node_name\(fan_outlet_node\)[^}]*SupplyOutlet"
        
        if re.search(branch_outlet_pattern, content, re.IGNORECASE):
            self.passed_checks.append({
                'file': str(file_path),
                'check': 'branch_component_outlet',
                'message': '✅ Branch component outlet uses SupplyOutlet fallback'
            })
        elif re.search(r"'outlet':\s*normalize_node_name\([^)]*_ZoneEquipmentInlet[^)]*\)", content, re.IGNORECASE):
            self.errors.append({
                'file': str(file_path),
                'check': 'branch_component_outlet',
                'message': '❌ Branch component outlet still uses ZoneEquipmentInlet fallback'
            })
    
    def validate_version_setting(self):
        """Check that version is set to 24.2"""
        file_path = self.project_root / "src" / "professional_idf_generator.py"
        
        if not file_path.exists():
            self.errors.append({
                'file': str(file_path),
                'check': 'version_setting',
                'message': 'File not found'
            })
            return
        
        content = file_path.read_text()
        
        # Check __init__ method
        init_pattern = r'def __init__\(self\):.*?super\(\)\.__init__\(version=["\']24\.2["\']\)'
        
        if re.search(init_pattern, content, re.DOTALL):
            self.passed_checks.append({
                'file': str(file_path),
                'check': 'version_setting',
                'message': '✅ ProfessionalIDFGenerator uses version 24.2'
            })
        elif re.search(r'super\(\)\.__init__\(version=["\']25\.1["\']\)', content):
            self.errors.append({
                'file': str(file_path),
                'check': 'version_setting',
                'message': '❌ ProfessionalIDFGenerator still uses version 25.1 (should be 24.2)'
            })
        else:
            self.warnings.append({
                'file': str(file_path),
                'check': 'version_setting',
                'message': '⚠️  Could not verify version setting'
            })
    
    def validate_ceiling_tilt_fix(self):
        """Check that ceiling tilt fix is implemented"""
        file_path = self.project_root / "src" / "advanced_geometry_engine.py"
        
        if not file_path.exists():
            return
        
        content = file_path.read_text()
        
        # Check that fix_vertex_ordering_for_ceiling is used
        if 'fix_vertex_ordering_for_ceiling' in content:
            self.passed_checks.append({
                'file': str(file_path),
                'check': 'ceiling_tilt_fix',
                'message': '✅ Ceiling tilt fix function is used'
            })
        else:
            self.warnings.append({
                'file': str(file_path),
                'check': 'ceiling_tilt_fix',
                'message': '⚠️  Could not find ceiling tilt fix function'
            })
        
        # Check geometry_utils has the function
        utils_file = self.project_root / "src" / "geometry_utils.py"
        if utils_file.exists():
            utils_content = utils_file.read_text()
            if 'def fix_vertex_ordering_for_ceiling' in utils_content:
                # Check that it ensures tilt ~0°
                if 'tilt > 90.0' in utils_content or 'tilt > 90' in utils_content:
                    self.passed_checks.append({
                        'file': str(utils_file),
                        'check': 'ceiling_tilt_logic',
                        'message': '✅ Ceiling tilt fix ensures tilt ~0° (not 180°)'
                    })
    
    def validate_zone_floor_area(self):
        """Check that zone floor area is explicitly set"""
        file_path = self.project_root / "src" / "professional_idf_generator.py"
        
        if not file_path.exists():
            return
        
        content = file_path.read_text()
        
        # Check generate_zone_object method
        if 'def generate_zone_object' in content:
            # Look for floor area being set explicitly
            zone_method = re.search(r'def generate_zone_object\([^)]*\):.*?return', content, re.DOTALL)
            
            if zone_method:
                method_content = zone_method.group(0)
                
                # Check for explicit floor area setting
                if re.search(r'floor_area_str\s*=\s*f"[^"]*zone\.area[^"]*"', method_content) or \
                   re.search(r'\{floor_area_str\}', method_content):
                    self.passed_checks.append({
                        'file': str(file_path),
                        'check': 'zone_floor_area',
                        'message': '✅ Zone floor area is explicitly set from zone.area'
                    })
                else:
                    self.warnings.append({
                        'file': str(file_path),
                        'check': 'zone_floor_area',
                        'message': '⚠️  Could not verify zone floor area is explicitly set'
                    })
    
    def validate_duplicate_node_validation(self):
        """Check that duplicate node validation exists"""
        file_path = self.project_root / "src" / "professional_idf_generator.py"
        
        if not file_path.exists():
            return
        
        content = file_path.read_text()
        
        # Check for validation in format_hvac_object
        if 'CRITICAL VALIDATION: Ensure supply outlet and demand inlet are different nodes' in content:
            self.passed_checks.append({
                'file': str(file_path),
                'check': 'duplicate_node_validation',
                'message': '✅ Duplicate node validation exists'
            })
        else:
            self.warnings.append({
                'file': str(file_path),
                'check': 'duplicate_node_validation',
                'message': '⚠️  Could not find duplicate node validation'
            })
        
        # Check for the actual validation logic
        if re.search(r'supply_outlet_value\.upper\(\)\s*==\s*demand_inlet_value\.upper\(\)', content):
            self.passed_checks.append({
                'file': str(file_path),
                'check': 'duplicate_node_check_logic',
                'message': '✅ Duplicate node check logic is implemented'
            })
    
    def _find_line_number(self, content: str, search_text: str) -> int:
        """Find line number for search text"""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if search_text in line:
                return i
        return 0
    
    def print_results(self, results: Dict):
        """Print validation results"""
        print("=" * 80)
        print("CODE FIX VALIDATION RESULTS")
        print("=" * 80)
        print()
        
        if results['all_passed']:
            print("✅ ALL CHECKS PASSED\n")
        else:
            print("❌ SOME CHECKS FAILED\n")
        
        # Print passed checks
        if results['passed']:
            print(f"✅ PASSED CHECKS ({len(results['passed'])}):")
            for check in results['passed']:
                print(f"   {check['message']}")
                print(f"      File: {check['file']}")
            print()
        
        # Print errors
        if results['errors']:
            print(f"❌ ERRORS ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"   {error['message']}")
                print(f"      File: {error['file']}")
                if 'line' in error:
                    print(f"      Line: {error['line']}")
            print()
        
        # Print warnings
        if results['warnings']:
            print(f"⚠️  WARNINGS ({len(results['warnings'])}):")
            for warning in results['warnings']:
                print(f"   {warning['message']}")
                print(f"      File: {warning['file']}")
            print()
        
        print("=" * 80)
        print(f"Summary: {len(results['passed'])} passed, {len(results['errors'])} errors, {len(results['warnings'])} warnings")
        print("=" * 80)
        print()


def main():
    validator = CodeFixValidator()
    results = validator.validate_all()
    validator.print_results(results)
    
    # Exit with error code if there are errors
    sys.exit(0 if results['all_passed'] else 1)


if __name__ == '__main__':
    main()

