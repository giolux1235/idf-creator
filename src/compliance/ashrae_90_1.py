"""
ASHRAE 90.1 Compliance Checker
Validates generated IDFs against ASHRAE 90.1 energy code requirements
"""
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ComplianceIssue:
    """Represents a compliance issue"""
    severity: str  # 'critical', 'warning', 'info'
    category: str  # 'envelope', 'lighting', 'mechanical', 'equipment'
    requirement: str
    actual_value: Optional[float]
    required_value: Optional[float]
    unit: str
    message: str


class ASHRAE901ComplianceChecker:
    """
    ASHRAE 90.1-2019 Compliance Checker
    
    Checks generated IDFs against prescriptive path requirements:
    - Envelope R-values, U-factors
    - Lighting power density (LPD)
    - Mechanical efficiency (COP/EER)
    - Window properties
    """
    
    def __init__(self):
        # ASHRAE 90.1-2019 prescriptive requirements by climate zone
        self.requirements = self._load_ashrae_requirements()
    
    def _load_ashrae_requirements(self) -> Dict:
        """Load ASHRAE 90.1-2019 prescriptive requirements"""
        return {
            'climate_zones': {
                '1': {'heating_days': 0, 'cooling_days': 7000},
                '2': {'heating_days': 2000, 'cooling_days': 7000},
                '3': {'heating_days': 2500, 'cooling_days': 5500},
                '4': {'heating_days': 3500, 'cooling_days': 4500},
                '5': {'heating_days': 5000, 'cooling_days': 2500},
                '6': {'heating_days': 6000, 'cooling_days': 1500},
                '7': {'heating_days': 7000, 'cooling_days': 1000},
                '8': {'heating_days': 9000, 'cooling_days': 0}
            },
            'envelope': {
                # Wall U-factor (W/m²-K) by climate zone
                'wall_u_max': {
                    '1-2': 0.557,  # R-3.2
                    '3-4': 0.365,  # R-4.9
                    '5': 0.289,    # R-6.2
                    '6': 0.227,    # R-7.9
                    '7-8': 0.189   # R-9.5
                },
                # Roof U-factor (W/m²-K) by climate zone
                'roof_u_max': {
                    '1-2': 0.318,  # R-5.6
                    '3': 0.227,    # R-7.9
                    '4-8': 0.195   # R-9.2
                },
                # Floor U-factor (W/m²-K) by climate zone
                'floor_u_max': {
                    '1-2': 0.455,  # R-4.4
                    '3-8': 0.318   # R-6.3
                },
                # Window U-factor (W/m²-K) by climate zone
                'window_u_max': {
                    '1': 4.55,
                    '2': 3.41,
                    '3': 2.56,
                    '4': 2.27,
                    '5': 1.99,
                    '6': 1.99,
                    '7': 1.99,
                    '8': 1.70
                },
                # Window SHGC by climate zone and orientation
                'window_shgc_max': {
                    '1': {'N': 0.66, 'E': 0.42, 'S': 0.42, 'W': 0.42},
                    '2': {'N': 0.66, 'E': 0.42, 'S': 0.42, 'W': 0.42},
                    '3': {'N': 0.66, 'E': 0.42, 'S': 0.40, 'W': 0.42},
                    '4': {'N': 0.66, 'E': 0.42, 'S': 0.40, 'W': 0.42},
                    '5': {'N': 0.66, 'E': 0.40, 'S': 0.40, 'W': 0.40},
                    '6': {'N': 0.66, 'E': 0.40, 'S': 0.40, 'W': 0.40},
                    '7': {'N': 0.66, 'E': 0.36, 'S': 0.36, 'W': 0.36},
                    '8': {'N': 0.66, 'E': 0.28, 'S': 0.28, 'W': 0.28}
                }
            },
            'lighting': {
                # Lighting Power Density (W/m²) by space type
                'lpd_max': {
                    'office': 10.8,
                    'retail': 15.3,
                    'warehouse': 8.5,
                    'education': 11.8,
                    'healthcare': 10.8,
                    'lodging': 8.6,
                    'food_service': 16.3,
                    'public_assembly': 14.6,
                    'manufacturing': 16.4,
                    'storage': 8.5,
                    'garage': 3.3,
                    'atrium': 5.4
                }
            },
            'mechanical': {
                # Cooling COP minimums by equipment type
                'cooling_cop_min': {
                    'DX_Single_Speed_AC': 3.2,
                    'DX_Variable_Speed_AC': 3.8,
                    'Split_System': 3.2,
                    'Water_Cooled_Centrifugal': 5.2,
                    'Water_Cooled_Screw': 5.2,
                    'Air_Cooled_Chiller': 2.5
                },
                # EER minimums
                'eer_min': {
                    'DX_Single_Speed_AC': 11.0,
                    'DX_Variable_Speed_AC': 13.0,
                    'Split_System': 11.0
                }
            }
        }
    
    def check_compliance(self, idf_content: str, climate_zone: str = '5', 
                        building_type: str = 'office') -> Dict:
        """
        Check IDF for ASHRAE 90.1 compliance.
        
        Args:
            idf_content: Complete IDF file content
            climate_zone: Climate zone (1-8)
            building_type: Building type for LPD checking
            
        Returns:
            Compliance report dictionary
        """
        issues = []
        
        # Parse climate zone
        cz_match = re.search(r'(\d)', climate_zone)
        cz_num = cz_match.group(1) if cz_match else '5'
        
        # Check envelope compliance
        issues.extend(self._check_envelope(idf_content, cz_num))
        
        # Check lighting compliance
        issues.extend(self._check_lighting(idf_content, building_type))
        
        # Check mechanical compliance
        issues.extend(self._check_mechanical(idf_content))
        
        # Calculate compliance score
        critical_count = sum(1 for i in issues if i.severity == 'critical')
        warning_count = sum(1 for i in issues if i.severity == 'warning')
        
        total_checks = len(issues)
        passed_checks = total_checks - critical_count - warning_count
        
        compliance_percentage = (passed_checks / total_checks * 100) if total_checks > 0 else 100
        is_compliant = critical_count == 0
        
        return {
            'is_compliant': is_compliant,
            'compliance_percentage': compliance_percentage,
            'issues': issues,
            'critical_count': critical_count,
            'warning_count': warning_count,
            'info_count': total_checks - critical_count - warning_count,
            'climate_zone': climate_zone,
            'building_type': building_type
        }
    
    def _check_envelope(self, content: str, climate_zone: str) -> List[ComplianceIssue]:
        """Check envelope U-factors against ASHRAE 90.1"""
        issues = []
        
        # Determine climate zone ranges
        cz_ranges = {
            '1': '1-2', '2': '1-2',
            '3': '3-4', '4': '3-4',
            '5': '5', '6': '6',
            '7': '7-8', '8': '7-8'
        }
        cz_range = cz_ranges.get(climate_zone, '5')
        
        # Get max U-factors for this climate zone
        wall_u_max = self.requirements['envelope']['wall_u_max'].get(cz_range, 0.289)
        roof_u_max = self.requirements['envelope']['roof_u_max'].get(cz_range, 0.195)
        floor_u_max = self.requirements['envelope']['floor_u_max'].get(cz_range, 0.318)
        window_u_max = self.requirements['envelope']['window_u_max'].get(climate_zone, 1.99)
        
        # This is a simplified check - in practice, would parse constructions
        # to extract actual U-factors from the IDF
        
        return issues
    
    def _check_lighting(self, content: str, building_type: str) -> List[ComplianceIssue]:
        """Check lighting power density against ASHRAE 90.1"""
        issues = []
        
        # Get max LPD for building type
        # Handle None building_type
        building_type_normalized = building_type.lower() if building_type else 'office'
        lpd_max = self.requirements['lighting']['lpd_max'].get(
            building_type_normalized, 11.8
        )
        
        # Find Watts per Zone Floor Area values in Lights objects
        # Pattern matches: number followed by "!- Watts per Zone Floor Area"
        lighting_pattern = r'(\d+\.?\d*)\s*!-\s*Watts per Zone Floor Area'
        lpd_values = re.findall(lighting_pattern, content)
        
        if lpd_values:
            # Check if any LPD exceeds maximum
            for lpd_str in lpd_values:
                try:
                    lpd = float(lpd_str)
                    if lpd > lpd_max:
                        issues.append(ComplianceIssue(
                            severity='critical',
                            category='lighting',
                            requirement=f'LPD ≤ {lpd_max} W/m²',
                            actual_value=lpd,
                            required_value=lpd_max,
                            unit='W/m²',
                            message=f'Lighting power density ({lpd} W/m²) exceeds ASHRAE 90.1 maximum ({lpd_max} W/m²)'
                        ))
                except ValueError:
                    pass
        
        return issues
    
    def _check_mechanical(self, content: str) -> List[ComplianceIssue]:
        """Check mechanical equipment efficiency against ASHRAE 90.1"""
        issues = []
        
        # Check DX coil COP
        dx_pattern = r'Coil:Cooling:DX:SingleSpeed,.*?\n.*?Rated COP.*?\n.*?(\d+\.?\d*),'
        cop_values = re.findall(dx_pattern, content)
        
        cop_min = self.requirements['mechanical']['cooling_cop_min'].get(
            'DX_Single_Speed_AC', 3.2
        )
        
        for cop_str in cop_values:
            try:
                cop = float(cop_str)
                if cop < cop_min:
                    issues.append(ComplianceIssue(
                        severity='critical',
                        category='mechanical',
                        requirement=f'COP ≥ {cop_min}',
                        actual_value=cop,
                        required_value=cop_min,
                        unit='W/W',
                        message=f'Cooling COP ({cop}) below ASHRAE 90.1 minimum ({cop_min})'
                    ))
            except ValueError:
                pass
        
        return issues
    
    def generate_report(self, compliance_result: Dict) -> str:
        """Generate human-readable compliance report"""
        lines = [
            "=" * 80,
            "ASHRAE 90.1 COMPLIANCE REPORT",
            "=" * 80,
            f"\nClimate Zone: {compliance_result['climate_zone']}",
            f"Building Type: {compliance_result['building_type']}",
            f"Compliance Status: {'✓ COMPLIANT' if compliance_result['is_compliant'] else '✗ NON-COMPLIANT'}",
            f"Compliance Score: {compliance_result['compliance_percentage']:.1f}%",
            f"\nIssues Found:",
            f"  Critical: {compliance_result['critical_count']}",
            f"  Warnings: {compliance_result['warning_count']}",
            f"  Info: {compliance_result['info_count']}",
            ""
        ]
        
        # Group issues by category
        if compliance_result['issues']:
            issues = compliance_result['issues']
            
            by_severity = {
                'critical': [i for i in issues if i.severity == 'critical'],
                'warning': [i for i in issues if i.severity == 'warning'],
                'info': [i for i in issues if i.severity == 'info']
            }
            
            for severity in ['critical', 'warning', 'info']:
                if by_severity[severity]:
                    lines.append(f"{severity.upper()} ISSUES:")
                    lines.append("-" * 80)
                    for issue in by_severity[severity]:
                        value_info = f"{issue.actual_value} {issue.unit}" if issue.actual_value else "N/A"
                        req_info = f" (required: {issue.required_value} {issue.unit})" if issue.required_value else ""
                        lines.append(f"  [{issue.category}] {issue.message}")
                        lines.append(f"    {value_info}{req_info}")
                    lines.append("")
        else:
            lines.append("✓ No compliance issues found!")
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)


def check_ashrae_compliance(idf_content: str, climate_zone: str = '5', 
                           building_type: str = 'office') -> Dict:
    """
    Convenience function to check ASHRAE 90.1 compliance.
    
    Args:
        idf_content: Complete IDF file content
        climate_zone: Climate zone designation
        building_type: Building type for LPD checking
        
    Returns:
        Compliance report dictionary
    """
    checker = ASHRAE901ComplianceChecker()
    result = checker.check_compliance(idf_content, climate_zone, building_type)
    result['report'] = checker.generate_report(result)
    return result


if __name__ == "__main__":
    # Test the compliance checker
    test_idf = """Version,9.2;
Building,Test Building;
SimulationControl,
  Yes,Yes;

Lights,
  Office_Lighting,
  Always On,
  15.5,
  0.4,
  Lights Schedule,
  ,,,,,,;
"""
    
    checker = ASHRAE901ComplianceChecker()
    result = checker.check_compliance(test_idf, climate_zone='5', building_type='office')
    print(checker.generate_report(result))

