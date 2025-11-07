"""Module for parsing building documents and extracting parameters."""
import re
from typing import Dict, List, Optional
from pathlib import Path


class DocumentParser:
    """Parses PDF, image, and text documents to extract building parameters."""
    
    def __init__(self):
        self.footprints = []
    
    def parse_text(self, text: str) -> Dict:
        """
        Extract building parameters from plain text.
        
        Args:
            text: Plain text content
            
        Returns:
            Dictionary with extracted building parameters
        """
        params = {}
        
        # Extract floor area
        area_match = re.search(r'floor\s*area[:\s]*(\d+(?:\.\d+)?)\s*(?:sq|m2|sqm|m²)', 
                               text, re.IGNORECASE)
        if area_match:
            params['floor_area'] = float(area_match.group(1))
        
        # Extract number of stories
        stories_match = re.search(r'(\d+)\s*(?:story|floor|level)', 
                                  text, re.IGNORECASE)
        if stories_match:
            params['stories'] = int(stories_match.group(1))
        
        # Extract building type
        building_types = ['office', 'residential', 'retail', 'warehouse', 
                         'hospital', 'school', 'hotel', 'apartment']
        for btype in building_types:
            if re.search(r'\b' + btype + r'\b', text, re.IGNORECASE):
                params['building_type'] = btype.capitalize()
                break
        
        # Extract window to wall ratio
        wwr_match = re.search(r'window[:\s]*(\d+(?:\.\d+)?)\s*%', 
                              text, re.IGNORECASE)
        if wwr_match:
            params['window_to_wall_ratio'] = float(wwr_match.group(1)) / 100
        
        # Extract year built
        year_match = re.search(r'built\s+(\d{4})', text, re.IGNORECASE)
        if year_match:
            params['year_built'] = int(year_match.group(1))
        
        return params
    
    def parse_pdf(self, pdf_path: str) -> Dict:
        """
        Extract text from PDF and parse it.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with extracted building parameters
        """
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
            
            return self.parse_text(text)
        
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return {}
    
    def parse_image(self, image_path: str) -> Dict:
        """
        Extract text from image using OCR.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with extracted building parameters
        """
        try:
            from pytesseract import image_to_string
            from PIL import Image
            
            image = Image.open(image_path)
            text = image_to_string(image)
            
            return self.parse_text(text)
        
        except Exception as e:
            print(f"Error parsing image: {e}")
            return {}
    
    def parse_document(self, file_path: str) -> Dict:
        """
        Automatically detect file type and parse accordingly.
        
        Args:
            file_path: Path to document file
            
        Returns:
            Dictionary with extracted building parameters
        """
        path = Path(file_path)
        
        if path.suffix.lower() == '.pdf':
            return self.parse_pdf(file_path)
        elif path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            return self.parse_image(file_path)
        elif path.suffix.lower() == '.txt':
            with open(file_path, 'r') as f:
                return self.parse_text(f.read())
        else:
            print(f"Unsupported file type: {path.suffix}")
            return {}



























