# IDF Creator - Project Summary

## 🎯 Project Overview

**IDF Creator** is an automated tool that generates complete EnergyPlus Input Data Files (IDF) from minimal user input. Instead of manually creating complex IDF files with hundreds of objects, users can simply provide an address and optional documents to generate a simulation-ready file.

## 🏗️ Architecture

### Core Components

1. **Location Fetcher** (`src/location_fetcher.py`)
   - Geocodes addresses to get coordinates
   - Determines ASHRAE climate zones
   - Selects appropriate weather files
   - Uses OpenStreetMap Nominatim API

2. **Document Parser** (`src/document_parser.py`)
   - Parses PDFs using PyPDF2
   - Performs OCR on images using Tesseract
   - Extracts building parameters:
     - Floor area
     - Number of stories
     - Building type
     - Window-to-wall ratio
     - Year built

3. **Building Estimator** (`src/building_estimator.py`)
   - Provides default values for missing parameters
   - Estimates building dimensions from floor area
   - Calculates zone-level parameters (people, lighting, equipment)
   - Uses building-type templates for typical values

4. **IDF Generator** (`src/idf_generator.py`)
   - Core engine for creating IDF files
   - Generates all required IDF objects:
     - Building and location
     - Materials and constructions
     - Zones and surfaces
     - Internal loads (people, lighting, equipment)
     - HVAC systems
     - Schedules
     - Simulation controls
   - Ensures valid EnergyPlus syntax

5. **Main Application** (`main.py`)
   - Orchestrates the entire workflow
   - Command-line interface
   - Can be imported as a Python module
   - Combines all inputs into complete IDF

## 📊 Data Flow

```
User Input (Address + Optional Docs/Params)
           ↓
Location Fetcher → Coordinates + Climate Zone + Weather File
           ↓
Document Parser → Extracted Parameters
           ↓
Building Estimator → Complete Building Parameters
           ↓
IDF Generator → Full IDF File
           ↓
EnergyPlus Simulation Ready!
```

## 🔧 Key Features

### 1. Minimal Input Required
- **Required**: Building address
- **Optional**: Documents, custom parameters

### 2. Smart Defaults
- ASHRAE-compliant materials
- Building type templates
- Typical schedules
- Standard constructions

### 3. Document Intelligence
- Extracts key parameters automatically
- Works with PDFs and images
- OCR support for scanned documents

### 4. Climate-Aware
- Automatic climate zone detection
- Weather file recommendations
- Location-specific parameters

## 📁 Project Structure

```
IDF-CREATOR/
├── main.py                      # Main application entry point
├── example.py                   # Usage examples
├── config.yaml                  # Configuration file
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup
├── README.md                    # Full documentation
├── QUICKSTART.md               # Quick start guide
├── LICENSE                     # MIT License
├── src/
│   ├── __init__.py
│   ├── location_fetcher.py    # Geocoding and climate
│   ├── document_parser.py     # PDF/image parsing
│   ├── building_estimator.py  # Parameter estimation
│   └── idf_generator.py       # IDF file generation
└── output/                     # Generated IDF files (auto-created)
```

## 🎨 Design Decisions

### 1. Modular Architecture
- Each component is independent and testable
- Easy to extend with new features
- Clear separation of concerns

### 2. Parameter Hierarchy
Priority order (highest to lowest):
1. User-provided parameters
2. Document-extracted parameters
3. Building-type defaults
4. Generic defaults

### 3. EnergyPlus Compatibility
- Follows EnergyPlus IDF syntax exactly
- Includes all required objects
- Uses industry-standard material libraries
- Validates object references

### 4. User Experience
- Progress indicators during processing
- Clear error messages
- Helpful suggestions
- Both CLI and Python API

## 🔌 External APIs/Tools Used

1. **Nominatim (OpenStreetMap)**
   - Free geocoding service
   - No API key required
   - Global coverage

2. **Tesseract OCR**
   - Open-source OCR engine
   - Extracts text from images
   - Handles scanned documents

3. **PyEnergyPlus**
   - Python interface to EnergyPlus
   - IDF manipulation capabilities

## 🚀 Usage Examples

### Basic Command Line
```bash
python main.py "123 Main St, San Francisco, CA"
```

### With Documents
```bash
python main.py "456 Oak Ave" --documents plans.pdf floorplan.jpg
```

### Custom Parameters
```bash
python main.py "789 Pine Rd" --building-type Retail --stories 2
```

### Python API
```python
from main import IDFCreator

creator = IDFCreator()
creator.create_idf(
    address="Empire State Building",
    user_params={'building_type': 'Office', 'stories': 102}
)
```

## 📈 Future Enhancements

### Potential Improvements

1. **Enhanced Document Parsing**
   - AI/ML for better information extraction
   - CAD file support (AutoCAD, Revit)
   - Building information modeling (BIM) integration

2. **Advanced Geometry**
   - Complex building shapes
   - Multiple zones with different uses
   - Detailed fenestration modeling

3. **External Data Sources**
   - Building databases (e.g., CEC, NREL)
   - Building permits API integration
   - Zillow/similar property data

4. **More HVAC Options**
   - Detailed systems (VAV, PTAC, etc.)
   - Custom equipment
   - District energy

5. **Validation & Quality Checks**
   - IDF syntax validation
   - Parameter range checking
   - Simulation recommendations

6. **User Interface**
   - Web interface
   - Interactive parameter adjustment
   - Preview building geometry
   - Visualization tools

## 🧪 Testing

### Manual Testing
Run the example script:
```bash
python example.py
```

### Unit Tests (Future)
- Test each module independently
- Mock external API calls
- Validate IDF syntax

## 📚 Dependencies

### Core
- Python 3.8+
- geopy: Geocoding
- requests: HTTP requests
- PyYAML: Config parsing

### Document Processing
- PyPDF2: PDF parsing
- pytesseract: OCR
- Pillow: Image handling

### EnergyPlus
- pyenergyplus: IDF manipulation
- EnergyPlus (external): Simulation engine

## 🎓 Educational Value

This project demonstrates:
- API integration for geocoding
- Document parsing and OCR
- Template-based code generation
- EnergyPlus IDF file structure
- Building energy modeling workflows
- Command-line tool development
- Configuration management

## 🤝 Contributing

Areas where contributions would be valuable:
- Additional building type templates
- More sophisticated geometry estimation
- Enhanced document parsing
- Integration with more data sources
- UI/UX improvements
- Testing and validation

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

Built for the EnergyPlus community to make building energy simulation more accessible. Uses excellent open-source tools for geocoding (Nominatim), OCR (Tesseract), and energy simulation (EnergyPlus).

---

**Status**: ✅ Complete and ready to use
**Version**: 1.0.0
**Last Updated**: 2024















