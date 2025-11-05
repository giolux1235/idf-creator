# 🚀 START HERE - IDF Creator

Welcome to **IDF Creator**, an automated tool that generates complete EnergyPlus simulation files from minimal inputs!

## ✨ What You Got

A complete Python application that:
- ✅ Takes an address and generates a full EnergyPlus IDF file
- ✅ Parses building documents (PDFs, images) automatically
- ✅ Uses smart defaults based on building type
- ✅ Works with geocoding APIs to get location data
- ✅ Creates simulation-ready files

## 🏃 Quick Start (3 Steps)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run It!
```bash
python main.py "Empire State Building, New York, NY"
```

### Step 3: Your IDF is Ready!
Check the `output/` folder for your generated IDF file.

## 📁 Project Structure

```
IDF-CREATOR/
├── 🎯 main.py              ← Start here! Main application
├── 📖 README.md            ← Full documentation
├── ⚡ QUICKSTART.md        ← 5-minute guide
├── 📋 requirements.txt     ← Dependencies
├── ⚙️  config.yaml         ← Customize defaults
├── 📦 example.py           ← Usage examples
│
└── src/                    ← Core modules
    ├── location_fetcher.py      # Geocoding & climate
    ├── document_parser.py       # PDF/image parsing
    ├── building_estimator.py    # Smart defaults
    └── idf_generator.py         # IDF creation
```

## 💡 Example Commands

### Basic Usage
```bash
python main.py "1600 Amphitheatre Parkway, Mountain View, CA"
```

### With Building Type
```bash
python main.py "Times Square, New York, NY" --building-type Retail
```

### Full Customization
```bash
python main.py "123 Main St, Boston, MA" \
  --building-type "Office" \
  --stories 5 \
  --floor-area 2000 \
  --window-ratio 0.5 \
  --output my_building.idf
```

### With Documents
```bash
python main.py "456 Oak Ave" --documents plans.pdf floorplan.jpg
```

## 🎨 Use in Python Code

```python
from main import IDFCreator

# Create a creator instance
creator = IDFCreator()

# Generate an IDF
creator.create_idf(
    address="Empire State Building, New York, NY",
    user_params={
        'building_type': 'Office',
        'stories': 102,
        'floor_area': 50000
    }
)
```

## 📚 Documentation

- **README.md** - Complete documentation with all features
- **QUICKSTART.md** - Fast 5-minute setup guide
- **PROJECT_SUMMARY.md** - Technical architecture details
- **config.yaml** - Configuration options and defaults

## 🎯 Key Features

### 1. **Minimal Input**
   - Just an address required
   - Everything else is optional

### 2. **Smart Defaults**
   - Building type templates (Office, Residential, Retail, etc.)
   - Industry-standard materials
   - Typical schedules

### 3. **Document Intelligence**
   - Parse PDFs and images
   - Extract floor area, stories, building type
   - OCR support

### 4. **Climate-Aware**
   - Automatic climate zone detection
   - Weather file recommendations
   - Location-specific data

## 🛠️ Configuration

Edit `config.yaml` to customize:
- Default building parameters
- Material libraries
- HVAC systems
- Simulation settings

## 🔧 Advanced Options

Run with `--help` to see all options:
```bash
python main.py --help
```

Options include:
- `--building-type`: Office, Residential, Retail, Warehouse, School, Hospital
- `--stories`: Number of stories
- `--floor-area`: Total area in m²
- `--window-ratio`: Window-to-wall ratio (0-1)
- `--documents`: List of files to parse
- `--output`: Custom output path

## 📊 Building Types Supported

| Type        | Typical Use Case              |
|-------------|-------------------------------|
| Office      | Commercial office buildings   |
| Residential | Apartments, houses           |
| Retail      | Shops, malls                 |
| Warehouse   | Storage, industrial          |
| School      | Educational facilities       |
| Hospital    | Healthcare buildings         |

## 🎓 Next Steps

1. Try the basic example above
2. Read QUICKSTART.md for more examples
3. Customize config.yaml for your needs
4. Integrate into your workflow

## ❓ Need Help?

- Check README.md for detailed documentation
- See example.py for code examples
- Open an issue for support

## 🎉 You're Ready!

Your IDF Creator is fully set up and ready to generate EnergyPlus simulation files!

Start with:
```bash
python main.py "Your Building Address Here"
```

Happy simulating! 🏗️⚡

























