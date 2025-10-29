"""
Natural Language Processing for Building Description Parsing
Extracts building parameters from natural language descriptions using AI/LLM
"""

from typing import Dict, List, Optional
import re
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class BuildingDescriptionParser:
    """
    Parses natural language building descriptions to extract:
    - Building type
    - Size (area, stories, dimensions)
    - HVAC systems
    - Construction details
    - Operational parameters
    """
    
    def __init__(self, use_llm: bool = True, llm_provider: str = 'openai', api_key: str = None):
        """
        Initialize parser
        
        Args:
            use_llm: Use LLM for better understanding (requires API key)
            llm_provider: 'openai' or 'anthropic'
            api_key: API key for LLM provider
        """
        self.use_llm = use_llm and self._check_llm_availability()
        self.llm_provider = llm_provider if self.use_llm else None
        
        # Initialize LLM client if available
        if self.use_llm:
            self.api_key = api_key or self._get_api_key()
            if llm_provider == 'openai' and OPENAI_AVAILABLE:
                openai.api_key = self.api_key
                self.client = openai
            elif llm_provider == 'anthropic' and ANTHROPIC_AVAILABLE:
                self.client = Anthropic(api_key=self.api_key)
            else:
                self.use_llm = False
                print("⚠️  LLM not available, falling back to pattern matching")
        
        self.building_type_patterns = self._load_building_patterns()
        self.size_patterns = self._load_size_patterns()
        self.hvac_patterns = self._load_hvac_patterns()
    
    def _check_llm_availability(self) -> bool:
        """Check if LLM libraries are available"""
        return OPENAI_AVAILABLE or ANTHROPIC_AVAILABLE
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment variables"""
        import os
        if self.llm_provider == 'openai':
            return os.getenv('OPENAI_API_KEY')
        elif self.llm_provider == 'anthropic':
            return os.getenv('ANTHROPIC_API_KEY')
        return None
    
    def _load_building_patterns(self) -> Dict:
        """Keyword patterns for building type detection"""
        return {
            'office': ['office', 'commercial office', 'business', 'corporate', 'tower', 'skyscraper'],
            'residential': ['residential', 'apartment', 'house', 'home', 'condo', 'condominium', 'multi-family'],
            'retail': ['retail', 'store', 'shopping', 'mall', 'commercial', 'boutique', 'supermarket'],
            'school': ['school', 'education', 'university', 'college', 'elementary', 'high school'],
            'hospital': ['hospital', 'medical', 'healthcare', 'clinic', 'emergency'],
            'warehouse': ['warehouse', 'storage', 'industrial', 'distribution', 'factory'],
            'hotel': ['hotel', 'motel', 'hospitality', 'resort', 'lodge'],
            'restaurant': ['restaurant', 'dining', 'cafe', 'bistro', 'kitchen'],
        }
    
    def _load_size_patterns(self) -> Dict:
        """Patterns for extracting size information"""
        return {
            'stories': [
                r'(\d+)\s*(?:story|stories|floors?|levels?)',
                r'(?:story|stories|floors?|levels?)\s*(\d+)',
                r'(\d+)-story',
                r'multi-story',
                r'high-rise'
            ],
            'area': [
                r'(\d+(?:,\d+)?)\s*(?:sq\s*ft|ft²|square\s*feet)',
                r'(\d+(?:,\d+)?)\s*(?:sq\s*m|m²|square\s*meters?)',
                r'(\d+(?:,\d+)?)\s*(?:square\s*footage|sqft)',
                r'(\d+)\s*sf',
            ],
            'dimensions': [
                r'(\d+)\s*x\s*(\d+)',
                r'(\d+)\s*by\s*(\d+)',
                r'(\d+)\s*feet?\s*(?:wide|by)\s*(\d+)',
            ]
        }
    
    def _load_hvac_patterns(self) -> Dict:
        """Patterns for detecting HVAC systems"""
        return {
            'vav': ['variable air volume', 'vav', 'central hvac'],
            'rtu': ['rooftop unit', 'rtu', 'packaged rooftop'],
            'ptac': ['ptac', 'packaged terminal', 'wall unit'],
            'heat_pump': ['heat pump', 'mini-split', 'split system'],
            'chilled_water': ['chilled water', 'central plant', 'district cooling'],
        }
    
    def parse_description(self, description: str) -> Dict:
        """
        Parse natural language building description
        
        Args:
            description: Natural language description of the building
            
        Returns:
            Dictionary with extracted building parameters
        """
        # Try LLM first if available
        if self.use_llm and self.api_key:
            try:
                llm_params = self._parse_with_llm(description)
                if llm_params:
                    return llm_params
            except Exception as e:
                print(f"⚠️  LLM parsing failed: {e}, using pattern matching")
        
        # Fallback to pattern matching
        description_lower = description.lower()
        
        params = {
            'building_type': self._extract_building_type(description_lower),
            'stories': self._extract_stories(description_lower),
            'area': self._extract_area(description_lower),
            'dimensions': self._extract_dimensions(description_lower),
            'hvac_system': self._extract_hvac_system(description_lower),
            'construction': self._extract_construction(description_lower),
            'year_built': self._extract_year_built(description_lower),
            'special_features': self._extract_special_features(description_lower)
        }
        
        return params
    
    def _parse_with_llm(self, description: str) -> Optional[Dict]:
        """
        Parse description using LLM for better understanding
        
        Args:
            description: Building description
            
        Returns:
            Parsed parameters or None if failed
        """
        system_prompt = """You are an expert building energy modeler. Extract building parameters from descriptions 
