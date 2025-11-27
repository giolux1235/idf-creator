#!/usr/bin/env python3
"""
Extract comprehensive building and energy data from LEED PDF reports.
Processes reports page by page to extract addresses, building details, and energy metrics.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import PyPDF2


class LEEDReportExtractor:
    """Extract comprehensive data from LEED energy audit reports"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.full_text = ""
        self.pages_text = []
        self.data = {}
        
    def extract_all_pages(self) -> List[str]:
        """Extract text from all pages"""
        pdf = open(self.pdf_path, 'rb')
        reader = PyPDF2.PdfReader(pdf)
        
        pages_text = []
        full_text = ""
        
        print(f"  Processing {len(reader.pages)} pages...")
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            pages_text.append(page_text)
            full_text += f"\n--- PAGE {i+1} ---\n" + page_text + "\n"
            if (i + 1) % 10 == 0:
                print(f"    Processed {i+1}/{len(reader.pages)} pages...")
        
        pdf.close()
        
        self.pages_text = pages_text
        self.full_text = full_text
        return pages_text
    
    def extract_address(self) -> Optional[str]:
        """Extract building address from report"""
        # Common address patterns
        address_patterns = [
            r'(\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Lane|Ln|Way|Court|Ct|Place|Pl)[\s,]+[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?)',
            r'Address[:\s]+([^\n]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr)[^\n]+)',
            r'Location[:\s]+([^\n]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr)[^\n]+)',
            r'(\d+\s+[A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5})',
            r'Building Address[:\s]+([^\n]+)',
            r'Property Address[:\s]+([^\n]+)',
        ]
        
        # Search in first few pages (usually where address is)
        search_text = "\n".join(self.pages_text[:5])
        
        for pattern in address_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE | re.MULTILINE)
            if match:
                address = match.group(1).strip()
                # Clean up address
                address = re.sub(r'\s+', ' ', address)
                return address
        
        # Try to find city/state/zip patterns
        city_state_pattern = r'([A-Za-z\s]+),\s*([A-Z]{2})\s+(\d{5})'
        matches = re.findall(city_state_pattern, self.full_text[:5000])
        if matches:
            city, state, zip_code = matches[0]
            # Try to find street address nearby
            context_start = max(0, self.full_text.find(matches[0][0]) - 200)
            context = self.full_text[context_start:self.full_text.find(matches[0][0]) + 100]
            street_match = re.search(r'(\d+\s+[A-Za-z0-9\s]+)', context)
            if street_match:
                return f"{street_match.group(1).strip()}, {city}, {state} {zip_code}"
            return f"{city}, {state} {zip_code}"
        
        return None
    
    def extract_building_name(self) -> Optional[str]:
        """Extract building name"""
        patterns = [
            r'Building Name[:\s]+([^\n]+)',
            r'Facility Name[:\s]+([^\n]+)',
            r'Property Name[:\s]+([^\n]+)',
            r'Project Name[:\s]+([^\n]+)',
            r'Name of Building[:\s]+([^\n]+)',
        ]
        
        search_text = "\n".join(self.pages_text[:3])
        for pattern in patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Try to find title-like text in first page
        first_page_lines = self.pages_text[0].split('\n')[:20]
        for line in first_page_lines:
            line = line.strip()
            if len(line) > 10 and len(line) < 100 and not line.isdigit():
                if any(word in line.lower() for word in ['building', 'center', 'tower', 'hall', 'facility', 'complex']):
                    return line
        
        return None
    
    def extract_area(self) -> Dict[str, float]:
        """Extract building area in various units"""
        area_data = {}
        
        # Patterns for area extraction - more comprehensive
        patterns = [
            # Square feet - explicit labels first
            (r'Total\s+(?:Building\s+)?Area[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:sq\.?\s*ft\.?|ft²|SF|sf)', 'area_sqft'),
            (r'Building\s+Area[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:sq\.?\s*ft\.?|ft²|SF|sf)', 'area_sqft'),
            (r'Gross\s+Floor\s+Area[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:sq\.?\s*ft\.?|ft²|SF|sf)', 'area_sqft'),
            (r'GFA[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:sq\.?\s*ft\.?|ft²|SF|sf)', 'area_sqft'),
            (r'Floor\s+Area[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:sq\.?\s*ft\.?|ft²|SF|sf)', 'area_sqft'),
            (r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:sq\.?\s*ft\.?|ft²|SF|sf)', 'area_sqft'),
            # Square meters
            (r'Total\s+(?:Building\s+)?Area[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:sq\.?\s*m\.?|m²)', 'area_m2'),
            (r'Building\s+Area[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:sq\.?\s*m\.?|m²)', 'area_m2'),
            (r'Gross\s+Floor\s+Area[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:sq\.?\s*m\.?|m²)', 'area_m2'),
            (r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:sq\.?\s*m\.?|m²)', 'area_m2'),
        ]
        
        all_values_sqft = []
        all_values_m2 = []
        
        for pattern, key in patterns:
            matches = re.findall(pattern, self.full_text, re.IGNORECASE)
            if matches:
                values = [float(m.replace(',', '')) for m in matches]
                if key == 'area_sqft':
                    all_values_sqft.extend(values)
                elif key == 'area_m2':
                    all_values_m2.extend(values)
        
        # Filter reasonable values (100 sqft to 10M sqft)
        reasonable_sqft = [v for v in all_values_sqft if 100 <= v <= 10000000]
        reasonable_m2 = [v for v in all_values_m2 if 10 <= v <= 1000000]
        
        if reasonable_sqft:
            # Take median or largest reasonable value
            reasonable_sqft.sort()
            area_data['area_sqft'] = reasonable_sqft[len(reasonable_sqft)//2] if len(reasonable_sqft) > 1 else reasonable_sqft[0]
        
        if reasonable_m2:
            reasonable_m2.sort()
            area_data['area_m2'] = reasonable_m2[len(reasonable_m2)//2] if len(reasonable_m2) > 1 else reasonable_m2[0]
        
        # Convert between units if we have one
        if 'area_sqft' in area_data and 'area_m2' not in area_data:
            area_data['area_m2'] = area_data['area_sqft'] * 0.092903
        elif 'area_m2' in area_data and 'area_sqft' not in area_data:
            area_data['area_sqft'] = area_data['area_m2'] * 10.7639
        
        return area_data
    
    def extract_floors(self) -> Optional[int]:
        """Extract number of floors/stories"""
        patterns = [
            r'Number\s+of\s+Stories[:\s]+(\d+)',
            r'Number\s+of\s+Floors[:\s]+(\d+)',
            r'Stories[:\s]+(\d+)',
            r'Floors[:\s]+(\d+)',
            r'(\d+)\s*(?:stories|floors)',
            r'(\d+)\s*story',
            r'(\d+)\s*floor',
            r'(\d+)\s*level',
            r'(\d+)\s*storey',
        ]
        
        all_values = []
        for pattern in patterns:
            matches = re.findall(pattern, self.full_text, re.IGNORECASE)
            if matches:
                values = [int(m) for m in matches]
                all_values.extend(values)
        
        # Filter out unrealistic values
        reasonable_values = [v for v in all_values if 1 <= v <= 200]
        if reasonable_values:
            # Take the most common value, or median if tied
            from collections import Counter
            value_counts = Counter(reasonable_values)
            most_common = value_counts.most_common(1)[0]
            return most_common[0]
        
        return None
    
    def extract_year_built(self) -> Optional[int]:
        """Extract year built"""
        patterns = [
            r'Year\s+Built[:\s]+(\d{4})',
            r'Built[:\s]+(\d{4})',
            r'Construction\s+Year[:\s]+(\d{4})',
            r'(\d{4})\s+construction',
            r'constructed\s+in\s+(\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.full_text, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                if 1800 <= year <= 2025:
                    return year
        
        # Look for years in context
        year_matches = re.findall(r'\b(19\d{2}|20[0-2]\d)\b', self.full_text[:10000])
        if year_matches:
            years = [int(y) for y in year_matches if 1900 <= int(y) <= 2025]
            if years:
                # Return most common year (likely construction year)
                return max(set(years), key=years.count)
        
        return None
    
    def extract_building_type(self) -> str:
        """Extract building type"""
        search_text = self.full_text[:5000].lower()
        
        type_keywords = {
            'Office': ['office', 'commercial office', 'business'],
            'School': ['school', 'education', 'academic', 'university', 'college'],
            'Hospital': ['hospital', 'medical', 'healthcare', 'clinic'],
            'Retail': ['retail', 'store', 'shopping', 'mall'],
            'Residential': ['residential', 'apartment', 'housing', 'dormitory'],
            'Warehouse': ['warehouse', 'storage', 'distribution'],
            'Hotel': ['hotel', 'lodging', 'hospitality'],
            'Restaurant': ['restaurant', 'dining', 'cafeteria'],
            'Fire Station': ['fire station', 'fire department'],
            'Municipal': ['municipal', 'town hall', 'city hall', 'government'],
        }
        
        for btype, keywords in type_keywords.items():
            if any(keyword in search_text for keyword in keywords):
                return btype
        
        return 'Office'  # Default
    
    def extract_eui(self) -> Dict[str, float]:
        """Extract Energy Use Intensity (EUI)"""
        eui_data = {}
        
        patterns = [
            # kBtu/sqft patterns
            (r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*kBtu/sqft', 'eui_kbtu_sqft'),
            (r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*kBtu/sf', 'eui_kbtu_sqft'),
            (r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*kBtu/ft²', 'eui_kbtu_sqft'),
            (r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*kBtu/ft2', 'eui_kbtu_sqft'),
            (r'Site\s+EUI[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*kBtu', 'site_eui_kbtu_sqft'),
            (r'Source\s+EUI[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*kBtu', 'source_eui_kbtu_sqft'),
            # kWh/m2 patterns
            (r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*kWh/m²', 'eui_kwh_m2'),
            (r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*kWh/m2', 'eui_kwh_m2'),
            (r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*kWh/sq\.?\s*m', 'eui_kwh_m2'),
        ]
        
        for pattern, key in patterns:
            matches = re.findall(pattern, self.full_text, re.IGNORECASE)
            if matches:
                values = [float(m.replace(',', '')) for m in matches]
                if values:
                    # Take values in reasonable range
                    reasonable_values = [v for v in values if 10 <= v <= 500]
                    if reasonable_values:
                        eui_data[key] = reasonable_values[0]  # Take first reasonable value
        
        # Convert between units
        if 'eui_kbtu_sqft' in eui_data and 'eui_kwh_m2' not in eui_data:
            # kBtu/sqft to kWh/m2: 1 kBtu/sqft = 3.15459 kWh/m2
            eui_data['eui_kwh_m2'] = eui_data['eui_kbtu_sqft'] * 3.15459
        elif 'eui_kwh_m2' in eui_data and 'eui_kbtu_sqft' not in eui_data:
            # kWh/m2 to kBtu/sqft
            eui_data['eui_kbtu_sqft'] = eui_data['eui_kwh_m2'] / 3.15459
        
        return eui_data
    
    def extract_energy_consumption(self) -> Dict[str, float]:
        """Extract annual energy consumption"""
        energy_data = {}
        
        # Electricity patterns
        elec_patterns = [
            (r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*kWh\s*(?:per\s+year|annually|annual)', 'annual_electric_kwh'),
            (r'Annual\s+Electric[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*kWh', 'annual_electric_kwh'),
            (r'Total\s+Electric[:\s]+(\d{1,3}(?:,\d{3})*(?:,\d{3})*)\s*kWh', 'annual_electric_kwh'),
            (r'Electricity[:\s]+(\d{1,3}(?:,\d{3})*(?:,\d{3})*)\s*kWh', 'annual_electric_kwh'),
        ]
        
        # Natural gas patterns
        gas_patterns = [
            (r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*therms\s*(?:per\s+year|annually|annual)', 'annual_gas_therms'),
            (r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*MMBtu\s*(?:per\s+year|annually|annual)', 'annual_gas_mmbtu'),
            (r'Annual\s+Gas[:\s]+(\d{1,3}(?:,\d{3})*(?:,\d{3})*)\s*therms', 'annual_gas_therms'),
            (r'Natural\s+Gas[:\s]+(\d{1,3}(?:,\d{3})*(?:,\d{3})*)\s*therms', 'annual_gas_therms'),
        ]
        
        # Total site energy
        total_patterns = [
            (r'Total\s+Site\s+Energy[:\s]+(\d{1,3}(?:,\d{3})*(?:,\d{3})*)\s*kWh', 'total_site_energy_kwh'),
            (r'Total\s+Energy[:\s]+(\d{1,3}(?:,\d{3})*(?:,\d{3})*)\s*kWh', 'total_site_energy_kwh'),
            (r'(\d{1,3}(?:,\d{3})*(?:,\d{3})*)\s*kWh\s*Total', 'total_site_energy_kwh'),
        ]
        
        for pattern, key in elec_patterns + gas_patterns + total_patterns:
            matches = re.findall(pattern, self.full_text, re.IGNORECASE)
            if matches:
                values = [float(m.replace(',', '')) for m in matches]
                if values:
                    # Take largest reasonable value
                    reasonable_values = [v for v in values if v > 0]
                    if reasonable_values:
                        energy_data[key] = max(reasonable_values)
        
        # Convert gas units
        if 'annual_gas_therms' in energy_data:
            # 1 therm = 29.3 kWh
            energy_data['annual_gas_kwh'] = energy_data['annual_gas_therms'] * 29.3
        if 'annual_gas_mmbtu' in energy_data:
            # 1 MMBtu = 293.071 kWh
            energy_data['annual_gas_kwh'] = energy_data['annual_gas_mmbtu'] * 293.071
        
        return energy_data
    
    def extract_energy_breakdown(self) -> Dict[str, float]:
        """Extract energy breakdown by end use"""
        breakdown = {}
        
        # Look for percentage breakdowns
        end_use_patterns = [
            ('Lighting', r'Lighting[:\s]+(\d+(?:\.\d+)?)\s*%'),
            ('HVAC', r'HVAC[:\s]+(\d+(?:\.\d+)?)\s*%'),
            ('Heating', r'Heating[:\s]+(\d+(?:\.\d+)?)\s*%'),
            ('Cooling', r'Cooling[:\s]+(\d+(?:\.\d+)?)\s*%'),
            ('Plug Loads', r'Plug\s+Loads?[:\s]+(\d+(?:\.\d+)?)\s*%'),
            ('Equipment', r'Equipment[:\s]+(\d+(?:\.\d+)?)\s*%'),
            ('Water Heating', r'Water\s+Heating[:\s]+(\d+(?:\.\d+)?)\s*%'),
            ('Ventilation', r'Ventilation[:\s]+(\d+(?:\.\d+)?)\s*%'),
        ]
        
        for end_use, pattern in end_use_patterns:
            matches = re.findall(pattern, self.full_text, re.IGNORECASE)
            if matches:
                values = [float(m) for m in matches]
                if values:
                    # Take first reasonable value (0-100%)
                    reasonable = [v for v in values if 0 <= v <= 100]
                    if reasonable:
                        breakdown[end_use] = reasonable[0]
        
        return breakdown
    
    def extract_lighting_details(self) -> Dict[str, float]:
        """Extract lighting power density and details"""
        lighting_data = {}
        
        # Lighting power density patterns (W/sqft or W/m²)
        patterns = [
            (r'Lighting\s+Power\s+Density[:\s]+(\d+(?:\.\d+)?)\s*W/sqft', 'lighting_power_density_w_sqft'),
            (r'Lighting\s+Power\s+Density[:\s]+(\d+(?:\.\d+)?)\s*W/ft²', 'lighting_power_density_w_sqft'),
            (r'LPD[:\s]+(\d+(?:\.\d+)?)\s*W/sqft', 'lighting_power_density_w_sqft'),
            (r'LPD[:\s]+(\d+(?:\.\d+)?)\s*W/ft²', 'lighting_power_density_w_sqft'),
            (r'(\d+(?:\.\d+)?)\s*W/sqft\s*(?:lighting|LPD)', 'lighting_power_density_w_sqft'),
            (r'Lighting\s+Power\s+Density[:\s]+(\d+(?:\.\d+)?)\s*W/m²', 'lighting_power_density_w_m2'),
            (r'Lighting\s+Power\s+Density[:\s]+(\d+(?:\.\d+)?)\s*W/m2', 'lighting_power_density_w_m2'),
            (r'LPD[:\s]+(\d+(?:\.\d+)?)\s*W/m²', 'lighting_power_density_w_m2'),
            (r'(\d+(?:\.\d+)?)\s*W/m²\s*(?:lighting|LPD)', 'lighting_power_density_w_m2'),
        ]
        
        for pattern, key in patterns:
            matches = re.findall(pattern, self.full_text, re.IGNORECASE)
            if matches:
                values = [float(m) for m in matches]
                if values:
                    reasonable = [v for v in values if 0.1 <= v <= 50]  # Reasonable range
                    if reasonable:
                        lighting_data[key] = reasonable[0]
                        break
        
        # Convert between units
        if 'lighting_power_density_w_sqft' in lighting_data and 'lighting_power_density_w_m2' not in lighting_data:
            lighting_data['lighting_power_density_w_m2'] = lighting_data['lighting_power_density_w_sqft'] * 10.7639
        elif 'lighting_power_density_w_m2' in lighting_data and 'lighting_power_density_w_sqft' not in lighting_data:
            lighting_data['lighting_power_density_w_sqft'] = lighting_data['lighting_power_density_w_m2'] / 10.7639
        
        # Extract total lighting power if available
        lighting_power_patterns = [
            (r'Total\s+Lighting\s+Power[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*kW', 'total_lighting_power_kw'),
            (r'Lighting\s+Load[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*kW', 'total_lighting_power_kw'),
        ]
        
        for pattern, key in lighting_power_patterns:
            match = re.search(pattern, self.full_text, re.IGNORECASE)
            if match:
                value = float(match.group(1).replace(',', ''))
                if 0 < value < 10000:  # Reasonable range
                    lighting_data[key] = value
                    break
        
        return lighting_data
    
    def extract_equipment_details(self) -> Dict[str, float]:
        """Extract equipment power density and details"""
        equipment_data = {}
        
        # Equipment power density patterns
        patterns = [
            (r'Equipment\s+Power\s+Density[:\s]+(\d+(?:\.\d+)?)\s*W/sqft', 'equipment_power_density_w_sqft'),
            (r'Equipment\s+Power\s+Density[:\s]+(\d+(?:\.\d+)?)\s*W/ft²', 'equipment_power_density_w_sqft'),
            (r'EPD[:\s]+(\d+(?:\.\d+)?)\s*W/sqft', 'equipment_power_density_w_sqft'),
            (r'Plug\s+Load\s+Density[:\s]+(\d+(?:\.\d+)?)\s*W/sqft', 'equipment_power_density_w_sqft'),
            (r'(\d+(?:\.\d+)?)\s*W/sqft\s*(?:equipment|plug)', 'equipment_power_density_w_sqft'),
            (r'Equipment\s+Power\s+Density[:\s]+(\d+(?:\.\d+)?)\s*W/m²', 'equipment_power_density_w_m2'),
            (r'Equipment\s+Power\s+Density[:\s]+(\d+(?:\.\d+)?)\s*W/m2', 'equipment_power_density_w_m2'),
            (r'EPD[:\s]+(\d+(?:\.\d+)?)\s*W/m²', 'equipment_power_density_w_m2'),
        ]
        
        for pattern, key in patterns:
            matches = re.findall(pattern, self.full_text, re.IGNORECASE)
            if matches:
                values = [float(m) for m in matches]
                if values:
                    reasonable = [v for v in values if 0.1 <= v <= 50]
                    if reasonable:
                        equipment_data[key] = reasonable[0]
                        break
        
        # Convert between units
        if 'equipment_power_density_w_sqft' in equipment_data and 'equipment_power_density_w_m2' not in equipment_data:
            equipment_data['equipment_power_density_w_m2'] = equipment_data['equipment_power_density_w_sqft'] * 10.7639
        elif 'equipment_power_density_w_m2' in equipment_data and 'equipment_power_density_w_sqft' not in equipment_data:
            equipment_data['equipment_power_density_w_sqft'] = equipment_data['equipment_power_density_w_m2'] / 10.7639
        
        # Extract total equipment power
        equipment_power_patterns = [
            (r'Total\s+Equipment\s+Power[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*kW', 'total_equipment_power_kw'),
            (r'Equipment\s+Load[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*kW', 'total_equipment_power_kw'),
            (r'Plug\s+Load[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*kW', 'total_equipment_power_kw'),
        ]
        
        for pattern, key in equipment_power_patterns:
            match = re.search(pattern, self.full_text, re.IGNORECASE)
            if match:
                value = float(match.group(1).replace(',', ''))
                if 0 < value < 10000:
                    equipment_data[key] = value
                    break
        
        return equipment_data
    
    def extract_occupancy_details(self) -> Dict[str, float]:
        """Extract occupancy density and number of people"""
        occupancy_data = {}
        
        # Occupancy density patterns (people/sqft or people/m²)
        patterns = [
            (r'Occupancy\s+Density[:\s]+(\d+(?:\.\d+)?)\s*people/sqft', 'occupancy_density_people_sqft'),
            (r'Occupancy\s+Density[:\s]+(\d+(?:\.\d+)?)\s*people/ft²', 'occupancy_density_people_sqft'),
            (r'(\d+(?:\.\d+)?)\s*people/sqft', 'occupancy_density_people_sqft'),
            (r'Occupancy\s+Density[:\s]+(\d+(?:\.\d+)?)\s*people/m²', 'occupancy_density_people_m2'),
            (r'Occupancy\s+Density[:\s]+(\d+(?:\.\d+)?)\s*people/m2', 'occupancy_density_people_m2'),
            (r'(\d+(?:\.\d+)?)\s*people/m²', 'occupancy_density_people_m2'),
            (r'(\d+(?:\.\d+)?)\s*people/m2', 'occupancy_density_people_m2'),
        ]
        
        for pattern, key in patterns:
            matches = re.findall(pattern, self.full_text, re.IGNORECASE)
            if matches:
                values = [float(m) for m in matches]
                if values:
                    reasonable = [v for v in values if 0.001 <= v <= 1.0]  # Reasonable range
                    if reasonable:
                        occupancy_data[key] = reasonable[0]
                        break
        
        # Convert between units
        if 'occupancy_density_people_sqft' in occupancy_data and 'occupancy_density_people_m2' not in occupancy_data:
            occupancy_data['occupancy_density_people_m2'] = occupancy_data['occupancy_density_people_sqft'] * 10.7639
        elif 'occupancy_density_people_m2' in occupancy_data and 'occupancy_density_people_sqft' not in occupancy_data:
            occupancy_data['occupancy_density_people_sqft'] = occupancy_data['occupancy_density_people_m2'] / 10.7639
        
        # Extract total number of people
        people_patterns = [
            (r'Number\s+of\s+People[:\s]+(\d{1,3}(?:,\d{3})*)', 'total_people'),
            (r'Total\s+Occupancy[:\s]+(\d{1,3}(?:,\d{3})*)', 'total_people'),
            (r'Occupants[:\s]+(\d{1,3}(?:,\d{3})*)', 'total_people'),
            (r'(\d{1,3}(?:,\d{3})*)\s*(?:people|occupants|employees)', 'total_people'),
        ]
        
        for pattern, key in people_patterns:
            matches = re.findall(pattern, self.full_text, re.IGNORECASE)
            if matches:
                values = [int(m.replace(',', '')) for m in matches]
                if values:
                    reasonable = [v for v in values if 1 <= v <= 100000]
                    if reasonable:
                        # Take the largest reasonable value
                        occupancy_data[key] = max(reasonable)
                        break
        
        return occupancy_data
    
    def extract_hvac_details(self) -> Dict[str, any]:
        """Extract HVAC system type and details"""
        hvac_data = {}
        
        # HVAC system type patterns
        hvac_types = [
            'VAV', 'Variable Air Volume', 'Variable Air Volume System',
            'CAV', 'Constant Air Volume', 'Constant Air Volume System',
            'PTAC', 'Packaged Terminal Air Conditioner',
            'PSZ', 'Packaged Single Zone', 'Packaged Single Zone System',
            'RTU', 'Rooftop Unit', 'Rooftop Unit System',
            'Chiller', 'Chilled Water', 'Chilled Water System',
            'Boiler', 'Hot Water', 'Hot Water System',
            'Heat Pump', 'Heat Pump System',
            'DX', 'Direct Expansion', 'Direct Expansion System',
            'Split System', 'Split System Air Conditioner',
            'Window Unit', 'Window Air Conditioner',
            'Ideal Loads', 'Ideal Loads Air System',
        ]
        
        for hvac_type in hvac_types:
            pattern = rf'\b{re.escape(hvac_type)}\b'
            if re.search(pattern, self.full_text, re.IGNORECASE):
                if 'hvac_system_types' not in hvac_data:
                    hvac_data['hvac_system_types'] = []
                hvac_data['hvac_system_types'].append(hvac_type)
        
        # Extract HVAC capacity
        capacity_patterns = [
            (r'HVAC\s+Capacity[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*tons', 'hvac_capacity_tons'),
            (r'Cooling\s+Capacity[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*tons', 'cooling_capacity_tons'),
            (r'Heating\s+Capacity[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*MBH', 'heating_capacity_mbh'),
            (r'Total\s+Capacity[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*tons', 'hvac_capacity_tons'),
        ]
        
        for pattern, key in capacity_patterns:
            match = re.search(pattern, self.full_text, re.IGNORECASE)
            if match:
                value = float(match.group(1).replace(',', ''))
                if 0 < value < 10000:
                    hvac_data[key] = value
                    break
        
        return hvac_data
    
    def extract_operating_schedule(self) -> Dict[str, str]:
        """Extract operating hours and schedule information"""
        schedule_data = {}
        
        # Operating hours patterns
        hours_patterns = [
            (r'Operating\s+Hours[:\s]+(\d+)\s*(?:hours?|hrs?)', 'operating_hours_per_day'),
            (r'Hours\s+of\s+Operation[:\s]+(\d+)', 'operating_hours_per_day'),
            (r'(\d+)\s*hours?\s*(?:per\s+day|daily)', 'operating_hours_per_day'),
            (r'Open\s+(\d+)\s*(?:hours?|hrs?)', 'operating_hours_per_day'),
        ]
        
        for pattern, key in hours_patterns:
            match = re.search(pattern, self.full_text, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                if 1 <= value <= 24:
                    schedule_data[key] = value
                    break
        
        # Operating days patterns
        days_patterns = [
            (r'Operating\s+Days[:\s]+(\d+)', 'operating_days_per_week'),
            (r'(\d+)\s*days?\s*(?:per\s+week|weekly)', 'operating_days_per_week'),
        ]
        
        for pattern, key in days_patterns:
            match = re.search(pattern, self.full_text, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                if 1 <= value <= 7:
                    schedule_data[key] = value
                    break
        
        # Schedule description
        schedule_desc_patterns = [
            (r'Schedule[:\s]+([^\n]+)', 'schedule_description'),
            (r'Operating\s+Schedule[:\s]+([^\n]+)', 'schedule_description'),
            (r'Hours[:\s]+([^\n]+)', 'schedule_description'),
        ]
        
        for pattern, key in schedule_desc_patterns:
            match = re.search(pattern, self.full_text, re.IGNORECASE)
            if match:
                desc = match.group(1).strip()
                if len(desc) < 100:  # Reasonable length
                    schedule_data[key] = desc
                    break
        
        return schedule_data
    
    def extract_window_details(self) -> Dict[str, float]:
        """Extract window-to-wall ratio and window details"""
        window_data = {}
        
        # Window-to-wall ratio patterns
        wwr_patterns = [
            (r'Window[-\s]to[-\s]Wall\s+Ratio[:\s]+(\d+(?:\.\d+)?)\s*%', 'window_to_wall_ratio_percent'),
            (r'WWR[:\s]+(\d+(?:\.\d+)?)\s*%', 'window_to_wall_ratio_percent'),
            (r'Window\s+Ratio[:\s]+(\d+(?:\.\d+)?)\s*%', 'window_to_wall_ratio_percent'),
            (r'Glazing\s+Ratio[:\s]+(\d+(?:\.\d+)?)\s*%', 'window_to_wall_ratio_percent'),
        ]
        
        for pattern, key in wwr_patterns:
            match = re.search(pattern, self.full_text, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                if 0 <= value <= 100:
                    window_data[key] = value
                    window_data['window_to_wall_ratio'] = value / 100.0  # Convert to decimal
                    break
        
        return window_data
    
    def extract_all_data(self) -> Dict:
        """Extract all data from PDF"""
        print(f"Extracting data from: {os.path.basename(self.pdf_path)}")
        
        # Extract all pages
        self.extract_all_pages()
        
        # Extract all data fields
        data = {
            'pdf_path': self.pdf_path,
            'pdf_filename': os.path.basename(self.pdf_path),
        }
        
        # Extract address
        address = self.extract_address()
        if address:
            data['address'] = address
            print(f"  ✓ Address: {address}")
        
        # Extract building name
        building_name = self.extract_building_name()
        if building_name:
            data['building_name'] = building_name
            print(f"  ✓ Building: {building_name}")
        
        # Extract area
        area_data = self.extract_area()
        data.update(area_data)
        if 'area_sqft' in area_data:
            print(f"  ✓ Area: {area_data['area_sqft']:,.0f} sqft ({area_data.get('area_m2', 0):,.0f} m²)")
        
        # Extract floors
        floors = self.extract_floors()
        if floors:
            data['floors'] = floors
            print(f"  ✓ Floors: {floors}")
        
        # Extract year built
        year_built = self.extract_year_built()
        if year_built:
            data['year_built'] = year_built
            print(f"  ✓ Year Built: {year_built}")
        
        # Extract building type
        building_type = self.extract_building_type()
        data['building_type'] = building_type
        print(f"  ✓ Building Type: {building_type}")
        
        # Extract EUI
        eui_data = self.extract_eui()
        data.update(eui_data)
        if 'eui_kbtu_sqft' in eui_data:
            print(f"  ✓ EUI: {eui_data['eui_kbtu_sqft']:.1f} kBtu/sqft")
        
        # Extract energy consumption
        energy_data = self.extract_energy_consumption()
        data.update(energy_data)
        if 'annual_electric_kwh' in energy_data:
            print(f"  ✓ Annual Electric: {energy_data['annual_electric_kwh']:,.0f} kWh")
        if 'total_site_energy_kwh' in energy_data:
            print(f"  ✓ Total Site Energy: {energy_data['total_site_energy_kwh']:,.0f} kWh")
        
        # Extract energy breakdown
        breakdown = self.extract_energy_breakdown()
        if breakdown:
            data['energy_breakdown_percent'] = breakdown
            print(f"  ✓ Energy Breakdown: {breakdown}")
        
        # Extract lighting details
        lighting_details = self.extract_lighting_details()
        if lighting_details:
            data['lighting_details'] = lighting_details
            if 'lighting_power_density_w_m2' in lighting_details:
                print(f"  ✓ Lighting Power Density: {lighting_details['lighting_power_density_w_m2']:.2f} W/m²")
        
        # Extract equipment details
        equipment_details = self.extract_equipment_details()
        if equipment_details:
            data['equipment_details'] = equipment_details
            if 'equipment_power_density_w_m2' in equipment_details:
                print(f"  ✓ Equipment Power Density: {equipment_details['equipment_power_density_w_m2']:.2f} W/m²")
        
        # Extract occupancy details
        occupancy_details = self.extract_occupancy_details()
        if occupancy_details:
            data['occupancy_details'] = occupancy_details
            if 'occupancy_density_people_m2' in occupancy_details:
                print(f"  ✓ Occupancy Density: {occupancy_details['occupancy_density_people_m2']:.4f} people/m²")
            if 'total_people' in occupancy_details:
                print(f"  ✓ Total People: {occupancy_details['total_people']:,}")
        
        # Extract HVAC details
        hvac_details = self.extract_hvac_details()
        if hvac_details:
            data['hvac_details'] = hvac_details
            if 'hvac_system_types' in hvac_details:
                print(f"  ✓ HVAC System Types: {', '.join(hvac_details['hvac_system_types'][:3])}")
        
        # Extract operating schedule
        schedule_details = self.extract_operating_schedule()
        if schedule_details:
            data['operating_schedule'] = schedule_details
            if 'operating_hours_per_day' in schedule_details:
                print(f"  ✓ Operating Hours: {schedule_details['operating_hours_per_day']} hrs/day")
        
        # Extract window details
        window_details = self.extract_window_details()
        if window_details:
            data['window_details'] = window_details
            if 'window_to_wall_ratio_percent' in window_details:
                print(f"  ✓ Window-to-Wall Ratio: {window_details['window_to_wall_ratio_percent']:.1f}%")
        
        self.data = data
        return data


def select_diverse_reports(pdf_files: List[str]) -> List[str]:
    """Select 5 diverse reports for testing - prioritize complete energy audit reports"""
    selected = []
    pdf_files = [str(p) for p in pdf_files]  # Ensure strings
    
    # Prioritize reports with "Energy Audit" or "ASHRAE" in name (more complete)
    priority_keywords = ['Energy Audit', 'ASHRAE', 'Audit Report', 'Energy Model']
    
    # First pass: select priority reports
    for pdf in pdf_files:
        pdf_lower = os.path.basename(pdf).lower()
        if any(keyword.lower() in pdf_lower for keyword in priority_keywords):
            if pdf not in selected:
                selected.append(pdf)
                if len(selected) >= 5:
                    break
    
    # Second pass: fill remaining slots with diverse reports
    seen_prefixes = {os.path.basename(p)[:20] for p in selected}
    for pdf in pdf_files:
        if pdf not in selected:
            prefix = os.path.basename(pdf)[:20]
            if prefix not in seen_prefixes:
                selected.append(pdf)
                seen_prefixes.add(prefix)
                if len(selected) >= 5:
                    break
    
    # If still need more, add any remaining
    if len(selected) < 5:
        for pdf in pdf_files:
            if pdf not in selected:
                selected.append(pdf)
                if len(selected) >= 5:
                    break
    
    return selected[:5]


def main():
    """Main extraction function"""
    print("="*80)
    print("LEED REPORT DATA EXTRACTION")
    print("="*80)
    
    # Find all PDFs in test reports LEED directory
    downloads_dir = Path("/Users/giovanniamenta/Downloads")
    
    # Try to find the LEED directory
    leed_dirs = [d for d in downloads_dir.glob("*LEED*") if d.is_dir()]
    if not leed_dirs:
        print(f"❌ LEED directory not found in Downloads")
        return 1
    
    leed_dir = leed_dirs[0]  # Use first match
    
    print(f"✓ Found LEED directory: {leed_dir}")
    
    # Get all PDF files
    pdf_files = list(leed_dir.glob("*.pdf")) + list(leed_dir.glob("*.PDF"))
    
    if not pdf_files:
        print(f"❌ No PDF files found in {leed_dir}")
        return 1
    
    print(f"\nFound {len(pdf_files)} PDF files")
    
    # Select 5 diverse reports
    selected_reports = select_diverse_reports([str(p) for p in pdf_files])
    
    print(f"\nSelected {len(selected_reports)} reports for extraction:")
    for i, pdf in enumerate(selected_reports, 1):
        print(f"  {i}. {os.path.basename(pdf)}")
    
    # Extract data from each report
    all_extracted_data = []
    
    for i, pdf_path in enumerate(selected_reports, 1):
        print(f"\n[{i}/{len(selected_reports)}] Processing: {os.path.basename(pdf_path)}")
        print("-" * 80)
        
        try:
            extractor = LEEDReportExtractor(pdf_path)
            data = extractor.extract_all_data()
            all_extracted_data.append(data)
            print(f"  ✅ Successfully extracted data")
        except Exception as e:
            print(f"  ❌ Error extracting data: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Save extracted data
    output_dir = Path("artifacts/leed_extracted_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save individual test files
    for i, data in enumerate(all_extracted_data, 1):
        test_file = output_dir / f"test_{i}_{os.path.basename(data['pdf_filename']).replace('.pdf', '.json')}"
        with open(test_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n✓ Saved test {i}: {test_file}")
    
    # Save combined file
    combined_file = output_dir / "all_extracted_tests.json"
    with open(combined_file, 'w') as f:
        json.dump({
            'extraction_date': str(Path.cwd()),
            'total_reports': len(all_extracted_data),
            'tests': all_extracted_data
        }, f, indent=2)
    
    print(f"\n✓ Saved combined data: {combined_file}")
    
    # Print summary
    print("\n" + "="*80)
    print("EXTRACTION SUMMARY")
    print("="*80)
    
    for i, data in enumerate(all_extracted_data, 1):
        print(f"\nTest {i}: {data.get('building_name', 'Unknown')}")
        print(f"  Address: {data.get('address', 'Not found')}")
        print(f"  Type: {data.get('building_type', 'Unknown')}")
        if 'area_sqft' in data:
            print(f"  Area: {data['area_sqft']:,.0f} sqft")
        if 'floors' in data:
            print(f"  Floors: {data['floors']}")
        if 'eui_kbtu_sqft' in data:
            print(f"  EUI: {data['eui_kbtu_sqft']:.1f} kBtu/sqft")
    
    print("\n" + "="*80)
    print(f"✅ Successfully extracted data from {len(all_extracted_data)} reports")
    print(f"📁 Output directory: {output_dir}")
    print("="*80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

