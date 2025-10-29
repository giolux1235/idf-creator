# 🏗️ IDF Creator - Intelligent Building Energy Modeler

Automatically generate EnergyPlus IDF files from natural language descriptions and documents!

## ✨ Features

- 🤖 **Natural Language Input** - Describe your building in plain English
- 📄 **Document Upload** - Upload floor plans, specifications, drawings
- 🧠 **LLM Integration** - Uses OpenAI/Claude for intelligent parsing
- 🌍 **Location Intelligence** - Automatic climate data and OSM integration
- 🎯 **Professional IDFs** - Complete EnergyPlus compatible files
- ✅ **Validation** - CBECS benchmarking for results verification

## 🚀 Quick Start

### Web Interface

```bash
python web_interface.py
# Open http://localhost:5000
```

### Command Line

```bash
# Basic usage
python nlp_cli.py "5-story office building with 50,000 sq ft" \
  --address "San Francisco, CA" --professional

# With documents
python nlp_cli.py "Modern office tower" \
  --address "New York, NY" \
  --documents floorplan.pdf specifications.pdf \
  --professional
```

## 📊 Example

**Input**:
```
"A 3-story modern office building with 10,000 square feet, 
VAV HVAC system, LED lighting, built in 2020"
```

**Output**: Complete EnergyPlus IDF file ready to simulate!

## 🛠️ Capabilities

- ✅ 10+ building types
- ✅ Advanced HVAC systems (VAV, RTU, PTAC, Heat Pumps)
- ✅ ASHRAE 90.1 compliant materials
- ✅ Shading and daylighting
- ✅ Natural ventilation
- ✅ Renewable energy systems
- ✅ CBECS validation

## 🌐 Deploy on Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

Or deploy manually:
1. Fork this repo
2. Connect to Railway
3. Add environment variables
4. Deploy!

## 📚 Documentation

- [HOW_IT_WORKS.md](HOW_IT_WORKS.md) - How the system works
- [NATURAL_LANGUAGE_INPUT.md](NATURAL_LANGUAGE_INPUT.md) - Using NLP features
- [ENHANCED_CAPABILITIES.md](ENHANCED_CAPABILITIES.md) - Advanced features

## 📄 License

See [LICENSE](LICENSE) file.

## 🤝 Contributing

Contributions welcome! Open an issue or PR.

