# Weather File Handling: How It Works

## 🎯 Short Answer

**IDF Creator automatically determines the weather file NAME** from the address, but **the user needs to have the actual EPW file available** when running EnergyPlus.

---

## 📋 What IDF Creator Does Automatically

### 1. **Determines Weather File Name** (AUTOMATIC)

When you provide an address, IDF Creator:
1. Geocodes the address → gets latitude/longitude
2. Looks up closest weather station → determines weather file name
3. Includes weather file name in IDF location data

**Example**:
```python
Input: "Willis Tower, Chicago, IL"
       ↓
Output: {
  'weather_file': 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw',
  'weather_description': 'Chicago O\'Hare International Airport',
  'weather_url': 'https://energyplus.net/weather-location/...'
}
```

**Code**: `src/enhanced_location_fetcher.py` line 78-83
- Uses `NRELFetcher.get_closest_weather_file()` 
- Maps coordinates to appropriate TMY3 weather files
- Returns weather file name, description, and download URL

### 2. **Includes Weather Reference in IDF** (AUTOMATIC)

The IDF file includes:
- `Site:Location` object (latitude, longitude, elevation, time zone)
- Weather file name reference (though not the actual file)

**Code**: `src/professional_idf_generator.py` line 363-366
```python
# Weather File
idf_content.append(self.generate_weather_file_object(
    location_data.get('weather_file', 'USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw')
))
```

---

## ⚠️ What User Still Needs to Do

### **Get the Actual EPW File**

The IDF file **references** a weather file by name, but **doesn't include the actual EPW file**. EnergyPlus requires the physical `.epw` file to run simulations.

### Option 1: Use EnergyPlus Default Weather Files

If EnergyPlus is installed, it typically comes with weather files:

```bash
# Typical locations:
/usr/share/EnergyPlus/weather/
/opt/EnergyPlus/weather/
~/EnergyPlus/weather/

# Find weather files on your system
find /usr -name "*.epw" 2>/dev/null | head -5
```

**Most common locations have the standard TMY3 files** that IDF Creator references.

### Option 2: Download from EnergyPlus Website

IDF Creator provides a download URL in the location data:

```python
# Example location data
{
  'weather_file': 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw',
  'weather_url': 'https://energyplus.net/weather-location/north_and_central_america_wmo_region_4/USA/IL',
  'weather_description': 'Chicago O\'Hare International Airport'
}
```

**Download manually**:
1. Visit `https://energyplus.net/weather`
2. Search for your city
3. Download the `.epw` file
4. Place in EnergyPlus weather directory or your project directory

### Option 3: Use EnergyPlus API (Future Enhancement)

Currently, `NRELFetcher.download_epw_file()` is a **placeholder** (doesn't actually download):

```python
# From src/nrel_fetcher.py line 145-159
def download_epw_file(self, weather_file_name: str, 
                     output_path: str = "weather_data/") -> Optional[str]:
    """
    Download an EPW weather file.
    
    # In production, implement actual download from EnergyPlus weather database
    # For now, return the filename
    return weather_file_name
```

**Future**: This could be implemented to automatically download weather files.

---

## 🔍 How EnergyPlus Finds Weather Files

When you run EnergyPlus, it looks for weather files in this order:

1. **Current directory** (where you run EnergyPlus)
2. **Same directory as IDF file**
3. **EnergyPlus weather directory** (`/usr/share/EnergyPlus/weather/` or similar)
4. **Path specified in IDF file** (if absolute path is used)

### Running EnergyPlus

```bash
# If weather file is in same directory as IDF
energyplus -w USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw -r building.idf

# If weather file is in EnergyPlus weather directory
energyplus -w USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw building.idf

# If weather file is elsewhere, use full path
energyplus -w /path/to/weather/file.epw building.idf
```

---

## 📊 Current Implementation Status

### ✅ What Works

1. **Automatic weather file selection** based on address
2. **Weather file name included in IDF** location data
3. **Location-appropriate weather files** suggested (Chicago → Chicago weather, NYC → NYC weather)

### ⚠️ What's Missing

1. **Automatic EPW file download** - NREL fetcher only suggests file names
2. **EPW file validation** - No check if weather file exists before simulation
3. **Weather file bundling** - EPW files not included in generated IDF

### 🔮 Future Enhancements

Could be added:
1. **Auto-download weather files** from EnergyPlus/NREL
2. **Weather file validation** - Check if file exists before simulation
3. **Weather file caching** - Download once, reuse for similar locations
4. **Alternative weather sources** - NSRDB API integration

---

## 💡 Practical Workflow

### For Users

**Step 1: Generate IDF** (automatic weather file selection)
```python
creator = IDFCreator(professional=True)
data = creator.process_inputs('123 Main St, Chicago, IL')
# Weather file name automatically determined: 
# 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'
```

**Step 2: Get Weather File** (manual step)
```bash
# Option A: Download from energyplus.net
wget https://energyplus.net/weather/download/.../USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw

# Option B: Use EnergyPlus default (if installed)
# File may already be in /usr/share/EnergyPlus/weather/
```

**Step 3: Run EnergyPlus**
```bash
energyplus -w USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw building.idf
```

---

## 🎯 Summary

| Aspect | Status | Notes |
|--------|--------|-------|
| **Weather file selection** | ✅ Automatic | Based on address geocoding |
| **Weather file name in IDF** | ✅ Automatic | Included in location data |
| **EPW file download** | ❌ Manual | User must download or use EnergyPlus defaults |
| **Weather file validation** | ⚠️ Partial | Only checks if file exists during simulation |
| **Auto-bundling EPW** | ❌ Not implemented | IDF doesn't include weather file |

---

## 🔧 Technical Details

### Location in IDF File

The IDF file doesn't actually reference the weather file directly. EnergyPlus uses the `-w` command-line flag:

```bash
# Weather file is passed as command-line argument, not in IDF
energyplus -w weather.epw building.idf
```

The IDF file does include:
- `Site:Location` (lat/long for solar calculations)
- `Site:GroundTemperature:BuildingSurface` (ground temperatures)
- `Site:GroundTemperature:Shallow` (shallow ground temps)

These are used for ground heat transfer calculations, independent of the weather file.

---

## 📚 Related Files

- `src/nrel_fetcher.py` - Weather file name selection
- `src/enhanced_location_fetcher.py` - Location data fetching
- `src/professional_idf_generator.py` - IDF generation with location data




