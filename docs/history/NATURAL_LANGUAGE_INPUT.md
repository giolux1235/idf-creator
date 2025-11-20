# Natural Language IDF Creator 🎉

## Overview

You can now generate EnergyPlus IDF files using **natural language descriptions** and **uploaded documents**! Just describe your building in plain English, and we'll extract all the parameters automatically.

---

## ✨ Features

### 1. **Natural Language Parsing**
- Describe building in plain English
- Automatic extraction of:
  - Building type (office, retail, residential, etc.)
  - Size (stories, floor area, dimensions)
  - HVAC systems (VAV, RTU, PTAC, etc.)
  - Construction details (wall type, roof type, windows)
  - Year built
  - Special features (parking, solar, LED, etc.)

### 2. **Document Upload Support**
- Upload PDF floor plans
- Upload images (photos, drawings)
- Upload Word documents
- Extract building parameters from documents

### 3. **Multiple Interfaces**
- **CLI** - Command line interface
- **Web UI** - Browser-based interface

---

## 🚀 Quick Start

### Method 1: Command Line (CLI)

```bash
# Basic usage
python nlp_cli.py "5-story office building with 50,000 sq ft" --address "San Francisco, CA" --professional

# With documents
python nlp_cli.py "Modern office tower" --address "New York, NY" \
  --documents floorplan.pdf specifications.pdf --professional

# Show parsed parameters
python nlp_cli.py "Retail store, 10,000 sq ft" --address "Chicago, IL" \
  --professional --debug
```

### Method 2: Web Interface

```bash
# Start the web server
python web_interface.py

# Open browser to http://localhost:5000
```

---

## 📝 How to Write Building Descriptions

### Good Examples ✅

```
"5-story modern office building in downtown with 50,000 square feet, 
VAV HVAC system, built in 2015, features LED lighting and solar panels"
```

```
"A retail store with 10,000 sq ft, rooftop HVAC unit, 
constructed in 2020 with energy-efficient windows"
```

```
"Multi-story residential building, 30 apartments, built in 1990, 
features central heating and air conditioning"
```

```
"Warehouse facility, 100,000 square feet, single-story, 
high bay lighting, constructed in 2000"
```

### What You Can Include

**Building Type**:
- office, commercial, retail, store, shopping
- residential, apartment, house, multi-family
- school, university, education
- hospital, medical, healthcare, clinic
- warehouse, industrial, manufacturing
- hotel, hospitality, restaurant

**Size**:
- Number of stories/floors
- Square footage or square meters
- Dimensions (e.g., "100 feet by 200 feet")

**HVAC Systems**:
- VAV (variable air volume)
- RTU (rooftop unit)
- PTAC (packaged terminal AC)
- Heat pump
- Chilled water
- Central HVAC

**Construction Details**:
- Wall type (brick, concrete, steel, wood)
- Roof type (flat, pitched, gabled)
- Window type (single/double/triple pane)

**Features**:
- Parking/garage
- Elevator
- Solar panels
- LED lighting
- Conference rooms
- Fitness center
- Atrium/courtyard
- Basement

**Year**:
- Any 4-digit year (1900-2100)

---

## 🎯 Example Use Cases

### Example 1: Office Building

**Input**:
```bash
python nlp_cli.py "3-story office building, 75,000 square feet, VAV system, built 2018, LED lighting, parking garage" \
  --address "Seattle, WA" \
  --professional
```

**Extracted**:
- Building Type: Office
- Stories: 3
- Floor Area: 75,000 sq ft (6,968 m²)
- HVAC: VAV
- Year: 2018
- Features: LED, parking

### Example 2: Retail Store

**Input**:
```bash
python nlp_cli.py "Single-story retail building with 15,000 sq ft, rooftop AC unit, concrete construction, built 2015" \
  --address "Phoenix, AZ" \
  --professional
```

**Extracted**:
- Building Type: Retail
- Stories: 1
- Floor Area: 15,000 sq ft (1,394 m²)
- HVAC: RTU
- Construction: Concrete
- Year: 2015

### Example 3: With Documents

**Input**:
```bash
python nlp_cli.py "Modern office tower" \
  --address "Chicago, IL" \
  --documents floor_plan.pdf mechanical_drawing.jpg specifications.docx \
  --professional
```

**Process**:
1. Parse natural language description
2. Extract data from uploaded documents
3. Combine all information
4. Generate comprehensive IDF file

---

## 🖥️ Web Interface

### Starting the Web Server

```bash
python web_interface.py
```

### Using the Web Interface

1. **Open your browser** to `http://localhost:5000`

2. **Enter building details**:
   - Building address (required)
   - Natural language description (required)
   - Upload documents (optional)

