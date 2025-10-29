# Quick Start Guide

Get up and running with IDF Creator in 5 minutes!

## 1. Installation (1 minute)

```bash
# Install Python dependencies
pip install -r requirements.txt
```

## 2. First IDF Creation (30 seconds)

Try the simplest example:

```bash
python main.py "Empire State Building, New York, NY"
```

You should see output like:
```
============================================================
🏗️  IDF Creator for EnergyPlus
============================================================

🔍 Fetching location data...
✓ Found location: 40.7484, -73.9857
✓ Climate zone: ASHRAE_C5

📐 Estimating building parameters...
✓ Building dimensions: 25.0m × 20.0m

⚙️  Generating IDF file...

✅ IDF file created: output/Building.idf
```

## 3. Customize Your Building (2 minutes)

Create a retail building with 2 stories:

```bash
python main.py "Times Square, New York, NY" \
  --building-type "Retail" \
  --stories 2 \
  --floor-area 1500
```

## 4. Use Python API (2 minutes)

Create a Python script:

```python
# my_building.py
from main import IDFCreator

creator = IDFCreator()

creator.create_idf(
    address="1600 Amphitheatre Parkway, Mountain View, CA",
    user_params={
        'building_type': 'Office',
        'stories': 4,
        'floor_area': 2000
    }
)
```

Run it:
```bash
python my_building.py
```

## 5. Advanced: With Documents

If you have building plans:

```bash
python main.py "123 Main St, Boston, MA" \
  --documents plans.pdf floorplan.jpg
```

The tool will automatically extract floor area, stories, and other info!

## That's It! 🎉

Your IDF files are ready in the `output/` directory.

Run them with EnergyPlus:
```bash
energyplus -w weather.epw output/Building.idf
```

---

**Next Steps:**
- Read the full [README.md](README.md) for more options
- Check `config.yaml` to customize default values
- See `example.py` for more examples