and return a JSON object with these fields:
- building_type: office, retail, residential, school, hospital, warehouse, hotel, restaurant
- stories: integer number of floors (or null if not mentioned)
- area: floor area in square meters (convert from sq ft if needed)
- dimensions: {length: meters, width: meters} or null
- hvac_system: vav, rtu, ptac, heat_pump, chilled_water, or null
- construction: {wall_type: concrete/steel_frame/wood_frame/brick, roof_type: flat/gabled, window_type: single_pane/double_pane/triple_pane}
- year_built: integer year or null
- special_features: array of features like ["parking", "elevator", "solar", "led"]

Return ONLY valid JSON, no markdown or explanation."""

        user_prompt = f"Extract building parameters from this description: {description}"

        if self.llm_provider == 'openai' and OPENAI_AVAILABLE:
            try:
                response = self.client.ChatCompletion.create(
                    model="gpt-4o-mini",  # Fast and cheap
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,  # Low temperature for consistent extraction
                    max_tokens=500
                )
                
                result = response.choices[0].message.content.strip()
                
                # Parse JSON response
                if result.startswith('```json'):
                    result = result[7:]
                if result.endswith('```'):
                    result = result[:-3]
                
                return json.loads(result.strip())
                
            except Exception as e:
                print(f"OpenAI API error: {e}")
                return None
        
        elif self.llm_provider == 'anthropic' and ANTHROPIC_AVAILABLE:
            try:
                message = self.client.messages.create(
                    model="claude-3-haiku-20240307",  # Fast and cheap
                    max_tokens=500,
                    temperature=0.1,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                
                result = message.content[0].text.strip()
                
                # Parse JSON response
                if result.startswith('```json'):
                    result = result[7:]
                if result.endswith('```'):
                    result = result[:-3]
                
                return json.loads(result.strip())
                
            except Exception as e:
                print(f"Anthropic API error: {e}")
                return None
        
        return None
    
    def _extract_building_type(self, text: str) -> str:
        """Extract building type from description"""
        scores = {}
        
        for btype, patterns in self.building_type_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text)
            if score > 0:
                scores[btype] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'office'  # Default
    
    def _extract_stories(self, text: str) -> Optional[int]:
        """Extract number of stories"""
        for pattern in self.size_patterns['stories']:
            match = re.search(pattern, text)
            if match:
                try:
                    return int(match.group(1)) if match.group(1).isdigit() else None
                except:
                    pass
            
            # Handle multi-story without number
            if 'multi-story' in pattern and pattern in text:
                return 3  # Default assumption
            elif 'high-rise' in text:
                return 20  # Default for high-rise
        
        return None
    
    def _extract_area(self, text: str) -> Optional[float]:
        """Extract floor area"""
        areas = []
        
        # Check for sq ft
        for pattern in self.size_patterns['area']:
            match = re.search(pattern, text)
            if match:
                area_str = match.group(1).replace(',', '')
                try:
                    area = float(area_str)
                    # Check if it's sq ft or m²
                    if 'ft' in text[text.lower().find(pattern):text.lower().find(pattern)+50].lower():
                        # Convert sq ft to m²
                        area = area * 0.092903
                    areas.append(area)
                except:
                    pass
        
        return max(areas) if areas else None
    
    def _extract_dimensions(self, text: str) -> Optional[Dict]:
        """Extract building dimensions"""
        for pattern in self.size_patterns['dimensions']:
            match = re.search(pattern, text)
            if match:
                try:
                    length = float(match.group(1))
                    width = float(match.group(2))
                    return {'length': length, 'width': width}
                except:
                    pass
        
        return None
    
    def _extract_hvac_system(self, text: str) -> Optional[str]:
        """Extract HVAC system type"""
        for hvac_type, keywords in self.hvac_patterns.items():
            if any(keyword in text for keyword in keywords):
                return hvac_type
        
        return None
    
    def _extract_construction(self, text: str) -> Dict:
        """Extract construction details"""
        construction = {
            'wall_type': None,
            'roof_type': None,
            'window_type': None
        }
        
        # Wall types
        if 'brick' in text:
            construction['wall_type'] = 'masonry'
        elif 'concrete' in text:
            construction['wall_type'] = 'concrete'
        elif 'steel' in text or 'metal' in text:
            construction['wall_type'] = 'steel_frame'
        elif 'wood' in text:
            construction['wall_type'] = 'wood_frame'
        
        # Roof types
        if 'flat roof' in text:
            construction['roof_type'] = 'flat'
        elif 'gabled' in text or 'pitched' in text:
            construction['roof_type'] = 'gabled'
        
        # Window types
        if 'double pane' in text or 'double-pane' in text:
            construction['window_type'] = 'double_pane'
        elif 'triple pane' in text:
            construction['window_type'] = 'triple_pane'
        elif 'single pane' in text:
            construction['window_type'] = 'single_pane'
        
        return construction
    
    def _extract_year_built(self, text: str) -> Optional[int]:
        """Extract year built"""
        # Look for year patterns (1900-2100)
        year_pattern = r'\b(19|20)\d{2}\b'
        matches = re.findall(year_pattern, text)
        
        if matches:
            # Assume last mentioned year is the year built/renovated
            return int(matches[-1])
        
        return None
    
    def _extract_special_features(self, text: str) -> List[str]:
        """Extract special features"""
        features = []
        
        feature_keywords = {
            'parking': ['parking', 'garage', 'car park'],
            'elevator': ['elevator', 'lift'],
            'solar': ['solar', 'photovoltaic', 'pv panels'],
            'led': ['led lighting', 'led'],
            'high_ceiling': ['high ceiling', 'cathedral ceiling', 'vaulted'],
            'atrium': ['atrium', 'courtyard'],
            'terrace': ['terrace', 'balcony', 'patio'],
            'basement': ['basement', 'underground'],
            'conference_room': ['conference', 'meeting room'],
            'gym': ['gym', 'fitness', 'exercise'],
        }
        
        for feature, keywords in feature_keywords.items():
            if any(keyword in text for keyword in keywords):
                features.append(feature)
        
        return features
    
    def convert_to_idf_params(self, parsed_description: Dict) -> Dict:
        """
        Convert parsed description to IDF parameters
        
        Args:
            parsed_description: Output from parse_description()
            
        Returns:
            Dictionary compatible with IDF creator parameters
        """
        params = {}
        
        # Building type
        if parsed_description['building_type']:
            params['building_type'] = parsed_description['building_type'].capitalize()
        
        # Stories
        if parsed_description['stories']:
            params['stories'] = parsed_description['stories']
        
        # Floor area
        if parsed_description['area']:
            params['floor_area'] = parsed_description['area']
        
        # Dimensions
        if parsed_description['dimensions']:
            dims = parsed_description['dimensions']
            params['length'] = dims['length']
            params['width'] = dims['width']
        
        # HVAC system
        if parsed_description['hvac_system']:
            params['hvac_system_type'] = parsed_description['hvac_system']
        
        # Year built
        if parsed_description['year_built']:
            params['year_built'] = parsed_description['year_built']
        
        # Special features
        if parsed_description['special_features']:
            params['features'] = parsed_description['special_features']
        
        return params
    
    def process_and_generate_idf(self, description: str, address: str) -> Dict:
        """
        Complete pipeline: parse description and return IDF-ready parameters
        
        Args:
            description: Natural language building description
            address: Building address
            
        Returns:
            Complete parameter dictionary for IDF generation
        """
        # Parse the description
        parsed = self.parse_description(description)
        
        # Convert to IDF parameters
        idf_params = self.convert_to_idf_params(parsed)
        
        # Add the address
        idf_params['address'] = address
        
        return {
            'parsed_description': parsed,
            'idf_parameters': idf_params
        }