3. **Click "Generate IDF File"**

4. **Download** the generated IDF file

### Features
- Clean, modern UI
- File upload support
- Real-time processing
- Download generated files
- Error handling

---

## 🧠 How It Works

### 1. Natural Language Processing

```python
from src.nlp_building_parser import BuildingDescriptionParser

parser = BuildingDescriptionParser()
description = "5-story office building with 50,000 sq ft and VAV system"

# Parse description
result = parser.parse_description(description)

# Returns:
# {
#   'building_type': 'office',
#   'stories': 5,
#   'area': 4645.15,  # m² (converted from sq ft)
#   'hvac_system': 'vav',
#   'construction': {'roof_type': 'flat', ...},
#   'year_built': None,
#   'special_features': []
# }
```

### 2. Document Parsing

Documents are parsed using the existing `DocumentParser`:
- PDF text extraction
- Image OCR
- Word document parsing
- Pattern matching for common building parameters

### 3. Parameter Integration

All extracted parameters are combined:
1. Natural language parsing results
2. Document parsing results
3. Location data (from address)
4. Default templates (building type specific)

Final parameters are passed to IDF generator.

---

## 📊 Supported Input Formats

### Text Descriptions
- Plain English
- Any format you want
- Mix of numbers and text
- Natural language patterns

### Documents
- **PDF**: Floor plans, specifications, reports
- **Images**: Photos of buildings, drawings (JPG, PNG)
- **Word**: Specifications, building information (DOCX, DOC)

### Address Formats
- `"123 Main St, San Francisco, CA"`
- `"New York, NY"`
- `"Chicago"`
- Any geocodable address

---

## ⚙️ Command Line Options

```bash
python nlp_cli.py [description] --address ADDRESS [options]

Required:
  --address, -a    Building address

Input (one required):
  description      Building description text
  --input, -i      File with building description

Optional:
  --documents, -d  Upload documents (PDF, images, Word)
  --output, -o     Output IDF file path
  --professional   Use professional mode
  --debug          Show parsed parameters
```

---

## 🔧 Advanced Usage

### Batch Processing

```bash
# Create input file
echo "5-story office, 100,000 sq ft" > building.txt

# Process
python nlp_cli.py --input building.txt \
  --address "San Francisco, CA" \
  --professional
```

### Programmatic Use

```python
from src.nlp_building_parser import BuildingDescriptionParser
from main import IDFCreator

# Parse description
parser = BuildingDescriptionParser()
description = "Modern office building with VAV system"
result = parser.process_and_generate_idf(description, "San Francisco, CA")

# Get parameters
idf_params = result['idf_parameters']

# Generate IDF
creator = IDFCreator(enhanced=True, professional=True)
output = creator.create_idf(
    address="San Francisco, CA",
    user_params=idf_params
)
```

---

## 🐛 Troubleshooting

### Description Not Parsing Correctly

**Problem**: Extracted parameters seem wrong

**Solution**: 
- Be more specific in description
- Include exact numbers
- Use standard terminology (sq ft, stories, etc.)

### Documents Not Parsing

**Problem**: No data extracted from documents

**Solution**:
- Ensure documents contain readable text
- Use clear, high-quality images for OCR
- Check that documents have building info

### Generation Errors

**Problem**: IDF generation fails

**Solution**:
- Check address is valid
- Ensure required parameters are provided
- Use `--debug` flag to see what was extracted

---

## 🎓 Tips for Best Results

1. **Be Specific**: Include exact numbers when possible
   - ✅ "50,000 square feet"
   - ❌ "fairly large building"

2. **Use Standard Terms**: 
   - ✅ "5-story", "VAV system", "built in 2015"
   - ❌ "tall", "air conditioning", "recent"

3. **Include Key Features**:
   - Building type
   - Size (stories + area)
   - HVAC system
   - Year built
   - Special features

4. **Upload Documents When Available**:
   - Floor plans contain accurate dimensions
   - Specifications have HVAC details
   - Images show actual building features

---

## 🔮 Future Enhancements

Planned features:
- 🤖 AI/LLM integration for better understanding
- 📊 Automatic schedule generation from descriptions
- 🏢 Multi-building support
- 🌍 International address support
- 📱 Mobile-friendly web interface
- 🔗 API endpoints for integration

---

## ✅ Summary

**You can now**:
- ✅ Describe buildings in plain English
- ✅ Upload plans and documents
- ✅ Generate IDF files automatically
- ✅ Use CLI or web interface
- ✅ Get validation and feedback

**Try it now**:
```bash
python nlp_cli.py "A modern office building, 5 stories, 50,000 square feet, with VAV HVAC and LED lighting" --address "San Francisco, CA" --professional
```

🎉 **It's that simple!**

