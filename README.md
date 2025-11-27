# IDF Creator for EnergyPlus

**Generate complete EnergyPlus IDF (Input Data File) from minimal inputs like an address and basic building information.**

<div align="center">
  <img src="docs/assets/images/buildings/hero-building.png" alt="IDF Creator - Building Energy Modeling" width="800"/>
</div>

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

Creating EnergyPlus IDF files typically requires detailed knowledge of:
- Building geometry and construction
- Material properties and constructions
- HVAC systems and schedules
- Climate data and simulation parameters

**IDF Creator automates this process**, allowing you to generate simulation-ready IDF files with just:
- A building address (for location and climate data)
- Optional documents (PDFs, images with building plans)
- Basic parameters (building type, stories, floor area)

![Building Energy Modeling](docs/assets/images/buildings/building-example.png)
*Example: IDF Creator can generate energy models for various building types*

## ✨ Features

- 🌍 **Automatic location detection** - Geocoding and climate zone determination
- 📄 **Document parsing** - Extract building info from PDFs and images
- 🏗️ **Smart defaults** - Industry-standard materials and constructions
- ⚡ **Building type templates** - Office, Residential, Retail, Warehouse, etc.
- 🎛️ **Complete IDF generation** - Zones, surfaces, loads, HVAC, schedules
- 📊 **BESTEST-compliant outputs** - Automatically includes 30+ output variables for comprehensive analysis
- ✅ **Ready to simulate** - Output files work directly with EnergyPlus

<div align="center">
  <img src="docs/assets/images/buildings/building-types.png" alt="Supported Building Types" width="600"/>
  <p><em>IDF Creator supports multiple building types with industry-standard templates</em></p>
</div>

## 🚀 Quick Start

### Installation

1. **Clone or download this repository**

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **(Optional) Install Tesseract OCR for image parsing:**
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

4. **(Optional) Configure API keys** (for enhanced features):
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### Usage

#### Basic Usage
Generate an IDF file from just an address:
```bash
python main.py "123 Main St, San Francisco, CA"
```

#### With Documents
Parse building information from PDFs or images:
```bash
python main.py "456 Oak Ave, Boston, MA" --documents building_plans.pdf floorplan.jpg specifications.pdf
```

#### With Custom Parameters
Specify building characteristics:
```bash
python main.py "789 Pine Rd, Seattle, WA" \
  --building-type "Retail" \
  --stories 2 \
  --floor-area 1500 \
  --window-ratio 0.5
```

#### Custom Output Path
```bash
python main.py "321 Elm St, Chicago, IL" --output my_simulation.idf
```

## 📋 Input Options

### Required
- **address**: Building street address (any location worldwide)

### Optional Parameters
- `--building-type`: Office, Residential, Retail, Warehouse, School, Hospital
- `--stories`: Number of stories
- `--floor-area`: Total floor area in square meters
- `--window-ratio`: Window to wall ratio (0-1)
- `--documents`: List of PDFs, images, or text files
- `--output`: Custom output file path

## 📁 Output

The tool generates a complete EnergyPlus IDF file containing:

- ✅ **Building geometry** - Multi-story zones with realistic dimensions
- ✅ **Construction assemblies** - Exterior walls, roof, floor, windows
- ✅ **Material properties** - Industry-standard thermal properties
- ✅ **Internal loads** - People, lighting, equipment (type-dependent)
- ✅ **HVAC systems** - Ideal loads system
- ✅ **Schedules** - Occupancy, lighting, equipment, HVAC
- ✅ **Climate data** - Location and weather file references
- ✅ **Simulation control** - Run periods and output requests
- ✅ **Comprehensive outputs** - Automatically includes BESTEST-required output variables:
  - Zone-level metrics (temperature, heating/cooling energy)
  - Surface-level metrics (heat transfer, temperatures)
  - HVAC system performance (COP, efficiency, energy consumption)
  - Environmental data (outdoor conditions, solar radiation)
  - Building-level summaries

### Output Location

IDF files are saved to the `output/` directory by default, or to the specified path.

## 🏗️ How It Works

![IDF Creator Workflow](docs/assets/images/workflow/idf-creator-workflow.png)
*The IDF Creator pipeline: From address to complete EnergyPlus model*

1. **Location Processing**
   - Geocodes the address to get coordinates
   - Determines ASHRAE climate zone
   - Selects appropriate weather file

2. **Document Parsing** (if provided)
   - Extracts text from PDFs using PyPDF2
   - Performs OCR on images using Tesseract
   - Identifies floor area, stories, building type, etc.

3. **Parameter Estimation**
   - Uses building type to set typical loads and schedules
   - Estimates building dimensions from floor area
   - Calculates zone-level parameters

4. **IDF Generation**
   - Creates complete IDF structure
   - Generates zone, surface, and construction objects
   - Adds loads, HVAC, and schedules
   - Links to weather data

