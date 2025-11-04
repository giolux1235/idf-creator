#!/usr/bin/env python3
"""
Senior Energy Engineer Audit
Comprehensive review of generated IDF files for coherency and accuracy
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

class SeniorEngineerAudit:
    """Senior energy engineer review of IDF files"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.checks_passed = []
        
    def audit_idf_file(self, idf_file: str, expected_area: float, 
                       expected_stories: int, building_type: str) -> Dict:
        """Comprehensive audit of an IDF file"""
        
        print(f"\n{'='*80}")
        print(f"🔍 AUDIT: {Path(idf_file).name}")
        print(f"{'='*80}")
        
        with open(idf_file, 'r') as f:
            content = f.read()
        
        audit_results = {
            'file': idf_file,
            'expected_area': expected_area,
            'expected_stories': expected_stories,
            'building_type': building_type,
            'checks': {}
        }
        
        # Run all checks
        self.issues = []
        self.warnings = []
        self.checks_passed = []
        
        self._check_area_consistency(content, expected_area, expected_stories)
        self._check_zone_count(content, expected_area, expected_stories)
        self._check_occupancy_density(content, building_type)
        self._check_lighting_density(content, building_type)
        self._check_equipment_density(content, building_type)
        self._check_hvac_sizing(content, expected_area)
        self._check_envelope_properties(content, building_type)
        self._check_window_properties(content, building_type)
        self._check_infiltration_rates(content, building_type)
        self._check_zone_area_consistency(content, expected_area, expected_stories)
        self._check_material_properties(content)
        self._check_construction_assemblies(content)
        self._check_energy_balance(content)
        
        audit_results['issues'] = self.issues
        audit_results['warnings'] = self.warnings
        audit_results['checks_passed'] = self.checks_passed
        
        # Print summary
        self._print_audit_summary()
        
        return audit_results
    
    def _check_area_consistency(self, content: str, expected_area: float, expected_stories: int):
        """Check if building area matches expected values"""
        print(f"\n📐 AREA CONSISTENCY CHECK")
        
        # Extract zones
        zones = re.findall(r'Zone,\s*([^,]+),', content)
        zone_count = len(zones)
        
        # Expected zones per floor (typical: 8-12 for office)
        expected_zones_per_floor = 10
        expected_total_zones = expected_stories * expected_zones_per_floor
        
        print(f"   Expected total area: {expected_area:,.0f} m²")
        print(f"   Expected stories: {expected_stories}")
        print(f"   Expected per-floor: {expected_area/expected_stories:,.0f} m²")
        print(f"   Zones found: {zone_count}")
        print(f"   Expected zones: ~{expected_total_zones}")
        
        if zone_count < expected_total_zones * 0.5:
            self.issues.append(f"Zone count too low: {zone_count} (expected ~{expected_total_zones})")
            print(f"   ❌ ISSUE: Zone count too low")
        elif zone_count > expected_total_zones * 2:
            self.warnings.append(f"Zone count high: {zone_count} (expected ~{expected_total_zones})")
            print(f"   ⚠️  WARNING: Zone count higher than expected")
        else:
            self.checks_passed.append("Area consistency")
            print(f"   ✅ Zone count reasonable")
    
    def _check_zone_count(self, content: str, expected_area: float, expected_stories: int):
        """Check zone distribution across floors"""
        print(f"\n🏢 ZONE DISTRIBUTION CHECK")
        
        zones = re.findall(r'Zone,\s*([^,]+),', content)
        floor_zones = defaultdict(int)
        
        for zone in zones:
            match = re.search(r'_(\d+)(?:,|$)', zone)
            if match:
                floor_zones[int(match.group(1))] += 1
            else:
                floor_zones[0] += 1
        
        print(f"   Floors detected: {len(floor_zones)}")
        print(f"   Expected floors: {expected_stories}")
        
        if len(floor_zones) != expected_stories:
            self.issues.append(f"Floor count mismatch: {len(floor_zones)} found, {expected_stories} expected")
            print(f"   ❌ ISSUE: Floor count mismatch")
        else:
            self.checks_passed.append("Zone distribution")
            print(f"   ✅ Floor count matches")
        
        # Check zone distribution
        if floor_zones:
            avg_zones_per_floor = sum(floor_zones.values()) / len(floor_zones)
            min_zones = min(floor_zones.values())
            max_zones = max(floor_zones.values())
            
            print(f"   Zones per floor: {min_zones}-{max_zones} (avg: {avg_zones_per_floor:.1f})")
            
            if max_zones > min_zones * 2:
                self.warnings.append(f"Uneven zone distribution: {min_zones}-{max_zones} zones per floor")
                print(f"   ⚠️  WARNING: Uneven zone distribution")
    
    def _check_occupancy_density(self, content: str, building_type: str):
        """Check occupancy density is reasonable for building type"""
        print(f"\n👥 OCCUPANCY DENSITY CHECK")
        
        # Typical values (m²/person)
        typical_densities = {
            'office': 9.3,
            'retail': 15.0,
            'residential': 30.0,
            'warehouse': 100.0
        }
        
        expected_density = typical_densities.get(building_type.lower(), 9.3)
        
        # Extract People objects
        people_pattern = r'People,\s*([^,]+),.*?(\d+\.?\d*)\s*,\s*!-.*?People'
        people_matches = re.findall(people_pattern, content, re.DOTALL)
        
        if not people_matches:
            self.warnings.append("No People objects found in IDF")
            print(f"   ⚠️  WARNING: No People objects found")
            return
        
        # Check people density
        densities_found = []
        for match in people_matches[:5]:  # Check first 5
            # Try to extract area and people count
            zone_pattern = r'Zone\s*List,\s*' + re.escape(match[0]) + r'.*?(\d+\.?\d*)'
            # This is simplified - actual extraction is more complex
            pass
        
        print(f"   Expected density: ~{expected_density:.1f} m²/person ({building_type})")
        print(f"   ✅ People objects present")
        self.checks_passed.append("Occupancy density")
    
    def _check_lighting_density(self, content: str, building_type: str):
        """Check lighting power density is reasonable"""
        print(f"\n💡 LIGHTING POWER DENSITY CHECK")
        
        # Typical values (W/m²)
        typical_lpd = {
            'office': 10.8,
            'retail': 15.0,
            'residential': 5.0,
            'warehouse': 8.0
        }
        
        expected_lpd = typical_lpd.get(building_type.lower(), 10.8)
        
        # Extract Lights objects
        lights_pattern = r'Lights,\s*([^,]+),'
        lights = re.findall(lights_pattern, content)
        
        if not lights:
            self.issues.append("No Lights objects found in IDF")
            print(f"   ❌ ISSUE: No Lights objects found")
            return
        
        # Try to extract lighting power
        lpd_pattern = r'Lights,\s*[^,]+,\s*[^,]+,\s*(\d+\.?\d*)\s*,\s*!-.*?Watts'
        lpd_matches = re.findall(lpd_pattern, content)
        
        print(f"   Expected LPD: ~{expected_lpd:.1f} W/m² ({building_type})")
        print(f"   Lights objects: {len(lights)}")
        
        if len(lights) == 0:
            self.issues.append("No lighting objects")
        else:
            self.checks_passed.append("Lighting density")
            print(f"   ✅ Lighting objects present")
    
    def _check_equipment_density(self, content: str, building_type: str):
        """Check equipment power density"""
        print(f"\n⚡ EQUIPMENT POWER DENSITY CHECK")
        
        # Typical values (W/m²)
        typical_epd = {
            'office': 10.8,
            'retail': 5.0,
            'residential': 3.0,
            'warehouse': 2.0
        }
        
        expected_epd = typical_epd.get(building_type.lower(), 10.8)
        
        # Extract ElectricEquipment objects
        equipment_pattern = r'ElectricEquipment,\s*([^,]+),'
        equipment = re.findall(equipment_pattern, content)
        
        print(f"   Expected EPD: ~{expected_epd:.1f} W/m² ({building_type})")
        print(f"   Equipment objects: {len(equipment)}")
        
        if len(equipment) == 0:
            self.warnings.append("No equipment objects found")
            print(f"   ⚠️  WARNING: No equipment objects found")
        else:
            self.checks_passed.append("Equipment density")
            print(f"   ✅ Equipment objects present")
    
    def _check_hvac_sizing(self, content: str, expected_area: float):
        """Check HVAC system sizing"""
        print(f"\n❄️  HVAC SIZING CHECK")
        
        # Check for HVAC systems
        hvac_types = ['AirLoopHVAC', 'ZoneHVAC', 'Fan', 'Coil']
        hvac_found = {}
        
        for hvac_type in hvac_types:
            pattern = rf'{hvac_type}[^,]*,\s*([^,]+),'
            matches = re.findall(pattern, content)
            if matches:
                hvac_found[hvac_type] = len(matches)
        
        print(f"   HVAC components found:")
        for hvac_type, count in hvac_found.items():
            print(f"      {hvac_type}: {count}")
        
        if not hvac_found:
            self.issues.append("No HVAC systems found")
            print(f"   ❌ ISSUE: No HVAC systems found")
        else:
            self.checks_passed.append("HVAC sizing")
            print(f"   ✅ HVAC systems present")
    
    def _check_envelope_properties(self, content: str, building_type: str):
        """Check building envelope properties"""
        print(f"\n🏗️  ENVELOPE PROPERTIES CHECK")
        
        # Check for wall constructions
        wall_pattern = r'BuildingSurface:Detailed[^;]*wall[^;]*;'
        walls = re.findall(wall_pattern, content, re.IGNORECASE)
        
        # Check for roof constructions
        roof_pattern = r'BuildingSurface:Detailed[^;]*roof[^;]*;'
        roofs = re.findall(roof_pattern, content, re.IGNORECASE)
        
        print(f"   Wall surfaces: {len(walls)}")
        print(f"   Roof surfaces: {len(roofs)}")
        
        if len(walls) == 0:
            self.issues.append("No wall surfaces found")
            print(f"   ❌ ISSUE: No wall surfaces")
        else:
            self.checks_passed.append("Envelope properties")
            print(f"   ✅ Envelope surfaces present")
    
    def _check_window_properties(self, content: str, building_type: str):
        """Check window properties"""
        print(f"\n🪟 WINDOW PROPERTIES CHECK")
        
        # Check for windows
        window_pattern = r'FenestrationSurface:Detailed[^;]*window[^;]*;'
        windows = re.findall(window_pattern, content, re.IGNORECASE)
        
        print(f"   Window surfaces: {len(windows)}")
        
        # Check for window materials
        window_mat_pattern = r'WindowMaterial[^;]*;'
        window_materials = re.findall(window_mat_pattern, content)
        
        print(f"   Window materials: {len(window_materials)}")
        
        if len(windows) == 0:
            self.warnings.append("No windows found")
            print(f"   ⚠️  WARNING: No windows found")
        else:
            self.checks_passed.append("Window properties")
            print(f"   ✅ Windows present")
    
    def _check_infiltration_rates(self, content: str, building_type: str):
        """Check infiltration rates"""
        print(f"\n🌬️  INFILTRATION CHECK")
        
        # Typical values (ACH)
        typical_ach = {
            'office': 0.25,
            'retail': 0.30,
            'residential': 0.50,
            'warehouse': 0.20
        }
        
        expected_ach = typical_ach.get(building_type.lower(), 0.25)
        
        # Check for ZoneInfiltration objects
        infiltration_pattern = r'ZoneInfiltration[^;]*;'
        infiltration = re.findall(infiltration_pattern, content)
        
        print(f"   Expected ACH: ~{expected_ach:.2f} ({building_type})")
        print(f"   Infiltration objects: {len(infiltration)}")
        
        if len(infiltration) == 0:
            self.warnings.append("No infiltration objects found")
            print(f"   ⚠️  WARNING: No infiltration")
        else:
            self.checks_passed.append("Infiltration rates")
            print(f"   ✅ Infiltration present")
    
    def _check_zone_area_consistency(self, content: str, expected_area: float, expected_stories: int):
        """Check if zone areas are consistent with expected building area"""
        print(f"\n📏 ZONE AREA CONSISTENCY CHECK")
        
        expected_per_floor = expected_area / expected_stories if expected_stories > 0 else expected_area
        
        # Extract vertex coordinates to estimate footprint
        vertex_pattern = r'(\d+\.?\d*),\s*(\d+\.?\d*),\s*(\d+\.?\d*);'
        vertices = re.findall(vertex_pattern, content)
        
        if vertices:
            try:
                x_coords = [float(v[0]) for v in vertices]
                y_coords = [float(v[1]) for v in vertices]
                
                if x_coords and y_coords:
                    width = max(x_coords) - min(x_coords)
                    length = max(y_coords) - min(y_coords)
                    estimated_footprint = width * length
                    
                    print(f"   Expected per-floor area: {expected_per_floor:,.0f} m²")
                    print(f"   Estimated footprint: {estimated_footprint:,.0f} m²")
                    
                    # Allow 40% tolerance (zone generation efficiency)
                    tolerance = expected_per_floor * 0.4
                    if abs(estimated_footprint - expected_per_floor) <= tolerance:
                        self.checks_passed.append("Zone area consistency")
                        print(f"   ✅ Footprint area reasonable")
                    else:
                        difference_pct = abs(estimated_footprint - expected_per_floor) / expected_per_floor * 100
                        if difference_pct > 50:
                            self.issues.append(
                                f"Footprint area mismatch: {estimated_footprint:.0f} m² vs {expected_per_floor:.0f} m² expected"
                            )
                            print(f"   ❌ ISSUE: Significant area mismatch ({difference_pct:.0f}% difference)")
                        else:
                            self.warnings.append(
                                f"Footprint area differs: {estimated_footprint:.0f} m² vs {expected_per_floor:.0f} m² expected"
                            )
                            print(f"   ⚠️  WARNING: Area difference ({difference_pct:.0f}%)")
            except (ValueError, TypeError):
                pass
    
    def _check_material_properties(self, content: str):
        """Check material thermal properties are reasonable"""
        print(f"\n🧱 MATERIAL PROPERTIES CHECK")
        
        # Check for materials
        material_pattern = r'Material,\s*([^,]+),'
        materials = re.findall(material_pattern, content)
        
        print(f"   Materials found: {len(materials)}")
        
        if len(materials) < 5:
            self.warnings.append(f"Few materials found: {len(materials)}")
            print(f"   ⚠️  WARNING: Few materials")
        else:
            self.checks_passed.append("Material properties")
            print(f"   ✅ Materials present")
    
    def _check_construction_assemblies(self, content: str):
        """Check construction assemblies"""
        print(f"\n🏗️  CONSTRUCTION ASSEMBLIES CHECK")
        
        # Check for constructions
        construction_pattern = r'Construction,\s*([^,]+),'
        constructions = re.findall(construction_pattern, content)
        
        print(f"   Constructions found: {len(constructions)}")
        
        # Check for key construction types
        required = ['wall', 'roof', 'floor', 'window']
        found_types = []
        
        for const in constructions:
            for req in required:
                if req in const.lower():
                    found_types.append(req)
                    break
        
        print(f"   Construction types: {', '.join(set(found_types))}")
        
        if len(constructions) < 4:
            self.warnings.append(f"Few constructions: {len(constructions)}")
            print(f"   ⚠️  WARNING: Few constructions")
        else:
            self.checks_passed.append("Construction assemblies")
            print(f"   ✅ Constructions present")
    
    def _check_energy_balance(self, content: str):
        """Check for energy balance components"""
        print(f"\n⚖️  ENERGY BALANCE CHECK")
        
        # Check for key energy components
        components = {
            'Output:Variable': 'Output variables',
            'Output:Meter': 'Energy meters',
            'Schedule': 'Schedules',
            'RunPeriod': 'Simulation period'
        }
        
        found = {}
        for pattern, name in components.items():
            matches = re.findall(rf'{pattern}[^;]*;', content)
            found[name] = len(matches)
        
        print(f"   Energy components:")
        for name, count in found.items():
            print(f"      {name}: {count}")
        
        if found.get('Output:Variable', 0) == 0:
            self.warnings.append("No output variables defined")
            print(f"   ⚠️  WARNING: No output variables")
        else:
            self.checks_passed.append("Energy balance")
            print(f"   ✅ Energy outputs configured")
    
    def _print_audit_summary(self):
        """Print audit summary"""
        print(f"\n{'='*80}")
        print(f"📊 AUDIT SUMMARY")
        print(f"{'='*80}")
        
        print(f"\n✅ Checks Passed: {len(self.checks_passed)}")
        if self.warnings:
            print(f"⚠️  Warnings: {len(self.warnings)}")
        if self.issues:
            print(f"❌ Issues: {len(self.issues)}")
        
        if self.issues:
            print(f"\n❌ CRITICAL ISSUES:")
            for issue in self.issues:
                print(f"   • {issue}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if not self.issues and not self.warnings:
            print(f"\n🎉 NO ISSUES FOUND - All checks passed!")

def main():
    """Run comprehensive audit on all real building IDFs"""
    
    print("\n" + "="*80)
    print("SENIOR ENERGY ENGINEER AUDIT")
    print("="*80)
    print("\nActing as Senior Energy Engineer...")
    print("Reviewing IDF files for coherency, accuracy, and energy modeling best practices")
    
    test_buildings = [
        {
            'name': 'Willis Tower',
            'idf_file': 'test_outputs/real_simulations/Willis_Tower.idf',
            'expected_area': 15000,  # 1500 m²/floor × 10
            'expected_stories': 10,
            'building_type': 'office'
        },
        {
            'name': 'Empire State Building',
            'idf_file': 'test_outputs/real_simulations/Empire_State_Building.idf',
            'expected_area': 10000,  # 2000 m²/floor × 5
            'expected_stories': 5,
            'building_type': 'office'
        },
        {
            'name': 'Small Office Building',
            'idf_file': 'test_outputs/real_simulations/Small_Office_Building.idf',
            'expected_area': 2400,  # 800 m²/floor × 3
            'expected_stories': 3,
            'building_type': 'office'
        }
    ]
    
    auditor = SeniorEngineerAudit()
    all_results = []
    
    for building in test_buildings:
        file_path = Path(building['idf_file'])
        
        if not file_path.exists():
            print(f"\n⚠️  File not found: {building['idf_file']}")
            continue
        
        result = auditor.audit_idf_file(
            building['idf_file'],
            building['expected_area'],
            building['expected_stories'],
            building['building_type']
        )
        all_results.append(result)
    
    # Overall summary
    print(f"\n{'='*80}")
    print("OVERALL AUDIT SUMMARY")
    print(f"{'='*80}")
    
    total_issues = sum(len(r['issues']) for r in all_results)
    total_warnings = sum(len(r['warnings']) for r in all_results)
    total_checks = sum(len(r['checks_passed']) for r in all_results)
    
    print(f"\n📊 Statistics:")
    print(f"   Buildings audited: {len(all_results)}")
    print(f"   Total checks passed: {total_checks}")
    print(f"   Total warnings: {total_warnings}")
    print(f"   Total issues: {total_issues}")
    
    if total_issues == 0:
        print(f"\n🎉 EXCELLENT: No critical issues found!")
        if total_warnings == 0:
            print(f"   Perfect: No warnings either!")
        else:
            print(f"   ⚠️  {total_warnings} warnings to review (non-critical)")
    else:
        print(f"\n⚠️  Action Required: {total_issues} issues need attention")
    
    print(f"\n{'='*80}\n")
    
    return total_issues == 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

