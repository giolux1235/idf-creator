"""
Energy Coherence Validator
Validates that energy simulation results make physical sense
"""
import os
from typing import Dict, Optional, List
from dataclasses import dataclass

from .idf_validator import ValidationError
from ..cbecs_lookup import CBECSLookup


@dataclass
class EnergyCoherenceIssue:
    """Represents an energy coherence issue"""
    severity: str  # 'error', 'warning', 'info'
    metric: str  # 'electricity', 'heating', 'cooling', etc.
    value: float
    expected_range: tuple
    reason: str
    fix_suggestion: str


class EnergyCoherenceValidator:
    """Validates energy results for physical coherence"""
    
    def __init__(self):
        self.cbecs = CBECSLookup()
        self.issues: List[EnergyCoherenceIssue] = []
        self.warnings: List[EnergyCoherenceIssue] = []
    
    def validate_energy_coherence(self, energy_results: Dict, building_type: str,
                                 total_area_m2: float, stories: int = 1,
                                 idf_content: Optional[str] = None) -> Dict:
        """
        Validate energy results for physical coherence.
        
        Args:
            energy_results: Dictionary from get_energy_results()
            building_type: Building type (office, retail, etc.)
            total_area_m2: Total building area in m²
            stories: Number of stories
            idf_content: Optional IDF content to check HVAC system type
            
        Returns:
            Validation results dictionary
        """
        self.issues = []
        self.warnings = []
        
        if not energy_results or 'error' in energy_results:
            self.issues.append(EnergyCoherenceIssue(
                severity='error',
                metric='all',
                value=0,
                expected_range=(1, float('inf')),
                reason='No energy results available',
                fix_suggestion='Ensure simulation completed successfully'
            ))
            return self._format_results()
        
        # Check for zero energy
        total_energy = 0
        energy_by_type = {}
        
        data = energy_results.get('data', [])
        if not data:
            self.issues.append(EnergyCoherenceIssue(
                severity='error',
                metric='all',
                value=0,
                expected_range=(1, float('inf')),
                reason='No data rows in energy results',
                fix_suggestion='Check if simulation ran completely'
            ))
            return self._format_results()
        
        # Extract energy values from first row (annual totals)
        first_row = data[0]
        columns = energy_results.get('columns', [])
        
        # Find and sum all energy columns
        for col in columns:
            col_lower = col.lower()
            value = first_row.get(col, 0)
        
        # Try to extract specific metrics
        for col in columns:
            col_lower = col.lower()
            try:
                value = first_row.get(col, 0)
                if isinstance(value, str):
                    value = float(value.replace(',', ''))
                else:
                    value = float(value) if value else 0
                
                # Categorize by type
                if 'electricity' in col_lower or 'total site' in col_lower:
                    energy_by_type['electricity'] = energy_by_type.get('electricity', 0) + value
                elif 'gas' in col_lower or 'natural gas' in col_lower:
                    energy_by_type['gas'] = energy_by_type.get('gas', 0) + value
                elif 'heating' in col_lower:
                    energy_by_type['heating'] = energy_by_type.get('heating', 0) + value
                elif 'cooling' in col_lower:
                    energy_by_type['cooling'] = energy_by_type.get('cooling', 0) + value
                elif 'lighting' in col_lower:
                    energy_by_type['lighting'] = energy_by_type.get('lighting', 0) + value
                elif 'fan' in col_lower or 'ventilation' in col_lower:
                    energy_by_type['fan'] = energy_by_type.get('fan', 0) + value
                elif 'equipment' in col_lower or 'plug' in col_lower:
                    energy_by_type['equipment'] = energy_by_type.get('equipment', 0) + value
                
                if value > 0:
                    total_energy += value
            except (ValueError, TypeError):
                pass
        
        # Calculate EUI
        total_area_ft2 = total_area_m2 * 10.764
        total_energy_kbtu = total_energy * 3.412 / 1000  # kWh to kBtu
        eui_kbtu_ft2 = (total_energy_kbtu / total_area_ft2) if total_area_ft2 > 0 else 0
        eui_kwh_m2 = (total_energy / total_area_m2) if total_area_m2 > 0 else 0
        
        # Check for zero energy
        if total_energy == 0:
            self.issues.append(EnergyCoherenceIssue(
                severity='error',
                metric='total',
                value=0,
                expected_range=(1, float('inf')),
                reason='Total energy consumption is zero',
                fix_suggestion='Check if using Ideal Loads HVAC (does not report energy). Switch to VAV/PTAC/RTU systems.'
            ))
            
            # Check HVAC system type in IDF
            if idf_content:
                if 'ZoneHVAC:IdealLoadsAirSystem' in idf_content:
                    self.warnings.append(EnergyCoherenceIssue(
                        severity='warning',
                        metric='hvac',
                        value=0,
                        expected_range=(0, 0),
                        reason='Ideal Loads HVAC system used - does not report equipment energy by design',
                        fix_suggestion='Use real HVAC systems (VAV/PTAC/RTU) to get energy consumption. Set simple_hvac=False or use professional mode.'
                    ))
        
        # Compare against CBECS benchmarks
        if eui_kbtu_ft2 > 0:
            typical_eui = self.cbecs.get_site_eui(building_type.lower())
            
            # Also check against absolute kWh/m²/year range (100-200 kWh/m²/year)
            # Convert to kBtu/ft² for comparison: 100 kWh/m² = 31.7 kBtu/ft², 200 kWh/m² = 63.4 kBtu/ft²
            min_expected_kwh_m2 = 100
            max_expected_kwh_m2 = 200
            min_expected_kbtu_ft2 = 31.7
            max_expected_kbtu_ft2 = 63.4
            
            # Check against absolute range first (more specific for office buildings)
            if eui_kwh_m2 < min_expected_kwh_m2:
                if eui_kwh_m2 < 50:
                    self.issues.append(EnergyCoherenceIssue(
                        severity='error',
                        metric='eui',
                        value=eui_kbtu_ft2,
                        expected_range=(min_expected_kbtu_ft2, max_expected_kbtu_ft2),
                        reason=f'EUI {eui_kwh_m2:.1f} kWh/m²/year ({eui_kbtu_ft2:.1f} kBtu/ft²) is very low. Expected range: 100-200 kWh/m²/year (31.7-63.4 kBtu/ft²)',
                        fix_suggestion='Energy consumption is below expected range. Check if thermostats are properly configured and HVAC systems are operating. Verify ZoneControl:Thermostat objects are not commented out.'
                    ))
                else:
                    self.warnings.append(EnergyCoherenceIssue(
                        severity='warning',
                        metric='eui',
                        value=eui_kbtu_ft2,
                        expected_range=(min_expected_kbtu_ft2, max_expected_kbtu_ft2),
                        reason=f'EUI {eui_kwh_m2:.1f} kWh/m²/year ({eui_kbtu_ft2:.1f} kBtu/ft²) is below expected range of 100-200 kWh/m²/year',
                        fix_suggestion='Energy consumption is low. Verify HVAC systems are reporting energy and thermostats are active.'
                    ))
            elif eui_kwh_m2 > max_expected_kwh_m2:
                if eui_kwh_m2 > 300:
                    self.issues.append(EnergyCoherenceIssue(
                        severity='error',
                        metric='eui',
                        value=eui_kbtu_ft2,
                        expected_range=(min_expected_kbtu_ft2, max_expected_kbtu_ft2),
                        reason=f'EUI {eui_kwh_m2:.1f} kWh/m²/year ({eui_kbtu_ft2:.1f} kBtu/ft²) is very high. Expected range: 100-200 kWh/m²/year (31.7-63.4 kBtu/ft²)',
                        fix_suggestion='Energy consumption is very high. Check for excessive loads, HVAC efficiency issues, or weather file problems.'
                    ))
                else:
                    self.warnings.append(EnergyCoherenceIssue(
                        severity='warning',
                        metric='eui',
                        value=eui_kbtu_ft2,
                        expected_range=(min_expected_kbtu_ft2, max_expected_kbtu_ft2),
                        reason=f'EUI {eui_kwh_m2:.1f} kWh/m²/year ({eui_kbtu_ft2:.1f} kBtu/ft²) is above expected range of 100-200 kWh/m²/year',
                        fix_suggestion='Energy consumption is high. Check loads, schedules, and HVAC efficiency settings.'
                    ))
            
            # Also compare against CBECS typical values for additional context
            if typical_eui:
                # Check if EUI is in reasonable range (±50% of typical)
                min_acceptable = typical_eui * 0.3
                max_acceptable = typical_eui * 2.0
                
                if eui_kbtu_ft2 < min_acceptable:
                    # Only add if not already flagged by absolute range check
                    if eui_kwh_m2 >= min_expected_kwh_m2:
                        self.issues.append(EnergyCoherenceIssue(
                            severity='error',
                            metric='eui',
                            value=eui_kbtu_ft2,
                            expected_range=(min_acceptable, typical_eui),
                            reason=f'EUI {eui_kbtu_ft2:.1f} kBtu/ft² is very low (typical {building_type}: {typical_eui:.1f} kBtu/ft²)',
                            fix_suggestion='Check if HVAC systems are reporting energy. Verify internal loads are defined.'
                        ))
                elif eui_kbtu_ft2 < typical_eui * 0.7:
                    # Only add if not already flagged
                    if eui_kwh_m2 >= min_expected_kwh_m2:
                        self.warnings.append(EnergyCoherenceIssue(
                            severity='warning',
                            metric='eui',
                            value=eui_kbtu_ft2,
                            expected_range=(typical_eui * 0.7, typical_eui * 1.3),
                            reason=f'EUI {eui_kbtu_ft2:.1f} kBtu/ft² is low (typical {building_type}: {typical_eui:.1f} kBtu/ft²)',
                            fix_suggestion='EUI is 30-70% of typical. May be using Ideal Loads or missing HVAC energy.'
                        ))
                elif eui_kbtu_ft2 > max_acceptable:
                    # Only add if not already flagged
                    if eui_kwh_m2 <= max_expected_kwh_m2:
                        self.issues.append(EnergyCoherenceIssue(
                            severity='error',
                            metric='eui',
                            value=eui_kbtu_ft2,
                            expected_range=(typical_eui, max_acceptable),
                            reason=f'EUI {eui_kbtu_ft2:.1f} kBtu/ft² is very high (typical {building_type}: {typical_eui:.1f} kBtu/ft²)',
                            fix_suggestion='Check for excessive loads, HVAC efficiency issues, or weather file problems.'
                        ))
                elif eui_kbtu_ft2 > typical_eui * 1.5:
                    # Only add if not already flagged
                    if eui_kwh_m2 <= max_expected_kwh_m2:
                        self.warnings.append(EnergyCoherenceIssue(
                            severity='warning',
                            metric='eui',
                            value=eui_kbtu_ft2,
                            expected_range=(typical_eui * 0.7, typical_eui * 1.3),
                            reason=f'EUI {eui_kbtu_ft2:.1f} kBtu/ft² is high (typical {building_type}: {typical_eui:.1f} kBtu/ft²)',
                            fix_suggestion='EUI is high - check loads, schedules, and HVAC efficiency.'
                        ))
        
        # Check individual energy components
        if 'electricity' in energy_by_type:
            elec = energy_by_type['electricity']
            if elec == 0:
                self.warnings.append(EnergyCoherenceIssue(
                    severity='warning',
                    metric='electricity',
                    value=0,
                    expected_range=(1, float('inf')),
                    reason='Electricity consumption is zero',
                    fix_suggestion='Check if lighting and equipment loads are defined and active.'
                ))
        
        if 'heating' in energy_by_type and energy_by_type['heating'] == 0:
            # This might be OK depending on climate
            pass
        
        if 'cooling' in energy_by_type and energy_by_type['cooling'] == 0:
            # This might be OK depending on climate
            pass
        
        if 'lighting' in energy_by_type:
            lighting = energy_by_type['lighting']
            if lighting == 0:
                self.issues.append(EnergyCoherenceIssue(
                    severity='error',
                    metric='lighting',
                    value=0,
                    expected_range=(1, float('inf')),
                    reason='Lighting energy is zero',
                    fix_suggestion='Verify Lights objects are defined and schedules are active.'
                ))
        
        if 'fan' in energy_by_type:
            fan = energy_by_type['fan']
            if fan == 0:
                # Fan energy zero is expected if using Ideal Loads
                if idf_content and 'ZoneHVAC:IdealLoadsAirSystem' in idf_content:
                    pass  # Expected
                else:
                    self.warnings.append(EnergyCoherenceIssue(
                        severity='warning',
                        metric='fan',
                        value=0,
                        expected_range=(1, float('inf')),
                        reason='Fan energy is zero (unusual for VAV/PTAC systems)',
                        fix_suggestion='Check fan definitions and schedules.'
                    ))
        
        return self._format_results()
    
    def _format_results(self) -> Dict:
        """Format validation results"""
        return {
            'issues': self.issues,
            'warnings': self.warnings,
            'issue_count': len(self.issues),
            'warning_count': len(self.warnings),
            'is_coherent': len(self.issues) == 0
        }


def validate_energy_coherence(energy_results: Dict, building_type: str,
                              total_area_m2: float, stories: int = 1,
                              idf_content: Optional[str] = None) -> Dict:
    """
    Convenience function to validate energy coherence.
    
    Args:
        energy_results: Energy results from get_energy_results()
        building_type: Building type
        total_area_m2: Total area in m²
        stories: Number of stories
        idf_content: Optional IDF content for HVAC checking
        
    Returns:
        Validation results dictionary
    """
    validator = EnergyCoherenceValidator()
    return validator.validate_energy_coherence(
        energy_results, building_type, total_area_m2, stories, idf_content
    )