## 🛠️ Advanced Configuration

Edit `config.yaml` to customize:

```yaml
defaults:
  building_type: "Office"
  stories: 3
  floor_area_per_story_m2: 500
  window_to_wall_ratio: 0.4

materials:
  wall_construction: "ASHRAE_C90"
  roof_construction: "ASHRAE_M90"
  
simulation:
  run_period_start: "1/1"
  run_period_end: "12/31"
  timestep: 6
```

## 📚 Example Output

When you run the tool, you'll see:

```
============================================================
🏗️  IDF Creator for EnergyPlus
============================================================

🔍 Fetching location data...
✓ Found location: 37.7749, -122.4194
✓ Climate zone: ASHRAE_C3

📐 Estimating building parameters...
✓ Building dimensions: 25.0m × 20.0m

⚙️  Generating IDF file...

✅ IDF file created: output/Building.idf
📊 Zone area: 500.0 m²
👥 People per zone: 35
💡 Lighting power: 5000.0 W

============================================================
✨ Ready to simulate in EnergyPlus!
============================================================
```

![Example Building Model](docs/assets/images/buildings/example-building-model.png)
*Example: Generated building model ready for EnergyPlus simulation*

## 🔧 Requirements

- Python 3.8+
- EnergyPlus (for running simulations)

### Python Packages
- pyenergyplus - IDF manipulation
- geopy - Geocoding
- requests - API calls
- PyPDF2 - PDF parsing
- pytesseract - OCR
- pillow - Image processing
- pandas, numpy - Data processing

See `requirements.txt` for complete list.

## 🌍 API Keys (Optional)

Some features can be enhanced with API keys (not required for basic functionality):

- **Google Maps API** - Enhanced geocoding
- **Weather APIs** - More accurate climate data

Add them to `.env` (see `.env.example`).

## 🎓 Building Types

The tool includes templates for common building types with typical:

| Building Type | People/m² | Lighting W/m² | Equipment W/m² | Infiltration (ACH) |
|--------------|-----------|---------------|----------------|---------------------|
| Office       | 0.07      | 10.0          | 15.0           | 0.25                |
| Residential  | 0.05      | 8.0           | 5.0            | 0.5                 |
| Retail       | 0.15      | 15.0          | 8.0            | 0.3                 |
| Warehouse    | 0.005     | 8.0           | 2.0            | 0.5                 |
| School       | 0.2       | 12.0          | 5.0            | 0.4                 |
| Hospital     | 0.1       | 12.0          | 20.0           | 0.2                 |

## 🚀 Running EnergyPlus Simulations

Once you have an IDF file, run it with EnergyPlus:

```bash
# Download weather file first
# Then run EnergyPlus:
energyplus -w weather.epw output/Building.idf
```

## 📝 Notes

- The generated IDF files use simplified default values suitable for most simulations
- Materials and constructions follow ASHRAE standards
- HVAC systems use ideal loads (simplified but comprehensive)
- Consider customizing materials and systems for detailed studies
- Weather files should match your climate zone

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
```

For more information, see [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md).

## 📚 Additional Documentation

- [Contributing Guidelines](CONTRIBUTING.md) - How to contribute to the project
- [API Documentation](docs/API_DOCUMENTATION.md) - API reference
- [User Workflow Guide](docs/USER_WORKFLOW_GUIDE.md) - Detailed usage guide
- [How It Works](docs/HOW_IT_WORKS.md) - Technical overview

## 📁 Project Structure

```
idf-creator/
├── src/                    # Main source code
│   ├── core/              # Core IDF generation logic
│   ├── validation/        # Validation modules
│   ├── compliance/        # Compliance checking (ASHRAE 90.1)
│   ├── utils/             # Utility functions
│   └── ...                # Other modules (HVAC, geometry, etc.)
├── tests/                  # Test suite
│   ├── data/             # Test data files
│   └── test_*.py         # Test modules
├── examples/              # Example scripts and usage
├── scripts/               # Utility scripts
│   └── archive/          # Historical/one-off scripts
├── docs/                  # Documentation
│   ├── history/         # Historical documentation
│   └── *.md             # Current documentation
├── main.py               # Main entry point
├── requirements.txt      # Python dependencies
├── CONTRIBUTING.md       # Contribution guidelines
└── README.md            # This file
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and add tests
4. Run tests: `python -m pytest tests/`
5. Submit a pull request

### Areas for Contribution

- Enhanced document parsing
- More building type templates
- Additional HVAC system types
- Better geometry estimation
- Integration with building databases
- Improved test coverage
- Documentation improvements

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

Built for the EnergyPlus community. Uses open-source geocoding and document processing tools.

---

**Need help?** Open an issue or check the documentation.

**Ready to simulate?** Generate your IDF file and run EnergyPlus!



























